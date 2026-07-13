# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds a **Token Number** (Int) custom field to the **Patient Appointment** doctype.

This field stores a daily auto-incrementing token number (starting at 1 each day)
so staff can easily track and reference appointments by their token for the day.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Patient Appointment": [
            {
                "fieldname": "token_number",
                "label": "Token Number",
                "fieldtype": "Int",
                "insert_after": "appointment_date",
                "read_only": 1,
                "no_copy": 1,
                "description": "Daily token number auto-assigned sequentially (resets to 1 each day).",
            },
        ],
    })
