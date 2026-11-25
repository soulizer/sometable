import json
import os
import tempfile
import threading
from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.module_loading import import_string

# Where the admin-managed storage settings are persisted. The file lives on a
# dedicated Docker volume so it is independent of the configured storage backend.
DEFAULT_STORAGE_SETTINGS_FILE = "/baserow/config/storage.json"
DEFAULT_BACKUP_STORAGE_SETTINGS_FILE = "/baserow/config/backup-storage.json"

_lock = threading.Lock()


class InvalidStorageConfig(Exception):
    pass


def get_settings_file() -> str:
    return getattr(
        settings, "STORAGE_SETTINGS_FILE", DEFAULT_STORAGE_SETTINGS_FILE
    )


def get_backup_storage_settings_file() -> str:
    """Backup storage has its own credentials and bucket, independent of media."""

    return getattr(
        settings,
        "BACKUP_STORAGE_SETTINGS_FILE",
        DEFAULT_BACKUP_STORAGE_SETTINGS_FILE,
    )


def _env_config() -> dict[str, Any]:
    """
    Returns the storage configuration derived from the deployment environment.
    This keeps existing `.env` based deployments working out of the box.
    """

    if not getattr(settings, "AWS_STORAGE_ENABLED", False):
        return {"type": "local"}

    return {
        "type": "s3",
        "bucket_name": getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""),
        "endpoint_url": getattr(settings, "AWS_S3_ENDPOINT_URL", "") or "",
        "region_name": getattr(settings, "AWS_S3_REGION_NAME", "") or "",
        "location": getattr(settings, "AWS_LOCATION", "") or "",
        "access_key_id": getattr(settings, "AWS_ACCESS_KEY_ID", "") or "",
        "secret_access_key": getattr(settings, "AWS_SECRET_ACCESS_KEY", "") or "",
        "custom_domain": getattr(settings, "AWS_S3_CUSTOM_DOMAIN", "") or "",
        "addressing_style": getattr(settings, "AWS_S3_ADDRESSING_STYLE", "") or "path",
        "querystring_auth": bool(
            getattr(settings, "AWS_QUERYSTRING_AUTH", True)
        ),
        "querystring_expire": getattr(settings, "AWS_QUERYSTRING_EXPIRE", None),
        "default_acl": getattr(settings, "AWS_DEFAULT_ACL", None),
    }


def _load_config(path: str, env_config: dict[str, Any]) -> tuple[dict[str, Any], str]:
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("type") in {"local", "s3"}:
            if data.get("type") == "local":
                return {"type": "local"}, "file"
            # Secrets are never returned to the API, but they are needed to
            # build the storage backend.
            merged = dict(env_config)
            merged.update(data)
            return merged, "file"
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return env_config, ("env" if env_config["type"] == "s3" else "default")


def load_storage_config() -> tuple[dict[str, Any], str]:
    """
    Loads the effective storage configuration.

    :return: a tuple with the configuration and its source, which is one of
        `file` (managed through the admin interface), `env` (deployment
        environment variables) or `default` (local file system).
    """

    return _load_config(get_settings_file(), _env_config())


def load_backup_storage_config() -> tuple[dict[str, Any], str]:
    """Loads the optional remote storage used to upload backup archives."""

    return _load_config(
        get_backup_storage_settings_file(), {"type": "local"}
    )


def validate_storage_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise InvalidStorageConfig("The configuration must be an object.")

    storage_type = config.get("type")
    if storage_type not in {"local", "s3"}:
        raise InvalidStorageConfig("Unknown storage type.")

    if storage_type == "local":
        return {"type": "local"}

    cleaned = {
        "type": "s3",
        "bucket_name": str(config.get("bucket_name") or "").strip(),
        "endpoint_url": str(config.get("endpoint_url") or "").strip(),
        "region_name": str(config.get("region_name") or "").strip(),
        "location": str(config.get("location") or "").strip().strip("/"),
        "access_key_id": str(config.get("access_key_id") or "").strip(),
        "secret_access_key": str(config.get("secret_access_key") or ""),
        "custom_domain": str(config.get("custom_domain") or "").strip(),
        "addressing_style": (
            "virtual"
            if config.get("addressing_style") == "virtual"
            else "path"
        ),
        "querystring_auth": bool(config.get("querystring_auth", True)),
        "querystring_expire": config.get("querystring_expire") or None,
        "default_acl": config.get("default_acl") or None,
    }

    if cleaned["querystring_expire"] is not None:
        try:
            cleaned["querystring_expire"] = int(cleaned["querystring_expire"])
        except (TypeError, ValueError):
            raise InvalidStorageConfig("The signed URL expiry must be a number.")

    if not cleaned["bucket_name"]:
        raise InvalidStorageConfig("The bucket name is required.")

    if not cleaned["access_key_id"] or not cleaned["secret_access_key"]:
        raise InvalidStorageConfig(
            "The access key ID and secret access key are required."
        )

    for key in ("endpoint_url", "custom_domain"):
        value = cleaned[key]
        if value and not value.startswith(("http://", "https://")):
            raise InvalidStorageConfig(f"{key} must start with http:// or https://.")

    return cleaned


