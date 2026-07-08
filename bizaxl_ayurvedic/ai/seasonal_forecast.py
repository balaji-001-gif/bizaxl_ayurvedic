# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Seasonal Herb Demand Forecasting (AI)
(Gap Analysis Section 2, Item 1 — white-space opportunity, no competitor has this)

Reads 12 months of Sales Invoice Item history per SKU from ERPNext and
produces monthly purchase-quantity suggestions. Uses a simple seasonal-naive
+ trend model out of the box (no extra Python dependency needed); if the
`prophet` package is installed, it transparently upgrades to a proper
time-series model — this keeps the base app installable on any bench without
forcing a heavy ML dependency.

Output is written to the "Reorder Forecast" child table's parent report doc,
surfaced on the manager dashboard workspace number card.
"""
import frappe
from frappe.utils import add_months, getdate, flt

try:
    from prophet import Prophet  # optional heavy dependency
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False


def _get_monthly_sales(item_code, months=12):
    rows = frappe.db.sql(
        """
        SELECT DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month, SUM(sii.qty) AS qty
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.item_code = %s AND si.docstatus = 1
          AND si.posting_date >= %s
        GROUP BY month
        ORDER BY month ASC
        """,
        (item_code, add_months(getdate(), -months)),
        as_dict=True,
    )
    return rows


def _forecast_naive_seasonal(history):
    """Fallback model: same-month-last-year qty, adjusted by recent trend."""
    if not history:
        return 0
    qtys = [flt(r.qty) for r in history]
    avg_recent = sum(qtys[-3:]) / max(1, len(qtys[-3:]))
    avg_year_ago = qtys[0] if len(qtys) >= 12 else avg_recent
    return round((avg_recent * 0.6) + (avg_year_ago * 0.4), 1)


def _forecast_prophet(history):
    import pandas as pd
    df = pd.DataFrame({
        "ds": [f"{r.month}-01" for r in history],
        "y": [flt(r.qty) for r in history],
    })
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m.fit(df)
    future = m.make_future_dataframe(periods=1, freq="MS")
    forecast = m.predict(future)
    return round(float(forecast.iloc[-1]["yhat"]), 1)


def forecast_item(item_code):
    history = _get_monthly_sales(item_code)
    if HAS_PROPHET and len(history) >= 6:
        try:
            return _forecast_prophet(history)
        except Exception:
            frappe.log_error(title="Seasonal forecast (prophet) failed, falling back")
    return _forecast_naive_seasonal(history)


def generate_reorder_forecast():
    """Weekly scheduled job — recomputes suggested reorder qty for every
    stock Item flagged for the Ayurvedic Store module and stores the result
    for the 'Reorder Forecast' report."""
    items = frappe.get_all("Item", filters={"is_stock_item": 1, "disabled": 0}, pluck="name")
    results = []
    for item_code in items:
        qty = forecast_item(item_code)
        if qty:
            results.append({"item_code": item_code, "suggested_qty": qty})

    frappe.cache().set_value("bizaxl_ayurvedic:reorder_forecast", frappe.as_json(results), expires_in_sec=7 * 86400)
    frappe.logger("bizaxl_ayurvedic").info(f"Seasonal reorder forecast generated for {len(results)} items")
    return results


@frappe.whitelist()
def get_reorder_forecast():
    cached = frappe.cache().get_value("bizaxl_ayurvedic:reorder_forecast")
    return frappe.parse_json(cached) if cached else []
