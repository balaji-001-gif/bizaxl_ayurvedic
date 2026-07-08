# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Ayurvedic Store Performance Benchmarking
(Gap Analysis Section 2, Item 5 — white-space opportunity)

Computes anonymised percentile rankings across opted-in bizaxl Ayurvedic
Store customers on a handful of KPIs, and emails each store owner a monthly
"How does your store compare?" report. In a single-tenant deployment this
module benchmarks branches/warehouses within the same company instead.
"""
import frappe
from frappe.utils import flt, add_months, getdate

KPIS = ["sales_per_sqft", "top_moving_sku_ratio", "expiry_loss_rate"]


def _company_kpis(company):
    sales = frappe.db.sql(
        """SELECT SUM(base_grand_total) FROM `tabSales Invoice`
           WHERE company=%s AND docstatus=1 AND posting_date >= %s""",
        (company, add_months(getdate(), -1)),
    )[0][0] or 0

    expiry_loss = frappe.db.sql(
        """SELECT SUM(actual_qty * valuation_rate) FROM `tabStock Ledger Entry`
           WHERE company=%s AND voucher_type='Stock Reconciliation'
             AND posting_date >= %s AND actual_qty < 0""",
        (company, add_months(getdate(), -1)),
    )[0][0] or 0

    floor_area = flt(frappe.db.get_value("Company", company, "custom_store_area_sqft") or 1)

    return {
        "sales_per_sqft": flt(sales) / floor_area,
        "expiry_loss_rate": flt(expiry_loss),
    }


def compute_store_benchmarks():
    """Weekly scheduled job. Opt-in via Company.custom_share_benchmark_data = 1"""
    companies = frappe.get_all(
        "Company", filters={"custom_share_benchmark_data": 1}, pluck="name"
    )
    if not companies:
        return

    all_kpis = {c: _company_kpis(c) for c in companies}
    ranked = {}
    for kpi in ["sales_per_sqft", "expiry_loss_rate"]:
        values = sorted(all_kpis.items(), key=lambda kv: kv[1].get(kpi, 0))
        n = max(1, len(values) - 1)
        for rank, (company, _) in enumerate(values):
            percentile = round((rank / n) * 100) if n else 100
            ranked.setdefault(company, {})[kpi] = percentile

    for company, percentiles in ranked.items():
        frappe.cache().hset("bizaxl_ayurvedic:store_benchmark", company, frappe.as_json(percentiles))
        _email_report(company, percentiles)


def _email_report(company, percentiles):
    recipients = frappe.get_all("User", filters={"role_profile_name": "Ayurvedic Store Manager"}, pluck="email")
    if not recipients:
        return
    frappe.sendmail(
        recipients=recipients,
        subject=f"bizaxl Store Intelligence — {company} Monthly Benchmark",
        template=None,
        message=(
            f"<h3>How does your store compare?</h3><ul>"
            + "".join(f"<li>{k}: {v}th percentile</li>" for k, v in percentiles.items())
            + "</ul>"
        ),
    )
