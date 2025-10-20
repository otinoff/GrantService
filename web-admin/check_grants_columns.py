#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except:
        pass

from utils.postgres_helper import execute_query

result = execute_query("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'grants'
    ORDER BY ordinal_position
""")

print("Колонки таблицы grants:")
for r in result:
    print(f"  - {r['column_name']}")
