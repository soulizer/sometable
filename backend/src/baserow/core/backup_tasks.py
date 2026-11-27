import logging

from baserow.config.celery import app

from .backup import SCOPE_ALL, get_config, is_due, restore_backup, run_backup
from .backup_status import (
    RESTORE_FAILED,
    RESTORE_RUNNING,
    RESTORE_SUCCESS,
    clear_maintenance_mode,
    set_maintenance_mode,
    set_restore_status,
)

logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def run_due_backup():
    """到点自动备份：由 Celery beat 每 15 分钟触发一次。"""

    config = get_config()
    if is_due(config):
        run_backup(config.scope, config.keep)


@app.task(ignore_result=True)
def run_backup_now(scope: str = "all"):
    """立即执行一次备份（由管理界面触发）。"""

    run_backup(scope=scope)


@app.task(ignore_result=True)
def restore_backup_task(token: str, backup_id: str):
    """Restores a backup in the background and reports progress via the cache."""

    set_restore_status(
        token, RESTORE_RUNNING, 10, "Creating a safety backup before the restore."
    )
    if not set_maintenance_mode(token):
        set_restore_status(
            token,
            RESTORE_FAILED,
            0,
            "Another restore is already in progress.",
        )
        return

    try:
        # Retention is skipped so the safety copy cannot delete the backup that
        # is about to be restored.
        run_backup(scope=SCOPE_ALL, keep=0)
        set_restore_status(
            token, RESTORE_RUNNING, 40, "Restoring the selected backup."
        )
        restore_backup(backup_id)
        set_restore_status(token, RESTORE_SUCCESS, 100, "Restore completed.")
    except FileNotFoundError:
        logger.warning("Backup %s not found during restore", backup_id)
        set_restore_status(token, RESTORE_FAILED, 0, "Backup not found.")
    except Exception as exc:  # noqa: BLE001 - status must reflect any failure
        logger.exception("Failed to restore backup %s", backup_id)
        set_restore_status(token, RESTORE_FAILED, 0, str(exc) or "Restore failed.")
    finally:
        clear_maintenance_mode(token)


@app.on_after_finalize.connect
def setup_periodic_backup_tasks(sender, **kwargs) -> None:
    sender.add_periodic_task(900.0, run_due_backup.s())
