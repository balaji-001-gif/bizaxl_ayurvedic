// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Treatment Plan Template" DocType (loaded via
// hooks.doctype_js). When a user selects a Therapy Type, Clinical Procedure,
// or Lab Test Template in the Items grid, this handler automatically fetches
// the rate from the master doctype and populates the plan_rate field.
//
// The Link field for the item master may be named "template" or "item_code"
// depending on the Frappe Healthcare version; we handle both.

// ── Item row: auto-fetch rate from master doctype into plan_rate ──

// Map item_type → master doctype and rate field
const ITEM_CONFIG = {
	"Therapy Type":              { doctype: "Therapy Type",              field: "rate" },
	"Therapy":                   { doctype: "Therapy Type",              field: "rate" },
	"Clinical Procedure Template": { doctype: "Clinical Procedure Template", field: "rate" },
	"Clinical Procedure":        { doctype: "Clinical Procedure Template", field: "rate" },
	"Lab Test Template":         { doctype: "Lab Test Template",         field: "lab_test_rate" },
	"Lab Test":                  { doctype: "Lab Test Template",         field: "lab_test_rate" },
};

// The Link field may be "template" or "item_code" depending on Frappe Health version
const ITEM_LINK_FIELDS = ["template", "item_code"];

function getItemCode(row) {
	// Try all possible Link field names
	for (const f of ITEM_LINK_FIELDS) {
		if (row[f]) return row[f];
	}
	return null;
}

function setItemCode(cdt, cdn, value) {
	// Try all possible Link field names
	for (const f of ITEM_LINK_FIELDS) {
		frappe.model.set_value(cdt, cdn, f, value);
	}
}

function fetchPlanRate(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const itemCode = getItemCode(row);
	if (!itemCode || !row.item_type) return;

	const cfg = ITEM_CONFIG[row.item_type];
	if (!cfg) return;

	frappe.db.get_value(cfg.doctype, itemCode, cfg.field, (r) => {
		const rate = r ? r[cfg.field] : 0;
		frappe.model.set_value(cdt, cdn, "plan_rate", rate || 0);
	});
}

function updateItemOptions(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row.item_type) return;

	const cfg = ITEM_CONFIG[row.item_type];
	if (!cfg) {
		// Unknown type — clear all link fields
		setItemCode(cdt, cdn, null);
		return;
	}

	// Update each possible Link field's options to point to the correct master doctype
	for (const f of ITEM_LINK_FIELDS) {
		frappe.meta.get_docfield(cdt, f, row.parent).options = cfg.doctype;
		frappe.model.set_value(cdt, cdn, f, null);
	}
}

// Register handlers for each possible child table doctype AND each possible link field name
["Treatment Plan Template Item", "Treatment Plan Item"].forEach((dt) => {
	const events = {
		item_type(frm, cdt, cdn) {
			updateItemOptions(cdt, cdn);
		},
	};
	// Register handler for every possible link field name
	ITEM_LINK_FIELDS.forEach((fieldName) => {
		events[fieldName] = function(frm, cdt, cdn) {
			fetchPlanRate(cdt, cdn);
		};
	});
	frappe.ui.form.on(dt, events);
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
