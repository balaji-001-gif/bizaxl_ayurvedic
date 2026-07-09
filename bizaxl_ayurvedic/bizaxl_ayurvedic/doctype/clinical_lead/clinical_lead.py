# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# ── Master type → doctype / rate-field mapping (shared across helpers) ──
ITEM_TYPE_CONFIG = {
    "Clinical Procedure Template": {"doctype": "Clinical Procedure Template", "rate_fields": ["rate", "price"]},
    "Clinical Procedure": {"doctype": "Clinical Procedure Template", "rate_fields": ["rate", "price"]},
    "Lab Test Template": {"doctype": "Lab Test Template", "rate_fields": ["lab_test_rate", "rate", "price"]},
    "Lab Test": {"doctype": "Lab Test Template", "rate_fields": ["lab_test_rate", "rate", "price"]},
    "Therapy Type": {"doctype": "Therapy Type", "rate_fields": ["rate", "price"]},
    "Therapy": {"doctype": "Therapy Type", "rate_fields": ["rate", "price"]},
}


class ClinicalLead(Document):
    def before_insert(self):
        """Auto-set default lead status."""
        if not self.lead_status:
            self.lead_status = "New"

    def on_update(self):
        """Push lead-scoring signal recompute when key fields change (see ai/lead_scoring.py)."""
        from bizaxl_ayurvedic.ai.lead_scoring import enqueue_score_lead
        enqueue_score_lead(self.name)

# ------------------------------------------------------------------
# Whitelisted helpers used by clinical_lead.js
# ------------------------------------------------------------------

@frappe.whitelist()
def get_treatment_plan_templates():
    return frappe.get_list(
        "Treatment Plan Template",
        filters={"disabled": 0},
        fields=["name", "template_name"],
        order_by="template_name asc",
    )


@frappe.whitelist()
def get_treatment_plan_cost(template_name):
    """Returns pre-rendered HTML cost breakdown for a Treatment Plan Template.
    The client displays this HTML directly in a dialog — no JSON parsing needed."""
    try:
        template = frappe.get_doc("Treatment Plan Template", template_name)
        result = _compute_cost_breakdown(template)
        details, total = result["details"], result["total"]
    except Exception as e:
        frappe.log_error(
            title="Treatment Plan Cost Error",
            message=f"Template: {template_name}\nError: {e}"
        )
        frappe.throw(f"Could not compute cost for '{template_name}': {e}")

    # Build professional HTML (matching the client-side design from the original script)
    plan_name = frappe.utils.escape_html(template.template_name)

    rows_html = ""
    for d in details:
        item_name = frappe.utils.escape_html(str(d.get("name") or ""))
        item_type = frappe.utils.escape_html(str(d.get("type") or ""))
        rows_html += (
            "<tr>"
            f"<td style='padding:12px;border-bottom:1px solid #e2e8f0;'>{item_name}</td>"
            f"<td style='padding:12px;border-bottom:1px solid #e2e8f0;'>{item_type}</td>"
            f"<td style='padding:12px;text-align:center;border-bottom:1px solid #e2e8f0;'>{d['qty']}</td>"
            f"<td style='padding:12px;text-align:right;border-bottom:1px solid #e2e8f0;'>{frappe.utils.fmt_money(d['rate'])}</td>"
            f"<td style='padding:12px;text-align:right;border-bottom:1px solid #e2e8f0;'>{frappe.utils.fmt_money(d['amount'])}</td>"
            "</tr>"
        )

    if not rows_html:
        rows_html = "<tr><td colspan='5' style='text-align:center;padding:30px;'>No billable items found</td></tr>"

    return (
        "<div style='max-height:450px;overflow-y:auto;font-family:Inter,system-ui;'>"
        "<div style='padding:15px 0 5px 0;'>"
        f"<h3 style='margin:0 0 5px 0;color:#003960;font-weight:600;'>Treatment Plan Cost Summary</h3>"
        f"<p style='color:#2c5f5f;font-size:13px;margin-bottom:15px;'>{plan_name}</p>"
        "</div>"
        "<table style='width:100%;border-collapse:collapse;font-size:13px;border:1px solid #e2e8f0;'>"
        "<thead>"
        "<tr style='background-color:#003960;color:white;'>"
        "<th style='padding:12px;text-align:left;'>Item</th>"
        "<th style='padding:12px;text-align:left;'>Type</th>"
        "<th style='padding:12px;text-align:center;'>Qty</th>"
        "<th style='padding:12px;text-align:right;'>Unit Rate</th>"
        "<th style='padding:12px;text-align:right;'>Amount</th>"
        "</tr>"
        "</thead>"
        f"<tbody>{rows_html}</tbody>"
        "<tfoot>"
        f"<tr style='background-color:#f0fdf4;border-top:2px solid #00f2b4;'>"
        "<td colspan='4' style='padding:12px;text-align:right;font-weight:700;font-size:14px;'>Total</td>"
        f"<td style='padding:12px;text-align:right;font-weight:700;font-size:14px;color:#003960;'>{frappe.utils.fmt_money(total)}</td>"
        "</tr>"
        "</tfoot>"
        "</table>"
        "</div>"
    )


