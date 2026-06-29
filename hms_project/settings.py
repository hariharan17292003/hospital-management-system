"""
Django settings for hms_project.

Design note: configuration is pulled from environment variables via
python-decouple so the same codebase runs locally, in CI, or anywhere else
without code changes. A `.env.example` is provided in the repo root of the
`hms/` app — copy it to `.env` and fill in real values.
"""

from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-only-secret-key-change-me")

DEBUG = config("DEBUG", default=True, cast=bool)

# ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
# ALLOWED_HOSTS = [*]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # local apps
    "accounts",
    "doctors",
    "patients",
    "bookings",
    "calendar_integration",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "hms_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hms_project.wsgi.application"

# --- Database -----------------------------------------------------------
# Local PostgreSQL by default. Override via env vars for other setups.
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": config("DB_NAME", default="hms_db"),
#         "USER": config("DB_USER", default="hms_user"),
#         "PASSWORD": config("DB_PASSWORD", default="hms_password"),
#         "HOST": config("DB_HOST", default="localhost"),
#         "PORT": config("DB_PORT", default="5432"),
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hms_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}



# --- Custom user model ---------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:redirect_after_login"
LOGOUT_REDIRECT_URL = "accounts:login"

LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="Asia/Kolkata")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Serverless email service ------------------------------------------
# Base URL of the serverless-offline endpoint. Default matches
# `serverless-offline`'s default local port (3000) for this project.
EMAIL_SERVICE_BASE_URL = config(
    "EMAIL_SERVICE_BASE_URL", default="http://localhost:3000/dev"
)
# Internal shared secret so the email service can confirm requests are
# coming from this backend and not a random caller hitting the local port.
EMAIL_SERVICE_SHARED_SECRET = config(
    "EMAIL_SERVICE_SHARED_SECRET", default="dev-shared-secret-change-me"
)
# If True, failures calling the email service are logged but never raised —
# a booking should not fail just because a notification email failed.
EMAIL_SERVICE_FAIL_SILENTLY = config(
    "EMAIL_SERVICE_FAIL_SILENTLY", default=True, cast=bool
)

# --- Google Calendar OAuth2 ----------------------------------------------
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_REDIRECT_URI = config(
    "GOOGLE_REDIRECT_URI", default="http://localhost:8000/calendar/oauth2/callback/"
)
GOOGLE_OAUTH_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# Allows OAuth2 library to work over http on localhost during local dev only.
import os  # noqa: E402

if DEBUG:
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
