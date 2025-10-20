#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from utils.postgres_helper import execute_query

result = execute_query("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'sessions'
    ORDER BY ordinal_position
""")

print("Sessions table columns:")
print("="*60)
for row in result:
    print(f"  {row['column_name']:30s} - {row['data_type']}")
