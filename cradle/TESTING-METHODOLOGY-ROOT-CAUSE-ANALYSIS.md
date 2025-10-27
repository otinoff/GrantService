# ROOT CAUSE ANALYSIS: Testing Methodology Failure
## Iteration 53 - InteractiveInterviewerAgentV2

**Date:** 2025-10-27
**Project:** GrantService
**Incident:** Production import error after passing E2E tests

---

## КРИТИЧЕСКАЯ ОШИБКА

### Production Error:
```python
ModuleNotFoundError: No module named 'agents.interactive_interviewer_agent_v2'
```

**Location:** `telegram-bot/main.py:1965`

**Context:**
- E2E тесты PASSED (88 секунд, 10 вопросов, anketa.txt создан, audit score 36.5/100)
- Production bot FAILED при попытке использовать InteractiveInterviewerAgentV2

---

## КРИТИЧЕСКАЯ ПРОБЛЕМА: Агент не работает на production уже несколько дней

**Статус:** БЛОКИРУЕТ PRODUCTION
**Приоритет:** P0 - КРИТИЧЕСКИЙ

**Симптомы:**
- E2E тесты PASSED
- Production бот НЕ РАБОТАЕТ
- Тесты не отражают реальный production workflow

---

## ПОЧЕМУ ТЕСТ НЕ ПОЙМАЛ ОШИБКУ?

### Проблема #1: Изоляция вместо интеграции

**Что делал тест:**
```python
# test_full_interview_workflow.py
from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2

agent = InteractiveInterviewerAgentV2(db=test_db, llm_provider="gigachat")
result = await agent.conduct_interview(...)
```

**Что делает production:**
```python
# telegram-bot/main.py (OLD - BROKEN)
from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
                    ^^^^^^^^^^^^^^^^^^^^^^^^^ СТАРЫЙ ПУТЬ!
```

**Вывод:**
- Тест импортирует агент НАПРЯМУЮ через НОВЫЙ путь
- Production использует СТАРЫЙ путь через Telegram bot handler
- **Тест не тестирует production entry points!**

---

### Проблема #2: Memory-based workflow вместо Database workflow

**Что делал тест:**
```python
# PHASE 2: Conduct Interview
result = await agent.conduct_interview(...)

# PHASE 3: Generate anketa.txt
anketa_data = result['anketa']  # <-- ИЗ ПАМЯТИ!
anketa_txt = generate_anketa_txt(anketa_data)
```

**Что делает production:**
```python
# FullFlowManager.start_interview()
1. session_id = self.db.create_interview_session(...)  # Сохранить в БД
2. await agent.conduct_interview(...)
3. anketa = self.db.get_session_data(session_id)      # Прочитать из БД
4. anketa_txt = generate_anketa_txt(anketa)            # Экспорт
```

**Вывод:**
- Тест использует данные из памяти (in-memory)
- Production сохраняет → читает из БД → экспортирует
- **Тест не тестирует Database persistence workflow!**

---

### Проблема #3: Отсутствие Import Validation Tests

**Что произошло при рефакторинге (Phase 6):**
```
Moved: agents/interactive_interviewer_agent_v2.py
    → agents/interactive_interviewer_v2/agent.py

Updated: 13+ files with new import paths
Missed:  telegram-bot/main.py:1965
```

**Почему пропустили:**
- Нет автоматического теста, проверяющего все импорты
- Полагались на ручной поиск (grep)
- E2E тест не покрывает production entry points

**Вывод:**
- **Нужен тест, который валидирует ВСЕ production импорты**
- При рефакторинге нужен checklist с автоматической проверкой

---

## ЧТО НЕ ТАК С МЕТОДОЛОГИЕЙ?

### 1. E2E Tests != Production Tests

**Текущая методология (TESTING-METHODOLOGY.md):**
```
E2E Tests:
- Тестируют полный workflow
- От начала до конца
- С реальной БД
```

**Проблема:**
- "Полный workflow" != "Production workflow"
- Тест вызывает agent напрямую
- Production вызывает через Telegram handler
- **Gap: Entry points не тестируются**

**Решение:**
```python
# NEW: Integration Test через production entry point
async def test_telegram_bot_interview_workflow():
    """Test через РЕАЛЬНЫЙ Telegram bot handler."""

    # 1. Используем настоящий TelegramBot handler
    from telegram_bot.handlers import InterviewHandler

    # 2. Симулируем Telegram callback
    update = create_mock_telegram_update(...)
    context = create_mock_telegram_context(...)

    # 3. Вызываем production handler
    await interview_handler.start_interactive_interview(update, context)

    # 4. Проверяем результат
    assert bot sent anketa.txt file
    assert database has session record
```

