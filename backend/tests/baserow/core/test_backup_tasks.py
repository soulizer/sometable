from unittest.mock import patch

from django.core.cache import cache

import pytest

from baserow.core.backup import SCOPE_ALL
from baserow.core.backup_status import (
    RESTORE_FAILED,
    RESTORE_SUCCESS,
    clear_maintenance_mode,
    is_maintenance_mode_enabled,
    restore_status_key,
    set_maintenance_mode,
)
from baserow.core.backup_tasks import restore_backup_task

RESTORE_TOKEN = "core-restore-task-token"
BACKUP_ID = "20240101-000000"


@pytest.fixture(autouse=True)
def cleanup_restore_state():
    yield
    cache.delete(restore_status_key(RESTORE_TOKEN))
    clear_maintenance_mode()


def test_restore_task_records_success_and_clears_maintenance():
    def assert_maintenance_on(backup_id):
        assert backup_id == BACKUP_ID
        assert is_maintenance_mode_enabled()

    with patch("baserow.core.backup_tasks.run_backup") as run_backup_mock:
        with patch(
            "baserow.core.backup_tasks.restore_backup",
            side_effect=assert_maintenance_on,
        ) as restore_backup_mock:
            restore_backup_task(RESTORE_TOKEN, BACKUP_ID)

    run_backup_mock.assert_called_once_with(scope=SCOPE_ALL, keep=0)
    restore_backup_mock.assert_called_once_with(BACKUP_ID)
    from_cache = cache.get(restore_status_key(RESTORE_TOKEN))
    assert from_cache["status"] == RESTORE_SUCCESS
    assert from_cache["progress"] == 100
    assert not is_maintenance_mode_enabled()


def test_restore_task_records_failure_and_clears_maintenance():
    with patch("baserow.core.backup_tasks.run_backup"):
        with patch(
            "baserow.core.backup_tasks.restore_backup",
            side_effect=RuntimeError("restore exploded"),
        ):
            restore_backup_task(RESTORE_TOKEN, BACKUP_ID)

    from_cache = cache.get(restore_status_key(RESTORE_TOKEN))
    assert from_cache["status"] == RESTORE_FAILED
    assert from_cache["message"] == "restore exploded"
    assert not is_maintenance_mode_enabled()


def test_restore_task_reports_missing_backup():
    with patch("baserow.core.backup_tasks.run_backup"):
        with patch(
            "baserow.core.backup_tasks.restore_backup",
            side_effect=FileNotFoundError(BACKUP_ID),
        ):
            restore_backup_task(RESTORE_TOKEN, BACKUP_ID)

    from_cache = cache.get(restore_status_key(RESTORE_TOKEN))
    assert from_cache["status"] == RESTORE_FAILED
    assert from_cache["message"] == "Backup not found."
    assert not is_maintenance_mode_enabled()


def test_restore_task_does_not_clear_another_restores_maintenance_flag():
    other_token = "another-restore-token"
    with patch("baserow.core.backup_tasks.run_backup") as run_backup_mock:
        with patch("baserow.core.backup_tasks.restore_backup"):
            set_maintenance_mode(other_token)
            try:
                restore_backup_task(RESTORE_TOKEN, BACKUP_ID)
                assert is_maintenance_mode_enabled()
                from_cache = cache.get(restore_status_key(RESTORE_TOKEN))
                assert from_cache["status"] == RESTORE_FAILED
                assert from_cache["message"] == "Another restore is already in progress."
                run_backup_mock.assert_not_called()
            finally:
                clear_maintenance_mode(other_token)
