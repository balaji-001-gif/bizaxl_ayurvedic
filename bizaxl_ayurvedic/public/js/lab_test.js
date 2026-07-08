// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Lab Test" DocType (loaded via hooks.doctype_js)
// with: (1) a Clinical Decision Support reference panel pulled from
// Lab Test Parameter Reference, and (2) a bulk row-delete helper for long
// result tables.

frappe.ui.form.on("Lab Test", {
	refresh(frm) {
		show_parameter_reference(frm);
		add_bulk_delete_button(frm, "normal_test_items");
		add_bulk_delete_button(frm, "normal_test_result");
	},
});

function show_parameter_reference(frm) {
	if (!frm.doc.template) {
		frm.dashboard.clear_comment();
		frm.dashboard.add_comment(__("No Template selected — reference ranges unavailable"), "orange", true);
		return;
	}

	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Lab Test Parameter Reference",
			filters: { lab_test: frm.doc.template },
			fields: ["name"],
			limit_page_length: 1,
		},
		callback(r) {
			const match = (r.message || [])[0];
			if (!match) {
				frm.dashboard.add_comment(__("No matching parameter reference found for this template"), "red", true);
				return;
			}
			frappe.call({
				method: "frappe.client.get",
				args: { doctype: "Lab Test Parameter Reference", name: match.name },
				callback(res) {
					const doc = res.message;
					let rows = (doc.lab_test_parameter_detail || [])
						.map(
							(row) =>
								`<tr><td>${row.parameter_name || ""}</td><td>${row.gender__age_group || ""}</td>` +
								`<td>${row.unit || ""}</td><td>${row.range || ""}</td></tr>`
						)
						.join("");
					const html = `
						<div>
							<h5>${__("Clinical Reference — Normal Ranges")}</h5>
							<table class="table table-bordered">
								<thead><tr><th>${__("Parameter")}</th><th>${__("Gender/Age")}</th><th>${__("Unit")}</th><th>${__("Range")}</th></tr></thead>
								<tbody>${rows}</tbody>
							</table>
						</div>`;
					frm.dashboard.add_section(html, __("Lab Parameter Reference"));
				},
			});
		},
	});
}

function add_bulk_delete_button(frm, child_table) {
	if (!frm.fields_dict[child_table]) return;

	setTimeout(() => {
		let grid = frm.fields_dict[child_table]?.grid;
		if (grid) {
			grid.multiselect = true;
			grid.enable_checkbox_selection = true;
			grid.refresh();
		}
	}, 500);

	frm.add_custom_button(
		__("Delete Selected Rows ({0})", [child_table]),
		() => {
			let grid = frm.fields_dict[child_table]?.grid;
			if (!grid) return;
			let selected = grid.get_selected_children();
			if (!selected.length) {
				frappe.msgprint(__("Select rows using checkboxes first."));
				return;
			}
			frappe.confirm(__("Delete {0} row(s)?", [selected.length]), () => {
				selected.forEach((row) => frappe.model.clear_doc(row.doctype, row.name));
				frm.refresh_field(child_table);
				frappe.show_alert({ message: __("Deleted."), indicator: "green" });
			});
		},
		__("Actions")
	);
}
