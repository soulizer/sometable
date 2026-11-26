# dms.caransfer.com 部署说明

> 本文件仅针对 `dms.caransfer.com` 这台服务器的实例，不涉及 sometable.com 生产环境。
> 部署日期：2026-11-25（最新源码：`develop` @ `ca8d9b3` + 本地修复，r3b26）

## 访问信息

| 项 | 值 |
| --- | --- |
| 站点 | https://dms.caransfer.com |
| 管理员邮箱 | `admin@dms.caransfer.com` |
| 管理员初始密码 | 见服务器 `/root/.sometable-admin-password`（首次登录后请修改） |
| 源码/部署目录 | `/www/apps/sometable` |
| 镜像标签 | `local-20261126-r3b26` |
| 本地备份目录 | `/www/backups/sometable` |

## 运行架构

```
浏览器 HTTPS 443
  └─ 宝塔 Nginx（dms.caransfer.com.conf，TLS 终止）
       └─ 127.0.0.1:8088 → Docker Compose Caddy
            ├─ backend（Django，迁移/定时备份）
            ├─ web-frontend（Nuxt）
            ├─ celery / celery-beat / celery-export
            ├─ db（pgvector/pgvector:pg15）
            └─ redis:6
```

Caddy 的 8088/8443 只绑定 `127.0.0.1`，不直接暴露公网。

## 对象存储

| 配置项 | 值 |
| --- | --- |
| Endpoint | `https://s3.bitiful.net` |
| Bucket | `caransfer` |
| Region | `cn-east-1` |
| 媒体前缀 | `dms/` |
| 备份前缀 | `backup/` |
| 寻址方式 | path-style |
| 媒体访问 | 7 天有效的预签名 URL（桶不公开读） |

运行时配置保存在 Docker 卷 `sometable_app_config`：

- `/baserow/config/storage.json`：媒体存储
- `/baserow/config/backup-storage.json`：远端备份存储

界面路径：管理员设置 → 文件存储 / 备份 → 远端备份存储。

## 表格快捷键

- `Ctrl/Cmd + F`：打开当前视图搜索
- `Ctrl/Cmd + A`：用复选框选中当前已加载的行
- `Delete / Backspace`：删除复选框选中的行（移入回收站）

## 导出下载

- 对象存储的预签名 URL 不再追加 `dl` 参数，避免签名失效导致 `SignatureDoesNotMatch`。
- 导出进度中的状态文案已翻译为「等待中 / 正在导出… / 已完成」等。

## 表格去重

- 表格（Grid 视图）工具栏提供「去除重复行」。
- 选择 1 个或多个判重字段 → 预览重复分组 → 选择保留规则（最早 / 最新 / 手动指定）→ 二次确认后批量移入回收站。
- 可选删除前自动做一次整库备份；操作复用 Baserow 的行删除 action，支持撤销和审计。
- 单次最多扫描 50000 行、10 个判重字段，预览最多 100 组。

## 管理员用户管理

- 管理员后台「用户」页面右上角提供「新增用户」，可直接设置邮箱、密码、是否管理员和是否启用。
- 用户列表新增「邮箱已验证」列。
- 用户行的右键菜单可直接「标记邮箱为已验证 / 取消邮箱验证」，管理员也可以对自己的账号执行该操作。
- 新增用户默认标记邮箱已验证，不需要外发邮件。

## 备份

- 应用内定时备份：每天 03:00，范围「全部」，保留 7 份。
- 本地目录：`/www/backups/sometable/<时间戳>/`
- 远端归档：`caransfer/backup/<时间戳>.tar.gz`
- 管理员可在「备份」页面立即备份、查看本地/远端列表、恢复到指定时间点。

## 常用命令

```bash
cd /www/apps/sometable

docker compose ps
docker compose logs -f backend
docker compose restart
docker compose exec backend /baserow/backend/docker/docker-entrypoint.sh manage shell
```

## 本实例为适配服务器做的构建调整

- Dockerfile 增加 `GITHUB_PROXY`、腾讯/清华镜像源，避免 GitHub/PyPI 下载超时。
- 后端依赖改为由 `backend/uv-export-prod.txt`（从 uv.lock 导出）经 pip 安装，绕过 uv 在该网络环境下的下载死锁。
- 备份远端前缀由代码内置的 `sometable-backups/` 改为可通过 `BACKUP_REMOTE_PREFIX` 配置，默认空，因此归档直接落在 `backup/` 下。

## 证书

- 证书：`/www/server/panel/vhost/cert/dms.caransfer.com/`
- acme.sh 自动续期（宝塔已有 acme.sh cron），续期后自动 `nginx -s reload`。

## 源码与发布

- GitHub 仓库：`soulizer/sometable`
- 部署分支：`deploy/dms-caransfer`（基于 `develop`）
- 服务器 SSH 别名：`github-sometable`，deploy key 位于 `/root/.ssh/sometable_deploy`
- 后续在本机的修改先提交到该分支再推送；`.env`、Docker 卷和运行数据不进入仓库。
- 回滚镜像：`baserow/backend:local-20261125-r3b23`、`baserow/web-frontend:local-20261125-r3b23`
