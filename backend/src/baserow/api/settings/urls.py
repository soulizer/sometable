from django.urls import re_path

from .backup_views import BackupRestoreView, BackupSettingsView
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
    re_path(r"^$", SettingsView.as_view(), name="get"),
]
