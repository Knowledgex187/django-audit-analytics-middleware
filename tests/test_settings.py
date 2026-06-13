"""Django settings for running tests"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "test-secret-key-for-analytics-middleware"

DEBUG = True

ALLOWED_HOSTS = ["testserver"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django_analytics_middleware",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_analytics_middleware.middleware.AnalyticsMiddleware",
]

ROOT_URLCONF = "test_urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True
TIME_ZONE = "UTC"

# Analytics middleware settings
ANALYTICS_LOG_PATH = "/tmp/test_analytics.log"
ANALYTICS_NOISE_PATHS = ["/health", "/admin", "/favicon.ico"]
ANALYTICS_LOG_LEVEL = "INFO"
