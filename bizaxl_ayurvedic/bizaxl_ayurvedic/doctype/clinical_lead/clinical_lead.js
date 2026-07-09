// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt

frappe.ui.form.on("Clinical Lead", {
	refresh(frm) {
		// Convert lead to Patient in one click
		if (!frm.doc.patient && !frm.is_new()) {
			frm.add_custom_button(__("Create Patient"), () => {
				frappe.new_doc("Patient", {
					patient_name: frm.doc.lead_name,
					mobile: frm.doc.mobile_number,
					sex: frm.doc.gender,
				}).then(() => {
					frappe.msgprint(__("Complete the Patient record, then link it back on this Lead."));
				});
			});
		}

		// AI: show lead score / next-best-action badge if available
		if (frm.doc.__onload && frm.doc.__onload.lead_score !== undefined) {
			frm.dashboard.add_indicator(
				__("AI Lead Score: {0}", [frm.doc.__onload.lead_score]),
				frm.doc.__onload.lead_score >= 70 ? "green" : frm.doc.__onload.lead_score >= 40 ? "orange" : "red"
			);
		}

		// ── Treatment Plan Cost — Show & Share ──
		show_treatment_plan_buttons(frm);
	},
});

function show_treatment_plan_buttons(frm) {
	let has_plan = frm.doc.treatment_plan_template;

	if (has_plan) {
		// One-click View Cost — uses the saved plan template directly
		frm.add_custom_button(__("View Treatment Plan Cost"), () => {
			show_cost_dialog(frm, frm.doc.treatment_plan_template);
		}, __("Treatment Plans"));

		if (frm.doc.mobile_number) {
			frm.add_custom_button(__("Share Cost on WhatsApp"), () => {
				frappe.call({
					method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.share_treatment_cost_via_whatsapp",
					args: {
						template_name: frm.doc.treatment_plan_template,
						mobile_number: frm.doc.mobile_number,
					},
					callback(res) {
						if (res.message && res.message.sent) {
							frappe.show_alert({
								message: `✅ Cost estimate (₹${res.message.total.toLocaleString()}) sent to ${res.message.mobile}`,
								indicator: "green",
							});
						} else {
							frappe.msgprint(__("Failed to send WhatsApp. Please check WhatsApp settings."));
						}
					},
				});
			}, __("Treatment Plans"));
		}
	} else {
		// No plan linked — prompt to select one
		frm.add_custom_button(__("Select Treatment Plan"), () => {
			pick_template_and_show_cost(frm);
		}, __("Treatment Plans"));
	}
}

function pick_template_and_show_cost(frm) {
	frappe.call({
		method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.get_treatment_plan_templates",
		callback(res) {
			const templates = res.message || [];
			if (!templates.length) {
				frappe.msgprint(__("No active treatment plan templates found."));
				return;
			}
			let dlg = new frappe.ui.Dialog({
				title: __("Select Treatment Plan"),
				fields: [{
					fieldname: "template",
					label: __("Treatment Plan"),
					fieldtype: "Select",
					options: templates.map((t) => t.name).join("\n"),
					reqd: 1,
				}],
				primary_action_label: __("Show Cost"),
				primary_action(values) {
					dlg.hide();
					show_cost_dialog(frm, values.template);
				},
			});
			dlg.show();
		},
	});
}

function show_cost_dialog(frm, template_name) {
	frappe.call({
		method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.get_treatment_plan_cost",
		args: { template_name },
		callback(r) {
			if (!r.message) {
				frappe.msgprint(__("No cost data available."));
				return;
			}
			const data = r.message;
			const details = data.details || [];
			const total = data.total || 0;
			const plan_name = data.template_name || template_name;

			let rows = "";
			details.forEach(d => {
				rows += `<tr>
					<td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">${d.name}</td>
					<td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">${d.type}</td>
					<td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">${d.qty}</td>
					<td style="padding: 12px; text-align: right; border-bottom: 1px solid #e2e8f0;">${frappe.utils.format_currency(d.rate, "INR")}</td>
					<td style="padding: 12px; text-align: right; border-bottom: 1px solid #e2e8f0;">${frappe.utils.format_currency(d.amount, "INR")}</td>
				</tr>`;
			});

			let html = `
			<div style="max-height: 450px; overflow-y: auto; font-family: 'Inter', system-ui;">
				<div style="padding: 15px 0 5px 0;">
					<h3 style="margin: 0 0 5px 0; color: #003960; font-weight: 600;">Treatment Plan Cost Summary</h3>
					<p style="color: #2c5f5f; font-size: 13px; margin-bottom: 15px;">${plan_name}</p>
				</div>
				<table style="width: 100%; border-collapse: collapse; font-size: 13px; border: 1px solid #e2e8f0;">
					<thead>
						<tr style="background-color: #003960; color: white;">
							<th style="padding: 12px; text-align: left;">Item</th>
							<th style="padding: 12px; text-align: left;">Type</th>
							<th style="padding: 12px; text-align: center;">Qty</th>
							<th style="padding: 12px; text-align: right;">Unit Rate (₹)</th>
							<th style="padding: 12px; text-align: right;">Amount (₹)</th>
						</tr>
					</thead>
					<tbody>
						${rows || '<tr><td colspan="5" style="text-align:center; padding:30px;">No billable items found</td></tr>'}
					</tbody>
					<tfoot>
						<tr style="background-color: #f0fdf4; border-top: 2px solid #00f2b4;">
							<td colspan="4" style="padding: 12px; text-align: right; font-weight: 700; font-size: 14px;">Total</td>
							<td style="padding: 12px; text-align: right; font-weight: 700; font-size: 14px; color: #003960;">${frappe.utils.format_currency(total, "INR")}</td>
						</tr>
					</tfoot>
				</table>
			</div>
			`;

			let cost_dlg = new frappe.ui.Dialog({
				title: `📋 ${plan_name}`,
				size: "extra-large",
				fields: [{ fieldtype: "HTML", fieldname: "cost_html" }],
				primary_action_label: __("📤 Share on WhatsApp"),
				primary_action() {
					cost_dlg.hide();
					share_cost_via_whatsapp(frm, template_name);
				},
			});
			cost_dlg.fields_dict.cost_html.$wrapper.html(html);
			cost_dlg.show();
		},
	});
}

function share_cost_via_whatsapp(frm, template_name) {
	if (!frm.doc.mobile_number) {
		frappe.msgprint(__("Lead has no mobile number."));
		return;
	}
	frappe.call({
		method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.share_treatment_cost_via_whatsapp",
		args: { template_name, mobile_number: frm.doc.mobile_number },
		callback(res) {
			if (res.message && res.message.sent) {
				frappe.show_alert({
					message: `✅ Cost estimate (₹${res.message.total.toLocaleString()}) sent to ${res.message.mobile}`,
					indicator: "green",
				});
			} else {
				frappe.msgprint(__("Failed to send WhatsApp. Please check WhatsApp settings."));
			}
		},
	});
}
