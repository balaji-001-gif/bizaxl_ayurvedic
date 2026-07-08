# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
from frappe import _


def get_data():
    return [
        {
            "module_name": "Bizaxl Ayurvedic",
            "category": "Modules",
            "label": _("Ayurvedic Store"),
            "color": "#2f7d5c",
            "icon": "octicon octicon-pulse",
            "type": "module",
            "description": "Ayurvedic Store & Clinic Suite — CRM, treatment records, prescriptions, "
                            "diet plans and AI automation.",
        }
    ]
