#!/usr/bin/env bash
#
# Backs up the sometable.com deployment:
#   - PostgreSQL database (pg_dump custom format)
#   - local Docker media volume (only when object storage is not configured)
#   - a manifest with sizes and checksums
#
# Usage:  sudo -n bash docs/deployment/scripts/backup-sometable.sh
# Env:    KEEP=7          number of backup sets to keep
#         BACKUP_DIR=...  destination directory
#
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$PROJECT_DIR" || exit 1

KEEP="${KEEP:-7}"
BACKUP_ROOT="${BACKUP_DIR:-/www/backups/sometable}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_ROOT/$STAMP"

COMPOSE=(sudo -n docker compose)

mkdir -p "$DEST" || exit 1

echo "[$(date -Is)] backup start -> $DEST"

# --- database -------------------------------------------------------------
if ! "${COMPOSE[@]}" exec -T db sh -c \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$DEST/database.dump"; then
  echo "[$(date -Is)] ERROR: database backup failed" >&2
  rm -rf "$DEST"
  exit 1
fi

# --- media ----------------------------------------------------------------
STORAGE_TYPE="local"
if grep -q '^AWS_STORAGE_BUCKET_NAME=.\+' .env 2>/dev/null; then
  STORAGE_TYPE="object-storage"
  echo "Object storage detected; the media bucket must be backed up separately." \
    > "$DEST/MEDIA_BACKUP_NOTICE.txt"
else
  if ! sudo -n docker run --rm -v sometable_media:/mnt:ro busybox \
    tar czf - -C /mnt . > "$DEST/media.tar.gz"; then
    echo "[$(date -Is)] ERROR: media backup failed" >&2
    rm -rf "$DEST"
    exit 1
  fi
fi

# --- object storage -----------------------------------------------------
mkdir -p /www/backups "$DEST"
sudo -n chown -R 9999:9999 "$DEST" 2>/dev/null || true
if ! sudo -n docker compose exec -T backend sh -c \
  "OBJECT_STORAGE_BACKUP_MODE=backup OBJECT_STORAGE_BACKUP_DIR=/baserow/backups/sometable/$STAMP python /baserow/scripts/backup-object-storage.py"; then
  echo "[$(date -Is)] ERROR: object storage backup failed" >&2
  rm -rf "$DEST"
  exit 1
fi

# --- manifest -------------------------------------------------------------
VERSION="$(grep '^BASEROW_VERSION=' .env 2>/dev/null | cut -d= -f2-)"
{
  echo "created_at=$(date -Is)"
  echo "project_dir=$PROJECT_DIR"
  echo "baserow_version=$VERSION"
  echo "storage_type=$STORAGE_TYPE"
  echo "hostname=$(hostname)"
  echo
  echo "--- files ---"
  (cd "$DEST" && ls -l)
  echo
  echo "--- sha256 ---"
  (cd "$DEST" && sha256sum ./* 2>/dev/null | grep -v manifest.txt)
} > "$DEST/manifest.txt"

# --- retention ------------------------------------------------------------
if [ -d "$BACKUP_ROOT" ]; then
  mapfile -t OLD < <(ls -1d "$BACKUP_ROOT"/*/ 2>/dev/null | sort -r | tail -n +$((KEEP + 1)))
  for dir in "${OLD[@]}"; do
    echo "[$(date -Is)] removing old backup $dir"
    rm -rf "$dir"
  done
fi

echo "[$(date -Is)] backup done: $DEST"
