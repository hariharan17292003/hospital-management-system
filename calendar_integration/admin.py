from django.contrib import admin

from .models import GoogleCalendarCredential


@admin.register(GoogleCalendarCredential)
class GoogleCalendarCredentialAdmin(admin.ModelAdmin):
    list_display = ["user", "updated_at"]
