# 批次 F3：更丰富的示例数据（更多角度）
from datetime import date, timedelta

from django.contrib.auth import get_user_model

from baserow.contrib.database.models import Database
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.dashboard.models import Dashboard
from baserow.contrib.dashboard.widgets.handler import WidgetHandler
from baserow.contrib.dashboard.widgets.registries import widget_type_registry
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace

User = get_user_model()


def main():
    admin = User.objects.filter(is_staff=True).first()
    handler = CoreHandler()
    workspace = Workspace.objects.get(name="演示-销售管理")
    db = Database.objects.get(name="销售数据", workspace=workspace)
    orders = db.table_set.get(name="订单")

    # 扩充订单到 30 行
    model = orders.get_model()
    if model.objects.count() < 30:
        customers = list(db.table_set.get(name="客户").get_model().objects.values_list("id", flat=True))
        products = list(db.table_set.get(name="产品").get_model().objects.values_list("id", flat=True))
        amount_field = orders.field_set.get(name="金额")
        status_field = orders.field_set.get(name="状态")
        date_field = orders.field_set.get(name="下单日期")
        base = date(2026, 1, 1)
        rows = []
        for index in range(model.objects.count(), 30):
            rows.append(
                {
                    f"field_{amount_field.id}": 1000 + index * 137,
                    f"field_{status_field.id}": ["新订单", "进行中", "已完成"][index % 3],
                    f"field_{date_field.id}": (base + timedelta(days=index * 7)).isoformat(),
                }
            )
        RowHandler().create_rows(admin, orders, rows)
    print("orders", model.objects.count())

    # 时间线与表单视图
    view_handler = ViewHandler()
    if not orders.view_set.filter(name="订单时间线").exists():
        start = orders.field_set.get(name="下单日期").specific
        view_handler.create_view(admin, orders, "timeline", name="订单时间线", date_field=start)
    if not orders.view_set.filter(name="订单录入").exists():
        view_handler.create_view(admin, orders, "form", name="订单录入")

    # 饼图组件
    dashboard = Dashboard.objects.get(name="销售仪表盘")
    chart_widget = dashboard.widget_set.get(title="订单金额").specific
    ds = chart_widget.data_source
    if not dashboard.widget_set.filter(title="订单状态占比").exists():
        pie_type = widget_type_registry.get("pie_chart")
        WidgetHandler().create_widget(
            pie_type,
            dashboard,
            data_source_id=ds.id,
            title="订单状态占比",
        )

    # 项目管理演示工作区
    pm, _ = Workspace.objects.get_or_create(name="演示-项目管理")
    handler.add_user_to_workspace(pm, admin, "ADMIN")
    pm_db = Database.objects.filter(name="项目数据", workspace=pm).first()
    if pm_db is None:
        pm_db = handler.create_application(admin, pm, "database", name="项目数据")
    projects = pm_db.table_set.filter(name="项目").first()
    if projects is None:
        projects, _ = TableHandler().create_table(
            admin,
            pm_db,
            name="项目",
            data=[
                ["名称", "状态", "开始日期", "截止日期"],
                ["官网改版", "进行中", "2026-01-10", "2026-03-30"],
                ["移动端上线", "新订单", "2026-02-01", "2026-06-30"],
                ["数据看板", "已完成", "2025-11-01", "2026-01-31"],
                ["客户门户", "进行中", "2026-03-01", "2026-08-31"],
            ],
            first_row_header=True,
        )
    tasks = pm_db.table_set.filter(name="任务").first()
    if tasks is None:
        tasks, _ = TableHandler().create_table(
            admin,
            pm_db,
            name="任务",
            data=[
                ["标题", "项目", "负责人", "截止日期"],
                ["首页视觉稿", "官网改版", "设计组", "2026-02-15"],
                ["接口联调", "移动端上线", "研发组", "2026-04-20"],
                ["埋点方案", "数据看板", "数据组", "2025-12-10"],
                ["权限模型", "客户门户", "研发组", "2026-07-15"],
            ],
            first_row_header=True,
        )
    from baserow.contrib.database.fields.handler import FieldHandler

    for field_name in ("开始日期", "截止日期"):
        field = projects.field_set.get(name=field_name)
        if type(field.specific).__name__ != "DateField":
            FieldHandler().update_field(
                admin, field.specific, "date", date_include_time=False
            )
    project_model = projects.get_model()
    start_field = projects.field_set.get(name="开始日期")
    end_field = projects.field_set.get(name="截止日期")
    for row in project_model.objects.all():
        RowHandler().update_row(
            admin,
            projects,
            row,
            {
                f"field_{start_field.id}": getattr(row, f"field_{start_field.id}"),
                f"field_{end_field.id}": getattr(row, f"field_{end_field.id}"),
            },
        )

    for view_type, name, kwargs in [
        ("grid", "全部项目", {}),
        ("kanban", "项目看板", {}),
        ("calendar", "项目日历", {}),
        ("timeline", "项目时间线", {}),
    ]:
        if projects.view_set.filter(name=name).exists():
            continue
        extra = {}
        if view_type == "kanban":
            if not projects.field_set.filter(name="看板分组").exists():
                from baserow.contrib.database.fields.handler import FieldHandler

                FieldHandler().create_field(
                    admin,
                    projects,
                    "single_select",
                    name="看板分组",
                    select_options=[
                        {"value": "新订单", "color": "blue"},
                        {"value": "进行中", "color": "orange"},
                        {"value": "已完成", "color": "green"},
                    ],
                )
            extra["single_select_field"] = projects.field_set.get(
                name="看板分组"
            ).specific
        if view_type in ("calendar", "timeline"):
            extra["date_field"] = projects.field_set.get(name="开始日期").specific
        view_handler.create_view(admin, projects, view_type, name=name, **extra)

    # 为看板分组字段填充与状态一致的值
    from baserow.contrib.database.fields.handler import FieldHandler as _FH

    group_field = projects.field_set.get(name="看板分组")
    status_field = projects.field_set.get(name="状态")
    pm = projects.get_model()
    for row in pm.objects.all():
        RowHandler().update_row(
            admin,
            projects,
            row,
            {
                f"field_{group_field.id}": getattr(row, f"field_{status_field.id}"),
            },
        )


    print("F3_DEMO_DONE")


main()
