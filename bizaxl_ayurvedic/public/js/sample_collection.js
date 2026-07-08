// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Sample Collection" DocType (loaded via
// hooks.doctype_js) to auto-create a linked Specimen and fetch collection
// timestamps back from it.

frappe.ui.form.on("Sample Collection", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Fetch from Specimen"), async () => {
				await fetch_from_specimen(frm, { save_after: true });
			});
			if (frm.doc.patient) {
				frm.add_custom_button(__("Create Specimen"), async () => {
					await create_specimen_and_link(frm);
				});
			}
		}
	},

	before_submit(frm) {
		const child_table_field = find_obs_child_table_field(frm);
		if (!child_table_field) return;
		const rows = frm.doc[child_table_field] || [];
		const not_ready = rows.some((r) => r.status !== "Collected" || !r.collection_date_time);
		if (not_ready) {
			frappe.throw(__("Please click 'Fetch from Specimen' before submitting."));
		}
	},
});

const CHILD_TABLE_FIELD = "observation_sample_collection"; // adjust if your schema differs
const CHILD_SPECIMEN_FIELD = "specimen";

function find_obs_child_table_field(frm) {
	for (const key in frm.fields_dict) {
		const f = frm.fields_dict[key];
		if (f?.df?.fieldtype === "Table" && f.df.options === "Observation Sample Collection") {
			return key;
		}
	}
	frappe.msgprint(__("Observation Sample Collection table not found on this form."));
	return null;
}

async function fetch_from_specimen(frm, { save_after }) {
	const child_table_field = find_obs_child_table_field(frm);
	if (!child_table_field) return;
	const rows = frm.doc[child_table_field] || [];
	if (!rows.length) {
		frappe.msgprint(__("No sample rows found. Add at least one row."));
		return;
	}

	const current_user = frappe.session.user;
	for (const row of rows) {
		const specimen_id = row.specimen;
		if (!specimen_id) continue;
		const r = await frappe.call({ method: "frappe.client.get", args: { doctype: "Specimen", name: specimen_id } });
		const sp = r.message || {};
		const received_dt = sp.received_date_time || sp.received_datetime || sp.received_on || sp.received_date || null;

		row.collection_date_time = row.collection_date_time || received_dt || frappe.datetime.now_datetime();
		row.status = "Collected";
		row.collected_user = row.collected_user || current_user;
		row.collected_by = row.collected_by || current_user;
	}
	frm.refresh_field(child_table_field);

	const all_collected = rows.every((r) => r.status === "Collected");
	await frm.set_value("status", all_collected ? "Collected" : "Partly Collected");

	if (save_after) {
		await frm.save();
		frappe.show_alert({ message: __("Fetched from Specimen and saved"), indicator: "green" });
	}
}

async function create_specimen_and_link(frm) {
	const rows = frm.doc[CHILD_TABLE_FIELD] || [];
	if (!rows.length) {
		frappe.msgprint(__("No rows found in the Samples/Observation table. Please add a row first."));
		return;
	}

	const existing = rows.find((r) => r[CHILD_SPECIMEN_FIELD]);
	if (existing) {
		frappe.set_route("Form", "Specimen", existing[CHILD_SPECIMEN_FIELD]);
		return;
	}

	try {
		const r = await frappe.call({
			method: "frappe.client.insert",
			args: {
				doc: {
					doctype: "Specimen",
					patient: frm.doc.patient,
					patient_name: frm.doc.patient_name,
					company: frm.doc.company,
					reference_doctype: "Sample Collection",
					reference_name: frm.doc.name,
				},
			},
		});
		const specimen_name = r.message.name;
		rows.forEach((row) => (row[CHILD_SPECIMEN_FIELD] = specimen_name));
		frm.refresh_field(CHILD_TABLE_FIELD);
		await frm.save();
		frappe.set_route("Form", "Specimen", specimen_name);
	} catch (e) {
		frappe.msgprint({ title: __("Specimen Creation Failed"), message: e.message || __("Check console for error."), indicator: "red" });
	}
}
