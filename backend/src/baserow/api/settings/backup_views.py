import secrets

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.schemas import get_error_schema
from baserow.core.backup import list_all_backups
from baserow.core.backup_status import (
    RESTORE_FAILED,
    RESTORE_PENDING,
    get_restore_status,
    set_restore_status,
)


class BackupSettingsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="list_backups",
        description="Lists the available backups. Only staff users can request it.",
        responses={200: None},
    )
    def get(self, request):
        return Response(list_all_backups())

    @extend_schema(
        tags=["Settings"],
        operation_id="create_backup",
        description="Creates a backup immediately. Only staff users can request it.",
        responses={200: None},
    )
    def post(self, request):
        scope = request.data.get("scope", None)
        from baserow.core.backup_tasks import run_backup_now

        run_backup_now.delay(scope)
        return Response({"ok": True, "queued": True})


class BackupRestoreView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="restore_backup",
        description="Queues a restore of a backup. The safety backup and the actual "
        "restore run asynchronously; poll the returned token's status endpoint. "
        "Only staff users can request it.",
        responses={
            202: None,
            400: get_error_schema(["ERROR_PERMISSION_DENIED"]),
        },
    )
    def post(self, request):
        backup_id = request.data.get("id")
        if not backup_id:
            return Response({"error": "Missing backup id."}, status=400)
        if request.data.get("confirm") != backup_id:
            return Response(
                {"error": "The backup id confirmation does not match."}, status=400
            )

        from baserow.core.backup_tasks import restore_backup_task

        token = secrets.token_urlsafe(16)
        set_restore_status(token, RESTORE_PENDING, 0, "Restore queued.")
        try:
            restore_backup_task.delay(token, backup_id)
        except Exception:
            set_restore_status(
                token, RESTORE_FAILED, 0, "Could not queue the restore task."
            )
            return Response({"error": "Could not queue the restore task."}, status=500)
        return Response({"ok": True, "token": token}, status=202)


class BackupRestoreStatusView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="restore_backup_status",
        description="Returns the progress of an asynchronous restore. Only staff "
        "users can request it.",
        responses={200: None, 404: None},
    )
    def get(self, request, token):
        status = get_restore_status(token)
        if status is None:
            return Response({"error": "Unknown restore token."}, status=404)
        return Response(status)
