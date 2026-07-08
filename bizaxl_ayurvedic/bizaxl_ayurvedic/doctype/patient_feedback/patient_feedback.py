# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PatientFeedback(Document):
    def validate(self):
        if self.rating:
            if self.rating >= 4:
                self.sentiment = "Positive"
            elif self.rating >= 3:
                self.sentiment = "Neutral"
            else:
                self.sentiment = "Negative"

    def on_update(self):
        """If rating >= 4 and we have a Google Review URL, flag for sending.

        Uses on_update (not after_insert) because feedbacks are first created
        with rating=0 (pending), then updated with the actual rating from the
        customer's WhatsApp reply. on_update fires on both insert and update.
        """
        if self.rating and self.rating >= 4 and not self.google_review_link_sent:
            settings = frappe.get_single("Bizaxl Ayurvedic Settings")
            if settings.google_review_url:
                self.db_set("google_review_link_sent", 1)
                # WhatsApp the Google Review link
                mobile = frappe.db.get_value("Customer", self.customer, "mobile_no") if self.customer else None
                if mobile:
                    from bizaxl_ayurvedic.integrations.whatsapp import send_text_message
                    send_text_message(
                        mobile,
                        f"Thank you for your feedback! We're glad you loved our service. "
                        f"Could you share your experience on Google: {settings.google_review_url}"
                    )
