import datetime as dt
import threading

from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model

from doctors.models import DoctorProfile, AvailabilitySlot
from patients.models import PatientProfile
from bookings.models import Booking
from bookings.services import book_slot, SlotAlreadyBookedError

User = get_user_model()


def _make_doctor():
    user = User.objects.create_user(
        username="dr_test", email="dr@test.com", password="pass12345",
        role=User.Role.DOCTOR, first_name="Asha",
    )
    return DoctorProfile.objects.create(user=user, specialization="Cardiology")


def _make_patient(username):
    user = User.objects.create_user(
        username=username, email=f"{username}@test.com", password="pass12345",
        role=User.Role.PATIENT, first_name=username,
    )
    return PatientProfile.objects.create(user=user)


class BookingRaceConditionTests(TransactionTestCase):
    """
    Uses TransactionTestCase (not TestCase) because the race condition test
    spins up real concurrent transactions in separate threads, which
    requires each thread to see committed data the way it would against a
    real Postgres server -- the default TestCase wraps everything in a
    single rolled-back transaction and won't exercise real locking.
    """

    def setUp(self):
        self.doctor = _make_doctor()
        self.patient1 = _make_patient("pat1")
        self.patient2 = _make_patient("pat2")
        self.slot = AvailabilitySlot.objects.create(
            doctor=self.doctor,
            date=dt.date.today() + dt.timedelta(days=1),
            start_time=dt.time(10, 0),
            end_time=dt.time(10, 30),
        )

    def test_only_one_booking_wins_under_concurrency(self):
        results = {}

        def attempt(patient, label):
            try:
                booking = book_slot(patient_profile=patient, slot_id=self.slot.id)
                results[label] = ("ok", booking.id)
            except SlotAlreadyBookedError as exc:
                results[label] = ("rejected", str(exc))

        t1 = threading.Thread(target=attempt, args=(self.patient1, "p1"))
        t2 = threading.Thread(target=attempt, args=(self.patient2, "p2"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        outcomes = [results["p1"][0], results["p2"][0]]
        self.assertEqual(outcomes.count("ok"), 1, f"Expected exactly one success, got {results}")
        self.assertEqual(outcomes.count("rejected"), 1, f"Expected exactly one rejection, got {results}")
        self.assertEqual(Booking.objects.filter(slot=self.slot).count(), 1)

        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)

    def test_second_sequential_booking_is_rejected(self):
        book_slot(patient_profile=self.patient1, slot_id=self.slot.id)
        with self.assertRaises(SlotAlreadyBookedError):
            book_slot(patient_profile=self.patient2, slot_id=self.slot.id)


class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.doctor = _make_doctor()
        self.patient = _make_patient("pat1")

    def test_patient_cannot_access_doctor_dashboard(self):
        client = Client()
        client.login(username="pat1", password="pass12345")
        response = client.get("/doctor/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_doctor_cannot_access_patient_dashboard(self):
        client = Client()
        client.login(username="dr_test", password="pass12345")
        response = client.get("/patient/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_doctor_can_access_own_dashboard(self):
        client = Client()
        client.login(username="dr_test", password="pass12345")
        response = client.get("/doctor/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_patient_can_access_own_dashboard(self):
        client = Client()
        client.login(username="pat1", password="pass12345")
        response = client.get("/patient/dashboard/")
        self.assertEqual(response.status_code, 200)


class SlotVisibilityTests(TestCase):
    def setUp(self):
        self.doctor = _make_doctor()
        self.patient = _make_patient("pat1")

    def test_booked_slot_not_shown_to_patients(self):
        slot = AvailabilitySlot.objects.create(
            doctor=self.doctor,
            date=dt.date.today() + dt.timedelta(days=1),
            start_time=dt.time(9, 0),
            end_time=dt.time(9, 30),
        )
        book_slot(patient_profile=self.patient, slot_id=slot.id)

        client = Client()
        client.login(username="pat1", password="pass12345")
        response = client.get("/patient/dashboard/")
        self.assertNotContains(response, "09:00")

    def test_past_slot_not_shown_to_patients(self):
        AvailabilitySlot.objects.create(
            doctor=self.doctor,
            date=dt.date.today() - dt.timedelta(days=1),
            start_time=dt.time(9, 0),
            end_time=dt.time(9, 30),
        )
        client = Client()
        client.login(username="pat1", password="pass12345")
        response = client.get("/patient/dashboard/")
        self.assertContains(response, "No open slots")
