from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import patient_required
from doctors.models import DoctorProfile, AvailabilitySlot


@patient_required
def dashboard(request):
    today = timezone.localdate()
    now = timezone.localtime().time()

    doctors = DoctorProfile.objects.select_related("user").all()

    # Slots are visible to patients only if they are in the future and
    # not already booked, per spec. We exclude past slots on today's date
    # using the current local time, not just the date.
    open_slots = (
        AvailabilitySlot.objects.filter(is_booked=False)
        .filter(
            models_q_future(today, now)
        )
        .select_related("doctor__user")
        .order_by("date", "start_time")
    )

    slots_by_doctor_id = {}
    for slot in open_slots:
        slots_by_doctor_id.setdefault(slot.doctor_id, []).append(slot)

    # Build a flat list of (doctor, slots) pairs so the template can loop
    # without needing dict-by-key lookups.
    doctor_rows = [
        {"doctor": doctor, "slots": slots_by_doctor_id.get(doctor.id, [])}
        for doctor in doctors
    ]

    return render(
        request,
        "patients/dashboard.html",
        {"doctor_rows": doctor_rows},
    )


def models_q_future(today, now):
    """Build the Q object for 'date is in the future, or today but later than now'."""
    from django.db.models import Q

    return Q(date__gt=today) | Q(date=today, start_time__gt=now)
