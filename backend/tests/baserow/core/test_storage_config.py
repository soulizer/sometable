import json
from io import BytesIO

from django.test.utils import override_settings

import pytest

from baserow.core.storage_config import (
    ConfigurableStorage,
    InvalidStorageConfig,
    load_storage_config,
    validate_storage_config,
)


def test_load_storage_config_defaults_to_local(tmp_path):
    with override_settings(
        STORAGE_SETTINGS_FILE=str(tmp_path / "storage.json"),
        AWS_STORAGE_ENABLED=False,
    ):
        config, source = load_storage_config()

    assert config == {"type": "local"}
    assert source == "default"


def test_load_storage_config_from_file(tmp_path):
    path = tmp_path / "storage.json"
    path.write_text(
        json.dumps(
            {
                "type": "s3",
                "bucket_name": "my-bucket",
                "access_key_id": "key",
                "secret_access_key": "secret",
            }
        )
    )

    with override_settings(STORAGE_SETTINGS_FILE=str(path)):
        config, source = load_storage_config()

    assert source == "file"
    assert config["bucket_name"] == "my-bucket"
    assert config["addressing_style"] == "path"


def test_validate_storage_config_requires_bucket_and_credentials():
    with pytest.raises(InvalidStorageConfig):
        validate_storage_config({"type": "s3"})

    with pytest.raises(InvalidStorageConfig):
        validate_storage_config(
            {"type": "s3", "bucket_name": "bucket", "access_key_id": "key"}
        )


def test_configurable_storage_reads_and_writes_local_files(tmp_path):
    with override_settings(
        STORAGE_SETTINGS_FILE=str(tmp_path / "storage.json"),
        AWS_STORAGE_ENABLED=False,
        MEDIA_ROOT=str(tmp_path / "media"),
        MEDIA_URL="/media/",
    ):
        storage = ConfigurableStorage()
        name = storage.save("test.txt", BytesIO(b"hello"))
        assert storage.exists(name)
        with storage.open(name) as f:
            assert f.read() == b"hello"
        assert storage.url(name).endswith("test.txt")
        storage.delete(name)
        assert not storage.exists(name)
