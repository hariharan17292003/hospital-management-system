from django.urls import path

from . import views

app_name = "doctors"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("slots/create/", views.create_slot, name="create_slot"),
    path("slots/<int:slot_id>/delete/", views.delete_slot, name="delete_slot"),
]
