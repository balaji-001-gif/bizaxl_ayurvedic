# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
v0.3 — Multi-Language, Feedback Collection & Clinical Decision Support

Adds custom fields to support the three new gap-closing features:

1. Multi-Language (Hindi/Sanskrit):
   - `prescription_language` on Healthcare Medication Prescription
   - `instructions_regional` on Healthcare Prescription Item
   (These are added via JSON updates — bench migrate syncs them)

2. Automated Feedback Collection:
   - `store_name` and `google_review_url` fields on Bizaxl Ayurvedic Settings
   (Added via JSON update to the Settings doctype)

3. Seeds the Ayurvedic Herb Reference with common herbs for the
   Clinical Decision Support engine to work immediately after install.
"""
import frappe
import csv
import os


def execute():
    _seed_herb_reference_data()
    _import_translations()
    frappe.logger("bizaxl_ayurvedic").info(
        "v0.3: Seeded herb reference data and imported Hindi/Sanskrit translations"
    )


def _seed_herb_reference_data():
    """Pre-populate the Ayurvedic Herb Reference with common herbs so the
    suggestion engine works out of the box."""
    herbs = [
        {
            "herb_name": "Triphala",
            "sanskrit_name": "त्रिफला",
            "latin_name": "Terminalia chebula + Terminalia bellirica + Emblica officinalis",
            "dosha_effect": "Tridoshic",
            "properties": "Rasa: Madhura, Amla, Katu, Tikta, Kasaya; Virya: Usna",
            "classical_formulations": "Triphala Churna, Triphala Ghrita, Triphala Rasayana",
            "typical_dosage": "3-6 g powder with warm water at bedtime",
            "contraindications": "Pregnancy, severe diarrhea",
            "references": "Charaka Samhita, Sutrasthana 1/68",
            "symptoms": [
                {"symptom": "indigestion", "symptom_type": "Digestive", "formulation": "Triphala Churna 3g with warm water"},
                {"symptom": "constipation", "symptom_type": "Digestive", "formulation": "Triphala Churna 5g at bedtime"},
                {"symptom": "poor digestion", "symptom_type": "Digestive", "formulation": "Triphala with honey"},
                {"symptom": "detox", "symptom_type": "General Wellness", "formulation": "Triphala Rasayana"},
            ],
        },
        {
            "herb_name": "Ashwagandha",
            "sanskrit_name": "अश्वगन्धा",
            "latin_name": "Withania somnifera",
            "dosha_effect": "Vata-Pacifying",
            "properties": "Rasa: Madhura, Tikta; Virya: Usna; Vipaka: Madhura",
            "classical_formulations": "Ashwagandha Churna, Ashwagandharishta, Ashwagandha Ghrita",
            "typical_dosage": "3-6 g powder with milk, 1-2 capsules (500 mg each) twice daily",
            "contraindications": "Hyperthyroidism, pregnancy (high doses)",
            "references": "Charaka Samhita, Chikitsasthana",
            "symptoms": [
                {"symptom": "stress", "symptom_type": "Mental Health", "formulation": "Ashwagandha Churna 3g with warm milk"},
                {"symptom": "anxiety", "symptom_type": "Mental Health", "formulation": "Ashwagandha powder 3g twice daily"},
                {"symptom": "fatigue", "symptom_type": "General Wellness", "formulation": "Ashwagandha with milk"},
                {"symptom": "joint pain", "symptom_type": "Joint / Muscular", "formulation": "Ashwagandha + sesame oil massage"},
            ],
        },
        {
            "herb_name": "Tulsi",
            "sanskrit_name": "तुलसी",
            "latin_name": "Ocimum sanctum",
            "dosha_effect": "Vata-Kapha-Pacifying",
            "properties": "Rasa: Katu, Tikta; Virya: Usna; Vipaka: Katu",
            "classical_formulations": "Tulsi tea, Tulsi drops, Trikatu + Tulsi",
            "typical_dosage": "3-6 leaves chewed daily, 1 cup tea, 10-15 drops extract",
            "contraindications": "May thin blood — caution with anticoagulants",
            "references": "Charaka Samhita, Sushruta Samhita",
            "symptoms": [
                {"symptom": "cough", "symptom_type": "Respiratory", "formulation": "Tulsi tea with ginger and honey"},
                {"symptom": "cold", "symptom_type": "Respiratory", "formulation": "Tulsi + black pepper decoction"},
                {"symptom": "sore throat", "symptom_type": "Respiratory", "formulation": "Tulsi water gargle"},
                {"symptom": "fever", "symptom_type": "General Wellness", "formulation": "Tulsi decoction with cardamom"},
            ],
        },
        {
            "herb_name": "Turmeric",
            "sanskrit_name": "हरिद्रा",
            "latin_name": "Curcuma longa",
            "dosha_effect": "Tridoshic",
            "properties": "Rasa: Tikta, Katu; Virya: Usna; Vipaka: Katu",
            "classical_formulations": "Haridra Khanda, Turmeric milk, Triphala + Turmeric",
            "typical_dosage": "1-3 g powder with meals, 1 cup turmeric milk at bedtime",
            "contraindications": "Gallstones, bile duct obstruction, anticoagulant therapy",
            "references": "Ashtanga Hridayam, Sutrasthana",
            "symptoms": [
                {"symptom": "inflammation", "symptom_type": "Joint / Muscular", "formulation": "Turmeric milk with black pepper"},
                {"symptom": "joint pain", "symptom_type": "Joint / Muscular", "formulation": "Turmeric + ginger decoction"},
                {"symptom": "skin issues", "symptom_type": "Skin", "formulation": "Turmeric paste externally"},
                {"symptom": "poor immunity", "symptom_type": "General Wellness", "formulation": "Turmeric milk daily"},
            ],
        },
        {
            "herb_name": "Brahmi",
            "sanskrit_name": "ब्राह्मी",
            "latin_name": "Bacopa monnieri",
            "dosha_effect": "Vata-Pitta-Pacifying",
            "properties": "Rasa: Madhura, Tikta, Kasaya; Virya: Sita; Vipaka: Madhura",
            "classical_formulations": "Brahmi Ghrita, Brahmi Churna, Brahmi Vati",
            "typical_dosage": "3-6 g powder, 5-10 ml Brahmi juice, 1-2 capsules (500 mg) twice daily",
            "contraindications": "Slow heart rate, excess Kapha conditions",
            "references": "Charaka Samhita, Sushruta Samhita",
            "symptoms": [
                {"symptom": "poor memory", "symptom_type": "Nervous System", "formulation": "Brahmi Churna 3g with honey"},
                {"symptom": "stress", "symptom_type": "Mental Health", "formulation": "Brahmi Ghrita 5ml twice daily"},
                {"symptom": "anxiety", "symptom_type": "Mental Health", "formulation": "Brahmi + Ashwagandha powder"},
                {"symptom": "brain fog", "symptom_type": "Nervous System", "formulation": "Brahmi tea daily"},
            ],
        },
        {
            "herb_name": "Ginger",
            "sanskrit_name": "शुण्ठी",
            "latin_name": "Zingiber officinale",
            "dosha_effect": "Vata-Kapha-Pacifying",
            "properties": "Rasa: Katu; Virya: Usna; Vipaka: Madhura",
            "classical_formulations": "Shunthi Churna, Trikatu, Shunthi Siddha Jala",
            "typical_dosage": "1-2 g powder, 1-inch fresh root in cooking, ginger tea 2-3 cups/day",
            "contraindications": "Excess heat conditions, peptic ulcer, bleeding disorders",
            "references": "Charaka Samhita, Sutrasthana",
            "symptoms": [
                {"symptom": "indigestion", "symptom_type": "Digestive", "formulation": "Ginger tea before meals"},
                {"symptom": "nausea", "symptom_type": "Digestive", "formulation": "Fresh ginger juice with honey"},
                {"symptom": "cold", "symptom_type": "Respiratory", "formulation": "Ginger + tulsi decoction"},
                {"symptom": "poor appetite", "symptom_type": "Digestive", "formulation": "Ginger powder with rock salt"},
            ],
        },
    ]

    for herb_data in herbs:
        symptoms = herb_data.pop("symptoms", [])
        try:
            if frappe.db.exists("Ayurvedic Herb Reference", herb_data["herb_name"]):
                continue

            doc = frappe.get_doc({
                "doctype": "Ayurvedic Herb Reference",
                **herb_data,
            })
            for s in symptoms:
                doc.append("symptom_map", {
                    "symptom": s["symptom"],
                    "symptom_type": s["symptom_type"],
                    "formulation": s.get("formulation", ""),
                })
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.insert()
        except Exception as e:
            frappe.log_error(
                title="v0.3 Herb seed failed",
                message=f"Herb: {herb_data['herb_name']}, Error: {e}"
            )

    frappe.logger("bizaxl_ayurvedic").info(
        f"v0.3: Seeded {len(herbs)} herbs into Ayurvedic Herb Reference"
    )


def _import_translations():
    """Import Hindi and Sanskrit translations from CSV files into the Translation doctype."""
    translations_dir = frappe.get_app_path("bizaxl_ayurvedic", "translations")
    for filename in ["hindi.csv", "sanskrit.csv"]:
        filepath = os.path.join(translations_dir, filename)
        if not os.path.exists(filepath):
            continue

        lang_code = "hi" if "hindi" in filename else "sa"
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                source = row.get("source_text", "").strip()
                translated = row.get("translated_text", "").strip()
                if not source or not translated:
                    continue
                if not frappe.db.exists("Translation", {
                    "source_text": source,
                    "language": row.get("language", lang_code),
                }):
                    doc = frappe.get_doc({
                        "doctype": "Translation",
                        "source_text": source,
                        "translated_text": translated,
                        "language": row.get("language", lang_code),
                    })
                    doc.flags.ignore_permissions = True
                    doc.insert()
                    count += 1
            if count:
                frappe.logger("bizaxl_ayurvedic").info(
                    f"v0.3: Imported {count} new {filename} translations"
                )
