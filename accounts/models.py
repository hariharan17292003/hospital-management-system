from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Single user model for both doctors and patients, distinguished by `role`.

    Design note: we use one table with a role flag rather than two separate
    user models (DoctorUser / PatientUser). This keeps Django's built-in
    auth (login, password hashing, sessions) working unmodified for both
    roles, and role-based access is enforced via decorators/mixins that
    check `request.user.role` rather than via separate auth backends.
    See README -> System Architecture for how this is enforced at the view
    layer.
    """

    class Role(models.TextChoices):
        DOCTOR = "DOCTOR", "Doctor"
        PATIENT = "PATIENT", "Patient"

    role = models.CharField(max_length=10, choices=Role.choices)

    # Each user can independently connect their own Google account for
    # calendar sync. Tokens are stored per-user (see calendar_integration app).

    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    def is_patient(self):
        return self.role == self.Role.PATIENT

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
