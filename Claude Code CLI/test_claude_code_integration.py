#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование интеграции Claude Code API в GrantService

Проверяет:
1. Подключение к Claude Code API
2. Базовые операции (chat, code execution)
3. LLM Router (автоматический выбор провайдера)
4. Промпты для грантовых задач
"""

import asyncio
import json
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from shared.llm.claude_code_client import ClaudeCodeClient
from shared.llm.llm_router import LLMRouter, TaskType
from shared.llm.config import CLAUDE_CODE_API_KEY, CLAUDE_CODE_BASE_URL
from agents.prompts.claude_code_prompts import (
    create_evaluation_prompt,
    generate_budget_validation_code,
    AUDITOR_QUICK_SCORE_PROMPT
)


async def test_claude_code_client():
    """Тест базового клиента Claude Code"""
    print("\n" + "="*70)
    print("ТЕСТ 1: Claude Code Client - Базовые операции")
    print("="*70)

    try:
        async with ClaudeCodeClient(api_key=CLAUDE_CODE_API_KEY, base_url=CLAUDE_CODE_BASE_URL) as client:

            # 1. Health check
            print("\n1️⃣ Проверка здоровья API...")
            healthy = await client.check_health()
            print(f"   {'✅' if healthy else '❌'} API {'доступен' if healthy else 'недоступен'}")

            if not healthy:
                print("   ⚠️ Claude Code API недоступен. Дальнейшие тесты пропущены.")
                return False

            # 2. Список моделей
            print("\n2️⃣ Получение списка моделей...")
            models = await client.list_models()
            print(f"   Доступные модели: {models}")

            # 3. Простой чат
            print("\n3️⃣ Тест простого чата...")
            response = await client.chat(
                message="Привет! Дай короткий ответ: что такое грантовая заявка?",
                temperature=0.7,
                max_tokens=200
            )
            print(f"   Ответ Claude: {response[:150]}...")

            # 4. Чат с сессией
            print("\n4️⃣ Тест сессионного чата...")
            session_id = "test_session_123"

            await client.chat(
                message="Запомни: проект называется 'Поддержка молодых учёных'",
                session_id=session_id
            )

            response = await client.chat(
                message="Как называется проект?",
                session_id=session_id
            )
            print(f"   Ответ с контекстом: {response}")

            # 5. Выполнение кода
            print("\n5️⃣ Тест выполнения кода...")
            code = """
import json

data = {
    "актуальность": 8,
    "новизна": 7,
    "методология": 9
}

total = sum(data.values())
average = round(total / len(data), 2)

result = {
    "scores": data,
    "total": total,
    "average": average
}

