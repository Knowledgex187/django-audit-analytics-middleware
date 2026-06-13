"""Tests for the AnalyticsMiddleware"""

import json
import os
import tempfile
import pytest
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from django.http import HttpResponse
from unittest.mock import patch, MagicMock


class TestAnalyticsMiddleware:
    """Test the AnalyticsMiddleware functionality"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        self.factory = RequestFactory()
        # Create a temporary log file for testing
        self.temp_log = tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        )
        self.log_path = self.temp_log.name
        self.temp_log.close()

    def teardown_method(self):
        """Clean up test fixtures after each test"""
        if os.path.exists(self.log_path):
            os.unlink(self.log_path)

    def create_middleware(self, log_path=None, noise_paths=None):
        """Helper to create middleware instance with test config"""
        from django_analytics_middleware.middleware import AnalyticsMiddleware

        def get_response(request):
            return HttpResponse("OK", status=200)

        # Patch settings for this test
        with patch(
            "django.conf.settings.ANALYTICS_LOG_PATH", log_path or self.log_path
        ):
            with patch(
                "django.conf.settings.ANALYTICS_NOISE_PATHS",
                noise_paths or ["/health", "/admin", "/favicon.ico"],
            ):
                middleware = AnalyticsMiddleware(get_response)
                return middleware

    def create_middleware_with_custom_response(
        self, response_status=200, response_data="OK"
    ):
        """Helper to create middleware with custom response"""
        from django_analytics_middleware.middleware import AnalyticsMiddleware

        def get_response(request):
            return HttpResponse(response_data, status=response_status)

        with patch("django.conf.settings.ANALYTICS_LOG_PATH", self.log_path):
            middleware = AnalyticsMiddleware(get_response)
            return middleware

    def test_middleware_logs_request(self):
        """Test that middleware creates log entry for request"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")

        response = middleware(request)

        assert response.status_code == 200

        # Check log file was written
        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            assert log_entry["path"] == "/api/test"
            assert log_entry["method"] == "GET"
            assert log_entry["status"] == 200

    def test_middleware_logs_post_request(self):
        """Test that POST requests are logged correctly"""
        middleware = self.create_middleware()
        request = self.factory.post("/api/users", data={"name": "test"})

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            assert log_entry["path"] == "/api/users"
            assert log_entry["method"] == "POST"

    def test_middleware_tracks_duration(self):
        """Test that middleware records request duration in milliseconds"""
        import time

        def slow_response(request):
            time.sleep(0.1)  # 100ms delay
            return HttpResponse("OK", status=200)

        from django_analytics_middleware.middleware import AnalyticsMiddleware

        with patch("django.conf.settings.ANALYTICS_LOG_PATH", self.log_path):
            middleware = AnalyticsMiddleware(slow_response)
            request = self.factory.get("/api/slow")

            response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            # Duration should be at least 100ms
            assert log_entry["duration_ms"] >= 100
            assert log_entry["duration_ms"] < 200

    def test_middleware_skips_noise_paths(self):
        """Test that noise paths are not logged"""
        middleware = self.create_middleware(noise_paths=["/health", "/metrics"])
        request = self.factory.get("/health")

        response = middleware(request)

        # Check that no log file was created or it's empty
        if os.path.exists(self.log_path):
            with open(self.log_path, "r") as f:
                content = f.read()
                assert content == ""

    def test_middleware_logs_non_noise_paths(self):
        """Test that non-noise paths are logged"""
        middleware = self.create_middleware(noise_paths=["/health"])
        request = self.factory.get("/api/users")

        response = middleware(request)

        with open(self.log_path, "r") as f:
            content = f.read()
            assert content != ""

    def test_middleware_logs_authenticated_user(self):
        """Test that authenticated user UUID is captured"""
        # Create a mock user with uuid attribute
        user = MagicMock()
        user.is_authenticated = True
        user.uuid = "test-uuid-123-456"

        middleware = self.create_middleware()
        request = self.factory.get("/api/profile")
        request.user = user

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["user_uuid"] == "test-uuid-123-456"

    def test_middleware_logs_anonymous_user(self):
        """Test that anonymous users are marked as unauthorized"""
        # Create anonymous user
        user = MagicMock()
        user.is_authenticated = False

        middleware = self.create_middleware()
        request = self.factory.get("/api/public")
        request.user = user

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["user_uuid"] == "unauthorized user"

    def test_middleware_extracts_ip_from_forwarded_header(self):
        """Test that X-Forwarded-For header is used for IP"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        request.META["HTTP_X_FORWARDED_FOR"] = (
            "203.0.113.195, 198.51.100.17, 192.168.1.1"
        )

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["ip"] == "203.0.113.195"

    def test_middleware_extracts_direct_ip(self):
        """Test that REMOTE_ADDR is used when no X-Forwarded-For"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["ip"] == "192.168.1.100"

    def test_middleware_handles_empty_x_forwarded_for(self):
        """Test that empty X-Forwarded-For falls back to REMOTE_ADDR"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        request.META["HTTP_X_FORWARDED_FOR"] = ""
        request.META["REMOTE_ADDR"] = "10.0.0.1"

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["ip"] == "10.0.0.1"

    def test_middleware_logs_user_agent(self):
        """Test that User-Agent header is captured"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 (Test Browser)"

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["user_agent"] == "Mozilla/5.0 (Test Browser)"

    def test_middleware_logs_referrer(self):
        """Test that Referer header is captured"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        request.META["HTTP_REFERER"] = "https://google.com/search?q=django"

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["referrer"] == "https://google.com/search?q=django"

    def test_middleware_handles_missing_referrer(self):
        """Test that missing referrer becomes empty string"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        # No HTTP_REFERER set

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["referrer"] == ""

    def test_middleware_handles_write_error_gracefully(self):
        """Test that middleware doesn't crash if log write fails"""
        # Use an invalid path that can't be written to
        middleware = self.create_middleware(
            log_path="/invalid/path/that/doesnt/exist.log"
        )
        request = self.factory.get("/api/test")

        # Should not raise exception
        response = middleware(request)
        assert response.status_code == 200

    def test_middleware_disabled_when_no_log_path(self):
        """Test that middleware is disabled when no log path configured"""
        middleware = self.create_middleware(log_path=None)
        request = self.factory.get("/api/test")

        response = middleware(request)

        # No log file should be created
        assert not os.path.exists(self.log_path)

    def test_middleware_logs_status_codes(self):
        """Test that different HTTP status codes are logged"""
        status_codes = [200, 201, 400, 401, 403, 404, 500]

        for status_code in status_codes:
            # Reset for each test
            if os.path.exists(self.log_path):
                os.unlink(self.log_path)

            middleware = self.create_middleware_with_custom_response(
                response_status=status_code
            )
            request = self.factory.get("/api/test")

            response = middleware(request)

            with open(self.log_path, "r") as f:
                log_line = f.readline()
                log_entry = json.loads(log_line)
                assert log_entry["status"] == status_code

    def test_middleware_logs_time_dimensions(self):
        """Test that time dimensions (month, week, day, hour) are included"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            assert "month" in log_entry
            assert "week" in log_entry
            assert "day" in log_entry
            assert "hour" in log_entry
            assert isinstance(log_entry["month"], str)
            assert isinstance(log_entry["week"], str)
            assert isinstance(log_entry["day"], str)
            assert isinstance(log_entry["hour"], str)

    def test_middleware_logs_timestamp(self):
        """Test that ISO timestamp is included"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            assert "timestamp" in log_entry
            assert "T" in log_entry["timestamp"]  # ISO format has T separator
            assert (
                "+" in log_entry["timestamp"] or "Z" in log_entry["timestamp"]
            )  # Has timezone

    def test_multiple_requests_log_separately(self):
        """Test that multiple requests create multiple log lines"""
        middleware = self.create_middleware()

        for i in range(3):
            request = self.factory.get(f"/api/test/{i}")
            response = middleware(request)

        with open(self.log_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 3

    def test_json_format_is_valid(self):
        """Test that each log line is valid JSON"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")

        response = middleware(request)

        with open(self.log_path, "r") as f:
            for line in f:
                # Should not raise JSON decode error
                json.loads(line)

    def test_middleware_returns_response_correctly(self):
        """Test that middleware returns the response unmodified"""
        middleware = self.create_middleware_with_custom_response(
            response_data="Custom Body"
        )
        request = self.factory.get("/api/test")

        response = middleware(request)

        assert response.content == b"Custom Body"
        assert response.status_code == 200

    def test_log_entry_contains_all_fields(self):
        """Test that log entry contains all expected fields"""
        expected_fields = [
            "path",
            "method",
            "status",
            "user_uuid",
            "duration_ms",
            "ip",
            "user_agent",
            "referrer",
            "timestamp",
            "month",
            "week",
            "day",
            "hour",
        ]

        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        request.META["HTTP_USER_AGENT"] = "Test Browser"

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            for field in expected_fields:
                assert field in log_entry, f"Missing field: {field}"

    def test_middleware_handles_null_user_agent(self):
        """Test that missing user agent becomes empty string"""
        middleware = self.create_middleware()
        request = self.factory.get("/api/test")
        # No HTTP_USER_AGENT set

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["user_agent"] == ""

    def test_middleware_handles_multiple_slashes_in_path(self):
        """Test that paths with multiple slashes are logged correctly"""
        middleware = self.create_middleware()
        request = self.factory.get("/api//users//profile/")

        response = middleware(request)

        with open(self.log_path, "r") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["path"] == "/api//users//profile/"

    def test_noise_paths_case_sensitive(self):
        """Test that noise path matching is case-sensitive"""
        middleware = self.create_middleware(noise_paths=["/Health"])
        request = self.factory.get("/health")  # Different case

        response = middleware(request)

        # Should be logged because case doesn't match
        with open(self.log_path, "r") as f:
            content = f.read()
            assert content != ""