@frappe.whitelist()
def share_treatment_cost_via_whatsapp(template_name, mobile_number):
    """Send treatment plan cost breakdown as a WhatsApp message to a patient/lead.
    Returns a status dict so the front-end can confirm delivery."""
    from bizaxl_ayurvedic.integrations.whatsapp import send_text_message

    template = frappe.get_doc("Treatment Plan Template", template_name)
    cost_result = _compute_cost_breakdown(template)

    store_name = (
        frappe.db.get_single_value("Bizaxl Ayurvedic Settings", "store_name")
        or "Our Clinic"
    )

    lines = [
        f"🏥 *{store_name}* — Treatment Plan Cost Estimate",
        "",
        f"*Plan:* {template.template_name}",
        "",
        "*Cost Breakdown:*",
    ]
    for d in cost_result["details"]:
        lines.append(f"  • {d['name']} ({d['type']}) x{d['qty']} — ₹{d['amount']:,.0f}")

    lines.extend([
        "",
        f"*Estimated Total: ₹{cost_result['total']:,.0f}*",
        "",
        "This is an estimate. Final costs may vary based on consultation. "
        "Please visit us for a detailed discussion.",
        "",
        f"*{store_name}*",
    ])

    message = "\n".join(lines)
    result = send_text_message(mobile_number, message)
    return {"sent": bool(result), "total": cost_result["total"], "mobile": mobile_number}


def populate_plan_rates_from_masters(doc, method=None):
    """DocType Event: Treatment Plan Template -> validate.

    Auto-populates the `plan_rate` field on each item row from the
    linked master doctype (Therapy Type, Clinical Procedure Template,
    Lab Test Template) so the rate is visible in the grid and can be
    customised per item without looking up the master each time.

    Also auto-populates the `rate` field on each drug row from the
    Item master's standard_rate, with a guard to preserve manually
    entered rates.
    """
    for item in getattr(doc, "items", []):
        # Only auto-populate if plan_rate is not already set manually
        if getattr(item, "plan_rate", None):
            continue
        item_type = getattr(item, "item_type", None)
        item_template = getattr(item, "template", None)
        if not item_type or not item_template:
            continue
        config = ITEM_TYPE_CONFIG.get(item_type)
        if not config:
            continue
        master = frappe.db.get_value(
            config["doctype"], item_template, config["rate_fields"], as_dict=True
        )
        if master:
            for f in config["rate_fields"]:
                if master.get(f):
                    item.plan_rate = master.get(f)
                    break

    # Auto-populate drug rates from Item master (skip if already set manually)
    for drug in getattr(doc, "drugs", []):
        if getattr(drug, "rate", None):
            continue  # Preserve manually entered rate
        if not getattr(drug, "drug_code", None):
            continue
        standard_rate = frappe.db.get_value("Item", drug.drug_code, "standard_rate")
        if standard_rate:
            drug.rate = standard_rate


def _compute_cost_breakdown(template):
    """Shared helper — returns a dict with 'details' list and 'total'."""
    details = []
    total = 0

    for item in getattr(template, "items", []):
        item_type = getattr(item, "item_type", None)
        item_template = getattr(item, "template", None)
        qty = getattr(item, "qty", 1) or 1
        # Pick rate from item row (try plan_rate first, then rate),
        # then fall back to master doctype
        rate = getattr(item, "plan_rate", None) or getattr(item, "rate", None) or 0
        if not rate:
            config = ITEM_TYPE_CONFIG.get(item_type)
            if config and item_template:
                master = frappe.db.get_value(config["doctype"], item_template, config["rate_fields"], as_dict=True)
                if master:
                    for f in config["rate_fields"]:
                        if master.get(f):
                            rate = master.get(f)
                            break
        amount = rate * qty
        total += amount
        details.append({"name": item_template, "type": item_type, "qty": qty, "rate": rate, "amount": amount})

    for drug in getattr(template, "drugs", []):
        # Try multiple rate fields. `amount` is intentionally excluded
        # because Drug Prescription's amount = rate * qty, so using it
        # as a unit rate would produce wrong totals.
        drug_rate_fields = ["rate", "price", "unit_price", "unit_rate", "selling_price"]
        rate = 0
        for f in drug_rate_fields:
            val = getattr(drug, f, None)
            if val:
                rate = val
                break
        qty = getattr(drug, "quantity", 1) or 1
        amount = rate * qty
        total += amount
        details.append({"name": drug.drug_code, "type": "Drug Prescription", "qty": qty, "rate": rate, "amount": amount})

    return {"details": details, "total": total}
