# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DietPlan(Document):
    pass

# ------------------------------------------------------------------
# Whitelisted helpers used by diet_plan.js
# ------------------------------------------------------------------

_MEAL_TIME_SLOTS = {
    "Morning": "08:00:00",
    "Afternoon": "13:00:00",
    "Evening": "17:00:00",
    "Night": "20:00:00",
}


@frappe.whitelist()
def get_template_rows(template, start_date=None):
    """Returns Diet Plan Meal Schedule rows fetched from a Diet Template,
    auto-assigning a default scheduled_time per meal slot."""
    tmpl = frappe.get_doc("Diet Template", template)
    rows = []
    for item in tmpl.items:
        rows.append({
            "meal_type": item.meal_time,
            "menu_item": item.food_item,
            "remarks": item.instruction,
            "scheduled_time": _MEAL_TIME_SLOTS.get(item.meal_time),
            "date": start_date or frappe.utils.today(),
        })
    return rows


@frappe.whitelist()
def create_meal_logs(docname):
    """Creates a Meal Preparation Log for every meal-schedule row that doesn't
    already have one. Skips duplicates. Ported from the client's original
    'To create a Meal log in diet plan' Client Script."""
    plan = frappe.get_doc("Diet Plan", docname)
    created, skipped = 0, 0

    for row in plan.table_mcva:
        exists = frappe.db.exists("Meal Preparation Log", {
            "diet_plan": plan.name,
            "patient": plan.patient,
            "meal_time": row.meal_type,
            "food_items": row.menu_item,
        })
        if exists:
            skipped += 1
            continue

        frappe.get_doc({
            "doctype": "Meal Preparation Log",
            "date": frappe.utils.today(),
            "diet_plan": plan.name,
            "patient": plan.patient,
            "wardbed": plan.wardbed,
            "meal_time": row.meal_type,
            "food_items": row.menu_item,
            "status": "Draft",
        }).insert(ignore_permissions=True)
        created += 1

    return f"Created: {created}, Skipped (already exists): {skipped}"
