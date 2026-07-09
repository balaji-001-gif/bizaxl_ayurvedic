# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

"""
Patch: v0.4 — Add status and patient_mobile fields to Token Counter doctype
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Creates:
  - A new `status` Select field on Token Counter (Waiting / In Consultation /
    Completed / Called, default Waiting)
  - A new `patient_mobile` Data field on Token Counter (fetched from Patient)

Run after deploying the JSON schema update so existing tokens get populated.
"""

import frappe


def execute():
    doctype = "Token Counter"

    frappe.reload_doc("Bizaxl Ayurvedic", "doctype", "token_counter")

    # Backfill patient_mobile for existing tokens that have a patient_appointment
    existing = frappe.get_all(
        "Token Counter",
        filters={"patient_mobile": ["is", "not set"]},
        fields=["name", "patient_appointment"],
    )
    for t in existing:
        if not t.patient_appointment:
            continue
        patient = frappe.db.get_value(
            "Patient Appointment", t.patient_appointment, "patient"
        )
        if not patient:
            continue
        mobile = frappe.db.get_value("Patient", patient, "mobile")
        if mobile:
            frappe.db.set_value(
                "Token Counter", t.name, "patient_mobile", mobile,
                update_modified=False,
            )

    frappe.db.commit()
