#!/usr/bin/env python3
"""
Test PostgreSQL 18 connection without password prompt
"""
import psycopg2
import sys

# PostgreSQL 18 connection parameters
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',  # default database
    'user': 'postgres',
    'password': 'root'
}

def test_connection():
    """Test PostgreSQL connection"""
    try:
        print("Connecting to PostgreSQL 18...")
        print(f"Host: {PG_CONFIG['host']}:{PG_CONFIG['port']}")
        print(f"User: {PG_CONFIG['user']}")
        print()

        # Connect
        conn = psycopg2.connect(**PG_CONFIG)
        cursor = conn.cursor()

        # Get version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print("[OK] Connection successful!")
        print(f"[OK] Version: {version}")
        print()

        # List databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        print("Available databases:")
        for db in databases:
            print(f"  - {db[0]}")
        print()

        # Check if grantservice database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='grantservice';")
        exists = cursor.fetchone()

        if exists:
            print("[OK] Database 'grantservice' exists")
        else:
            print("[WARN] Database 'grantservice' does NOT exist")
            print("  Run: CREATE DATABASE grantservice;")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        print()
        print("Possible solutions:")
        print("1. Check PostgreSQL is running: sc query postgresql-x64-18")
        print("2. Verify password is correct (currently: 'root')")
        print("3. Check pg_hba.conf allows local connections")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
