#!/usr/bin/env bash
set -uo pipefail
cd /www/apps/sometable
TAG="local-20261121-r3b21"
BUILD_LOG="docs/deployment/build-logs/r3b21-build.log"
DEPLOY_LOG="docs/deployment/build-logs/r3b21-deploy.log"
STALL_LIMIT=600
ts(){ date -Is; }
logb(){ echo "[$(ts)] $*" >> "$BUILD_LOG"; }
logd(){ echo "[$(ts)] $*" >> "$DEPLOY_LOG"; }
mkdir -p docs/deployment/build-logs

logb "r3b21 build start tag=$TAG"
# 前端代码自 r3b17 起未变更，直接复用已构建的镜像，只重建后端。
sudo -n docker tag baserow/web-frontend:local-20261121-r3b20 baserow/web-frontend:"$TAG" >> "$BUILD_LOG" 2>&1
logb "pre: $(free -h | tr '\n' ';') swapon=$(swapon --show --noheadings 2>/dev/null | tr '\n' ';') df=$(df -h /www / | tr '\n' ';')"

# 前置资源门槛（临时 swap 扩至 8G，门槛下调至 1.8G）
avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
if [ "$avail_kb" -lt 1800000 ]; then logb "ABORT: available memory ${avail_kb}kB < 1.8GB"; exit 1; fi

build_guarded() {
  local svc="$1"; shift
  logb "building $svc"
  sudo -n env BASEROW_VERSION="$TAG" NODE_MAX_OLD_SPACE_MB=3072 docker compose -f docker-compose.yml -f docker-compose.build.yml build "$svc" >> "$BUILD_LOG" 2>&1 &
  local pid=$!
  local last_size=-1 stall=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 30
    local size; size=$(wc -c < "$BUILD_LOG")
    if [ "$size" = "$last_size" ]; then stall=$((stall+30)); else stall=0; last_size=$size; fi
    echo "[$(ts)] heartbeat $svc stall=${stall}s avail=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)MB" >> "$BUILD_LOG"
    if [ "$stall" -ge "$STALL_LIMIT" ]; then
      logb "STALL detected for $svc (${stall}s no output) -> kill"
      sudo -n pkill -9 -f "docker compose -f docker-compose.yml -f docker-compose.build.yml build $svc" || true
      kill -9 "$pid" 2>/dev/null || true
      return 97
    fi
  done
  wait "$pid"; return $?
}

logb "web-frontend image reused from r3b17"
RC=0

build_guarded backend; RC=$?
logb "backend build done rc=$RC"
logb "post-build: $(free -h | tr '\n' ';') df=$(df -h /www / | tr '\n' ';')"
[ $RC -ne 0 ] && { logb "build failed, skip deploy"; exit $RC; }

logd "deploy start tag=$TAG"
cp .env ".env.bak-r3b21-$(date +%Y%m%d%H%M%S)"
sed -i "s/^BASEROW_VERSION=.*/BASEROW_VERSION=${TAG}/" .env
sudo -n env BASEROW_VERSION="$TAG" docker compose up -d >> "$DEPLOY_LOG" 2>&1
logd "up rc=$?"
sudo -n docker compose restart caddy >> "$DEPLOY_LOG" 2>&1 || true
# 等待就绪：最多 180s
for i in $(seq 1 18); do
  sleep 10
  code=$(curl -sS -m 8 -H 'Host: sometable.com' -o /dev/null -w '%{http_code}' http://127.0.0.1:8088/api/_health/ 2>/dev/null || echo 000)
  logd "wait ${i}0s health=$code"
  [ "$code" = "200" ] && break
done
sudo -n docker compose ps >> "$DEPLOY_LOG" 2>&1 || true
for path in "/" "/login/" "/api/_health/" "/api/settings/"; do
  logd "curl $path"
  curl -sS -m 20 -H 'Host: sometable.com' -o docs/deployment/build-logs/r3b21-curl.out -w 'http=%{http_code}\n' "http://127.0.0.1:8088$path" >> "$DEPLOY_LOG" 2>&1 || echo "curl-failed" >> "$DEPLOY_LOG"
  echo >> "$DEPLOY_LOG"
done
logd "resources:"; free -h >> "$DEPLOY_LOG" 2>&1; swapon --show >> "$DEPLOY_LOG" 2>&1; df -h /www / >> "$DEPLOY_LOG" 2>&1
logd "deploy done tag=$TAG"
logb "r3b21 chain done"
