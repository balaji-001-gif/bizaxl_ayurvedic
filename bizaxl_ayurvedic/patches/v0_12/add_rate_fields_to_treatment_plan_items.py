# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds a **Rate** (Currency) custom field to the Items child table of Treatment
Plan Template so rates are visible and editable on the form.

The child table may be named "Treatment Plan Template Item" or "Treatment Plan
Item" depending on the Frappe Healthcare version — the patch handles both.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    CANDIDATES = ["Treatment Plan Template Item", "Treatment Plan Item"]

    for dt in CANDIDATES:
        if not frappe.db.exists("DocType", dt):
            continue
        if frappe.get_meta(dt).has_field("rate"):
            continue

        create_custom_fields({
            dt: [
                {
                    "fieldname": "rate",
                    "label": "Rate",
                    "fieldtype": "Currency",
                    "insert_after": "qty",
                    "description": "Unit rate auto-fetched from the master doctype. Override manually if needed.",
                },
            ],
        })
