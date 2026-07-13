# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds an **Exercise Steps** custom field to the **Therapy Session Exercise** child
table doctype (from Frappe Healthcare). When an Exercise Type is selected in a
Therapy Session, the exercise_steps HTML is auto-fetched from the Exercise Type
and stored in this field so it displays directly inside the grid row.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # Check if already exists
    if frappe.get_meta("Therapy Session Exercise").has_field("exercise_steps"):
        return

    create_custom_fields({
        "Therapy Session Exercise": [
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
