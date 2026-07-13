frappe.ui.form.on("Treatment Record", {
	refresh(frm) {
		// Compare Before/After button
		if (frm.doc.photos && frm.doc.photos.length >= 2) {
			frm.add_custom_button(__("Compare Before / After"), () => {
				frappe.call({
					method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.treatment_record.treatment_record.get_compare_gallery_html",
					args: { docname: frm.doc.name },
					callback(r) {
						frappe.msgprint({ title: __("Before / After Comparison"), message: r.message, wide: true });
					},
				});
			});
		}
	},
	treatment_package(frm) {
		if (frm.doc.treatment_package) {
			fetch_exercises(frm);
		} else {
			frm.clear_table("exercise_details");
			frm.refresh_field("exercise_details");
		}
	},
});

function fetch_exercises(frm) {
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Therapy Session",
			name: frm.doc.treatment_package,
		},
		callback(r) {
			let session = r.message;
			if (!session) {
				frappe.msgprint(__("Therapy Session not found. Please select a valid session."));
				return;
			}
			frm.clear_table("exercise_details");
			if (session.exercises && session.exercises.length > 0) {
				session.exercises.forEach((ex) => {
					let row = frm.add_child("exercise_details");
					row.exercise_type = ex.exercise_type;
					row.difficulty_level = ex.difficulty_level;
					row.counts_target = ex.counts_target;
					row.counts_completed = ex.counts_completed;
					row.assistance_level = ex.assistance_level;
				});
			}
			frm.refresh_field("exercise_details");
		},
	});
}
