// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Patient Appointment" DocType (loaded via
// hooks.doctype_js) with auto-generated OPD tokens and a live Token Queue view.

frappe.ui.form.on("Patient Appointment", {
	after_save(frm) {
		if (frm.token_created) return;
		const date = frm.doc.appointment_date;
		const doctor = frm.doc.practitioner;
		if (!date || !doctor) return;
		frm.token_created = true;

		frappe.call({
			method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.create_next_token",
			args: { appointment: frm.doc.name, date, practitioner: doctor },
			callback(r) {
				if (r.message) {
					frappe.show_alert({ message: __("Token Submitted: {0}", [r.message]), indicator: "green" });
				}
			},
		});
	},

	refresh(frm) {
		frm.add_custom_button(__("Token Queue"), () => {
			const practitioner = frm.doc.healthcare_practitioner || frm.doc.practitioner;
			if (!practitioner) {
				frappe.msgprint(__("Healthcare Practitioner missing"));
				return;
			}
			frappe.call({
				method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.get_token_queue_html",
				args: { practitioner },
				callback(r) {
					let d = new frappe.ui.Dialog({
						title: __("Healthcare Token Queue"),
						size: "extra-large",
						fields: [{ fieldtype: "HTML", fieldname: "queue_html" }],
					});
					d.fields_dict.queue_html.$wrapper.html(r.message);
					d.show();
				},
			});
		}, __("View"));
	},
});
