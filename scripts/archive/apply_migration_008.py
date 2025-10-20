#!/usr/bin/env python3
"""
Apply Migration 008: Upgrade researcher_research JSONB structure and indexes

This script applies migration 008 which:
1. Ensures research_results is JSONB type (converts from TEXT if needed)
2. Creates optimized GIN indexes for JSONB queries
3. Adds comprehensive documentation comments
4. Adds validation constraints
5. Optimizes query performance

Usage:
    python apply_migration_008.py [--rollback]

Options:
    --rollback    Rollback the migration (restore previous state)
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2 not installed")
    print("Install with: pip install psycopg2-binary")
    sys.exit(1)


def get_database_connection():
    """Get PostgreSQL database connection from environment"""
    try:
        # Try to load from .env file
        env_file = project_root / 'config' / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            os.environ.setdefault(key.strip(), value.strip())

        # Get connection parameters (try both POSTGRES_* and PG* prefixes)
        db_host = os.getenv('POSTGRES_HOST') or os.getenv('PGHOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT') or os.getenv('PGPORT', '5432')
        db_name = os.getenv('POSTGRES_DB') or os.getenv('PGDATABASE', 'grantservice')
        db_user = os.getenv('POSTGRES_USER') or os.getenv('PGUSER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD') or os.getenv('PGPASSWORD', '')

        print(f"Connecting to PostgreSQL: {db_user}@{db_host}:{db_port}/{db_name}")

        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )

        return conn

    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)


def check_migration_status(conn):
    """Check if migration 008 has already been applied"""
    try:
        with conn.cursor() as cur:
            # Check if index exists (indicator of migration applied)
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'researcher_research'
                    AND indexname = 'idx_researcher_results_gin'
                )
            """)
            index_exists = cur.fetchone()[0]

            # Check if validation constraint exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'check_completed_has_results'
                )
            """)
            constraint_exists = cur.fetchone()[0]

            return {
                'index_exists': index_exists,
                'constraint_exists': constraint_exists,
                'already_applied': index_exists and constraint_exists
            }

    except Exception as e:
        print(f"ERROR checking migration status: {e}")
        return {'already_applied': False}


def apply_migration(conn, migration_file):
    """Apply migration SQL file"""
    print(f"\n{'='*60}")
    print(f"Applying Migration 008: Upgrade researcher_research JSONB")
    print(f"{'='*60}\n")

    # Check if already applied
    status = check_migration_status(conn)
    if status['already_applied']:
        print("⚠️  WARNING: Migration 008 appears to be already applied")
        print(f"   - Index idx_researcher_results_gin exists: {status['index_exists']}")
        print(f"   - Constraint check_completed_has_results exists: {status['constraint_exists']}")
        response = input("\nDo you want to reapply anyway? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Migration cancelled by user")
            return False

    # Read migration SQL
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
    except Exception as e:
        print(f"ERROR: Failed to read migration file: {e}")
        return False

    # Execute migration
    try:
        print("Executing migration SQL...")
        print("-" * 60)

        with conn.cursor() as cur:
            # Execute the migration
            cur.execute(migration_sql)

        conn.commit()

        print("-" * 60)
        print("✅ Migration executed successfully")

        # Verify results
        verify_migration(conn)

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: Migration failed: {e}")
        print("\nTransaction rolled back. Database unchanged.")
        return False


def verify_migration(conn):
    """Verify migration was applied correctly"""
    print(f"\n{'='*60}")
    print("Verifying Migration Results")
    print(f"{'='*60}\n")

    try:
        with conn.cursor() as cur:
            # Check research_results type
            cur.execute("""
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'researcher_research'
                AND column_name = 'research_results'
            """)
            result = cur.fetchone()
            data_type = result[0] if result else 'NOT FOUND'
            print(f"✓ research_results column type: {data_type}")

            # Check indexes
            cur.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'researcher_research'
                AND indexname LIKE 'idx_researcher%'
                ORDER BY indexname
            """)
            indexes = [row[0] for row in cur.fetchall()]
            print(f"\n✓ JSONB indexes created ({len(indexes)}):")
            for idx in indexes:
                print(f"  - {idx}")

            # Check constraint
            cur.execute("""
                SELECT conname
                FROM pg_constraint
                WHERE conname = 'check_completed_has_results'
            """)
            constraint = cur.fetchone()
            if constraint:
                print(f"\n✓ Validation constraint: {constraint[0]}")
            else:
                print("\n⚠️  Warning: Validation constraint not found")

            # Check table comment
            cur.execute("""
                SELECT obj_description('researcher_research'::regclass)
            """)
            comment = cur.fetchone()
            if comment and comment[0]:
                print(f"\n✓ Table comment: {comment[0][:80]}...")
            else:
                print("\n⚠️  Warning: Table comment not found")

            # Check data statistics
            cur.execute("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN research_results IS NOT NULL THEN 1 END) as with_results
                FROM researcher_research
            """)
            stats = cur.fetchone()
            print(f"\n📊 Data Statistics:")
            print(f"  - Total records: {stats[0]}")
            print(f"  - Completed: {stats[1]}")
            print(f"  - With results: {stats[2]}")

        print(f"\n{'='*60}")
        print("✅ Verification completed successfully")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n⚠️  Verification failed: {e}")


def rollback_migration(conn):
    """Rollback migration 008"""
    print(f"\n{'='*60}")
    print("Rolling Back Migration 008")
    print(f"{'='*60}\n")

    print("⚠️  WARNING: This will:")
    print("  1. Drop new JSONB indexes")
    print("  2. Remove validation constraint")
    print("  3. Remove documentation comments")
    print("  4. NOTE: Will NOT convert JSONB back to TEXT (data preserved)")
    print()

    response = input("Are you sure you want to rollback? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Rollback cancelled by user")
        return False

    rollback_sql = """
    BEGIN;

    -- Drop new indexes
    DROP INDEX IF EXISTS idx_researcher_results_gin;
    DROP INDEX IF EXISTS idx_researcher_status_completed;
    DROP INDEX IF EXISTS idx_researcher_anketa_status;
    DROP INDEX IF EXISTS idx_researcher_completed_date;
    DROP INDEX IF EXISTS idx_researcher_metadata_gin;

    -- Drop validation constraint
    ALTER TABLE researcher_research
    DROP CONSTRAINT IF EXISTS check_completed_has_results;

    -- Remove comments (set to NULL)
    COMMENT ON TABLE researcher_research IS NULL;
    COMMENT ON COLUMN researcher_research.research_results IS NULL;
    COMMENT ON COLUMN researcher_research.metadata IS NULL;
    COMMENT ON COLUMN researcher_research.status IS NULL;

    -- Recreate old GIN index (from migration 001)
    CREATE INDEX IF NOT EXISTS idx_research_results_gin
    ON researcher_research USING gin(research_results);

    COMMIT;

    SELECT 'Rollback completed' as status;
    """

    try:
        print("Executing rollback SQL...")
        print("-" * 60)

        with conn.cursor() as cur:
            cur.execute(rollback_sql)

        conn.commit()

        print("-" * 60)
        print("✅ Rollback completed successfully")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: Rollback failed: {e}")
        print("\nTransaction rolled back.")
        return False


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Apply or rollback migration 008 for researcher_research table'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback the migration instead of applying it'
    )

    args = parser.parse_args()

    # Get migration file path
    migration_file = project_root / 'database' / 'migrations' / '008_upgrade_researcher_research_jsonb.sql'

    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    # Connect to database
    print(f"\n{'='*60}")
    print(f"Migration 008: Researcher Research JSONB Upgrade")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    conn = get_database_connection()

    try:
        if args.rollback:
            success = rollback_migration(conn)
        else:
            success = apply_migration(conn, migration_file)

        if success:
            print("\n✅ Operation completed successfully!")
            print("\n📝 Next steps:")
            if not args.rollback:
                print("  1. Test JSONB queries on researcher_research table")
                print("  2. Update ResearcherAgent to use new structure")
                print("  3. Verify Writer agent can read research_results")
                print("  4. Run E2E tests with real research data")
            sys.exit(0)
        else:
            print("\n❌ Operation failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
