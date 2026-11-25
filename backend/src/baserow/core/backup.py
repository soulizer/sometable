import json
import logging
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.db import connections

from baserow.core.storage_config import (
    build_s3_client,
    load_backup_storage_config,
    load_storage_config,
)

logger = logging.getLogger(__name__)

DEFAULT_BACKUP_ROOT = "/baserow/backups/sometable"
REMOTE_PREFIX = "sometable-backups"
BACKUP_ID_PATTERN = re.compile(r"^\d{8}-\d{6}$")

SCOPE_ALL = "all"
SCOPE_DATABASE = "database"
SCOPE_OBJECT_STORAGE = "object_storage"


@dataclass
class BackupConfig:
    scope: str = SCOPE_ALL
    frequency: str = "daily"
    hour: int = 3
    day_of_week: int = 0
    day_of_month: int = 1
    keep: int = 7


def get_backup_root() -> str:
    root = getattr(settings, "BACKUP_DIR", DEFAULT_BACKUP_ROOT)
    os.makedirs(root, exist_ok=True)
    return root


def _db_settings():
    return connections["default"].settings_dict


def _run(command, env=None):
    subprocess.run(command, check=True, env=env)


def backup_database(dest: str) -> int:
    db = _db_settings()
    target = os.path.join(dest, "database.dump")
    env = dict(os.environ)
    if db.get("PASSWORD"):
        env["PGPASSWORD"] = db["PASSWORD"]
    _run(
        [
            "pg_dump",
            "-h",
            db.get("HOST") or "localhost",
            "-p",
            str(db.get("PORT") or 5432),
            "-U",
            db.get("USER") or "baserow",
            "-d",
            db.get("NAME") or "baserow",
            "-Fc",
            "-f",
            target,
        ],
        env=env,
    )
    return os.path.getsize(target)


def backup_media(dest: str) -> int:
    media_root = settings.MEDIA_ROOT
    if not os.path.isdir(media_root):
        return 0
    target = os.path.join(dest, "media.tar.gz")
    with tarfile.open(target, "w:gz") as tar:
        tar.add(media_root, arcname="media")
    return os.path.getsize(target)


def _object_storage_config():
    config, _ = load_storage_config()
    return config if config.get("type") == "s3" else None


def object_storage_enabled() -> bool:
    """Media object storage, as configured in the admin UI or the environment."""

    return _object_storage_config() is not None


