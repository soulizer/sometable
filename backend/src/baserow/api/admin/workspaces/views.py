from django.db import transaction
from django.db.models import Count

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.admin.views import AdminListingView, APIListingView
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST
from baserow.api.jobs.errors import ERROR_MAX_JOB_COUNT_EXCEEDED
from baserow.api.jobs.serializers import JobSerializer
from baserow.api.pagination import PageNumberPaginationWithApproximateCount
from baserow.api.schemas import get_error_schema
from baserow.api.workspaces.errors import (
    ERROR_GROUP_USER_IS_LAST_ADMIN,
    ERROR_INVALID_WORKSPACE_ROLE,
)
from baserow.api.workspaces.users.errors import (
    ERROR_CANNOT_CHANGE_YOUR_OWN_ROLE,
    ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP,
    ERROR_GROUP_USER_DOES_NOT_EXIST,
)
from baserow.core.admin.workspaces.exceptions import CannotDeleteATemplateGroupError
from baserow.core.admin.workspaces.handler import WorkspacesAdminHandler
from baserow.core.exceptions import (
    CannotChangeYourOwnWorkspaceRole,
    CannotDeleteYourselfFromWorkspace,
    InvalidWorkspaceRole,
    LastAdminOfWorkspace,
    WorkspaceDoesNotExist,
    WorkspaceUserDoesNotExist,
)
from baserow.core.handler import CoreHandler
from baserow.core.job_types import ExportApplicationsJobType
from baserow.core.jobs.exceptions import MaxJobCountExceeded
from baserow.core.jobs.registries import job_type_registry
from baserow.core.models import Workspace, WorkspaceUser
from baserow.core.usage.handler import UsageHandler

from .errors import ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP
from .serializers import (
    AdminWorkspaceMemberSerializer,
    AdminWorkspaceMemberUpdateSerializer,
    AdminWorkspaceOptionsSerializer,
    AdminWorkspaceUpdateSerializer,
    WorkspacesAdminResponseSerializer,
)

WORKSPACE_ID_PARAMETER = OpenApiParameter(
    name="workspace_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="The id of the workspace",
)
MEMBER_ID_PARAMETER = OpenApiParameter(
    name="member_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="The id of the workspace member",
)


def get_workspace_member_for_admin(workspace, member_id):
    """Returns a human workspace member belonging to the given workspace."""

    return CoreHandler().get_workspace_user(
        member_id, base_queryset=WorkspaceUser.objects.filter(workspace=workspace)
    )


class WorkspacesAdminView(AdminListingView):
    serializer_class = WorkspacesAdminResponseSerializer
    pagination_class = PageNumberPaginationWithApproximateCount
    search_fields = ["id", "name"]
    sort_field_mapping = {
        "id": "id",
        "name": "name",
        "application_count": "application_count",
        "created_on": "created_on",
        "row_count": "row_count",
        "storage_usage": "storage_usage",
    }

    def get_queryset(self, request):
        return (
            Workspace.objects.prefetch_related(
                "workspaceuser_set", "workspaceuser_set__user"
            )
            .annotate(
                application_count=Count("application"),
                template_count=Count("template"),
                **{
                    WorkspacesAdminResponseSerializer.ROW_COUNT_ANNOTATION_NAME: UsageHandler.get_workspace_row_count_annotation()
                },
            )
            .exclude(template_count__gt=0)
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_list_workspaces",
        description="Returns all workspaces with detailed information on each workspace, "
        "if the requesting user is staff.",
        **AdminListingView.get_extend_schema_parameters(
            "workspaces", serializer_class, search_fields, sort_field_mapping
        ),
    )
    def get(self, request):
        return super().get(request)


class WorkspaceOptionsAdminView(APIListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AdminWorkspaceOptionsSerializer
    pagination_class = PageNumberPaginationWithApproximateCount
    search_fields = ["id", "name"]
    default_order_by = "name"

    def get_queryset(self, request):
        # Checking the join column lets PostgreSQL recognize an anti join and
        # estimate the workspace count without the selective NULL-id filter.
        return Workspace.objects.filter(template__workspace_id__isnull=True)

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_list_workspaces_as_options",
        description=(
            "Lists all workspaces. This endpoint is intended for admin-level "
            "features that need a workspace dropdown."
        ),
        **APIListingView.get_extend_schema_parameters(
            "workspaces", serializer_class, search_fields, {}
        ),
    )
    def get(self, request):
        return super().get(request)


class WorkspaceAdminView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_update_workspace",
        request=AdminWorkspaceUpdateSerializer,
        description="Renames the specified workspace if the requesting user is staff.",
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the workspace to update",
            ),
        ],
        responses={
            200: AdminWorkspaceOptionsSerializer(),
            400: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
            401: None,
        },
    )
    @validate_body(AdminWorkspaceUpdateSerializer)
    @map_exceptions({WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST})
    @transaction.atomic
    def patch(self, request, workspace_id, data):
        """Renames the specified workspace."""

        workspace = CoreHandler().get_workspace(workspace_id)
        workspace = WorkspacesAdminHandler().rename_workspace(
            request.user, workspace, data["name"]
        )
        return Response({"id": workspace.id, "name": workspace.name})

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_delete_workspace",
        description="Deletes the specified workspace and the applications inside that "
        "workspace, if the requesting user is staff.",
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the workspace to delete",
            ),
        ],
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_GROUP_DOES_NOT_EXIST", "ERROR_FEATURE_NOT_AVAILABLE"]
            ),
            401: None,
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            CannotDeleteATemplateGroupError: ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP,
        }
    )
    @transaction.atomic
    def delete(self, request, workspace_id):
        """Deletes the specified workspace"""

        workspace = CoreHandler().get_workspace(
            workspace_id,
            base_queryset=Workspace.objects.select_for_update(of=("self",)),
        )
        handler = WorkspacesAdminHandler()
        handler.delete_workspace(request.user, workspace)

        return Response(status=204)


