#!/usr/bin/env bash
set -uo pipefail
cd /www/apps/sometable
TAG="local-20261121-r3b11"
BUILD_LOG="docs/deployment/build-logs/r3b11-build.log"
DEPLOY_LOG="docs/deployment/build-logs/r3b11-deploy.log"
STALL_LIMIT=600
ts(){ date -Is; }
logb(){ echo "[$(ts)] $*" >> "$BUILD_LOG"; }
logd(){ echo "[$(ts)] $*" >> "$DEPLOY_LOG"; }
mkdir -p docs/deployment/build-logs

logb "r3b11 backend-only build start tag=$TAG"
logb "pre: $(free -h | tr '\n' ';') df=$(df -h /www / | tr '\n' ';')"

avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
if [ "$avail_kb" -lt 1500000 ]; then logb "ABORT: available memory ${avail_kb}kB < 1.5GB"; exit 1; fi

logb "building backend"
sudo -n env BASEROW_VERSION="$TAG" NODE_MAX_OLD_SPACE_MB=3072 docker compose -f docker-compose.yml -f docker-compose.build.yml build backend >> "$BUILD_LOG" 2>&1 &
pid=$!
last_size=-1; stall=0
while kill -0 "$pid" 2>/dev/null; do
  sleep 30
  size=$(wc -c < "$BUILD_LOG")
  if [ "$size" = "$last_size" ]; then stall=$((stall+30)); else stall=0; last_size=$size; fi
  echo "[$(ts)] heartbeat backend stall=${stall}s avail=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)MB" >> "$BUILD_LOG"
  if [ "$stall" -ge "$STALL_LIMIT" ]; then
    logb "STALL detected (${stall}s) -> kill"
    kill -9 "$pid" 2>/dev/null || true
    exit 97
  fi
done
wait "$pid"; RC=$?
logb "backend build done rc=$RC"
[ $RC -ne 0 ] && { logb "abort"; exit $RC; }

# The frontend is unchanged in this batch: re-tag the r3b10 image so both
# services can share the new version tag.
if sudo -n docker image tag baserow/web-frontend:local-20261121-r3b10 "baserow/web-frontend:${TAG}"; then
  logb "frontend image re-tagged as $TAG"
else
  logb "ERROR: could not re-tag frontend image"
  exit 1
fi

logd "deploy start tag=$TAG"
cp .env ".env.bak-r3b11-$(date +%Y%m%d%H%M%S)"
sed -i "s/^BASEROW_VERSION=.*/BASEROW_VERSION=${TAG}/" .env
sudo -n env BASEROW_VERSION="$TAG" docker compose up -d >> "$DEPLOY_LOG" 2>&1
logd "up rc=$?"
sudo -n docker compose restart caddy >> "$DEPLOY_LOG" 2>&1 || true
for i in $(seq 1 18); do
  sleep 10
  code=$(curl -sS -m 8 -H 'Host: sometable.com' -o /dev/null -w '%{http_code}' http://127.0.0.1:8088/api/_health/ 2>/dev/null || echo 000)
  logd "wait ${i}0s health=$code"
  [ "$code" = "200" ] && break
done
sudo -n docker compose ps >> "$DEPLOY_LOG" 2>&1 || true
for path in "/" "/login/" "/api/_health/" "/api/settings/"; do
  curl -sS -m 20 -H 'Host: sometable.com' -o /dev/null -w "$path http=%{http_code}\n" "http://127.0.0.1:8088$path" >> "$DEPLOY_LOG" 2>&1 || echo "curl-failed" >> "$DEPLOY_LOG"
done
logd "deploy done tag=$TAG"
logb "r3b11 chain done"