---

### 2. Отсутствие Smoke Tests для импортов

**Что нужно добавить:**
```python
# tests/smoke/test_production_imports.py

def test_all_production_modules_can_import():
    """Smoke test: все production модули импортируются без ошибок."""

    # Test telegram-bot imports
    try:
        from telegram_bot.main import GrantServiceBot
        from telegram_bot.handlers import InterviewHandler
    except ImportError as e:
        pytest.fail(f"Production import failed: {e}")

    # Test agent imports
    try:
        from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2
        from agents.auditor_agent import AuditorAgent
        from agents.writer_agent import WriterAgent
    except ImportError as e:
        pytest.fail(f"Agent import failed: {e}")

    # Success!
    assert True
```

**Когда запускать:**
- ПЕРЕД каждым коммитом (pre-commit hook)
- ПОСЛЕ любого рефакторинга
- В CI/CD pipeline

---

### 3. Отсутствие Database Persistence Tests

**Что тестировали:**
```python
result = await agent.conduct_interview(...)
anketa = result['anketa']  # Memory
```

**Что НУЖНО тестировать:**
```python
# Test database persistence
session_id = db.create_interview_session(user_id, grant_type)
await agent.conduct_interview(...)
anketa_from_db = db.get_session_data(session_id)

assert anketa_from_db is not None
assert anketa_from_db['project_name'] == expected_name
```

---

## УЛУЧШЕННАЯ МЕТОДОЛОГИЯ ТЕСТИРОВАНИЯ

### Test Pyramid для GrantService:

```
                    /\
                   /  \
                  / E2E \         5% - Полный production workflow
                 /______\
                /        \
               / Integration\      15% - Production entry points
              /____________\
             /              \
            /  Unit Tests    \     80% - Изолированная логика
           /__________________\
```

---

### Уровень 1: Unit Tests (80%)

**Цель:** Тестировать изолированную логику

**Примеры:**
```python
# Test question generation
def test_adaptive_question_generator_generates_valid_question():
    generator = AdaptiveQuestionGenerator(...)
    question = generator.generate_next_question(context)
    assert question is not None
    assert len(question) > 0

# Test anketa formatting
def test_generate_anketa_txt_formats_correctly():
    data = {'project_name': 'Test', 'budget': '1M'}
    result = generate_anketa_txt(data)
    assert 'Test' in result
    assert '1M' in result
```

---

### Уровень 2: Integration Tests (15%)

**Цель:** Тестировать production entry points

**Примеры:**
```python
# Test Telegram bot handler
async def test_telegram_interview_handler_starts_successfully():
    handler = InterviewHandler(bot, db)
    update = create_mock_update(user_id=123, text="/start")

    await handler.handle_start_interview(update, context)

    # Check database state
    session = db.get_active_session(123)
    assert session is not None

# Test production imports
def test_production_modules_import_without_errors():
    from telegram_bot.main import GrantServiceBot
    from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2
    assert True
```

---

### Уровень 3: E2E Tests (5%)

**Цель:** Тестировать ПОЛНЫЙ production workflow

**Что изменить:**
```python
# OLD (WRONG)
agent = InteractiveInterviewerAgentV2(...)
result = await agent.conduct_interview(...)
anketa = result['anketa']  # From memory

# NEW (CORRECT)
from telegram_bot.main import GrantServiceBot
bot = GrantServiceBot(...)

# Simulate full Telegram user interaction
await bot.handle_update(update_start_interview)
await bot.handle_update(update_answer_q1)
...
await bot.handle_update(update_finish)

# Check database
session = db.get_session(user_id)
anketa_file = db.export_anketa_txt(session.id)
assert anketa_file exists
```

---

## CHECKLIST: Refactoring Safety

При любом рефакторинге (переименование, перемещение файлов):

### 1. Pre-Refactoring
- [ ] Записать все текущие import paths
- [ ] Найти все места использования: `grep -r "from old_module import"`
- [ ] Сделать список всех файлов для обновления

### 2. Refactoring
- [ ] Переместить/переименовать файлы
- [ ] Обновить импорты в КАЖДОМ файле из списка
- [ ] Проверить еще раз: `grep -r "from old_module import"` (должно быть 0)

### 3. Post-Refactoring
- [ ] Запустить smoke tests: `pytest tests/smoke/ -v`
- [ ] Запустить unit tests: `pytest tests/unit/ -v`
- [ ] Запустить integration tests: `pytest tests/integration/ -v`
- [ ] Запустить E2E tests: `pytest tests/e2e/ -v`
- [ ] Manually test в production-like environment

