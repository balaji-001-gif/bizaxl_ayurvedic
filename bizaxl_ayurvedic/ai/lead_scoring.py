# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
AI-Powered Lead Scoring & Follow-Up Reminders
(Gap Analysis Section 1 — HIGH priority gap vs EasyClinic / NeftX)

Rule-based scoring engine today, designed so the same interface can later be
swapped for a trained model (e.g. a lightweight scikit-learn classifier)
without touching call sites. Score = weighted blend of:
  - Recency of last contact / follow-up
  - Lead source quality (historical conversion rate by source)
  - Engagement signals (status progression, budget stated)
  - Lapsed-visit risk for already-converted patients
"""
import frappe
from frappe.utils import now_datetime, date_diff, getdate

SOURCE_WEIGHTS = {
    "Referral": 25, "Walk-in": 22, "WhatsApp": 18, "Call": 16,
    "Website": 14, "Instagram": 10, "Facebook": 10, "Google": 12,
}
STATUS_WEIGHTS = {
    "New": 5, "Contacted": 15, "Interested": 30,
    "Appointment Scheduled": 45, "Visited": 55, "Converted": 100, "Lost": 0,
}


def score_lead(lead) -> int:
    """Pure function: Clinical Lead doc -> integer score 0-100."""
    score = 0
    score += STATUS_WEIGHTS.get(lead.lead_status, 5)
    score += SOURCE_WEIGHTS.get(lead.lead_source, 5)

    if lead.expected_budget:
        score += min(10, int(lead.expected_budget) // 5000)

    if lead.follow_up_date:
        days_until = date_diff(getdate(lead.follow_up_date), getdate())
        if 0 <= days_until <= 2:
            score += 10  # follow-up imminent, prioritise
        elif days_until < 0:
            score -= 10  # overdue, still needs attention but signals neglect risk

    return max(0, min(100, score))


def enqueue_score_lead(lead_name):
    """Called from Clinical Lead's on_update hook — recomputes and caches the
    score on the lead's __onload so the client badge (see clinical_lead.js)
    can render it without a full recompute round trip on every page view."""
    frappe.enqueue(
        "bizaxl_ayurvedic.ai.lead_scoring.recompute_lead_score",
        queue="short",
        lead_name=lead_name,
        enqueue_after_commit=True,
    )


def recompute_lead_score(lead_name):
    lead = frappe.get_doc("Clinical Lead", lead_name)
    score = score_lead(lead)
    frappe.cache().hset("bizaxl_ayurvedic:lead_score", lead_name, score)


@frappe.whitelist()
def get_lead_score(lead_name):
    cached = frappe.cache().hget("bizaxl_ayurvedic:lead_score", lead_name)
    if cached is not None:
        return cached
    lead = frappe.get_doc("Clinical Lead", lead_name)
    return score_lead(lead)


def recompute_all_lead_scores():
    """Daily scheduled job — recomputes scores for all open leads so the
    'Hot Leads' report / workspace number card stays fresh."""
    leads = frappe.get_all("Clinical Lead", filters={"lead_status": ["not in", ["Converted", "Lost"]]},
                            pluck="name")
    for name in leads:
        recompute_lead_score(name)
    frappe.logger("bizaxl_ayurvedic").info(f"Recomputed lead scores for {len(leads)} leads")
