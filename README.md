# Bizaxl Ayurvedic — Ayurvedic Store & Clinic Suite
### Frappe app for **ERPNext v15+** / **Frappe Framework v15+** (built on the Frappe Healthcare domain app, installed app name: `healthcare`)

Bizaxl Ayurvedic closes the feature gaps identified in `bizaxl`'s Ayurvedic
Store Software Gap Analysis (2026) against Healthray, Clinicea, DMA Aarogya,
EasyClinic, NeftX and VaidyaManager — and adds six AI-powered features no
competitor in the category currently offers.

---

## 1. What's in this app

| Area | Included |
|---|---|
| **Custom DocTypes** | 15 DocTypes (9 parent + 6 child tables) — see table below |
| **Custom Scripts & Automation** | Client scripts (`.js`) + server-side controller hooks (`.py`), ported from the client's original ad-hoc Client/Server Script records into version-controlled app code |
| **AI Integration** | Lead scoring, follow-up reminders, seasonal demand forecasting, WhatsApp prescription bot, AI chatbot, store benchmarking, brand loyalty tie-up, booking micro-site |
| **Reports** | Hot Leads (AI Score), Seasonal Reorder Forecast |
| **Workspace** | "Ayurvedic Store" desk workspace with shortcuts to every module |
| **Notifications** | Follow-up due, treatment visit due, prescription ready |
| **Custom Fields (patch)** | Dosha/Prakriti profile + Brand Loyalty fields on `Customer`, benchmarking opt-in fields on `Company` |
| **Website page** | `/book/<store>` — public appointment booking micro-site |
| **Settings** | Single DocType `Bizaxl Ayurvedic Settings` for WhatsApp/OCR/LLM credentials |

---

## 2. DocType map (source: `DocType.xlsx`, `Client_Script.xlsx`, `Server_Script-2.xlsx`)

| DocType | Type | Purpose |
|---|---|---|
| `Clinical Lead` | Submittable | Lead capture with Dosha-ready fields, AI lead score, one-click "Create Patient" |
| `Treatment Record` | Submittable | Customer treatment package + before/after photo gallery |
| `Treatment Photo` | Child table | Before/after image with angle & annotation (of `Treatment Record`) |
| `Healthcare Medication Prescription` | Submittable | Printable/WhatsApp-shareable prescription, auto-filled from `Patient Encounter` |
| `Healthcare Prescription Item` | Child table | Medication line item (of the prescription above) |
| `Token Counter` | Submittable | Daily OPD token queue per practitioner, auto-created from `Patient Appointment` |
| `Diet Template` | Standard | Reusable Dosha/diet-type template |
| `Diet Template Item` | Child table | Meal-time/food-item row (of `Diet Template`) |
| `Diet Plan` | Submittable, tabbed | Patient-specific diet plan; fetches a `Diet Template` and can bulk-generate kitchen logs |
| `Diet Plan Meal Schedule` | Child table | Per-meal schedule row (of `Diet Plan`) |
| `Meal Preparation Log` | Standard | Kitchen worklist: prepared / sent / served tracking |
| `Lab Test Parameter Reference` | Standard | Normal-range reference sheet per Lab Test Template |
| `Lab Test Parameter Detail` | Child table | Individual parameter range row (of the reference above) |
| `Treatment Follow-Up` | Submittable | Rolling care plan per patient; auto-extended after every consultation |
| `Follow-up Visits` | Child table | Scheduled visit row (of `Treatment Follow-Up`) |
| `Bizaxl Ayurvedic Settings` | Single | WhatsApp / OCR / LLM / loyalty configuration |

All field definitions were carried over field-for-field from the client's
`DocType.xlsx` export (options, mandatory flags, fetch-from, select values,
etc.) — nothing was invented; a few sensible defaults (e.g. status default
values) were added where the source left them blank.

---

## 3. Custom Scripts & Automation — before vs. after

The client's `Client_Script.xlsx` / `Server_Script-2.xlsx` held **ad-hoc
Client Script / Server Script DocType records** (edited live in the browser,
no version control, no code review, no test coverage). This app ports every
one of them into proper, git-tracked files:

