app_name = "bizaxl_ayurvedic"
app_title = "Bizaxl Ayurvedic"
app_publisher = "bizaxl"
app_description = "Ayurvedic Store & Clinic Suite for ERPNext v15+ — closes the competitive gaps " \
                   "identified against Healthray, Clinicea, DMA Aarogya, EasyClinic, NeftX and " \
                   "VaidyaManager, and layers on AI features no competitor currently offers."
app_email = "sales@bizaxl.com"
app_license = "MIT"
app_icon = "octicon octicon-pulse"
app_color = "#2f7d5c"
required_apps = ["erpnext", "healthcare"]  # ERPNext + Frappe Healthcare v15+
# NOTE: required_apps must list the app's actual module/folder name as it
# appears under `apps/` and in `sites/apps.txt` — NOT a GitHub "org/repo"
# path. The Healthcare domain app's real module name is "healthcare"
# (github.com/frappe/health, but the installable app package is "healthcare").

# ------------------------------------------------------------------
# Includes: bring in the app-wide bundle plus per-form JS extensions.
# doctype_js only applies to DocTypes that are NOT owned by this app
# (Healthcare/core doctypes); app-owned doctypes load their own
# doctype/<name>/<name>.js automatically.
# ------------------------------------------------------------------
app_include_js = ["/assets/bizaxl_ayurvedic/js/bizaxl_ayurvedic.bundle.js"]
app_include_css = ["/assets/bizaxl_ayurvedic/css/bizaxl_ayurvedic.css"]

doctype_js = {
    "Patient Encounter": "public/js/patient_encounter.js",
    "Patient Appointment": "public/js/patient_appointment.js",
    "Lab Test": "public/js/lab_test.js",
    "Sample Collection": "public/js/sample_collection.js",
    "Treatment Plan Template": "public/js/treatment_plan_template.js",
    "Patient Assessment": "public/js/patient_assessment.js",
    "Therapy Session": "public/js/therapy_session.js",
}

# ------------------------------------------------------------------
# DocType Event hooks — server-side automation
# (These replace the client's original ad-hoc "Server Script" doctype
# records with proper, version-controlled Python in each controller.)
# ------------------------------------------------------------------
doc_events = {
    "Patient Encounter": {
        "on_submit": "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.treatment_follow_up.treatment_follow_up.create_or_extend_from_encounter",
    },
    "Sales Invoice": {
        "on_submit": "bizaxl_ayurvedic.ai.feedback_collector.request_feedback_after_billing",
    },
    "Treatment Plan Template": {
        "validate": "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.clinical_lead.populate_drug_rates_from_master",
    },
    "Patient Appointment": {
        "before_insert": "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.assign_token_number",
    },
}

# ------------------------------------------------------------------
# Scheduled jobs — AI features from the Gap Analysis "white-space" list
# ------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "bizaxl_ayurvedic.ai.lead_scoring.recompute_all_lead_scores",
        "bizaxl_ayurvedic.ai.follow_up_reminders.send_due_follow_up_reminders",
        "bizaxl_ayurvedic.ai.feedback_collector.send_pending_feedback_requests",
    ],
    "weekly": [
        "bizaxl_ayurvedic.ai.seasonal_forecast.generate_reorder_forecast",
        "bizaxl_ayurvedic.ai.store_benchmarking.compute_store_benchmarks",
    ],
}

# ------------------------------------------------------------------
# Fixtures — export workspace / notifications / custom roles with the app
# ------------------------------------------------------------------
fixtures = [
    {"dt": "Workspace", "filters": [["name", "=", "Ayurvedic Store"]]},
    {"dt": "Notification", "filters": [["module", "=", "Bizaxl Ayurvedic"]]},
    {"dt": "Role", "filters": [["name", "in", ["Ayurvedic Store Manager", "Ayurvedic Counsellor"]]]},
    {"dt": "Translation", "filters": [["module", "=", "Bizaxl Ayurvedic"]]},
]

# ------------------------------------------------------------------
# Website / portal routes for the AI Appointment Booking micro-site concept
# (see gap analysis Section 2, item 6)
# ------------------------------------------------------------------
website_route_rules = [
    {"from_route": "/book/<store>", "to_route": "book_appointment"},
]

# ------------------------------------------------------------------
# Whitelisted REST-style API surface (see bizaxl_ayurvedic/api/)
# ------------------------------------------------------------------
# Exposed automatically via @frappe.whitelist() decorators in bizaxl_ayurvedic/api/*.py
# Reachable at /api/method/bizaxl_ayurvedic.api.<module>.<function>

# ------------------------------------------------------------------
# Standard boilerplate placeholders (kept for easy extension)
# ------------------------------------------------------------------
# permission_query_conditions = {}
# override_doctype_class = {}
# on_session_creation = []
# boot_session = "bizaxl_ayurvedic.boot.boot_session"
