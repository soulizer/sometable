from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from loguru import logger
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_query_parameters
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.search.serializers import (
    GlobalSearchResponseSerializer,
    WorkspaceSearchResponseSerializer,
    WorkspaceSearchSerializer,
)
from baserow.core.exceptions import UserNotInWorkspace, WorkspaceDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.core.operations import (
    ListWorkspacesOperationType,
    ReadWorkspaceOperationType,
)
from baserow.core.search.handler import WorkspaceSearchHandler


class WorkspaceSearchView(APIView):
    """
    API view for workspace search functionality.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Workspace ID to search within",
            ),
        ],
        request=WorkspaceSearchSerializer,
        responses={
            200: WorkspaceSearchResponseSerializer,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_INVALID_SEARCH_QUERY"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
        tags=["Search"],
        operation_id="workspace_search",
        description="Search across all searchable content within a workspace",
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
        }
    )
    @validate_query_parameters(WorkspaceSearchSerializer, return_validated=True)
    def get(self, request, workspace_id, query_params):
        workspace = CoreHandler().get_workspace(workspace_id)
        CoreHandler().check_permissions(
            request.user,
            ReadWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )

        handler = WorkspaceSearchHandler()
        result_data = handler.search_workspace(
            user=request.user,
            workspace=workspace,
            query=query_params["query"],
            limit=query_params["limit"],
            offset=query_params["offset"],
        )
        serializer = WorkspaceSearchResponseSerializer(data=result_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GlobalSearchView(APIView):
    """
    API view for searching across all workspaces the user can access.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="query",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Search query",
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Maximum number of returned results",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Number of results to skip per workspace",
            ),
        ],
        responses={
            200: GlobalSearchResponseSerializer,
            400: get_error_schema(["ERROR_QUERY_PARAMETER_VALIDATION"]),
        },
        tags=["Search"],
        operation_id="global_search",
        description="Search across all workspaces accessible to the user",
    )
    @validate_query_parameters(WorkspaceSearchSerializer, return_validated=True)
    def get(self, request, query_params):
        core_handler = CoreHandler()
        workspaces = core_handler.filter_queryset(
            request.user,
            ListWorkspacesOperationType.type,
            core_handler.list_user_workspaces(request.user),
        ).order_by("id")

        search_handler = WorkspaceSearchHandler()
        results = []
        has_more = False
        limit = query_params["limit"]

        # Workspace IDs are never read from the request: the allowed workspaces are
        # derived solely from the current user's permissions.
        for workspace in workspaces:
            try:
                workspace_results = search_handler.search_workspace(
                    user=request.user,
                    workspace=workspace,
                    query=query_params["query"],
                    limit=limit,
                    offset=query_params["offset"],
                )
            except Exception:
                logger.exception(
                    "Global workspace search failed for workspace {workspace_id}",
                    workspace_id=workspace.id,
                )
                continue

            has_more = has_more or workspace_results.get("has_more", False)
            for result in workspace_results.get("results", []):
                if len(results) >= limit:
                    break
                metadata = result.get("metadata") or {}
                if "workspace_id" not in metadata:
                    result = {
                        **result,
                        "metadata": {**metadata, "workspace_id": workspace.id},
                    }
                results.append(result)

        serializer = GlobalSearchResponseSerializer(
            data={
                "count": len(results),
                "results": results,
                "has_more": has_more,
            }
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
