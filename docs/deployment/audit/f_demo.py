# 批次 F：演示数据（销售管理），便于理解系统实际运作
from django.contrib.auth import get_user_model

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.models import Database, Table
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace

User = get_user_model()
WORKSPACE = "演示-销售管理"
RESULTS = []


def check(name, fn):
    try:
        value = fn()
        RESULTS.append(("PASS", name, "" if value is None else str(value)[:60]))
    except Exception as e:  # noqa: BLE001
        RESULTS.append(("FAIL", name, f"{type(e).__name__}: {e}"))


def main():
    admin = User.objects.filter(is_staff=True).first()
    handler = CoreHandler()
    workspace, _ = Workspace.objects.get_or_create(name=WORKSPACE)
    handler.add_user_to_workspace(workspace, admin, "ADMIN")

    app = Database.objects.filter(name="销售数据", workspace=workspace).first()
    if app is None:
        app = handler.create_application(admin, workspace, "database", name="销售数据")

    def create_table(name, rows):
        table = app.table_set.filter(name=name).first()
        if table is None:
            table, _ = TableHandler().create_table(
                admin, app, name=name, data=rows, first_row_header=True
            )
        return table

    customers = create_table(
        "客户",
        [
            ["名称", "行业", "级别", "联系电话"],
            ["星辰科技", "互联网", "A", "13800000001"],
            ["远山制造", "制造", "B", "13800000002"],
            ["蓝海零售", "零售", "A", "13800000003"],
            ["晨光咨询", "服务", "C", "13800000004"],
        ],
    )
    products = create_table(
        "产品",
        [
            ["名称", "单价", "库存"],
            ["企业版订阅", 1999, 100],
            ["专业版订阅", 999, 200],
            ["定制开发", 8888, 20],
            ["培训课程", 1299, 50],
        ],
    )
    orders = create_table(
        "订单",
        [
            ["订单号", "客户", "产品", "数量", "金额", "状态", "日期"],
            ["SO-2026-001", "星辰科技", "企业版订阅", 10, 19990, "已完成", "2026-01-05"],
            ["SO-2026-002", "远山制造", "定制开发", 2, 17776, "进行中", "2026-02-10"],
            ["SO-2026-003", "蓝海零售", "专业版订阅", 20, 19980, "进行中", "2026-03-15"],
            ["SO-2026-004", "晨光咨询", "培训课程", 5, 6495, "新订单", "2026-04-20"],
            ["SO-2026-005", "星辰科技", "专业版订阅", 30, 29970, "已完成", "2026-05-25"],
        ],
    )

    # 将客户/产品/状态列升级为单选，金额/数量保持数字
    def field_by_name(table, name):
        return table.field_set.get(name=name)

    status_field = field_by_name(orders, "状态")
    if type(status_field.specific).__name__ != "SingleSelectField":
        FieldHandler().update_field(
            admin,
            status_field.specific,
            "single_select",
            select_options=[
                {"value": "新订单", "color": "blue"},
                {"value": "进行中", "color": "orange"},
                {"value": "已完成", "color": "green"},
            ],
        )
    industry_field = field_by_name(customers, "行业")
    if type(industry_field.specific).__name__ != "SingleSelectField":
        FieldHandler().update_field(
            admin,
            industry_field.specific,
            "single_select",
            select_options=[
                {"value": "互联网", "color": "blue"},
                {"value": "制造", "color": "orange"},
                {"value": "零售", "color": "green"},
                {"value": "服务", "color": "purple"},
            ],
        )

    # 真实日期字段（初始导入的列都是文本）
    if not orders.field_set.filter(name="下单日期").exists():
        FieldHandler().create_field(
            admin, orders, "date", name="下单日期", date_include_time=False
        )
    order_date_field = field_by_name(orders, "下单日期")
    text_date_field = field_by_name(orders, "日期")
    order_model = orders.get_model()
    for row in order_model.objects.all():
        RowHandler().update_row(
            admin,
            orders,
            row,
            {f"field_{order_date_field.id}": getattr(row, f"field_{text_date_field.id}")},
        )

    # 视图
    view_handler = ViewHandler()
    for view_type, name in [
        ("grid", "全部订单"),
        ("gallery", "订单卡片"),
        ("kanban", "按状态看板"),
    ]:
        if not orders.view_set.filter(name=name).exists():
            kwargs = {"name": name}
            if view_type == "kanban":
                if not orders.field_set.filter(name="看板分组").exists():
                    FieldHandler().create_field(
                        admin,
                        orders,
                        "single_select",
                        name="看板分组",
                        select_options=[
                            {"value": "新订单", "color": "blue"},
                            {"value": "进行中", "color": "orange"},
                            {"value": "已完成", "color": "green"},
                        ],
                    )
                kwargs["single_select_field"] = orders.field_set.get(
                    name="看板分组"
                ).specific
            view_handler.create_view(admin, orders, view_type, **kwargs)
    if not orders.view_set.filter(name="订单日历").exists():
        view_handler.create_view(
            admin,
            orders,
            "calendar",
            name="订单日历",
            date_field=order_date_field.specific,
        )

    # 示例数据截图用
    print("TABLE_IDS", customers.id, products.id, orders.id)
    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    print("F_DEMO_DB_DONE")


main()
