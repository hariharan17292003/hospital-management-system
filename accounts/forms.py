from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class DoctorSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)
    specialization = forms.CharField(max_length=120, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DOCTOR
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            from doctors.models import DoctorProfile

            DoctorProfile.objects.create(
                user=user, specialization=self.cleaned_data["specialization"]
            )
        return user


class PatientSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            from patients.models import PatientProfile

            PatientProfile.objects.create(user=user)
        return user


class EmailOrUsernameAuthForm(forms.Form):
    """Login form accepting either username or email, per the spec."""

    identifier = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)
