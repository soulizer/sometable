#!/usr/bin/env bash
set -uo pipefail
cd /www/apps/sometable

TAG="local-20261120-r3b3"
BUILD_LOG="docs/deployment/build-logs/r3b3-build.log"
DEPLOY_LOG="docs/deployment/build-logs/r3b3-deploy.log"
ts(){ date -Is; }
logb(){ echo "[$(ts)] $*" >> "$BUILD_LOG"; }
logd(){ echo "[$(ts)] $*" >> "$DEPLOY_LOG"; }

mkdir -p docs/deployment/build-logs
logb "r3b3 build+deploy start tag=$TAG"
logb "pre: $(free -h | tr '\n' ';') swapon=$(swapon --show --noheadings 2>/dev/null | tr '\n' ';') df=$(df -h /www / | tr '\n' ';')"

logb "building web-frontend"
sudo -n env BASEROW_VERSION="$TAG" NODE_MAX_OLD_SPACE_MB=4096 docker compose -f docker-compose.yml -f docker-compose.build.yml build web-frontend >> "$BUILD_LOG" 2>&1
RC=$?
logb "web-frontend build done rc=$RC"
if [ $RC -ne 0 ]; then logb "aborting after web-frontend failure"; exit $RC; fi

logb "building backend"
sudo -n env BASEROW_VERSION="$TAG" docker compose -f docker-compose.yml -f docker-compose.build.yml build backend >> "$BUILD_LOG" 2>&1
RC=$?
logb "backend build done rc=$RC"
logb "post-build: $(free -h | tr '\n' ';') df=$(df -h /www / | tr '\n' ';')"
if [ $RC -ne 0 ]; then logb "build failed, skip deploy"; exit $RC; fi

logd "deploy start tag=$TAG"
cp .env ".env.bak-r3b3-$(date +%Y%m%d%H%M%S)"
if grep -q '^BASEROW_VERSION=' .env; then
  sed -i "s/^BASEROW_VERSION=.*/BASEROW_VERSION=${TAG}/" .env
else
  echo "BASEROW_VERSION=${TAG}" >> .env
fi
logd ".env BASEROW_VERSION=$(grep '^BASEROW_VERSION=' .env)"

logd "docker compose up -d"
sudo -n env BASEROW_VERSION="$TAG" docker compose up -d >> "$DEPLOY_LOG" 2>&1
RC=$?
logd "up rc=$RC"
if [ $RC -ne 0 ]; then logd "compose up failed"; fi

sudo -n docker compose restart caddy >> "$DEPLOY_LOG" 2>&1 || true
sleep 25
logd "compose ps:"
sudo -n docker compose ps >> "$DEPLOY_LOG" 2>&1 || true

for path in "/" "/login/" "/api/_health/" "/api/settings/"; do
  url="http://127.0.0.1:8088${path}"
  logd "curl Host:sometable.com $url"
  curl -sS -m 20 -H 'Host: sometable.com' -o /tmp/r3b3-curl.out -w 'http=%{http_code}\n' "$url" >> "$DEPLOY_LOG" 2>&1 || echo "curl-failed" >> "$DEPLOY_LOG"
  head -c 300 /tmp/r3b3-curl.out >> "$DEPLOY_LOG" 2>&1 || true
  echo >> "$DEPLOY_LOG"
done

logd "resources:"
free -h >> "$DEPLOY_LOG" 2>&1 || true
swapon --show >> "$DEPLOY_LOG" 2>&1 || true
df -h /www / >> "$DEPLOY_LOG" 2>&1 || true
logd "deploy done tag=$TAG"
logb "r3b3 chain done"
