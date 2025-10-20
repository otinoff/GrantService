#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find all SQLite usage in web-admin pages
"""

import re
from pathlib import Path

web_admin = Path(__file__).parent / "web-admin"
pages_dir = web_admin / "pages"

print("="*70)
print("FINDING SQLITE USAGE IN WEB-ADMIN")
print("="*70)

pages = list(pages_dir.glob("*.py"))

total_issues = 0

for page in pages:
    with open(page, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Find get_db_connection() calls
    issues = []
    for i, line in enumerate(lines, 1):
        if 'get_db_connection()' in line and 'import' not in line:
            issues.append((i, line.strip()))

    if issues:
        # Remove emoji from filename for display
        display_name = page.name.encode('ascii', errors='ignore').decode('ascii')
        if not display_name.strip():
            display_name = f"Page_{len(issues)}_issues"

        print(f"\n[FILE] {display_name or page.stem}")
        print(f"   Found {len(issues)} SQLite calls:")
        for line_num, line_text in issues:
            print(f"   Line {line_num}: {line_text[:80]}")
        total_issues += len(issues)

print("\n" + "="*70)
print(f"TOTAL: {total_issues} SQLite calls found across {len(pages)} pages")
print("="*70)

# Also check utils/database.py
utils_db = web_admin / "utils" / "database.py"
if utils_db.exists():
    with open(utils_db, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'sqlite3.connect' in content:
        print("\n[WARNING] utils/database.py still uses SQLite!")
        print("   get_db_connection() returns SQLite connection")
    else:
        print("\n[OK] utils/database.py uses PostgreSQL")
