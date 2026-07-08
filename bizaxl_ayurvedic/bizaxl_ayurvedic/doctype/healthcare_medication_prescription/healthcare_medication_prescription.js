frappe.ui.form.on("Healthcare Medication Prescription", {
	refresh(frm) {
		// Print / WhatsApp share button (existing)
		if (frm.doc.status === "Approved" && !frm.doc.__islocal) {
			frm.add_custom_button(__("Print / Share on WhatsApp"), () => {
				window.open(`/printview?doctype=Healthcare%20Medication%20Prescription&name=${frm.doc.name}&trigger_print=1`, "_blank");
			});
		}

		// --- Clinical Decision Support: Herb Suggestion Button ---
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("🌿 Suggest Herb for Symptom"), () => {
				const dlg = new frappe.ui.Dialog({
					title: __("Ayurvedic Herb Suggestion"),
					fields: [
						{
							fieldname: "symptom",
							label: __("Symptom / Condition"),
							fieldtype: "Data",
							reqd: 1,
							description: __("Type a symptom (e.g. indigestion, cough, joint pain)")
						},
						{
							fieldname: "dosha_filter",
							label: __("Filter by Dosha"),
							fieldtype: "Select",
							options: ["", "Vata", "Pitta", "Kapha"]
						}
					],
					primary_action_label: __("Search Herbs"),
					primary_action(values) {
						dlg.hide();
						frappe.call({
							method: "bizaxl_ayurvedic.ai.herb_suggestion.suggest_herbs_for_symptom",
							args: { symptom: values.symptom, limit: 10 },
							callback(r) {
								let herbs = r.message || [];
								if (values.dosha_filter) {
									herbs = herbs.filter(h => h.dosha_effect && h.dosha_effect.includes(values.dosha_filter));
								}
								show_herb_results(frm, herbs, values.symptom);
							}
						});
					}
				});
				dlg.show();
			});
		}
	},

	prescription_language(frm) {
		// Only fetch translations for saved documents
		if (frm.doc.__islocal || !frm.doc.name) return;

		if (frm.doc.prescription_language && frm.doc.prescription_language !== "English") {
			frappe.call({
				method: "bizaxl_ayurvedic.translations.translate.get_prescription_translations",
				args: { docname: frm.doc.name },
				callback(r) {
					const data = r.message;
					if (data && data.medications && data.medications.length) {
						frappe.show_alert({
							message: __("Translations are available for {0} medications", [data.medications.length]),
							indicator: "green"
						});
					}
				}
			});
		}
	}
});

function show_herb_results(frm, herbs, symptom) {
	const dlg = new frappe.ui.Dialog({
		title: __("Herbs for: {0}", [symptom]),
		fields: [
			{
				fieldname: "results_html",
				fieldtype: "HTML"
			}
		],
		primary_action_label: __("Add Selected as Medication"),
		primary_action(values) {
			dlg.hide();
		}
	});

	let html = "";
	if (!herbs || herbs.length === 0) {
		html = `<div class="alert alert-warning">No herbs found for "${symptom}". Try a different symptom or add herbs in Ayurvedic Herb Reference first.</div>`;
	} else {
		html = `<div class="list-group" style="max-height:400px;overflow-y:auto;">`;
		herbs.forEach((h, i) => {
			const sanskrit = h.sanskrit_name ? ` (${h.sanskrit_name})` : "";
			const dosage = h.typical_dosage ? `<br><small class="text-muted">Dosage: ${h.typical_dosage}</small>` : "";
			const formulations = h.classical_formulations ? `<br><small class="text-muted">Formulations: ${h.classical_formulations}</small>` : "";
			const contraindications = h.contraindications ? `<br><small class="text-danger">Caution: ${h.contraindications}</small>` : "";
			html += `
				<div class="list-group-item list-group-item-action" style="cursor:pointer" onclick="add_herb_to_prescription('${frm.doc.name}', '${h.herb_name}')">
					<div class="d-flex w-100 justify-content-between">
						<h6 class="mb-1"><b>${h.herb_name}</b>${sanskrit}</h6>
						<small class="text-muted">${h.dosha_effect || ""}</small>
					</div>
					${h.matched_symptom ? `<p class="mb-1"><i>Matched: ${h.matched_symptom}</i></p>` : ""}
					${formulations}
					${dosage}
					${contraindications}
				</div>
			`;
		});
		html += `</div>`;
	}

	dlg.fields_dict.results_html.$wrapper.html(html);
	dlg.show();
}

// Global function so onclick works from dialog HTML
window.add_herb_to_prescription = function(docname, herb_name) {
	const cur_frm = cur_frm || frappe.current_form;
	if (cur_frm && cur_frm.doctype === "Healthcare Medication Prescription") {
		cur_frm.add_child("medications", {
			medication: herb_name,
			dosage: "",
			frequency: "",
			duration: 0,
			quantity: 0,
			instructions: ""
		});
		cur_frm.refresh_field("medications");
		frappe.show_alert({ message: __("Added {0} to prescription", [herb_name]), indicator: "green" });
	}
};
