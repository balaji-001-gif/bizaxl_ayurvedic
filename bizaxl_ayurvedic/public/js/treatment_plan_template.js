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

// The child table may use different field names depending on the Frappe
// Healthcare version. The type field can be "item_type" or "service_type".
// The Link field can be "template", "service", or "item_code".
const ITEM_TYPE_FIELDS = ["item_type", "service_type"];
const ITEM_LINK_FIELDS = ["template", "service", "item_code"];

function getType(row) {
	for (const f of ITEM_TYPE_FIELDS) {
		if (row[f]) return row[f];
	}
	return null;
}

function updateItemOptions(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const itemType = getType(row);
	if (!itemType) return;

	const cfg = ITEM_CONFIG[itemType];
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

// ── Plan items: auto-fetch rate from master doctype ──

const ITEM_RATE_CONFIG = {
	"Therapy Type":              { doctype: "Therapy Type", rate_fields: ["rate", "price"] },
	"Therapy":                   { doctype: "Therapy Type", rate_fields: ["rate", "price"] },
	"Clinical Procedure Template": { doctype: "Clinical Procedure Template", rate_fields: ["rate", "price"] },
	"Clinical Procedure":        { doctype: "Clinical Procedure Template", rate_fields: ["rate", "price"] },
	"Lab Test Template":         { doctype: "Lab Test Template", rate_fields: ["lab_test_rate", "rate", "price"] },
	"Lab Test":                  { doctype: "Lab Test Template", rate_fields: ["lab_test_rate", "rate", "price"] },
};

function fetchItemRate(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const itemType = getType(row);
	const itemCode = getItemCode(row);
	if (!itemType || !itemCode) return;

	const cfg = ITEM_RATE_CONFIG[itemType];
	if (!cfg) return;

	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: cfg.doctype,
			filters: { name: itemCode },
			fieldname: cfg.rate_fields.join(","),
		},
		callback(r) {
			if (r.message) {
				let rate = 0;
				for (const f of cfg.rate_fields) {
					if (r.message[f]) {
						rate = r.message[f];
						break;
					}
				}
				frappe.model.set_value(cdt, cdn, "rate", rate);
			}
		},
	});
}

function getItemCode(row) {
	for (const f of ITEM_LINK_FIELDS) {
		if (row[f]) return row[f];
	}
	return null;
}

// Register handlers for each possible child table doctype AND each possible type/link field name
["Treatment Plan Template Item", "Treatment Plan Item"].forEach((dt) => {
	const events = {};
	ITEM_TYPE_FIELDS.forEach((fieldName) => {
		events[fieldName] = function(frm, cdt, cdn) {
			updateItemOptions(cdt, cdn);
			fetchItemRate(cdt, cdn);
		};
	});
	ITEM_LINK_FIELDS.forEach((fieldName) => {
		events[fieldName] = function(frm, cdt, cdn) {
			fetchItemRate(cdt, cdn);
		};
	});
	frappe.ui.form.on(dt, events);
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
