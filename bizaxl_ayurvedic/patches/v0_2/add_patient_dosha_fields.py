# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds Dosha/Prakriti-Vikriti profiling custom fields to the **Patient** doctype
(from Frappe Healthcare) — closes the 'Prakriti/Dosha Customer Profiling'
CRITICAL gap vs Healthray, DMA Aarogya, Clinicea, EasyClinic, VaidyaManager.

These fields complement the existing Customer-level fields (added in v0_1)
with a clinical Ayurvedic profile tab on the Patient record, which is the
canonical identity record used across encounters, diet plans, prescriptions,
and treatment records.

Inserted after the `language` field — the last basic-info field — so the
Ayurvedic Profile tab appears naturally after demographics and before the
more-info / clinical-history sections.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Patient": [
            {
                "fieldname": "ayurvedic_profile_tab",
                "fieldtype": "Tab Break",
                "label": "Ayurvedic Profile",
                "insert_after": "language",
            },
            {
                "fieldname": "dosha_type",
                "fieldtype": "Select",
                "label": "Prakriti / Dosha Type",
                "options": "\nVata\nPitta\nKapha\nVata-Pitta\nPitta-Kapha\nVata-Kapha\nTridosha",
                "insert_after": "ayurvedic_profile_tab",
                "description": "Baseline Ayurvedic constitution (Prakriti). "
                                "Set once and refined over time — does not change per visit.",
            },
            {
                "fieldname": "column_break_dosha_patient",
                "fieldtype": "Column Break",
                "insert_after": "dosha_type",
            },
            {
                "fieldname": "dietary_notes",
                "fieldtype": "Small Text",
                "label": "Dietary Notes",
                "insert_after": "column_break_dosha_patient",
                "description": "Dietary preferences, restrictions, and observations relevant to the patient's constitution.",
            },
            {
                "fieldname": "lifestyle_observations",
                "fieldtype": "Small Text",
                "label": "Lifestyle Observations",
                "insert_after": "dietary_notes",
                "description": "Daily routine, sleep patterns, exercise habits, stress levels — key inputs for Ayurvedic assessment.",
            },
        ],
    })
