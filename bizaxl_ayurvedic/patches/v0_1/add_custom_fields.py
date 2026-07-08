# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds the custom fields this app's automation depends on, on top of core
Customer / Company doctypes — run automatically on `bench migrate`.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Customer": [
            {
                "fieldname": "ayurvedic_profile_tab",
                "fieldtype": "Tab Break",
                "label": "Ayurvedic Profile",
                "insert_after": "companies",
            },
            {
                "fieldname": "dosha_type",
                "fieldtype": "Select",
                "label": "Prakriti / Dosha Type",
                "options": "\nVata\nPitta\nKapha\nVata-Pitta\nPitta-Kapha\nVata-Kapha\nTridosha",
                "insert_after": "ayurvedic_profile_tab",
                "description": "Closes the 'Prakriti/Dosha Customer Profiling' CRITICAL gap "
                                "vs Healthray, DMA Aarogya, Clinicea, EasyClinic, VaidyaManager.",
            },
            {
                "fieldname": "column_break_dosha",
                "fieldtype": "Column Break",
                "insert_after": "dosha_type",
            },
            {
                "fieldname": "dietary_notes",
                "fieldtype": "Small Text",
                "label": "Dietary Notes",
                "insert_after": "column_break_dosha",
            },
            {
                "fieldname": "lifestyle_observations",
                "fieldtype": "Small Text",
                "label": "Lifestyle Observations",
                "insert_after": "dietary_notes",
            },
            {
                "fieldname": "sb_brand_loyalty",
                "fieldtype": "Section Break",
                "label": "Brand Loyalty Tie-Up",
                "insert_after": "lifestyle_observations",
            },
            {
                "fieldname": "custom_brand_loyalty_program",
                "fieldtype": "Select",
                "label": "Brand Loyalty Program",
                "options": "\nPatanjali Samridhi\nDabur Rewards\nOther",
                "insert_after": "sb_brand_loyalty",
                "description": "Brand Loyalty Tie-Up Portal — Gap Analysis Section 2, Item 4.",
            },
            {
                "fieldname": "custom_brand_loyalty_code",
                "fieldtype": "Data",
                "label": "Brand Loyalty Code",
                "insert_after": "custom_brand_loyalty_program",
            },
            {
                "fieldname": "cb_brand_loyalty",
                "fieldtype": "Column Break",
                "insert_after": "custom_brand_loyalty_code",
            },
            {
                "fieldname": "custom_brand_loyalty_points",
                "fieldtype": "Float",
                "label": "Consolidated Brand Loyalty Points",
                "insert_after": "cb_brand_loyalty",
                "read_only": 1,
            },
        ],
        "Company": [
            {
                "fieldname": "sb_store_benchmarking",
                "fieldtype": "Section Break",
                "label": "Ayurvedic Store Benchmarking",
                "insert_after": "date_of_incorporation",
                "collapsible": 1,
            },
            {
                "fieldname": "custom_share_benchmark_data",
                "fieldtype": "Check",
                "label": "Opt in to anonymised bizaxl Store Intelligence benchmarking",
                "insert_after": "sb_store_benchmarking",
                "description": "Gap Analysis Section 2, Item 5.",
            },
            {
                "fieldname": "custom_store_area_sqft",
                "fieldtype": "Float",
                "label": "Store Floor Area (sq ft)",
                "insert_after": "custom_share_benchmark_data",
            },
        ],
    })
