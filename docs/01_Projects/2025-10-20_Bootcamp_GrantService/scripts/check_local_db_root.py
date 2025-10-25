#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка ЛОКАЛЬНОЙ БД PostgreSQL 18 с паролем root
"""

import psycopg2
import sys

def check_local_db():
    """Проверить локальную БД"""

    print("Connecting to LOCAL PostgreSQL 18...")
    print("Host: localhost:5432")
    print("User: postgres")
    print("Password: root")
    print()

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='root',
            connect_timeout=5,
            client_encoding='utf8'
        )
        print("SUCCESS Connected to local PostgreSQL!")

        cursor = conn.cursor()

        # Version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\nVersion: {version[:60]}...")

        # List databases
        cursor.execute("""
            SELECT datname FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        databases = cursor.fetchall()

        print(f"\nDatabases ({len(databases)}):")
        grantservice_exists = False
        for db in databases:
            db_name = db[0]
            if db_name == 'grantservice':
                print(f"  * {db_name} (TARGET DATABASE)")
                grantservice_exists = True
            else:
                print(f"  - {db_name}")

        if grantservice_exists:
            print("\n[OK] grantservice database EXISTS")

            # Check tables in grantservice
            conn2 = psycopg2.connect(
                host='localhost',
                port=5432,
                database='grantservice',
                user='postgres',
                password='root',
                connect_timeout=5,
                client_encoding='utf8'
            )
            cursor2 = conn2.cursor()

            cursor2.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor2.fetchall()

            print(f"\nTables in grantservice ({len(tables)}):")
            for table in tables:
                print(f"  - {table[0]}")

            cursor2.close()
            conn2.close()
        else:
            print("\n! grantservice database NOT FOUND - need to create")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print(f"\nERROR Connection failed: {e}")
        print("\nTry manually: psql -U postgres -h localhost -p 5432")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = check_local_db()
    sys.exit(0 if success else 1)
