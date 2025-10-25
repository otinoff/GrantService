# LLM Детальное логирование - Guide

**Создано:** 2025-10-23 (Iteration 27)
**Зачем:** Понять что происходит с LLM запросами/ответами

---

## Проблема которую решает

Когда E2E тест "успешен" но результаты плохие - нужно видеть:
- Какие промпты отправляются к LLM
- Какие ответы приходят
- Используется ли правильный LLM провайдер
- Есть ли ошибки в запросах

**Пример из Iteration 27:**
- E2E тест "успешен"
- НО грантовая заявка пустая
- НО нет расхода токенов в админке GigaChat
- → Оказалось Writer использовал Claude Code вместо GigaChat!

---

## Модуль LLM Logger

### Файл: `scripts/llm_logger.py`

**Функции:**
```python
from llm_logger import get_llm_logger

logger = get_llm_logger()

# Логирование запроса (первые 500 символов)
logger.log_request(
    agent="writer",
    stage="planning",
    prompt="Напиши план...",
    model="GigaChat-2-Max"
)

# Логирование ответа (первые 500 символов)
logger.log_response(
    agent="writer",
    stage="planning",
    response="План: 1. Анализ...",
    success=True,
    tokens_used=250
)

# Логирование ошибки
logger.log_error(
    agent="writer",
    stage="planning",
    error="Connection timeout"
)

# Получить summary
summary = logger.get_summary()
print(summary)
```

**Особенности:**
- Первые 500 символов prompt/response
- Timestamp для каждого события
- Консольный вывод real-time
- Сохранение в JSONL файл
- Summary по всей сессии

**Лог файл:**
```
test_results/llm_logs/llm_dialog_YYYYMMDD_HHMMSS.jsonl
```

---

## E2E Test с логированием

### Файл: `scripts/run_e2e_with_llm_logging.py`

**Что делает:**
1. Инициализирует LLM Logger
2. Monkey-patch UnifiedLLMClient для логирования
3. Запускает Writer V2
4. Логирует все LLM запросы/ответы
5. Показывает summary в конце

**Monkey-patch:**
```python
def patch_unified_llm_client():
    """Патчим UnifiedLLMClient чтобы логировать все запросы"""
    from llm.unified_llm_client import UnifiedLLMClient

    original_generate_gigachat = UnifiedLLMClient._generate_gigachat

    async def logged_generate_gigachat(self, prompt, temperature, max_tokens):
        llm_logger = get_llm_logger()

        # Логируем запрос
        llm_logger.log_request(
            agent="writer",
            stage="gigachat_call",
            prompt=prompt,
            model=self.model
        )

        try:
            response = await original_generate_gigachat(self, prompt, temperature, max_tokens)

            # Логируем ответ
            llm_logger.log_response(
                agent="writer",
                stage="gigachat_call",
                response=response,
                success=True
            )

            return response
        except Exception as e:
            # Логируем ошибку
            llm_logger.log_error(
                agent="writer",
                stage="gigachat_call",
                error=str(e)
            )
            raise

    UnifiedLLMClient._generate_gigachat = logged_generate_gigachat
```

**Запуск:**
```bash
python -X utf8 scripts/run_e2e_with_llm_logging.py
```

---

## Консольный вывод

### Формат REQUEST:
```
================================================================================
🔵 LLM REQUEST | WRITER | planning
================================================================================
Model: GigaChat-2-Max
Prompt length: 5585 chars

Prompt preview (first 500 chars):
--------------------------------------------------------------------------------
Ты - профессиональный писатель грантовых заявок. Твоя задача - создать план...
--------------------------------------------------------------------------------
```

### Формат RESPONSE:
```
================================================================================
✅ LLM RESPONSE | WRITER | planning
================================================================================
Success: True
Response length: 2345 chars
Tokens used: 450

Response preview (first 500 chars):
--------------------------------------------------------------------------------
План грантовой заявки:

1. КРАТКОЕ ОПИСАНИЕ ПРОЕКТА (300-500 слов)
   - Основная идея проекта
   - Целевая аудитория
...
--------------------------------------------------------------------------------
```

