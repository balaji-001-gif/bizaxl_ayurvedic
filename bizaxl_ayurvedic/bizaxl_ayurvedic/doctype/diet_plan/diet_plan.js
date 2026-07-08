frappe.ui.form.on("Diet Plan", {
	refresh(frm) {
		frm.add_custom_button(__("Fetch Diet Template"), () => {
			frappe.prompt(
				[{
					fieldname: "diet_template",
					label: "Diet Template",
					fieldtype: "Link",
					options: "Diet Template",
					reqd: 1,
				}],
				(values) => {
					frappe.call({
						method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.diet_plan.diet_plan.get_template_rows",
						args: { template: values.diet_template, start_date: frm.doc.start_date },
						callback(r) {
							if (!r.message) return;
							frm.clear_table("table_mcva");
							(r.message || []).forEach((row) => {
								let d = frm.add_child("table_mcva");
								Object.assign(d, row);
							});
							frm.refresh_field("table_mcva");
							frappe.show_alert({ message: __("Diet Template fetched successfully"), indicator: "green" });
						},
					});
				},
				__("Select Diet Template")
			);
		});

		if (!frm.is_new() && frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Create Meal Logs"), () => {
				frappe.call({
					method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.diet_plan.diet_plan.create_meal_logs",
					args: { docname: frm.doc.name },
					callback(r) {
						frappe.msgprint(r.message);
					},
				});
			});
		}
	},
});
