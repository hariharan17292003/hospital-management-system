from django.urls import path

from . import views

app_name = "calendar_integration"

urlpatterns = [
    path("connect/", views.connect, name="connect"),
    path("oauth2/callback/", views.oauth2_callback, name="oauth2_callback"),
]