### Формат ERROR:
```
================================================================================
❌ LLM ERROR | WRITER | planning
================================================================================
Error: Connection timeout after 30 seconds
================================================================================
```

---

## JSONL формат лога

Каждая строка - JSON объект:

### Request:
```json
{
  "type": "request",
  "timestamp": "2025-10-23T22:52:47.123456",
  "agent": "writer",
  "stage": "planning",
  "model": "GigaChat-2-Max",
  "prompt_preview": "Ты - профессиональный писатель...",
  "prompt_length": 5585,
  "kwargs": {"temperature": 0.7}
}
```

### Response:
```json
{
  "type": "response",
  "timestamp": "2025-10-23T22:52:50.234567",
  "agent": "writer",
  "stage": "planning",
  "success": true,
  "response_preview": "План грантовой заявки:\n\n1. КРАТКОЕ...",
  "response_length": 2345,
  "kwargs": {"tokens_used": 450}
}
```

### Error:
```json
{
  "type": "error",
  "timestamp": "2025-10-23T22:52:55.345678",
  "agent": "writer",
  "stage": "planning",
  "error": "Connection timeout",
  "kwargs": {}
}
```

---

## Summary формат

```json
{
  "requests": 3,
  "responses": 2,
  "errors": 1,
  "total_prompt_length": 15000,
  "total_response_length": 8000,
  "by_agent": {
    "writer": {
      "requests": 3,
      "responses": 2,
      "errors": 1
    }
  }
}
```

---

## Как это помогло в Iteration 27

### 1. Обнаружили неправильный провайдер
**В логах:**
```
INFO:llm.unified_llm_client:🔧 Инициализирован CLAUDE_CODE клиент с моделью 'sonnet'
```

**Проблема:** Writer использует Claude Code вместо GigaChat!

### 2. Нашли ошибки Expert Agent
**В логах:**
```
ERROR:writer_agent_v2:❌ WriterV2: Ошибка получения требований от Expert Agent: [WinError 10061]
```

**Проблема:** Expert Agent не может подключиться к Qdrant

### 3. Увидели что промпты отправляются
**В логах:**
```
INFO:writer_agent_v2:📤 WriterV2 Stage 1: Отправляем запрос на планирование (промпт: 5585 символов)
```

**Вывод:** Промпты формируются правильно

---

## Best Practices

### 1. Используй для debugging
Когда E2E тест "успешен" но результаты неожиданные:
```bash
python -X utf8 scripts/run_e2e_with_llm_logging.py
```

### 2. Проверяй первые 500 символов
Этого достаточно чтобы понять:
- Правильный ли промпт
- Есть ли ответ
- Какого качества ответ

### 3. Анализируй JSONL файл
Для глубокого анализа:
```python
import json

with open('llm_dialog_20251023_225225.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        entry = json.loads(line)
        if entry['type'] == 'error':
            print(f"Error at {entry['timestamp']}: {entry['error']}")
```

### 4. Проверяй summary
Быстрая проверка что все запросы прошли:
```python
summary = logger.get_summary()
if summary['errors'] > 0:
    print(f"Warning: {summary['errors']} errors occurred")
```

---

## Windows encoding fix

**Важно для Windows:**
```python
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
```

Иначе будет `UnicodeEncodeError` при выводе emoji!

---

## Результаты Iteration 27

**Благодаря детальному логированию:**
- ✅ Нашли что Writer использует Claude Code
- ✅ Нашли что Researcher использует Claude
- ✅ Исправили config.py
- ✅ Готовы протестировать с GigaChat-2-Max

**User observation:**
> "нет расхода токенов в админке гигачата"

**+ Детальное логирование** → ROOT CAUSE FOUND в течение 10 минут!

---

## Расширение для будущего

### Добавить патчи для других LLM методов:
- `_generate_perplexity()`
- `_generate_ollama()`
- `_generate_claude_code()`

### Добавить метрики:
- Latency (время ответа)
- Token usage (из response metadata)
- Success rate

### Добавить filters:
- По агенту
- По stage
- По времени

---

**Документация создана:** 2025-10-23
**Статус:** ✅ WORKING
**Используется с:** Iteration 27+
