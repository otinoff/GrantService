#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обновление БД на production"""
import psycopg2

# Connect
conn = psycopg2.connect(
    host='localhost',
    port=5434,
    dbname='grantservice',
    user='grantservice',
    password='jPsGn%Nt%q#THnUB&&cqo*1Q'
)
cur = conn.cursor()

# 1. Update block_audit prompt (escaped JSON example)
prompt_text = '''Проверь ответы на {block_num} блок вопросов.

ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ:
{block_answers}

ОЦЕНИ БЛОК ПО ШКАЛЕ 1-10:
- Достаточно ли информации?
- Есть ли конкретика (цифры, факты, имена)?
- Понятно ли что хочет сделать человек?

ЧТО СМОТРЕТЬ:
Блок 1 (о чём проект):
- Понятно ли название и цель?
- Описана ли проблема конкретно?
- Ясна ли целевая аудитория?

Блок 2 (как делать):
- Понятен ли план действий?
- Расписан ли бюджет?
- Есть ли конкретные результаты?

Блок 3 (кто делает):
- Описана ли команда?
- Есть ли партнёры?
- Продуман ли план после гранта?

ВАЖНО:
1. Верни ТОЛЬКО JSON, без дополнительного текста до и после
2. Не пиши объяснений, только JSON
3. Если всё хорошо (score >= 7) - не придумывай проблемы, верни пустой массив need_clarifications

ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
{{
    "block_score": 7,
    "weak_points": ["бюджет без деталей", "нет конкретных партнёров"],
    "need_clarifications": [
        {{"topic": "бюджет", "question": "Расскажи подробнее на что пойдут деньги?"}},
        {{"topic": "партнёры", "question": "Кто конкретно будет помогать?"}}
    ]
}}'''

cur.execute("UPDATE agent_prompts SET prompt_template = %s WHERE id = 78", (prompt_text,))
conn.commit()
print("✅ block_audit prompt updated (JSON example escaped)")

# 2. Update mode to interactive
cur.execute("UPDATE ai_agent_settings SET mode = 'interactive' WHERE agent_name = 'interviewer'")
conn.commit()
print("✅ Interviewer mode set to 'interactive'")

cur.close()
conn.close()

print("✅ All database updates complete!")
