# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
WhatsApp Business Cloud API integration layer.

Centralises all outbound/inbound WhatsApp traffic so the AI chatbot,
follow-up reminders, and the "WhatsApp Prescription Fulfilment Bot" (Gap
Analysis Section 2, Item 2) share one client. Configure credentials in
"Bizaxl Ayurvedic Settings" (Single DocType, see fixtures) — never hard-code
tokens here.
"""
import frappe
import requests

SETTINGS_DOCTYPE = "Bizaxl Ayurvedic Settings"


def _get_settings():
    return frappe.get_single(SETTINGS_DOCTYPE)


def send_text_message(to_number, message):
    settings = _get_settings()
    if not settings.whatsapp_access_token or not to_number:
        frappe.logger("bizaxl_ayurvedic").warning("WhatsApp not configured or missing recipient; skipping send")
        return None

    url = f"https://graph.facebook.com/v19.0/{settings.whatsapp_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {settings.get_password('whatsapp_access_token')}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message},
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        frappe.log_error(title="WhatsApp send_text_message failed")
        return None


@frappe.whitelist(allow_guest=True)
def inbound_webhook():
    """Registered as the WhatsApp Cloud API webhook target
    (/api/method/bizaxl_ayurvedic.integrations.whatsapp.inbound_webhook).

    Routes:
      - image/document with a prescription photo -> OCR + catalogue match
        (WhatsApp Prescription Fulfilment Bot, Section 2 Item 2)
      - plain text -> AI Chatbot (Section 2 Item 3)
    """
    payload = frappe.request.get_json(silent=True) or {}
    entry = (payload.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])[0]
    messages = (changes.get("value") or {}).get("messages") or []

    for msg in messages:
        from_number = msg.get("from")
        if msg.get("type") == "image":
            from bizaxl_ayurvedic.integrations.prescription_ocr import handle_prescription_image
            handle_prescription_image(from_number, msg["image"]["id"])
        elif msg.get("type") == "text":
            from bizaxl_ayurvedic.ai.chatbot import handle_user_message
            handle_user_message(from_number, msg["text"]["body"])

    return {"status": "ok"}
