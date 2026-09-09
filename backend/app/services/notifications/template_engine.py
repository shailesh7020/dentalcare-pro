from __future__ import annotations

import re


def render_template(template_str: str, context: dict[str, str | int | float | None]) -> str:
    """Replaces {{variable_name}} with context values cleanly."""
    if not template_str:
        return ""

    def replace_match(match: re.Match) -> str:
        key = match.group(1).strip()
        val = context.get(key)
        return str(val) if val is not None else ""

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace_match, template_str)


DEFAULT_TEMPLATES: dict[str, dict[str, str]] = {
    "APPOINTMENT_BOOKED": {
        "subject": "Appointment Confirmation: {{clinic_name}}",
        "body": "Hello {{patient_name}}, your dental visit with Dr. {{dentist_name}} is confirmed for {{appointment_date}} at {{appointment_time}}. Please arrive 10 minutes early. - {{clinic_name}}",
    },
    "APPOINTMENT_REMINDER": {
        "subject": "Upcoming Visit Reminder: {{clinic_name}}",
        "body": "Hi {{patient_name}}, this is a friendly reminder for your appointment on {{appointment_date}} at {{appointment_time}} with Dr. {{dentist_name}}. Clinic contact: {{clinic_phone}}.",
    },
    "APPOINTMENT_CANCELLED": {
        "subject": "Appointment Cancelled: {{clinic_name}}",
        "body": "Hello {{patient_name}}, your appointment on {{appointment_date}} has been cancelled as requested. Reason: {{cancellation_reason}}.",
    },
    "APPOINTMENT_RESCHEDULED": {
        "subject": "Appointment Rescheduled: {{clinic_name}}",
        "body": "Hello {{patient_name}}, your appointment has been rescheduled to {{appointment_date}} at {{appointment_time}} with Dr. {{dentist_name}}.",
    },
    "FOLLOW_UP_REMINDER": {
        "subject": "Clinical Follow-Up Care Due: {{clinic_name}}",
        "body": "Dear {{patient_name}}, it is time for your follow-up check following your {{procedure_name}} procedure. Due on: {{follow_up_date}}. Call {{clinic_phone}} to reserve your chair.",
    },
    "PRESCRIPTION_READY": {
        "subject": "Prescription Ready: {{prescription_number}}",
        "body": "Hello {{patient_name}}, your prescription ({{prescription_number}}) issued by Dr. {{dentist_name}} is now ready. You can view or download your medication plan on the DentalCare Pro Patient Portal.",
    },
    "INVOICE_GENERATED": {
        "subject": "Treatment Invoice: {{invoice_number}}",
        "body": "Dear {{patient_name}}, invoice {{invoice_number}} for ₹{{amount}} has been generated for your treatment at {{clinic_name}}. Balance due: ₹{{balance_due}}.",
    },
    "PAYMENT_RECEIVED": {
        "subject": "Payment Receipt: {{receipt_number}}",
        "body": "Thank you {{patient_name}}! We received your payment of ₹{{amount}} via {{payment_method}} for invoice {{invoice_number}}. Receipt {{receipt_number}} is available in your patient portal.",
    },
}


class NotificationTemplateEngine:
    @staticmethod
    def render_text(template_str: str, context: dict[str, str | int | float | None]) -> str:
        return render_template(template_str, context)