print(json.dumps(result, ensure_ascii=False, indent=2))
"""

            code_result = await client.execute_code(code, language="python")
            print(f"   Результат кода: {code_result['result']}")

            # 6. Статистика
            print("\n6️⃣ Статистика клиента...")
            stats = await client.get_statistics()
            print(f"   Всего запросов: {stats['total_requests']}")
            print(f"   Успешных: {stats['successful']}")
            print(f"   Success rate: {stats['success_rate']:.1f}%")

            print("\n✅ Все тесты клиента пройдены успешно!")
            return True

    except Exception as e:
        print(f"\n❌ Ошибка тестирования клиента: {e}")
        return False


async def test_llm_router():
    """Тест LLM Router (автоматический выбор провайдера)"""
    print("\n" + "="*70)
    print("ТЕСТ 2: LLM Router - Автоматический выбор провайдера")
    print("="*70)

    try:
        async with LLMRouter() as router:

            # 1. Health check провайдеров
            print("\n1️⃣ Проверка доступности провайдеров...")
            health = await router.check_providers_health()
            print(f"   GigaChat: {'✅' if health.get('gigachat') else '❌'}")
            print(f"   Claude: {'✅' if health.get('claude') else '❌'}")

            # 2. Анализ (должен выбрать Claude)
            print("\n2️⃣ Тест ANALYSIS (должен использовать Claude)...")
            analysis = await router.generate(
                prompt="Проанализируй проект: создание молодёжного центра. Дай краткую оценку.",
                task_type=TaskType.ANALYSIS,
                temperature=0.3,
                max_tokens=300
            )
            print(f"   Анализ: {analysis[:200]}...")

            # 3. Генерация текста (должен выбрать GigaChat, но может fallback на Claude)
            print("\n3️⃣ Тест GENERATION (предпочтительно GigaChat)...")
            try:
                text = await router.generate(
                    prompt="Напиши короткое введение для грантовой заявки на создание молодёжного центра.",
                    task_type=TaskType.GENERATION,
                    temperature=0.7,
                    max_tokens=300
                )
                print(f"   Текст: {text[:200]}...")
            except Exception as e:
                print(f"   ⚠️ GigaChat недоступен, fallback на Claude: {e}")

            # 4. Оценка (должен выбрать Claude)
            print("\n4️⃣ Тест EVALUATION (должен использовать Claude)...")
            evaluation = await router.generate(
                prompt="Оцени актуальность проекта 'Молодёжный центр' по шкале 1-10. Дай только число и краткое обоснование.",
                task_type=TaskType.EVALUATION,
                temperature=0.3,
                max_tokens=200
            )
            print(f"   Оценка: {evaluation}")

            # 5. Выполнение кода
            print("\n5️⃣ Тест CODE EXECUTION...")
            code_result = await router.execute_code(
                code="print('Hello from Claude Code!')",
                language="python"
            )
            print(f"   Результат: {code_result['result']}")

            # 6. Статистика
            print("\n6️⃣ Статистика роутера...")
            stats = router.get_statistics()
            print(f"   Всего запросов: {stats['total_requests']}")
            print(f"   GigaChat: {stats['gigachat_requests']} ({stats['gigachat_percent']:.1f}%)")
            print(f"   Claude: {stats['claude_requests']} ({stats['claude_percent']:.1f}%)")
            print(f"   Fallback: {stats['fallback_count']}")

            print("\n✅ Все тесты роутера пройдены успешно!")
            return True

    except Exception as e:
        print(f"\n❌ Ошибка тестирования роутера: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_grant_prompts():
    """Тест грантовых промптов"""
    print("\n" + "="*70)
    print("ТЕСТ 3: Грантовые промпты для Claude Code")
    print("="*70)

    try:
        async with ClaudeCodeClient(api_key=CLAUDE_CODE_API_KEY) as client:

            # 1. Быстрая оценка проекта
            print("\n1️⃣ Быстрая оценка проекта...")
            project = "Создание молодёжного IT-центра для обучения программированию в малых городах"

            quick_score_prompt = AUDITOR_QUICK_SCORE_PROMPT.format(
                project_description=project
            )

            score_result = await client.chat(
                message=quick_score_prompt,
                temperature=0.3,
                max_tokens=500
            )
            print(f"   Результат оценки:\n{score_result}")

            # 2. Валидация бюджета через код
            print("\n2️⃣ Валидация бюджета (выполнение кода)...")
            budget_data = {
                "total": 1000000,
                "items": [
                    {"name": "Зарплаты", "category": "personnel", "amount": 600000},
                    {"name": "Оборудование", "category": "equipment", "amount": 300000},
                    {"name": "Расходники", "category": "materials", "amount": 50000}
                ],
                "max_item_cost": 500000,
                "category_limits": {
                    "personnel": 60,
                    "equipment": 30,
                    "materials": 10
                }
            }

            validation_code = generate_budget_validation_code(budget_data)
            validation_result = await client.execute_code(
                code=validation_code,
                language="python"
            )

            result_data = json.loads(validation_result['result'])
            print(f"   Бюджет валиден: {result_data['valid']}")
            if result_data['errors']:
                print(f"   Ошибки: {len(result_data['errors'])}")
                for error in result_data['errors']:
                    print(f"     - {error['message']}")
            if result_data['warnings']:
                print(f"   Предупреждения: {len(result_data['warnings'])}")

            # 3. Полная оценка проекта
            print("\n3️⃣ Полная оценка проекта (может занять время)...")
            project_data = {
                "название": "IT-центр для молодёжи",
                "описание": project,
                "целевая_аудитория": "Молодёжь 14-25 лет из малых городов",
                "бюджет": 1000000,
                "команда": "3 программиста, 1 методист",
                "длительность": "12 месяцев"
            }

            evaluation_prompt = create_evaluation_prompt(project_data)

            evaluation = await client.chat(
                message=evaluation_prompt,
                temperature=0.3,
                max_tokens=3000
            )

            # Попытка распарсить JSON
            try:
                eval_data = json.loads(evaluation)
                print(f"   Общий балл: {eval_data['total_score']}/{eval_data['total_max']}")
                print(f"   Рекомендация: {eval_data['recommendation']}")
                print(f"   Сильные стороны: {len(eval_data['strengths'])}")
                print(f"   Слабые стороны: {len(eval_data['weaknesses'])}")
            except json.JSONDecodeError:
                print(f"   Ответ (не JSON): {evaluation[:300]}...")

            print("\n✅ Все тесты промптов пройдены успешно!")
            return True

    except Exception as e:
        print(f"\n❌ Ошибка тестирования промптов: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Главная функция тестирования"""
    print("\n" + "🔬 " * 35)
    print("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ CLAUDE CODE API В GRANTSERVICE")
    print("🔬 " * 35)

    results = []

    # Тест 1: Базовый клиент
    results.append(await test_claude_code_client())

    # Тест 2: LLM Router
    results.append(await test_llm_router())

    # Тест 3: Грантовые промпты
    results.append(await test_grant_prompts())

    # Итоги
    print("\n" + "="*70)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*70)

    total_tests = len(results)
    passed_tests = sum(results)

    print(f"\nВсего тестов: {total_tests}")
    print(f"✅ Пройдено: {passed_tests}")
    print(f"❌ Провалено: {total_tests - passed_tests}")

    if passed_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n✅ Claude Code API полностью интегрирован в GrantService")
        print("\nСледующие шаги:")
        print("1. Обновить Auditor Agent для использования Claude Code")
        print("2. Интегрировать в Telegram Bot")
        print("3. Добавить логирование в БД")
        print("4. Настроить мониторинг")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("Проверьте ошибки выше и исправьте проблемы.")

    return passed_tests == total_tests


if __name__ == "__main__":
    # Запуск тестов
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
