#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест интерактивного интервьюера с моими ответами
Проект: Инклюзивная кофейня
"""

import sys
import os
import io
from pathlib import Path
import logging
import asyncio
import json

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
sys.path.insert(0, str(project_root / "web-admin"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 80)
print("🧪 ТЕСТ: Интерактивный интервьюер с простыми промптами")
print("=" * 80)

# Тестовые данные: Инклюзивная кофейня (мои ответы разного качества)
TEST_DATA = {
    # Базовая информация
    "telegram_id": 111222333,
    "username": "coffee_inclusive",
    "first_name": "Мария",
    "last_name": "Смирнова",
    "email": "maria@coffee.ru",
    "phone": "+79995554433",
    "grant_fund": "Фонд президентских грантов",

    # БЛОК 1: Базовая информация
    # (специально делаю ответы разного качества)

    "block_1_q1": "Инклюзивная кофейня",  # СЛАБЫЙ ответ - короткий

    "block_1_q2": "Создать кофейню где работают люди с инвалидностью",  # СРЕДНИЙ ответ

    "block_1_q3": """В нашем городе людям с инвалидностью очень сложно найти работу.
Работодатели не хотят их нанимать из-за предрассудков.
По статистике только 15% людей с инвалидностью трудоустроены.
Это приводит к социальной изоляции и бедности.""",  # ХОРОШИЙ ответ - детальный

    "block_1_q4": "Люди с инвалидностью 18-45 лет",  # СЛАБЫЙ ответ - мало деталей

    "block_1_q5": "Москва",  # СЛАБЫЙ ответ - только город

    # БЛОК 2: Методология и бюджет

    "block_2_q1": """1. Открыть кофейню
2. Нанять людей
3. Обучить персонал
4. Провести рекламу""",  # СЛАБЫЙ ответ - общие фразы

    "block_2_q2": """Мы арендуем помещение 80 кв.м в центре города.
Адаптируем его для доступности (пандусы, широкие проходы).
Купим профессиональное оборудование для кофейни.
Обучим 8 сотрудников с инвалидностью работе бариста.
Запустим маркетинговую кампанию в соцсетях.""",  # ХОРОШИЙ ответ

    "block_2_q3": """1. Трудоустроено 8 человек с инвалидностью
2. Обслужено 5000+ посетителей за год
3. Средняя зарплата 35000 рублей
4. Создана доступная среда для посетителей с инвалидностью
5. Проведено 12 мастер-классов по кофе""",  # ХОРОШИЙ ответ - измеримо

    "block_2_q4": "500000",  # СЛАБЫЙ - только цифра

    "block_2_q5": """Аренда помещения: 150000
Оборудование: 200000
Обучение: 50000
Реклама: 100000""",  # СРЕДНИЙ ответ - есть цифры но кратко

    # БЛОК 3: Команда, партнёры, риски

    "block_3_q1": "Я руководитель, есть бухгалтер и технолог",  # СЛАБЫЙ ответ

    "block_3_q2": """Всероссийское общество инвалидов - помощь в подборе персонала
Департамент соцзащиты - консультации
Учебный центр Кофемания - обучение бариста""",  # ХОРОШИЙ ответ

    "block_3_q3": "Риск что не будет клиентов",  # ОЧЕНЬ СЛАБЫЙ ответ

    "block_3_q4": """После гранта кофейня будет работать на самоокупаемости.
