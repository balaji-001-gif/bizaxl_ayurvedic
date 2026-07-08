# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HealthcareMedicationPrescription(Document):
    def before_insert(self):
        """Auto-fetch medications from the linked Patient Encounter, mirroring the
        client's original Server Script ("To get the prescription from consultation
        to medication prescription").

        Only populates if the user has not already entered medications manually
        on the form — prevents silent data loss.
        """
        if not self.encounter or self.medications:
            return

        encounter = frappe.get_doc("Patient Encounter", self.encounter)
        for d in encounter.drug_prescription:
            # DrugPrescription in Healthcare v15 has no dedicated "frequency"
            # field; the dosage instruction lives in the "dosage" field.
            self.append("medications", {
                "medication": d.drug_code or "",
                "dosage": d.dosage or "",
                "frequency": getattr(d, "frequency", "") or d.dosage or "",
                "duration": d.period or 0,
                "quantity": d.qty or 0,
                "instructions": d.comment or "",
            })
