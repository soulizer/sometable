#!/usr/bin/env bash
set -uo pipefail
cd /www/apps/sometable
TAG="local-20261120-1738-r3b2"
LOG=docs/deployment/build-logs/r3b2.log
BUILD_PID=${1:-1501575}
DEPLOY_LOG=docs/deployment/build-logs/r3b2-deploy.log
ts(){ date -Is; }

echo "[$(ts)] deploy-watcher start waiting for pid=$BUILD_PID" >> "$DEPLOY_LOG"
# wait for build process
while kill -0 "$BUILD_PID" 2>/dev/null; do
  sleep 20
done
echo "[$(ts)] build pid exited" >> "$DEPLOY_LOG"

# detect success
if grep -q "backend build done rc=0" "$LOG" && grep -q "web-frontend build done rc=0" "$LOG"; then
  echo "[$(ts)] build success detected" >> "$DEPLOY_LOG"
else
  echo "[$(ts)] build FAILED or incomplete; tail:" >> "$DEPLOY_LOG"
  tail -n 60 "$LOG" >> "$DEPLOY_LOG" 2>&1 || true
  exit 1
fi

# backup env and set version
cp .env ".env.bak-r3b2-$(date +%Y%m%d%H%M%S)"
if grep -q '^BASEROW_VERSION=' .env; then
  sed -i "s/^BASEROW_VERSION=.*/BASEROW_VERSION=${TAG}/" .env
else
  echo "BASEROW_VERSION=${TAG}" >> .env
fi
echo "[$(ts)] .env BASEROW_VERSION=$(grep '^BASEROW_VERSION=' .env)" >> "$DEPLOY_LOG"

# rolling update
echo "[$(ts)] docker compose up -d" >> "$DEPLOY_LOG"
sudo -n docker compose up -d >> "$DEPLOY_LOG" 2>&1
RC=$?
echo "[$(ts)] up rc=$RC" >> "$DEPLOY_LOG"

# restart caddy to refresh upstream resolution
sudo -n docker compose restart caddy >> "$DEPLOY_LOG" 2>&1 || true

sleep 15
echo "[$(ts)] compose ps:" >> "$DEPLOY_LOG"
sudo -n docker compose ps >> "$DEPLOY_LOG" 2>&1 || true

# basic checks
for url in "http://127.0.0.1:8088/" "http://127.0.0.1:8088/api/_health/" "http://127.0.0.1:8088/api/settings/"; do
  echo "[$(ts)] curl $url" >> "$DEPLOY_LOG"
  curl -fsS -m 20 -o /tmp/r3b2-curl.out -w 'http=%{http_code}\n' "$url" >> "$DEPLOY_LOG" 2>&1 || echo "curl-failed" >> "$DEPLOY_LOG"
  head -c 300 /tmp/r3b2-curl.out >> "$DEPLOY_LOG" 2>&1 || true
  echo >> "$DEPLOY_LOG"
done

echo "[$(ts)] deploy-watcher done" >> "$DEPLOY_LOG"
