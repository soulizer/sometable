# 批次 F2：演示仪表盘与自动化
from django.contrib.auth import get_user_model

from baserow.contrib.automation.nodes.handler import AutomationNodeHandler
from baserow.contrib.automation.nodes.registries import automation_node_type_registry
from baserow.contrib.automation.workflows.handler import AutomationWorkflowHandler
from baserow.contrib.dashboard.data_sources.handler import DashboardDataSourceHandler
from baserow.contrib.dashboard.data_sources.models import DashboardDataSource
from baserow.contrib.dashboard.models import Dashboard
from baserow.contrib.dashboard.widgets.models import Widget
from baserow.contrib.dashboard.widgets.handler import WidgetHandler
from baserow.contrib.dashboard.widgets.registries import widget_type_registry
from baserow.contrib.database.models import Database
from baserow.contrib.integrations.local_baserow.models import LocalBaserowAggregateRows
from baserow.core.handler import CoreHandler
from baserow.core.models import Application, Workspace
from baserow.core.services.registries import service_type_registry
from baserow.core.services.handler import ServiceHandler

User = get_user_model()
WORKSPACE = "演示-销售管理"
RESULTS = []


def check(name, fn):
    try:
        value = fn()
        RESULTS.append(("PASS", name, "" if value is None else str(value)[:80]))
    except Exception as e:  # noqa: BLE001
        RESULTS.append(("FAIL", name, f"{type(e).__name__}: {e}"))


def main():
    admin = User.objects.filter(is_staff=True).first()
    handler = CoreHandler()
    workspace = Workspace.objects.get(name=WORKSPACE)
    orders = Database.objects.get(name="销售数据", workspace=workspace).table_set.get(
        name="订单"
    )
    amount = orders.field_set.get(name="金额")
    status = orders.field_set.get(name="状态")

    # --- 仪表盘 ---
    dashboard_app = Application.objects.filter(
        name="销售仪表盘", workspace=workspace
    ).first()
    if dashboard_app is None:
        dashboard_app = handler.create_application(
            admin, workspace, "dashboard", name="销售仪表盘"
        )
    dashboard = Dashboard.objects.get(id=dashboard_app.id)
    service_type = service_type_registry.get("local_baserow_grouped_aggregate_rows")
    data_source = DashboardDataSource.objects.filter(
        dashboard=dashboard, name="订单金额按状态"
    ).first()
    if data_source is None:
        data_source = DashboardDataSourceHandler().create_data_source(
            dashboard,
            "订单金额按状态",
            service_type,
            table_id=orders.id,
            aggregation_series=[
                {"field_id": amount.id, "aggregation_type": "sum"}
            ],
            aggregation_group_bys=[{"field_id": status.id, "mode": "asc"}],
        )
    chart_type = widget_type_registry.get("chart")
    widget = Widget.objects.filter(dashboard=dashboard, title="订单金额").first()
    if widget is None:
        widget = WidgetHandler().create_widget(
            chart_type,
            dashboard,
            data_source_id=data_source.id,
            default_series_chart_type="BAR",
            title="订单金额",
        )
    summary_type = widget_type_registry.get("summary")
    summary = Widget.objects.filter(dashboard=dashboard, title="订单总数").first()
    if summary is None:
        summary = WidgetHandler().create_widget(
            summary_type, dashboard, title="订单总数"
        )
    print("DASHBOARD", dashboard.id, data_source.id, widget.id, summary.id)

    # --- 自动化 ---
    automation_app = Application.objects.filter(
        name="订单自动化", workspace=workspace
    ).first()
    if automation_app is None:
        automation_app = handler.create_application(
            admin, workspace, "automation", name="订单自动化"
        )
    from baserow.contrib.automation.models import Automation

    automation = Automation.objects.get(id=automation_app.id)
    workflow = AutomationWorkflow.objects.filter(automation=automation).first()
    if workflow is None:
        workflow = AutomationWorkflowHandler().create_workflow(automation, "新订单记录")
    trigger_type = automation_node_type_registry.get("local_baserow_rows_created")
    trigger_service = ServiceHandler().create_service(
        service_type_registry.get("local_baserow_rows_created"),
        table_id=orders.id,
    )
    trigger = AutomationNodeHandler().create_node(
        trigger_type, workflow, service=trigger_service
    )

    log_table = Database.objects.get(
        name="销售数据", workspace=workspace
    ).table_set.filter(name="订单日志").first()
    if log_table is None:
        from baserow.contrib.database.table.handler import TableHandler

        log_table, _ = TableHandler().create_table(
            admin,
            Database.objects.get(name="销售数据", workspace=workspace),
            name="订单日志",
            data=[
                ["订单号", "状态", "记录时间"],
                ["SO-2026-001", "已完成", "2026-01-05 10:00"],
            ],
            first_row_header=True,
        )
    service = ServiceHandler().create_service(
        service_type_registry.get("local_baserow_upsert_row"),
        table_id=log_table.id,
        values={},
    )
    action_type = automation_node_type_registry.get("local_baserow_create_row")
    existing_action = workflow.automation_workflow_nodes.filter(
        service=service
    ).first()
    if existing_action is None:
        action = AutomationNodeHandler().create_node(
            action_type, workflow, service=service
        )
    else:
        action = existing_action
    print("AUTOMATION", workflow.id, trigger.id, action.id)

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    print("F_DEMO2_DONE")


main()
