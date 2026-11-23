import json
import os
import shutil
import subprocess
import tarfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.db import connections

DEFAULT_BACKUP_ROOT = "/baserow/backups/sometable"

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


def _object_storage_client():
    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
        region_name=settings.AWS_S3_REGION_NAME or None,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": settings.AWS_S3_ADDRESSING_STYLE or "auto"},
        ),
    )


def object_storage_enabled() -> bool:
    return bool(getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""))


def backup_object_storage(dest: str) -> tuple[int, int]:
    if not object_storage_enabled():
        return 0, 0
    s3 = _object_storage_client()
    prefix = (settings.AWS_LOCATION or "").strip("/")
    storage_dir = os.path.join(dest, "object-storage")
    os.makedirs(storage_dir, exist_ok=True)
    count = 0
    total = 0
    paginator = s3.get_paginator("paginate")
    for page in paginator.paginate(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix
    ):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel = key[len(prefix) :].lstrip("/") if prefix else key
            target = os.path.join(storage_dir, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, key, target)
            count += 1
            total += os.path.getsize(target)
    return count, total


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
    with open(os.path.join(dest, "manifest.json"), "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    if keep is None:
        keep = get_config().keep
    apply_retention(keep)
    return manifest


def list_backups() -> list[dict]:
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
        manifest["path"] = path
        items.append(manifest)
    return items


def apply_retention(keep: int) -> None:
    if keep <= 0:
        return
    for item in list_backups()[keep:]:
        shutil.rmtree(item["path"], ignore_errors=True)


def is_due(config: BackupConfig, now: Optional[datetime] = None) -> bool:
    """根据配置判断当前是否到达备份时间。"""

    if config.frequency == "disabled":
        return False
    now = now or datetime.now()
    backups = list_backups()
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


def restore_backup(backup_id: str) -> None:
    """从备份目录恢复数据库与对象存储/媒体。"""

    path = os.path.join(get_backup_root(), backup_id)
    manifest_path = os.path.join(path, "manifest.json")
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

    if manifest.get("object_storage") and object_storage_enabled():
        s3 = _object_storage_client()
        prefix = (settings.AWS_LOCATION or "").strip("/")
        storage_dir = os.path.join(path, "object-storage")
        for root, _, files in os.walk(storage_dir):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, storage_dir)
                key = f"{prefix}/{rel}" if prefix else rel
                s3.upload_file(
                    full,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    key,
                    ExtraArgs={"CacheControl": "max-age=86400"},
                )
