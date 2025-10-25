# 🧪 Методология автономного тестирования для GrantService

**Дата создания:** 2025-10-22
**Цель:** Документировать как Claude Code должен тестировать код САМОСТОЯТЕЛЬНО без участия пользователя

---

## 🎯 Главный принцип

> **"Не заставляй меня тестировать - тестируй сам!"**

Claude Code должен:
- ✅ Сам писать тесты
- ✅ Сам запускать тесты
- ✅ Сам анализировать результаты
- ✅ Сам исправлять ошибки
- ❌ НЕ просить пользователя "запустите тесты"
- ❌ НЕ просить пользователя "проверьте результат"

---

## 📋 Когда применять автономное тестирование

### 1. После написания нового кода
```
Написали новый агент → СРАЗУ пишем тесты → СРАЗУ запускаем → СРАЗУ исправляем ошибки
```

### 2. После рефакторинга
```
Изменили логику → Обновляем тесты → Запускаем → Проверяем что ничего не сломалось
```

### 3. Перед коммитом
```
Финальная проверка → Запускаем все тесты → 100% pass rate → Готово к коммиту
```

---

## 🔧 Инструменты для автономного тестирования

### Python: pytest + asyncio + unittest.mock

**Пример структуры теста:**
```python
import asyncio
import pytest
from unittest.mock import Mock, patch

class AutonomousTestRunner:
    """Автономный тестировщик - сам запускает и проверяет все"""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def log_test(self, test_name, passed, message=""):
        """Логирование результата теста"""
        status = "PASS" if passed else "FAIL"
        emoji = "[OK]" if passed else "[FAIL]"

        result = {
            "test": test_name,
            "status": status,
            "message": message
        }

        self.test_results.append(result)

        if passed:
            self.tests_passed += 1
            print(f"{emoji} {status}: {test_name}")
        else:
            self.tests_failed += 1
            print(f"{emoji} {status}: {test_name}")
            if message:
                print(f"   ERROR: {message}")

    async def test_example(self):
        """Пример теста"""
        try:
            # Arrange
            component = MyComponent()

            # Act
            result = await component.do_something()

            # Assert
            assert result == expected_value, f"Expected {expected_value}, got {result}"

            self.log_test("test_example", True)
            return True

        except Exception as e:
            self.log_test("test_example", False, str(e))
            return False

    async def run_all_tests(self):
        """Запустить все тесты автономно"""
        print("=" * 80)
        print("AUTONOMOUS TEST RUNNER - Running all tests automatically")
        print("No user intervention required!")
        print("=" * 80)

        # Запускаем все тесты
        await self.test_example()
        # ... другие тесты

        # Итоги
        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"\nTotal tests: {total_tests}")
        print(f"Passed: {self.tests_passed} [OK]")
        print(f"Failed: {self.tests_failed} [FAIL]")
        print(f"Pass rate: {pass_rate:.1f}%")

        return self.tests_failed == 0

async def main():
    """Главная функция - запускает все автономно"""
    runner = AutonomousTestRunner()
    success = await runner.run_all_tests()

    # Exit code для CI/CD
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📝 Шаблон автономного теста

### 1. Базовая структура файла
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автономное тестирование [НАЗВАНИЕ КОМПОНЕНТА]

Тесты запускаются БЕЗ участия пользователя!
"""

import sys
import json
import asyncio
from pathlib import Path

# Импортируем тестируемый компонент
from my_component import MyComponent

class AutonomousTestRunner:
    # ... (см. выше)
    pass

async def main():
    runner = AutonomousTestRunner()
    success = await runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Типы тестов

#### Тест 1: Инициализация
```python
async def test_basic_initialization(self):
    """Тест: Базовая инициализация компонента"""
    try:
        component = MyComponent(param1="value1")

        # Проверяем что инициализировался корректно
        assert component.param1 == "value1"
        assert component.is_ready == True

        self.log_test("test_basic_initialization", True)
        return True

    except Exception as e:
        self.log_test("test_basic_initialization", False, str(e))
        return False
```

#### Тест 2: Проверка политики (например, LLM provider)
```python
async def test_claude_code_is_default(self):
    """Тест: Claude Code - провайдер по умолчанию"""
    try:
        # Без указания provider
        interviewer = AdaptiveInterviewerWithQuestionBank()

        # Должен быть claude_code по умолчанию
        assert interviewer.llm_provider == "claude_code", \
            f"Default should be claude_code, got {interviewer.llm_provider}"

        self.log_test("test_claude_code_is_default", True)
        return True

    except Exception as e:
        self.log_test("test_claude_code_is_default", False, str(e))
        return False

