from django.urls import re_path

from baserow.api.admin.workspaces.views import (
    WorkspaceAdminView,
    WorkspaceExportAdminView,
    WorkspaceMemberAdminView,
    WorkspaceMembersAdminView,
    WorkspaceOptionsAdminView,
    WorkspacesAdminView,
)

app_name = "baserow.api.admin.workspaces"

urlpatterns = [
    re_path(r"^$", WorkspacesAdminView.as_view(), name="list"),
    re_path(r"^options/$", WorkspaceOptionsAdminView.as_view(), name="options"),
    re_path(
        r"^(?P<workspace_id>[0-9]+)/members/$",
        WorkspaceMembersAdminView.as_view(),
        name="members",
    ),
    re_path(
        r"^(?P<workspace_id>[0-9]+)/members/(?P<member_id>[0-9]+)/$",
        WorkspaceMemberAdminView.as_view(),
        name="edit-member",
    ),
    re_path(
        r"^(?P<workspace_id>[0-9]+)/export/async/$",
        WorkspaceExportAdminView.as_view(),
        name="export-async",
    ),
    re_path(r"^(?P<workspace_id>[0-9]+)/$", WorkspaceAdminView.as_view(), name="edit"),
]
