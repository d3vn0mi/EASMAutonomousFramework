"""
Base Django settings for RAVEN EASM Platform.
"""
import os
from pathlib import Path

from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ── Applications ──────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third-party
    "channels",
    "rest_framework",
    "django_filters",
    # RAVEN apps
    "apps.accounts",
    "apps.dashboard",
    "apps.clients",
    "apps.engagements",
    "apps.scanning",
    "apps.findings",
    "apps.correlation",
    "apps.reports",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.AuditTrailMiddleware",
]

ROOT_URLCONF = "raven.urls"

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
                "django.template.context_processors.i18n",
            ],
        },
    },
]

ASGI_APPLICATION = "raven.asgi.application"
WSGI_APPLICATION = "raven.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="raven_easm"),
        "USER": config("POSTGRES_USER", default="raven"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="raven"),
        "HOST": config("POSTGRES_HOST", default="localhost"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

# ── Cache & Channels ─────────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# ── Celery ────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE = {}

# ── Auth ──────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalization ──────────────────────────────────────────────────
LANGUAGE_CODE = config("DEFAULT_LANGUAGE", default="en")
LANGUAGES = [
    ("en", "English"),
    ("el", "Ελληνικά"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_L10N = True
TIME_ZONE = "UTC"
USE_TZ = True

# ── Static & Media ────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── REST Framework ────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

# ── RAVEN-specific settings ──────────────────────────────────────────────
CORRELATION_ENGINE = config("CORRELATION_ENGINE", default="claude")
ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434")

SHODAN_API_KEY = config("SHODAN_API_KEY", default="")
CENSYS_API_ID = config("CENSYS_API_ID", default="")
CENSYS_API_SECRET = config("CENSYS_API_SECRET", default="")

# Path to the documentation templates (mounted read-only in Docker)
RAVEN_TEMPLATES_DIR = config(
    "RAVEN_TEMPLATES_DIR",
    default=str(BASE_DIR.parent / "documentation"),
)

# Scanner output storage
SCANNER_OUTPUT_DIR = str(MEDIA_ROOT / "scan_output")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
