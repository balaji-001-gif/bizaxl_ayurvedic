# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TreatmentRecord(Document):
    pass

# ------------------------------------------------------------------
# Whitelisted helpers used by treatment_record.js
# ------------------------------------------------------------------

@frappe.whitelist()
def get_compare_gallery_html(docname):
    """Builds a simple side-by-side Before/After comparison gallery."""
    doc = frappe.get_doc("Treatment Record", docname)
    before = [p for p in doc.photos if p.photo_type == "Before"]
    after = [p for p in doc.photos if p.photo_type == "After"]

    def _cell(photo):
        if not photo:
            return "<td>-</td>"
        return (
            f"<td><img src='{photo.photo}' style='max-width:220px;border-radius:6px'/>"
            f"<br><small>{photo.treatment_date or ''} {photo.angle or ''}</small></td>"
        )

    rows = "".join(
        f"<tr>{_cell(b)}{_cell(a)}</tr>"
        for b, a in zip(before or [None], after or [None])
    )
    return (
        "<table class='table'><thead><tr><th>Before</th><th>After</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )
