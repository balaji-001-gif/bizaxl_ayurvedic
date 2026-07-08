# Changelog

All notable changes to the **Bizaxl Ayurvedic** app will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-07-08

### Added

#### DocTypes (15 total — 9 parent + 6 child tables)
- **Clinical Lead** — Lead capture with Dosha-ready fields, AI lead score, and one-click "Create Patient" conversion
- **Treatment Record** — Customer treatment package with before/after photo gallery
- **Treatment Photo** (child) — Before/after image with angle & annotation
- **Healthcare Medication Prescription** — Printable/WhatsApp-shareable prescription, auto-filled from Patient Encounter
- **Healthcare Prescription Item** (child) — Medication line item
- **Token Counter** — Daily OPD token queue per practitioner, auto-created from Patient Appointment
- **Diet Template** — Reusable Dosha/diet-type template
- **Diet Template Item** (child) — Meal-time / food-item row
- **Diet Plan** — Patient-specific diet plan with tabbed UI; fetches a Diet Template and can bulk-generate kitchen logs
- **Diet Plan Meal Schedule** (child) — Per-meal schedule row
- **Meal Preparation Log** — Kitchen worklist: prepared / sent / served tracking
- **Lab Test Parameter Reference** — Normal-range reference sheet per Lab Test Template
- **Lab Test Parameter Detail** (child) — Individual parameter range row
- **Treatment Follow-Up** — Rolling care plan per patient; auto-extended after every consultation
- **Follow-up Visits** (child) — Scheduled visit row
- **Bizaxl Ayurvedic Settings** (Single) — WhatsApp / OCR / LLM / loyalty configuration

#### AI Features (6 features, `bizaxl_ayurvedic/ai/`)
- AI-Powered Lead Scoring (`ai/lead_scoring.py`)
- AI Follow-Up Reminders (`ai/follow_up_reminders.py`)
- Seasonal Herb Demand Forecasting (`ai/seasonal_forecast.py` — seasonal-naive default, auto-upgrades to Prophet)
- AI Chatbot for Customer & Counter Assistant (`ai/chatbot.py` — provider-agnostic `call_llm()`)
- Ayurvedic Store Performance Benchmarking (`ai/store_benchmarking.py`)
- Brand Loyalty Tie-Up Portal (custom fields on `Customer` + chatbot loyalty intent)

#### Integrations (`bizaxl_ayurvedic/integrations/`)
- WhatsApp Prescription Fulfilment Bot (`integrations/whatsapp.py`)
- Prescription OCR processing (`integrations/prescription_ocr.py`)

#### Website
- Public appointment booking micro-site at `/book/<store>` (`www/book_appointment.py` + `.html`)

#### Reports
- **Hot Leads (AI Score)** — AI-scored lead ranking report
- **Seasonal Reorder Forecast** — Forecasting report for herb/drug inventory

#### Automation & Scripting
- All 12 ad-hoc Client Scripts ported from `Client_Script.xlsx` into version-controlled `.js` files
- All 2 ad-hoc Server Scripts ported from `Server_Script-2.xlsx` into version-controlled `.py` DocType Event hooks
- Treatment Follow-up auto-visit-date calculation
- Clinical Lead → Create Patient button
- Treatment Plan Cost Calculator
- Patient Encounter → Create Prescription workflow
- Patient Appointment → Token Queue auto-creation
- Diet Plan → Fetch Diet Template & Create Meal Logs
- Lab Test parameter reference panel + bulk row delete
- Sample Collection → Fetch/Create Specimen

#### Workspace
- "Ayurvedic Store" desk workspace with shortcuts to every module

#### Notifications
- Clinical Lead Follow-Up Due
- Treatment Follow-Up Visit Due
- Prescription Ready for Dispatch

#### Roles
- Ayurvedic Store Manager
- Ayurvedic Counsellor

#### Custom Fields (patch `v0_1/add_custom_fields.py`)
- Dosha / Prakriti profile fields on `Customer`
- Brand Loyalty fields on `Customer`
- Benchmarking opt-in fields on `Company`

#### Infrastructure
- Scheduler events for all AI background jobs
- Scheduler events for follow-up reminders
- WhatsApp webhook endpoint (`/api/method/bizaxl_ayurvedic.integrations.whatsapp.inbound_webhook`)
- `pyproject.toml` with Flit build backend and optional Prophet forecasting support

---

## [Unreleased]

### Planned
- **NABH-Ready Documentation & Compliance Exports** — `NABH Audit Log` DocType + PDF export report
- **Multi-angle (4-image) photo compare slideshow** — Carousel/lightbox for the full 4-image compare experience
- **Full Lab Test Dashboard** — Restore the original elaborate multi-card HTML dashboard
- **Real ML lead-scoring model** — Trained classifier to replace the rule-based scorer

---

[0.1.0]: https://github.com/balaji-001-gif/bizaxl_ayurvedic/releases/tag/v0.1.0
