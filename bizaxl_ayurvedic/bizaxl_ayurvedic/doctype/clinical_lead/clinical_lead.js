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

		frm.add_custom_button(__("Treatment Plan Cost"), () => {
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
						primary_action_label: __("Show Cost Breakdown"),
						primary_action(values) {
							dlg.hide();
							frappe.call({
								method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.get_treatment_plan_cost",
								args: { template_name: values.template },
								callback(r) {
									let cost_html = r.message || "<p>No cost data</p>";
									let cost_dlg = new frappe.ui.Dialog({
										title: __("Cost Breakdown"),
										size: "extra-large",
										fields: [{ fieldtype: "HTML", fieldname: "cost_html" }],
										primary_action_label: __("📤 Share on WhatsApp"),
										primary_action() {
											cost_dlg.hide();
											frappe.call({
												method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.share_treatment_cost_via_whatsapp",
												args: {
													template_name: values.template,
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
										},
									});
									cost_dlg.fields_dict.cost_html.$wrapper.html(cost_html);
									cost_dlg.show();
								},
							});
						},
					});
					dlg.show();
				},
			});
		}, __("Treatment Plans"));
	},
});
