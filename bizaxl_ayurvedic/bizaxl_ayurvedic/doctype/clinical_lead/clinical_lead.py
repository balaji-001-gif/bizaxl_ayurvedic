# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


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
    """Builds an HTML cost breakdown for a Treatment Plan Template, combining
    procedure/therapy/lab-test rate lookups with child-table drug rates.
    Ported from the client's original 'Show treatment cost' Client Script."""
    template = frappe.get_doc("Treatment Plan Template", template_name)
    result = _compute_cost_breakdown(template)
    details, total = result["details"], result["total"]

    rows_html = "".join(
        f"<tr><td>{d['name']}</td><td>{d['type']}</td><td>{d['qty']}</td>"
        f"<td>{frappe.utils.fmt_money(d['rate'])}</td><td>{frappe.utils.fmt_money(d['amount'])}</td></tr>"
        for d in details
    ) or "<tr><td colspan='5'>No billable items found</td></tr>"

    return (
        f"<h4>{frappe.utils.escape_html(template.template_name)}</h4>"
        "<table class='table table-bordered'><thead><tr>"
        "<th>Item</th><th>Type</th><th>Qty</th><th>Unit Rate</th><th>Amount</th>"
        f"</tr></thead><tbody>{rows_html}</tbody>"
        f"<tfoot><tr><th colspan='4'>Total</th><th>{frappe.utils.fmt_money(total)}</th></tr></tfoot></table>"
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


def _compute_cost_breakdown(template):
    """Shared helper — returns a dict with 'details' list and 'total'."""
    item_type_config = {
        "Clinical Procedure Template": {"doctype": "Clinical Procedure Template", "rate_fields": ["rate", "price"]},
        "Clinical Procedure": {"doctype": "Clinical Procedure Template", "rate_fields": ["rate", "price"]},
        "Lab Test Template": {"doctype": "Lab Test Template", "rate_fields": ["lab_test_rate", "rate", "price"]},
        "Lab Test": {"doctype": "Lab Test Template", "rate_fields": ["lab_test_rate", "rate", "price"]},
        "Therapy Type": {"doctype": "Therapy Type", "rate_fields": ["rate", "price"]},
        "Therapy": {"doctype": "Therapy Type", "rate_fields": ["rate", "price"]},
    }

    details = []
    total = 0

    for item in getattr(template, "items", []):
        item_type = getattr(item, "item_type", None)
        item_template = getattr(item, "template", None)
        qty = getattr(item, "qty", 1) or 1
        config = item_type_config.get(item_type)
        rate = 0
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
        rate = getattr(drug, "rate", 0) or 0
        qty = getattr(drug, "quantity", 1) or 1
        amount = rate * qty
        total += amount
        details.append({"name": drug.drug_code, "type": "Drug Prescription", "qty": qty, "rate": rate, "amount": amount})

    return {"details": details, "total": total}
