from unittest.mock import patch

from django.test.utils import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN


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
