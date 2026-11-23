from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.schemas import get_error_schema
from baserow.core.backup import list_backups, run_backup, restore_backup


class BackupSettingsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="list_backups",
        description="Lists the available backups. Only staff users can request it.",
        responses={200: None},
    )
    def get(self, request):
        return Response(list_backups())

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
        try:
            restore_backup(backup_id)
        except FileNotFoundError:
            return Response({"error": "Backup not found."}, status=404)
        return Response({"ok": True})
