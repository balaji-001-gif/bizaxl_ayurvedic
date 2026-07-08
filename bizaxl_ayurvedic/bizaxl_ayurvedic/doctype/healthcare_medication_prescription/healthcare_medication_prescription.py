# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HealthcareMedicationPrescription(Document):
    def before_insert(self):
        """Auto-fetch medications from the linked Patient Encounter, mirroring the
        client's original Server Script ("To get the prescription from consultation
        to medication prescription")."""
        if not self.encounter:
            return

        encounter = frappe.get_doc("Patient Encounter", self.encounter)
        self.medications = []
        for d in encounter.drug_prescription:
            self.append("medications", {
                "medication": d.drug_code or "",
                "dosage": d.dosage or "",
                "frequency": d.frequency or "",
                "duration": d.period or 0,
                "quantity": d.qty or 0,
                "instructions": d.comment or "",
            })
