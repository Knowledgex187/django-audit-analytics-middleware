"""URL configuration for tests"""

from django.urls import path
from django.http import HttpResponse


def test_view(request):
    """Simple test view"""
    return HttpResponse("OK")


def health_view(request):
    """Health check view for testing noise paths"""
    return HttpResponse("OK")


urlpatterns = [
    path("test/", test_view, name="test"),
    path("health/", health_view, name="health"),
    path("admin/", test_view, name="admin"),
]
