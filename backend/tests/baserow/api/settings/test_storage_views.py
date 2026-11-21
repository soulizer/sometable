from django.test.utils import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)


@pytest.mark.django_db
@override_settings(
    STORAGE_SETTINGS_FILE="/tmp/baserow-test-storage-settings.json",
    AWS_STORAGE_ENABLED=False,
)
def test_storage_settings_requires_staff(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:settings:storage"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
@override_settings(
    STORAGE_SETTINGS_FILE="/tmp/baserow-test-storage-settings.json",
    AWS_STORAGE_ENABLED=False,
)
def test_storage_settings_get_and_update(api_client, data_fixture, tmp_path):
    user, token = data_fixture.create_user_and_token(is_staff=True)
    settings_file = tmp_path / "storage.json"

    with override_settings(STORAGE_SETTINGS_FILE=str(settings_file)):
        response = api_client.get(
            reverse("api:settings:storage"),
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK
        assert response.json()["type"] == "local"
        assert response.json()["source"] == "default"

        response = api_client.put(
            reverse("api:settings:storage"),
            {"type": "local"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK
        assert response.json()["source"] == "file"
        assert settings_file.exists()


@pytest.mark.django_db
@override_settings(
    STORAGE_SETTINGS_FILE="/tmp/baserow-test-storage-settings.json",
    AWS_STORAGE_ENABLED=False,
)
def test_storage_settings_rejects_incomplete_s3(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.put(
        reverse("api:settings:storage"),
        {"type": "s3", "bucket_name": "bucket"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@override_settings(
    STORAGE_SETTINGS_FILE="/tmp/baserow-test-storage-settings.json",
    AWS_STORAGE_ENABLED=False,
)
def test_storage_settings_test_local_connection(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.post(
        reverse("api:settings:storage_test"),
        {"type": "local"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"ok": True}
