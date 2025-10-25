#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка подключения к удалённой БД PostgreSQL
"""

import psycopg2
import sys

def check_connection():
    """Проверить подключение к БД"""

    print("🔌 Connecting to PostgreSQL...")
    print("   Host: 5.35.88.251:5434")
    print("   Database: grantservice")
    print("   User: grantservice")
    print()

    try:
        conn = psycopg2.connect(
            host='5.35.88.251',
            port=5434,
            database='grantservice',
            user='grantservice',
            password='jPsGn%Nt%q#THnUB&&cqo*1Q'
        )

        print("✅ Connected successfully!")

        # Get database info
        cursor = conn.cursor()
        cursor.execute("SELECT current_database(), version();")
        db_name, version = cursor.fetchone()

        print(f"\n📊 Database: {db_name}")
        print(f"📦 Version: {version}")

        # Check tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        print(f"\n📋 Tables ({len(tables)}):")
        for table in tables:
            print(f"   • {table[0]}")

        # Check if Natalia's anketa exists
        cursor.execute("""
            SELECT anketa_id, status, created_at
            FROM sessions
            WHERE anketa_id LIKE '%Natalia%' OR anketa_id LIKE '%natalia%'
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        anketas = cursor.fetchall()

        print(f"\n🔍 Анкеты Натальи ({len(anketas)}):")
        for anketa_id, status, created_at in anketas:
            print(f"   • {anketa_id} | {status} | {created_at}")

        cursor.close()
        conn.close()

        print("\n✅ Всё работает!")
        return True

    except Exception as e:
        print(f"\n❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    success = check_connection()
    sys.exit(0 if success else 1)