async def test_no_gigachat_by_default(self):
    """Тест: НЕТ автоматического использования GigaChat"""
    try:
        interviewer = AdaptiveInterviewerWithQuestionBank(llm_client=None)

        # Проверяем что НЕ gigachat
        assert interviewer.llm_provider != "gigachat", \
            "Should NOT default to gigachat!"

        self.log_test("test_no_gigachat_by_default", True)
        return True

    except Exception as e:
        self.log_test("test_no_gigachat_by_default", False, str(e))
        return False
```

#### Тест 3: Mock режим (без реального LLM)
```python
async def test_mock_full_workflow(self):
    """Тест: Полный workflow в mock режиме"""
    try:
        component = MyComponent(llm_client=None)  # Mock режим

        # Тестовые данные
        test_inputs = ["input1", "input2", "input3"]

        # Выполняем workflow
        for inp in test_inputs:
            result = await component.process(inp)
            assert result is not None, "Result should not be None"

        # Проверяем итоговый результат
        final_result = component.get_result()
        assert len(final_result) > 0, "Final result should not be empty"

        self.log_test("test_mock_full_workflow", True)
        return True

    except Exception as e:
        self.log_test("test_mock_full_workflow", False, str(e))
        return False
```

#### Тест 4: Структура данных
```python
async def test_data_structure(self):
    """Тест: Структура банка вопросов"""
    try:
        interviewer = AdaptiveInterviewerWithQuestionBank()

        # Проверяем все вопросы
        for q_id, data in interviewer.QUESTION_BANK.items():
            # Проверяем наличие обязательных полей
            assert 'text' in data, f"{q_id} missing 'text'"
            assert 'priority' in data, f"{q_id} missing 'priority'"

            # Проверяем валидность значений
            assert data['priority'] in ['P0', 'P1', 'P2'], \
                f"{q_id} invalid priority: {data['priority']}"

            assert len(data['text']) > 10, \
                f"{q_id} text too short: {data['text']}"

        self.log_test("test_data_structure", True)
        return True

    except Exception as e:
        self.log_test("test_data_structure", False, str(e))
        return False
```

---

## 🚀 Процесс автономного тестирования

### Шаг 1: Написать тесты
```python
# Создать файл: autonomous_test_runner.py
class AutonomousTestRunner:
    # Минимум 5-6 тестов для покрытия основных сценариев
    async def test_1_initialization(self): ...
    async def test_2_basic_functionality(self): ...
    async def test_3_policy_compliance(self): ...
    async def test_4_data_structure(self): ...
    async def test_5_full_workflow(self): ...
    async def test_6_error_handling(self): ...
```

### Шаг 2: Запустить тесты через Bash
```bash
cd "C:\Path\To\Project"
python autonomous_test_runner.py
```

### Шаг 3: Анализировать результаты
```
✅ Все тесты прошли (100%)
   → Код готов к следующему этапу

❌ Есть падающие тесты
   → Анализируем ошибки
   → Исправляем код
   → Запускаем снова
   → Повторяем до 100% pass rate
```

### Шаг 4: Сохранить результаты
```python
# Сохраняем в JSON для истории
results_file = Path(__file__).parent / "test_results.json"
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': '2025-10-22',
        'total': total_tests,
        'passed': self.tests_passed,
        'failed': self.tests_failed,
        'pass_rate': pass_rate,
        'results': self.test_results
    }, f, indent=2, ensure_ascii=False)
