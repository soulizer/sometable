from datetime import datetime, timedelta

from django.test.utils import override_settings

import pytest

from baserow.core.backup import list_backups, run_backup


@pytest.mark.django_db
@override_settings(BACKUP_DIR="/tmp/baserow-test-backups")
def test_run_backup_creates_manifest(tmp_path):
    with override_settings(BACKUP_DIR=str(tmp_path)):
        manifest = run_backup(scope="database", keep=3)
        assert manifest["scope"] == "database"
        assert manifest["database"]["bytes"] > 0
        backups = list_backups()
        assert len(backups) == 1
        assert backups[0]["id"]
        assert backups[0]["database"]["bytes"] > 0


@pytest.mark.django_db
@override_settings(BACKUP_DIR="/tmp/baserow-test-backups")
def test_backup_retention(tmp_path):
    with override_settings(BACKUP_DIR=str(tmp_path)):
        for _ in range(3):
            run_backup(scope="database", keep=2)
        backups = list_backups()
        assert len(backups) == 2

