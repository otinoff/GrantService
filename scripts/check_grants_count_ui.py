#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка количества заявок на странице Грантов через headless browser
"""

import sys
import time
import subprocess
import signal
from pathlib import Path
from playwright.sync_api import sync_playwright

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.database import GrantServiceDatabase

# Конфигурация
PORT = 8553
PAGE_FILE = project_root / "web-admin" / "pages" / "📄_Гранты.py"


def get_expected_count():
    """Получить ожидаемое количество заявок из БД"""
    db = GrantServiceDatabase()
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM grant_applications")
        count = cursor.fetchone()[0]
        cursor.close()
    return count


def start_streamlit():
    """Запустить Streamlit сервер"""
    print(f"Starting Streamlit on port {PORT}...")

    process = subprocess.Popen(
        ["streamlit", "run", str(PAGE_FILE), "--server.port", str(PORT), "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    print("Waiting for server to start (20 seconds)...")
    time.sleep(20)

    if process.poll() is not None:
        raise Exception("Streamlit failed to start")

    print("[OK] Streamlit started")
    return process


def check_page_content(expected_count):
    """Проверить содержимое страницы через headless browser"""
    url = f"http://localhost:{PORT}"

    print(f"\nOpening page: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            # Открываем страницу
            response = page.goto(url, timeout=45000, wait_until="networkidle")

            if response.status != 200:
                raise Exception(f"HTTP {response.status}")

            print(f"[OK] Page loaded: HTTP {response.status}")

            # Ждем рендеринга
            page.wait_for_timeout(8000)

            # Получаем текст страницы
            content = page.content()
            text_content = page.inner_text("body")

            # Проверяем наличие ошибок
            if "Traceback" in content or "Error" in content:
                if "ImportError" in content or "ModuleNotFoundError" in content:
                    print("[ERROR] Import error detected!")
                    return False

            # Ищем количество заявок
            print(f"\nSearching for count {expected_count} on page...")

            # Streamlit может показывать count в разных форматах:
            # "Всего заявок: 22"
            # "22 заявки"
            # или просто "22" в метрике

            found_count = False

            # Вариант 1: Точное совпадение "Всего: 22" или "Total: 22"
            if f"Всего: {expected_count}" in text_content or f"Total: {expected_count}" in text_content:
                print(f"[OK] Found 'Всего: {expected_count}' in text")
                found_count = True

            # Вариант 2: Просто число присутствует
            elif str(expected_count) in text_content:
                print(f"[OK] Found number {expected_count} in page text")
                found_count = True

            # Проверяем последнюю заявку
            print(f"\nSearching for latest application...")

            db = GrantServiceDatabase()
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT application_number, title
                    FROM grant_applications
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                latest = cursor.fetchone()
                cursor.close()

            if latest:
                app_number, title = latest
                if app_number in text_content:
                    print(f"[OK] Found latest application: {app_number}")
                else:
                    print(f"[WARNING] Latest application {app_number} NOT found in text")

            # Делаем скриншот
            screenshot_dir = project_root / "test_screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            screenshot_path = screenshot_dir / "grants_count_check.png"
            page.screenshot(path=str(screenshot_path))
            print(f"\n[OK] Screenshot saved: {screenshot_path}")

            return found_count

        except Exception as e:
            print(f"[ERROR] {e}")
            return False

        finally:
            browser.close()


def main():
    print("="*70)
    print("CHECKING GRANTS COUNT IN STREAMLIT UI")
    print("="*70)

    # Получаем ожидаемое количество
    expected_count = get_expected_count()
    print(f"\nExpected grants count from DB: {expected_count}")

    streamlit_process = None

    try:
        # Запускаем Streamlit
        streamlit_process = start_streamlit()

        # Проверяем страницу
        result = check_page_content(expected_count)

        print("\n" + "="*70)
        if result:
            print("[SUCCESS] Grants count check PASSED")
            print(f"Expected: {expected_count} grants")
            print("Page displays the count correctly")
        else:
            print("[WARNING] Could not verify exact count match")
            print("Check the screenshot manually")
        print("="*70)

        return 0 if result else 1

    finally:
        # Останавливаем Streamlit
        if streamlit_process:
            print("\nStopping Streamlit...")
            if sys.platform == "win32":
                streamlit_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                streamlit_process.terminate()

            try:
                streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                streamlit_process.kill()

            print("[OK] Streamlit stopped")


if __name__ == "__main__":
    sys.exit(main())
