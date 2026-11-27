from unittest.mock import patch

from django.core.cache import cache
from django.test.utils import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from baserow.core.backup_status import (
    RESTORE_PENDING,
    RESTORE_RUNNING,
    restore_status_key,
    set_restore_status,
)


@pytest.mark.django_db
@override_settings(BACKUP_DIR="/tmp/baserow-test-backups")
def test_backup_settings_requires_staff(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:settings:backups"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
@override_settings(BACKUP_DIR="/tmp/baserow-test-backups")
def test_backup_settings_list_and_queue(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.get(
        reverse("api:settings:backups"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == []

    with patch("baserow.core.backup_tasks.run_backup_now") as mock_task:
        response = api_client.post(
            reverse("api:settings:backups"),
            {"scope": "database"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    assert response.status_code == HTTP_200_OK
    assert response.json()["queued"] is True
    assert mock_task.delay.called


@pytest.mark.django_db
def test_backup_restore_queues_async_task(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    with patch("baserow.core.backup_tasks.restore_backup_task") as mock_task:
        response = api_client.post(
            reverse("api:settings:backups_restore"),
            {"id": "20240101-000000", "confirm": "20240101-000000"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert response.status_code == HTTP_202_ACCEPTED
    restore_token = response.json()["token"]
    assert restore_token
    mock_task.delay.assert_called_once_with(restore_token, "20240101-000000")

    status_response = api_client.get(
        reverse(
            "api:settings:backups_restore_status",
            kwargs={"token": restore_token},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert status_response.status_code == HTTP_200_OK
    assert status_response.json()["status"] == RESTORE_PENDING
    cache.delete(restore_status_key(restore_token))


@pytest.mark.django_db
def test_backup_restore_validates_payload(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)
    url = reverse("api:settings:backups_restore")

    with patch("baserow.core.backup_tasks.restore_backup_task") as mock_task:
        response = api_client.post(
            url,
            {"confirm": "20240101-000000"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

        response = api_client.post(
            url,
            {"id": "20240101-000000", "confirm": "other"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    assert not mock_task.delay.called


@pytest.mark.django_db
def test_backup_restore_status(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)
    restore_token = "status-test-token"
    set_restore_status(restore_token, RESTORE_RUNNING, 42, "Restoring the backup.")

    response = api_client.get(
        reverse(
            "api:settings:backups_restore_status",
            kwargs={"token": restore_token},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "status": RESTORE_RUNNING,
        "progress": 42,
        "message": "Restoring the backup.",
    }

    response = api_client.get(
        reverse(
            "api:settings:backups_restore_status",
            kwargs={"token": "unknown-token"},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    cache.delete(restore_status_key(restore_token))


@pytest.mark.django_db
def test_backup_restore_status_requires_staff(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    restore_token = "status-staff-test-token"
    set_restore_status(restore_token, RESTORE_RUNNING)

    response = api_client.get(
        reverse(
            "api:settings:backups_restore_status",
            kwargs={"token": restore_token},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN
    cache.delete(restore_status_key(restore_token))