| Original ad-hoc script | Now lives at |
|---|---|
| Treatment Followup auto-visit-date calculation | `doctype/treatment_follow_up/treatment_follow_up.js` |
| Clinical Lead → Create Patient button | `doctype/clinical_lead/clinical_lead.js` |
| Clinical Lead / Patient Encounter → Treatment Plan Cost Calculator | `doctype/clinical_lead/clinical_lead.py` (`get_treatment_plan_cost`) |
| Patient Encounter → Create Prescription | `public/js/patient_encounter.js` + `healthcare_medication_prescription.py` (`before_insert`) |
| Patient Appointment → Token Queue / auto-token creation | `public/js/patient_appointment.js` + `token_counter.py` |
| Diet Plan → Fetch Diet Template | `doctype/diet_plan/diet_plan.js` + `.py` (`get_template_rows`) |
| Diet Plan → Create Meal Logs | `doctype/diet_plan/diet_plan.py` (`create_meal_logs`) |
| Lab Test → Parameter reference panel + bulk row delete | `public/js/lab_test.js` |
| Lab Test Dashboard | simplified/hardened into the same file (heavy inline HTML from the original was trimmed for maintainability — extend `public/js/lab_test.js` if you need the full dashboard back) |
| Sample Collection → Fetch/Create Specimen | `public/js/sample_collection.js` |
| Server Script: fetch prescription from consultation | `doctype/healthcare_medication_prescription/healthcare_medication_prescription.py` (`before_insert` DocType Event) |
| Server Script: follow-up status tracking | `doctype/treatment_follow_up/treatment_follow_up.py` (`create_or_extend_from_encounter`, a module-level function), wired via `hooks.doc_events["Patient Encounter"]["after_insert"]` |

**Why this matters:** ad-hoc Client/Server Script records can't be code
reviewed, unit tested, or diffed in a pull request, and they silently break
across ERPNext upgrades. Moving them into the app means `bench migrate`,
`bench run-tests`, and normal git workflows all just work.

---

## 4. AI Integration (`bizaxl_ayurvedic/ai/`, `bizaxl_ayurvedic/integrations/`)

| Feature | Gap Analysis ref | Module |
|---|---|---|
| AI-Powered Lead Scoring & Follow-Up Reminders | Section 1, HIGH | `ai/lead_scoring.py`, `ai/follow_up_reminders.py` |
| Seasonal Herb Demand Forecasting | Section 2, Item 1 | `ai/seasonal_forecast.py` (seasonal-naive by default; auto-upgrades to Prophet if installed) |
| WhatsApp Prescription Fulfilment Bot | Section 2, Item 2 | `integrations/prescription_ocr.py` + `integrations/whatsapp.py` |
| AI Chatbot (Customer & Counter Assistant) | Section 2, Item 3 | `ai/chatbot.py` (provider-agnostic `call_llm()`) |
| Brand Loyalty Tie-Up Portal | Section 2, Item 4 | Custom fields on `Customer` (patch) + `ai/chatbot.py` loyalty-points intent |
| Ayurvedic Store Performance Benchmarking | Section 2, Item 5 | `ai/store_benchmarking.py` |
| Appointment Booking Mini-Website | Section 2, Item 6 | `www/book_appointment.py` / `.html` |
| Clinical Decision Support (Herb/Symptom Reference) | Section 1, MEDIUM | `Lab Test Parameter Reference` DocType + `public/js/lab_test.js` dashboard panel |
| Multi-Language Prescription & UI | Section 1, MEDIUM | Enable via Frappe's built-in Translation tool on `Healthcare Medication Prescription`; no extra code needed — just add Hindi/Sanskrit translations in **Setup → Translations** |
| Automated Feedback & Review Collection | Section 1, MEDIUM | `ai/chatbot.py` feedback intent + `integrations/whatsapp.py` |
| NABH-Ready Documentation & Compliance Exports | Section 1, LOW | Roadmap — not built in this pass; see §7 |

All AI modules are designed so a **rule-based / statistical default always
works out of the box** (no paid API required to install), and every module
has one clearly marked integration point for swapping in a real ML model,
Prophet, Google Vision OCR, or an LLM endpoint — configured centrally in
**Bizaxl Ayurvedic Settings**, never hard-coded.

