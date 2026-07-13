// Patient Assessment — photo click-to-view (added via doctype_js in hooks.py)
frappe.ui.form.on("Patient Assessment", {
	refresh(frm) {
		// The Attach Image field natively renders as a clickable thumbnail
		// that opens the full-size image in a lightbox. No extra code needed
		// for the click-to-view behavior — it's built into Frappe's Attach
		// Image fieldtype.
		//
		// This file is registered so we have a hook point for future
		// Patient Assessment enhancements.
	},
});
