from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/doctor/", views.signup_doctor, name="signup_doctor"),
    path("signup/patient/", views.signup_patient, name="signup_patient"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.redirect_after_login, name="redirect_after_login"),
]