class WorkspaceMembersAdminView(APIListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AdminWorkspaceMemberSerializer
    pagination_class = PageNumberPaginationWithApproximateCount
    search_fields = ["user__email", "user__username"]
    sort_field_mapping = {
        "email": "user__email",
        "permissions": "permissions",
        "created_on": "created_on",
    }
    default_order_by = "user__email"

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_list_workspace_members",
        description="Lists the members of the specified workspace if the requesting "
        "user is staff.",
        **APIListingView.get_extend_schema_parameters(
            "workspace members",
            serializer_class,
            search_fields,
            sort_field_mapping,
            extra_parameters=[WORKSPACE_ID_PARAMETER],
            extra_responses={
                404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
            },
        ),
    )
    @map_exceptions({WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST})
    def get(self, request, workspace_id):
        return super().get(request)

    def get_queryset(self, request):
        workspace = CoreHandler().get_workspace(self.kwargs["workspace_id"])
        return WorkspacesAdminHandler().list_workspace_members(request.user, workspace)


class WorkspaceMemberAdminView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_update_workspace_member",
        request=AdminWorkspaceMemberUpdateSerializer,
        description="Changes the role of a workspace member if the requesting user is "
        "staff.",
        parameters=[WORKSPACE_ID_PARAMETER, MEMBER_ID_PARAMETER],
        responses={
            200: AdminWorkspaceMemberSerializer,
            400: get_error_schema(
                [
                    "ERROR_CANNOT_CHANGE_YOUR_OWN_ROLE",
                    "ERROR_INVALID_WORKSPACE_ROLE",
                    "ERROR_GROUP_USER_IS_LAST_ADMIN",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_USER_DOES_NOT_EXIST"]),
        },
    )
    @validate_body(AdminWorkspaceMemberUpdateSerializer)
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            WorkspaceUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            CannotChangeYourOwnWorkspaceRole: ERROR_CANNOT_CHANGE_YOUR_OWN_ROLE,
            InvalidWorkspaceRole: ERROR_INVALID_WORKSPACE_ROLE,
            LastAdminOfWorkspace: ERROR_GROUP_USER_IS_LAST_ADMIN,
        }
    )
    @transaction.atomic
    def patch(self, request, workspace_id, member_id, data):
        """Changes the role of the given workspace member."""

        workspace = CoreHandler().get_workspace(workspace_id)
        workspace_user = get_workspace_member_for_admin(
            workspace,
            member_id,
        )
        workspace_user = WorkspacesAdminHandler().update_workspace_member(
            request.user, workspace_user, data["permissions"]
        )
        return Response(AdminWorkspaceMemberSerializer(workspace_user).data)

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_delete_workspace_member",
        description="Removes a member from the specified workspace if the requesting "
        "user is staff.",
        parameters=[WORKSPACE_ID_PARAMETER, MEMBER_ID_PARAMETER],
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP",
                    "ERROR_GROUP_USER_IS_LAST_ADMIN",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_GROUP_DOES_NOT_EXIST",
                    "ERROR_GROUP_USER_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            WorkspaceUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            CannotDeleteYourselfFromWorkspace: ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP,
            LastAdminOfWorkspace: ERROR_GROUP_USER_IS_LAST_ADMIN,
        }
    )
    @transaction.atomic
    def delete(self, request, workspace_id, member_id):
        """Removes the given workspace member."""

        workspace = CoreHandler().get_workspace(workspace_id)
        workspace_user = CoreHandler().get_workspace_user(
            member_id,
            base_queryset=WorkspaceUser.objects.filter(
                workspace=workspace
            ).select_for_update(of=("self",)),
        )
        WorkspacesAdminHandler().delete_workspace_member(request.user, workspace_user)
        return Response(status=204)


class WorkspaceExportAdminView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_export_workspace_async",
        description="Starts an asynchronous export of a workspace if the requesting "
        "user is staff. If application ids are provided only those applications are "
        "exported.",
        parameters=[WORKSPACE_ID_PARAMETER],
        request=ExportApplicationsJobType().request_serializer_class,
        responses={
            202: ExportApplicationsJobType().response_serializer_class,
            400: get_error_schema(
                [
                    "ERROR_MAX_JOB_COUNT_EXCEEDED",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @validate_body(
        ExportApplicationsJobType().request_serializer_class, return_validated=True
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            MaxJobCountExceeded: ERROR_MAX_JOB_COUNT_EXCEEDED,
        }
    )
    @transaction.atomic
    def post(self, request, workspace_id, data):
        """Starts an asynchronous export job for the given workspace."""

        workspace = CoreHandler().get_workspace(workspace_id)
        job = WorkspacesAdminHandler().export_workspace(
            request.user,
            workspace,
            application_ids=data.get("application_ids"),
            only_structure=data.get("only_structure", False),
        )
        serializer = job_type_registry.get_serializer(job, JobSerializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
