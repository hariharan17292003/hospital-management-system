from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("create/<int:slot_id>/", views.create_booking, name="create_booking"),
    path("mine/", views.my_bookings_patient, name="my_bookings"),
    path("doctor/mine/", views.my_bookings_doctor, name="doctor_bookings"),
    
    path(
    "cancel/<int:booking_id>/",
    views.cancel_booking,
    name="cancel_booking",
),
    

]
