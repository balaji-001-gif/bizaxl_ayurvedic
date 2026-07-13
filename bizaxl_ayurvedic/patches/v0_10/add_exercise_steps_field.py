# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Ensures an **Exercise Steps** field is available on the **Exercise Type** doctype.

The standard Frappe Healthcare Exercise Type already includes an `exercise_steps`
field by default — this patch just checks if it's available and, if not, creates
it as a custom Text Editor field. This makes the patch safe to run regardless of
the Healthcare version (some versions may omit the field).
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # Check if exercise_steps already exists (either as standard or custom field)
    existing = frappe.db.exists(
        "Custom Field",
        {"dt": "Exercise Type", "fieldname": "exercise_steps"},
    )
    if existing:
        return  # Field already present — nothing to do

    create_custom_fields({
        "Exercise Type": [
            {
                "fieldname": "exercise_steps",
                "label": "Exercise Steps",
                "fieldtype": "Text Editor",
                "insert_after": "difficulty_level",
                "description": "Step-by-step instructions for this exercise. Supports rich text formatting (bold, lists, images, etc.).",
            },
        ],
    })
