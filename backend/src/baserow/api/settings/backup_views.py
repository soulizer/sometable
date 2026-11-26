from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from loguru import logger

from baserow.api.schemas import get_error_schema
from baserow.core.backup import (
    SCOPE_ALL,
    list_all_backups,
    restore_backup,
    run_backup,
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
        description="Restores a backup. This overwrites current data. Only staff "
        "users can request it.",
        responses={
            200: None,
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

        # Always keep a copy of the current state before overwriting it. Retention
        # is skipped so the safety copy cannot delete the backup being restored.
        try:
            run_backup(scope=SCOPE_ALL, keep=0)
        except Exception:
            logger.exception("Failed to create the safety backup before a restore")
            return Response(
                {"error": "Could not create a safety backup; restore cancelled."},
                status=500,
            )

        try:
            restore_backup(backup_id)
        except FileNotFoundError:
            return Response({"error": "Backup not found."}, status=404)
        return Response({"ok": True})
