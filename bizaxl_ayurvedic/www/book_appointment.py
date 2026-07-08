# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Agent-Branded Appointment Booking Mini-Website
(Gap Analysis Section 2, Item 6 — white-space opportunity)

Public-facing page at /book/<store> (see hooks.website_route_rules) that lets
customers pick a practitioner, date, and therapy slot without calling the
store. Submissions create a Patient Appointment directly, and a WhatsApp
confirmation is sent via bizaxl_ayurvedic.integrations.whatsapp.
"""
import frappe


def get_context(context):
    store = frappe.form_dict.get("store") or frappe.local.request.args.get("store")
    context.no_cache = 1
    context.store = store
    context.practitioners = frappe.get_all(
        "Healthcare Practitioner",
        filters={"status": "Active"},
        fields=["name", "practitioner_name", "department"],
    )
    context.therapy_types = frappe.get_all("Therapy Type", fields=["name", "therapy_type"], limit_page_length=20)
    return context


@frappe.whitelist(allow_guest=True)
def submit_booking(practitioner, therapy_type, date, time, patient_name, mobile_number):
    appointment = frappe.get_doc({
        "doctype": "Patient Appointment",
        "practitioner": practitioner,
        "therapy_type": therapy_type,
        "appointment_date": date,
        "appointment_time": time,
        "patient_name": patient_name,
        "mobile": mobile_number,
        "source": "Online Booking",
    })
    appointment.flags.ignore_mandatory = True
    appointment.insert(ignore_permissions=True)

    from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
    send_text_message(
        mobile_number,
        f"Your appointment with {practitioner} is booked for {date} {time}. "
        f"Reference: {appointment.name}",
    )
    return {"name": appointment.name}
