# sometable

sometable.com 的项目仓库。

- 正式站点：https://sometable.com
- 部署与开发记录：[docs/deployment](./docs/deployment/README.md)

## 部署

```bash
cd /www/apps/sometable
sudo docker compose up -d
```

环境变量保存在 `.env`（不入库）。详细说明见
[docs/deployment/部署日志.md](./docs/deployment/部署日志.md)。

## 开发约定

1. 每轮开发前在 `docs/deployment/开发规划.md` 写下规划。
2. 每轮完成后在 `docs/deployment/开发小结.md` 记录结果。
3. 变更验证后推送回 `soulizer/sometable` 的 `develop` 分支。

## 技术栈

基于 Baserow（Django + Vue 3 + PostgreSQL），由 Docker Compose 编排，
Nginx 终止 TLS 并反代到容器内的 Caddy。
