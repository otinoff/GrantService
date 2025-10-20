#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply migration 007: Replace interview questions with new 14Q set
"""
import sys
import os
from pathlib import Path

# Add web-admin to path
sys.path.insert(0, str(Path(__file__).parent / 'web-admin'))

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

from utils.postgres_helper import execute_query, execute_update

print("=" * 80)
print("MIGRATION 007: Replace Interview Questions (14Q)")
print("=" * 80)

# Step 1: Check current state
print("\n[1/4] Checking current questions...")
current = execute_query("""
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN is_active = true THEN 1 END) as active
    FROM interview_questions
""")

if current:
    print(f"  Current: {current[0]['total']} total, {current[0]['active']} active")

# Step 2: Shift old questions
print("\n[2/4] Shifting old questions to 15-38 and disabling...")
try:
    execute_update("""
        UPDATE interview_questions
        SET question_number = question_number + 14,
            is_active = false,
            updated_at = NOW()
    """)
    print("  ✅ Old questions shifted and disabled")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Step 3: Insert new questions
print("\n[3/4] Inserting new 14 questions...")

new_questions = [
    (1, 'Опишите суть проекта, что хотите сделать и для кого и зачем',
     '1 предложение — что / для кого / и зачем. Пример: «Интерактивный ИИ‑аватар для студентов, чтобы быстрее получать ответы и вовлекаться в мероприятия».',
     'project_essence', 'textarea', True, True),

    (2, 'Укажите географию проекта (город, регион и тп)',
     'регион/город и основные площадки. Пример: «Кемерово; кампус КемГИК, аудитории №…».',
     'geography', 'textarea', True, True),

    (3, 'Какую проблему решает проект и какую социальную значимость он несет?',
     'что не работает, кого касается, где проявляется, почему сейчас важно (цифры не требуются). Пример: «Медленная и разрозненная коммуникация в вузе мешает студентам быстро получать информацию и вовлекаться».',
     'problem_and_significance', 'textarea', True, True),

    (4, 'Опишите целевую группу (участники, возраст)',
     'кто именно, возраст, ориентировочная численность. Пример: «Студенты 17–23, ~2500; абитуриенты и родители».',
     'target_group', 'textarea', True, True),

    (5, 'Главная цель проекта (видение решения проблемы)',
     'одна чёткая цель, связанная с проблемой. Пример: «Повысить доступность и скорость коммуникации в вузе через ИИ‑аватара».',
     'main_goal', 'textarea', True, True),

    (6, 'Задачи, которые нужно решить для достижения цели',
     '3–5 задач, каждая ведёт к цели (глаголами). Пример: «Создать 3D‑аватар; обучить на базе данных вуза; интегрировать с сайтами; обучить персонал».',
     'tasks', 'textarea', True, True),

    (7, 'Какие мероприятия планируете провести?',
     'формат, периодичность, длительность, ориентировочный охват и площадки. Пример: «Мастер‑класс 2/мес, 2 ч, 25 чел; инфосессия 1/кв; 2 итоговых события».',
     'events', 'textarea', True, True),

    (8, 'Партнеры проекта (организации, формы поддержки)',
     'перечислите партнёров и формы поддержки; ресурсы: что уже есть и чего не хватает. Пример: «КемГИК — помещения/оборудование; требуется: лицензия TTS (аренда), GPU (облако)».',
     'partners', 'textarea', True, True),

    (9, 'Какая сумма позволит реализовать проект?',
     'ориентировочная общая сумма в рублях. Пример: «2 400 000».',
     'budget', 'text', True, True),

    (10, 'Ссылки на сайт/соцсети (для оценки инфо‑открытости)',
     'сайт, 1–2 соцсети, публичные отчёты/реестры (если есть). Пример: «site.ru; VK: vk.com/...; отчёт в ЕГРЮЛ/Контур».',
     'links', 'textarea', False, True),

    (11, 'История получения грантов (год, фонд, результат)',
     '1–3 кейса — год, донор/программа, сумма, результат/URL. Пример: «2023, ФПГ, 1,2 млн, «цифровые сервисы», отчёт: …».',
     'grant_history', 'textarea', False, True),

    (12, 'Наличие ресурсов и оборудования для реализации',
     'помещения, оборудование, ПО/лицензии, сервера/облако, интеграции. Пример: «Студия, микрофоны, лицензии Zoom, VPS, интеграция с LMS».',
     'resources', 'textarea', True, True),

    (13, 'Планируемые результаты (количественные и качественные)',
     '2–3 ключевых изменения без цифр и как их фиксировать (логи/опрос/отчёт), периодичность (мес/кв). Пример: «Больше консультаций через аватар (логи, мес); выше удовлетворённость (опрос/NPS, квартал)».',
     'results', 'textarea', True, True),

    (14, 'Устойчивость после гранта: источники и планы масштабирования',
     'что продолжится после гранта, источники финансирования, роли партнёров, планы тиражирования. Пример: «Поддержка 12 мес за счёт внебюджета; партнёр — техподдержка; тиражирование в факультеты».',
     'sustainability', 'textarea', True, True),
]

for q_num, q_text, hint, field, q_type, req, active in new_questions:
    try:
        execute_update("""
            INSERT INTO interview_questions
            (question_number, question_text, hint_text, field_name, question_type, is_required, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (q_num, q_text, hint, field, q_type, req, active))
        print(f"  ✅ Q{q_num}: {q_text[:50]}...")
    except Exception as e:
        print(f"  ❌ Q{q_num} Error: {e}")

# Step 4: Verify results
print("\n[4/4] Verifying results...")
result = execute_query("""
    SELECT question_number, question_text, is_active
    FROM interview_questions
    ORDER BY question_number
""")

if result:
    active_count = len([r for r in result if r['is_active']])
    inactive_count = len([r for r in result if not r['is_active']])

    print(f"\n  Total questions: {len(result)}")
    print(f"  Active (1-14): {active_count}")
    print(f"  Inactive (15+): {inactive_count}")

    print("\n  Active questions (1-14):")
    for r in result:
        if r['is_active']:
            print(f"    {r['question_number']}. {r['question_text'][:60]}...")

print("\n" + "=" * 80)
print("✅ MIGRATION 007 COMPLETED SUCCESSFULLY")
print("=" * 80)