```

---

## 🎯 Критерии успешного автономного теста

### Минимальные требования:
- ✅ Тесты запускаются БЕЗ ошибок импорта
- ✅ Тесты НЕ требуют ввода от пользователя
- ✅ Тесты НЕ требуют внешних сервисов (mock LLM, mock DB)
- ✅ Тесты выводят понятные сообщения об ошибках
- ✅ Тесты сохраняют результаты в JSON

### Целевые показатели:
- 🎯 Pass rate ≥ 100% (все тесты зеленые)
- 🎯 Время выполнения < 10 секунд
- 🎯 Покрытие кода ≥ 80%
- 🎯 Тестирование всех критичных путей

---

## 🔍 Примеры из реальных проектов

### Пример 1: Adaptive Interviewer (2025-10-22)

**Файл:** `autonomous_test_runner.py`

**Тесты:**
1. ✅ test_basic_initialization - инициализация с Claude Code
2. ✅ test_first_question_is_q1 - первый вопрос всегда Q1
3. ✅ test_claude_code_is_default - Claude Code по умолчанию
4. ✅ test_no_gigachat_by_default - НЕТ GigaChat по умолчанию
5. ✅ test_question_bank_structure - структура банка вопросов
6. ✅ test_mock_full_interview - полное интервью в mock режиме

**Результат:** 6/6 PASS (100%)

**Что проверяли:**
- LLM Provider Policy (Claude Code ONLY)
- Банк вопросов (10 вопросов, приоритеты P0/P1/P2)
- Mock режим работает без LLM
- Анкета заполняется корректно

**Как запускали:**
```bash
cd "C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_InteractiveInterviewer_Development"
python autonomous_test_runner.py
```

**Что исправили:**
- ❌ Проблема: Anketa пустая (conversation_history не сохранялся)
- ✅ Решение: Обновили логику - Q1 добавляется в историю сразу, ответы обновляют последнюю запись
- ✅ Результат: Все тесты прошли

---

## 📊 Mock стратегии для автономных тестов

### 1. Mock LLM Client
```python
class MockLLMClient:
    """Mock для UnifiedLLMClient"""

    async def generate_async(self, prompt, **kwargs):
        """Возвращает фиксированный ответ вместо реального LLM"""
        return {
            'content': json.dumps({
                "next_action": "ask_from_bank",
                "next_question": {"id": "Q2", "text": "..."},
                "should_finish": False
            })
        }
```

### 2. Mock Database
```python
class MockDatabase:
    """Mock для PostgreSQL"""

    def __init__(self):
        self.data = {}

    def save(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)
```

### 3. Mock Qdrant
```python
class MockQdrantClient:
    """Mock для Qdrant векторной БД"""

    def search(self, collection_name, query_vector, limit=5):
        """Возвращает фейковые результаты поиска"""
        return [
            {"id": 1, "score": 0.85, "payload": {"text": "Mock result 1"}},
            {"id": 2, "score": 0.72, "payload": {"text": "Mock result 2"}},
        ]
```

### 4. Mock Telegram Bot API
```python
class MockTelegramBot:
    """Mock для Telegram Bot API"""

    def __init__(self):
        self.messages_sent = []

    async def send_message(self, chat_id, text):
        self.messages_sent.append({
            'chat_id': chat_id,
            'text': text,
            'timestamp': datetime.now()
        })
        return {'ok': True, 'message_id': len(self.messages_sent)}
```

---

## 🛠️ Отладка падающих тестов

### Шаг 1: Анализируем сообщение об ошибке
```
[FAIL] FAIL: test_mock_full_interview
   ERROR: Anketa should not be empty
```

### Шаг 2: Добавляем debug output
```python
async def test_mock_full_interview(self):
    try:
        # ... код теста ...

        # Debug output
        print(f"DEBUG: conversation_history length: {len(interviewer.conversation_history)}")
        print(f"DEBUG: conversation_history: {interviewer.conversation_history}")

        anketa = interviewer.get_anketa()
        print(f"DEBUG: anketa: {anketa}")

        assert len(anketa) > 0, "Anketa should not be empty"
        # ...
```

### Шаг 3: Находим root cause
```
DEBUG: conversation_history length: 0
DEBUG: conversation_history: []
DEBUG: anketa: {}
```

**Root cause:** Q1 не добавлялся в conversation_history!

### Шаг 4: Исправляем код
```python
# Было:
if len(self.conversation_history) == 0:
    return {...}  # Возвращаемся без добавления в историю

# Стало:
if len(self.conversation_history) == 0:
    self.conversation_history.append({  # Добавляем в историю!
        'question_id': 'Q1',
        'question_text': self.QUESTION_BANK['Q1']['text'],
        'is_clarifying': False
    })
    return {...}
```

### Шаг 5: Запускаем тесты снова
```bash
python autonomous_test_runner.py
```

### Шаг 6: Проверяем результат
```
[OK] PASS: test_mock_full_interview
...
Pass rate: 100.0%
[SUCCESS] ALL TESTS PASSED!
```

---

## 🎓 Best Practices

### 1. Всегда тестируй в mock режиме первым делом
```python
# ✅ ПРАВИЛЬНО - сначала mock, потом real LLM
component = MyComponent(llm_client=None)  # Mock режим

