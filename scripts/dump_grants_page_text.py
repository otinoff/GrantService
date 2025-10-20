#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вывести весь текст со страницы Грантов для отладки
"""

import sys
import time
import subprocess
import signal
from pathlib import Path
from playwright.sync_api import sync_playwright

# Конфигурация
PORT = 8554
project_root = Path(__file__).parent.parent
PAGE_FILE = project_root / "web-admin" / "pages" / "📄_Гранты.py"


def main():
    print("Starting Streamlit...")

    process = subprocess.Popen(
        ["streamlit", "run", str(PAGE_FILE), "--server.port", str(PORT), "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    time.sleep(20)

    try:
        url = f"http://localhost:{PORT}"
        print(f"Opening {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=45000, wait_until="networkidle")
            page.wait_for_timeout(8000)

            # Получаем весь текст
            text = page.inner_text("body")

            print("\n" + "="*70)
            print("PAGE TEXT CONTENT:")
            print("="*70)
            print(text[:2000])  # Первые 2000 символов
            print("="*70)

            # Ищем ключевые слова
            keywords = ["заяв", "grant", "AN-", "Otinoff", "22", "всего", "total"]
            print("\nSearching for keywords:")
            for kw in keywords:
                if kw.lower() in text.lower():
                    print(f"  [FOUND] '{kw}'")
                else:
                    print(f"  [NOT FOUND] '{kw}'")

            browser.close()

    finally:
        if sys.platform == "win32":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()
        process.wait(timeout=5)

        print("\nStreamlit stopped")


if __name__ == "__main__":
    main()
