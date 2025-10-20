#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Researcher Agent with WebSearch on Valeria's anketa
"""
import sys
import os
from pathlib import Path

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup paths
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir / 'web-admin'))
sys.path.insert(0, str(base_dir))
sys.path.insert(0, str(base_dir / 'data'))
sys.path.insert(0, str(base_dir / 'agents'))

print("=" * 80)
print("TEST: Researcher Agent with WebSearch")
print("=" * 80)

# Import database first
print("\n1. Importing Database...")
try:
    from data.database import db, session_manager
    print("OK: Database imported")
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)

# Check Valeria's anketa
print("\n2. Checking Valeria's anketa...")
ANKETA_ID = 'VALERIA_PTSD_888465306'

try:
    anketa = db.get_session_by_anketa_id(ANKETA_ID)
    if not anketa:
        print(f"ERROR: Anketa {ANKETA_ID} not found!")
        sys.exit(1)

    print(f"OK: Anketa found: {ANKETA_ID}")
    print(f"   Status: anketa exists")
except Exception as e:
    print(f"ERROR: Failed to get anketa: {e}")
    sys.exit(1)

# Import Researcher Agent
print("\n3. Importing Researcher Agent...")
try:
    from agents.researcher_agent import ResearcherAgent
    print("OK: ResearcherAgent imported")
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)

# Create Researcher Agent
print("\n4. Creating Researcher Agent...")
try:
    researcher = ResearcherAgent(db, llm_provider="claude_code")
    print("OK: Researcher Agent created")
except Exception as e:
    print(f"ERROR: Agent creation failed: {e}")
    sys.exit(1)

# Run research
print("\n5. Running research...")
print(f"   Anketa ID: {ANKETA_ID}")
print("   This will take ~30-60 seconds (3 WebSearch queries)")
print()

try:
    result = researcher.research_anketa(ANKETA_ID)

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if result.get('status') == 'success':
        print("SUCCESS: Research completed!")
        print()
        print(f"Research ID: {result.get('research_id')}")
        print(f"Anketa ID: {result.get('anketa_id')}")
        print(f"Provider: {result.get('provider_used')}")

        # Show metadata
        results_data = result.get('results', {})
        metadata = results_data.get('metadata', {})

        print()
        print("Metadata:")
        print(f"   Queries executed: {metadata.get('total_queries', 0)}")
        print(f"   Sources found: {metadata.get('sources_count', 0)}")
        print(f"   Version: {metadata.get('version', 'N/A')}")

        # Show block1 summary
        block1 = results_data.get('block1', {})
        queries = block1.get('queries', [])

        print()
        print(f"Block 1: {block1.get('block_name', 'N/A')}")
        print(f"   Queries: {len(queries)}")

        for i, q in enumerate(queries, 1):
            print()
            print(f"   {i}. {q.get('name', 'N/A')}")
            print(f"      Query: {q.get('query', '')[:80]}...")

            summary = q.get('result', {}).get('summary', '')
            if summary:
                # Show first 200 chars
                print(f"      Summary: {summary[:200]}...")

    else:
        print("FAILED: Research failed!")
        print(f"   Error: {result.get('message', 'Unknown error')}")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verify in database
print("\n" + "=" * 80)
print("6. Verifying in database...")
try:
    # Add web-admin to path for postgres_helper
    sys.path.insert(0, str(base_dir / 'web-admin'))
    from utils.postgres_helper import execute_query

    result = execute_query("""
        SELECT research_id, status, completed_at, llm_provider, model,
               LENGTH(research_results::text) as results_length
        FROM researcher_research
        WHERE anketa_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (ANKETA_ID,))

    if result and result[0]:
        row = result[0]
        print(f"OK: Record found in DB:")
        print(f"   Research ID: {row['research_id']}")
        print(f"   Status: {row['status']}")
        print(f"   Completed: {row['completed_at']}")
        print(f"   Provider: {row['llm_provider']}")
        print(f"   Model: {row['model']}")
        print(f"   Results size: {row['results_length']} bytes")

        if row['status'] == 'completed' and row['completed_at']:
            print()
            print("SUCCESS! Researcher works correctly!")
        else:
            print()
            print("WARNING: Status is not 'completed' or completed_at is empty")
    else:
        print("ERROR: Record NOT found in DB!")
except Exception as e:
    print(f"WARNING: Could not verify in DB: {e}")
    print("But this doesn't mean the research failed - check manually.")

print("\n" + "=" * 80)
print("TEST COMPLETED")
print("=" * 80)
