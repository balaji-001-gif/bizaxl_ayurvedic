# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
WhatsApp Prescription Fulfilment Bot
(Gap Analysis Section 2, Item 2 — white-space opportunity)

Flow: customer sends a WhatsApp photo of an Ayurvedic prescription -> OCR
extracts line items -> fuzzy-match against the ERPNext Item master ->
draft Sales Order created for counter staff to confirm and dispatch.

OCR provider is pluggable: defaults to Tesseract (bundled, no external cost);
swap in Google Cloud Vision by setting
Bizaxl Ayurvedic Settings.ocr_provider = "google_vision".
"""
import io
import frappe
from frappe.utils import cint
from difflib import get_close_matches


def _download_media(media_id):
    from bizaxl_ayurvedic.integrations.whatsapp import _get_settings
    import requests
    settings = _get_settings()
    token = settings.get_password("whatsapp_access_token")
    meta = requests.get(
        f"https://graph.facebook.com/v19.0/{media_id}",
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    ).json()
    media_url = meta.get("url")
    if not media_url:
        return None
    return requests.get(media_url, headers={"Authorization": f"Bearer {token}"}, timeout=15).content


def _ocr_text(image_bytes, provider="tesseract"):
    if provider == "google_vision":
        # Placeholder: wire up google-cloud-vision client here with your own
        # service-account credentials; kept out of the base app to avoid an
        # unnecessary hard dependency.
        raise NotImplementedError("Configure Google Vision credentials in Bizaxl Ayurvedic Settings")

    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(io.BytesIO(image_bytes)))


def _match_items(lines):
    all_items = frappe.get_all("Item", filters={"disabled": 0}, pluck="item_name")
    matched = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        close = get_close_matches(line, all_items, n=1, cutoff=0.6)
        if close:
            matched.append({"item_name": close[0], "raw_text": line})
    return matched


def handle_prescription_image(from_number, media_id):
    settings = frappe.get_single("Bizaxl Ayurvedic Settings")
    image_bytes = _download_media(media_id)
    if not image_bytes:
        return

    text = _ocr_text(image_bytes, provider=getattr(settings, "ocr_provider", "tesseract"))
    lines = [l for l in text.splitlines() if l.strip()]
    matched = _match_items(lines)

    if not matched:
        from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
        send_text_message(from_number, "We couldn't read any items from that prescription. "
                                        "Could you try a clearer photo, or reply with the item names?")
        return

    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": _get_or_create_customer_by_phone(from_number),
        "delivery_date": frappe.utils.add_days(frappe.utils.today(), 1),
        "items": [
            {"item_code": frappe.db.get_value("Item", {"item_name": m["item_name"]}, "name"), "qty": 1}
            for m in matched
        ],
    })
    so.flags.ignore_mandatory = True
    so.insert(ignore_permissions=True)

    from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
    item_list = ", ".join(m["item_name"] for m in matched)
    send_text_message(
        from_number,
        f"We found these items on your prescription: {item_list}. "
        f"A draft order {so.name} has been created — our team will confirm pricing and delivery shortly.",
    )


def _get_or_create_customer_by_phone(phone_number):
    existing = frappe.db.get_value("Customer", {"mobile_no": phone_number}, "name")
    if existing:
        return existing
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": f"WhatsApp Customer {phone_number}",
        "customer_type": "Individual",
        "mobile_no": phone_number,
    }).insert(ignore_permissions=True)
    return customer.name
