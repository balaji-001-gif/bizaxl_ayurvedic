# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds an **Exercise Steps** field to the standard **Exercise Type** doctype
(from Frappe Healthcare) so therapists can document step-by-step instructions
with rich formatting (HTML).

When an Exercise Type is selected in a Therapy Session, the exercise steps
HTML is fetched and displayed inline for reference.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Exercise Type": [
            {
                "fieldname": "section_break_exercise_steps",
                "fieldtype": "Section Break",
                "label": "Exercise Steps",
                "insert_after": "difficulty_level",
            },
            {
                "fieldname": "exercise_steps",
                "label": "Exercise Steps",
                "fieldtype": "Text Editor",
                "insert_after": "section_break_exercise_steps",
                "description": "Step-by-step instructions for this exercise. Supports rich text formatting (bold, lists, images, etc.).",
            },
        ],
    })