# ❌ НЕПРАВИЛЬНО - сразу real LLM (дорого и медленно)
component = MyComponent(llm_client=UnifiedLLMClient())
```

### 2. Используй assert с понятными сообщениями
```python
# ✅ ПРАВИЛЬНО
assert result == expected, f"Expected {expected}, got {result}"

# ❌ НЕПРАВИЛЬНО
assert result == expected  # Непонятно что пошло не так
```

### 3. Логируй все тесты
```python
# ✅ ПРАВИЛЬНО
self.log_test("test_name", True, "Optional success message")

# ❌ НЕПРАВИЛЬНО
return True  # Нет логирования
```

### 4. Сохраняй результаты в JSON
```python
# ✅ ПРАВИЛЬНО - можно отслеживать историю
with open('test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# ❌ НЕПРАВИЛЬНО - результаты потеряются
print(results)
```

### 5. Проверяй политики (Claude Code ONLY!)
```python
# ✅ ПРАВИЛЬНО - всегда проверяем что используется Claude Code
async def test_claude_code_is_default(self):
    component = MyComponent()
    assert component.llm_provider == "claude_code"

# ❌ НЕПРАВИЛЬНО - не проверяем политику
# (может случайно использоваться GigaChat!)
```

---

## 📝 Чеклист перед запуском тестов

- [ ] Тесты написаны (минимум 5-6 тестов)
- [ ] Тесты покрывают критичные сценарии
- [ ] Используется mock для LLM/DB/API
- [ ] Тесты НЕ требуют ввода пользователя
- [ ] Тесты НЕ требуют внешних сервисов
- [ ] Добавлено логирование результатов
- [ ] Результаты сохраняются в JSON
- [ ] Проверяется политика LLM (Claude Code ONLY)
- [ ] Есть assert с понятными сообщениями
- [ ] Exit code: 0 если success, 1 если fail

---

## 🚨 Что НЕЛЬЗЯ делать

### ❌ НЕ просить пользователя тестировать
```
# НЕПРАВИЛЬНО:
"Теперь запустите тесты и сообщите результат"

# ПРАВИЛЬНО:
*Запускает тесты сам через Bash tool*
*Анализирует результаты*
*Исправляет ошибки*
*Запускает снова*
```

### ❌ НЕ использовать реальный LLM в тестах
```python
# НЕПРАВИЛЬНО - дорого и медленно
llm_client = UnifiedLLMClient(provider="claude_code")

# ПРАВИЛЬНО - mock
llm_client = None  # Mock режим
```

### ❌ НЕ игнорировать падающие тесты
```
# НЕПРАВИЛЬНО:
"5 из 6 тестов прошли, достаточно"

# ПРАВИЛЬНО:
"5 из 6 прошли, исправляю 6-й тест до 100%"
```

### ❌ НЕ тестировать вручную через print()
```python
# НЕПРАВИЛЬНО - manual testing
print(f"Result: {result}")
# *User checks if result is correct*

# ПРАВИЛЬНО - automated testing
assert result == expected, f"Expected {expected}, got {result}"
```

---

## 📚 Ссылки на примеры

### Реальные autonomous тесты в проекте:
- `01_Projects/2025-10-20_InteractiveInterviewer_Development/autonomous_test_runner.py`
- `GrantService/test_bot_interactive.py` (методология Telegram бота)
- `GrantService/test_qdrant_search.py` (методология Qdrant)

### Документация:
- `LLM_PROVIDER_POLICY.md` - политика LLM провайдера
- `INTERVIEWER_PHILOSOPHY.md` - философия интервьюера
- `GRANTSERVICE_PROJECT_PHILOSOPHY.md` - философия проекта

---

## ✅ Итоговый алгоритм

```
1. Написали код
   ↓
2. Написали autonomous_test_runner.py (5-6 тестов)
   ↓
3. Запустили через Bash: python autonomous_test_runner.py
   ↓
4. Анализируем результаты:

   ✅ 100% pass rate → Готово!

   ❌ Есть ошибки → Исправляем → Запускаем снова → Повторяем до 100%
   ↓
5. Сохранили test_results.json
   ↓
6. Готово к следующему этапу!
```

---

**Главное правило:**
> Если ты Claude Code написал код - ты же и тестируешь его САМ!
> Не перекладывай тестирование на пользователя!

---

**Дата создания:** 2025-10-22
**Автор:** Claude Code + User Feedback
**Версия:** 1.0
**Статус:** ✅ ОБЯЗАТЕЛЬНА К ПРИМЕНЕНИЮ
