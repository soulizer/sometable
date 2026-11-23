# 对象存储备份 / 恢复（在 backend 容器内通过 `manage shell` 运行）。
#
# 环境变量：
#   OBJECT_STORAGE_BACKUP_MODE=backup|restore
#   OBJECT_STORAGE_BACKUP_DIR=/baserow/backups/<批次目录>
#
# 备份：把 AWS_LOCATION 前缀下的所有对象下载到 BACKUP_DIR/object-storage/，
#       并生成 manifest.json。
# 恢复：把 BACKUP_DIR/object-storage/ 下的文件按相对路径上传回该前缀。
import json
import os
import sys
import time

import boto3
from botocore.client import Config
from django.conf import settings

MODE = os.environ.get("OBJECT_STORAGE_BACKUP_MODE", "backup")
BACKUP_DIR = os.environ.get("OBJECT_STORAGE_BACKUP_DIR", "/baserow/backups/object-storage")
PREFIX = (settings.AWS_LOCATION or "").strip("/")
STORAGE_DIR = os.path.join(BACKUP_DIR, "object-storage")


def client():
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


def list_keys(s3):
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=PREFIX
    ):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


def backup():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    s3 = client()
    keys = list_keys(s3)
    total = 0
    for index, key in enumerate(keys, 1):
        rel = key[len(PREFIX) :].lstrip("/") if PREFIX else key
        dest = os.path.join(STORAGE_DIR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, key, dest)
        total += os.path.getsize(dest)
        print(f"downloaded {index}/{len(keys)} {key}", flush=True)
    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "bucket": settings.AWS_STORAGE_BUCKET_NAME,
        "prefix": PREFIX,
        "count": len(keys),
        "bytes": total,
        "keys": keys,
    }
    with open(os.path.join(BACKUP_DIR, "object-storage-manifest.json"), "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(
        f"OBJECT_STORAGE_BACKUP_OK count={len(keys)} bytes={total}",
        flush=True,
    )


def restore():
    manifest_path = os.path.join(BACKUP_DIR, "object-storage-manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    s3 = client()
    uploaded = 0
    for key in manifest["keys"]:
        rel = key[len(PREFIX) :].lstrip("/") if PREFIX else key
        src = os.path.join(STORAGE_DIR, rel)
        if not os.path.exists(src):
            print(f"MISSING {src}", flush=True)
            continue
        s3.upload_file(
            src,
            settings.AWS_STORAGE_BUCKET_NAME,
            key,
            ExtraArgs={"CacheControl": "max-age=86400"},
        )
        uploaded += 1
        print(f"uploaded {uploaded}/{len(manifest['keys'])} {key}", flush=True)
    print(f"OBJECT_STORAGE_RESTORE_OK count={uploaded}", flush=True)


if __name__ == "__main__":
    if MODE == "restore":
        restore()
    else:
        backup()
