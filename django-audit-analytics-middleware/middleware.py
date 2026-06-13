from django.utils import timezone
from django.conf import settings
import json


class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.log_path = getattr(settings, "ANALYTICS_LOG_PATH", None)
        self.noise_paths = getattr(
            settings, "ANALYTICS_NOISE_PATHS", ["/health", "/admin", "/favicon.ico"]
        )
        self.disabled = not self.log_path

    def __call__(self, request):
        if self.disabled:
            return self.get_response(request)

        if any(request.path.startswith(path) for path in self.noise_paths):
            return self.get_response(request)

        start = timezone.now()
        response = self.get_response(request)
        duration = timezone.now() - start

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.META.get("REMOTE_ADDR")
        )

        log_entry = {
            "path": request.path,
            "method": request.method,
            "status": response.status_code,
            "user_uuid": str(request.user.uuid)
            if request.user.is_authenticated
            else "unauthorized user",
            "duration_ms": int(round(duration.total_seconds() * 1000)),
            "ip": ip,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "referrer": request.META.get("HTTP_REFERER", ""),
            "timestamp": timezone.now().isoformat(),
            "month": timezone.now().strftime("%b"),
            "week": timezone.now().strftime("%V"),
            "day": timezone.now().strftime("%a"),
            "hour": timezone.now().strftime("%H"),
        }

        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            print(f"[Analytics Middleware Error]: {str(e)}")

        return response
