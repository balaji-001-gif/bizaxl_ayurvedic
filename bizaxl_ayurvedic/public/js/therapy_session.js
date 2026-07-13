// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// Extends the core Healthcare "Therapy Session" DocType (loaded via
// hooks.doctype_js) with auto-fetch of exercise steps from Exercise Type.
// When a user selects an Exercise Type in the exercises child table,
// the exercise steps HTML is fetched and displayed inline.

frappe.ui.form.on("Therapy Session", {
	refresh(frm) {
		// Clear any stale step displays on page refresh
		frm.$wrapper.find(".exercise-steps-display").remove();
	},

	before_save(frm) {
		// Clear step displays before save (they'll be re-rendered on refresh)
		frm.$wrapper.find(".exercise-steps-display").remove();
	},
});

frappe.ui.form.on("Therapy Session Exercise", {
	exercise_type(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (!row.exercise_type) return;

		// Fetch exercise steps from Exercise Type doctype
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Exercise Type",
				filters: { name: row.exercise_type },
				fieldname: "exercise_steps",
			},
			callback(r) {
				if (r.message && r.message.exercise_steps) {
					show_exercise_steps(frm, cdn, row.exercise_type, r.message.exercise_steps);
				} else {
					// Clear any existing display for this row if no steps
					frm.$wrapper.find(`.exercise-steps-display[data-cdn="${cdn}"]`).remove();
				}
			},
		});
	},

	// Also refresh when the form is refreshed
	form_render(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (row.exercise_type) {
			// Check if we already have steps displayed for this row
			if (frm.$wrapper.find(`.exercise-steps-display[data-cdn="${cdn}"]`).length === 0) {
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Exercise Type",
						filters: { name: row.exercise_type },
						fieldname: "exercise_steps",
					},
					callback(r) {
						if (r.message && r.message.exercise_steps) {
							show_exercise_steps(frm, cdn, row.exercise_type, r.message.exercise_steps);
						}
					},
				});
			}
		}
	},
});

function show_exercise_steps(frm, cdn, exercise_name, steps_html) {
	// Remove any existing display for this specific row
	frm.$wrapper.find(`.exercise-steps-display[data-cdn="${cdn}"]`).remove();

	// Find the grid row element and insert steps display after it
	let $grid = frm.$wrapper.find(`[data-cdn="${cdn}"]`).first();
	if (!$grid.length) return;

	let $display = $(`
		<div class="exercise-steps-display panel panel-default" data-cdn="${cdn}"
			style="margin: 8px 0 12px 0; border-left: 4px solid #003960; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
			<div class="panel-heading" style="background:#f0f7ff; padding: 10px 14px; border-bottom:1px solid #e2e8f0; border-radius: 6px 6px 0 0;">
				<div style="display:flex; justify-content:space-between; align-items:center;">
					<h6 style="margin:0; font-weight:600; color:#003960;">
						<i class="fa fa-list-ol" style="margin-right:6px;"></i>
						Exercise Steps — ${frappe.utils.escape_html(exercise_name)}
					</h6>
					<button class="btn btn-xs btn-default close-steps-btn" style="padding:0 6px; font-size:14px; line-height:1;">
						<i class="fa fa-times"></i>
					</button>
				</div>
			</div>
			<div class="panel-body" style="padding: 14px; font-size: 13px; line-height: 1.7;">
				${steps_html}
			</div>
		</div>
	`);

	$display.find(".close-steps-btn").on("click", function () {
		$(this).closest(".exercise-steps-display").remove();
	});

	$grid.closest(".grid-row").after($display);
}
