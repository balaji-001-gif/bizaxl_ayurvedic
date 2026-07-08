// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Patient Encounter" DocType (loaded via
// hooks.doctype_js) with a one-click "Create Prescription" button that
// spins up a Healthcare Medication Prescription pre-filled from the
// consultation's drug prescriptions.

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
	},
});