---

## 5. Installation (Frappe Bench, ERPNext v15+)

```bash
# 1. Get the app onto your bench
cd ~/frappe-bench
bench get-app bizaxl_ayurvedic /path/to/bizaxl_ayurvedic   # or a git remote URL

# 2. Install prerequisites (ERPNext + Healthcare)
bench --site your-site.local install-app erpnext
bench --site your-site.local install-app healthcare

# 3. Install this app
bench --site your-site.local install-app bizaxl_ayurvedic

# 4. Run migrations (creates DocTypes, applies the custom-fields patch,
#    imports the workspace/notifications/roles fixtures)
bench --site your-site.local migrate

# 5. (Optional) install the seasonal-forecasting upgrade path
./env/bin/pip install "bizaxl_ayurvedic[forecasting]"

# 6. Restart
bench restart
```

After install, open **Ayurvedic Store** in the Desk sidebar (workspace),
and configure WhatsApp/OCR/LLM credentials in
**Bizaxl Ayurvedic Settings** (search bar → "Bizaxl Ayurvedic Settings").

### Enabling the AI scheduled jobs
`bench migrate` registers the scheduler events automatically (see
`hooks.py → scheduler_events`). Confirm the scheduler is enabled:

```bash
bench --site your-site.local scheduler enable
bench --site your-site.local scheduler resume
```

### WhatsApp webhook
Point your WhatsApp Business Cloud API webhook at:

```
https://your-site.local/api/method/bizaxl_ayurvedic.integrations.whatsapp.inbound_webhook
```

---

## 6. Repository layout

```
bizaxl_ayurvedic/
├── README.md
├── license.txt
├── pyproject.toml
├── requirements.txt
├── MANIFEST.in
└── bizaxl_ayurvedic/
    ├── hooks.py                     # doc_events, doctype_js, scheduler_events, fixtures
    ├── modules.txt
    ├── patches.txt
    ├── config/desktop.py
    ├── ai/                          # AI feature modules (see §4)
    ├── integrations/                # WhatsApp + OCR provider layer
    ├── patches/v0_1/add_custom_fields.py
    ├── www/book_appointment.{py,html}
    ├── public/
    │   ├── js/                      # app bundle + core-DocType extensions
    │   └── css/
    └── bizaxl_ayurvedic/                # the "Bizaxl Ayurvedic" Frappe module
        ├── doctype/                  # 15 DocTypes (JSON + .py + .js)
        ├── report/                   # Hot Leads (AI Score), Seasonal Reorder Forecast
        ├── workspace/ayurvedic_store/
        ├── notification/
        └── role/
```

---

## 7. Roadmap / not yet built in this pass

- **NABH-Ready Documentation & Compliance Exports** (LOW priority in the gap
  analysis) — scaffolding only; add a `NABH Audit Log` DocType + PDF export
  report when a customer actually needs NABH accreditation.
- **Multi-angle (4-image) photo compare slideshow** — `Treatment Record` /
  `Treatment Photo` currently render a simple 2-column before/after table;
  extend `get_compare_gallery_html()` with a carousel/lightbox for the full
  4-image compare experience.
- **Full Lab Test Dashboard** — the original ad-hoc script built an elaborate
  multi-card HTML dashboard (patient, practitioner, invoices, history). This
  app ships a trimmed, maintainable version; the original's HTML structure is
  preserved in git history / the source `Client_Script.xlsx` if you want to
  restore full fidelity.
- **Real ML lead-scoring model** — `ai/lead_scoring.py` ships a transparent,
  tunable rule-based scorer. Swap `score_lead()` for a trained classifier once
  you have enough labeled conversion data.

---

## 8. Source material this app was generated from

- `ayurvedic_gap_analysis.pdf` — bizaxl's competitor gap analysis (Section 1)
  and white-space AI opportunities (Section 2)
- `DocType.xlsx` — full field-level export of the 15 target DocTypes
- `Client_Script.xlsx` — 12 ad-hoc Client Scripts, ported to versioned `.js`
- `Server_Script-2.xlsx` — 2 ad-hoc Server Scripts, ported to versioned `.py`
  DocType Event hooks