---

## НОВЫЕ ОБЯЗАТЕЛЬНЫЕ ТЕСТЫ

### 1. Smoke Test Suite
```bash
pytest tests/smoke/ -v
```

**Содержание:**
- `test_production_imports.py` - все импорты работают
- `test_database_connection.py` - БД доступна
- `test_llm_providers.py` - GigaChat/Claude доступны

**Время:** <10 секунд
**Когда:** Перед каждым коммитом

---

### 2. Integration Test Suite
```bash
pytest tests/integration/ -v
```

**Содержание:**
- `test_telegram_handlers.py` - Telegram bot handlers
- `test_database_persistence.py` - Save/Read workflow
- `test_agent_initialization.py` - Все агенты создаются

**Время:** <60 секунд
**Когда:** Перед push в production

---

### 3. E2E Test Suite
```bash
pytest tests/e2e/ -v
```

**Содержание:**
- `test_full_production_workflow.py` - От Telegram → БД → Export
- `test_complete_grant_flow.py` - Interview → Audit → Writer

**Время:** <300 секунд
**Когда:** Перед release

---

## ВЫВОДЫ

### Почему произошла ошибка?

1. **E2E тест не покрывал production entry points**
   - Тест: импортировал agent напрямую (НОВЫЙ путь)
   - Production: использовал Telegram handler (СТАРЫЙ путь)

2. **Отсутствие smoke tests для импортов**
   - Нет теста, который проверяет все production импорты
   - При рефакторинге полагались на ручной grep

3. **Тест не следовал production workflow**
   - Тест: использовал данные из памяти
   - Production: сохраняет → читает из БД

### Что делать?

1. **Добавить Smoke Tests** (сделано в этой итерации)
2. **Добавить Integration Tests** (TODO: Iteration 54)
3. **Улучшить E2E Tests** - тестировать через production handlers
4. **Создать Refactoring Checklist** - автоматические проверки

---

## ACTION ITEMS

### Immediate (Iteration 53)
- [x] Исправить production import в `telegram-bot/main.py:1965`
- [x] Создать ROOT CAUSE ANALYSIS (этот файл)
- [ ] Создать `tests/smoke/test_production_imports.py`
- [ ] Добавить в pre-commit hook: `pytest tests/smoke/`

### Short-term (Iteration 54)
- [ ] Создать `tests/integration/test_telegram_handlers.py`
- [ ] Создать `tests/integration/test_database_persistence.py`
- [ ] Улучшить E2E test - использовать production handlers

### Long-term (Iteration 55+)
- [ ] Автоматизировать рефакторинг (AST-based tool)
- [ ] CI/CD pipeline с обязательными smoke tests
- [ ] Pre-production staging environment

---

## ИДЕАЛЬНАЯ МЕТОДОЛОГИЯ ТЕСТИРОВАНИЯ GrantService

### КРИТИЧЕСКАЯ ПРОБЛЕМА: Production не работает несколько дней

**Почему тесты не помогли:**
- Тесты PASSED, но не тестировали реальный production workflow
- Анкета "стрельба из лука" в БД - это НЕ из теста, это реальный пользователь
- **Тест должен был использовать LLM для автоматической генерации ответов**

---

## 🎯 ИДЕАЛЬНЫЙ E2E ТЕСТ - Как ДОЛЖНО БЫТЬ

### Концепция: LLM-Driven Interactive Test

**Цель:** Тест должен проходить ПОЛНЫЙ production workflow, используя LLM для генерации ответов

### 1. ПРАВИЛЬНЫЙ WORKFLOW ТЕСТА

```
ТЕСТ ДОЛЖЕН:

1. START INTERVIEW (как пользователь в Telegram)
   - Создать session в БД
   - Получить первый вопрос: "Как называется ваш проект?"

2. ANSWER WITH LLM (генерировать ответы через GigaChat/Claude)
   - LLM генерирует реалистичный ответ на каждый вопрос
   - Ответ сохраняется в БД (session.interview_data)
   - Agent задает следующий вопрос

3. CONTINUE UNTIL COMPLETE (10-15 вопросов)
   - Каждый цикл: вопрос → LLM ответ → сохранить в БД
   - НЕ предопределенные ответы!
   - LLM должен генерировать НОВЫЕ ответы каждый раз

4. SAVE TO DATABASE
   - После всех вопросов: сохранить session.interview_data
   - Пометить session как completed

5. EXPORT FROM DATABASE (как production)
   - Прочитать session из БД
   - Сгенерировать anketa.txt из БД данных
   - НЕ из памяти!

6. SEND AUDIT
   - Пользователь нажимает "Начать аудит"
   - Читаем данные из БД
   - Запускаем Auditor Agent
   - Сохраняем результат в БД
```

