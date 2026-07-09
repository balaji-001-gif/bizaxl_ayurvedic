// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Patient Encounter" DocType (loaded via
// hooks.doctype_js) with a one-click "Create Prescription" button and
// "Treatment Plan Cost" — show / WhatsApp cost breakdown to patients.

frappe.ui.form.on("Patient Encounter", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		frm.add_custom_button(__("Create Prescription"), () => {
			let meds = (frm.doc.drug_prescription || []).map((d) => ({
				doctype: "Healthcare Prescription Item",
				medication: d.drug_code || "",
				dosage: d.dosage || "",
				frequency: d.dosage || "",
				duration: d.period || "",
				quantity: d.qty || 0,
				instructions: d.comment || "",
			}));
			frappe.new_doc("Healthcare Medication Prescription", {
				patient: frm.doc.patient,
				encounter: frm.doc.name,
				practitioner: frm.doc.practitioner,
				prescription_date: frappe.datetime.now_datetime(),
				medications: meds,
			});
		}, __("Create"));

		// ── Treatment Plan Cost — Show & Share ──
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
						title: __("Treatment Plan Cost — Share with Patient"),
						fields: [{
							fieldname: "template",
							label: __("Select Treatment Plan"),
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
											share_cost_via_whatsapp(frm, values.template);
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
		}, __("Plans"));
	},
});

function share_cost_via_whatsapp(frm, template_name) {
	// Get patient mobile from the encounter's linked Patient
	frappe.db.get_value("Patient", frm.doc.patient, "mobile", (r) => {
		let mobile = r ? r.mobile : "";
		if (!mobile) {
			frappe.msgprint(__("Patient has no mobile number on file."));
			return;
		}
		frappe.call({
			method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.share_treatment_cost_via_whatsapp",
			args: { template_name, mobile_number: mobile },
			callback(res) {
				if (res.message && res.message.sent) {
					frappe.show_alert({
						message: `✅ Cost estimate (₹${res.message.total.toLocaleString()}) sent to ${mobile}`,
						indicator: "green",
					});
				} else {
					frappe.msgprint(__("Failed to send WhatsApp. Please check WhatsApp settings."));
				}
			},
		});
	});
}
