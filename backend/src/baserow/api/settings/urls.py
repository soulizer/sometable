from django.urls import re_path

from .backup_storage_views import BackupStorageSettingsView, BackupStorageTestView
from .backup_views import (
    BackupRestoreStatusView,
    BackupRestoreView,
    BackupSettingsView,
)
from .storage_views import StorageSettingsTestView, StorageSettingsView
from .views import SettingsView, UpdateSettingsView

app_name = "baserow.api.settings"

urlpatterns = [
    re_path(r"^update/$", UpdateSettingsView.as_view(), name="update"),
    re_path(r"^storage/$", StorageSettingsView.as_view(), name="storage"),
    re_path(
        r"^storage/test/$",
        StorageSettingsTestView.as_view(),
        name="storage_test",
    ),
    re_path(r"^backups/$", BackupSettingsView.as_view(), name="backups"),
    re_path(
        r"^backups/restore/$",
        BackupRestoreView.as_view(),
        name="backups_restore",
    ),
    re_path(
        r"^backups/restore/(?P<token>[A-Za-z0-9_-]+)/status/$",
        BackupRestoreStatusView.as_view(),
        name="backups_restore_status",
    ),
    re_path(
        r"^backup-storage/$",
        BackupStorageSettingsView.as_view(),
        name="backup_storage",
    ),
    re_path(
        r"^backup-storage/test/$",
        BackupStorageTestView.as_view(),
        name="backup_storage_test",
    ),
    re_path(r"^$", SettingsView.as_view(), name="get"),
]
