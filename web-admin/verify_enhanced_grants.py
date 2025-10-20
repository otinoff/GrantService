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
import json

print("="*70)
print("ENHANCED GRANTS VERIFICATION")
print("="*70)

# Count by status
status_counts = execute_query("""
    SELECT status, COUNT(*) as cnt
    FROM grants
    GROUP BY status
    ORDER BY cnt DESC
""")

print("\n📊 Grant Status Distribution:")
for row in status_counts:
    print(f"  {row['status']}: {row['cnt']}")

# Count enhanced grants
enhanced = execute_query("""
    SELECT COUNT(*) as cnt
    FROM grants
    WHERE llm_provider = 'enhanced_writer'
""")
print(f"\n✅ Enhanced Writer Grants: {enhanced[0]['cnt']}")

# Check sample grant
sample = execute_query("""
    SELECT
        grant_id,
        grant_title,
        LENGTH(grant_content) as content_length,
        grant_sections,
        status,
        created_at
    FROM grants
    WHERE llm_provider = 'enhanced_writer'
    ORDER BY created_at DESC
    LIMIT 1
""")

if sample:
    grant = sample[0]
    print(f"\n📄 Sample Enhanced Grant:")
    print(f"  ID: {grant['grant_id']}")
    print(f"  Title: {grant['grant_title']}")
    print(f"  Length: {grant['content_length']} characters")
    print(f"  Status: {grant['status']}")
    print(f"  Created: {grant['created_at']}")

    sections = grant['grant_sections']
    if isinstance(sections, dict):
        print(f"\n  Sections ({len(sections)} total):")
        for key in sections.keys():
            print(f"    ✓ {key}")

# Verify visibility on Grants page
ready_grants = execute_query("""
    SELECT COUNT(*) as cnt
    FROM grants
    WHERE status = 'completed'
""")

print(f"\n📄 Visible on 'Готовые гранты' page: {ready_grants[0]['cnt']}")

print("\n" + "="*70)
print("✅ VERIFICATION COMPLETE")
print("="*70)
print("\nNext step: Refresh admin panel to see all 29 grants")
