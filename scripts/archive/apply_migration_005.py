#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply migration 005: Agent Prompts Management System"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-admin"))

from utils.postgres_helper import execute_update, execute_query

def main():
    print("=" * 70)
    print("Applying migration 005: Agent Prompts Management System")
    print("=" * 70)

    # Read migration file
    migration_file = Path(__file__).parent / "database" / "migrations" / "005_add_agent_prompts.sql"

    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    print(f"\nReading migration from: {migration_file}")
    print(f"SQL size: {len(migration_sql)} characters\n")

    try:
        # Execute migration
        print("Executing migration...")
        execute_update(migration_sql)

        # Verify table created
        result = execute_query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'agent_prompts'
        """)

        if result:
            print("✅ Table 'agent_prompts' created successfully")

            # Count prompts
            count_result = execute_query("SELECT COUNT(*) as cnt FROM agent_prompts")
            if count_result:
                print(f"✅ Loaded {count_result[0]['cnt']} initial prompts")

            # Show prompts
            prompts = execute_query("""
                SELECT agent_name, prompt_type, prompt_key, is_default
                FROM agent_prompts
                ORDER BY agent_name, prompt_type
            """)

            if prompts:
                print("\n📝 Loaded prompts:")
                for p in prompts:
                    default_mark = " (DEFAULT)" if p['is_default'] else ""
                    print(f"  - {p['agent_name']:15} | {p['prompt_type']:20} | {p['prompt_key']}{default_mark}")

        else:
            print("❌ Table 'agent_prompts' not found!")
            return 1

        print("\n" + "=" * 70)
        print("✅ Migration 005 applied successfully!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
