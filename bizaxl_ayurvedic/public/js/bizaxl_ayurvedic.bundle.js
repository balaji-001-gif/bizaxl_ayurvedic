// Copyright (c) 2026, Bizaxl Ayurvedic and contributors
// For license information, please see license.txt
//
// App-wide bundle, loaded on every Desk page via hooks.app_include_js.
// Keep this file lightweight — per-DocType logic belongs in
// bizaxl_ayurvedic/bizaxl_ayurvedic/doctype/<name>/<name>.js or in a dedicated
// public/js/<core_doctype>.js registered through hooks.doctype_js.

frappe.provide("bizaxl_ayurvedic");

bizaxl_ayurvedic.show_ai_score_badge = function (frm, score) {
	if (score === undefined || score === null) return;
	const color = score >= 70 ? "green" : score >= 40 ? "orange" : "red";
	frm.dashboard.add_indicator(__("AI Score: {0}", [score]), color);
};
