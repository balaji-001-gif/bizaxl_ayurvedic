frappe.ui.form.on("Healthcare Medication Prescription", {
	refresh(frm) {
		if (frm.doc.status === "Approved" && !frm.doc.__islocal) {
			frm.add_custom_button(__("Print / Share on WhatsApp"), () => {
				window.open(`/printview?doctype=Healthcare%20Medication%20Prescription&name=${frm.doc.name}&trigger_print=1`, "_blank");
			});
		}
	},
});
// NOTE: the matching "Create Prescription" button on Patient Encounter lives in
// public/js/patient_encounter.js (registered via hooks.doctype_js), since core
// DocType forms only auto-load JS from their own bundle, not from this app's
// custom DocType folder.
