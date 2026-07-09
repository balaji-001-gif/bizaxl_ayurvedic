// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Treatment Plan Template" DocType (loaded via
// hooks.doctype_js). When a user selects a Therapy Type, Clinical Procedure,
// or Lab Test Template in the Items grid, this handler automatically fetches
// the rate from the master doctype and populates the plan_rate field.

// ── Item row: auto-fetch rate from master doctype into plan_rate ──
// The child table doctype may be "Treatment Plan Template Item" or
// "Treatment Plan Item" depending on the Frappe Health version.
["Treatment Plan Template Item", "Treatment Plan Item"].forEach((dt) => {
	frappe.ui.form.on(dt, {
		template(frm, cdt, cdn) {
			const row = frappe.get_doc(cdt, cdn);
			if (!row.template || !row.item_type) return;

			// Map item_type → master doctype and rate field
			const config = {
				"Therapy Type":              { doctype: "Therapy Type",              field: "rate" },
				"Therapy":                   { doctype: "Therapy Type",              field: "rate" },
				"Clinical Procedure Template": { doctype: "Clinical Procedure Template", field: "rate" },
				"Clinical Procedure":        { doctype: "Clinical Procedure Template", field: "rate" },
				"Lab Test Template":         { doctype: "Lab Test Template",         field: "lab_test_rate" },
				"Lab Test":                  { doctype: "Lab Test Template",         field: "lab_test_rate" },
			};

			const cfg = config[row.item_type];
			if (!cfg) return;

			frappe.db.get_value(cfg.doctype, row.template, cfg.field, (r) => {
				const rate = r ? r[cfg.field] : 0;
				frappe.model.set_value(cdt, cdn, "plan_rate", rate || 0);
			});
		},
	});
});
