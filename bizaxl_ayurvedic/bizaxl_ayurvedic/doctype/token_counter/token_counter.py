# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TokenCounter(Document):
    def before_insert(self):
        """Auto-populate patient mobile from the linked Patient Appointment."""
        if self.patient_appointment:
            patient = frappe.db.get_value(
                "Patient Appointment", self.patient_appointment, "patient"
            )
            if patient:
                self.patient_mobile = frappe.db.get_value("Patient", patient, "mobile")


# ------------------------------------------------------------------
# Whitelisted helpers — Token Dashboard API and legacy queue helpers
# ------------------------------------------------------------------

def assign_token_number(doc, method=None):
    """DocType Event: Patient Appointment -> before_insert.

    Auto-assigns a daily-resetting token number (starts at 1 each day)
    by querying the highest existing token_number for the appointment date.
    Reliable server-side approach — no async issues."""
    if doc.token_number:
        return
    last_token = frappe.db.get_value(
        "Patient Appointment",
        filters={"appointment_date": doc.appointment_date},
        fieldname="token_number",
        order_by="token_number desc",
    )
    doc.token_number = (last_token or 0) + 1


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
    """Legacy helper — returns an HTML table for the Token Queue dialog."""
    data = frappe.get_all(
        "Token Counter",
        filters={"healthcare_practitioner": practitioner},
        fields=["last_token", "patient_appointment", "patient_name",
                "practitioner_name", "date", "status"],
        order_by="last_token asc",
        limit_page_length=100,
    )
    if not data:
        return "<p>No tokens found for today.</p>"

    row_html = []
    for i, d in enumerate(data):
        row_class = "ba-current" if i == 0 and d.status == "Waiting" else ""
        display_status = d.status or "Waiting"
        row_html.append(
            f"<tr class='{row_class}'>"
            f"<td>{d.last_token}</td><td>{d.patient_name or '-'}</td>"
            f"<td>{d.patient_appointment or '-'}</td><td>{d.date or '-'}</td>"
            f"<td>{display_status}</td></tr>"
        )
    rows = "".join(row_html)
    return (
        f"<h4>Practitioner: {data[0].practitioner_name or '-'} &middot; Queue: {len(data)}</h4>"
        "<table class='table table-bordered'><thead><tr>"
        "<th>Token</th><th>Patient</th><th>Appointment</th><th>Date</th><th>Status</th>"
        f"</tr></thead><tbody>{rows}</tbody></table>"
    )


# ------------------------------------------------------------------
# Token Dashboard API — used by the Token Dashboard page
# ------------------------------------------------------------------

@frappe.whitelist()
def get_today_queue(date=None):
    """Return today's token queue grouped by practitioner, with summary stats.
    Called by the Token Dashboard page every ~15 seconds (auto-refresh)."""
    from frappe.utils import today as _today
    if not date:
        date = _today()

    tokens = frappe.get_all(
        "Token Counter",
        filters={"date": date, "docstatus": 1},
        fields=[
            "name", "last_token", "patient_name", "patient_mobile",
            "patient_appointment", "healthcare_practitioner",
            "practitioner_name", "status", "date",
        ],
        order_by="healthcare_practitioner asc, last_token asc",
    )

    # Group by practitioner + compute stats
    practitioners = {}
    for t in tokens:
        p = t.healthcare_practitioner
        pname = t.practitioner_name or p
        if p not in practitioners:
            practitioners[p] = {
                "practitioner": p,
                "practitioner_name": pname,
                "tokens": [],
                "stats": {"total": 0, "waiting": 0, "in_consultation": 0, "completed": 0, "called": 0},
            }
        practitioners[p]["tokens"].append(t)
        practitioners[p]["stats"]["total"] += 1
        st = (t.status or "Waiting").lower().replace(" ", "_")
        if st in practitioners[p]["stats"]:
            practitioners[p]["stats"][st] += 1

    return {
        "date": date,
        "total_tokens": len(tokens),
        "practitioners": list(practitioners.values()),
    }


@frappe.whitelist()
def call_patient(token_name):
    """Mark a token as 'Called' so the receptionist knows to alert the patient.
    Returns the patient mobile and name for easy dialing."""
    doc = frappe.get_doc("Token Counter", token_name)
    doc.flags.ignore_validate_update_after_submit = True
    doc.status = "Called"
    doc.save(ignore_permissions=True)
    return {
        "patient_name": doc.patient_name,
        "patient_mobile": doc.patient_mobile,
    }


@frappe.whitelist()
def update_status(token_name, status):
    """Update a token's status (Waiting / In Consultation / Completed / Called)."""
    valid = {"Waiting", "In Consultation", "Completed", "Called"}
    if status not in valid:
        frappe.throw(f"Invalid status: {status}")
    doc = frappe.get_doc("Token Counter", token_name)
    doc.flags.ignore_validate_update_after_submit = True
    doc.status = status
    doc.save(ignore_permissions=True)
    return doc.status


@frappe.whitelist()
def get_dashboard_stats(date=None):
    """Return aggregate token stats for a given date (or today)."""
    from frappe.utils import today as _today
    if not date:
        date = _today()

    tokens = frappe.get_all(
        "Token Counter",
        filters={"date": date, "docstatus": 1},
        fields=["status", "healthcare_practitioner"],
    )
    total = len(tokens)
    stats = {"total": total, "waiting": 0, "in_consultation": 0, "completed": 0, "called": 0}
    for t in tokens:
        st = (t.status or "Waiting").lower().replace(" ", "_")
        if st in stats:
            stats[st] += 1
    return stats
