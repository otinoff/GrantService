#!/usr/bin/env python3
"""
Headless browser test for GrantService Admin Panel
Checks all pages after deployment

Author: Deployment Manager Agent
Created: 2025-10-03
Version: 1.0.0
"""
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "https://grantservice.onff.ru"

PAGES_TO_CHECK = [
    {"name": "Dashboard", "url": "/", "expect": "GrantService"},
    {"name": "Grants", "url": "/📄_Гранты", "expect": "Управление грантами"},
    {"name": "Users", "url": "/👥_Пользователи", "expect": "Пользователи"},
    {"name": "Analytics", "url": "/📊_Аналитика", "expect": "Аналитика"},
    {"name": "Agents", "url": "/🤖_Агенты", "expect": "Агенты"},
    {"name": "Settings", "url": "/⚙️_Настройки", "expect": "Настройки"}
]

def check_page(page, url, expected_text):
    """Check single page"""
    try:
        # Navigate to page
        response = page.goto(url, timeout=15000, wait_until="networkidle")

        if response.status != 200:
            return False, f"HTTP {response.status}"

        # Wait for content to load
        page.wait_for_timeout(2000)

        # Check if expected text is present
        content = page.content()
        if expected_text not in content:
            return False, f"Expected text '{expected_text}' not found"

        # Check for error messages
        if "Error" in content or "error" in content.lower():
            # Some errors might be acceptable (like empty data messages)
            # But check for critical errors
            if "ImportError" in content or "ModuleNotFoundError" in content:
                return False, "Import error detected"

        return True, "OK"

    except PlaywrightTimeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def run_headless_tests():
    """Run all headless tests"""
    print("=" * 60)
    print("🌐 Headless Browser Tests - GrantService Admin")
    print("=" * 60)
    print()

    results = []

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="GrantService-Deployment-Checker/1.0"
        )
        page = context.new_page()

        # Test each page
        for page_info in PAGES_TO_CHECK:
            name = page_info["name"]
            url = BASE_URL + page_info["url"]
            expected = page_info["expect"]

            print(f"Testing {name}... ", end="", flush=True)

            success, message = check_page(page, url, expected)
            results.append({
                "name": name,
                "url": url,
                "success": success,
                "message": message
            })

            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")

        browser.close()

    # Summary
    print()
    print("=" * 60)
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed

    print(f"Results: {passed}/{total} passed, {failed} failed")

    if failed > 0:
        print()
        print("Failed pages:")
        for r in results:
            if not r["success"]:
                print(f"  ❌ {r['name']}: {r['message']}")
        print("=" * 60)
        return 1
    else:
        print("✅ All pages working correctly!")
        print("=" * 60)
        return 0

if __name__ == "__main__":
    sys.exit(run_headless_tests())
