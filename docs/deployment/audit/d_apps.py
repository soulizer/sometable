# 批次 D：应用（构建器/仪表盘/自动化/智能体）创建与权限
from django.contrib.auth import get_user_model

from baserow.contrib.agent.models import AgentApplication
from baserow.contrib.automation.models import Automation
from baserow.contrib.automation.workflows.handler import AutomationWorkflowHandler
from baserow.contrib.automation.workflows.models import AutomationWorkflow
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import HeadingElement
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.dashboard.handler import DashboardHandler
from baserow.contrib.dashboard.models import Dashboard
from baserow.contrib.dashboard.widgets.handler import WidgetHandler
from baserow.contrib.dashboard.widgets.registries import widget_type_registry
from baserow.core.exceptions import PermissionDenied
from baserow.core.handler import CoreHandler
from baserow.core.models import Application, Workspace

User = get_user_model()
WORKSPACE_NAME = "审计-工作区"
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


def get_or_create_app(handler, user, workspace, type_name, name):
    app = Application.objects.filter(name=name, workspace=workspace).first()
    if app is None:
        app = handler.create_application(user, workspace, type_name)
        app.name = name
        app.save(update_fields=["name"])
        print("created", type_name, app.id)
    return app


def main():
    handler = CoreHandler()
    builder = get_user("builder")
    viewer = get_user("viewer")
    workspace = Workspace.objects.get(name=WORKSPACE_NAME)

    check(
        "应用-查看者不能创建",
        lambda: handler.create_application(viewer, workspace, "builder", name="越权应用"),
        raises=PermissionDenied,
    )

    builder_app = get_or_create_app(handler, builder, workspace, "builder", "审计-应用")
    dashboard_app = get_or_create_app(
        handler, builder, workspace, "dashboard", "审计-仪表盘应用"
    )
    automation_app = get_or_create_app(
        handler, builder, workspace, "automation", "审计-自动化应用"
    )
    agent_app = get_or_create_app(handler, builder, workspace, "agent", "审计-智能体应用")

    # --- 构建器 ---
    builder_app = Builder.objects.get(id=builder_app.id)
    page = Page.objects.filter(builder=builder_app, name="审计页面").first()
    if page is None:
        page = PageHandler().create_page(builder_app, "审计页面", "/audit")
    check("构建器-页面创建", lambda: page.id is not None)
    heading_type = element_type_registry.get("heading")
    if not HeadingElement.objects.filter(page=page).exists():
        ElementHandler().create_element(
            heading_type, page, values={"value": "审计标题"}
        )
    check(
        "构建器-元素创建",
        lambda: HeadingElement.objects.filter(page=page).exists(),
    )

    # --- 仪表盘 ---
    dashboard = Dashboard.objects.get(id=dashboard_app.id)
    summary_type = widget_type_registry.get("summary")
    if not dashboard.widget_set.exists():
        WidgetHandler().create_widget(summary_type, dashboard, title="审计汇总")
    check("仪表盘-组件创建", lambda: dashboard.widget_set.exists())
    check(
        "仪表盘-图表类型可用",
        lambda: widget_type_registry.get("chart") is not None
        and widget_type_registry.get("pie_chart") is not None,
    )

    # --- 自动化 ---
    automation = Automation.objects.get(id=automation_app.id)
    workflow = AutomationWorkflow.objects.filter(
        automation=automation, name="审计工作流"
    ).first()
    if workflow is None:
        workflow = AutomationWorkflowHandler().create_workflow(
            automation, "审计工作流"
        )
    check("自动化-工作流创建", lambda: workflow.id is not None)

    # --- 智能体 ---
    agent = AgentApplication.objects.get(id=agent_app.id)
    check("智能体-应用创建", lambda: agent.id is not None)

    # --- 回收站 ---
    check(
        "应用-查看者不能删除",
        lambda: handler.delete_application(viewer, builder_app),
        raises=PermissionDenied,
    )
    check(
        "应用-构建者删除入回收站",
        lambda: handler.delete_application(builder, agent_app) is None,
    )
    check(
        "应用-回收站外不可见",
        lambda: Application.objects.filter(id=agent_app.id).exists() is False,
    )

    for status, name, detail in RESULTS:
        print(f"[{status}] {name} {detail}")
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"D_APPS_OK total={len(RESULTS)} failed={len(failed)}")


main()
