# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

"""
Patch: v0.6 — Add plan_rate custom field on Treatment Plan Item child table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The standard Treatment Plan Template Item child table (from Frappe Health)
only has a `rate` field. This patch adds a `plan_rate` Currency field so
practitioners can set item-level pricing directly on the Treatment Plan
Template — the cost breakdown logic already tries `plan_rate` first.

Note: some installations name this child table "Treatment Plan Item" while
others (Frappe Health app) name it "Treatment Plan Template Item". The
patch tries the latter first (the Frappe Health v15 name), and falls back
to the former if that fails.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # Try the Frappe Health app name first, fall back to ERPNext healthcare name
    doctype_names = ["Treatment Plan Template Item", "Treatment Plan Item"]

    for doctype in doctype_names:
        if frappe.db.exists("DocType", doctype):
            custom_fields = {
                doctype: [
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
            frappe.logger("bizaxl_ayurvedic").info(
                f"v0.6 patch: added plan_rate field on {doctype}"
            )
            break
    else:
        frappe.logger("bizaxl_ayurvedic").warning(
            "v0.6 patch: neither 'Treatment Plan Template Item' nor 'Treatment Plan Item' "
            "DocType found. Skipping plan_rate field creation."
        )

    frappe.db.commit()
