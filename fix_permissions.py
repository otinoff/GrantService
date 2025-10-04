#!/usr/bin/env python3
"""Fix schema permissions"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

params = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'root',
    'database': 'grantservice'
}

print("[*] Connecting as superuser...")
conn = psycopg2.connect(**params)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

try:
    print("[*] Granting schema permissions...")
    cursor.execute("GRANT ALL ON SCHEMA public TO grantservice_user;")
    cursor.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO grantservice_user;")
    cursor.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO grantservice_user;")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO grantservice_user;")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO grantservice_user;")
    print("[OK] Permissions granted!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
