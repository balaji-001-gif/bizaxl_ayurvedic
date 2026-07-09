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
//
// Fires on both `item_type` (type) and `template` field changes so the
// plan_rate is always kept in sync regardless of which field the user
// edits first or changes later.

// Map item_type → master doctype and rate field
const ITEM_CONFIG = {
	"Therapy Type":              { doctype: "Therapy Type",              field: "rate" },
	"Therapy":                   { doctype: "Therapy Type",              field: "rate" },
	"Clinical Procedure Template": { doctype: "Clinical Procedure Template", field: "rate" },
	"Clinical Procedure":        { doctype: "Clinical Procedure Template", field: "rate" },
	"Lab Test Template":         { doctype: "Lab Test Template",         field: "lab_test_rate" },
	"Lab Test":                  { doctype: "Lab Test Template",         field: "lab_test_rate" },
};

function fetchPlanRate(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row.template || !row.item_type) return;

	const cfg = ITEM_CONFIG[row.item_type];
	if (!cfg) return;

	frappe.db.get_value(cfg.doctype, row.template, cfg.field, (r) => {
		const rate = r ? r[cfg.field] : 0;
		frappe.model.set_value(cdt, cdn, "plan_rate", rate || 0);
	});
}

function updateTemplateOptions(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row.item_type) return;

	const cfg = ITEM_CONFIG[row.item_type];
	if (!cfg) {
		// Unknown type — clear template
		frappe.model.set_value(cdt, cdn, "template", null);
		return;
	}

	// Update the template Link field to point to the correct master doctype
	frappe.meta.get_docfield(cdt, "template", row.parent).options = cfg.doctype;
	// Clear the template value since the target doctype changed
	frappe.model.set_value(cdt, cdn, "template", null);
}

["Treatment Plan Template Item", "Treatment Plan Item"].forEach((dt) => {
	frappe.ui.form.on(dt, {
		template(frm, cdt, cdn) {
			fetchPlanRate(cdt, cdn);
		},
		item_type(frm, cdt, cdn) {
			updateTemplateOptions(cdt, cdn);
		},
	});
});

// ── Drug row: auto-fetch rate from Item master into rate ──
// The Drugs child table in Treatment Plan Template uses the standard
// "Drug Prescription" child table (same one used in Patient Encounter).
// When a user selects a drug_code, this handler fetches the Item's
// standard_rate and populates the rate field.

function fetchDrugRate(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row.drug_code) return;

	frappe.db.get_value("Item", row.drug_code, "standard_rate", (r) => {
		const rate = r ? r.standard_rate : 0;
		frappe.model.set_value(cdt, cdn, "rate", rate || 0);
	});
}

frappe.ui.form.on("Drug Prescription", {
	drug_code(frm, cdt, cdn) {
		fetchDrugRate(cdt, cdn);
	},
});
