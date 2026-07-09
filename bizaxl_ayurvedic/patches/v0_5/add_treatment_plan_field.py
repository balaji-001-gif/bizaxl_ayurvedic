# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

"""
Patch: v0.5 — Add Treatment Plan Template link + cost fields
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Adds a custom field `treatment_plan_template` on the Patient Encounter
doctype so practitioners can associate a treatment plan and view/share
its cost breakdown directly from the encounter form.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Patient Encounter": [
            {
                "fieldname": "treatment_plan_template",
                "label": "Treatment Plan Template",
                "fieldtype": "Link",
                "options": "Treatment Plan Template",
                "insert_after": "encounter_date",
                "in_list_view": 1,
            },
        ],
    }
    create_custom_fields(custom_fields, ignore_validate=True)
    frappe.db.commit()
