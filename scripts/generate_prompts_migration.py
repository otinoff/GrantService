#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для генерации SQL миграции всех промптов из кода в БД
Извлекает все hardcoded промпты из агентов и создает INSERT statements
"""

import sys
import os
import json
from pathlib import Path

# Добавляем путь к agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.prompt_loader import ResearcherPromptLoader


def escape_sql_string(s: str) -> str:
    """Экранировать строку для SQL"""
    return s.replace("'", "''")


def generate_researcher_queries_sql():
    """Генерация SQL для 27 запросов Researcher V2"""

    loader = ResearcherPromptLoader()

    # Тестовые placeholders
    placeholders = {
        'ПРОБЛЕМА': '{ПРОБЛЕМА}',
        'РЕГИОН': '{РЕГИОН}',
        'МУНИЦИПАЛИТЕТ': '{МУНИЦИПАЛИТЕТ}',
        'СФЕРА': '{СФЕРА}',
        'ЦЕЛЕВАЯ_ГРУППА': '{ЦЕЛЕВАЯ_ГРУППА}',
        'ВОЗРАСТ': '{ВОЗРАСТ}',
        'ТЕМА_ПРОЕКТА': '{ТЕМА_ПРОЕКТА}',
        'ГЛАВНАЯ_ЦЕЛЬ': '{ГЛАВНАЯ_ЦЕЛЬ}',
        'КЛЮЧЕВЫЕ_ЗАДАЧИ': '{КЛЮЧЕВЫЕ_ЗАДАЧИ}',
        'МЕРОПРИЯТИЯ': '{МЕРОПРИЯТИЯ}',
        'ПОДХОД_МОДЕЛЬ': '{ПОДХОД_МОДЕЛЬ}',
        'ПЕРИОД': '{ПЕРИОД}',
        'ИНДИКАТОР': '{ИНДИКАТОР}',
        'ПРОФИЛЬНОЕ_МИНИСТЕРСТВО': '{ПРОФИЛЬНОЕ_МИНИСТЕРСТВО}',
        'KPI': '{KPI}',
        'КОЛИЧЕСТВЕННЫЕ_РЕЗУЛЬТАТЫ': '{КОЛИЧЕСТВЕННЫЕ_РЕЗУЛЬТАТЫ}',
        'КАЧЕСТВЕННЫЕ_РЕЗУЛЬТАТЫ': '{КАЧЕСТВЕННЫЕ_РЕЗУЛЬТАТЫ}'
    }

    all_queries = loader.get_all_queries(placeholders)

    sql_lines = []
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Researcher V2: 27 экспертных запросов")
    sql_lines.append("-- ============================================================================\n")

    # Блок 1
    sql_lines.append("-- Блок 1: Проблема и социальная значимость (10 запросов)")
    for idx, query in enumerate(all_queries['block1'], 1):
        # Определяем переменные из запроса
        variables = {}
        for key in placeholders.keys():
            if f'{{{key}}}' in query:
                variables[key] = "string"

        sql = f"""
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, order_index, variables, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'researcher_block1'),
  'Block1 Query {idx}',
  'Запрос {idx} блока 1',
  '{escape_sql_string(query.strip())}',
  'researcher_v2',
  'block1_query',
  {idx},
  '{json.dumps(variables, ensure_ascii=False)}'::jsonb,
  true
);
"""
        sql_lines.append(sql)

    # Блок 2
    sql_lines.append("\n-- Блок 2: География и целевая аудитория (10 запросов)")
    for idx, query in enumerate(all_queries['block2'], 1):
        variables = {}
        for key in placeholders.keys():
            if f'{{{key}}}' in query:
                variables[key] = "string"

        sql = f"""
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, order_index, variables, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'researcher_block2'),
  'Block2 Query {idx}',
  'Запрос {idx} блока 2',
  '{escape_sql_string(query.strip())}',
  'researcher_v2',
  'block2_query',
  {idx},
  '{json.dumps(variables, ensure_ascii=False)}'::jsonb,
  true
);
"""
        sql_lines.append(sql)

    # Блок 3
    sql_lines.append("\n-- Блок 3: Задачи, мероприятия и цели (7 запросов)")
    for idx, query in enumerate(all_queries['block3'], 1):
        variables = {}
        for key in placeholders.keys():
            if f'{{{key}}}' in query:
                variables[key] = "string"

        sql = f"""
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, order_index, variables, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'researcher_block3'),
  'Block3 Query {idx}',
  'Запрос {idx} блока 3',
  '{escape_sql_string(query.strip())}',
  'researcher_v2',
  'block3_query',
  {idx},
  '{json.dumps(variables, ensure_ascii=False)}'::jsonb,
  true
);
"""
        sql_lines.append(sql)

    return "\n".join(sql_lines)


def generate_writer_prompts_sql():
    """Генерация SQL для Writer V2 промптов"""

    sql_lines = []
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Writer V2: Goal, Backstory, Stage 1, Stage 2")
    sql_lines.append("-- ============================================================================\n")

    # Goal и Backstory
    sql_lines.append("""
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, is_active, priority) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Writer V2 Goal',
  'Цель агента Writer V2',
  'Создать качественную заявку на грант с использованием результатов исследования (27 запросов), минимум 10 цитат и 2 таблицы',
  'writer_v2',
  'goal',
  true,
  100
),
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Writer V2 Backstory',
  'Предыстория агента Writer V2',
  'Ты профессиональный грант-райтер с 15-летним опытом написания заявок. Ты знаешь все секреты успешных заявок, умеешь структурировать информацию и убедительно представлять проекты. Твои заявки содержат официальную статистику, цитаты из госпрограмм, успешные кейсы и сравнительные таблицы. Твои заявки имеют высокий процент одобрения (40-50%).',
  'writer_v2',
  'backstory',
  true,
  100
);
""")

    # Stage 1 Planning (большой промпт - упрощенная версия)
    stage1_template = """Ты эксперт по написанию заявок на Президентские гранты РФ. Твоя задача - спланировать структуру заявки согласно официальной форме ФПГ.

