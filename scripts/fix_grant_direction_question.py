#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix grant direction question: move from 29 to 15 and activate
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'web-admin'))
os.environ['PYTHONIOENCODING'] = 'utf-8'

from utils.postgres_helper import execute_query, execute_update

print("=" * 80)
print("FIX: Grant Direction Question (29 → 15)")
print("=" * 80)

# Step 1: Find the grant direction question
print("\n[1/3] Finding grant direction question at position 29...")
result = execute_query("""
    SELECT id, question_number, question_text, is_active
    FROM interview_questions
    WHERE question_number = 29
""")

if result:
    for r in result:
        print(f"  Found: Q{r['question_number']} - {r['question_text'][:60]}...")
        print(f"  Active: {r['is_active']}")
        question_id = r['id']
else:
    print("  ❌ Question not found at position 29")
    sys.exit(1)

# Step 2: Move to position 15 and activate
print("\n[2/3] Moving to position 15 and activating...")
try:
    execute_update("""
        UPDATE interview_questions
        SET question_number = 15,
            is_active = true,
            updated_at = NOW()
        WHERE id = %s
    """, (question_id,))
    print("  ✅ Question moved to position 15 and activated")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Step 3: Verify
print("\n[3/3] Verifying active questions...")
active = execute_query("""
    SELECT question_number, LEFT(question_text, 60) as question
    FROM interview_questions
    WHERE is_active = true
    ORDER BY question_number
""")

if active:
    print(f"\n  Active questions: {len(active)}")
    for r in active:
        print(f"    {r['question_number']}. {r['question']}...")

print("\n" + "=" * 80)
print("✅ FIX COMPLETED")
print("=" * 80)
