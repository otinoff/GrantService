#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E тест для Researcher Agent V2
Проверяет выполнение всех 27 экспертных запросов на реальных данных
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Установка кодировки UTF-8 для Windows консоли
if os.name == 'nt':  # Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Добавляем пути
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from data.database.models import GrantServiceDatabase
from test_db_wrapper import DatabaseWrapper


async def test_researcher_v2_full_workflow():
    """Тест полного workflow Researcher V2"""

    print("="*80)
    print("E2E ТЕСТ: Researcher Agent V2 - 27 экспертных запросов")
    print("="*80)
    print()

    # 1. Подключение к БД
    print("[STEP 1] Подключение к PostgreSQL...")
    try:
        raw_db = GrantServiceDatabase()
        db = DatabaseWrapper(raw_db)  # Оборачиваем для совместимости
        print("[OK] Подключение установлено")
    except Exception as e:
        print(f"[ERROR] Не удалось подключиться к БД: {e}")
        print("Проверьте переменные окружения: PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD")
        return False

    # 2. Найти существующую анкету для теста
    print("\n[STEP 2] Поиск тестовой анкеты...")
    try:
        # Ищем сессию с завершенным статусом и anketa_id
        result = db.execute_query("""
            SELECT id, anketa_id, telegram_id, started_at
            FROM sessions
            WHERE completion_status = 'completed'
              AND anketa_id IS NOT NULL
            ORDER BY started_at DESC
            LIMIT 1
        """, fetch_one=True)

        if not result or not result.get('anketa_id'):
            print("[WARN] Не найдены завершенные анкеты с anketa_id, создаем тестовую...")
            # Создадим минимальную тестовую анкету
            anketa_id = await create_test_anketa(db)
        else:
            anketa_id = result['anketa_id']  # Используем anketa_id, не session id!
            print(f"[OK] Найдена анкета: {anketa_id}")
            print(f"    Session ID: {result['id']}")
            print(f"    Telegram ID: {result['telegram_id']}")
            print(f"    Created: {result['started_at']}")

    except Exception as e:
        print(f"[ERROR] Ошибка поиска анкеты: {e}")
        import traceback
        traceback.print_exc()
        # Создадим тестовую анкету
        anketa_id = "TEST_RESEARCHER_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"[WARN] Используем тестовый ID: {anketa_id}")

    # 3. Инициализация Researcher V2
    print("\n[STEP 3] Инициализация Researcher V2...")
    try:
        # Импортируем после того как пути добавлены
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))
        from agents.researcher_agent_v2 import ResearcherAgentV2

        researcher = ResearcherAgentV2(db, llm_provider="claude_code")
        print("[OK] Researcher V2 инициализирован")
    except ImportError as e:
        print(f"[ERROR] Не удалось импортировать ResearcherAgentV2: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации Researcher V2: {e}")
        return False

    # 4. Запуск 27 запросов
    print("\n[STEP 4] Запуск 27 экспертных запросов...")
    print("⏳ Это займет 2-5 минут...")
    print()

    start_time = datetime.now()

    try:
        # Запускаем полный workflow
        research_result = await researcher.research_with_expert_prompts(anketa_id)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # 5. Анализ результатов
        print("\n" + "="*80)
        print("[STEP 5] АНАЛИЗ РЕЗУЛЬТАТОВ")
        print("="*80)

        status = research_result.get('status')
        print(f"\n✓ Статус: {status}")

        if status == 'completed':
            metadata = research_result.get('metadata', {})

            print(f"\n📊 СТАТИСТИКА:")
            print(f"   - Всего запросов: {metadata.get('total_queries', 0)}")
            print(f"   - Успешных: {metadata.get('successful_queries', 0)}")
            print(f"   - С ошибками: {metadata.get('failed_queries', 0)}")
            print(f"   - Всего источников: {metadata.get('total_sources', 0)}")
            print(f"   - Всего результатов: {metadata.get('total_results', 0)}")
            print(f"   - Время выполнения: {elapsed:.1f}s")

            # Проверяем структуру данных
            research_data = research_result.get('research_results', {})

            print(f"\n📦 СТРУКТУРА ДАННЫХ:")
            print(f"   - Block 1 (Проблема): {'✓' if 'block1_problem' in research_data else '✗'}")
            print(f"   - Block 2 (География): {'✓' if 'block2_geography' in research_data else '✗'}")
            print(f"   - Block 3 (Цели): {'✓' if 'block3_goals' in research_data else '✗'}")

            # Примеры результатов
            if research_data.get('block1_problem'):
                block1 = research_data['block1_problem']
                print(f"\n🔍 ПРИМЕР: Block 1 - Проблема")
                print(f"   Запросов в блоке: {len(block1.get('queries', []))}")

                if block1.get('queries'):
                    first_query = block1['queries'][0]
                    print(f"   Первый запрос: {first_query.get('query', 'N/A')[:80]}...")
                    print(f"   Результатов: {first_query.get('results_count', 0)}")
                    print(f"   Источников: {len(first_query.get('sources', []))}")

            # 6. Проверка сохранения в БД
            print(f"\n[STEP 6] Проверка сохранения в БД...")
            try:
                db_record = db.execute_query("""
                    SELECT
                        research_id,
                        status,
                        jsonb_typeof(research_results) as data_type,
                        created_at
                    FROM researcher_research
                    WHERE anketa_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (anketa_id,), fetch_one=True)

                if db_record:
                    print(f"[OK] Данные сохранены в БД:")
                    print(f"   - Research ID: {db_record['research_id']}")
                    print(f"   - Status: {db_record['status']}")
                    print(f"   - Data Type: {db_record['data_type']}")
                    print(f"   - Created: {db_record['created_at']}")
                else:
                    print("[WARN] Запись в БД не найдена")

            except Exception as e:
                print(f"[ERROR] Ошибка проверки БД: {e}")
                import traceback
                traceback.print_exc()

            # Итоговая оценка
            print("\n" + "="*80)
            success_rate = metadata.get('successful_queries', 0) / 27 * 100

            if success_rate >= 90:
                print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО")
                print(f"   Успешность: {success_rate:.1f}% (≥90%)")
            elif success_rate >= 70:
                print("⚠️ ТЕСТ ПРОЙДЕН С ПРЕДУПРЕЖДЕНИЯМИ")
                print(f"   Успешность: {success_rate:.1f}% (70-90%)")
            else:
                print("❌ ТЕСТ НЕ ПРОЙДЕН")
                print(f"   Успешность: {success_rate:.1f}% (<70%)")

            print("="*80)

            return success_rate >= 70

        else:
            print(f"[ERROR] Исследование завершилось со статусом: {status}")
            print(f"Сообщение: {research_result.get('message', 'N/A')}")
            return False

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        pass  # db is GrantServiceDatabase, doesn't need to be closed


async def create_test_anketa(db):
    """Создать минимальную тестовую анкету"""

    print("   Создание тестовой анкеты...")

    try:
        # Генерируем уникальный anketa_id
        anketa_id = "TEST_E2E_" + datetime.now().strftime("%Y%m%d_%H%M%S")

        # Вставляем тестового пользователя если его нет
        db.execute_query("""
            INSERT INTO users (telegram_id, username, full_name, role)
            VALUES (999999, 'test_e2e', 'Test E2E User', 'user')
            ON CONFLICT (telegram_id) DO NOTHING
        """)

        # Вставляем минимальную сессию с anketa_id
        result = db.execute_query("""
            INSERT INTO sessions (
                telegram_id,
                anketa_id,
                current_step,
                completion_status,
                started_at,
                last_activity,
                questions_answered,
                total_questions
            )
            VALUES (999999, %s, 'completed', 'completed', NOW(), NOW(), 10, 10)
            RETURNING id, anketa_id
        """, (anketa_id,), fetch_one=True)

        if result:
            print(f"[OK] Создана тестовая анкета:")
            print(f"    Anketa ID: {result['anketa_id']}")
            print(f"    Session ID: {result['id']}")
            return result['anketa_id']
        else:
            print(f"[ERROR] Не удалось создать анкету, fallback")
            return anketa_id

    except Exception as e:
        print(f"[ERROR] Не удалось создать анкету: {e}")
        import traceback
        traceback.print_exc()
        # Fallback - используем строковый ID
        return "TEST_E2E_" + datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    try:
        result = asyncio.run(test_researcher_v2_full_workflow())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
