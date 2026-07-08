frappe.ui.form.on("Treatment Record", {
	refresh(frm) {
		if (frm.doc.photos && frm.doc.photos.length >= 2) {
			frm.add_custom_button(__("Compare Before / After"), () => {
				frappe.call({
					method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.treatment_record.treatment_record.get_compare_gallery_html",
					args: { docname: frm.doc.name },
					callback(r) {
						frappe.msgprint({ title: __("Before / After Comparison"), message: r.message, wide: true });
					},
				});
			});
		}
	},
});
