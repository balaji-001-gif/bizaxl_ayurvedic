frappe.ui.form.on("Treatment Follow-Up", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			// Show Update button on submitted docs — like Token Counter pattern
			frm.page.set_primary_action(__("Update & Recalculate"), () => {
				frm.save("Update");
			});
		}
	},
	follow_up_after_days(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.follow_up_after_days) {
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(
				__("Follow-up visits will be recalculated on save based on the new interval.")
			);
		}
	},
	after_save(frm) {
		if (frm.doc.docstatus === 1) {
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(
				__("Follow-up visits recalculated. Review and submit when ready.")
			);
			frm.refresh_field("follow_up_visits");
		}
	},
});

frappe.ui.form.on("Follow-up Visits", {
	follow_up_days(frm, cdt, cdn) {
		update_next_date(frm, cdt, cdn);
	},
	visit_date(frm, cdt, cdn) {
		update_next_date(frm, cdt, cdn);
	},
	after_insert(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (row.visit_date) return;
		let rows = frm.doc.follow_up_visits || [];
		let idx = rows.findIndex((r) => r.name === row.name);
		if (idx > 0 && rows[idx - 1].next_follow_up_date) {
			frappe.model.set_value(cdt, cdn, "visit_date", rows[idx - 1].next_follow_up_date);
		}
	},
});

function update_next_date(frm, cdt, cdn) {
	let row = frappe.get_doc(cdt, cdn);
	if (row.visit_date && row.follow_up_days && !isNaN(row.follow_up_days)) {
		let visit_date = frappe.datetime.str_to_obj(row.visit_date);
		let next_date = new Date(visit_date);
		next_date.setDate(visit_date.getDate() + parseInt(row.follow_up_days));
		frappe.model.set_value(cdt, cdn, "next_follow_up_date", frappe.datetime.obj_to_str(next_date));
	}
}
