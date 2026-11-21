from drf_spectacular.utils import extend_schema
from django.conf import settings
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.core.storage_config import (
    InvalidStorageConfig,
    build_storage,
    load_storage_config,
    save_storage_config,
    validate_storage_config,
)


def _public_config(config, source):
    return {
        "type": config.get("type", "local"),
        "source": source,
        "bucket_name": config.get("bucket_name", ""),
        "endpoint_url": config.get("endpoint_url", ""),
        "region_name": config.get("region_name", ""),
        "location": config.get("location", ""),
        "custom_domain": config.get("custom_domain", ""),
        "addressing_style": config.get("addressing_style", "path"),
        "querystring_auth": bool(config.get("querystring_auth", True)),
        "has_credentials": bool(
            config.get("access_key_id") and config.get("secret_access_key")
        ),
        "local_path": settings.MEDIA_ROOT,
    }


def _merged_config(data):
    """
    Reuses the stored credentials when they are not provided again, so the
    secret never has to be sent back to the browser.
    """

    current, _ = load_storage_config()
    merged = dict(data)
    if merged.get("type") == "s3":
        if not merged.get("access_key_id"):
            merged["access_key_id"] = current.get("access_key_id", "")
        if not merged.get("secret_access_key"):
            merged["secret_access_key"] = current.get("secret_access_key", "")
        for key in ("querystring_expire", "default_acl"):
            if merged.get(key) is None and current.get(key) is not None:
                merged[key] = current[key]
    return merged


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
        return Response(_public_config(config, source))

    @extend_schema(
        tags=["Settings"],
        operation_id="update_storage_settings",
        description="Updates the file storage configuration. Changes apply to "
        "new file operations immediately. Existing files are not migrated. "
        "Only staff users can update it.",
    )
    def put(self, request):
        try:
            saved = save_storage_config(_merged_config(request.data))
        except InvalidStorageConfig as e:
            return Response({"error": str(e)}, status=400)
        except OSError as e:
            return Response({"error": str(e)}, status=400)

        return Response(_public_config(saved, "file"))


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
            config = validate_storage_config(_merged_config(request.data))
        except InvalidStorageConfig as e:
            return Response({"error": str(e)}, status=400)

        if config["type"] == "local":
            return Response({"ok": True})

        try:
            storage = build_storage(config)
            storage.connection.list_objects_v2(
                Bucket=config["bucket_name"],
                Prefix=config["location"] or "",
                MaxKeys=1,
            )
        except Exception as e:  # noqa: BLE001 - report the provider error as is
            return Response({"ok": False, "error": str(e)}, status=400)

        return Response({"ok": True})
