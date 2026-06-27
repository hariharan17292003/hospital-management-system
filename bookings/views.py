import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import doctor_required, patient_required
from accounts.email_client import (
    send_booking_confirmation,
    send_booking_cancellation,
)
from calendar_integration.services import create_booking_calendar_events
from .models import Booking
from .services import SlotAlreadyBookedError, book_slot

logger = logging.getLogger(__name__)


@patient_required
def create_booking(request, slot_id):
    if request.method != "POST":
        return redirect("patients:dashboard")

    patient_profile = request.user.patient_profile

    try:
        booking = book_slot(
            patient_profile=patient_profile,
            slot_id=slot_id,
        )
    except SlotAlreadyBookedError as exc:
        messages.error(request, str(exc))
        return redirect("patients:dashboard")

    slot = booking.slot
    doctor_user = slot.doctor.user
    patient_user = patient_profile.user

    # Google Calendar Sync
    try:
        create_booking_calendar_events(booking)
    except Exception:
        logger.exception(
            "Calendar sync failed for booking %s",
            booking.id,
        )

        messages.warning(
            request,
            "Booking confirmed, but we couldn't sync to Google Calendar.",
        )

    # Booking confirmation email
    send_booking_confirmation(
        doctor_email=doctor_user.email,
        doctor_name=doctor_user.get_full_name() or doctor_user.username,
        patient_email=patient_user.email,
        patient_name=patient_user.get_full_name() or patient_user.username,
        slot_date=str(slot.date),
        start_time=str(slot.start_time),
        end_time=str(slot.end_time),
    )

    messages.success(
        request,
        "Appointment booked successfully.",
    )

    return redirect("bookings:my_bookings")


@patient_required
def my_bookings_patient(request):

    bookings = (
        Booking.objects.filter(
            patient=request.user.patient_profile
        )
        .select_related(
            "slot__doctor__user"
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "bookings/my_bookings.html",
        {
            "bookings": bookings,
        },
    )


@doctor_required
def my_bookings_doctor(request):

    bookings = (
        Booking.objects.filter(
            slot__doctor=request.user.doctor_profile
        )
        .select_related(
            "slot",
            "patient__user",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "bookings/doctor_bookings.html",
        {
            "bookings": bookings,
        },
    )


@patient_required
def cancel_booking(request, booking_id):

    if request.method != "POST":
        return redirect("bookings:my_bookings")

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        patient=request.user.patient_profile,
    )

    slot = booking.slot
    doctor = slot.doctor.user
    patient = booking.patient.user

    # Make slot available again
    slot.is_booked = False
    slot.save()

    # Send cancellation email via serverless email service
    try:
        send_booking_cancellation(
            doctor_email=doctor.email,
            doctor_name=doctor.get_full_name() or doctor.username,
            patient_email=patient.email,
            patient_name=patient.get_full_name() or patient.username,
            slot_date=str(slot.date),
            start_time=str(slot.start_time),
            end_time=str(slot.end_time),
        )
    except Exception:
        logger.exception(
            "Failed to send booking cancellation email."
        )

    # Delete booking
    booking.delete()

    messages.success(
        request,
        "Your appointment has been cancelled successfully.",
    )

    return redirect("bookings:my_bookings")