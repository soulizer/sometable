# 批次 B：账号与工作区功能审计
# 依赖 setup.py 已创建的审计用户/工作区。
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import EmailMessage

from baserow.core.exceptions import (
    PermissionDenied,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from baserow.core.cache import local_cache
from baserow.core.handler import CoreHandler
from baserow.core.models import Settings, Workspace
from baserow.core.operations import (
    CreateWorkspaceOperationType,
    DeleteWorkspaceOperationType,
    ReadWorkspaceOperationType,
    UpdateWorkspaceOperationType,
)
from baserow.core.trash.handler import TrashHandler
from baserow.core.user.exceptions import (
    DisabledSignupError,
    PasswordDoesNotMatchValidation,
    UserAlreadyExist,
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
            RESULTS.append(
                ("FAIL", name, f"异常 {type(e).__name__}: {e}")
            )
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
    settings = Settings.objects.get()
    admin = User.objects.filter(is_staff=True).first()
    viewer = get_user("viewer")

    # --- 注册 ---
    old_signups = settings.allow_new_signups
    settings.allow_new_signups = True
    settings.save(update_fields=["allow_new_signups"])
    local_cache.clear()
    email = "audit-signup@access126.com"
    User.objects.filter(email=email).delete()
    check(
        "注册-允许时成功",
        lambda: UserHandler().create_user(
            name="审计注册", email=email, password=PASSWORD, email_verified=True
        ),
    )
    check(
        "注册-重复邮箱拒绝",
        lambda: UserHandler().create_user(
            name="审计注册2", email=email, password=PASSWORD, email_verified=True
        ),
        raises=UserAlreadyExist,
    )
    check(
        "注册-弱密码拒绝",
        lambda: UserHandler().create_user(
            name="审计弱密码", email="audit-weak@access126.com", password="123"
        ),
        raises=PasswordDoesNotMatchValidation,
    )
    settings.allow_new_signups = False
    settings.save(update_fields=["allow_new_signups"])
    local_cache.clear()
    check(
        "注册-关闭注册后拒绝",
        lambda: UserHandler().create_user(
            name="审计关闭注册",
            email="audit-closed@access126.com",
            password=PASSWORD,
        ),
        raises=DisabledSignupError,
    )
    settings.allow_new_signups = old_signups
    settings.save(update_fields=["allow_new_signups"])
    local_cache.clear()

    # --- 登录 ---
    check(
        "登录-正确密码",
        lambda: authenticate(username="audit-viewer@access126.com", password=PASSWORD)
        is not None,
    )
    check(
        "登录-错误密码",
        lambda: authenticate(username="audit-viewer@access126.com", password="wrong")
        is None,
    )

    # --- 找回密码（拦截邮件，不真实发送）---
    sent = []
    original_send = EmailMessage.send
    EmailMessage.send = lambda self, *a, **k: sent.append(self)
    try:
        check(
            "找回密码-发送重置邮件",
            lambda: UserHandler().send_reset_password_email(viewer) is True,
        )
    finally:
        EmailMessage.send = original_send
    token = None
    if sent:
        body = sent[0].body
        marker = "reset-password/"
        token = body.split(marker, 1)[1].split()[0].strip()
    check("找回密码-邮件包含令牌", lambda: bool(token))
    if token:
        check(
            "找回密码-令牌可重置",
            lambda: UserHandler().reset_password(token, "Audit-New-2026!") is not None,
        )
        check(
            "找回密码-新密码可登录",
            lambda: authenticate(
                username="audit-viewer@access126.com", password="Audit-New-2026!"
            )
            is not None,
        )

    # --- 工作区 ---
    try:
        workspace = Workspace.objects.get(name=WORKSPACE_NAME)
    except Workspace.DoesNotExist:
        workspace = handler.create_workspace(user=admin, name=WORKSPACE_NAME).workspace

    check(
        "工作区-管理员读取",
        lambda: handler.get_workspace(workspace.id) is not None,
    )
    outsider = User.objects.get(email="audit-signup@access126.com")
    check(
        "工作区-非成员读取拒绝",
        lambda: handler.check_permissions(
            outsider,
            ReadWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        ),
        raises=(PermissionDenied, UserNotInWorkspace),
    )
    check(
        "工作区-非管理员更新拒绝",
        lambda: handler.update_workspace(
            viewer, workspace, name="审计-越权改名"
        ),
        raises=PermissionDenied,
    )
    check(
        "工作区-管理员改名",
        lambda: handler.update_workspace(admin, workspace, name=WORKSPACE_NAME).name
        == WORKSPACE_NAME,
    )
    check(
        "工作区-删除入回收站",
        lambda: handler.delete_workspace(admin, workspace) is None,
    )
    check(
        "工作区-回收站中不可读",
        lambda: handler.get_workspace(workspace.id),
        raises=WorkspaceDoesNotExist,
    )
    check(
        "工作区-从回收站恢复",
        lambda: TrashHandler.restore_item(admin, "workspace", workspace.id) is None,
    )
    check(
        "工作区-恢复后可读",
        lambda: handler.get_workspace(workspace.id) is not None,
    )

    # --- 权限操作类型 ---
    check(
        "权限-读取动作对成员通过",
        lambda: handler.check_permissions(
            get_user("editor"),
            ReadWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )
        is None,
    )
    check(
        "权限-删除动作对编辑拒绝",
        lambda: handler.check_permissions(
            get_user("editor"),
            DeleteWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        ),
        raises=PermissionDenied,
    )
    check(
        "权限-更新动作对构建者拒绝",
        lambda: handler.check_permissions(
            get_user("builder"),
            UpdateWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        ),
        raises=PermissionDenied,
    )

    # --- 全局建工作区开关 ---
    old_global = settings.allow_global_workspace_creation
    settings.allow_global_workspace_creation = False
    settings.save(update_fields=["allow_global_workspace_creation"])
    local_cache.clear()
    check(
        "工作区-关闭全局创建后非员工被拒",
        lambda: handler.create_workspace(user=get_user("editor"), name="审计-越权工作区"),
        raises=PermissionDenied,
    )
    settings.allow_global_workspace_creation = old_global
    settings.save(update_fields=["allow_global_workspace_creation"])
    local_cache.clear()
    check(
        "工作区-开启全局创建后非员工可建",
        lambda: handler.create_workspace(
            user=get_user("editor"), name="审计-自建工作区"
        ).workspace.name
        == "审计-自建工作区",
    )

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"B_ACCOUNTS_OK total={len(RESULTS)} failed={len(failed)}")


main()
