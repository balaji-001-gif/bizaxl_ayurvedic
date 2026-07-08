# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TokenCounter(Document):
    pass

# ------------------------------------------------------------------
# Whitelisted helpers used by token_counter.js (bound to Patient Appointment)
# ------------------------------------------------------------------

@frappe.whitelist()
def create_next_token(appointment, date, practitioner):
    """Creates and submits the next sequential Token Counter for a
    practitioner/date combination. Ported from the client's original
    'Create the token counter number from the patient appointment details'
    Client Script."""
    last = frappe.get_all(
        "Token Counter",
        filters={"date": date, "healthcare_practitioner": practitioner},
        fields=["last_token"],
        order_by="last_token desc",
        limit_page_length=1,
    )
    new_token = (last[0].last_token + 1) if last else 1

    token_doc = frappe.get_doc({
        "doctype": "Token Counter",
        "date": date,
        "healthcare_practitioner": practitioner,
        "patient_appointment": appointment,
        "last_token": new_token,
    }).insert(ignore_permissions=True)
    token_doc.submit()
    return new_token


@frappe.whitelist()
def get_token_queue_html(practitioner):
    data = frappe.get_all(
        "Token Counter",
        filters={"healthcare_practitioner": practitioner},
        fields=["last_token", "patient_appointment", "patient_name", "practitioner_name", "date"],
        order_by="last_token asc",
        limit_page_length=100,
    )
    if not data:
        return "<p>No tokens found for today.</p>"

    row_html = []
    for i, d in enumerate(data):
        row_class = "table-warning" if i == 0 else ""
        status = "Current" if i == 0 else "Waiting"
        row_html.append(
            f"<tr class='{row_class}'>"
            f"<td>{d.last_token}</td><td>{d.patient_name or '-'}</td>"
            f"<td>{d.patient_appointment or '-'}</td><td>{d.date or '-'}</td>"
            f"<td>{status}</td></tr>"
        )
    rows = "".join(row_html)
    return (
        f"<h4>Practitioner: {data[0].practitioner_name or '-'} &middot; Queue: {len(data)}</h4>"
        "<table class='table table-bordered'><thead><tr>"
        "<th>Token</th><th>Patient</th><th>Appointment</th><th>Date</th><th>Status</th>"
        f"</tr></thead><tbody>{rows}</tbody></table>"
    )
