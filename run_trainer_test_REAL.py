"""
Запуск Trainer Agent для РЕАЛЬНОГО тестирования Writer Agent V2 с Claude Code
Тестовые данные: Школа олимпийского резерва по стрельбе из лука

ВАЖНО: Это реальный тест с Claude Code API
- Сгенерирует НАСТОЯЩУЮ заявку на грант
- Займет ~3-5 минут
- Использует Expert Agent (векторная БД с требованиями ФПГ)
- Создаст полноценный текст заявки (15,000+ символов)
"""
import sys
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
load_dotenv(env_path)

# Добавляем пути
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database.models import GrantServiceDatabase
from agents.trainer_agent import TrainerAgent


async def main():
    """Запуск РЕАЛЬНОГО тестирования Writer Agent V2 с Claude Code"""

    print("=" * 80)
    print("TRAINER AGENT - REAL TEST: Writer Agent V2 + Claude Code + Expert Agent")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("[!] ATTENTION: This is REAL test with Claude Code API")
    print("[!] Execution time: ~3-5 minutes")
    print("[!] Will create REAL grant application")
    print()

    # Инициализация
    print("[1/3] Initialization...")
    db = GrantServiceDatabase()
    trainer = TrainerAgent(db)
    print("OK: Trainer Agent initialized")
    print()

    # Генерация тестовых данных
    print("[2/3] Generating test data (archery club)...")
    test_anketa = trainer.generate_test_anketa(project_type="sport")
    print(f"OK: Test anketa generated: {test_anketa['anketa_id']}")
    print(f"    Project: {test_anketa['user_answers']['project_name']}")
    print()

    # Запуск РЕАЛЬНОГО теста
    print("[3/3] Running Writer Agent REAL test with Claude Code...")
    print("    Mode: REAL LLM (Claude Code API)")
    print("    Expected: 15,000+ символов, 10+ цитат, 2+ таблицы")
    print("    This will:")
    print("      1. Query Expert Agent (векторная БД с требованиями ФПГ)")
    print("      2. Generate REAL grant application with Claude Code")
    print("      3. Validate quality (structure, citations, tables)")
    print("      4. Save to database")
    print()
    print("[~] Please wait 3-5 minutes...")
    print()

    results = await trainer.test_writer_functionality(
        test_case=test_anketa,
        use_real_llm=True  # 🔥 РЕАЛЬНЫЙ ТЕСТ!
    )

    # Результаты
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Status: {results['status'].upper()}")
    print(f"Agent: {results.get('agent', 'unknown')}")
    print(f"Test Type: {results.get('test_type', 'functionality')}")
    print(f"Test ID: {results.get('test_id', 'N/A')}")
    print(f"Execution time: {results['execution_time']:.2f} seconds")
    print(f"Checks passed: {results['checks_passed']}/{results['checks_total']}")
    print()

    print("Detailed checks:")
    for check_name, check_result in results['checks'].items():
        status = "[PASS]" if check_result else "[FAIL]"
        print(f"  {status} {check_name}")
    print()

    # Превью результата
    if results.get('result_preview'):
        preview = results['result_preview']
        print("Application preview:")
        print(f"  - Application number: {preview.get('application_number', 'N/A')}")
        print(f"  - Quality score: {preview.get('quality_score', 0)}/10")
        print(f"  - Citations count: {preview.get('citations_count', 0)}")
        print(f"  - Tables count: {preview.get('tables_count', 0)}")
        print(f"  - Has application: {preview.get('has_application', False)}")
        print()

    if results['errors']:
        print("[X] ERRORS:")
        for error in results['errors']:
            print(f"  - {error}")
        print()

    if results['warnings']:
        print("[!] WARNINGS:")
        for warning in results['warnings']:
            print(f"  - {warning}")
        print()

    # Путь к отчету
    if results.get('report_path'):
        print(f"[>] Report saved: {results['report_path']}")
        print()

    # Итоговое сообщение
    if results['status'] == 'passed':
        print("[OK] [OK] [OK] SUCCESS! [OK] [OK] [OK]")
        print()
        print("Real grant application generated successfully!")
        print("Writer Agent V2 + Expert Agent + Claude Code working correctly.")
    else:
        print("[X] TEST FAILED")
        print("Check errors above.")

    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())

        # Exit code
        if results['status'] == 'passed':
            print("\n[OK] Test passed successfully!")
            sys.exit(0)
        else:
            print("\n[X] Test failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[X] CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
