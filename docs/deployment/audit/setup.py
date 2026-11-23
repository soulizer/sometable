# 审计测试数据初始化（幂等）
# 通过 `manage shell` 在生产库运行；仅在不存在时创建，重复执行安全。
from django.contrib.auth import get_user_model

from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace

User = get_user_model()
PASSWORD = "Audit-Test-2026!"
WORKSPACE_NAME = "审计-工作区"

ROLES = {
    "admin": "ADMIN",
    "builder": "BUILDER",
    "editor": "EDITOR",
    "commenter": "COMMENTER",
    "viewer": "VIEWER",
    "none": "NO_ACCESS",
}


def get_or_create_user(email, name, is_staff=False):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        from baserow.core.user.handler import UserHandler

        user = UserHandler().force_create_user(
            email=email,
            name=name,
            password=PASSWORD,
            is_staff=is_staff,
            language="zh-hans",
        )
        user.profile.email_verified = True
        user.profile.save(update_fields=["email_verified"])
        print("created user", email)
        return user


def main():
    instance_admin = User.objects.filter(is_staff=True).first()
    assert instance_admin is not None, "no staff user found"

    users = {
        role: get_or_create_user(f"audit-{role}@access126.com", f"审计-{role}")
        for role in ROLES
    }

    try:
        workspace = Workspace.objects.get(name=WORKSPACE_NAME)
        print("workspace exists", workspace.id)
    except Workspace.DoesNotExist:
        workspace_user = CoreHandler().create_workspace(
            user=instance_admin, name=WORKSPACE_NAME
        )
        workspace = workspace_user.workspace
        print("created workspace", workspace.id)

    handler = CoreHandler()
    members = [instance_admin] + list(users.values())
    for user in members:
        role = "ADMIN" if user == instance_admin else ROLES[user.email.split("-")[1].split("@")[0]]
        workspace_user = handler.add_user_to_workspace(workspace, user, role)
        workspace_user.permissions = role
        workspace_user.save(update_fields=["permissions"])
        print("member", user.email, role)

    print("SETUP_OK", workspace.id)


main()
