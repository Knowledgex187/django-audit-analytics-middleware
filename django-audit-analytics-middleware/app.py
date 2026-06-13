import os
import sys
import logging
from django.conf import settings
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class AnalyticsMiddlewareConfig(AppConfig):
    """Django app configuration for the analytics middleware"""

    name = "django_analytics_middleware"
    verbose_name = "Django Analytics Middleware"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        Called once when Django starts
        """
        if self._is_running_management_command():
            return

        # Validation Configuration
        self._validate_configuration()
        self._setup_package_logging()

        logger = logging.getLogger(__name__)
        logger.info("Analytics middleware initiated successfully")

    def _is_running_management_command(self):
        """Check if Django is running a command"""
        return len(sys.argv) > 1 and sys.argv[1] in [
            "migrate",
            "makemigrations",
            "collectstatic",
            "flush",
            "loaddata",
            "dumpdata",
        ]

    def _validate_configuration(self):
        """Validate user settings at startup"""
        log_path = getattr(settings, "ANALYTICS_LOG_PATH", None)

        if not log_path:
            print(
                "Analytics middleware: You must set ANALYTICS_LOG_PATH in your settings.py"
            )
            print(
                "Example: ANALYTICS_LOG_PATH = os.path.join(BASEDIR, 'logs', 'analytics.log')"
            )
            print("Or in .env ANALYTICS_LOG_PATH=<LOG PATH>")
            raise ImproperlyConfigured(
                "Analytics middleware: You must set ANALYTICS_LOG_PATH in your settings.py\n"
                "Example: ANALYTICS_LOG_PATH = os.path.join(BASEDIR, 'logs', 'analytics.log')\n"
                "Or in .env ANALYTICS_LOG_PATH=<LOG PATH>"
            )

        # Test directory actually exists and create
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

        # Tries to write to log to test permissions
        try:
            with open(log_path, "a") as test_file:
                test_file.write("")
        except PermissionError:
            raise ImproperlyConfigured("Can't write to log file")

        # Retrieves noise paths list from settings.py
        noise_paths = getattr(settings, "ANALYTICS_NOISE_PATHS", None)
        if noise_paths is None:
            print("No noise path field discovered within settings.py.")
            print("Using default noise paths: /health, /admin, /favicon.ico")
            noise_paths = ["/health", "/admin", "/favicon.ico"]  # Set default

    def _setup_package_logging(self):
        """Configure logging"""

        log_level_name = getattr(settings, "ANALYTICS_LOG_LEVEL", "WARNING")
        log_level = getattr(logging, log_level_name.upper(), logging.WARNING)

        # Configure package logger
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)

        # Dont add handlers if already configured
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
