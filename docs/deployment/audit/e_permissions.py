# 批次 E：权限矩阵
from django.contrib.auth import get_user_model

from baserow.contrib.database.models import Database, Table
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace

User = get_user_model()
WORKSPACE_NAME = "审计-工作区"
ROLES = ["none", "viewer", "commenter", "editor", "builder", "admin"]
RESULTS = []


def main():
    handler = CoreHandler()
    workspace = Workspace.objects.get(name=WORKSPACE_NAME)
    app = Database.objects.get(name="审计-数据库", workspace=workspace)
    table = Table.objects.filter(
        name="审计-数据表", database=app
    ).first()
    if table is None:
        from baserow.core.trash.handler import TrashHandler

        trashed = Table.objects_and_trash.filter(
            name="审计-数据表", database=app
        ).first()
        TrashHandler.restore_item(
            User.objects.filter(is_staff=True).first(), "table", trashed.id
        )
        table = Table.objects.get(name="审计-数据表", database=app)
    field = table.field_set.get(name="名称")
    view = table.view_set.get(name="审计-grid")
    model = table.get_model()
    row = model.objects.first()

    contexts = {
        "workspace": (workspace, workspace),
        "application": (app, app),
        "table": (table, table),
        "field": (field, table),
        "view": (view, view),
        "row": (row, table),
    }

    # (操作, 上下文, 允许的角色)
    matrix = [
        ("workspace.read", "workspace", ["viewer", "commenter", "editor", "builder", "admin"]),
        ("workspace.update", "workspace", ["admin"]),
        ("workspace.delete", "workspace", ["admin"]),
        ("workspace.create_application", "workspace", ["builder", "admin"]),
        ("workspace.create_invitation", "workspace", ["admin"]),
        ("workspace.list_workspace_users", "workspace", ["editor", "builder", "admin"]),
        ("database.table.read", "table", ["viewer", "commenter", "editor", "builder", "admin"]),
        ("database.table.update", "table", ["builder", "admin"]),
        ("database.table.delete", "table", ["builder", "admin"]),
        ("database.table.create_field", "table", ["builder", "admin"]),
        ("database.table.field.read", "field", ["viewer", "commenter", "editor", "builder", "admin"]),
        ("database.table.field.update", "field", ["builder", "admin"]),
        ("database.table.field.delete", "field", ["builder", "admin"]),
        ("database.table.read_row", "row", ["viewer", "commenter", "editor", "builder", "admin"]),
        ("database.table.create_row", "row", ["editor", "builder", "admin"]),
        ("database.table.update_row", "row", ["editor", "builder", "admin"]),
        ("database.table.delete_row", "row", ["editor", "builder", "admin"]),
        ("database.table.view.read", "view", ["viewer", "commenter", "editor", "builder", "admin"]),
        ("database.table.view.update", "view", ["builder", "admin"]),
        ("database.table.view.delete", "view", ["builder", "admin"]),
        ("database.table.view.list_rows", "view", ["viewer", "commenter", "editor", "builder", "admin"]),
        ("database.table.create_comment", "view", ["commenter", "editor", "builder", "admin"]),
        ("database.table.list_comments", "view", ["commenter", "editor", "builder", "admin"]),
    ]

    users = {role: User.objects.get(email=f"audit-{role}@access126.com") for role in ROLES}

    for operation, context_key, allowed_roles in matrix:
        context, parent = contexts[context_key]
        for role in ROLES:
            user = users[role]
            try:
                allowed = handler.check_permissions(
                    user,
                    operation,
                    workspace=workspace,
                    context=parent,
                    raise_permission_exceptions=False,
                )
            except Exception:
                allowed = False
            expected = role in allowed_roles
            if allowed != expected:
                RESULTS.append(
                    (
                        "FAIL",
                        f"{operation}/{role}",
                        f"实际={allowed} 预期={expected}",
                    )
                )

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    total = len(matrix) * len(ROLES)
    print(f"E_PERMISSIONS_OK total={total} failed={len(RESULTS)}")


main()
