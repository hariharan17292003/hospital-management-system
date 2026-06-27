from django.db import models

from doctors.models import AvailabilitySlot
from patients.models import PatientProfile


class Booking(models.Model):
    """
    A confirmed appointment. One-to-one with the slot it consumes: a slot
    that is booked has exactly one Booking row, enforced by OneToOneField
    so the database itself rejects a second booking on the same slot even
    if application-level checks were somehow bypassed.
    """

    slot = models.OneToOneField(
        AvailabilitySlot, on_delete=models.CASCADE, related_name="booking"
    )
    patient = models.ForeignKey(
        PatientProfile, on_delete=models.CASCADE, related_name="bookings"
    )

    # Calendar sync status, populated by calendar_integration after booking.
    doctor_calendar_event_id = models.CharField(max_length=255, blank=True, default="")
    patient_calendar_event_id = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def doctor(self):
        return self.slot.doctor

    def __str__(self):
        return f"{self.patient} -> {self.slot}"
