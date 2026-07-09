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


def execute():
    doctype_names = ["Treatment Plan Template Item", "Treatment Plan Item"]

    for doctype in doctype_names:
        if frappe.db.exists("DocType", doctype):
            custom_field_name = f"{doctype}-plan_rate"
            if frappe.db.exists("Custom Field", custom_field_name):
                frappe.delete_doc(
                    "Custom Field",
                    custom_field_name,
                    ignore_permissions=True,
                    force=True,
                )
                frappe.logger("bizaxl_ayurvedic").info(
                    f"v0.7 patch: deleted plan_rate field from {doctype}"
                )

    frappe.db.commit()