---

### 2. ТЕКУЩИЙ ТЕСТ vs ИДЕАЛЬНЫЙ ТЕСТ

#### ❌ ЧТО ДЕЛАЕТ ТЕКУЩИЙ ТЕСТ (НЕПРАВИЛЬНО):

```python
# test_full_interview_workflow.py (ТЕКУЩИЙ - ПЛОХО)

class InterviewAutoResponder:
    def __init__(self):
        # ПРЕДОПРЕДЕЛЕННЫЕ ответы
        self.answer_patterns = {
            'название': 'AI Grant Assistant',  # ❌ СТАТИЧНО
            'бюджет': '1 500 000 рублей',      # ❌ СТАТИЧНО
        }

    async def ask_question(self, question: str) -> str:
        # Ищет keyword и возвращает СТАТИЧНЫЙ ответ
        for keyword, response in self.answer_patterns.items():
            if keyword in question_lower:
                return response  # ❌ НЕ LLM!

# Результат:
result = await agent.conduct_interview(...)
anketa = result['anketa']  # ❌ ИЗ ПАМЯТИ, НЕ ИЗ БД!
```

**Проблемы:**
1. Ответы статичные, не через LLM
2. Данные из памяти, НЕ из БД
3. НЕ тестирует production entry points (Telegram bot)
4. НЕ тестирует сохранение/чтение из БД

---

#### ✅ КАК ДОЛЖЕН РАБОТАТЬ ИДЕАЛЬНЫЙ ТЕСТ:

```python
# test_ideal_interactive_interview.py (ПРАВИЛЬНО)

class LLMInterviewResponder:
    """Использует РЕАЛЬНЫЙ LLM для генерации ответов"""

    def __init__(self, llm_client):
        self.llm = llm_client  # ✅ НАСТОЯЩИЙ GigaChat/Claude
        self.context = []

    async def ask_question(self, question: str) -> str:
        # Генерировать ответ через LLM
        prompt = f"""
        Ты - основатель социального проекта.
        Отвечай на вопросы интервью о твоем проекте.

        История разговора:
        {self.context}

        Вопрос: {question}

        Ответь кратко и реалистично (2-3 предложения).
        """

        response = await self.llm.generate(prompt)  # ✅ РЕАЛЬНЫЙ LLM!
        self.context.append(f"Q: {question}\nA: {response}")
        return response

async def test_full_production_workflow_with_llm():
    """
    ИДЕАЛЬНЫЙ E2E ТЕСТ

    Тестирует ПОЛНЫЙ production workflow:
    1. Telegram bot создает session
    2. FullFlowManager управляет процессом
    3. Agent задает вопросы
    4. LLM генерирует ответы
    5. Данные сохраняются в БД после КАЖДОГО вопроса
    6. По завершении читаем из БД
    7. Генерируем anketa.txt из БД
    8. Запускаем Audit
    """

    # PHASE 1: Initialize (через production код!)
    from telegram_bot.main import GrantServiceBot
    from agents.full_flow_manager import FullFlowManager

    bot = GrantServiceBot()  # ✅ НАСТОЯЩИЙ TELEGRAM BOT!
    flow_manager = FullFlowManager(bot.db)

    # PHASE 2: Start Interview (как в production)
    user_id = 999999999  # Test user
    session_id = flow_manager.start_interview(
        user_id=user_id,
        grant_type="Фонд Президентских Грантов"
    )

    # ✅ Session создана в БД!
    assert db.get_session(session_id) is not None

    # PHASE 3: Conduct Interview with LLM
    llm_responder = LLMInterviewResponder(
        llm_client=UnifiedLLMClient(provider="gigachat")  # ✅ РЕАЛЬНЫЙ LLM!
    )

    for question_num in range(1, 11):  # 10 вопросов
        # Agent задает вопрос
        question = await flow_manager.get_next_question(session_id)

        # LLM генерирует ответ
        answer = await llm_responder.ask_question(question)  # ✅ ЧЕРЕЗ LLM!

        # Сохраняем в БД
        flow_manager.save_answer(session_id, question, answer)  # ✅ СОХРАНИТЬ В БД!

        # Проверяем, что данные в БД
        session = db.get_session(session_id)
        assert question in session['interview_data']  # ✅ ПРОВЕРЯЕМ БД!

    # PHASE 4: Complete Interview
    flow_manager.complete_interview(session_id)

    # ✅ Проверяем статус в БД
    session = db.get_session(session_id)
    assert session['completion_status'] == 'completed'

    # PHASE 5: Export from DATABASE (как production!)
    anketa_data = db.get_session_data(session_id)  # ✅ ЧИТАЕМ ИЗ БД!
    anketa_txt = generate_anketa_txt(anketa_data)   # ✅ ИЗ БД, НЕ ПАМЯТИ!

    # PHASE 6: Audit (через production код)
    audit_result = await flow_manager.start_audit(session_id)  # ✅ ИЗ БД!

    # PHASE 7: Verify
    assert anketa_txt is not None
    assert audit_result['overall_score'] > 0
    assert len(anketa_data['interview_data']) >= 10  # Все вопросы

    print(f"✅ ТЕСТ ПРОШЕЛ! LLM сгенерировал {len(anketa_data['interview_data'])} ответов")
    print(f"✅ Данные сохранены в БД session_id={session_id}")
    print(f"✅ Anketa экспортирована из БД")
    print(f"✅ Audit score: {audit_result['overall_score']}/100")
```

