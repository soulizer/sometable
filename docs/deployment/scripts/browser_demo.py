#!/usr/bin/env python3
"""演示数据截图：销售管理工作区、数据库、仪表盘、自动化。"""
import sys

from playwright.sync_api import sync_playwright

BASE = "https://sometable.com"
EMAIL = "audit-browser@access126.com"
PASSWORD = "Audit-Browser-2026!"
OUT = "docs/deployment/audit/screenshots"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            base_url=BASE,
            locale="zh-CN",
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto("/login/", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.fill('input[type="email"]', EMAIL)
        page.fill('input[type="password"]', PASSWORD)
        with page.expect_response(lambda r: "token-auth" in r.url, timeout=30000):
            page.click("form button")
        page.wait_for_url("**/all-workspaces", timeout=30000)
        page.wait_for_timeout(1000)

        targets = [
            ("demo-1-workspace", "/workspace/178"),
            ("demo-2-orders", "/database/300/table/907"),
            ("demo-3-dashboard", "/dashboard/288"),
            ("demo-4-automation", "/automation/291/workflow/31"),
        ]
        for name, path in targets:
            page.goto(path, wait_until="networkidle")
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{OUT}/{name}.png", full_page=False)
            print(name, page.url, "errors", len(errors))

        browser.close()
    print("DEMO_SHOTS_DONE", errors[:5])


if __name__ == "__main__":
    sys.exit(main())
