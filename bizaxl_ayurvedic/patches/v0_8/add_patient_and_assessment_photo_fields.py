# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Adds an Attach Image field on Patient doctype and an Attach Image field on
Patient Assessment doctype so that staff can upload patient photos and
session assessment photos that are clickable and viewable from the form.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Patient": [
            {
                "fieldname": "patient_photo_cb",
                "fieldtype": "Column Break",
                "insert_after": "lifestyle_observations",
            },
            {
                "fieldname": "patient_photo",
                "label": "Patient Photo",
                "fieldtype": "Attach Image",
                "insert_after": "patient_photo_cb",
                "description": "Upload a patient photo for identification. Click the image to view full size.",
                "allow_read_on_all_document_types": 1,
            },
        ],
        "Patient Assessment": [
            {
                "fieldname": "assessment_photo",
                "label": "Assessment Photo",
                "fieldtype": "Attach Image",
                "insert_after": "assessment_description",
                "description": "Attach a photo related to this assessment. Click the image to view full size.",
                "allow_read_on_all_document_types": 1,
            },
            {
                "fieldname": "section_break_assessment_photo_2",
                "fieldtype": "Section Break",
                "insert_after": "assessment_photo",
            },
        ],
    })
