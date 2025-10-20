#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест DatabasePromptManager - нового менеджера промптов
"""

import sys
import os

# Добавляем путь к web-admin
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'web-admin'))

from utils.prompt_manager import DatabasePromptManager, get_database_prompt_manager


def test_prompt_manager():
    """Тест работы DatabasePromptManager"""

    print("=" * 80)
    print("ТЕСТ DatabasePromptManager")
    print("=" * 80)

    # Создаем экземпляр
    pm = get_database_prompt_manager()

    # Тест 1: Статистика
    print("\n1. СТАТИСТИКА ПРОМПТОВ:")
    print("-" * 80)
    stats = pm.get_stats()
    print(f"Всего промптов: {stats['total_prompts']}")
    print(f"Типов агентов: {stats['agent_types']}")
    print(f"Кеш валиден: {stats['cache_valid']}")
    print(f"\nПромпты по агентам:")
    for agent, count in stats['agent_counts'].items():
        print(f"  - {agent}: {count} промптов")

    # Тест 2: Interviewer Goal
    print("\n2. INTERVIEWER GOAL:")
    print("-" * 80)
    goal = pm.get_prompt('interviewer', 'goal')
    print(goal[:200] + "..." if goal and len(goal) > 200 else goal)

    # Тест 3: Interviewer Fallback Questions
    print("\n3. INTERVIEWER FALLBACK QUESTIONS:")
    print("-" * 80)
    fallback_questions = pm.get_all_prompts('interviewer', 'fallback_question')
    print(f"Найдено fallback вопросов: {len(fallback_questions)}")
    for i, q in enumerate(fallback_questions[:3], 1):
        print(f"\n  Вопрос {i} (order_index={q['order_index']}):")
        print(f"  {q['prompt_template']}")

    # Тест 4: Researcher V2 Queries
    print("\n4. RESEARCHER V2 QUERIES:")
    print("-" * 80)
    for block in [1, 2, 3]:
        queries = pm.get_researcher_queries(block)
        print(f"Блок {block}: {len(queries)} запросов")
        if queries:
            print(f"  Первый запрос: {queries[0][:100]}...")

    # Тест 5: Writer V2 Config
    print("\n5. WRITER V2 CONFIG:")
    print("-" * 80)
    config = pm.get_agent_config('writer_v2')
    print(f"Goal: {config['goal'][:150]}...")
    print(f"Backstory: {config['backstory'][:150]}...")

    # Тест 6: Writer Stage 1 Prompt с переменными
    print("\n6. WRITER STAGE 1 PROMPT (с переменными):")
    print("-" * 80)
    stage1_vars = {
        'project_name': 'Детский спорт в регионах',
        'description': 'Развитие детского спорта',
        'problem': 'Недостаток спортивной инфраструктуры',
        'solution': 'Строительство спортплощадок',
        'budget': '500000',
        'timeline': '12',
        'block1_summary': 'Проблема подтверждена статистикой',
        'block2_summary': 'География: Московская область',
        'block3_summary': 'Цели: Охват 1000 детей',
        'sources_count': '27',
        'key_facts_count': '15'
    }

    stage1_prompt = pm.get_writer_stage_prompt(1, stage1_vars)
    if stage1_prompt:
        print(f"Длина промпта: {len(stage1_prompt)} символов")
        print(f"Первые 300 символов:\n{stage1_prompt[:300]}...")
    else:
        print("ОШИБКА: Промпт не найден!")

    # Тест 7: Auditor LLM Prompts
    print("\n7. AUDITOR LLM PROMPTS:")
    print("-" * 80)
    for prompt_type in ['llm_completeness', 'llm_quality', 'llm_compliance', 'llm_innovation']:
        prompt = pm.get_prompt('auditor', prompt_type)
        if prompt:
            print(f"  {prompt_type}: {len(prompt)} символов")

    # Тест 8: Reviewer Config
    print("\n8. REVIEWER CONFIG:")
    print("-" * 80)
    reviewer_config = pm.get_agent_config('reviewer')
    print(f"Goal: {reviewer_config['goal']}")
    print(f"Backstory: {reviewer_config['backstory'][:150]}...")

    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_prompt_manager()
    except Exception as e:
        print(f"\nОШИБКА ТЕСТА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
