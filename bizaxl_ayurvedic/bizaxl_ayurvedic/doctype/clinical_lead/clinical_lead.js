// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt

frappe.ui.form.on("Clinical Lead", {
	refresh(frm) {
		// ── Patient navigation & creation ──
		if (!frm.is_new()) {
			if (frm.doc.patient) {
				// Patient already linked — show View button to open it
				frm.add_custom_button(__("View Patient"), () => {
					frappe.set_route("Form", "Patient", frm.doc.patient);
				});
			} else if (frm.doc.lead_status === "Converted") {
				// Lead manually set to Converted but no patient linked yet — show Create button
				frm.add_custom_button(__("Create Patient"), () => {
					frappe.new_doc("Patient", {
						patient_name: frm.doc.lead_name,
						mobile: frm.doc.mobile_number,
						sex: frm.doc.gender,
						email: frm.doc.email,
					});
				});
			}
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
	// Unified flow: one button always opens the plan selector, then shows cost
	frm.add_custom_button(__("View Treatment Plan Cost"), () => {
		pick_template_and_show_cost(frm);
	}, __("Treatment Plans"));
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
			let cost_html = r.message || "<p>No cost data available.</p>";
			let plan_name = template_name;
			let cost_dlg = new frappe.ui.Dialog({
				title: `📋 ${plan_name}`,
				size: "large",
				fields: [{ fieldtype: "HTML", fieldname: "cost_html" }],
				primary_action_label: __("📤 Share on WhatsApp"),
				primary_action() {
					cost_dlg.hide();
					share_cost_via_whatsapp(frm, template_name);
				},
			});
			cost_dlg.fields_dict.cost_html.$wrapper.html(cost_html);
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
