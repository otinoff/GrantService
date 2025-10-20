#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct SQL update for WebSearch provider settings
"""

import psycopg2
import json

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="grantservice",
    user="grantservice_user",
    password="grant_secure_pass_2024"
)

cur = conn.cursor()

print("=" * 80)
print("UPDATE WEBSEARCH PROVIDER SETTINGS (Direct SQL)")
print("=" * 80)

# Get current settings
cur.execute("SELECT id, config FROM ai_agent_settings WHERE agent_name = 'researcher'")
row = cur.fetchone()

if not row:
    print("[ERROR] Researcher settings not found")
    exit(1)

settings_id, config = row

print("\n[BEFORE]")
print(f"  websearch_provider: {config.get('websearch_provider')}")
print(f"  websearch_fallback: {config.get('websearch_fallback')}")

# Update
config['websearch_provider'] = 'claude_code'
config['websearch_fallback'] = None

cur.execute(
    "UPDATE ai_agent_settings SET config = %s WHERE id = %s",
    (json.dumps(config), settings_id)
)

conn.commit()

# Verify
cur.execute("SELECT config FROM ai_agent_settings WHERE id = %s", (settings_id,))
updated_config = cur.fetchone()[0]

print("\n[AFTER]")
print(f"  websearch_provider: {updated_config.get('websearch_provider')}")
print(f"  websearch_fallback: {updated_config.get('websearch_fallback')}")

print("\n[OK] Settings updated!")

cur.close()
conn.close()
