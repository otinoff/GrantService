#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load prompts from agents/prompts/ to agent_prompts table"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data.database import GrantServiceDatabase

def main():
    print("Loading prompts to database...")

    db = GrantServiceDatabase()

    # First, create table if not exists
    with db.connect() as conn:
        cursor = conn.cursor()

        # Read and execute migration
        migration_file = Path(__file__).parent / "database" / "migrations" / "005_add_agent_prompts.sql"

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        print(f"Executing migration from {migration_file}...")

        try:
            cursor.execute(migration_sql)
            conn.commit()
            print("Migration executed successfully")
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
            # Table might already exist, continue

        # Check prompts count
        cursor.execute("SELECT COUNT(*) FROM agent_prompts")
        count = cursor.fetchone()[0]

        print(f"\nPrompts in database: {count}")

        if count > 0:
            cursor.execute("""
                SELECT agent_name, prompt_type, prompt_key
                FROM agent_prompts
                ORDER BY agent_name, prompt_type
            """)

            prompts = cursor.fetchall()
            print("\nLoaded prompts:")
            for p in prompts:
                print(f"  - {p[0]:15} | {p[1]:20} | {p[2]}")

        cursor.close()

    print("\nDone!")

if __name__ == "__main__":
    main()
