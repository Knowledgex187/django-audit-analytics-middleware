"""Pytest configuration for Django tests - MUST BE FIRST"""

import os
import sys
import django
from django.conf import settings


# Configure Django settings BEFORE any Django imports
def pytest_configure():
    """Configure Django settings for testing - runs before any tests"""

    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY="test-secret-key-for-analytics-middleware",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django_analytics_middleware",
            ],
            MIDDLEWARE=[
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django_analytics_middleware.middleware.AnalyticsMiddleware",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_TZ=True,
            TIME_ZONE="UTC",
            ANALYTICS_LOG_PATH="/tmp/test_analytics.log",
            ANALYTICS_NOISE_PATHS=["/health", "/admin", "/favicon.ico"],
            ANALYTICS_LOG_LEVEL="INFO",
            ROOT_URLCONF="tests.test_urls",
        )

    django.setup()


# This ensures settings are configured before any test imports
pytest_configure()
