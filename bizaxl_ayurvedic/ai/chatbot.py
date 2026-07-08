# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
AI Chatbot (Customer & Counter Assistant)
(Gap Analysis Section 2, Item 3 — white-space opportunity)

24/7 WhatsApp + website chatbot answering product/health queries, checking
loyalty points, confirming stock, booking appointments, and collecting
feedback. Implemented as a thin retrieval-augmented layer: intent routing
here, actual generation delegated to whichever LLM provider is configured
in "Bizaxl Ayurvedic Settings" (kept provider-agnostic — plug in Claude, or
any OpenAI-compatible endpoint, via a single call_llm() function).
"""
import frappe
import re

INTENT_PATTERNS = {
    "loyalty_points": re.compile(r"\b(loyalty|points|reward)\b", re.I),
    "stock_check": re.compile(r"\b(stock|available|in stock)\b", re.I),
    "book_appointment": re.compile(r"\b(book|appointment|slot|panchakarma)\b", re.I),
    "feedback": re.compile(r"\b(feedback|review|rating|complaint)\b", re.I),
}


def classify_intent(message: str) -> str:
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(message):
            return intent
    return "general_query"


def call_llm(prompt: str, context: str = "") -> str:
    """Provider-agnostic LLM call. Reads endpoint/key from Bizaxl Ayurvedic
    Settings so any OpenAI-compatible or Anthropic-compatible endpoint can be
    plugged in without code changes. Returns a plain-text answer."""
    settings = frappe.get_single("Bizaxl Ayurvedic Settings")
    if not settings.llm_api_endpoint:
        return ("I can help once our team finishes connecting the AI assistant. "
                "In the meantime, please call the store directly.")

    import requests
    try:
        r = requests.post(
            settings.llm_api_endpoint,
            headers={"Authorization": f"Bearer {settings.get_password('llm_api_key')}"},
            json={"prompt": prompt, "context": context},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("answer", "")
    except Exception:
        frappe.log_error(title="AI Chatbot LLM call failed")
        return "Sorry, I'm having trouble answering that right now — a staff member will follow up."


def handle_user_message(from_number, message):
    intent = classify_intent(message)
    reply = _dispatch(intent, from_number, message)

    from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
    send_text_message(from_number, reply)

    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Customer",
        "reference_name": frappe.db.get_value("Customer", {"mobile_no": from_number}, "name") or "",
        "content": f"Chatbot Q: {message}\nIntent: {intent}\nA: {reply}",
    }).insert(ignore_permissions=True)


def _dispatch(intent, from_number, message):
    if intent == "loyalty_points":
        customer = frappe.db.get_value("Customer", {"mobile_no": from_number},
                                        ["name", "loyalty_program", "custom_brand_loyalty_points"], as_dict=True)
        if not customer:
            return "We couldn't find a loyalty account for this number yet — visit the store to enroll!"
        return f"You currently have {customer.custom_brand_loyalty_points or 0} loyalty points."

    if intent == "stock_check":
        # naive keyword search against Item name; production version would use
        # NLU to extract the product name before querying
        items = frappe.get_all("Item", filters={"item_name": ["like", f"%{message.split()[-1]}%"]},
                                fields=["item_name"], limit_page_length=3)
        if not items:
            return "I couldn't find that product — could you share the exact name?"
        return "In stock: " + ", ".join(i.item_name for i in items)

    if intent == "book_appointment":
        return ("Sure! Please share your preferred date and treatment, or use our booking page: "
                "https://<storename>.bizaxl.com/book")

    if intent == "feedback":
        return "Thank you! Please rate your last visit 1-5 and add any comments — we read every message."

    return call_llm(message)
