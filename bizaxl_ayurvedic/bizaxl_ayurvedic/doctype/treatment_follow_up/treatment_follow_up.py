# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TreatmentFollowUp(Document):
    def validate(self):
        """Auto-create the next pending visit row when an existing row's status
        changes to 'Completed'. Only triggers for rows that existed *before*
        this save (i.e. were already persisted) — newly appended rows from
        create_or_extend_from_encounter are excluded because that function
        already creates the next pending row."""
        if self.is_new() or not self.follow_up_visits:
            return

        previous = self.get_doc_before_save()
        if not previous:
            return

        prev_statuses = {r.name: r.status for r in (previous.follow_up_visits or [])}
        interval = self.follow_up_after_days or 30
        add_days = frappe.utils.add_days
        getdate = frappe.utils.getdate

        for row in self.follow_up_visits:
            prev_status = prev_statuses.get(row.name)
            # Only act on EXISTING rows whose status changed TO Completed.
            # New rows appended by create_or_extend_from_encounter have
            # prev_status = None and are safely skipped.
            if prev_status is not None and prev_status != "Completed" and row.status == "Completed":
                next_date = row.next_follow_up_date or add_days(
                    getdate(row.visit_date or self.start_date), interval
                )
                # Guard: don't duplicate an already-scheduled Pending visit
                already_exists = any(
                    r.status == "Pending" and r.visit_date == next_date
                    for r in self.follow_up_visits
                )
                if not already_exists:
                    self.append("follow_up_visits", {
                        "visit_date": next_date,
                        "next_follow_up_date": add_days(getdate(next_date), interval),
                        "status": "Pending",
                    })


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
