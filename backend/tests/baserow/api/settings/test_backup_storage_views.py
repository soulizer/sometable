import json
import os

from django.test.utils import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN


@pytest.fixture
def backup_storage_file(tmp_path):
    return str(tmp_path / 'backup-storage.json')


@pytest.mark.django_db
def test_backup_storage_settings_requires_staff(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse('api:settings:backup_storage'),
        HTTP_AUTHORIZATION=f'JWT {token}',
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_backup_storage_defaults_to_local(
    api_client, data_fixture, backup_storage_file
):
    _, token = data_fixture.create_user_and_token(is_staff=True)

    with override_settings(BACKUP_STORAGE_SETTINGS_FILE=backup_storage_file):
        response = api_client.get(
            reverse('api:settings:backup_storage'),
            HTTP_AUTHORIZATION=f'JWT {token}',
        )
    assert response.status_code == HTTP_200_OK
    assert response.json()['type'] == 'local'
    assert response.json()['source'] == 'default'


@pytest.mark.django_db
def test_backup_storage_put_never_returns_secrets(
    api_client, data_fixture, backup_storage_file
):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    body = {
        'type': 's3',
        'bucket_name': 'backup-bucket',
        'endpoint_url': 'https://s3.example.com',
        'region_name': '',
        'location': 'sometable',
        'access_key_id': 'AKIAEXAMPLE',
        'secret_access_key': 'top-secret',
        'addressing_style': 'path',
        'querystring_auth': True,
    }

    with override_settings(BACKUP_STORAGE_SETTINGS_FILE=backup_storage_file):
        put = api_client.put(
            reverse('api:settings:backup_storage'),
            body,
            format='json',
            HTTP_AUTHORIZATION=f'JWT {token}',
        )
        assert put.status_code == HTTP_200_OK
        data = put.json()
        assert data['has_credentials'] is True
        assert 'access_key_id' not in data
        assert 'secret_access_key' not in data

        stored = json.load(open(backup_storage_file))
        assert stored['secret_access_key'] == 'top-secret'
        assert os.stat(backup_storage_file).st_mode & 0o777 == 0o600

        # Leaving the secret blank keeps the stored one and does not leak it.
        body['secret_access_key'] = ''
        put2 = api_client.put(
            reverse('api:settings:backup_storage'),
            body,
            format='json',
            HTTP_AUTHORIZATION=f'JWT {token}',
        )
        assert put2.status_code == HTTP_200_OK
        assert json.load(open(backup_storage_file))['secret_access_key'] == (
            'top-secret'
        )


@pytest.mark.django_db
def test_backup_storage_put_rejects_incomplete_s3(
    api_client, data_fixture, backup_storage_file
):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    with override_settings(BACKUP_STORAGE_SETTINGS_FILE=backup_storage_file):
        response = api_client.put(
            reverse('api:settings:backup_storage'),
            {'type': 's3', 'bucket_name': 'backup-bucket'},
            format='json',
            HTTP_AUTHORIZATION=f'JWT {token}',
        )
    assert response.status_code == HTTP_400_BAD_REQUEST
