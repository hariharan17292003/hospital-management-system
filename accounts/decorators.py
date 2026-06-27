"""
Role-based access control helpers.

Design note: role checks live here as small composable decorators rather
than as separate Django auth backends or permission classes. Every
doctor-only or patient-only view is wrapped explicitly, so reading a
view's decorators tells you its access rule with no indirection. See
README -> System Architecture for the broader discussion of this choice.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def doctor_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_doctor():
            raise PermissionDenied("This action is restricted to doctor accounts.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def patient_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_patient():
            raise PermissionDenied("This action is restricted to patient accounts.")
        return view_func(request, *args, **kwargs)

    return _wrapped
