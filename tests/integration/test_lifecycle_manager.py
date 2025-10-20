#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Grant Lifecycle Manager with real data
"""
import sys
from pathlib import Path

# Add web-admin to path
sys.path.insert(0, str(Path(__file__).parent / 'web-admin'))

from utils.grant_lifecycle_manager import GrantLifecycleManager, get_lifecycle_summary
from utils.artifact_exporter import export_artifact
from utils.postgres_helper import execute_query

# Find a real anketa_id from the database
print("=" * 80)
print("TESTING GRANT LIFECYCLE MANAGER")
print("=" * 80)
print()

# Use a known anketa_id from previous tests
# Query: SELECT anketa_id FROM grants WHERE anketa_id LIKE 'AN-%' LIMIT 1
test_anketa_id = "AN-20250905-Natalia_bruzzzz-001"  # Known good anketa_id

print(f"Using known anketa_id: {test_anketa_id}")
print("-" * 80)
print(f"\nTesting with anketa_id: {test_anketa_id}")
print("=" * 80)

# Test GrantLifecycleManager
manager = GrantLifecycleManager(test_anketa_id)
lifecycle_data = manager.get_all_artifacts()

if not lifecycle_data:
    print("[ERROR] Failed to get lifecycle data!")
    sys.exit(1)

print("\n[OK] Lifecycle data retrieved successfully!")
print(f"  Anketa ID: {lifecycle_data.get('anketa_id')}")
print(f"  Current Stage: {lifecycle_data.get('current_stage')}")
print(f"  Progress: {lifecycle_data.get('progress'):.0f}%")
print()

# Check each stage
artifacts = lifecycle_data.get('artifacts', {})
print("Stage Status:")
for stage_name, artifact in artifacts.items():
    status = artifact.get('status', 'unknown')
    mark = '[OK]' if status == 'completed' else '[ ]'
    print(f"  {mark} {stage_name.upper()}: {status}")

print()
print("-" * 80)

# Test exporters
print("\nTesting Artifact Exporters:")
print("-" * 80)

# TXT export
print("\n1. Testing TXT export...")
try:
    txt_data = export_artifact(lifecycle_data, 'txt')
    print(f"  [OK] TXT export successful ({len(txt_data)} bytes)")
    print(f"  Preview (first 200 chars):")
    preview = txt_data.decode('utf-8')[:200] if isinstance(txt_data, bytes) else str(txt_data)[:200]
    print(f"  {preview}...")
except Exception as e:
    print(f"  [ERROR] TXT export failed: {e}")

# PDF export
print("\n2. Testing PDF export...")
try:
    pdf_data = export_artifact(lifecycle_data, 'pdf')
    print(f"  [OK] PDF export successful ({len(pdf_data)} bytes)")
except Exception as e:
    print(f"  [ERROR] PDF export failed: {e}")

# DOCX export
print("\n3. Testing DOCX export...")
try:
    docx_data = export_artifact(lifecycle_data, 'docx')
    print(f"  [OK] DOCX export successful ({len(docx_data)} bytes)")
except Exception as e:
    print(f"  [ERROR] DOCX export failed: {e}")

print()
print("=" * 80)
print("[OK] ALL TESTS COMPLETED")
print("=" * 80)
