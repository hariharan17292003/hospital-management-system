from django.conf import settings
from django.db import models


class GoogleCalendarCredential(models.Model):
    """
    Stores one Google OAuth2 token set per user, so each doctor/patient can
    independently connect their own Google account (per spec: "assume one
    Google account per user").

    Design note: refresh_token is stored so we can mint new access tokens
    without asking the user to re-authenticate every time the short-lived
    access token expires. See README -> Design Decision for the discussion
    of storing this in plaintext in the local Postgres DB (acceptable for
    this local/demo scope) vs. encrypting it at rest (the production
    answer, called out in Limitations).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="google_credential"
    )
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, default="")
    token_expiry = models.DateTimeField(null=True, blank=True)
    scope = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Google credential for {self.user}"
