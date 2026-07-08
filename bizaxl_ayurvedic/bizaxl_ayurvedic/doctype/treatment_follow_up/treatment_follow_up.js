frappe.ui.form.on("Treatment Follow-Up", {
	refresh(frm) {
		// placeholder for future dashboard buttons
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
