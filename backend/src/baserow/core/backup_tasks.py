from baserow.config.celery import app

from .backup import get_config, is_due, run_backup


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


@app.on_after_finalize.connect
def setup_periodic_backup_tasks(sender, **kwargs) -> None:
    sender.add_periodic_task(900.0, run_due_backup.s())
