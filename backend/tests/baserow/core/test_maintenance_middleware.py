import json
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

import pytest

from baserow.core.backup_status import (
    clear_maintenance_mode,
    set_maintenance_mode,
)
from baserow.middleware import MaintenanceModeMiddleware

STAFF_USER = SimpleNamespace(is_authenticated=True, is_staff=True)


@pytest.fixture(autouse=True)
def cleanup_maintenance_flag():
    yield
    clear_maintenance_mode()


def make_middleware():
    def get_response(request):
        return HttpResponse("ok")

    return MaintenanceModeMiddleware(get_response)


@pytest.mark.parametrize(
    "path",
    [
        "/api/_health/",
        "/api/_health/live/",
        "/static/core.css",
        "/_nuxt/app.js",
        "/favicon.ico",
    ],
)
def test_maintenance_mode_allows_health_and_static_paths(api_request_factory, path):
    middleware = make_middleware()
    request = api_request_factory.get(path)
    request.user = AnonymousUser()

    set_maintenance_mode("token")
    response = middleware(request)

    assert response.status_code == 200
    assert response.content == b"ok"


def test_maintenance_mode_allows_staff_backup_routes(api_request_factory):
    middleware = make_middleware()
    request = api_request_factory.get(
        "/api/settings/backups/restore/token/status/"
    )
    request.user = STAFF_USER

    set_maintenance_mode("token")
    response = middleware(request)

    assert response.status_code == 200
    assert response.content == b"ok"


def test_maintenance_mode_blocks_normal_requests(api_request_factory):
    middleware = make_middleware()
    request = api_request_factory.get("/api/applications/")
    request.user = AnonymousUser()

    assert middleware(request).status_code == 200

    set_maintenance_mode("token")
    response = middleware(request)

    assert response.status_code == 503
    assert response.status_code == 503
    assert json.loads(response.content)["error"] == "ERROR_MAINTENANCE_MODE"

    clear_maintenance_mode()
    assert middleware(request).status_code == 200


def test_maintenance_mode_blocks_non_staff_backup_routes(api_request_factory):
    middleware = make_middleware()
    request = api_request_factory.get("/api/settings/backups/")
    request.user = AnonymousUser()

    set_maintenance_mode("token")
    response = middleware(request)

    assert response.status_code == 503
    assert response.status_code == 503
    assert json.loads(response.content)["error"] == "ERROR_MAINTENANCE_MODE"
