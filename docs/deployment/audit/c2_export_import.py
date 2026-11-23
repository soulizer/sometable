# 批次 C2：应用导出 / 导入（工作区级）
from django.contrib.auth import get_user_model

from baserow.core.handler import CoreHandler
from baserow.core.import_export.handler import ImportExportHandler
from baserow.core.models import Application, Workspace
from baserow.core.registries import ImportExportConfig
from baserow.core.storage import get_default_storage
from baserow.core.trash.handler import TrashHandler
from baserow.contrib.database.models import Database, Table

User = get_user_model()
WORKSPACE_NAME = "审计-工作区"
IMPORT_WORKSPACE_NAME = "审计-导入工作区"
APP_NAME = "审计-数据库"
TABLE_NAME = "审计-数据表"
RESULTS = []


def check(name, fn, raises=None, predicate=None):
    try:
        value = fn()
    except Exception as e:  # noqa: BLE001
        if raises is not None and isinstance(e, raises):
            RESULTS.append(("PASS", name, f"预期异常 {type(e).__name__}"))
        else:
            RESULTS.append(("FAIL", name, f"异常 {type(e).__name__}: {e}"))
        return
    if raises is not None:
        RESULTS.append(("FAIL", name, f"预期 {raises.__name__} 但未抛出"))
    elif predicate is not None and not predicate(value):
        RESULTS.append(("FAIL", name, "断言不成立"))
    else:
        RESULTS.append(("PASS", name, ""))


def main():
    admin = User.objects.filter(is_staff=True).first()
    handler = CoreHandler()
    source = Workspace.objects.get(name=WORKSPACE_NAME)

    # c_database 结束时会把审计表放入回收站，这里先恢复。
    table = Table.objects.filter(name=TABLE_NAME, database__workspace=source).first()
    if table is None:
        trashed = Table.objects_and_trash.filter(
            name=TABLE_NAME, database__workspace=source
        ).first()
        if trashed is not None:
            TrashHandler.restore_item(admin, "table", trashed.id)
            table = Table.objects.filter(
                name=TABLE_NAME, database__workspace=source
            ).first()
    check("导出-审计表存在", lambda: table is not None)

    app = Database.objects.get(name=APP_NAME, workspace=source)
    config = ImportExportConfig(include_permission_data=False, reduce_disk_space_usage=True)
    resource = ImportExportHandler().export_workspace_applications(
        [app], config
    )
    check("导出-生成资源", lambda: resource.is_valid and resource.size > 0)

    # 导出文件默认在 export_files/，导入接口读取 import_files/，这里模拟任务流转。
    storage = get_default_storage()
    export_path = ImportExportHandler().get_export_storage_path(
        resource.get_archive_name()
    )
    import_path = ImportExportHandler().get_import_storage_path(
        resource.get_archive_name()
    )
    with storage.open(export_path, "rb") as f:
        storage.save(import_path, f)

    target, _ = Workspace.objects.get_or_create(name=IMPORT_WORKSPACE_NAME)
    handler.add_user_to_workspace(target, admin, "ADMIN")
    imported = ImportExportHandler().import_workspace_applications(
        admin, target, resource
    )
    check(
        "导入-应用已导入",
        lambda: any(a.name == APP_NAME for a in imported),
    )
    imported_app = Database.objects.get(name=APP_NAME, workspace=target)
    imported_table = imported_app.table_set.get(name=TABLE_NAME)
    check(
        "导入-表与行数一致",
        lambda: imported_table.get_model().objects.count()
        == table.get_model().objects.count(),
    )

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"C2_EXPORT_OK total={len(RESULTS)} failed={len(failed)}")


main()
