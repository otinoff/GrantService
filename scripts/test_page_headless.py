#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless browser testing for individual Streamlit pages
Tests page for Python errors and Streamlit exceptions
"""

import sys
import os
import asyncio
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    # Set UTF-8 output for Windows console
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Check if playwright is installed
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ ERROR: Playwright not installed")
    print("Install with: pip install playwright")
    print("Then run: python -m playwright install chromium")
    sys.exit(1)


async def test_streamlit_page(page_path: str, port: int = 8552):
    """
    Test a Streamlit page in headless mode

    Args:
        page_path: Path to the .py file (e.g., "web-admin/pages/🎯_Dashboard.py")
        port: Port to run Streamlit on (default: 8552)

    Returns:
        bool: True if test passed, False otherwise
    """

    page_file = Path(page_path)
    if not page_file.exists():
        print(f"❌ File not found: {page_path}")
        return False

    page_name = page_file.stem
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create screenshots directory
    screenshots_dir = Path("test_screenshots")
    screenshots_dir.mkdir(exist_ok=True)

    print(f"\n{'='*70}")
    print(f"🧪 TESTING PAGE: {page_name}")
    print(f"{'='*70}\n")

    # Start Streamlit server
    print(f"🚀 Starting Streamlit server on port {port}...")

    streamlit_cmd = [
        "streamlit", "run", str(page_file),
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.runOnSave", "false",
        "--browser.gatherUsageStats", "false"
    ]

    process = None
    try:
        # Start Streamlit in background
        process = subprocess.Popen(
            streamlit_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for server to start (max 15 seconds)
        print("⏳ Waiting for server to start...")
        server_started = False
        for i in range(30):
            time.sleep(0.5)
            if process.poll() is not None:
                # Process died
                stdout, stderr = process.communicate()
                print(f"❌ Streamlit failed to start!")
                print(f"\nSTDOUT:\n{stdout}")
                print(f"\nSTDERR:\n{stderr}")
                return False

            # Check if server is listening
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            if result == 0:
                server_started = True
                print("✅ Server started")
                break

        if not server_started:
            print(f"❌ Server didn't start within 15 seconds")
            return False

        # Give it a bit more time to fully initialize
        time.sleep(2)

        # Test with Playwright
        print(f"🌐 Opening page in headless browser...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Collect console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text()) if msg.type == "error" else None)

            # Navigate to page
            url = f"http://localhost:{port}"
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                print(f"✅ Page loaded (status: {response.status})")
            except Exception as e:
                print(f"❌ Failed to load page: {e}")
                await browser.close()
                return False

            # Wait for page to render
            print("⏳ Waiting for page to render (5 seconds)...")
            await asyncio.sleep(5)

            # Check for errors
            has_errors = False

            # 1. Check for Python traceback
            page_content = await page.content()

            if "Traceback (most recent call last)" in page_content:
                print("❌ Python traceback found in page!")
                has_errors = True
            else:
                print("✅ No Python traceback found")

            # 2. Check for Streamlit exceptions
            error_elements = await page.query_selector_all(".stException")
            if error_elements:
                print(f"❌ Found {len(error_elements)} Streamlit exception(s)!")
                for elem in error_elements[:3]:  # Show first 3
                    text = await elem.inner_text()
                    print(f"   Error: {text[:200]}")
                has_errors = True
            else:
                print("✅ No Streamlit exceptions found")

            # 3. Check for error messages in markdown
            markdown_errors = await page.query_selector_all(".stMarkdown:has-text('Error'), .stMarkdown:has-text('exception')")
            if markdown_errors:
                print(f"⚠️  Warning: Found {len(markdown_errors)} potential error message(s)")

            # 4. Check console errors
            if console_errors:
                print(f"⚠️  Warning: {len(console_errors)} console error(s)")
                for err in console_errors[:3]:
                    print(f"   Console: {err[:150]}")

            # Take screenshot
            screenshot_name = f"{page_name}_{timestamp}"
            if has_errors:
                screenshot_name += "_ERROR"
            screenshot_name += ".png"

            screenshot_path = screenshots_dir / screenshot_name
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")

            await browser.close()

            # Result
            print(f"\n{'='*70}")
            if has_errors:
                print("❌ TEST FAILED")
                print(f"{'='*70}\n")
                return False
            else:
                print("✅ TEST PASSED")
                print(f"{'='*70}\n")
                return True

    finally:
        # Stop Streamlit server
        if process:
            print("🛑 Stopping Streamlit server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ Server stopped")


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_page_headless.py <page_path>")
        print("Example: python test_page_headless.py web-admin/pages/🎯_Dashboard.py")
        sys.exit(1)

    page_path = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8552

    # Run test
    success = asyncio.run(test_streamlit_page(page_path, port))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
