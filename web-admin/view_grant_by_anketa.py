#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from utils.postgres_helper import execute_query
import json

# Получить anketa_id из аргументов
if len(sys.argv) < 2:
    print("Usage: python view_grant_by_anketa.py <anketa_id>")
    sys.exit(1)

anketa_id = sys.argv[1]

# Получить грант
result = execute_query("""
    SELECT
        grant_id,
        grant_title,
        grant_content,
        grant_sections,
        status,
        LENGTH(grant_content) as content_length,
        created_at
    FROM grants
    WHERE anketa_id = %s
""", (anketa_id,))

if not result:
    print(f"Грант не найден для анкеты: {anketa_id}")
    sys.exit(1)

grant = result[0]

print("="*70)
print(f"ГРАНТ ДЛЯ АНКЕТЫ: {anketa_id}")
print("="*70)
print(f"Grant ID: {grant['grant_id']}")
print(f"Название: {grant['grant_title']}")
print(f"Длина: {grant['content_length']} символов")
print(f"Статус: {grant['status']}")
print(f"Создан: {grant['created_at']}")

sections = grant['grant_sections']
if isinstance(sections, dict):
    print(f"\nСекции ({len(sections)} всего):")
    for key in sections.keys():
        print(f"  ✓ {key}")

print("\n" + "="*70)
print("СОДЕРЖАНИЕ ГРАНТА")
print("="*70 + "\n")

print(grant['grant_content'])

print("\n" + "="*70)

# Сохранить в файл
filename = f"grant_{anketa_id.replace('#', '').replace('-', '_')}.txt"
with open(filename, 'w', encoding='utf-8') as f:
    f.write(f"ГРАНТ ДЛЯ АНКЕТЫ: {anketa_id}\n")
    f.write("="*70 + "\n\n")
    f.write(grant['grant_content'])

print(f"\n✅ Грант сохранен в файл: {filename}")
