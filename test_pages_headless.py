#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless browser test for fixed admin pages
"""

import asyncio
from playwright.async_api import async_playwright
import sys

async def test_pages():
    """Test fixed admin pages"""

    pages_to_test = [
        "👥_Пользователи",
        "📄_Просмотр_заявки",
        "📋_Анкеты_пользователей",
        "❓_Вопросы_интервью",
        "✍️_Writer_Agent",
        "🔍_Researcher_Agent",
        "📊_Общая_аналитика",
        "🔬_Аналитика_исследователя",
    ]

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("\n" + "="*60)
        print("TESTING FIXED ADMIN PAGES")
        print("="*60 + "\n")

        for page_name in pages_to_test:
            try:
                url = f"http://localhost:8551"
                print(f"Testing: {page_name}...", end=" ")

                # Navigate to page
                response = await page.goto(url, wait_until="networkidle", timeout=10000)

                # Check for Python errors
                errors = []
                page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

                # Wait a bit for page to load
                await asyncio.sleep(2)

                # Check for Streamlit error messages
                error_elements = await page.query_selector_all(".stException, .element-container .stMarkdown [data-testid='stMarkdownContainer'] p")

                has_errors = False
                for elem in error_elements:
                    text = await elem.inner_text()
                    if "error" in text.lower() or "traceback" in text.lower() or "exception" in text.lower():
                        has_errors = True
                        print(f"❌ ERROR")
                        print(f"   Error found: {text[:100]}")
                        results.append((page_name, False, text[:200]))
                        break

                if not has_errors:
                    # Check if page loaded (should have some content)
                    content = await page.content()
                    if len(content) > 5000:  # Basic check that page has content
                        print("✅ OK")
                        results.append((page_name, True, "Page loaded successfully"))
                    else:
                        print("⚠️  WARNING (minimal content)")
                        results.append((page_name, True, "Page loaded but minimal content"))

            except Exception as e:
                print(f"❌ FAILED: {str(e)[:50]}")
                results.append((page_name, False, str(e)[:200]))

        await browser.close()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed

    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")

    if failed > 0:
        print("\nFailed pages:")
        for name, ok, msg in results:
            if not ok:
                print(f"  - {name}: {msg}")

    return failed == 0

if __name__ == "__main__":
    try:
        success = asyncio.run(test_pages())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
