#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load FPG knowledge base to PRODUCTION Qdrant
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import the existing load script
from expert_agent.load_fpg_knowledge import parse_fpg_knowledge_base, load_to_database
from expert_agent.expert_agent import ExpertAgent
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# PRODUCTION configuration
PROD_POSTGRES_HOST = "localhost"  # PostgreSQL через SSH tunnel или localhost
PROD_POSTGRES_PORT = 5432
PROD_POSTGRES_USER = "postgres"
PROD_POSTGRES_PASSWORD = "root"
PROD_POSTGRES_DB = "grantservice"

PROD_QDRANT_HOST = "5.35.88.251"  # Remote Qdrant
PROD_QDRANT_PORT = 6333

FPG_KB_FILE = "fpg_docs_2025/UNIFIED_KNOWLEDGE_BASE.md"

print("=" * 80)
print("LOADING FPG KNOWLEDGE BASE TO PRODUCTION")
print("=" * 80)

try:
    print(f"\n1. Initializing Expert Agent...")
    print(f"   PostgreSQL: {PROD_POSTGRES_HOST}:{PROD_POSTGRES_PORT}")
    print(f"   Qdrant: {PROD_QDRANT_HOST}:{PROD_QDRANT_PORT}")

    agent = ExpertAgent(
        postgres_host=PROD_POSTGRES_HOST,
        postgres_port=PROD_POSTGRES_PORT,
        postgres_user=PROD_POSTGRES_USER,
        postgres_password=PROD_POSTGRES_PASSWORD,
        postgres_db=PROD_POSTGRES_DB,
        qdrant_host=PROD_QDRANT_HOST,
        qdrant_port=PROD_QDRANT_PORT
    )
    print("   OK Agent initialized!")

    print(f"\n2. Parsing knowledge base: {FPG_KB_FILE}...")
    sections = parse_fpg_knowledge_base(FPG_KB_FILE)
    print(f"   OK Found {len(sections)} sections")

    print(f"\n3. Loading to database...")
    load_to_database(sections, agent)

    print("\n" + "=" * 80)
    print("SUCCESS! FPG KNOWLEDGE BASE LOADED")
    print("=" * 80)

    # Verify
    print("\n4. Verifying...")
    collections = agent.qdrant.get_collections()
    for coll in collections.collections:
        print(f"   - {coll.name}: {coll.points_count} points")

    print("\n5. Testing search...")
    results = agent.search_knowledge(
        query="Какие требования к бюджету проекта?",
        fund_name="fpg",
        limit=3
    )

    print("\nTop 3 results:")
    for i, r in enumerate(results, 1):
        print(f"\n  {i}. {r['section_name']}")
        print(f"     Score: {r['score']:.3f}")
        print(f"     Preview: {r['content'][:150]}...")

    print("\n" + "=" * 80)
    print("READY TO USE!")
    print("=" * 80)

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
