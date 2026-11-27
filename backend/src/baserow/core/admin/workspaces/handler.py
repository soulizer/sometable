from baserow.core.admin.workspaces.exceptions import CannotDeleteATemplateGroupError
from baserow.core.exceptions import (
    CannotChangeYourOwnWorkspaceRole,
    CannotDeleteYourselfFromWorkspace,
    IsNotAdminError,
)
from baserow.core.handler import CoreHandler
from baserow.core.job_types import ExportApplicationsJobType
from baserow.core.jobs.handler import JobHandler
from baserow.core.models import WorkspaceUser
from baserow.core.signals import (
    before_workspace_user_deleted,
    workspace_deleted,
    workspace_user_deleted,
)
from baserow.core.trash.handler import TrashHandler


class WorkspacesAdminHandler:
    def rename_workspace(self, user, workspace, name):
        """
        Renames a workspace if the requesting user is staff.

        :raises IsNotAdminError: If the user is not admin or staff.
        """

        if not user.is_staff:
            raise IsNotAdminError()

        workspace.name = name
        workspace.save(update_fields=["name"])
        return workspace

    def delete_workspace(self, user, workspace):
        """
        Deletes an existing workspace and related applications if the user is staff.

        :param user: The user on whose behalf the workspace is deleted
        :type: user: User
        :param workspace: The workspace instance that must be deleted.
        :type: workspace: Workspace
        :raises IsNotAdminError: If the user is not admin or staff.
        """

        if not user.is_staff:
            raise IsNotAdminError()

        if workspace.has_template():
            raise CannotDeleteATemplateGroupError()

        # Load the workspace users before the workspace is deleted so that we can
        # pass those along with the signal.
        workspace_id = workspace.id
        workspace_users = list(workspace.users.all())

        TrashHandler.permanently_delete(workspace)

        workspace_deleted.send(
            self,
            workspace_id=workspace_id,
            workspace=workspace,
            workspace_users=workspace_users,
        )

    def list_workspace_members(self, user, workspace):
        """
        Lists the human members of a workspace if the requesting user is staff.

        :param user: The staff user on whose behalf the members are listed.
        :param workspace: The workspace whose members must be listed.
        :return: A queryset of workspace memberships with their users loaded.
        :raises IsNotAdminError: If the user is not staff.
        """

        if not user.is_staff:
            raise IsNotAdminError()

        return WorkspaceUser.objects.filter(workspace=workspace).select_related("user")

    def update_workspace_member(self, user, workspace_user, permissions):
        """
        Changes the role of a workspace member as a staff user. The workspace role
        validation, the self-change guard and the last admin guard are shared with the
        regular workspace member update flow.

        :param user: The staff user on whose behalf the role is changed.
        :param workspace_user: The membership whose role must be changed.
        :param permissions: The role uid to assign to the member.
        :return: The updated workspace membership.
        :raises IsNotAdminError: If the user is not staff.
        """

        if not user.is_staff:
            raise IsNotAdminError()

        if user.id == workspace_user.user_id:
            raise CannotChangeYourOwnWorkspaceRole(
                "Cannot change your own role in the workspace."
            )

        CoreHandler().raise_if_invalid_workspace_role(
            permissions, workspace_user.workspace
        )
        stored_role = CoreHandler.get_stored_workspace_role_uid(permissions)

        return CoreHandler().force_update_workspace_user(
            user, workspace_user, permissions=stored_role
        )

    def delete_workspace_member(self, user, workspace_user):
        """
        Removes a member from a workspace as a staff user. A staff member does not
        need to belong to the workspace, so the core permission check is replaced by
        the explicit staff check, while the self-delete, last admin and signal
        semantics of `CoreHandler.delete_workspace_user` are preserved.

        :param user: The staff user on whose behalf the member is removed.
        :param workspace_user: The membership that must be deleted.
        :raises IsNotAdminError: If the user is not staff.
        """

        if not user.is_staff:
            raise IsNotAdminError()

        if user.id == workspace_user.user_id:
            raise CannotDeleteYourselfFromWorkspace(
                "Cannot delete yourself from workspace."
            )

        CoreHandler.raise_if_user_is_last_admin_of_workspace(workspace_user)

        before_workspace_user_deleted.send(
            self,
            user=workspace_user.user,
            workspace=workspace_user.workspace,
            workspace_user=workspace_user,
        )

        workspace_user_id = workspace_user.id
        workspace_user.delete()

        workspace_user_deleted.send(
            self,
            workspace_user_id=workspace_user_id,
            workspace_user=workspace_user,
            user=user,
        )

    def export_workspace(
        self, user, workspace, application_ids=None, only_structure=False
    ):
        """
        Starts an asynchronous export of a workspace as a staff user.

        :param user: The staff user on whose behalf the export is started.
        :param workspace: The workspace to export.
        :param application_ids: Optional list of application ids to export.
        :param only_structure: If True the application data is not exported.
        :return: The created export job.
        :raises IsNotAdminError: If the user is not staff.
        """

        if not user.is_staff:
            raise IsNotAdminError()

        return JobHandler().create_and_start_job(
            user,
            ExportApplicationsJobType.type,
            workspace_id=workspace.id,
            application_ids=application_ids,
            only_structure=only_structure,
        )
