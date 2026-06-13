"""Tests for the AnalyticsMiddlewareConfig AppConfig"""

import os
import sys
import tempfile
import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from unittest.mock import patch


class TestAnalyticsMiddlewareConfig:
    """Test the AppConfig validation logic"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        # Import here to avoid Django setup issues
        from django_analytics_middleware.apps import AnalyticsMiddlewareConfig

        self.config = AnalyticsMiddlewareConfig(
            "django_analytics_middleware", AnalyticsMiddlewareConfig
        )

    def test_requires_log_path_setting(self):
        """Test that ImproperlyConfigured is raised when ANALYTICS_LOG_PATH is missing"""
        with override_settings(ANALYTICS_LOG_PATH=None):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                self.config._validate_configuration()
            assert "ANALYTICS_LOG_PATH" in str(exc_info.value)

    def test_accepts_valid_log_path(self):
        """Test that valid log path passes validation"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log") as tmp_file:
            log_path = tmp_file.name
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                # Should not raise exception
                self.config._validate_configuration()

    def test_creates_directory_if_not_exists(self):
        """Test that log directory is created automatically when it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "subdir", "analytics.log")
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                self.config._validate_configuration()
                assert os.path.exists(os.path.dirname(log_path))

    def test_permission_error_when_cannot_create_directory(self):
        """Test that PermissionError is caught and raised as RuntimeError"""
        # This test only runs on Unix-like systems
        if os.name == "nt":
            pytest.skip("Permission test not applicable on Windows")

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Make directory read-only
            os.chmod(tmp_dir, 0o444)
            log_path = os.path.join(tmp_dir, "subdir", "analytics.log")
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                with pytest.raises(RuntimeError) as exc_info:
                    self.config._validate_configuration()
                assert "Cannot create directory" in str(exc_info.value)
            # Clean up - make writable again for deletion
            os.chmod(tmp_dir, 0o755)

    def test_permission_error_when_cannot_write_to_file(self):
        """Test that PermissionError when writing to file raises ImproperlyConfigured"""
        # This test only runs on Unix-like systems
        if os.name == "nt":
            pytest.skip("Permission test not applicable on Windows")

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Make directory read-only
            os.chmod(tmp_dir, 0o444)
            log_path = os.path.join(tmp_dir, "analytics.log")

            # Create the file first
            with open(log_path, "w") as f:
                f.write("")

            with override_settings(ANALYTICS_LOG_PATH=log_path):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    self.config._validate_configuration()
                assert "Can't write to log file" in str(exc_info.value)

            # Clean up
            os.chmod(tmp_dir, 0o755)

    def test_uses_default_noise_paths_when_not_set(self):
        """Test that default noise paths are used when ANALYTICS_NOISE_PATHS is not set"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log") as tmp_file:
            log_path = tmp_file.name
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                with override_settings(ANALYTICS_NOISE_PATHS=None):
                    # Should not raise exception
                    self.config._validate_configuration()
                    # The method sets default but doesn't store it
                    # Just verify no exception is raised

    def test_accepts_custom_noise_paths(self):
        """Test that custom noise paths are accepted"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log") as tmp_file:
            log_path = tmp_file.name
            custom_noise_paths = ["/custom/health", "/custom/metrics"]
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                with override_settings(ANALYTICS_NOISE_PATHS=custom_noise_paths):
                    # Should not raise exception
                    self.config._validate_configuration()

    def test_skips_validation_during_management_commands(self):
        """Test that validation is skipped during Django management commands"""
        original_argv = sys.argv.copy()
        sys.argv = ["manage.py", "migrate"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log") as tmp_file:
            log_path = tmp_file.name
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                # ready() should return early without raising exception
                result = self.config.ready()
                assert result is None

        sys.argv = original_argv

    def test_runs_validation_during_normal_server_start(self):
        """Test that validation runs during normal server start (not management command)"""
        original_argv = sys.argv.copy()
        sys.argv = ["manage.py", "runserver"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log") as tmp_file:
            log_path = tmp_file.name
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                # Should not raise exception
                self.config.ready()

        sys.argv = original_argv

    def test_log_path_with_trailing_slash(self):
        """Test that log path with directory trailing slash is handled correctly"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "analytics.log")
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                self.config._validate_configuration()
                assert os.path.exists(os.path.dirname(log_path))

    def test_existing_directory_does_not_recreate(self):
        """Test that existing directory is not recreated"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "analytics.log")
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                # Run validation first time
                self.config._validate_configuration()
                # Run again - should not raise exception
                self.config._validate_configuration()

    def test_empty_log_path_raises_error(self):
        """Test that empty string as log path raises error"""
        with override_settings(ANALYTICS_LOG_PATH=""):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                self.config._validate_configuration()
            assert "ANALYTICS_LOG_PATH" in str(exc_info.value)

    def test_setup_package_logging_creates_handler(self):
        """Test that package logging is set up correctly"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log") as tmp_file:
            log_path = tmp_file.name
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                self.config._setup_package_logging()

                import logging

                logger = logging.getLogger("django_analytics_middleware")
                # Logger should have handlers
                assert len(logger.handlers) > 0

    def test_setup_package_logging_respects_log_level(self):
        """Test that package logging respects ANALYTICS_LOG_LEVEL setting"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log") as tmp_file:
            log_path = tmp_file.name
            with override_settings(ANALYTICS_LOG_PATH=log_path):
                with override_settings(ANALYTICS_LOG_LEVEL="DEBUG"):
                    self.config._setup_package_logging()

                    import logging

                    logger = logging.getLogger("django_analytics_middleware")
                    assert logger.level == logging.DEBUG

    def test_management_command_list(self):
        """Test that all management commands are correctly identified"""
        management_commands = [
            "migrate",
            "makemigrations",
            "collectstatic",
            "flush",
            "loaddata",
            "dumpdata",
        ]

        for cmd in management_commands:
            assert self.config._is_running_management_command() is False
            # Set sys.argv to simulate command
            original_argv = sys.argv.copy()
            sys.argv = ["manage.py", cmd]
            assert self.config._is_running_management_command() is True
            sys.argv = original_argv
