#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update WebSearch Provider Settings to Claude Code ONLY

Обновляет настройки WebSearch провайдера в БД:
- websearch_provider: claude_code (primary and ONLY)
- websearch_fallback: null (NO fallback)
"""

import os

# Set PostgreSQL environment BEFORE any imports
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'grantservice'
os.environ['DB_USER'] = 'grantservice_user'
os.environ['DB_PASSWORD'] = 'grant_secure_pass_2024'

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database.models import db
import json


def update_websearch_settings():
    """Обновить настройки WebSearch провайдера"""
    print("=" * 80)
    print("UPDATE WEBSEARCH PROVIDER SETTINGS")
    print("=" * 80)

    try:
        # Получить текущие настройки
        result = db.query_one(
            "SELECT id, agent_name, config FROM ai_agent_settings WHERE agent_name = %s",
            ('researcher',)
        )

        if not result:
            print("[ERROR] Researcher agent settings not found in DB")
            return False

        settings_id, agent_name, config = result

        # Текущие настройки
        print("\n[BEFORE]")
        print(f"  websearch_provider: {config.get('websearch_provider')}")
        print(f"  websearch_fallback: {config.get('websearch_fallback')}")

        # Обновить настройки
        config['websearch_provider'] = 'claude_code'
        config['websearch_fallback'] = None  # NO fallback

        # Обновить в БД
        db.execute(
            "UPDATE ai_agent_settings SET config = %s WHERE id = %s",
            (json.dumps(config), settings_id)
        )

        # Проверить обновление
        updated = db.query_one(
            "SELECT config FROM ai_agent_settings WHERE id = %s",
            (settings_id,)
        )

        print("\n[AFTER]")
        print(f"  websearch_provider: {updated[0].get('websearch_provider')}")
        print(f"  websearch_fallback: {updated[0].get('websearch_fallback')}")

        print("\n[OK] WebSearch provider settings updated successfully!")
        print("     - Primary: Claude Code CLI")
        print("     - Fallback: NONE")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to update settings: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = update_websearch_settings()
    sys.exit(0 if success else 1)
