#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка ЛОКАЛЬНОЙ БД PostgreSQL 18
"""

import psycopg2
import sys

def check_local_db():
    """Проверить локальную БД"""

    print("Checking local PostgreSQL 18...")
    print("Host: localhost:5432")
    print()

    # Пробуем разные пароли
    passwords = ['postgres', 'admin', '']

    conn = None
    for password in passwords:
        try:
            print(f"Trying password: '{password}'...")
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres',
                password=password,
                connect_timeout=3
            )
            print(f"SUCCESS! Password: '{password}'")
            break
        except Exception as e:
            print(f"Failed: {e}")
            continue

    if not conn:
        print("\nFailed to connect. Try manually:")
        print("psql -U postgres -h localhost -p 5432")
        return False

    print("\nConnected to local PostgreSQL!")

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"Version: {version}")

    # List databases
    cursor.execute("""
        SELECT datname FROM pg_database
        WHERE datistemplate = false
        ORDER BY datname;
    """)
    databases = cursor.fetchall()

    print(f"\nDatabases ({len(databases)}):")
    for db in databases:
        print(f"  - {db[0]}")

    # Check if grantservice exists
    grantservice_exists = any(db[0] == 'grantservice' for db in databases)

    if grantservice_exists:
        print("\ngrantservice database EXISTS")
    else:
        print("\ngrantservice database NOT FOUND - need to create")

    cursor.close()
    conn.close()

    return True

if __name__ == "__main__":
    success = check_local_db()
    sys.exit(0 if success else 1)
