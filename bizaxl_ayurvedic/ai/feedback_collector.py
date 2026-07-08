# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Automated Feedback & Review Collection
(Gap Analysis — MEDIUM priority gap vs Clinicea / NeftX)

Auto-sends WhatsApp feedback requests after billing (Sales Invoice submit)
and aggregates ratings in a store-level Patient Feedback doctype. Satisfied
customers (rating >= 4) are prompted with a Google Review link.

Flow:
  1. Sales Invoice is submitted → `request_feedback_after_billing()` queues
     a WhatsApp message asking for a 1-5 rating.
  2. Customer replies via WhatsApp → chatbot's feedback intent captures the
     rating and creates a Patient Feedback record.
  3. If rating >= 4, a Google Review link is auto-shared.
  4. A daily scheduled job (`send_pending_feedback_requests`) retries any
     feedback requests that haven't been answered within 2 days.
"""
import frappe
from frappe.utils import today, add_days


def request_feedback_after_billing(doc, method):
    """Hook on Sales Invoice 'on_submit' — sends a feedback request via WhatsApp.

    Only sends for walk-in / store billing (not internal transfers or
    adjustments). Creates a placeholder Patient Feedback record so the
    daily retry job can track unanswered requests.
    """
    if not doc.mobile_no:
        return

    # Skip internal / zero-value invoices
    if doc.docstatus != 1 or doc.total <= 0:
        return

    # Check if feedback was already requested for this invoice
    existing = frappe.db.exists("Patient Feedback", {"sales_invoice": doc.name})
    if existing:
        return

    # Create a pending feedback record
    feedback = frappe.get_doc({
        "doctype": "Patient Feedback",
        "customer": doc.customer,
        "sales_invoice": doc.name,
        "source": "WhatsApp",
        "rating": 0,
    })
    feedback.flags.ignore_mandatory = True
    feedback.insert(ignore_permissions=True)

    # Send WhatsApp feedback request
    from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
    send_text_message(
        doc.mobile_no,
        f"Thank you for visiting {frappe.db.get_single_value('Bizaxl Ayurvedic Settings', 'store_name') or 'our store'}! "
        f"We'd love your feedback. Please reply with a rating from 1-5 "
        f"(5 = Excellent) and any comments. Your input helps us serve you better 🙏",
    )


@frappe.whitelist()
def handle_feedback_response(from_number: str, message: str):
    """Handle incoming WhatsApp feedback response from the chatbot.

    Expected format: "<rating>/5" or "<rating>" followed by optional comments.
    E.g. "4/5 Great service!" or "5"
    """
    import re

    # Try to extract rating from the message
    rating_match = re.search(r"(\d+)\s*(?:/5)?", message.strip())
    if not rating_match:
        return "Please reply with a rating from 1-5. Example: '4/5 Great service!'"

    rating = int(rating_match.group(1))
    if rating < 1 or rating > 5:
        return "Please choose a rating between 1 and 5."

    # Extract comments (text after the rating)
    comments = message.strip()
    # Remove the rating prefix
    comments = re.sub(r"^\d+\s*(?:/5)?\s*", "", comments).strip()

    # Find the customer by phone number
    customer = frappe.db.get_value("Customer", {"mobile_no": from_number}, "name")
    patient = frappe.db.get_value("Patient", {"mobile": from_number}, "name")

    # Find the most recent unanswered feedback for this customer
    feedback_name = frappe.db.get_value(
        "Patient Feedback",
        {"customer": customer, "rating": 0},
        order_by="creation desc",
    )

    if feedback_name:
        feedback = frappe.get_doc("Patient Feedback", feedback_name)
        feedback.rating = rating
        feedback.comments = comments
        feedback.source = "WhatsApp"
        feedback.flags.ignore_mandatory = True
        feedback.save(ignore_permissions=True)
    else:
        # Create new feedback record
        feedback = frappe.get_doc({
            "doctype": "Patient Feedback",
            "customer": customer or "",
            "patient": patient or "",
            "rating": rating,
            "comments": comments,
            "source": "WhatsApp",
        })
        feedback.flags.ignore_mandatory = True
        feedback.insert(ignore_permissions=True)

    reply = f"Thank you for your {rating}/5 rating! 🙏"
    if rating >= 4 and feedback.google_review_link_sent:
        reply += " We really appreciate your support!"

    return reply


def send_pending_feedback_requests():
    """Daily scheduled job — retries feedback requests that haven't been
    answered within 2 days of the original invoice date.
    """
    two_days_ago = add_days(today(), -2)
    pending = frappe.get_all(
        "Patient Feedback",
        filters={
            "rating": 0,
            "creation": ["<=", two_days_ago],
        },
        fields=["name", "customer", "sales_invoice"],
    )
    for fb in pending:
        if fb.sales_invoice:
            invoice = frappe.get_doc("Sales Invoice", fb.sales_invoice)
            if invoice.mobile_no and invoice.docstatus == 1:
                from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
                send_text_message(
                    invoice.mobile_no,
                    f"Hi! We'd still love to hear your feedback on your recent visit. "
                    f"A quick rating (1-5) helps us improve 🙏",
                )

    if pending:
        frappe.logger("bizaxl_ayurvedic").info(
            f"Sent {len(pending)} pending feedback request reminders"
        )
