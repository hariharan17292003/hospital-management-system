"""
Thin HTTP client the Django app uses to call the separate serverless email
microservice (see /email-service in the repo root).

Design note: the Django app never sends emails itself. It only POSTs an
event payload to the serverless function's HTTP endpoint and lets that
function decide how to send the email. This keeps email-sending logic and
its dependencies (SMTP credentials, templates) fully out of the Django
codebase, mirroring how a real microservice split would work.

Failures here are logged but, by default, never raised — see
EMAIL_SERVICE_FAIL_SILENTLY in settings. A booking or signup should not be
rolled back just because the notification side-channel is down; the
booking/account itself is the source of truth.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Raised when the serverless email service call fails and silent-fail is off."""


def _post_event(event_type: str, payload: dict):
    url = f"{settings.EMAIL_SERVICE_BASE_URL}/notify"
    body = {
        "event_type": event_type,
        "secret": settings.EMAIL_SERVICE_SHARED_SECRET,
        "data": payload,
    }
    try:
        response = requests.post(url, json=body, timeout=5)
        response.raise_for_status()
        logger.info("Email service call succeeded for event=%s", event_type)
        return response.json()
    except requests.RequestException as exc:
        logger.warning("Email service call failed for event=%s: %s", event_type, exc)
        if not settings.EMAIL_SERVICE_FAIL_SILENTLY:
            raise EmailServiceError(str(exc)) from exc
        return None


def send_signup_welcome(*, to_email: str, full_name: str, role: str):
    return _post_event(
        "SIGNUP_WELCOME",
        {"to_email": to_email, "full_name": full_name, "role": role},
    )


def send_booking_confirmation(
    *, doctor_email: str, doctor_name: str, patient_email: str,
    patient_name: str, slot_date: str, start_time: str, end_time: str,
):
    return _post_event(
        "BOOKING_CONFIRMATION",
        {
            "doctor_email": doctor_email,
            "doctor_name": doctor_name,
            "patient_email": patient_email,
            "patient_name": patient_name,
            "date": slot_date,
            "start_time": start_time,
            "end_time": end_time,
        },
    )



def send_booking_cancellation(
    *,
    doctor_email: str,
    doctor_name: str,
    patient_email: str,
    patient_name: str,
    slot_date: str,
    start_time: str,
    end_time: str,
):
    return _post_event(
        "BOOKING_CANCELLATION",
        {
            "doctor_email": doctor_email,
            "doctor_name": doctor_name,
            "patient_email": patient_email,
            "patient_name": patient_name,
            "date": slot_date,
            "start_time": start_time,
            "end_time": end_time,
        },
    )