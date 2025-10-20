#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update block_audit prompt on production server
"""
import psycopg2

# Production DB credentials
DB_CONFIG = {
    'host': '5.35.88.251',
    'port': 5434,
    'database': 'grantservice',
    'user': 'grantservice',
    'password': 'jPsGn%Nt%q#THnUB&&cqo*1Q'
}

# Fixed prompt template with proper JSON escaping (4 braces)
PROMPT_TEMPLATE = """Проверь ответы на {block_num} блок вопросов.

ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ:
{block_answers}

ОЦЕНИ БЛОК ПО ШКАЛЕ 1-10:
- Достаточно ли информации?
- Есть ли конкретика (цифры, факты, имена)?
- Понятно ли что хочет сделать человек?

ВАЖНО:
1. Верни ТОЛЬКО JSON, без дополнительного текста до и после
2. Не пиши объяснений, только JSON

ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
{{{{
    "block_score": 7,
    "weak_points": ["пример"],
    "need_clarifications": [
        {{{{ "topic": "тема", "question": "вопрос?" }}}}
    ]
}}}}"""

def update_prompt():
    """Update block_audit prompt on production"""
    print("=" * 80)
    print("UPDATING block_audit PROMPT ON PRODUCTION")
    print("=" * 80)

    try:
        # Connect to production DB
        print(f"\n1. Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("   ✅ Connected")

        # Get category_id for interactive_block_audit
        print("\n2. Getting category ID...")
        cur.execute("""
            SELECT id FROM prompt_categories
            WHERE name='interactive_block_audit'
        """)
        result = cur.fetchone()
        if not result:
            print("   ❌ Category 'interactive_block_audit' not found!")
            return False

        category_id = result[0]
        print(f"   ✅ Category ID: {category_id}")

        # Check current prompt
        print("\n3. Checking current prompt...")
        cur.execute("""
            SELECT id, LEFT(prompt_template, 100)
            FROM agent_prompts
            WHERE name='block_audit' AND category_id=%s
        """, (category_id,))
        result = cur.fetchone()
        if result:
            print(f"   Current prompt ID: {result[0]}")
            print(f"   Preview: {result[1]}...")
        else:
            print("   ❌ Prompt 'block_audit' not found!")
            return False

        # Update prompt
        print("\n4. Updating prompt...")
        cur.execute("""
            UPDATE agent_prompts
            SET prompt_template = %s
            WHERE name='block_audit' AND category_id=%s
        """, (PROMPT_TEMPLATE, category_id))

        rows_updated = cur.rowcount
        print(f"   ✅ Updated {rows_updated} row(s)")

        # Commit changes
        conn.commit()
        print("\n5. Changes committed")

        # Verify update
        print("\n6. Verifying update...")
        cur.execute("""
            SELECT LEFT(prompt_template, 150)
            FROM agent_prompts
            WHERE name='block_audit' AND category_id=%s
        """, (category_id,))
        result = cur.fetchone()
        if result:
            print(f"   New prompt preview: {result[0]}...")

            # Check if contains {{{{
            if '{{{{' in result[0]:
                print("   ✅ JSON escaping correct (contains {{{{)")
            else:
                print("   ❌ JSON escaping may be incorrect")

        cur.close()
        conn.close()

        print("\n" + "=" * 80)
        print("✅ UPDATE COMPLETE!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_prompt()
    exit(0 if success else 1)
