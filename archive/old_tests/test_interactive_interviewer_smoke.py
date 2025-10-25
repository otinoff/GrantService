#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMOKE TEST: InteractiveInterviewerAgent
Быстрая проверка что агент работает корректно

Тест:
1. Импортирует InteractiveInterviewerAgent
2. Создает экземпляр с тестовыми данными
3. Запускает интервью на тему "Лучные клубы Кемерово"
4. Проверяет результат: anketa_id, audit_score
5. Выводит результат в консоль

Author: Claude Code
Date: 2025-10-20
"""

import sys
import os
import io
from pathlib import Path
import logging
import asyncio

# Fix UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "data" / "database"))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "telegram-bot" / "services"))
sys.path.insert(0, str(project_root / "web-admin"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 80)
print("🧪 SMOKE TEST: InteractiveInterviewerAgent")
print("=" * 80)

# Тестовые данные: Лучные клубы Кемерово (упрощенная версия)
TEST_DATA = {
    # Базовая информация
    "telegram_id": 999888777,
    "username": "test_archery",
    "first_name": "Тестовый",
    "last_name": "Пользователь",
    "email": "test@example.com",
    "phone": "+79001234567",
    "grant_fund": "Фонд президентских грантов",

    # БЛОК 1
    "block_1_q1": "Развитие стрельбы из лука в Кемерово",
    "block_1_q2": "Создание сети лучных клубов для вовлечения молодёжи в спорт",
    "block_1_q3": "В Кемерово нет инфраструктуры для занятий стрельбой из лука. Молодёжи негде заниматься.",
    "block_1_q4": "Молодёжь 14-25 лет, семьи с детьми",
    "block_1_q5": "Кемерово, Кемеровская область",

    # БЛОК 2
    "block_2_q1": "Открыть 3 лучных клуба, обучить тренеров, провести соревнования",
    "block_2_q2": "Аренда площадок, закупка оборудования, обучение тренеров, проведение мастер-классов",
    "block_2_q3": "500+ участников, 3 клуба, 5 тренеров, 10 мастер-классов",
    "block_2_q4": "800000",
    "block_2_q5": "Аренда 300k, оборудование 250k, обучение 100k, мероприятия 100k, онлайн-платформа 50k",

    # БЛОК 3
    "block_3_q1": "Руководитель Иван Петров, 5 тренеров с опытом стрельбы из лука",
    "block_3_q2": "Департамент спорта Кемеровской области, КемГУ, клуб реконструкции",
    "block_3_q3": "Риск низкой посещаемости - митигация через рекламу. Риск травм - через инструктаж.",
    "block_3_q4": "Членские взносы 300 руб/месяц, платные мероприятия, партнёрство с депспорта",
    "block_3_q5": "12 месяцев"
}

async def main():
    """Основная функция теста"""

    print("\n📦 Шаг 1: Импорт модулей...")
    try:
        from models import GrantServiceDatabase
        from interactive_interviewer_agent import InteractiveInterviewerAgent
        print("✅ Импорт успешен")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

    print("\n🗄️  Шаг 2: Подключение к БД...")
    try:
        db = GrantServiceDatabase()
        print("✅ БД подключена")
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

    print("\n🤖 Шаг 3: Создание InteractiveInterviewerAgent...")
    try:
        # ВАЖНО: Используем Claude Code для АДАПТИВНОГО интервьюера
        agent = InteractiveInterviewerAgent(db, llm_provider="claude_code")
        print("✅ Агент создан (LLM: Claude Code / Sonnet 4.5)")
    except Exception as e:
        print(f"❌ Ошибка создания агента: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n🎤 Шаг 4: Запуск интерактивного интервью...")
    print("   Тема: Лучные клубы Кемерово")
    print("   LLM: Claude Code (Sonnet 4.5)")
    print("   (Это займет ~2-3 минуты, идут вызовы LLM к wrapper 178.236.17.55:8000)...")

    try:
        result = await agent.conduct_interview_with_audit(user_data=TEST_DATA)
        print("✅ Интервью завершено")
    except Exception as e:
        print(f"❌ Ошибка интервью: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n📊 Шаг 5: Проверка результатов...")

    # Проверка обязательных полей
    required_fields = ['status', 'anketa', 'anketa_id', 'audit_score']
    missing = [f for f in required_fields if f not in result]

    if missing:
        print(f"❌ Отсутствуют поля: {missing}")
        return False

    if result['status'] != 'success':
        print(f"❌ Статус не success: {result.get('status')}")
        return False

    print(f"✅ Все обязательные поля присутствуют")

    print("\n" + "=" * 80)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТА")
    print("=" * 80)
    print(f"Статус:        {result['status']}")
    print(f"Anketa ID:     {result['anketa_id']}")
    print(f"Audit Score:   {result['audit_score']}/100")
    print(f"Время:         {result.get('processing_time', 'N/A')} сек")

    # Проверка анкеты
    anketa = result['anketa']
    print(f"\n📝 АНКЕТА:")
    print(f"  Название:    {anketa.get('project_name', 'N/A')[:50]}...")
    print(f"  Цель:        {anketa.get('project_goal', 'N/A')[:50]}...")
    print(f"  География:   {anketa.get('geography', 'N/A')}")
    print(f"  Бюджет:      {anketa.get('budget', 'N/A')}")

    # Проверка рекомендаций
    recommendations = result.get('recommendations', [])
    print(f"\n💡 РЕКОМЕНДАЦИИ ({len(recommendations)}):")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"  {i}. {rec[:80]}...")

    # Проверка промежуточных аудитов
    feedback = result.get('interactive_feedback', [])
    print(f"\n🔍 ПРОМЕЖУТОЧНЫЕ АУДИТЫ ({len(feedback)}):")
    for block in feedback:
        print(f"  Блок {block['block']}: score={block['audit_score']}/10, уточнений={len(block.get('clarifications', {}))}")

    print("\n" + "=" * 80)
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("=" * 80)

    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())

        if success:
            print("\n🎉 SMOKE TEST PASSED")
            print("✅ InteractiveInterviewerAgent ГОТОВ к использованию")
            sys.exit(0)
        else:
            print("\n❌ SMOKE TEST FAILED")
            print("⚠️  InteractiveInterviewerAgent НЕ ГОТОВ")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
