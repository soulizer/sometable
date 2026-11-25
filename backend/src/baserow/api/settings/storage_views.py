from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.core.storage_config import (
    InvalidStorageConfig,
    build_storage,
    load_storage_config,
    merged_config,
    public_config,
    save_storage_config,
    validate_storage_config,
)


class StorageSettingsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="get_storage_settings",
        description="Returns the effective file storage configuration. Only "
        "staff users can request it.",
    )
    def get(self, request):
        config, source = load_storage_config()
        return Response(public_config(config, source))

    @extend_schema(
        tags=["Settings"],
        operation_id="update_storage_settings",
        description="Updates the file storage configuration. Changes apply to "
        "new file operations immediately. Existing files are not migrated. "
        "Only staff users can update it.",
    )
    def put(self, request):
        try:
            saved = save_storage_config(merged_config(request.data))
        except InvalidStorageConfig as e:
            return Response({"error": str(e)}, status=400)
        except OSError as e:
            return Response({"error": str(e)}, status=400)

        return Response(public_config(saved, "file"))


class StorageSettingsTestView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Settings"],
        operation_id="test_storage_settings",
        description="Checks that the provided storage configuration is "
        "reachable. Only staff users can request it.",
    )
    def post(self, request):
        try:
            config = validate_storage_config(merged_config(request.data))
        except InvalidStorageConfig as e:
            return Response({"error": str(e)}, status=400)

        if config["type"] == "local":
            return Response({"ok": True})

        try:
            storage = build_storage(config)
            # `connection` is a boto3 *resource*, the low-level client lives on
            # `meta.client`.
            storage.connection.meta.client.list_objects_v2(
                Bucket=config["bucket_name"],
                Prefix=config["location"] or "",
                MaxKeys=1,
            )
        except Exception as e:  # noqa: BLE001 - report the provider error as is
            return Response({"ok": False, "error": str(e)}, status=400)

        return Response({"ok": True})
