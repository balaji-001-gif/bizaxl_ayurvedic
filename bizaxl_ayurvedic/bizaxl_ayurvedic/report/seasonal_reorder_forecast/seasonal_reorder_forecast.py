# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""Script Report surfacing the AI Seasonal Herb Demand Forecast (see
bizaxl_ayurvedic/ai/seasonal_forecast.py) as a manager-facing Reorder Forecast —
Gap Analysis Section 2, Item 1 (white-space opportunity)."""
import frappe
from bizaxl_ayurvedic.ai.seasonal_forecast import get_reorder_forecast


def execute(filters=None):
    columns = [
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 200},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": "Suggested Reorder Qty (Next Month)", "fieldname": "suggested_qty", "fieldtype": "Float", "width": 220},
    ]

    data = get_reorder_forecast()
    for row in data:
        row["item_name"] = frappe.db.get_value("Item", row["item_code"], "item_name")

    data.sort(key=lambda r: r["suggested_qty"], reverse=True)
    return columns, data
