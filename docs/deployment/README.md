# sometable 部署与开发记录

本目录用于记录 sometable.com 项目的部署过程、每一轮开发规划与开发小结，避免因对话丢失而中断进度。

## 文档索引

| 文档 | 内容 |
| --- | --- |
| [部署日志](./部署日志.md) | 服务器环境、部署步骤、当前状态、变更历史 |
| [开发规划](./开发规划.md) | 后续每一轮的开发计划 |
| [开发小结](./开发小结.md) | 每一轮开发完成后的总结 |

## 项目基本信息

| 项 | 值 |
| --- | --- |
| 源码仓库 | `git@github.com:soulizer/sometable.git`（分支 `develop`） |
| 部署目录 | `/www/apps/sometable` |
| 运行方式 | Docker Compose（Baserow 官方镜像） |
| 正式域名 | `https://sometable.com` |
| 跳转域名 | `www.sometable.com`、`sometables.com`、`www.sometables.com` → `https://sometable.com` |
| 反向代理 | 宝塔面板 Nginx（TLS 终止）→ `127.0.0.1:8088`（容器内 Caddy） |
| 对象存储 | 缤纷云 S4（S3 协议），桶 `drive`，前缀 `sometable/` |

## 重要约定

1. 本项目的所有变更，完成验证后第一时间推送回 `soulizer/sometable` 的 `develop` 分支。
2. 每一轮开发规划写入 `docs/deployment/开发规划.md`，完成后的小结写入 `docs/deployment/开发小结.md`。
3. 文档默认使用中文。
4. 生产环境变量保存在 `/www/apps/sometable/.env`（已被 git 忽略，切勿提交）。
