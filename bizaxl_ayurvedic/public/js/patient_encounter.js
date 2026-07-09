// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Patient Encounter" DocType (loaded via
// hooks.doctype_js) with:
//   - One-click "Create Prescription"
//   - "Treatment Plan Cost" — view / WhatsApp cost breakdown to patients
//   - Auto-uses the linked treatment_plan_template if available

frappe.ui.form.on("Patient Encounter", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		// ── Create Prescription ──
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

		frm.add_custom_button(__("Share Cost on WhatsApp"), () => {
			frappe.db.get_value("Patient", frm.doc.patient, "mobile", (r) => {
				let mobile = r ? r.mobile : "";
				if (!mobile) {
					frappe.msgprint(__("Patient has no mobile number on file."));
					return;
				}
				frappe.call({
					method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.share_treatment_cost_via_whatsapp",
					args: { template_name: frm.doc.treatment_plan_template, mobile_number: mobile },
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
		}, __("Treatment Plans"));
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
			let cost_html = r.message || "<p>No cost data</p>";

			// Build plan name and total from the HTML
			let plan_name = template_name;
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
			cost_dlg.fields_dict.cost_html.$wrapper.html(cost_html);
			cost_dlg.show();
		},
	});
}

function share_cost_via_whatsapp(frm, template_name) {
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