Выручка от продажи кофе покроет зарплаты и аренду.
Средний чек 300 рублей, планируем 50-70 чеков в день.""",  # ХОРОШИЙ ответ

    "block_3_q5": "12 месяцев"  # ОК
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
        # Используем Claude Code для качественного анализа
        agent = InteractiveInterviewerAgent(db, llm_provider="claude_code")
        print("✅ Агент создан (LLM: Claude Code / Sonnet 4.5)")
    except Exception as e:
        print(f"❌ Ошибка создания агента: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n🎤 Шаг 4: Запуск интерактивного интервью...")
    print("   Тема: Инклюзивная кофейня")
    print("   Ответы: Разного качества (от слабых до хороших)")
    print("   (Это займет ~2-3 минуты, идут вызовы LLM к wrapper 178.236.17.55:8000)...")

    try:
        result = await agent.conduct_interview_with_audit(user_data=TEST_DATA)
        print("✅ Интервью завершено")
    except Exception as e:
        print(f"❌ Ошибка интервью: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n📊 Шаг 5: Сохранение результатов...")

    # Сохраняем полный результат
    with open('test_interactive_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("✅ Результат сохранен: test_interactive_result.json")

    # Создаем дамп диалога
    dialog_dump = create_dialog_dump(result)
    with open('test_interactive_dialog.txt', 'w', encoding='utf-8') as f:
        f.write(dialog_dump)
    print("✅ Дамп диалога: test_interactive_dialog.txt")

    print("\n" + "=" * 80)
    print("📋 КРАТКИЕ РЕЗУЛЬТАТЫ")
    print("=" * 80)
    print(f"Статус:        {result['status']}")
    print(f"Anketa ID:     {result['anketa_id']}")
    print(f"Audit Score:   {result['audit_score']}/100")
    print(f"Время:         {result.get('processing_time', 'N/A'):.1f} сек")

    # Проверка промежуточных аудитов
    feedback = result.get('interactive_feedback', [])
    print(f"\n🔍 ПРОМЕЖУТОЧНЫЕ АУДИТЫ ({len(feedback)}):")
    for block in feedback:
        print(f"  Блок {block['block']}: score={block['audit_score']}/10, уточнений={len(block.get('clarifications', {}))}")

    print("\n" + "=" * 80)
    print("✅ ТЕСТ ЗАВЕРШЕН!")
    print("=" * 80)

    return True

def create_dialog_dump(result):
    """Создать текстовый дамп диалога"""
    from interactive_interviewer_agent import INTERVIEW_QUESTIONS

    dump = []
    dump.append("=" * 80)
    dump.append("ДАМП ИНТЕРАКТИВНОГО ДИАЛОГА")
    dump.append("=" * 80)
    dump.append("")
    dump.append(f"Проект: Инклюзивная кофейня")
    dump.append(f"Anketa ID: {result['anketa_id']}")
    dump.append(f"Финальная оценка: {result['audit_score']}/100")
    dump.append("")

    anketa = result['anketa']

    # БЛОК 1
    dump.append("=" * 80)
    dump.append("БЛОК 1: БАЗОВАЯ ИНФОРМАЦИЯ")
    dump.append("=" * 80)
    dump.append("")

    block1_questions = INTERVIEW_QUESTIONS["block_1"]
    block1_answers = [
        anketa.get('project_name', ''),
        anketa.get('project_goal', ''),
        anketa.get('problem_statement', ''),
        anketa.get('target_audience', ''),
        anketa.get('geography', '')
    ]

    for i, (q, a) in enumerate(zip(block1_questions, block1_answers), 1):
        dump.append(f"❓ ВОПРОС {i}: {q}")
        dump.append("")
        dump.append(f"💬 ОТВЕТ {i}:")
        dump.append(a)
        dump.append("")
        dump.append("-" * 80)
        dump.append("")

    # БЛОК 2
    dump.append("=" * 80)
    dump.append("БЛОК 2: МЕТОДОЛОГИЯ И БЮДЖЕТ")
    dump.append("=" * 80)
    dump.append("")

    block2_questions = INTERVIEW_QUESTIONS["block_2"]
    block2_answers = [
        anketa.get('project_tasks', ''),
        anketa.get('methodology', ''),
        anketa.get('expected_results', ''),
        anketa.get('budget', ''),
        anketa.get('budget_breakdown', '')
    ]

    for i, (q, a) in enumerate(zip(block2_questions, block2_answers), 6):
        dump.append(f"❓ ВОПРОС {i}: {q}")
        dump.append("")
        dump.append(f"💬 ОТВЕТ {i}:")
        dump.append(a)
        dump.append("")
        dump.append("-" * 80)
        dump.append("")

    # БЛОК 3
    dump.append("=" * 80)
    dump.append("БЛОК 3: КОМАНДА, ПАРТНЁРЫ, РИСКИ")
    dump.append("=" * 80)
    dump.append("")

    block3_questions = INTERVIEW_QUESTIONS["block_3"]
    block3_answers = [
        anketa.get('team_experience', ''),
        anketa.get('partnerships', ''),
        anketa.get('risk_management', ''),
        anketa.get('sustainability', ''),
        anketa.get('project_duration', '')
    ]

    for i, (q, a) in enumerate(zip(block3_questions, block3_answers), 11):
        dump.append(f"❓ ВОПРОС {i}: {q}")
        dump.append("")
        dump.append(f"💬 ОТВЕТ {i}:")
        dump.append(a)
        dump.append("")
        dump.append("-" * 80)
        dump.append("")

    # ПРОМЕЖУТОЧНЫЕ АУДИТЫ
    dump.append("=" * 80)
    dump.append("ПРОМЕЖУТОЧНЫЕ АУДИТЫ")
    dump.append("=" * 80)
    dump.append("")

    feedback = result.get('interactive_feedback', [])
    for block_feedback in feedback:
        block_num = block_feedback['block']
        score = block_feedback['audit_score']
        clarifications = block_feedback.get('clarifications', {})

        dump.append(f"🔍 БЛОК {block_num} - Оценка: {score}/10")
        dump.append("")

        if clarifications:
            dump.append("💡 Уточняющие вопросы:")
            for key, value in clarifications.items():
                dump.append(f"  - {key}: {value}")
        else:
            dump.append("✅ Уточнений не требуется")

        dump.append("")
        dump.append("-" * 80)
        dump.append("")

    # ФИНАЛ
    dump.append("=" * 80)
    dump.append("ФИНАЛЬНАЯ ОЦЕНКА")
    dump.append("=" * 80)
    dump.append("")
    dump.append(f"Audit Score: {result['audit_score']}/100")
    dump.append("")

    recommendations = result.get('recommendations', [])
    if recommendations:
        dump.append("📝 РЕКОМЕНДАЦИИ:")
        for i, rec in enumerate(recommendations, 1):
            dump.append(f"{i}. {rec}")

    dump.append("")
    dump.append("=" * 80)
    dump.append("Конец дампа")
    dump.append("=" * 80)

    return "\n".join(dump)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())

        if success:
            print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО")
            sys.exit(0)
        else:
            print("\n❌ ТЕСТ НЕ ПРОЙДЕН")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