КОНТЕКСТ ПРОЕКТА:
Название: {project_name}
Описание: {description}
Проблема: {problem}
Решение: {solution}
Бюджет: {budget} рублей
Срок реализации: {timeline} месяцев

РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ (27 запросов):
Блок 1 - Проблема: {block1_summary}
Блок 2 - География: {block2_summary}
Блок 3 - Цели и задачи: {block3_summary}

Статистика:
- Всего источников: {sources_count}
- Ключевые факты: {key_facts_count}

СТРУКТУРА ЗАЯВКИ НА ПРЕЗИДЕНТСКИЙ ГРАНТ:
Создай детальный план из 9 разделов:
1. КРАТКОЕ ОПИСАНИЕ (0.5-1 стр, ~2000 символов)
2. ОПИСАНИЕ ПРОБЛЕМЫ (2-4 стр, ~8000 символов)
3. ЦЕЛЬ ПРОЕКТА (1 абзац, ~500 символов, SMART)
4. РЕЗУЛЬТАТЫ
5. ЗАДАЧИ (3-5 задач)
6. ПАРТНЕРЫ
7. ИНФОРМАЦИОННОЕ СОПРОВОЖДЕНИЕ
8. ДАЛЬНЕЙШЕЕ РАЗВИТИЕ
9. КАЛЕНДАРНЫЙ ПЛАН

Ответ дай в формате JSON с детальным планом каждого раздела."""

    sql_lines.append(f"""
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, max_tokens, temperature, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'writer_stage1'),
  'Writer V2 Stage 1: Planning',
  'Промпт для планирования структуры заявки (Stage 1)',
  '{escape_sql_string(stage1_template)}',
  'writer_v2',
  'stage1_planning',
  2000,
  0.3,
  true
);
""")

    # Stage 2 Writing (огромный промпт - упрощенная версия)
    stage2_template = """Ты профессиональный грант-райтер с 15-летним опытом написания заявок на Президентские гранты РФ.

КРИТИЧНО ВАЖНО - СТИЛЬ НАПИСАНИЯ:
✅ Официальный, деловой, бюрократический стиль
✅ Третье лицо ВСЕГДА ("проект направлен на...", "планируется...")
✅ НЕТ первого лица ("мы", "наш")
✅ Безэмоциональный тон (только факты, цифры, ссылки)

