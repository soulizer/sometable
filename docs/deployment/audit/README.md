# 全站功能审计（脚本与结果）

运行方式（容器内已包含源码与依赖）：

```bash
cd /www/apps/sometable
docker cp docs/deployment/audit/setup.py sometable-backend-1:/tmp/audit_setup.py
sudo -n docker compose exec -T backend /baserow/backend/docker/docker-entrypoint.sh \
  manage shell < /tmp/audit_setup.py
```

- `setup.py`：幂等创建审计用户与工作区（命名前缀 `审计-`），角色覆盖 admin/builder/editor/commenter/viewer/无权限。
- 其余脚本按批次添加，命名 `b_*.py`（账号/工作区）、`c_*.py`（数据库/视图）、`d_*.py`（应用/自动化/仪表盘/AI）、`e_*.py`（权限/通知/安全）。
- `f_demo.py` / `f_demo2.py` / `f_demo3.py`：演示数据（销售管理：数据库/视图/仪表盘/自动化；项目管理；更多订单）。
- 邮件测试只发往 `access@126.com`；本地验证使用 `../scripts/smtp_sink.py`（不对外发送）。
- 无头浏览器冒烟：`../scripts/browser_smoke.py`、`../scripts/browser_demo.py`，截图存 `screenshots/`。
- 对象存储备份/恢复：`../scripts/backup-object-storage.py`（由 `backup-sometable.sh` 调用），也可在「管理员设置 → 备份」界面配置与执行。
- 结果记录在本目录 `结果-*.md` 与 `docs/deployment/部署日志.md`。
