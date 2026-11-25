import json
from unittest.mock import MagicMock, patch

from django.test.utils import override_settings

import pytest

from baserow.core.backup import (
    list_all_backups,
    list_remote_backups,
    upload_backup_to_remote,
)


@pytest.fixture
def remote_config_file(tmp_path):
    path = tmp_path / 'backup-storage.json'
    path.write_text(
        json.dumps(
            {
                'type': 's3',
                'bucket_name': 'backup-bucket',
                'endpoint_url': 'https://s3.example.com',
                'region_name': '',
                'location': 'sometable',
                'access_key_id': 'AKIAEXAMPLE',
                'secret_access_key': 'secret',
                'addressing_style': 'path',
            }
        )
    )
    return str(path)


@pytest.mark.django_db
def test_upload_backup_to_remote(tmp_path, remote_config_file):
    dest = tmp_path / '20261125-030000'
    dest.mkdir()
    manifest = {'scope': 'database'}
    (dest / 'manifest.json').write_text(json.dumps(manifest))

    client = MagicMock()
    with override_settings(
        BACKUP_STORAGE_SETTINGS_FILE=remote_config_file,
        BACKUP_DIR=str(tmp_path),
    ), patch(
        'baserow.core.backup.build_s3_client', return_value=client
    ):
        upload_backup_to_remote('20261125-030000', str(dest), manifest)

    client.upload_file.assert_called_once()
    args = client.upload_file.call_args.args
    assert args[1] == 'backup-bucket'
    assert args[2] == 'sometable/sometable-backups/20261125-030000.tar.gz'
    saved = json.loads((dest / 'manifest.json').read_text())
    assert saved['remote']['bucket'] == 'backup-bucket'
    assert saved['remote']['key'].endswith('.tar.gz')


@pytest.mark.django_db
def test_list_remote_backups_merges_with_local(tmp_path, remote_config_file):
    local = tmp_path / '20261125-030000'
    local.mkdir()
    (local / 'manifest.json').write_text(json.dumps({'scope': 'database'}))

    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value = [
        {
            'Contents': [
                {'Key': 'sometable/sometable-backups/20261125-030000.tar.gz', 'Size': 1},
                {'Key': 'sometable/sometable-backups/20261124-030000.tar.gz', 'Size': 2},
                {'Key': 'sometable/other/file.txt', 'Size': 3},
            ]
        }
    ]
    with override_settings(
        BACKUP_STORAGE_SETTINGS_FILE=remote_config_file,
        BACKUP_DIR=str(tmp_path),
    ), patch(
        'baserow.core.backup.build_s3_client', return_value=client
    ):
        remote = list_remote_backups()
        all_backups = list_all_backups()

    assert len(remote) == 2
    assert remote[0]['id'] == '20261125-030000'
    assert remote[0]['local'] is False
    assert len(all_backups) == 2
    assert any(item['id'] == '20261124-030000' for item in all_backups)
