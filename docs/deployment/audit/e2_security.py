# 批次 E2：数据隔离、共享权限、审计日志、通知、行评论、数据扫描
from django.contrib.auth import get_user_model

from baserow.contrib.database.models import Database, Table
from baserow.core.exceptions import PermissionDenied
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace
from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.models import NotificationRecipient
from baserow_enterprise.audit_log.models import AuditLogEntry
from baserow_enterprise.data_scanner.models import DataScan

User = get_user_model()
WORKSPACE_NAME = "审计-工作区"
RESULTS = []


def check(name, fn, raises=None, predicate=None):
    try:
        value = fn()
    except Exception as e:  # noqa: BLE001
        if raises is not None and isinstance(e, raises):
            RESULTS.append(("PASS", name, f"预期异常 {type(e).__name__}"))
        else:
            RESULTS.append(("FAIL", name, f"异常 {type(e).__name__}: {e}"))
        return
    if raises is not None:
        RESULTS.append(("FAIL", name, f"预期 {raises.__name__} 但未抛出"))
    elif predicate is not None and not predicate(value):
        RESULTS.append(("FAIL", name, "断言不成立"))
    else:
        RESULTS.append(("PASS", name, ""))


def main():
    handler = CoreHandler()
    workspace = Workspace.objects.get(name=WORKSPACE_NAME)
    app = Database.objects.get(name="审计-数据库", workspace=workspace)
    table = Table.objects.filter(name="审计-数据表", database=app).first()
    if table is None:
        from baserow.core.trash.handler import TrashHandler

        trashed = Table.objects_and_trash.filter(
            name="审计-数据表", database=app
        ).first()
        TrashHandler.restore_item(
            User.objects.filter(is_staff=True).first(), "table", trashed.id
        )
        table = Table.objects.get(name="审计-数据表", database=app)
    grid = table.view_set.get(name="审计-grid")
    row = table.get_model().objects.first()

    outsider = User.objects.get(email="audit-signup@access126.com")
    check(
        "隔离-外部工作区用户读取表被拒",
        lambda: handler.check_permissions(
            outsider,
            "database.table.read",
            workspace=workspace,
            context=table,
            raise_permission_exceptions=False,
        )
        is False,
    )
    check(
        "隔离-外部工作区用户读取行被拒",
        lambda: handler.check_permissions(
            outsider,
            "database.table.read_row",
            workspace=workspace,
            context=table,
            raise_permission_exceptions=False,
        )
        is False,
    )

    # 共享权限
    check(
        "共享-编辑不能公开视图",
        lambda: handler.check_permissions(
            User.objects.get(email="audit-editor@access126.com"),
            "database.table.view.update_public",
            workspace=workspace,
            context=grid,
            raise_permission_exceptions=False,
        )
        is False,
    )
    check(
        "共享-构建者可公开视图",
        lambda: handler.check_permissions(
            User.objects.get(email="audit-builder@access126.com"),
            "database.table.view.update_public",
            workspace=workspace,
            context=grid,
            raise_permission_exceptions=False,
        )
        is True,
    )

    # 审计日志
    check(
        "审计-存在工作区操作记录",
        lambda: AuditLogEntry.objects.filter(workspace_id=workspace.id).count() > 0,
    )
    check(
        "审计-编辑不能查看",
        lambda: handler.check_permissions(
            User.objects.get(email="audit-editor@access126.com"),
            "workspace.list_audit_log_entries",
            workspace=workspace,
            context=workspace,
            raise_permission_exceptions=False,
        )
        is False,
    )
    check(
        "审计-管理员可查看",
        lambda: handler.check_permissions(
            User.objects.get(email="audit-admin@access126.com"),
            "workspace.list_audit_log_entries",
            workspace=workspace,
            context=workspace,
            raise_permission_exceptions=False,
        )
        is True,
    )

    # 通知
    invitee = User.objects.get(email="audit-invitee@access126.com")
    admin = User.objects.filter(is_staff=True).first()
    recipients = NotificationHandler.create_direct_notification_for_users(
        notification_type="workspace_invitation_created",
        recipients=[invitee],
        sender=admin,
        data={
            "invitation_id": 0,
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
        },
        workspace=workspace,
    )
    check("通知-创建直连通知", lambda: len(recipients) == 1)
    n = recipients[0].notification
    check(
        "通知-未读数大于0",
        lambda: NotificationHandler.get_unread_notifications_count(invitee) >= 1,
    )
    NotificationHandler.mark_notification_as_read(invitee, n)
    check(
        "通知-标记已读",
        lambda: not NotificationRecipient.objects.filter(
            recipient=invitee, notification=n, read=False
        ).exists(),
    )

    # 行评论
    from baserow_premium.row_comments.handler import RowCommentHandler

    commenter = User.objects.get(email="audit-commenter@access126.com")
    viewer = User.objects.get(email="audit-viewer@access126.com")
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "审计评论"}],
            }
        ],
    }
    comment = RowCommentHandler.create_comment(commenter, table.id, row.id, doc)
    check("行评论-评论者可创建", lambda: comment.id is not None)
    check(
        "行评论-评论者可读取",
        lambda: RowCommentHandler.get_comments(commenter, table.id, row.id).count()
        >= 1,
    )
    check(
        "行评论-查看者不能读取",
        lambda: RowCommentHandler.get_comments(viewer, table.id, row.id),
        raises=PermissionDenied,
    )
    check(
        "行评论-查看者不能创建",
        lambda: RowCommentHandler.create_comment(viewer, table.id, row.id, doc),
        raises=PermissionDenied,
    )

    # 数据扫描
    check("扫描-模型可用", lambda: DataScan.objects.count() >= 0)
    check(
        "扫描-仅员工可访问管理页",
        lambda: (
            User.objects.get(email="audit-admin@access126.com").is_staff
            and not User.objects.get(email="audit-editor@access126.com").is_staff
        ),
    )

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"E2_SECURITY_OK total={len(RESULTS)} failed={len(failed)}")


main()
