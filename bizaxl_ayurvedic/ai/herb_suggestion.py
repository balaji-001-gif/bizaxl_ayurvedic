# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Clinical Decision Support — Herb / Symptom Reference Engine
(Gap Analysis — MEDIUM priority gap vs AyurCDS)

Symptom-aware herb suggestion engine that queries the Ayurvedic Herb Reference
doctype and returns classical formulation recommendations. Embedded in the
prescription builder so counter staff and practitioners can find appropriate
herbs for common symptoms without switching screens.

Usage:
    from bizaxl_ayurvedic.ai.herb_suggestion import suggest_herbs_for_symptom

    results = suggest_herbs_for_symptom("indigestion")
    # -> [{"herb": "Haritaki", "formulation": "Triphala", ...}, ...]
"""
import frappe


@frappe.whitelist()
def suggest_herbs_for_symptom(symptom: str, limit: int = 5) -> list[dict]:
    """Search the Ayurvedic Herb Reference for herbs indicated for a symptom.

    Matches against both the symptom name and symptom type fields in the
    Herb Symptom Map child table. Returns the top N matches ordered by
    relevance.
    """
    if not symptom or len(symptom.strip()) < 2:
        return []

    symptom = symptom.strip().lower()

    # Find herbs whose symptom_map contains this symptom (fuzzy via LIKE)
    herb_symptom_rows = frappe.db.sql(
        """
        SELECT DISTINCT
            hsm.parent AS herb_name,
            hsm.symptom AS matched_symptom,
            hsm.formulation AS recommended_formulation,
            hsm.symptom_type
        FROM `tabHerb Symptom Map` hsm
        WHERE LOWER(hsm.symptom) LIKE %(symptom)s
           OR LOWER(hsm.symptom_type) LIKE %(symptom)s
        LIMIT %(limit)s
        """,
        {"symptom": f"%{symptom}%", "limit": limit},
        as_dict=True,
    )

    # Enrich results with herb details
    results = []
    for row in herb_symptom_rows:
        herb_doc = frappe.get_cached_doc("Ayurvedic Herb Reference", row.herb_name)
        results.append({
            "herb_name": row.herb_name,
            "sanskrit_name": herb_doc.sanskrit_name or "",
            "dosha_effect": herb_doc.dosha_effect or "",
            "matched_symptom": row.matched_symptom,
            "recommended_formulation": row.recommended_formulation or "",
            "classical_formulations": herb_doc.classical_formulations or "",
            "typical_dosage": herb_doc.typical_dosage or "",
            "contraindications": herb_doc.contraindications or "",
        })

    # Fallback: if no symptom_map matches, try direct name match
    if not results:
        direct = frappe.db.get_all(
            "Ayurvedic Herb Reference",
            filters={"herb_name": ["like", f"%{symptom}%"]},
            fields=["herb_name", "sanskrit_name", "dosha_effect",
                    "classical_formulations", "typical_dosage", "contraindications"],
            limit_page_length=limit,
        )
        for d in direct:
            results.append({
                "herb_name": d.herb_name,
                "sanskrit_name": d.sanskrit_name or "",
                "dosha_effect": d.dosha_effect or "",
                "matched_symptom": "",
                "recommended_formulation": "",
                "classical_formulations": d.classical_formulations or "",
                "typical_dosage": d.typical_dosage or "",
                "contraindications": d.contraindications or "",
            })

    return results


@frappe.whitelist()
def get_common_symptoms() -> list[str]:
    """Return a deduplicated list of all symptoms catalogued in the system."""
    rows = frappe.db.sql(
        "SELECT DISTINCT symptom FROM `tabHerb Symptom Map` ORDER BY symptom"
    )
    return [r[0] for r in rows if r[0]]


@frappe.whitelist()
def get_herbs_for_dosha(dosha_type: str) -> list[dict]:
    """Return herbs that pacify a given dosha type."""
    if not dosha_type:
        return []

    # Normalize: "Vata" -> "Vata-Pacifying"
    dosha_filter = f"{dosha_type}-Pacifying"

    herbs = frappe.db.get_all(
        "Ayurvedic Herb Reference",
        filters={"dosha_effect": ["like", f"%{dosha_filter}%"]},
        fields=["herb_name", "sanskrit_name", "dosha_effect",
                "classical_formulations", "typical_dosage"],
        limit_page_length=10,
    )
    return herbs
