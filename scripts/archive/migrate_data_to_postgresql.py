#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Data Migration from SQLite to PostgreSQL on Production Server
GrantService - 2025-10-04
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.migrations.migrate_sqlite_to_postgresql import SQLiteToPostgreSQLMigrator

def main():
    """Run migration using environment variables"""

    # SQLite source database
    sqlite_db = "/var/GrantService/data/grantservice.db"

    # PostgreSQL target (from environment variables)
    pg_config = {
        'host': os.getenv('PGHOST', 'localhost'),
        'port': int(os.getenv('PGPORT', '5434')),
        'database': os.getenv('PGDATABASE', 'grantservice'),
        'user': os.getenv('PGUSER', 'grantservice'),
        'password': os.getenv('PGPASSWORD', 'jPsGn%Nt%q#THnUB&&cqo*1Q')
    }

    print("=" * 70)
    print("SQLite → PostgreSQL Data Migration")
    print("=" * 70)
    print(f"Source: {sqlite_db}")
    print(f"Target: {pg_config['host']}:{pg_config['port']}/{pg_config['database']}")
    print()

    # Create migrator
    migrator = SQLiteToPostgreSQLMigrator(sqlite_db, pg_config)

    try:
        # Connect to databases
        migrator.connect_databases()

        # Run migration
        print("\n🚀 Starting data migration...\n")
        migrator.run_migration()

        # Show results
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nMigrated {migrator.stats['total_rows']} total rows:")
        for table, count in migrator.stats['tables'].items():
            print(f"  ✓ {table}: {count} rows")

        if migrator.stats['errors']:
            print(f"\n⚠️  {len(migrator.stats['errors'])} errors occurred:")
            for error in migrator.stats['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")

        return 0

    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}", file=sys.stderr)
        return 1

    finally:
        # Close connections
        if migrator.sqlite_conn:
            migrator.sqlite_conn.close()
        if migrator.pg_conn:
            migrator.pg_conn.close()

if __name__ == '__main__':
    sys.exit(main())
