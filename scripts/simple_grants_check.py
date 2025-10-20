#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая проверка: запустить админку через launcher.py и проверить через браузер
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.database import GrantServiceDatabase

print("="*70)
print("SIMPLE CHECK: Grants Count")
print("="*70)

# Получаем count из БД
db = GrantServiceDatabase()
with db.connect() as conn:
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM grant_applications")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT application_number, title, status, created_at
        FROM grant_applications
        ORDER BY created_at DESC
        LIMIT 5
    """)

    latest_apps = cursor.fetchall()
    cursor.close()

print(f"\n[DATABASE CHECK]")
print(f"Total grants: {total}")
print(f"\nLatest 5 applications:")
for app in latest_apps:
    print(f"  - {app[0]} | {app[1][:40]}... | {app[2]} | {app[3]}")

print("\n" + "="*70)
print("[NEXT STEPS]")
print("="*70)
print("1. Launch admin panel manually:")
print("   python launcher.py")
print("   or")
print("   admin.bat")
print("")
print("2. Open browser: http://localhost:8501")
print("")
print("3. Go to page '📄 Гранты' (Grants)")
print("")
print("4. Check that you see:")
print(f"   - Total grants count: {total}")
print(f"   - Latest application: {latest_apps[0][0]}")
print(f"   - User: Otinoff (Andrey Otinov)")
print("="*70)
