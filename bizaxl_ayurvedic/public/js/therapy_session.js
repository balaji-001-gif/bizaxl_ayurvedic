// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Therapy Session" DocType (loaded via
// hooks.doctype_js) with auto-fetch of exercise steps from Exercise Type.
// When a user selects an Exercise Type in the exercises child table,
// the exercise_steps HTML is fetched and set on the row directly,
// so it displays inline inside the grid.

frappe.ui.form.on("Therapy Session", {
	refresh(frm) {
		fetch_all_exercise_steps(frm);
	},
});

frappe.ui.form.on("Therapy Session Exercise", {
	exercise_type(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (!row.exercise_type) {
			frappe.model.set_value(cdt, cdn, "exercise_steps", "");
			return;
		}

		// Show loading indicator in the field
		frappe.model.set_value(cdt, cdn, "exercise_steps",
			'<div style="padding:8px; color:#6c757d;"><i class="fa fa-spinner fa-spin"></i> Loading steps...</div>');

		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Exercise Type",
				filters: { name: row.exercise_type },
				fieldname: "exercise_steps",
			},
			callback(r) {
				let steps = "";
				if (r.message && r.message.exercise_steps) {
					steps = r.message.exercise_steps;
				}
				frappe.model.set_value(cdt, cdn, "exercise_steps", steps);
				frm.refresh_field("exercises");
			},
		});
	},
});

function fetch_all_exercise_steps(frm) {
	if (!frm.doc.exercises) return;

	frm.doc.exercises.forEach((row) => {
		// Only fetch if exercise_type is set but exercise_steps is empty
		if (row.exercise_type && !row.exercise_steps) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Exercise Type",
					filters: { name: row.exercise_type },
					fieldname: "exercise_steps",
				},
				callback(r) {
					if (r.message && r.message.exercise_steps && row.name) {
						frappe.model.set_value(
							"Therapy Session Exercise",
							row.name,
							"exercise_steps",
							r.message.exercise_steps
						);
					}
				},
			});
		}
	});
}