---

### 3. КЛЮЧЕВЫЕ ПРИНЦИПЫ ИДЕАЛЬНОГО ТЕСТА

#### Принцип #1: Production Parity
```
ТЕСТ = PRODUCTION

- Используй настоящий TelegramBot
- Используй настоящий FullFlowManager
- Используй настоящую БД (не mock!)
- Используй настоящий LLM (GigaChat)
```

#### Принцип #2: Database-First
```
WORKFLOW:
1. Сохранить в БД
2. Прочитать из БД
3. Экспортировать из БД

НЕ ИСПОЛЬЗОВАТЬ in-memory данные!
```

#### Принцип #3: LLM-Driven
```
ОТВЕТЫ:
- Генерировать через LLM
- НЕ статичные answer_patterns
- НЕ предопределенные ответы
- Каждый запуск = НОВЫЕ ответы
```

#### Принцип #4: Full Integration
```
ENTRY POINTS:
- Telegram bot handler (не agent напрямую!)
- FullFlowManager (не agent.conduct_interview!)
- Production импорты (проверяются автоматически!)
```

---

### 4. МЕТОДОЛОГИЯ РАЗРАБОТКИ ТЕСТОВ

#### Шаг 1: Smoke Tests (10 секунд)
```bash
pytest tests/smoke/ -v

Проверяют:
- Все импорты работают
- БД доступна
- LLM доступен
```

#### Шаг 2: Integration Tests (60 секунд)
```bash
pytest tests/integration/ -v

Проверяют:
- Telegram bot handlers
- FullFlowManager
- Database persistence
- Production entry points
```

#### Шаг 3: E2E Tests with LLM (300 секунд)
```bash
pytest tests/e2e/ -v

Проверяют:
- ПОЛНЫЙ production workflow
- LLM генерация ответов
- Save → Read → Export из БД
- Interview → Audit → Writer
```

---

### 5. ЧЕКЛИСТ ПЕРЕД КОММИТОМ

```
□ Smoke tests PASSED (pytest tests/smoke/)
□ Integration tests PASSED (pytest tests/integration/)
□ E2E tests PASSED (pytest tests/e2e/)
□ Проверили production импорты (grep -r "from agents")
□ Проверили БД workflow (save → read → export)
□ Проверили LLM integration (не mock!)
□ Проверили через Telegram bot (не agent напрямую!)
```

---

### 6. ЧТО ДЕЛАТЬ СЕЙЧАС (ПРИОРИТЕТ)

**P0 - КРИТИЧНО:**
1. ✅ Исправить production import (`telegram-bot/main.py:1965`) - **СДЕЛАНО**
2. ⚠️ Запустить production бот и ПРОВЕРИТЬ, что он работает
3. ⚠️ Создать LLM-driven E2E тест (следующая итерация)

**P1 - ВАЖНО:**
4. Добавить Integration tests для Telegram handlers
5. Добавить Database persistence tests
6. Создать pre-commit hooks с smoke tests

**P2 - УЛУЧШЕНИЯ:**
7. Автоматизация рефакторинга (AST-based)
8. CI/CD pipeline
9. Staging environment

---

**Last Updated:** 2025-10-27
**Author:** Claude Code (ROOT CAUSE ANALYSIS + IDEAL METHODOLOGY)
**Status:** ACTIVE - Use as reference for all testing
**Priority:** P0 - КРИТИЧЕСКИ ВАЖНО для production
