# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds a **Rate** (Currency) custom field to the Drug Prescription child table
so medicine rates can be auto-fetched from the Item master and shown/edited
in forms that use this child table (e.g. Treatment Plan Template → Drugs,
Patient Encounter → Drug Prescription).

If the standard Frappe Healthcare Drug Prescription already has a `rate` field
(built-in), this patch safely skips.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    CHILD = "Drug Prescription"

    if not frappe.db.exists("DocType", CHILD):
        return

    if frappe.get_meta(CHILD).has_field("rate"):
        return

    create_custom_fields({
        CHILD: [
            {
                "fieldname": "rate",
                "label": "Rate",
                "fieldtype": "Currency",
                "insert_after": "qty",
                "in_list_view": 1,
                "description": "Unit rate auto-fetched from Item master. Override manually if needed.",
            },
        ],
    })
