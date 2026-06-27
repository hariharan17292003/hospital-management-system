from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.decorators import doctor_required
from .forms import AvailabilitySlotForm
from .models import AvailabilitySlot


@doctor_required
def dashboard(request):
    profile = request.user.doctor_profile
    # Ownership enforced here: always scoped to request.user's own profile,
    # never to a doctor id taken from the request.
    upcoming_slots = profile.slots.filter(
        date__gte=timezone.localdate()
    ).order_by("date", "start_time")
    bookings = profile.user.bookings_as_doctor.select_related(
        "patient__user", "slot"
    ).order_by("-created_at")[:20] if hasattr(profile.user, "bookings_as_doctor") else []
    return render(
        request,
        "doctors/dashboard.html",
        {"profile": profile, "slots": upcoming_slots, "bookings": bookings},
    )


@doctor_required
def create_slot(request):
    profile = request.user.doctor_profile
    if request.method == "POST":
        form = AvailabilitySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = profile
            try:
                slot.full_clean()
                slot.save()
                messages.success(request, "Availability slot added.")
                return redirect("doctors:dashboard")
            except Exception as exc:  # noqa: BLE001 - surfaced to user as form error
                messages.error(request, str(exc))
    else:
        form = AvailabilitySlotForm()
    return render(request, "doctors/create_slot.html", {"form": form})


@doctor_required
def delete_slot(request, slot_id):
    profile = request.user.doctor_profile
    # get_object_or_404 scoped to this doctor's own slots only -- a doctor
    # cannot delete another doctor's slot even by guessing the id.
    slot = get_object_or_404(AvailabilitySlot, id=slot_id, doctor=profile)
    if slot.is_booked:
        messages.error(request, "Cannot delete a slot that is already booked.")
    else:
        slot.delete()
        messages.success(request, "Slot removed.")
    return redirect("doctors:dashboard")
