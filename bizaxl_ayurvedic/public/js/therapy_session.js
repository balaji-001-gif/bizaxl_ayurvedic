// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Therapy Session" DocType (loaded via
// hooks.doctype_js) with auto-fetch of exercise steps from Exercise Type.
// When a user selects an Exercise Type in the exercises child table,
// the exercise steps HTML is fetched and displayed inline below the row.

frappe.ui.form.on("Therapy Session", {
	refresh(frm) {
		load_all_exercise_steps(frm);
	},
});

frappe.ui.form.on("Therapy Session Exercise", {
	exercise_type(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (!row.exercise_type) {
			remove_steps_display(cdn);
			return;
		}

		// Show loading placeholder
		show_steps_loading(cdn);

		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Exercise Type",
				filters: { name: row.exercise_type },
				fieldname: "exercise_steps",
			},
			callback(r) {
				if (r.message && r.message.exercise_steps) {
					show_exercise_steps(cdn, row.exercise_type, r.message.exercise_steps);
				} else {
					remove_steps_display(cdn);
				}
			},
		});
	},
});

// ── Helpers ──

function load_all_exercise_steps(frm) {
	// Clear all stale displays first
	$(".exercise-steps-display").remove();

	if (!frm.doc.exercises) return;

	frm.doc.exercises.forEach((row) => {
		if (row.exercise_type && row.name) {
			// Check if we already have steps loaded for this row
			if ($(`.exercise-steps-display[data-cdn="${row.name}"]`).length) return;

			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Exercise Type",
					filters: { name: row.exercise_type },
					fieldname: "exercise_steps",
				},
				callback(r) {
					if (r.message && r.message.exercise_steps) {
						show_exercise_steps(row.name, row.exercise_type, r.message.exercise_steps);
					}
				},
			});
		}
	});
}

function show_steps_loading(cdn) {
	remove_steps_display(cdn);
	let $row = $(`tr[data-name="${cdn}"]`);
	if (!$row.length) return;

	let $loading = $(`
		<div class="exercise-steps-display" data-cdn="${cdn}"
			style="margin:4px 0 8px 0; padding:10px 14px; background:#f8f9fa; border-left:3px solid #adb5bd; border-radius:4px; font-size:12px; color:#6c757d;">
			<i class="fa fa-spinner fa-spin"></i> Loading exercise steps...
		</div>
	`);
	$row.after($loading);
}

function show_exercise_steps(cdn, exercise_name, steps_html) {
	remove_steps_display(cdn);
	let $row = $(`tr[data-name="${cdn}"]`);
	if (!$row.length) return;

	let $display = $(`
		<div class="exercise-steps-display panel panel-default" data-cdn="${cdn}"
			style="margin:4px 0 12px 0; border-left:4px solid #003960; border-radius:6px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
			<div class="panel-heading"
				style="background:#f0f7ff; padding:8px 14px; border-bottom:1px solid #e2e8f0; border-radius:6px 6px 0 0;
					display:flex; justify-content:space-between; align-items:center;">
				<h6 style="margin:0; font-weight:600; color:#003960; font-size:13px;">
					<i class="fa fa-list-ol" style="margin-right:6px;"></i>
					Exercise Steps — ${frappe.utils.escape_html(exercise_name)}
				</h6>
				<button class="btn btn-xs btn-default close-steps-btn"
					style="padding:0 6px; font-size:14px; line-height:1; border:none; background:transparent; cursor:pointer;">
					<i class="fa fa-times" style="color:#6c757d;"></i>
				</button>
			</div>
			<div class="panel-body" style="padding:14px; font-size:13px; line-height:1.7;">
				${steps_html}
			</div>
		</div>
	`);

	$display.find(".close-steps-btn").on("click", function () {
		$(this).closest(".exercise-steps-display").remove();
	});

	$row.after($display);
}

function remove_steps_display(cdn) {
	$(`.exercise-steps-display[data-cdn="${cdn}"]`).remove();
}
