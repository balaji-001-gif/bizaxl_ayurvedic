# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds an **Exercise Steps** custom field to the **Exercise** child table doctype
(from Frappe Healthcare — the exercises table inside Therapy Session).

When an Exercise Type is selected in a Therapy Session, the exercise_steps HTML
is auto-fetched from the Exercise Type and stored in this field so it displays
directly inside the grid row.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    CHILD_DOCTYPE = "Exercise"

    # Guard: the Healthcare child table might not be installed yet
    if not frappe.db.exists("DocType", CHILD_DOCTYPE):
        return

    # Check if field already exists
    if frappe.get_meta(CHILD_DOCTYPE).has_field("exercise_steps"):
        return

    create_custom_fields({
        CHILD_DOCTYPE: [
            {
                "fieldname": "exercise_steps",
                "label": "Exercise Steps",
                "fieldtype": "Text Editor",
                "insert_after": "exercise_type",
                "read_only": 1,
                "description": "Auto-fetched from Exercise Type. Shows step-by-step instructions.",
            },
        ],
    })
