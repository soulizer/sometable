# sometable 部署与开发记录

本目录用于记录 sometable.com 项目的部署过程、每一轮开发规划与开发小结，避免因对话丢失而中断进度。

## 文档索引

| 文档 | 内容 |
| --- | --- |
| **[第3轮交接文档](./第3轮交接文档.md)** | **★ AI 接手必读：现状、待办、规则、踩坑、构建部署规程** |
| [第3轮进度与计划](./第3轮进度与计划.md) | 第 3 轮滚动进度、已完成/待办、子批次日志 |
| [部署日志](./部署日志.md) | 服务器环境、部署步骤、当前状态、变更历史（含资源事故） |
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
   `.env.bak*` 备份文件**未被** gitignore，提交时务必排除：`git add -A -- . ":(exclude).env.bak*"`。
5. **所有临时/长期文档一律写入 `docs/` 目录**，不要写到 /tmp 或会话缓存。
6. 每个代码变更批次：提交 → 推送 GitHub → 构建部署上线 → 在 `部署日志.md` 记录（用户不看代码，只看线上）。
