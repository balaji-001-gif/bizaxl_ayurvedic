# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TreatmentFollowUp(Document):
    pass


def create_or_extend_from_encounter(doc, method=None):
    """DocType Event handler: Patient Encounter -> After Insert.
    Registered in hooks.py as:
        bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.treatment_follow_up.treatment_follow_up.create_or_extend_from_encounter

    NOTE: this must be a module-level function (not a class method) because
    frappe.get_attr() only resolves one level of `module.function` — it does
    not walk through an intermediate class.

    Ports the client's original Server Script ("Follow-up status tracking in
    treatment follow-up"): reuses an existing, still-valid Treatment Follow-Up
    for the patient, or creates a new one, and appends the next scheduled visit.
    """
    add_days = frappe.utils.add_days
    getdate = frappe.utils.getdate

    existing = frappe.get_all(
        "Treatment Follow-Up",
        filters={"patient": doc.patient},
        fields=["name", "start_date"],
        order_by="creation desc",
        limit_page_length=1,
    )

    doc_follow = None
    if existing:
        doc_follow = frappe.get_doc("Treatment Follow-Up", existing[0].name)
        if add_days(getdate(doc_follow.start_date), 30) >= getdate(doc.encounter_date):
            doc_follow.flags.ignore_validate_update_after_submit = True
            doc_follow.append("follow_up_visits", {
                "visit_date": doc.encounter_date,
                "next_follow_up_date": add_days(getdate(doc.encounter_date), 30),
                "status": "Pending",
            })
            doc_follow.save(ignore_permissions=True, ignore_version=True)
        else:
            doc_follow = None

    if not doc_follow:
        doc_follow = frappe.new_doc("Treatment Follow-Up")
        doc_follow.patient = doc.patient
        doc_follow.consultation = doc.name
        doc_follow.start_date = doc.encounter_date
        doc_follow.expected_recovery_date = add_days(getdate(doc.encounter_date), 90)
        doc_follow.append("follow_up_visits", {
            "visit_date": doc.encounter_date,
            "next_follow_up_date": add_days(getdate(doc.encounter_date), 30),
            "status": "Pending",
        })
        doc_follow.insert(ignore_permissions=True)
