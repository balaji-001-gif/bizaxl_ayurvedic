# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

"""
Patch: v0.7 — Remove plan_rate custom field from Treatment Plan Item child table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The v0.6 patch added a `plan_rate` Currency field on the child table so
practitioners could set item-level pricing. However, the user has decided
this field is unnecessary — the Clinical Lead cost breakdown now always
fetches the rate directly from the master doctype (Therapy Type, Clinical
Procedure Template, Lab Test Template) without needing a stored field.

This patch removes the custom field from both possible child table names.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import delete_custom_field


def execute():
    doctype_names = ["Treatment Plan Template Item", "Treatment Plan Item"]

    for doctype in doctype_names:
        if frappe.db.exists("DocType", doctype):
            try:
                delete_custom_field(doctype, "plan_rate")
                frappe.logger("bizaxl_ayurvedic").info(
                    f"v0.7 patch: deleted plan_rate field from {doctype}"
                )
            except Exception as e:
                frappe.logger("bizaxl_ayurvedic").info(
                    f"v0.7 patch: plan_rate not found on {doctype} ({e})"
                )

    frappe.db.commit()