ФОРМАТ ЦИТИРОВАНИЯ:
"По данным [организация] [факт]. (ссылка: https://...)"

ДАННЫЕ ПРОЕКТА:
{user_answers}

ПЛАН СТРУКТУРЫ (из Stage 1):
{plan}

ЦИТАТЫ (минимум 10):
{citations}

ТАБЛИЦЫ (минимум 2):
{tables}

БЛОК 1 - ПРОБЛЕМА:
{research_block1}

БЛОК 2 - ГЕОГРАФИЯ:
{research_block2}

БЛОК 3 - ЦЕЛИ:
{research_block3}

ЗАДАНИЕ:
Напиши полную заявку на грант (25,000+ символов), включающую ВСЕ 9 разделов.

ТРЕБОВАНИЯ:
✅ Общий объем: 25,000+ символов
✅ Раздел 2 "Проблема": 8,000+ символов
✅ Официальный стиль, третье лицо
✅ Минимум 10 цитат
✅ 2 таблицы
✅ Календарный план в таблице

Верни результат в формате JSON с 9 секциями."""

    sql_lines.append(f"""
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, max_tokens, temperature, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'writer_stage2'),
  'Writer V2 Stage 2: Writing',
  'Промпт для написания текста заявки (Stage 2)',
  '{escape_sql_string(stage2_template)}',
  'writer_v2',
  'stage2_writing',
  8000,
  0.3,
  true
);
""")

    return "\n".join(sql_lines)


def generate_reviewer_prompts_sql():
    """Генерация SQL для Reviewer промптов"""

    sql_lines = []
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Reviewer: Goal, Backstory")
    sql_lines.append("-- ============================================================================\n")

    sql_lines.append("""
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, is_active, priority) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Reviewer Goal',
  'Цель агента Reviewer',
  'Провести финальную оценку готовности гранта к подаче и рассчитать вероятность одобрения (40-50%)',
  'reviewer',
  'goal',
  true,
  100
),
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Reviewer Backstory',
  'Предыстория агента Reviewer',
  'Ты эксперт-ревьюер грантовых заявок с 25-летним опытом работы в экспертных комиссиях. Ты оцениваешь готовность заявок к подаче на основе 4 критериев: доказательная база (40%), структура (30%), индикаторный матчинг (20%), экономика (10%). Твоя оценка точно предсказывает вероятность одобрения заявки.',
  'reviewer',
  'backstory',
  true,
  100
);
""")

    return "\n".join(sql_lines)


def main():
    """Главная функция - генерирует полную SQL миграцию"""

    print("Генерация SQL миграции для всех промптов...")

    output_file = Path(__file__).parent.parent / "database" / "migrations" / "010_migrate_all_prompts_generated.sql"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("-- ============================================================================\n")
        f.write("-- Migration 010: АВТОМАТИЧЕСКИ СГЕНЕРИРОВАННАЯ миграция всех промптов\n")
        f.write("-- Дата генерации: 2025-10-10\n")
        f.write("-- Скрипт: scripts/generate_prompts_migration.py\n")
        f.write("-- ============================================================================\n\n")

        # Researcher V2 (27 запросов)
        print("  > Генерация Researcher V2 запросов (27)...")
        f.write(generate_researcher_queries_sql())
        f.write("\n\n")

        # Writer V2
        print("  > Генерация Writer V2 промптов...")
        f.write(generate_writer_prompts_sql())
        f.write("\n\n")

        # Reviewer
        print("  > Генерация Reviewer промптов...")
        f.write(generate_reviewer_prompts_sql())
        f.write("\n\n")

    print(f"SQL миграция сгенерирована: {output_file}")
    print(f"Размер файла: {output_file.stat().st_size / 1024:.1f} KB")

    # Подсчет количества INSERT'ов
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        inserts_count = content.count('INSERT INTO agent_prompts')

    print(f"Количество промптов: {inserts_count}")

    print("\nСледующие шаги:")
    print("1. Проверьте сгенерированный файл:")
    print(f"   {output_file}")
    print("2. Примените миграцию:")
    print("   psql -h localhost -U postgres -d grantservice -f database/migrations/010_migrate_all_prompts_generated.sql")


if __name__ == '__main__':
    main()
