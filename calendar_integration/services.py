"""
Creates the Google Calendar event for a confirmed booking, on both the
doctor's and patient's own calendars.

Each side's event is created using that user's own stored OAuth2
credentials (see models.GoogleCalendarCredential) -- there is no shared
service account. If a user hasn't connected Google yet, we skip that
side's event and let the caller decide how to surface that (see
bookings/views.py, which treats this as best-effort and never fails the
booking itself).
"""

import datetime as dt

from django.utils import timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .models import GoogleCalendarCredential


def _credentials_for(user):
    try:
        cred = GoogleCalendarCredential.objects.get(user=user)
    except GoogleCalendarCredential.DoesNotExist:
        return None

    return Credentials(
        token=cred.access_token,
        refresh_token=cred.refresh_token or None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=_client_id(),
        client_secret=_client_secret(),
        scopes=cred.scope.split() if cred.scope else None,
    )


def _client_id():
    from django.conf import settings

    return settings.GOOGLE_CLIENT_ID


def _client_secret():
    from django.conf import settings

    return settings.GOOGLE_CLIENT_SECRET


def _create_event_for_user(user, *, title: str, description: str, slot):
    credentials = _credentials_for(user)
    if credentials is None:
        return None  # user hasn't connected Google Calendar; skip silently

    service = build("calendar", "v3", credentials=credentials)

    start_dt = dt.datetime.combine(slot.date, slot.start_time)
    end_dt = dt.datetime.combine(slot.date, slot.end_time)
    tz_name = timezone.get_current_timezone_name()

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": tz_name},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": tz_name},
    }

    created = service.events().insert(calendarId="primary", body=event_body).execute()
    return created.get("id")


def create_booking_calendar_events(booking):
    slot = booking.slot
    doctor_user = slot.doctor.user
    patient_user = booking.patient.user

    doctor_name = doctor_user.get_full_name() or doctor_user.username
    patient_name = patient_user.get_full_name() or patient_user.username

    # Event on the patient's calendar, titled with the doctor's name.
    patient_event_id = _create_event_for_user(
        patient_user,
        title=f"Appointment with Dr. {doctor_name}",
        description="Appointment booked via Mini HMS.",
        slot=slot,
    )

    # Event on the doctor's calendar, titled with the patient's name.
    doctor_event_id = _create_event_for_user(
        doctor_user,
        title=f"Appointment with {patient_name}",
        description="Appointment booked via Mini HMS.",
        slot=slot,
    )

    update_fields = []
    if patient_event_id:
        booking.patient_calendar_event_id = patient_event_id
        update_fields.append("patient_calendar_event_id")
    if doctor_event_id:
        booking.doctor_calendar_event_id = doctor_event_id
        update_fields.append("doctor_calendar_event_id")
    if update_fields:
        booking.save(update_fields=update_fields)
