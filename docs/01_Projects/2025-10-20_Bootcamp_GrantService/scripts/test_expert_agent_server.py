#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Expert Agent with SERVER Qdrant (5.35.88.251:6333)
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add paths
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "expert_agent"))

# Setup database
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'
os.environ['PGDATABASE'] = 'grantservice'
os.environ['PGUSER'] = 'postgres'
os.environ['PGPASSWORD'] = 'root'

print("=" * 80)
print("🔍 TESTING EXPERT AGENT WITH SERVER QDRANT")
print("=" * 80)
print()

print("Initializing Expert Agent...")
print(f"  PostgreSQL: localhost:5432/grantservice")
print(f"  Qdrant: 5.35.88.251:6333")
print()

try:
    from expert_agent import ExpertAgent

    # Initialize with SERVER Qdrant
    expert = ExpertAgent(
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="grantservice",
        postgres_user="postgres",
        postgres_password="root",
        qdrant_host="5.35.88.251",  # SERVER!
        qdrant_port=6333
    )

    print("✅ Expert Agent initialized successfully!")
    print()

    # Test query
    test_query = "Какие общие требования к заполнению заявки на грант ФПГ?"
    print(f"Test query: {test_query}")
    print()

    print("Searching in knowledge_sections...")
    results = expert.query_knowledge(test_query, top_k=3)

    print()
    print(f"✅ Found {len(results)} results:")
    print()

    for i, result in enumerate(results, 1):
        print(f"{i}. {result}")
        print()

    print("=" * 80)
    print("🎉 TEST PASSED! Expert Agent works with SERVER Qdrant!")
    print("=" * 80)

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
