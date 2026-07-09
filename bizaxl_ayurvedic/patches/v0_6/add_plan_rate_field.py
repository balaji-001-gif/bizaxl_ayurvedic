# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

"""
Patch: v0.6 — Add plan_rate custom field on Treatment Plan Item child table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The standard Treatment Plan Item child table (from Frappe Healthcare) only
has a `rate` field. This patch adds a `plan_rate` Currency field so
practitioners can set item-level pricing directly on the Treatment Plan
Template — the cost breakdown logic already tries `plan_rate` first.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Treatment Plan Item": [
            {
                "fieldname": "plan_rate",
                "label": "Plan Rate",
                "fieldtype": "Currency",
                "insert_after": "rate",
                "description": "Custom rate for this treatment plan item. If set, overrides the master rate.",
                "in_list_view": 1,
            },
        ],
    }
    create_custom_fields(custom_fields, ignore_validate=True)
    frappe.db.commit()
