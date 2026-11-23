#!/usr/bin/env python3
"""无头浏览器冒烟测试：登录、侧栏、管理设置、数据库视图。

用法：
    /tmp/opencode/pw/bin/python docs/deployment/scripts/browser_smoke.py
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "https://sometable.com"
EMAIL = "audit-browser@access126.com"
PASSWORD = "Audit-Browser-2026!"

errors = []
requests_failed = []


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            base_url=BASE,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            ignore_https_errors=True,
        )
        page = context.new_page()

        def handle_api(route):
            request = route.request
            url = request.url
            headers = dict(request.headers)
            headers["host"] = "sometable.com"
            try:
                response = route.fetch(
                    url=url,
                    headers=headers,
                    method=request.method,
                    post_data=request.post_data,
                )
                route.fulfill(response=response)
            except Exception:
                route.abort()

        page.route("**/api/**", handle_api)
        page.on("console", lambda msg: errors.append(f"console.{msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
        page.on("requestfailed", lambda req: requests_failed.append(f"{req.url} {req.failure}"))
        page.on(
            "response",
            lambda res: errors.append(f"http {res.status} {res.url}")
            if res.status >= 400
            else None,
        )

        # 登录
        page.goto("/login/", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path="docs/deployment/audit/screenshots/01-login.png")
        page.fill('input[type="email"]', EMAIL)
        page.fill('input[type="password"]', PASSWORD)
        with page.expect_response(
            lambda r: "token-auth" in r.url, timeout=30000
        ) as response_info:
            page.click("form button")
        print("login status:", response_info.value.status)
        page.wait_for_url("**/all-workspaces", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="docs/deployment/audit/screenshots/02-after-login.png")

        # 侧栏工作区菜单（验证 ref 判空修复）
        selector = page.locator(".sidebar__workspaces-selector").first
        if selector.count() == 0:
            errors.append("sidebar selector not found")
        else:
            selector.click()
            time.sleep(1)
            menu = page.locator(".context__menu").first
            print("workspace menu visible:", menu.is_visible())
            page.screenshot(path="docs/deployment/audit/screenshots/03-workspace-menu.png")
            page.keyboard.press("Escape")

        # 管理设置
        page.goto("/admin/settings", wait_until="networkidle")
        time.sleep(2)
        print("admin url:", page.url)
        page.screenshot(path="docs/deployment/audit/screenshots/04-admin-settings.png")
        body = page.content()
        print("admin storage section:", "文件存储" in body)
        print("admin branding section:", "品牌定制" in body)
        print("admin favicon section:", "网站图标" in body)

        # 数据扫描
        page.goto("/admin/data-scanner/scans", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path="docs/deployment/audit/screenshots/05-data-scanner.png")
        print("data scanner page has content:", len(page.content()) > 1000)

        # 审计工作区（如果可见）
        page.goto("/admin/audit-log", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path="docs/deployment/audit/screenshots/05-audit-log.png")
        print("audit log page has table:", page.locator("table").count() > 0)

        # 数据库视图
        page.goto("/database/281/table/897", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path="docs/deployment/audit/screenshots/06-workspace.png")

        browser.close()

    print("CONSOLE_ERRORS", json.dumps(errors[:20], ensure_ascii=False))
    print("REQUEST_FAILED", json.dumps(requests_failed[:20], ensure_ascii=False))
    print("BROWSER_SMOKE_DONE errors=", len(errors), "failed_requests=", len(requests_failed))


if __name__ == "__main__":
    sys.exit(main())
