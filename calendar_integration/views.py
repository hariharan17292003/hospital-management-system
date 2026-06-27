"""
Google OAuth2 connect flow.
Each user connects their Google account and stores tokens securely.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from google_auth_oauthlib.flow import Flow

from .models import GoogleCalendarCredential


def _build_flow(state=None):
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        state=state,
    )

    # IMPORTANT: must match Google Console EXACTLY
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    return flow


@login_required
def connect(request):
    flow = _build_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    # Store state in session for CSRF protection
    request.session["google_oauth_state"] = state

    # Debug (you can remove later)
    print("\nGOOGLE AUTH URL:\n", authorization_url)

    return redirect(authorization_url)


@login_required
def oauth2_callback(request):
    state = request.session.get("google_oauth_state")

    # If session lost or expired
    if not state:
        messages.error(request, "OAuth session expired. Please try again.")
        return redirect("accounts:login")

    flow = _build_flow(state=state)

    try:
        # Exchange authorization code for tokens
        flow.fetch_token(
            authorization_response=request.build_absolute_uri()
        )
    except Exception as e:
        print("OAuth Error:", e)
        messages.error(request, "Google authentication failed. Try again.")
        return redirect("accounts:login")

    credentials = flow.credentials

    # Save tokens per user
    GoogleCalendarCredential.objects.update_or_create(
        user=request.user,
        defaults={
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token or "",
            "token_expiry": credentials.expiry,
            "scope": " ".join(credentials.scopes or []),
        },
    )

    # Clear session state after success
    request.session.pop("google_oauth_state", None)

    messages.success(request, "Google Calendar connected successfully!")

    # Redirect based on role
    if hasattr(request.user, "is_doctor") and request.user.is_doctor():
        return redirect("doctors:dashboard")

    return redirect("patients:dashboard")