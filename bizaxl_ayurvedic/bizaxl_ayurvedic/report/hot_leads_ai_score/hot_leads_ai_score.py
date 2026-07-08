# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""Script Report: ranks open Clinical Leads by their AI lead score (see
bizaxl_ayurvedic/ai/lead_scoring.py) so counsellors always work the hottest
leads first — directly answers the 'AI-Powered Lead Scoring & Follow-Up
Reminders' gap (HIGH priority)."""
import frappe
from bizaxl_ayurvedic.ai.lead_scoring import get_lead_score


def execute(filters=None):
    columns = [
        {"label": "Lead", "fieldname": "name", "fieldtype": "Link", "options": "Clinical Lead", "width": 140},
        {"label": "Lead Name", "fieldname": "lead_name", "fieldtype": "Data", "width": 160},
        {"label": "Status", "fieldname": "lead_status", "fieldtype": "Data", "width": 130},
        {"label": "Source", "fieldname": "lead_source", "fieldtype": "Data", "width": 110},
        {"label": "Follow Up Date", "fieldname": "follow_up_date", "fieldtype": "Date", "width": 120},
        {"label": "Counsellor", "fieldname": "counsellor", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 150},
        {"label": "AI Score", "fieldname": "ai_score", "fieldtype": "Int", "width": 90},
    ]

    leads = frappe.get_all(
        "Clinical Lead",
        filters={"lead_status": ["not in", ["Converted", "Lost"]]},
        fields=["name", "lead_name", "lead_status", "lead_source", "follow_up_date", "counsellor"],
    )
    for lead in leads:
        lead["ai_score"] = get_lead_score(lead["name"])

    leads.sort(key=lambda r: r["ai_score"], reverse=True)
    return columns, leads