def backup_object_storage(dest: str) -> tuple[int, int]:
    config = _object_storage_config()
    if config is None:
        return 0, 0
    s3 = build_s3_client(config)
    bucket = config["bucket_name"]
    prefix = (config.get("location") or "").strip("/")
    storage_dir = os.path.join(dest, "object-storage")
    os.makedirs(storage_dir, exist_ok=True)
    count = 0
    total = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel = key[len(prefix):].lstrip("/") if prefix else key
            if not rel:
                continue
            target = os.path.join(storage_dir, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            s3.download_file(bucket, key, target)
            count += 1
            total += os.path.getsize(target)
    return count, total


def remote_backup_config():
    """Returns the S3 config for backup archives, or None for local-only."""

    config, _ = load_backup_storage_config()
    return config if config.get("type") == "s3" else None


def remote_key_prefix(config: dict) -> str:
    location = (config.get("location") or "").strip("/")
    return f"{location}/{REMOTE_PREFIX}" if location else REMOTE_PREFIX


def remote_key(config: dict, stamp: str) -> str:
    return f"{remote_key_prefix(config)}/{stamp}.tar.gz"


def _write_manifest(path: str, manifest: dict) -> None:
    with open(path, "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def upload_backup_to_remote(stamp: str, dest: str, manifest: dict) -> None:
    """Uploads the finished backup directory as one archive.

    A remote failure is logged but never makes the local backup fail.
    """

    config = remote_backup_config()
    if config is None:
        return

    fd, archive = tempfile.mkstemp(suffix=".tar.gz")
    os.close(fd)
    try:
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(dest, arcname=stamp)
        key = remote_key(config, stamp)
        build_s3_client(config).upload_file(archive, config["bucket_name"], key)
        manifest["remote"] = {
            "bucket": config["bucket_name"],
            "key": key,
            "bytes": os.path.getsize(archive),
            "uploaded_at": datetime.now().isoformat(),
        }
        _write_manifest(os.path.join(dest, "manifest.json"), manifest)
    except Exception:  # noqa: BLE001 - remote storage must not break local backup
        logger.exception('Failed to upload backup %s to remote storage', stamp)
        manifest["remote_error"] = 'Upload failed; see backend logs.'
        _write_manifest(os.path.join(dest, "manifest.json"), manifest)
    finally:
        if os.path.exists(archive):
            os.unlink(archive)


def run_backup(scope: str = SCOPE_ALL, keep: Optional[int] = None) -> dict:
    """执行一次备份，返回 manifest。"""

    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(get_backup_root(), stamp)
    os.makedirs(dest, exist_ok=True)
    started = datetime.now()
    manifest = {
        "created_at": started.isoformat(),
        "scope": scope,
        "database": None,
        "media": None,
        "object_storage": None,
    }
    if scope in (SCOPE_ALL, SCOPE_DATABASE):
        size = backup_database(dest)
        manifest["database"] = {"file": "database.dump", "bytes": size}
    if scope == SCOPE_ALL:
        size = backup_media(dest)
        if size:
            manifest["media"] = {"file": "media.tar.gz", "bytes": size}
    if scope in (SCOPE_ALL, SCOPE_OBJECT_STORAGE):
        count, size = backup_object_storage(dest)
        manifest["object_storage"] = {"count": count, "bytes": size}
    _write_manifest(os.path.join(dest, "manifest.json"), manifest)

    upload_backup_to_remote(stamp, dest, manifest)

    if keep is None:
        keep = get_config().keep
    apply_retention(keep)
    return manifest


def _local_backups() -> list[dict]:
    root = get_backup_root()
    items = []
    for name in sorted(os.listdir(root), reverse=True):
        path = os.path.join(root, name)
        manifest_path = os.path.join(path, "manifest.json")
        if not os.path.isdir(path) or not os.path.exists(manifest_path):
            continue
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        manifest["id"] = name
        manifest["local"] = True
        manifest["_path"] = path
        items.append(manifest)
    return items


def list_backups() -> list[dict]:
    """Returns local backups only, without exposing server-side paths."""

    return [
        {k: v for k, v in item.items() if k != "_path"}
        for item in _local_backups()
    ]


def list_remote_backups() -> list[dict]:
    config = remote_backup_config()
    if config is None:
        return []
    items = []
    try:
        client = build_s3_client(config)
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=config["bucket_name"], Prefix=remote_key_prefix(config) + "/"
        ):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                stamp = os.path.basename(key).removesuffix(".tar.gz")
                if not BACKUP_ID_PATTERN.fullmatch(stamp):
                    continue
                items.append(
                    {
                        "id": stamp,
                        "created_at": datetime.strptime(
                            stamp, "%Y%m%d-%H%M%S"
                        ).isoformat(),
                        "scope": None,
                        "database": None,
                        "media": None,
                        "object_storage": None,
                        "local": False,
                        "remote": {
                            "bucket": config["bucket_name"],
                            "key": key,
                            "bytes": obj.get("Size", 0),
                        },
                    }
                )
    except Exception:  # noqa: BLE001 - listing must not break the backup page
        logger.exception('Failed to list remote backups')
    return sorted(items, key=lambda item: item["id"], reverse=True)


def list_all_backups() -> list[dict]:
    """Merges local and remote backups, preferring the richer local manifest."""

    local = list_backups()
    local_ids = {item["id"] for item in local}
    return local + [
        item for item in list_remote_backups() if item["id"] not in local_ids
    ]


def apply_retention(keep: int) -> None:
    if keep <= 0:
        return
    for item in _local_backups()[keep:]:
        shutil.rmtree(item["_path"], ignore_errors=True)

    config = remote_backup_config()
    if config is None:
        return
    try:
        client = build_s3_client(config)
        paginator = client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(
            Bucket=config["bucket_name"], Prefix=remote_key_prefix(config) + "/"
        ):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                stamp = os.path.basename(key).removesuffix(".tar.gz")
                if BACKUP_ID_PATTERN.fullmatch(stamp):
                    keys.append(key)
        for key in sorted(keys, reverse=True)[keep:]:
            client.delete_object(Bucket=config["bucket_name"], Key=key)
    except Exception:  # noqa: BLE001 - retention must not break local backup
        logger.exception('Failed to apply remote backup retention')


def is_due(config: BackupConfig, now: Optional[datetime] = None) -> bool:
    """根据配置判断当前是否到达备份时间。"""

    if config.frequency == "disabled":
        return False
    now = now or datetime.now()
    backups = list_all_backups()
    last = None
    if backups:
        try:
            last = datetime.fromisoformat(backups[0]["created_at"])
        except (KeyError, ValueError):
            last = None
    if config.frequency == "daily":
        target = now.replace(hour=config.hour, minute=0, second=0, microsecond=0)
        if now < target:
            target -= timedelta(days=1)
        return last is None or last < target
    if config.frequency == "weekly":
        target = now.replace(hour=config.hour, minute=0, second=0, microsecond=0)
        target -= timedelta(days=(now.weekday() - config.day_of_week) % 7)
        if now < target:
            target -= timedelta(days=7)
        return last is None or last < target
    if config.frequency == "monthly":
        target = now.replace(
            day=config.day_of_month,
            hour=config.hour,
            minute=0,
            second=0,
            microsecond=0,
        )
        if now < target:
            month = target.month - 1 or 12
            year = target.year if target.month > 1 else target.year - 1
            target = target.replace(month=month, year=year)
        return last is None or last < target
    return False


def get_config() -> BackupConfig:
    from baserow.core.handler import CoreHandler

    s = CoreHandler().get_settings()
    return BackupConfig(
        scope=s.backup_scope,
        frequency=s.backup_frequency,
        hour=s.backup_hour,
        day_of_week=s.backup_dow,
        day_of_month=s.backup_dom,
        keep=s.backup_keep,
    )


def _download_remote_backup(backup_id: str) -> None:
    config = remote_backup_config()
    if config is None:
        raise FileNotFoundError(backup_id)
    fd, archive = tempfile.mkstemp(suffix=".tar.gz")
    os.close(fd)
    try:
        build_s3_client(config).download_file(
            config["bucket_name"], remote_key(config, backup_id), archive
        )
        with tarfile.open(archive) as tar:
            tar.extractall(path=get_backup_root(), filter="data")
    except Exception:
        logger.exception('Failed to download backup %s from remote', backup_id)
        raise FileNotFoundError(backup_id) from None
    finally:
        if os.path.exists(archive):
            os.unlink(archive)


def restore_backup(backup_id: str) -> None:
    """从备份目录恢复数据库与对象存储/媒体。"""

    if not BACKUP_ID_PATTERN.fullmatch(backup_id):
        raise FileNotFoundError(backup_id)

    path = os.path.join(get_backup_root(), backup_id)
    manifest_path = os.path.join(path, "manifest.json")
    if not os.path.exists(manifest_path):
        _download_remote_backup(backup_id)
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(backup_id)
    with open(manifest_path) as f:
        manifest = json.load(f)

    if manifest.get("database"):
        db = _db_settings()
        env = dict(os.environ)
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]
        _run(
            [
                "pg_restore",
                "-h",
                db.get("HOST") or "localhost",
                "-p",
                str(db.get("PORT") or 5432),
                "-U",
                db.get("USER") or "baserow",
                "-d",
                db.get("NAME") or "baserow",
                "--no-owner",
                "--clean",
                "--if-exists",
                os.path.join(path, manifest["database"]["file"]),
            ],
            env=env,
        )

    if manifest.get("media"):
        media_root = settings.MEDIA_ROOT
        with tarfile.open(os.path.join(path, manifest["media"]["file"])) as tar:
            tar.extractall(path=os.path.dirname(media_root), filter="data")

    config = _object_storage_config()
    if manifest.get("object_storage") and config is not None:
        s3 = build_s3_client(config)
        bucket = config["bucket_name"]
        prefix = (config.get("location") or "").strip("/")
        storage_dir = os.path.join(path, "object-storage")
        for root, _, files in os.walk(storage_dir):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, storage_dir)
                key = f"{prefix}/{rel}" if prefix else rel
                s3.upload_file(
                    full,
                    bucket,
                    key,
                    ExtraArgs={"CacheControl": "max-age=86400"},
                )
