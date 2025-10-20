#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест Writer Agent V2 с Expert Agent
Первая интеграция векторной базы знаний ФПГ с генерацией гранта
"""
import sys
sys.path.append('C:\\SnowWhiteAI\\GrantService')

import asyncio
import logging
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорты
from data.database.models import Database
from expert_agent import ExpertAgent
from agents.writer_agent_v2 import WriterAgentV2

# Тестовые данные (проект про стрельбу из лука)
TEST_PROJECT_DATA = {
    "project_name": "Школа олимпийского резерва по стрельбе из лука 'Меткий лучник'",
    "description": "Создание современной школы олимпийского резерва для подготовки профессиональных спортсменов в области стрельбы из лука",
    "problem": "Низкий уровень развития олимпийских видов спорта в Кемеровской области, недостаток инфраструктуры для подготовки спортсменов высокого уровня",
    "solution": "Создание специализированной школы с современным оборудованием и квалифицированными тренерами",
    "target_group": "Дети и подростки 10-18 лет, проявляющие интерес к стрельбе из лука",
    "geography": "Кемеровская область - Кузбасс, город Кемерово",
    "budget": "2000000",
    "timeline": "12"
}

async def test_expert_agent_connection():
    """Проверка подключения к Expert Agent"""
    print("\n" + "="*70)
    print("ТЕСТ 1: Проверка Expert Agent")
    print("="*70 + "\n")

    try:
        expert = ExpertAgent()
        logger.info("✅ Expert Agent инициализирован")

        # Тестовый запрос
        results = expert.query_knowledge(
            question="Какие требования к названию проекта в заявке на грант ФПГ?",
            fund="fpg",
            top_k=3
        )

        print(f"\n📚 Найдено {len(results)} релевантных разделов:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['section_name']}")
            print(f"   Релевантность: {result['relevance_score']:.3f}")
            print(f"   Отрывок: {result['content'][:150]}...")

        expert.close()
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Expert Agent: {e}")
        return False


async def test_writer_with_expert():
    """Тест Writer Agent V2 с интеграцией Expert Agent"""
    print("\n" + "="*70)
    print("ТЕСТ 2: Writer Agent V2 + Expert Agent")
    print("="*70 + "\n")

    try:
        # Инициализация
        db = Database()
        writer = WriterAgentV2(db, llm_provider="gigachat")  # Используем GigaChat для русского

        # Проверяем что Expert Agent подключен
        if writer.expert_agent:
            logger.info("✅ Writer Agent: Expert Agent подключен успешно")
        else:
            logger.warning("⚠️ Writer Agent: Expert Agent НЕ подключен")

        # Создаем фейковую анкету для теста
        anketa_id = f"#AN-{datetime.now().strftime('%Y%m%d')}-test_expert-001"

        # Создаем минимальные research_results для теста
        research_results = {
            "metadata": {
                "sources_count": 27,
                "quotes_count": 45,
                "created_at": datetime.now().isoformat()
            },
            "block1_problem": {
                "summary": "В Кемеровской области наблюдается низкий уровень развития олимпийских видов спорта. По данным Минспорта, регион занимает только 45 место по количеству спортивных школ олимпийского резерва.",
                "key_facts": [
                    {
                        "fact": "Кемеровская область занимает 45 место по количеству СШОР",
                        "source": "Минспорт РФ, 2024",
                        "date": "2024-03-15"
                    },
                    {
                        "fact": "В регионе только 2 тренера по стрельбе из лука",
                        "source": "Департамент спорта Кузбасса",
                        "date": "2024-02-20"
                    }
                ],
                "programs": [
                    {
                        "name": "Спорт - норма жизни (национальный проект)",
                        "kpi": "Увеличение доли граждан, занимающихся спортом до 70% к 2030 году"
                    }
                ],
                "success_cases": [
                    {
                        "name": "Школа олимпийского резерва в Новосибирске",
                        "result": "Подготовлено 5 мастеров спорта за 3 года работы"
                    }
                ]
            },
            "block2_geography": {
                "summary": "Кемеровская область имеет население 2.6 млн человек, из них 12% - дети школьного возраста (10-18 лет). Инфраструктура для стрельбы из лука отсутствует.",
                "key_facts": [
                    {
                        "fact": "Население региона: 2.6 млн человек",
                        "source": "Росстат, 2024"
                    },
                    {
                        "fact": "Дети 10-18 лет: 312,000 человек (12%)",
                        "source": "Росстат, 2024"
                    }
                ]
            },
            "block3_goals": {
                "summary": "Создание школы олимпийского резерва позволит подготовить 50 спортсменов высокого уровня за 3 года реализации проекта.",
                "main_goal_variants": [
                    {
                        "text": "Создать современную школу олимпийского резерва по стрельбе из лука, обеспечив подготовку 50 спортсменов разрядников за 12 месяцев реализации проекта"
                    }
                ]
            }
        }

        # Сохраняем research_results в БД (для реалистичного теста)
        with db.connect() as conn:
            cursor = conn.cursor()

            # Проверяем существует ли такая запись
            cursor.execute("SELECT id FROM researcher_research WHERE anketa_id = %s", (anketa_id,))
            existing = cursor.fetchone()

            if existing:
                # Обновляем
                cursor.execute("""
                    UPDATE researcher_research
                    SET research_results = %s, status = 'completed', completed_at = NOW()
                    WHERE anketa_id = %s
                """, (json.dumps(research_results), anketa_id))
                logger.info(f"✅ Обновлены research_results для {anketa_id}")
            else:
                # Создаем новую запись
                cursor.execute("""
                    INSERT INTO researcher_research
                    (anketa_id, research_id, research_results, status, completed_at)
                    VALUES (%s, %s, %s, 'completed', NOW())
                """, (anketa_id, f"{anketa_id}-RS-001", json.dumps(research_results)))
                logger.info(f"✅ Созданы research_results для {anketa_id}")

            conn.commit()

        # Подготавливаем входные данные для Writer
        input_data = {
            "anketa_id": anketa_id,
            "user_answers": TEST_PROJECT_DATA,
            "selected_grant": {
                "name": "Фонд президентских грантов",
                "max_amount": 3000000
            },
            "requested_amount": 2000000.0,
            "project_duration": 12,
            "admin_user": "test_expert_integration"
        }

        print("\n📝 Начинаем генерацию заявки на грант...")
        print(f"   Проект: {TEST_PROJECT_DATA['project_name'][:50]}...")
        print(f"   Anketa ID: {anketa_id}")
        print(f"   LLM Provider: GigaChat (русский язык)")
        print(f"   Expert Agent: {'✅ Включен' if writer.expert_agent else '❌ Выключен'}")
        print()

        # Генерируем заявку
        result = await writer.write_application_async(input_data)

        print("\n" + "="*70)
        print("РЕЗУЛЬТАТ ГЕНЕРАЦИИ:")
        print("="*70 + "\n")

        if result['status'] == 'success':
            application = result['application']

            print(f"✅ Статус: УСПЕШНО")
            print(f"📄 Номер заявки: {result.get('application_number', 'N/A')}")
            print(f"⭐ Оценка качества: {result['quality_score']}/10")
            print(f"📊 Цитат использовано: {len(result['citations'])}")
            print(f"📈 Таблиц включено: {len(result['tables'])}")
            print(f"📝 Общий объем: {len(application.get('full_text', ''))} символов")
            print(f"🤖 Provider: {result.get('provider_used', 'N/A')}")
            print()

            # Показываем фрагменты разделов
            print("📋 ФРАГМЕНТЫ ЗАЯВКИ:\n")

            print("1️⃣ КРАТКОЕ ОПИСАНИЕ (первые 300 символов):")
            print(application.get('section_1_brief', '')[:300] + "...\n")

            print("2️⃣ ОПИСАНИЕ ПРОБЛЕМЫ (первые 500 символов):")
            print(application.get('section_2_problem', '')[:500] + "...\n")

            print("3️⃣ ЦЕЛЬ ПРОЕКТА:")
            print(application.get('section_3_goal', '')[:200] + "\n")

            # Рекомендации
            if result['suggestions']:
                print("💡 РЕКОМЕНДАЦИИ:")
                for suggestion in result['suggestions']:
                    print(f"   • {suggestion}")
                print()

            # Сохраняем в файл для проверки
            output_file = f"C:\\SnowWhiteAI\\GrantService\\grant_{anketa_id.replace('#', '').replace('-', '_')}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(application.get('full_text', ''))

            print(f"💾 Полная заявка сохранена: {output_file}")

            writer.expert_agent.close()
            return True

        else:
            print(f"❌ Ошибка: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка генерации: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Главная функция"""
    print("\n" + "🎯" * 35)
    print("  ТЕСТ ИНТЕГРАЦИИ: Writer Agent V2 + Expert Agent")
    print("  Первое использование векторной базы знаний ФПГ")
    print("🎯" * 35 + "\n")

    # Тест 1: Expert Agent
    test1_success = await test_expert_agent_connection()

    if not test1_success:
        print("\n❌ Тест Expert Agent провален. Останавливаем тестирование.")
        return

    # Небольшая пауза
    await asyncio.sleep(2)

    # Тест 2: Writer + Expert
    test2_success = await test_writer_with_expert()

    # Итоги
    print("\n" + "="*70)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print("="*70)
    print(f"Тест 1 (Expert Agent):        {'✅ ПРОЙДЕН' if test1_success else '❌ ПРОВАЛЕН'}")
    print(f"Тест 2 (Writer + Expert):     {'✅ ПРОЙДЕН' if test2_success else '❌ ПРОВАЛЕН'}")
    print("="*70 + "\n")

    if test1_success and test2_success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Интеграция работает корректно.")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте логи.")


if __name__ == "__main__":
    asyncio.run(main())
