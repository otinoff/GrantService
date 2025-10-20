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

# Get latest grant
result = execute_query("""
    SELECT grant_id, anketa_id, grant_title, grant_content, grant_sections
    FROM grants
    ORDER BY created_at DESC
    LIMIT 1
""")

if result:
    grant = result[0]

    print("="*70)
    print("SAMPLE GENERATED GRANT (Enhanced Writer v2.0)")
    print("="*70)
    print(f"Grant ID: {grant['grant_id']}")
    print(f"Anketa ID: {grant['anketa_id']}")
    print(f"Title: {grant['grant_title']}")
    print("="*70)
    print()
    print(grant['grant_content'])

    # Save to file
    filename = f"SAMPLE_GRANT_{grant['anketa_id']}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(grant['grant_content'])

    print(f"\n[OK] Grant saved to: {filename}")
else:
    print("[WARN] No grants found")
