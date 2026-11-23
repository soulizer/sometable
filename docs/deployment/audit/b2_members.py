# 批次 B2：工作区成员、邀请、通知、账号注销
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage

from baserow.core.cache import local_cache
from baserow.core.exceptions import (
    CannotChangeYourOwnWorkspaceRole,
    CannotDeleteYourselfFromWorkspace,
    LastAdminOfWorkspace,
    PermissionDenied,
    WorkspaceUserAlreadyExists,
    WorkspaceUserIsLastAdmin,
)
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace, WorkspaceUser
from baserow.core.notifications.models import NotificationRecipient
from baserow.core.user.actions import (
    CancelUserDeletionActionType,
    ScheduleUserDeletionActionType,
)
from baserow.core.user.handler import UserHandler

User = get_user_model()
PASSWORD = "Audit-Test-2026!"
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


def get_user(role):
    return User.objects.get(email=f"audit-{role}@access126.com")


def main():
    handler = CoreHandler()
    admin = User.objects.filter(is_staff=True).first()
    workspace = Workspace.objects.get(name=WORKSPACE_NAME)

    # --- 成员角色 ---
    check(
        "成员-管理员改名",
        lambda: handler.update_workspace(admin, workspace, name=WORKSPACE_NAME).name
        == WORKSPACE_NAME,
    )
    check(
        "成员-编辑不能邀请",
        lambda: handler.create_workspace_invitation(
            get_user("editor"), workspace, "audit-x@access126.com", "VIEWER"
        ),
        raises=PermissionDenied,
    )
    check(
        "成员-邀请已存在成员被拒",
        lambda: handler.create_workspace_invitation(
            admin, workspace, "audit-viewer@access126.com", "VIEWER"
        ),
        raises=WorkspaceUserAlreadyExists,
    )

    # --- 邀请与通知（拦截邮件）---
    WorkspaceUser.objects.filter(
        workspace=workspace, user__email="audit-invitee@access126.com"
    ).delete()
    try:
        invitee = User.objects.get(email="audit-invitee@access126.com")
    except User.DoesNotExist:
        invitee = UserHandler().force_create_user(
            email="audit-invitee@access126.com",
            name="审计-受邀",
            password=PASSWORD,
            language="zh-hans",
        )
    sent = []
    original_send = EmailMessage.send
    EmailMessage.send = lambda self, *a, **k: sent.append(self)
    try:
        invitation = handler.create_workspace_invitation(
            admin, workspace, invitee.email, "COMMENTER"
        )
    finally:
        EmailMessage.send = original_send
        local_cache.clear()
    check("邀请-创建成功", lambda: invitation.id is not None)
    check("邀请-发送邮件", lambda: len(sent) == 1)
    check(
        "邀请-生成通知",
        lambda: NotificationRecipient.objects.filter(
            recipient=invitee,
            notification__type="workspace_invitation_created",
        ).exists(),
    )
    check(
        "邀请-接受后加入",
        lambda: handler.accept_workspace_invitation(invitee, invitation).permissions
        == "COMMENTER",
    )

    # --- 角色保护 ---
    admin_membership = workspace.workspaceuser_set.get(user=admin)
    check(
        "成员-不能修改自己的角色",
        lambda: handler.update_workspace_user(
            admin, admin_membership, permissions="VIEWER"
        ),
        raises=CannotChangeYourOwnWorkspaceRole,
    )

    # 新建单管理员工作区验证最后管理员保护
    editor = get_user("editor")
    fresh = handler.create_workspace(user=editor, name="审计-单管理员工作区").workspace
    fresh_admin = fresh.workspaceuser_set.get(user=editor)
    check(
        "成员-唯一管理员不能降级自己",
        lambda: handler.update_workspace_user(
            editor, fresh_admin, permissions="VIEWER"
        ),
        raises=(WorkspaceUserIsLastAdmin, CannotChangeYourOwnWorkspaceRole),
    )
    check(
        "成员-唯一管理员不能删除自己",
        lambda: handler.delete_workspace_user(editor, fresh_admin),
        raises=(LastAdminOfWorkspace, CannotDeleteYourselfFromWorkspace),
    )

    # --- 账号注销 ---
    target = User.objects.get(email="audit-invitee@access126.com")
    check(
        "账号-预约注销",
        lambda: ScheduleUserDeletionActionType.do(target) is not None,
    )
    check(
        "账号-取消注销",
        lambda: CancelUserDeletionActionType.do(target) is not None,
    )

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"B2_MEMBERS_OK total={len(RESULTS)} failed={len(failed)}")


main()
