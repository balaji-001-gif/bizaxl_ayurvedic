// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Treatment Plan Template" DocType (loaded via
// hooks.doctype_js). When a user selects a type (Therapy Type, Clinical
// Procedure, Lab Test Template) in the Items grid, this handler dynamically
// updates the Link field's options so only the matching master records are
// shown. Drug rates are auto-fetched from the Item master.
//
// Plan item rates are NOT stored on the child row — the Clinical Lead cost
// breakdown always fetches them live from the master doctype.

// Map item_type → master doctype
const ITEM_CONFIG = {
	"Therapy Type":              { doctype: "Therapy Type" },
	"Therapy":                   { doctype: "Therapy Type" },
	"Clinical Procedure Template": { doctype: "Clinical Procedure Template" },
	"Clinical Procedure":        { doctype: "Clinical Procedure Template" },
	"Lab Test Template":         { doctype: "Lab Test Template" },
	"Lab Test":                  { doctype: "Lab Test Template" },
};

// The Link field may be "template" or "item_code" depending on Frappe Health version
const ITEM_LINK_FIELDS = ["template", "item_code"];

function updateItemOptions(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row.item_type) return;

	const cfg = ITEM_CONFIG[row.item_type];
	if (!cfg) {
		// Unknown type — clear all link fields
		for (const f of ITEM_LINK_FIELDS) {
			frappe.model.set_value(cdt, cdn, f, null);
		}
		return;
	}

	// Update each possible Link field's options to point to the correct master doctype
	for (const f of ITEM_LINK_FIELDS) {
		const df = frappe.meta.get_docfield(cdt, f, row.parent);
		if (df) df.options = cfg.doctype;
		frappe.model.set_value(cdt, cdn, f, null);
	}
}

// Register handlers for each possible child table doctype
["Treatment Plan Template Item", "Treatment Plan Item"].forEach((dt) => {
	frappe.ui.form.on(dt, {
		item_type(frm, cdt, cdn) {
			updateItemOptions(cdt, cdn);
		},
	});
});

// ── Drug row: auto-fetch rate from Item master into rate ──

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
