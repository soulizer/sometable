"""Cache backed state for asynchronous backup restores.

These values intentionally live in Redis via Django's cache framework instead of
the database: ``pg_restore --clean`` can drop database tables while a restore is
running, which would make any database backed progress or maintenance flag
unavailable at exactly the moment it is needed.
"""

from django.core.cache import cache

RESTORE_STATUS_PREFIX = "baserow:backup-restore-status:"
MAINTENANCE_MODE_CACHE_KEY = "baserow:backup-restore-maintenance"

# Keep finished restores long enough for an admin to reload the status page.
RESTORE_STATUS_TTL = 24 * 60 * 60
# Safety net in case a worker is killed before the task can clear the flag.
MAINTENANCE_MODE_TTL = 2 * 60 * 60

RESTORE_PENDING = "pending"
RESTORE_RUNNING = "running"
RESTORE_SUCCESS = "success"
RESTORE_FAILED = "failed"


def restore_status_key(token: str) -> str:
    return f"{RESTORE_STATUS_PREFIX}{token}"


def set_restore_status(
    token: str,
    status: str,
    progress: int | None = None,
    message: str | None = None,
) -> dict:
    """Updates the status stored under ``token`` and returns the new value."""

    key = restore_status_key(token)
    value = cache.get(key) or {}
    value["status"] = status
    if progress is not None:
        value["progress"] = progress
    if message is not None:
        value["message"] = message
    cache.set(key, value, timeout=RESTORE_STATUS_TTL)
    return value


def get_restore_status(token: str) -> dict | None:
    return cache.get(restore_status_key(token))


def set_maintenance_mode(token: str) -> bool:
    """
    Blocks normal API requests while the restore identified by ``token`` runs.

    Returns False when a different restore already owns the flag. The existing
    flag is never overwritten so a second restore cannot clear the first one.
    """

    existing_token = cache.get(MAINTENANCE_MODE_CACHE_KEY)
    if existing_token is not None and existing_token != token:
        return False
    cache.set(MAINTENANCE_MODE_CACHE_KEY, token, timeout=MAINTENANCE_MODE_TTL)
    return True


def clear_maintenance_mode(token: str | None = None) -> None:
    """Clears the flag, but never one that belongs to a different restore."""

    if token is None or cache.get(MAINTENANCE_MODE_CACHE_KEY) == token:
        cache.delete(MAINTENANCE_MODE_CACHE_KEY)


def is_maintenance_mode_enabled() -> bool:
    return cache.get(MAINTENANCE_MODE_CACHE_KEY) is not None
