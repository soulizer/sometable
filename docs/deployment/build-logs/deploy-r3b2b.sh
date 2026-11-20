#!/usr/bin/env bash
set -uo pipefail
cd /www/apps/sometable
TAG="local-20261120-1810-r3b2b"
LOG=docs/deployment/build-logs/r3b2b.log
BUILD_PID=${1:-}
DEPLOY_LOG=docs/deployment/build-logs/r3b2b-deploy.log
ts(){ date -Is; }

echo "[$(ts)] deploy-watcher start waiting for pid=${BUILD_PID:-unknown}" >> "$DEPLOY_LOG"
if [[ -n "${BUILD_PID}" ]]; then
  while kill -0 "$BUILD_PID" 2>/dev/null; do
    sleep 20
  done
fi
echo "[$(ts)] build process exited or not provided" >> "$DEPLOY_LOG"

if grep -q "backend build done rc=0" "$LOG" && grep -q "web-frontend build done rc=0" "$LOG"; then
  echo "[$(ts)] build success detected" >> "$DEPLOY_LOG"
else
  echo "[$(ts)] build FAILED or incomplete; tail:" >> "$DEPLOY_LOG"
  tail -n 80 "$LOG" >> "$DEPLOY_LOG" 2>&1 || true
  exit 1
fi

cp .env ".env.bak-r3b2b-$(date +%Y%m%d%H%M%S)"
if grep -q '^BASEROW_VERSION=' .env; then
  sed -i "s/^BASEROW_VERSION=.*/BASEROW_VERSION=${TAG}/" .env
else
  echo "BASEROW_VERSION=${TAG}" >> .env
fi
echo "[$(ts)] .env BASEROW_VERSION=$(grep '^BASEROW_VERSION=' .env)" >> "$DEPLOY_LOG"

echo "[$(ts)] docker compose up -d" >> "$DEPLOY_LOG"
sudo -n env BASEROW_VERSION="$TAG" docker compose up -d >> "$DEPLOY_LOG" 2>&1
RC=$?
echo "[$(ts)] up rc=$RC" >> "$DEPLOY_LOG"

sudo -n docker compose restart caddy >> "$DEPLOY_LOG" 2>&1 || true
sleep 20
echo "[$(ts)] compose ps:" >> "$DEPLOY_LOG"
sudo -n docker compose ps >> "$DEPLOY_LOG" 2>&1 || true

for url in "http://127.0.0.1:8088/" "http://127.0.0.1:8088/api/_health/" "http://127.0.0.1:8088/api/settings/"; do
  echo "[$(ts)] curl $url" >> "$DEPLOY_LOG"
  curl -fsS -m 20 -o /tmp/r3b2b-curl.out -w 'http=%{http_code}\n' "$url" >> "$DEPLOY_LOG" 2>&1 || echo "curl-failed" >> "$DEPLOY_LOG"
  head -c 400 /tmp/r3b2b-curl.out >> "$DEPLOY_LOG" 2>&1 || true
  echo >> "$DEPLOY_LOG"
done

echo "[$(ts)] resources:" >> "$DEPLOY_LOG"
free -h >> "$DEPLOY_LOG" 2>&1 || true
swapon --show >> "$DEPLOY_LOG" 2>&1 || true
df -h /www / >> "$DEPLOY_LOG" 2>&1 || true
echo "[$(ts)] deploy-watcher done" >> "$DEPLOY_LOG"
