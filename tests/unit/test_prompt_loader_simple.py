#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест PromptLoader - генерация 27 запросов

Автор: AI Integration Specialist
Дата: 2025-10-08
"""

import sys
import os

# Установить UTF-8 для вывода в консоль Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем пути
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.prompt_loader import ResearcherPromptLoader


def main():
    """Запустить тест PromptLoader"""
    print("="*80)
    print("ТЕСТ: PromptLoader - генерация 27 запросов")
    print("="*80)

    # Тестовая анкета
    test_anketa = {
        'anketa_id': 'TEST-001',
        'user_id': 12345,
        'answers': {
            'problem_and_significance': 'Низкая доступность спортивных секций для детей с ПТСР',
            'geography': 'Астраханская область',
            'sphere': 'Спорт и здоровье',
            'target_group': 'Дети 6-17 лет с ПТСР',
            'project_essence': 'Создание адаптивных спортивных программ',
            'main_goal': 'Увеличить охват детей с ПТСР спортом с 20% до 50% за 12 месяцев',
            'tasks': 'Открыть 5 спортивных секций, обучить 20 тренеров, провести 100 занятий',
            'events': 'Тренировки, мастер-классы, соревнования'
        }
    }

    # Создать loader
    loader = ResearcherPromptLoader()

    # Извлечь placeholders
    placeholders = loader.extract_placeholders(test_anketa)

    print("\n[OK] Placeholders извлечены:")
    for key, value in placeholders.items():
        value_str = str(value)[:50] if len(str(value)) > 50 else str(value)
        print(f"   - {key}: {value_str}")

    # Получить все запросы
    all_queries = loader.get_all_queries(placeholders)

    total_queries = sum(len(queries) for queries in all_queries.values())

    print(f"\n[OK] Всего запросов: {total_queries}")
    print(f"   - Блок 1 (Проблема): {len(all_queries['block1'])}")
    print(f"   - Блок 2 (География): {len(all_queries['block2'])}")
    print(f"   - Блок 3 (Цели): {len(all_queries['block3'])}")

    assert total_queries == 27, f"Ожидалось 27 запросов, получено {total_queries}"

    # Показать примеры запросов
    print("\n[INFO] Примеры запросов:")

    print(f"\nБлок 1, Запрос 1 (первые 200 символов):")
    print(f"{all_queries['block1'][0][:200]}...")

    print(f"\nБлок 2, Запрос 1 (первые 200 символов):")
    print(f"{all_queries['block2'][0][:200]}...")

    print(f"\nБлок 3, Запрос 1 (первые 200 символов):")
    print(f"{all_queries['block3'][0][:200]}...")

    print("\n" + "="*80)
    print("[OK] ТЕСТ ПРОЙДЕН УСПЕШНО")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
