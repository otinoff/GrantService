#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except:
        pass

from utils.postgres_helper import execute_query
import json

# Test get_grant_details function
grant_id = "GRANT-#AN-20250905-Natalia_bruzzzz-001"

query = """
SELECT
    grant_id,
    grant_title,
    grant_content,
    grant_sections,
    metadata,
    quality_score,
    llm_provider,
    model,
    created_at,
    user_id,
    username
FROM grants
WHERE grant_id = %s
"""

result = execute_query(query, (grant_id,))

if result:
    row = result[0]
    print(f"✅ Грант найден!")
    print(f"  ID: {row['grant_id']}")
    print(f"  Название: {row['grant_title']}")
    print(f"  Длина контента: {len(row['grant_content']) if row['grant_content'] else 0} символов")
    print(f"  Оценка: {row['quality_score']}/10")
    print(f"  LLM: {row['llm_provider']}")
    print(f"  Username: {row['username']}")

    # Test grant details dict
    grant_details = {
        'grant_id': row.get('grant_id'),
        'title': row.get('grant_title'),
        'content': row.get('grant_content'),
        'quality_score': row.get('quality_score'),
        'llm_provider': row.get('llm_provider'),
        'model': row.get('model'),
        'created_at': row.get('created_at'),
        'username': row.get('username')
    }

    print(f"\n✅ Словарь grant_details создан успешно")
    print(f"  Ключи: {list(grant_details.keys())}")

    if grant_details['content']:
        print(f"\n✅ Контент есть, можно создать файл!")
    else:
        print(f"\n❌ Контент пустой!")
else:
    print(f"❌ Грант не найден!")
