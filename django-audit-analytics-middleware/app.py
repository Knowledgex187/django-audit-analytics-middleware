import os
import sys
import logging
import django.conf import settings
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class AnalyticsMiddlewareConfig(AppConfig):
    """Django app configuration for the analytics middleware"""

    name = "django_analytics_middleware"
    verbose_name = "Django Analytics Middleware"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        pass

    """Check if Django is running a command"""

    def _is_running_management_command(self):
        return len(sys.argv) > 1 and sys.argv[1] in [
            "migrate",
            "makemigrations",
            "collectstatic",
            "flush",
            "loaddata",
            "dumpdata",
        ]

    """Validate user settings at startup"""
    def _validate_configuration(self):
        log_path = getattr(settings, "ANALYTICS_LOG_PATH", None)
        
        if not log_path:
            print("Analytics middleware: You must set ANALYTICS_LOG_PATH in your settings.py")
            print("Example: ANALYTICS_LOG_PATH = os.path.join(BASEDIR, 'logs', 'analytics.log')")
            print("Or in .env ANALYTICS_LOG_PATH=<LOG PATH>")
            raise ImproperlyConfigured(
                "Analytics middleware: You must set ANALYTICS_LOG_PATH in your settings.py\n"
                "Example: ANALYTICS_LOG_PATH = os.path.join(BASEDIR, 'logs', 'analytics.log')\n"
                "Or in .env ANALYTICS_LOG_PATH=<LOG PATH>"
                )
        
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                print(f"Created log directory: {log_dir}")
            
            except PermissionError:
                raise RuntimeError(
                    f"Analytics middleware: Cannot create directory '{log_dir}'."
                    f"Either fix permissions or change ANALYTICS_LOG_PATH within settings.py."
                )
