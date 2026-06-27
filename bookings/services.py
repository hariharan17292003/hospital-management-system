"""
Booking creation logic.

This is the function the design decision in the README is about: how to
stop two patients from booking the same slot when they hit "book" at
almost the same instant.

Approach used: a single atomic transaction that takes a row-level lock on
the target slot with SELECT ... FOR UPDATE (via select_for_update()),
re-checks is_booked under that lock, and only then creates the Booking and
flips is_booked. The second request to reach the lock blocks until the
first transaction commits, then re-reads is_booked=True and is rejected
with SlotAlreadyBookedError. No double booking is possible regardless of
how close together the two requests arrive, because the database -- not
application code -- is what's serializing access to that row.

The alternative considered (optimistic locking with a version column, or
just a plain `if not slot.is_booked` check before saving) is discussed
and explicitly rejected in the README's Design Decision section.
"""

from django.db import transaction

from doctors.models import AvailabilitySlot
from .models import Booking


class SlotAlreadyBookedError(Exception):
    """Raised when the requested slot was booked by someone else first."""


def book_slot(*, patient_profile, slot_id: int) -> Booking:
    with transaction.atomic():
        try:
            # select_for_update() issues SELECT ... FOR UPDATE, taking a
            # row lock that forces any concurrent request for the same
            # slot to wait until this transaction commits or rolls back.
            slot = AvailabilitySlot.objects.select_for_update().get(id=slot_id)
        except AvailabilitySlot.DoesNotExist:
            raise SlotAlreadyBookedError("This slot no longer exists.")

        if slot.is_booked:
            # Either booked previously, or by a request that won the race
            # to acquire the lock first. Either way, reject cleanly.
            raise SlotAlreadyBookedError("This slot has just been booked by another patient.")

        slot.is_booked = True
        slot.save(update_fields=["is_booked"])

        booking = Booking.objects.create(slot=slot, patient=patient_profile)
        return booking