def save_storage_config(
    config: dict[str, Any], path: str | None = None
) -> dict[str, Any]:
    """
    Persists the storage configuration atomically. The secret is stored in the
    file with restrictive permissions and is never exposed through the API.
    """

    cleaned = validate_storage_config(config)
    path = path or get_settings_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with _lock:
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(cleaned, f)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return cleaned


def save_backup_storage_config(config: dict[str, Any]) -> dict[str, Any]:
    return save_storage_config(config, get_backup_storage_settings_file())


def build_s3_client(config: dict[str, Any]):
    """Low-level boto3 client shared by media and backup storage operations."""

    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=config.get("endpoint_url") or None,
        region_name=config.get("region_name") or None,
        aws_access_key_id=config.get("access_key_id") or None,
        aws_secret_access_key=config.get("secret_access_key") or None,
        config=Config(
            signature_version="s3v4",
            s3={
                "addressing_style": config.get("addressing_style") or "path"
            },
        ),
    )


def public_config(
    config: dict[str, Any], source: str, local_path: str | None = None
) -> dict[str, Any]:
    """Serializes a configuration without ever returning secrets."""

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
        "local_path": local_path or settings.MEDIA_ROOT,
    }


def merged_config(data: dict[str, Any], loader=load_storage_config):
    """Keeps stored credentials when the user leaves the secret fields blank."""

    current, _ = loader()
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


def build_storage(config: dict[str, Any]) -> Storage:
    if config.get("type") == "s3":
        backend = import_string("storages.backends.s3boto3.S3Boto3Storage")
        return backend(
            bucket_name=config["bucket_name"],
            access_key=config["access_key_id"],
            secret_key=config["secret_access_key"],
            endpoint_url=config["endpoint_url"] or None,
            region_name=config["region_name"] or None,
            location=config["location"] or "",
            custom_domain=config["custom_domain"] or None,
            addressing_style=config["addressing_style"],
            querystring_auth=config["querystring_auth"],
            querystring_expire=config.get("querystring_expire"),
            default_acl=config.get("default_acl"),
            file_overwrite=False,
            object_parameters={"CacheControl": "max-age=86400"},
        )

    return FileSystemStorage(
        location=settings.MEDIA_ROOT,
        base_url=settings.MEDIA_URL,
    )


class ConfigurableStorage(Storage):
    """
    Storage backend that delegates to the configuration managed in the admin
    settings. The configuration is re-read when the file changes, so switching
    storage does not require restarting the processes.
    """

    def __init__(self, *args, **kwargs):
        self._delegate: Storage | None = None
        self._fingerprint: tuple[int, int] | None = None
        super().__init__(*args, **kwargs)

    def _get_delegate(self) -> Storage:
        path = get_settings_file()
        try:
            stat = os.stat(path)
            fingerprint = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            fingerprint = None

        with _lock:
            if self._delegate is None or fingerprint != self._fingerprint:
                config, _ = load_storage_config()
                self._delegate = build_storage(config)
                self._fingerprint = fingerprint
            return self._delegate

    def __getattr__(self, name):
        # Delegate anything that is not part of the public storage API.
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._get_delegate(), name)

    # Explicit delegations: the base `Storage` class implements these methods
    # with `NotImplementedError`, so `__getattr__` would not be called.
    def open(self, name, mode="rb"):
        return self._get_delegate().open(name, mode)

    def save(self, name, content, max_length=None):
        return self._get_delegate().save(name, content, max_length=max_length)

    def delete(self, name):
        return self._get_delegate().delete(name)

    def exists(self, name):
        return self._get_delegate().exists(name)

    def listdir(self, path):
        return self._get_delegate().listdir(path)

    def size(self, name):
        return self._get_delegate().size(name)

    def url(self, name):
        return self._get_delegate().url(name)

    def path(self, name):
        return self._get_delegate().path(name)

    def get_accessed_time(self, name):
        return self._get_delegate().get_accessed_time(name)

    def get_created_time(self, name):
        return self._get_delegate().get_created_time(name)

    def get_modified_time(self, name):
        return self._get_delegate().get_modified_time(name)

    def get_available_name(self, name, max_length=None):
        return self._get_delegate().get_available_name(
            name, max_length=max_length
        )

    def generate_filename(self, filename):
        return self._get_delegate().generate_filename(filename)

    def get_valid_name(self, name):
        return self._get_delegate().get_valid_name(name)
