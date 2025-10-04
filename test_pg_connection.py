#!/usr/bin/env python3
"""Test PostgreSQL 18 connection and create database"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connection parameters
params = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'root'
}

try:
    # Connect to postgres database
    print("[*] Connecting to PostgreSQL 18...")
    conn = psycopg2.connect(**params, database='postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Check version
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"[OK] Connected! Version: {version[:50]}...")

    # Check if grantservice database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='grantservice';")
    exists = cursor.fetchone()

    if exists:
        print("[INFO] Database 'grantservice' already exists")
    else:
        # Create database
        print("[*] Creating database 'grantservice'...")
        cursor.execute("CREATE DATABASE grantservice;")
        print("[OK] Database 'grantservice' created successfully!")

    # Check if user exists
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='grantservice_user';")
    user_exists = cursor.fetchone()

    if user_exists:
        print("[INFO] User 'grantservice_user' already exists")
    else:
        # Create user
        print("[*] Creating user 'grantservice_user'...")
        cursor.execute("CREATE USER grantservice_user WITH PASSWORD 'grantservice2024';")
        print("[OK] User 'grantservice_user' created!")

    # Grant privileges
    print("[*] Granting privileges...")
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE grantservice TO grantservice_user;")
    print("[OK] Privileges granted!")

    cursor.close()
    conn.close()

    print("\n[OK] PostgreSQL 18 setup complete!")
    print("Database: grantservice")
    print("User: grantservice_user")
    print("Password: grantservice2024")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
