from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from .email_client import send_signup_welcome
from .forms import DoctorSignUpForm, PatientSignUpForm, EmailOrUsernameAuthForm
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:redirect_after_login")
    return render(request, "accounts/home.html")


def signup_doctor(request):
    if request.method == "POST":
        form = DoctorSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_signup_welcome(
                to_email=user.email,
                full_name=user.get_full_name() or user.username,
                role="DOCTOR",
            )
            login(request, user)
            messages.success(request, "Welcome! Your doctor account is ready.")
            return redirect("doctors:dashboard")
    else:
        form = DoctorSignUpForm()
    return render(request, "accounts/signup.html", {"form": form, "role": "Doctor"})


def signup_patient(request):
    if request.method == "POST":
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_signup_welcome(
                to_email=user.email,
                full_name=user.get_full_name() or user.username,
                role="PATIENT",
            )
            login(request, user)
            messages.success(request, "Welcome! Your patient account is ready.")
            return redirect("patients:dashboard")
    else:
        form = PatientSignUpForm()
    return render(request, "accounts/signup.html", {"form": form, "role": "Patient"})


def login_view(request):
    if request.method == "POST":
        form = EmailOrUsernameAuthForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"]
            password = form.cleaned_data["password"]

            # Accept either username or email at the login form, per spec
            # ("Username/email + password"). We resolve email -> username
            # first since Django's auth backend authenticates by username.
            username = identifier
            if "@" in identifier:
                try:
                    matched = User.objects.get(email__iexact=identifier)
                    username = matched.username
                except User.DoesNotExist:
                    username = identifier  # will simply fail auth below

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("accounts:redirect_after_login")
            messages.error(request, "Invalid credentials.")
    else:
        form = EmailOrUsernameAuthForm()
    return render(request, "accounts/login.html", {"form": form})


@login_required
def redirect_after_login(request):
    if request.user.is_doctor():
        return redirect("doctors:dashboard")
    return redirect("patients:dashboard")


@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:home")
