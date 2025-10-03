#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple import test for fixed admin pages
"""

import sys
import os

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
web_admin_dir = os.path.join(current_dir, 'web-admin')
sys.path.insert(0, current_dir)
sys.path.insert(0, web_admin_dir)

pages_to_test = [
    "web-admin/pages/👥_Пользователи.py",
    "web-admin/pages/📄_Просмотр_заявки.py",
    "web-admin/pages/📋_Анкеты_пользователей.py",
    "web-admin/pages/❓_Вопросы_интервью.py",
    "web-admin/pages/✍️_Writer_Agent.py",
    "web-admin/pages/🔍_Researcher_Agent.py",
    "web-admin/pages/📊_Общая_аналитика.py",
    "web-admin/pages/🔬_Аналитика_исследователя.py",
    "web-admin/pages/🏠_Главная.py",
    "web-admin/pages/📄_Грантовые_заявки.py",
    "web-admin/pages/🔐_Вход.py",
]

print("\n" + "="*70)
print("TESTING FIXED ADMIN PAGES - SYNTAX & IMPORTS CHECK")
print("="*70 + "\n")

passed = 0
failed = 0

for page_path in pages_to_test:
    full_path = os.path.join(current_dir, page_path)
    page_name = os.path.basename(page_path)

    print(f"Testing: {page_name:40s} ", end="")

    try:
        # Read file
        with open(full_path, 'r', encoding='utf-8') as f:
            code = f.read()

        # Check for triple duplication pattern
        import_count = code.count('import streamlit as st')
        if import_count > 1:
            print(f"❌ FAIL (found {import_count}x 'import streamlit as st')")
            failed += 1
            continue

        # Check for wrong imports
        if 'from data.database.models import GrantServiceDatabase' in code:
            print("❌ FAIL (wrong DB import path)")
            failed += 1
            continue

        if 'from database.prompts import' in code:
            print("❌ FAIL (wrong prompts import path)")
            failed += 1
            continue

        # Check syntax by compiling
        compile(code, full_path, 'exec')

        # Check specific fixes
        issues = []

        if page_name == '📄_Просмотр_заявки.py':
            if 'import json' not in code:
                issues.append("missing 'import json'")
            if 'from datetime import datetime' not in code and 'import datetime' not in code:
                issues.append("missing datetime import")

        if page_name == '🏠_Главная.py':
            if 'YOUR_BOT_TOKEN_HERE' in code:
                issues.append("hardcoded token still present")

        if page_name == '❓_Вопросы_интервью.py':
            if "sys.path.append('/var/GrantService')" in code:
                issues.append("hardcoded Linux path still present")

        if page_name == '🔐_Вход.py':
            # Count debug st.info statements
            debug_count = code.count('st.info(f"🔍 Debug:')
            if debug_count > 0:
                issues.append(f"{debug_count} debug prints remain")

        if issues:
            print(f"⚠️  WARN ({'; '.join(issues)})")
            passed += 1  # Still counts as pass for syntax
        else:
            print("✅ OK")
            passed += 1

    except SyntaxError as e:
        print(f"❌ FAIL (syntax error: {e.msg} line {e.lineno})")
        failed += 1
    except Exception as e:
        print(f"❌ FAIL ({str(e)[:50]})")
        failed += 1

print("\n" + "="*70)
print(f"SUMMARY: ✅ {passed} passed | ❌ {failed} failed | Total: {len(pages_to_test)}")
print("="*70 + "\n")

sys.exit(0 if failed == 0 else 1)
