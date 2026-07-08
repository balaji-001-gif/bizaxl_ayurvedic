# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Multi-Language Helper for Hindi (हिन्दी) and Sanskrit (संस्कृत)
(Gap Analysis — MEDIUM priority gap vs VaidyaManager)

Provides language-aware helpers for prescription labels, dosage instructions,
and WhatsApp messages. Uses Frappe's built-in Translation doctype so that
labels can be managed through the UI at:
    Settings > Customize > Translations

Usage:
    from bizaxl_ayurvedic.translations.translate import t, prescription_language_options

    # Get translated text for the current language
    label = t("Dosage", lang="hi")

    # Get dosage instruction in regional language
    instruction = translate_dosage("Once Daily", lang="sa")
"""
import frappe

REGIONAL_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "sa": "संस्कृत (Sanskrit)",
}

# Common Ayurvedic terms with Hindi and Sanskrit translations
AYURVEDIC_TERMS = {
    "Dosage":         {"hi": "मात्रा", "sa": "मात्रा"},
    "Frequency":      {"hi": "आवृत्ति", "sa": "आवृत्तिः"},
    "Duration":       {"hi": "अवधि", "sa": "अवधिः"},
    "Instructions":   {"hi": "निर्देश", "sa": "निर्देशाः"},
    "Medication":     {"hi": "औषधि", "sa": "औषधम्"},
    "Patient":        {"hi": "रोगी", "sa": "रोगी"},
    "Practitioner":   {"hi": "चिकित्सक", "sa": "वैद्यः"},
    "Prescription":   {"hi": "पर्चा", "sa": "प्रलेखः"},
    "Morning":        {"hi": "सुबह", "sa": "प्रातः"},
    "Afternoon":      {"hi": "दोपहर", "sa": "मध्याह्ने"},
    "Evening":        {"hi": "शाम", "sa": "सायम्"},
    "Night":          {"hi": "रात", "sa": "रात्रौ"},
    "Before Meal":    {"hi": "भोजन से पहले", "sa": "भोजनात् पूर्वम्"},
    "After Meal":     {"hi": "भोजन के बाद", "sa": "भोजनानन्तरम्"},
    "With Water":     {"hi": "पानी के साथ", "sa": "जलेन सह"},
    "With Milk":      {"hi": "दूध के साथ", "sa": "दुग्धेन सह"},
    "Once Daily":     {"hi": "दिन में एक बार", "sa": "दिने सकृत्"},
    "Twice Daily":    {"hi": "दिन में दो बार", "sa": "दिने द्विवारम्"},
    "Thrice Daily":   {"hi": "दिन में तीन बार", "sa": "दिने त्रिवारम्"},
    "OD":             {"hi": "दिन में एक बार", "sa": "दिने सकृत्"},
    "BD":             {"hi": "दिन में दो बार", "sa": "दिने द्विवारम्"},
    "TID":            {"hi": "दिन में तीन बार", "sa": "दिने त्रिवारम्"},
    "QID":            {"hi": "दिन में चार बार", "sa": "दिने चतुर्वारम्"},
    "Notes":          {"hi": "टिप्पणी", "sa": "टिप्पणी"},
    "Date":           {"hi": "दिनांक", "sa": "दिनाङ्कः"},
}


def t(text: str, lang: str = "en") -> str:
    """Translate a single term into the given language.

    Falls back to English if no translation is available.
    """
    if lang == "en" or not lang:
        return text
    term = AYURVEDIC_TERMS.get(text)
    if term and lang in term:
        return term[lang]
    # Try Frappe's built-in Translation doctype as fallback
    try:
        translated = frappe.get_value(
            "Translation",
            {"source_text": text, "language": lang},
            "translated_text",
        )
        if translated:
            return translated
    except Exception:
        pass
    return text


def translate_dosage(dosage_text: str, lang: str = "en") -> str:
    """Translate a full dosage instruction into the regional language.

    Handles common patterns like 'Once Daily', '1-0-1', 'BD', etc.
    """
    if lang == "en" or not lang:
        return dosage_text
    words = dosage_text.split()
    translated_words = []
    for word in words:
        translated_words.append(t(word, lang))
    return " ".join(translated_words)


@frappe.whitelist()
def get_prescription_translations(docname: str) -> dict:
    """Return translated prescription data for a given prescription document."""
    doc = frappe.get_doc("Healthcare Medication Prescription", docname)
    lang = getattr(doc, "prescription_language", "en")
    if lang == "en":
        return {"language": lang, "medications": []}

    translations = []
    for item in doc.medications:
        translations.append({
            "medication": item.medication,
            "dosage": translate_dosage(item.dosage or "", lang),
            "frequency": t(item.frequency or "", lang),
            "instructions": t(item.instructions or "", lang),
        })
    return {"language": lang, "medications": translations}
