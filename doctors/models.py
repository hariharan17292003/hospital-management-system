from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    specialization = models.CharField(max_length=120)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"


class AvailabilitySlot(models.Model):
    """
    A single bookable time window for a doctor.

    Ownership: every slot belongs to exactly one doctor
    (doctor = ForeignKey, never nullable). This is what makes "doctors can
    only see/manage their own slots" enforceable at the queryset level —
    every doctor-facing view filters `AvailabilitySlot.objects.filter(doctor=request.user.doctor_profile)`
    rather than trusting a slot id passed in from the client.
    """

    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="slots"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # is_booked is the field the race-condition handling logic guards.
    # See bookings/services.py for how this is updated atomically.
    is_booked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "start_time", "end_time"],
                name="unique_slot_per_doctor_datetime",
            )
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self):
        return f"{self.doctor} | {self.date} {self.start_time}-{self.end_time}"
