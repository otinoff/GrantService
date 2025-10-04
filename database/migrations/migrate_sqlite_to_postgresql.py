#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite to PostgreSQL Data Migration Script
GrantService Database Migration Tool

Usage:
    python migrate_sqlite_to_postgresql.py --sqlite-db path/to/sqlite.db --pg-host localhost --pg-db grantservice --pg-user user --pg-password pass
"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SQLiteToPostgreSQLMigrator:
    """Migrates GrantService database from SQLite to PostgreSQL"""

    # Table migration order (respects foreign key dependencies)
    MIGRATION_ORDER = [
        'users',
        'interview_questions',
        'sessions',
        'user_answers',
        'prompt_categories',
        'agent_prompts',
        'prompt_versions',
        'researcher_logs',
        'grant_applications',
        'researcher_research',
        'grants',
        'auditor_results',
        'planner_structures',
        'auth_logs',
        'page_permissions',
        'sent_documents',
        'db_version',
        'db_timestamps'
    ]

    # Columns that need JSON → JSONB conversion
    JSON_COLUMNS = {
        'users': ['permissions'],
        'interview_questions': ['options', 'validation_rules'],
        'sessions': ['conversation_history', 'collected_data', 'interview_data',
                     'audit_result', 'plan_structure', 'answers_data'],
        'researcher_logs': ['sources', 'usage_stats'],
        'agent_prompts': ['variables', 'default_values'],
        'prompt_versions': ['variables', 'default_values'],
        'grant_applications': ['content_json'],
        'researcher_research': ['research_results', 'metadata'],
        'grants': ['grant_sections', 'metadata'],
        'auditor_results': ['recommendations', 'metadata'],
        'planner_structures': ['structure_json', 'missing_data_sections', 'metadata'],
        'page_permissions': ['required_permissions']
    }

    # Columns that need INTEGER (0/1) → BOOLEAN conversion
    BOOLEAN_COLUMNS = {
        'users': ['is_active'],
        'interview_questions': ['is_required', 'is_active'],
        'sessions': ['is_active'],
        'prompt_categories': ['is_active'],
        'agent_prompts': ['is_active', 'is_system'],
        'prompt_versions': ['is_active'],
        'auth_logs': ['success'],
        'page_permissions': ['is_active']
    }

    def __init__(self, sqlite_path: str, pg_config: Dict[str, str]):
        """Initialize migrator with database connections"""
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
        self.sqlite_conn = None
        self.pg_conn = None
        self.stats = {
            'tables': {},
            'total_rows': 0,
            'errors': []
        }

    def connect_databases(self):
        """Establish connections to both databases"""
        logger.info("=" * 60)
        logger.info("Connecting to databases...")

        # Connect to SQLite
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"✓ Connected to SQLite: {self.sqlite_path}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to SQLite: {e}")
            raise

        # Connect to PostgreSQL
        try:
            self.pg_conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config.get('port', 5432),
                database=self.pg_config['database'],
                user=self.pg_config['user'],
                password=self.pg_config['password']
            )
            self.pg_conn.autocommit = False
            logger.info(f"✓ Connected to PostgreSQL: {self.pg_config['database']}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to PostgreSQL: {e}")
            raise

    def convert_json_value(self, value: Any) -> Optional[str]:
        """Convert JSON-like values to proper JSON format"""
        if value is None:
            return None

        if isinstance(value, str):
            # Try to parse as JSON
            try:
                parsed = json.loads(value)
                return json.dumps(parsed)
            except json.JSONDecodeError:
                # Not valid JSON, return as is
                return value

        return json.dumps(value)

    def convert_boolean_value(self, value: Any) -> Optional[bool]:
        """Convert SQLite INTEGER (0/1) to PostgreSQL BOOLEAN"""
        if value is None:
            return None
        # SQLite stores boolean as 0/1
        return bool(value)

    def convert_row_data(self, table: str, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to PostgreSQL-compatible format"""
        data = dict(row)

        # Convert JSON columns
        if table in self.JSON_COLUMNS:
            for col in self.JSON_COLUMNS[table]:
                if col in data:
                    data[col] = self.convert_json_value(data[col])

        # Convert BOOLEAN columns (SQLite INTEGER 0/1 → PostgreSQL BOOLEAN)
        if table in self.BOOLEAN_COLUMNS:
            for col in self.BOOLEAN_COLUMNS[table]:
                if col in data:
                    data[col] = self.convert_boolean_value(data[col])

        # Remove sqlite_sequence id if present
        if 'id' in data and table == 'sqlite_sequence':
            del data['id']

        return data

    def get_table_columns(self, table: str) -> List[str]:
        """Get column names for a table"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return columns

    def migrate_table(self, table: str) -> int:
        """Migrate data from one table"""
        logger.info(f"\nMigrating table: {table}")
        logger.info("-" * 60)

        # Skip tables that are already populated by schema
        if table in ['db_version', 'db_timestamps']:
            logger.info(f"  → Table {table} is pre-populated in schema, skipping data migration")
            self.stats['tables'][table] = {'rows': 0, 'status': 'skipped'}
            return 0

        sqlite_cursor = self.sqlite_conn.cursor()
        pg_cursor = self.pg_conn.cursor()

        try:
            # Count rows in SQLite
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_rows = sqlite_cursor.fetchone()[0]

            if total_rows == 0:
                logger.info(f"  → Table {table} is empty, skipping")
                self.stats['tables'][table] = {'rows': 0, 'status': 'skipped'}
                return 0

            logger.info(f"  → Found {total_rows} rows to migrate")

            # Fetch all rows from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()

            # Get column names
            columns = self.get_table_columns(table)

            # Prepare INSERT statement
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join([f'"{col}"' for col in columns])

            # For tables with SERIAL primary key, we need to handle id column specially
            if 'id' in columns and table != 'db_version' and table != 'db_timestamps':
                # Temporarily disable id constraint
                insert_sql = f"""
                    INSERT INTO {table} ({column_names})
                    VALUES ({placeholders})
                """
            else:
                insert_sql = f"""
                    INSERT INTO {table} ({column_names})
                    VALUES ({placeholders})
                """

            # Insert rows in batches
            batch_size = 100
            inserted = 0

            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                batch_data = []

                for row in batch:
                    data = self.convert_row_data(table, row)
                    values = [data.get(col) for col in columns]
                    batch_data.append(values)

                # Execute batch insert
                psycopg2.extras.execute_batch(pg_cursor, insert_sql, batch_data)
                inserted += len(batch)

                logger.info(f"  → Inserted {inserted}/{total_rows} rows")

            # Reset sequence for SERIAL columns if table has id column
            if 'id' in columns and table != 'db_version' and table != 'db_timestamps':
                pg_cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence('{table}', 'id'),
                                  COALESCE((SELECT MAX(id) FROM {table}), 1),
                                  true)
                """)
                logger.info(f"  → Reset sequence for {table}.id")

            self.pg_conn.commit()
            logger.info(f"  ✓ Successfully migrated {inserted} rows")

            self.stats['tables'][table] = {'rows': inserted, 'status': 'success'}
            self.stats['total_rows'] += inserted

            return inserted

        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"  ✗ Error migrating {table}: {e}")
            self.stats['tables'][table] = {'rows': 0, 'status': 'error', 'error': str(e)}
            self.stats['errors'].append({'table': table, 'error': str(e)})
            raise

    def verify_migration(self):
        """Verify that migration was successful"""
        logger.info("\n" + "=" * 60)
        logger.info("Verifying migration...")
        logger.info("=" * 60)

        sqlite_cursor = self.sqlite_conn.cursor()
        pg_cursor = self.pg_conn.cursor()

        all_match = True

        for table in self.MIGRATION_ORDER:
            # Skip utility tables
            if table in ['sqlite_sequence']:
                continue

            # Count rows in SQLite
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]

            # Count rows in PostgreSQL
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]

            match = "✓" if sqlite_count == pg_count else "✗"
            logger.info(f"{match} {table:30s} SQLite: {sqlite_count:6d} | PostgreSQL: {pg_count:6d}")

            if sqlite_count != pg_count:
                all_match = False

        return all_match

    def print_summary(self):
        """Print migration summary"""
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)

        logger.info(f"\nTotal rows migrated: {self.stats['total_rows']}")
        logger.info(f"Tables processed: {len(self.stats['tables'])}")

        # Success count
        success_count = sum(1 for t in self.stats['tables'].values() if t['status'] == 'success')
        skip_count = sum(1 for t in self.stats['tables'].values() if t['status'] == 'skipped')
        error_count = sum(1 for t in self.stats['tables'].values() if t['status'] == 'error')

        logger.info(f"\nSuccessful: {success_count}")
        logger.info(f"Skipped (empty): {skip_count}")
        logger.info(f"Errors: {error_count}")

        if self.stats['errors']:
            logger.info("\nErrors encountered:")
            for error in self.stats['errors']:
                logger.error(f"  • {error['table']}: {error['error']}")

        logger.info("\n" + "=" * 60)

    def run_migration(self):
        """Execute the complete migration process"""
        start_time = datetime.now()

        logger.info("=" * 60)
        logger.info("SQLite to PostgreSQL Migration")
        logger.info("GrantService Database")
        logger.info("=" * 60)
        logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Connect to databases
            self.connect_databases()

            # Migrate each table in order
            for table in self.MIGRATION_ORDER:
                try:
                    self.migrate_table(table)
                except Exception as e:
                    logger.warning(f"Skipping table {table} due to error: {e}")
                    continue

            # Verify migration
            verification_passed = self.verify_migration()

            # Print summary
            self.print_summary()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"\nCompleted at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Total duration: {duration:.2f} seconds")

            if verification_passed and not self.stats['errors']:
                logger.info("\n✓ Migration completed successfully!")
                return True
            else:
                logger.warning("\n⚠ Migration completed with warnings/errors")
                return False

        except Exception as e:
            logger.error(f"\n✗ Migration failed: {e}")
            return False

        finally:
            # Close connections
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.pg_conn:
                self.pg_conn.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate GrantService database from SQLite to PostgreSQL'
    )

    # SQLite arguments
    parser.add_argument('--sqlite-db', required=True,
                       help='Path to SQLite database file')

    # PostgreSQL arguments
    parser.add_argument('--pg-host', default='localhost',
                       help='PostgreSQL host (default: localhost)')
    parser.add_argument('--pg-port', type=int, default=5432,
                       help='PostgreSQL port (default: 5432)')
    parser.add_argument('--pg-database', required=True,
                       help='PostgreSQL database name')
    parser.add_argument('--pg-user', required=True,
                       help='PostgreSQL username')
    parser.add_argument('--pg-password', required=True,
                       help='PostgreSQL password')

    args = parser.parse_args()

    # PostgreSQL configuration
    pg_config = {
        'host': args.pg_host,
        'port': args.pg_port,
        'database': args.pg_database,
        'user': args.pg_user,
        'password': args.pg_password
    }

    # Create migrator
    migrator = SQLiteToPostgreSQLMigrator(args.sqlite_db, pg_config)

    # Run migration
    success = migrator.run_migration()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
