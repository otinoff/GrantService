"""
GrantService Test Suite

Организация тестов:
- unit/ - Unit тесты (изолированные компоненты)
- integration/ - Интеграционные тесты (несколько компонентов)
- autonomous/ - Автономные тесты (без LLM, с моками)
- smoke/ - Smoke тесты (быстрая проверка)

Запуск:
- pytest tests/unit/          # Только unit тесты
- pytest tests/integration/   # Интеграционные
- pytest tests/                # Все тесты
- pytest -v tests/             # Verbose режим
"""
