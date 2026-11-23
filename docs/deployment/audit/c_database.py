# 批次 C：数据库、字段、行、视图、导入导出
from django.contrib.auth import get_user_model

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.models import Database
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.exceptions import PermissionDenied
from baserow.core.handler import CoreHandler
from baserow.core.models import Application, Workspace

User = get_user_model()
WORKSPACE_NAME = "审计-工作区"
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


def get_user(role):
    return User.objects.get(email=f"audit-{role}@access126.com")


def main():
    handler = CoreHandler()
    builder = get_user("builder")
    editor = get_user("editor")
    commenter = get_user("commenter")
    viewer = get_user("viewer")
    workspace = Workspace.objects.get(name=WORKSPACE_NAME)

    app = Database.objects.filter(name=APP_NAME, workspace=workspace).first()
    if app is None:
        app = handler.create_application(builder, workspace, "database", name=APP_NAME)
        print("created app", app.id)

    table = app.table_set.filter(name=TABLE_NAME).first()
    if table is None:
        table, _ = TableHandler().create_table(
            builder,
            app,
            name=TABLE_NAME,
            data=[
                ["名称", "状态", "数量", "日期"],
                ["审计行1", "进行中", 10, "2026-01-01"],
                ["审计行2", "已完成", 20, "2026-02-01"],
            ],
            first_row_header=True,
        )
        print("created table", table.id)

    field_names = [f.name for f in table.field_set.all()]
    check("表-包含初始字段", lambda: set(field_names) >= {"名称", "状态", "数量", "日期"})
    name_field = table.field_set.get(name="名称")
    status_field = table.field_set.get(name="状态")
    amount_field = table.field_set.get(name="数量")
    date_field = table.field_set.get(name="日期")

    # --- 字段 ---
    if not table.field_set.filter(name="备注").exists():
        FieldHandler().create_field(
            builder, table, "long_text", name="备注", description="审计"
        )
    if not table.field_set.filter(name="审计日期").exists():
        FieldHandler().create_field(
            builder, table, "date", name="审计日期", date_include_time=False
        )
    audit_date_field = table.field_set.get(name="审计日期")
    check(
        "字段-创建成功",
        lambda: table.field_set.filter(name="备注").exists(),
    )
    check(
        "字段-编辑者不能创建字段",
        lambda: FieldHandler().create_field(editor, table, "text", name="越权字段"),
        raises=PermissionDenied,
    )
    check(
        "字段-查看者不能创建字段",
        lambda: FieldHandler().create_field(viewer, table, "text", name="越权字段2"),
        raises=PermissionDenied,
    )

    # --- 行 ---
    row_handler = RowHandler()
    model = table.get_model()
    if model.objects.count() == 0:
        row_handler.create_rows(
            builder,
            table,
            [
                {
                    f"field_{name_field.id}": "审计行3",
                    f"field_{status_field.id}": "新",
                    f"field_{amount_field.id}": 30,
                    f"field_{date_field.id}": "2026-03-01",
                },
            ],
        )
    check("行-已创建", lambda: model.objects.count() >= 3)
    check(
        "行-编辑者可以创建",
        lambda: row_handler.create_rows(
            editor,
            table,
            [
                {
                    f"field_{name_field.id}": "审计行4",
                    f"field_{status_field.id}": "新",
                    f"field_{amount_field.id}": 40,
                    f"field_{audit_date_field.id}": "2026-04-01",
                }
            ],
        )
        is not None,
    )
    check(
        "行-评论者不能创建",
        lambda: row_handler.create_rows(
            commenter, table, [{"名称": "越权行", "状态": "新"}]
        ),
        raises=PermissionDenied,
    )
    check(
        "行-查看者不能创建",
        lambda: row_handler.create_rows(viewer, table, [{"名称": "越权行", "状态": "新"}]),
        raises=PermissionDenied,
    )
    first_row = model.objects.first()
    check(
        "行-编辑者可更新",
        lambda: row_handler.update_row(
            editor, table, row_handler.get_row(editor, table, first_row.id), {"数量": 99}
        )
        is not None,
    )
    check(
        "行-查看者不能更新",
        lambda: row_handler.update_row(
            viewer, table, row_handler.get_row(viewer, table, first_row.id), {"数量": 1}
        ),
        raises=PermissionDenied,
    )

    # --- 视图 ---
    view_handler = ViewHandler()
    view_types = ["grid", "gallery", "form", "kanban", "calendar", "timeline"]
    for index, view_type in enumerate(view_types):
        name = f"审计-{view_type}"
        view = table.view_set.filter(name=name).first()
        if view is None:
            kwargs = {"name": name}
            if view_type == "kanban":
                # 看板需要单选字段
                if not table.field_set.filter(name="看板分组").exists():
                    FieldHandler().create_field(
                        builder,
                        table,
                        "single_select",
                        name="看板分组",
                        select_options=[
                            {"value": "A", "color": "blue"},
                            {"value": "B", "color": "green"},
                        ],
                    )
                kwargs["single_select_field"] = table.field_set.get(name="看板分组").specific
            if view_type in ("calendar", "timeline"):
                kwargs["date_field"] = audit_date_field.specific
            view = view_handler.create_view(builder, table, view_type, **kwargs)
        check(f"视图-{view_type} 创建", lambda v=view: v.id is not None)
    check(
        "视图-编辑者不能创建",
        lambda: view_handler.create_view(editor, table, "grid", name="越权视图"),
        raises=PermissionDenied,
    )

    grid = table.view_set.get(name="审计-grid")
    # --- 筛选/排序/分组 ---
    if not grid.viewfilter_set.exists():
        view_handler.create_filter(builder, grid, name_field, "contains", "审计")
    check(
        "筛选-创建并生效",
        lambda: list(
            view_handler.apply_filters(grid, model.objects.all()).values_list(
                "id", flat=True
            )
        )
        == list(
            model.objects.filter(
                **{f"field_{name_field.id}__contains": "审计"}
            ).values_list("id", flat=True)
        ),
    )
    if not grid.viewsort_set.exists():
        view_handler.create_sort(builder, grid, amount_field, "DESC")
    check(
        "排序-创建",
        lambda: grid.viewsort_set.filter(field_id=amount_field.id).exists(),
    )
    if not grid.viewgroupby_set.exists():
        view_handler.create_group_by(builder, grid, status_field, "ASC", 200)
    check(
        "分组-创建",
        lambda: grid.viewgroupby_set.filter(field_id=status_field.id).exists(),
    )
    check(
        "视图-查看者可读",
        lambda: view_handler.get_view_as_user(viewer, grid.id) is not None,
    )
    check(
        "视图-评论者可读",
        lambda: view_handler.get_view_as_user(commenter, grid.id) is not None,
    )

    # --- 回收站 ---
    check(
        "表-编辑者不能删除",
        lambda: TableHandler().delete_table(editor, table),
        raises=PermissionDenied,
    )
    check(
        "表-构建者删除入回收站",
        lambda: TableHandler().delete_table(builder, table) is None,
    )
    check(
        "表-回收站外不可见",
        lambda: app.table_set.filter(id=table.id).exists() is False,
    )

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"C_DATABASE_OK total={len(RESULTS)} failed={len(failed)}")


main()
