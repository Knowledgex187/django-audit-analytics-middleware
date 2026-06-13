"""Pytest configuration for Django tests"""

import os
import sys
import django
from django.conf import settings


def pytest_configure():
    """Configure Django settings for testing"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY="test-secret-key",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django_analytics_middleware",
            ],
            MIDDLEWARE=[
                "django_analytics_middleware.middleware.AnalyticsMiddleware",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            ANALYTICS_LOG_PATH="/tmp/test_analytics.log",
        )

    django.setup()
