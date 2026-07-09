# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TreatmentFollowUp(Document):
    pass


def create_or_extend_from_encounter(doc, method=None):
    """DocType Event handler: Patient Encounter -> on_submit.
    Registered in hooks.py as:
        bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.treatment_follow_up.treatment_follow_up.create_or_extend_from_encounter

    NOTE: this must be a module-level function (not a class method) because
    frappe.get_attr() only resolves one level of `module.function` — it does
    not walk through an intermediate class.

    Creates or extends a single Treatment Follow-Up per patient (once per patient).
    Always reuses the existing record — never creates a duplicate.
    After recording the current encounter visit, also auto-creates the next
    scheduled follow-up visit row based on follow_up_after_days.
    """
    if doc.docstatus != 1:
        return  # Only act on submitted encounters

    add_days = frappe.utils.add_days
    getdate = frappe.utils.getdate

    # Find existing Treatment Follow-Up for this patient (once per patient)
    existing = frappe.get_all(
        "Treatment Follow-Up",
        filters={"patient": doc.patient},
        fields=["name"],
        limit_page_length=1,
    )

    if existing:
        doc_follow = frappe.get_doc("Treatment Follow-Up", existing[0].name)
        doc_follow.flags.ignore_validate_update_after_submit = True
        is_new = False
    else:
        doc_follow = frappe.new_doc("Treatment Follow-Up")
        doc_follow.patient = doc.patient
        doc_follow.consultation = doc.name
        doc_follow.start_date = doc.encounter_date
        duration = doc_follow.total_treatment_duration_days or 90
        doc_follow.expected_recovery_date = add_days(getdate(doc.encounter_date), duration)
        is_new = True

    # Determine the interval for the next follow-up
    interval = doc_follow.follow_up_after_days or 30

    # Record the current encounter as a completed visit
    next_follow_up_date = add_days(getdate(doc.encounter_date), interval)
    doc_follow.append("follow_up_visits", {
        "visit_date": doc.encounter_date,
        "next_follow_up_date": next_follow_up_date,
        "status": "Completed",
    })

    # Auto-create the next scheduled follow-up visit
    doc_follow.append("follow_up_visits", {
        "visit_date": next_follow_up_date,
        "next_follow_up_date": add_days(next_follow_up_date, interval),
        "status": "Pending",
    })

    if is_new:
        doc_follow.insert(ignore_permissions=True)
    else:
        doc_follow.save(ignore_permissions=True, ignore_version=True)
