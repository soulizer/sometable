from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.core.backup import get_backup_root
from baserow.core.storage_config import (
    InvalidStorageConfig,
    build_s3_client,
    load_backup_storage_config,
    merged_config,
    public_config,
    save_backup_storage_config,
    validate_storage_config,
)

REMOTE_PREFIX = 'sometable-backups'


class BackupStorageSettingsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="get_backup_storage_settings",
        description="Returns the optional remote storage for backup archives. "
        "Only staff users can request it.",
    )
    def get(self, request):
        config, source = load_backup_storage_config()
        return Response(public_config(config, source, get_backup_root()))

    @extend_schema(
        tags=["Settings"],
        operation_id="update_backup_storage_settings",
        description="Configures where backup archives are uploaded. This "
        "storage is independent from the media object storage. Only staff "
        "users can update it.",
    )
    def put(self, request):
        try:
            saved = save_backup_storage_config(
                merged_config(request.data, load_backup_storage_config)
            )
        except InvalidStorageConfig as e:
            return Response({"error": str(e)}, status=400)
        except OSError as e:
            return Response({"error": str(e)}, status=400)

        return Response(public_config(saved, "file", get_backup_root()))


class BackupStorageTestView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="test_backup_storage_settings",
        description="Checks that the remote backup storage is reachable. Only "
        "staff users can request it.",
    )
    def post(self, request):
        try:
            config = validate_storage_config(
                merged_config(request.data, load_backup_storage_config)
            )
        except InvalidStorageConfig as e:
            return Response({"error": str(e)}, status=400)

        if config["type"] == "local":
            return Response({"ok": True})

        try:
            client = build_s3_client(config)
            prefix = config.get("location", "").strip("/")
            key_prefix = f"{prefix}/{REMOTE_PREFIX}/" if prefix else f"{REMOTE_PREFIX}/"
            client.list_objects_v2(
                Bucket=config["bucket_name"],
                Prefix=key_prefix,
                MaxKeys=1,
            )
        except Exception as e:  # noqa: BLE001 - report the provider error as is
            return Response({"ok": False, "error": str(e)}, status=400)

        return Response({"ok": True})
