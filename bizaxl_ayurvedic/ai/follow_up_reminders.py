# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Auto-generated WhatsApp / in-app follow-up reminders for staff.
(Gap Analysis Section 1 — bundled with AI Lead Scoring, HIGH priority)

This module only prepares the reminder payloads and pushes an in-app
Notification Log entry; actual WhatsApp delivery is delegated to
bizaxl_ayurvedic.integrations.whatsapp (stub) so the WhatsApp Business Cloud
API credentials stay isolated from core business logic.
"""
import frappe
from frappe.utils import today, add_days, getdate


def send_due_follow_up_reminders():
    """Daily scheduled job."""
    due_leads = frappe.get_all(
        "Clinical Lead",
        filters={"follow_up_date": ["<=", today()], "lead_status": ["not in", ["Converted", "Lost"]]},
        fields=["name", "lead_name", "mobile_number", "counsellor", "follow_up_date"],
    )
    for lead in due_leads:
        _notify_counsellor(lead)

    due_visits = frappe.get_all(
        "Treatment Follow-Up",
        filters={"docstatus": 1},
        fields=["name", "patient"],
    )
    for tf in due_visits:
        _check_visit_rows(tf)


def _notify_counsellor(lead):
    if not lead.counsellor:
        return
    user = frappe.db.get_value("Healthcare Practitioner", lead.counsellor, "user_id")
    if not user:
        return
    frappe.get_doc({
        "doctype": "Notification Log",
        "subject": f"Follow up due today: {lead.lead_name}",
        "for_user": user,
        "type": "Alert",
        "document_type": "Clinical Lead",
        "document_name": lead.name,
    }).insert(ignore_permissions=True)
    # WhatsApp channel (see bizaxl_ayurvedic/integrations/whatsapp.py)
    from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
    send_text_message(lead.mobile_number, f"Reminder: your Ayurvedic consultation follow-up is due today.")


def _check_visit_rows(tf_name):
    tf = frappe.get_doc("Treatment Follow-Up", tf_name)
    for row in tf.follow_up_visits:
        if row.status == "Pending" and row.next_follow_up_date and getdate(row.next_follow_up_date) <= getdate(today()):
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"Patient follow-up due: {tf.patient}",
                "for_user": frappe.session.user,
                "type": "Alert",
                "document_type": "Treatment Follow-Up",
                "document_name": tf.name,
            }).insert(ignore_permissions=True)
