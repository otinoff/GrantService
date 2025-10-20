"""
Запуск Trainer Agent для тестирования Writer Agent V2
Тестовые данные: Школа олимпийского резерва по стрельбе из лука
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
    """Запуск тестирования Writer Agent"""

    print("=" * 80)
    print("TRAINER AGENT - TEST WRITER AGENT V2")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

    # Запуск теста
    print("[3/3] Running Writer Agent test...")
    print("    Mode: MOCK (fast test without real LLM)")
    print("    This will test 6 functional checks")
    print()

    results = await trainer.test_writer_functionality(
        test_case=test_anketa,
        use_real_llm=False  # Сначала мок-тест
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
        status = "PASS" if check_result else "FAIL"
        print(f"  [{status}] {check_name}")
    print()

    if results['errors']:
        print("ERRORS:")
        for error in results['errors']:
            print(f"  - {error}")
        print()

    if results['warnings']:
        print("WARNINGS:")
        for warning in results['warnings']:
            print(f"  - {warning}")
        print()

    # Путь к отчету
    if results.get('report_path'):
        print(f"Report saved: {results['report_path']}")

    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())

        # Exit code
        if results['status'] == 'passed':
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
