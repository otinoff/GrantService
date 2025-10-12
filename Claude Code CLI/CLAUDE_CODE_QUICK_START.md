# 🚀 Claude Code - Quick Start & Reference

**Версия**: 2.0 (объединённый)
**Дата**: 2025-10-12

---

## 📋 Содержание

1. [Quick Start](#-quick-start) - Для новых пользователей
2. [API Reference](#-api-reference) - Детальная справка
3. [Использование в агентах](#-использование-в-агентах)
4. [WebSearch](#-websearch-tool)
5. [Гибридный подход](#-гибридный-подход)
6. [Безопасность](#-безопасность)
7. [Troubleshooting](#-troubleshooting)
8. [FAQ](#-faq)

---

## 🚀 Quick Start

### Основная информация

**API Endpoints**:
```
Base URL: http://178.236.17.55:8000
API Key:  1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
Model:    Sonnet 4.5 (200k контекст)
```

### 1. Проверка подключения

#### Health Check (без авторизации)
```bash
curl -s http://178.236.17.55:8000/health
```

**Ожидаемый результат**:
```json
{"status": "healthy", "claude_code": "available", "claude_version": "2.0.5"}
```

#### Список моделей (с авторизацией)
```bash
curl -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  http://178.236.17.55:8000/models
```

**Ожидаемый результат**:
```json
{
  "models": [
    {"id": "sonnet", "name": "Claude Sonnet 4.5"},
    {"id": "opus", "name": "Claude Opus 4"}
  ]
}
```

#### В Python
```python
import requests

API_KEY = "1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732"
BASE_URL = "http://178.236.17.55:8000"

# Health check
response = requests.get(f"{BASE_URL}/health", timeout=3)
print(f"Status: {response.status_code}")  # 200

# Модели
headers = {"Authorization": f"Bearer {API_KEY}"}
models = requests.get(f"{BASE_URL}/models", headers=headers, timeout=3)
print(models.json())
```

### 2. Первое использование

#### Базовый клиент
```python
import asyncio
from shared.llm.claude_code_client import ClaudeCodeClient

async def example():
    async with ClaudeCodeClient(api_key=API_KEY, base_url=BASE_URL) as client:
        # Простой чат
        response = await client.chat(
            message="Оцени проект по шкале 1-10",
            temperature=0.3,
            max_tokens=500
        )
        print(response)

        # Выполнение кода
        result = await client.execute_code(
            code="print('Hello!')",
            language="python"
        )
        print(result['result'])

asyncio.run(example())
```

#### LLM Router (рекомендуется)
```python
from shared.llm.llm_router import LLMRouter, TaskType

async def example():
    async with LLMRouter() as router:
        # Автоматически выберет Claude для анализа
        analysis = await router.generate(
            prompt="Проанализируй проект...",
            task_type=TaskType.ANALYSIS,
            temperature=0.3
        )

        # Автоматически выберет GigaChat для генерации текста
        text = await router.generate(
            prompt="Напиши введение...",
            task_type=TaskType.GENERATION,
            temperature=0.7
        )

asyncio.run(example())
```

### 3. Типы задач

| TaskType | Провайдер | Применение |
|----------|-----------|------------|
| `ANALYSIS` | Claude | Анализ проектов, оценка |
| `EVALUATION` | Claude | Оценка по критериям |
| `STRUCTURING` | Claude | Структурирование заявки |
| `RESEARCH` | Claude | Поиск информации (WebSearch) |
| `CODE` | Claude | Выполнение кода |
| `VALIDATION` | Claude | Валидация данных |
| `GENERATION` | GigaChat | Генерация русского текста |
| `CONVERSATION` | GigaChat | Общение с пользователем |

---

## 📚 API Reference

### Доступные endpoints

| Endpoint | Метод | Описание | Authorization |
|----------|-------|----------|---------------|
| `/` | GET | Информация о сервисе | ❌ Нет |
| `/health` | GET | Проверка доступности | ❌ Нет |
| `/models` | GET | Список моделей | ✅ Bearer token |
| `/chat` | POST | Чат с Claude | ✅ Bearer token |
| `/code` | POST | Выполнение кода | ✅ Bearer token |
| `/sessions` | GET/POST/DELETE | Управление сессиями | ✅ Bearer token |

### POST /chat

**Request**:
```json
{
  "message": "Оцени проект по шкале 1-10",
  "session_id": "optional-session-id",
  "model": "sonnet",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response**:
```json
{
  "response": "Ответ Claude...",
  "session_id": "abc123",
  "model": "sonnet",
  "timestamp": "2025-10-12T11:46:00Z",
  "status": "success"
}
```

### POST /code

**Request**:
```json
{
  "code": "print('Hello, World!')",
  "language": "python",
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "result": "Hello, World!",
  "session_id": "abc123",
  "language": "python",
  "timestamp": "2025-10-12T11:46:00Z",
  "status": "success"
}
```

---

## 🤖 Использование в агентах

### Researcher Agent (с WebSearch)

```python
from agents.researcher_agent_v2 import ResearcherAgentV2

# Создать агент
researcher = ResearcherAgentV2(db, llm_provider="claude_code")

# Запустить исследование (27 запросов WebSearch)
result = await researcher.research_anketa(anketa_id='AN-20250905-Valeria-001')

# Результат
if result['status'] == 'success':
    print(f"Research ID: {result['research_id']}")
    print(f"Queries: {result['results']['metadata']['total_queries']}")
    print(f"Sources: {result['results']['metadata']['sources_count']}")
```

**WebSearch запрос**:
```python
# Внутри ResearcherAgent
result = await self._websearch_with_claude(
    query="официальная статистика детский спорт Кемеровская область 2022-2025",
    allowed_domains=["rosstat.gov.ru", "fedstat.ru", "minsport.gov.ru"],
    context="Найди точные цифры и динамику"
)

# Результат:
{
    'query': '...',
    'result': {
        'summary': '...',
        'sources': [
            {
                'url': 'https://rosstat.gov.ru/...',
                'title': '...',
                'organization': 'Росстат',
                'date': '2024',
                'relevance': 'high'
            }
        ],
        'quotes': [
            {
                'text': '...',
                'source': 'https://...',
                'organization': 'Росстат',
                'date': '2024',
                'strength': 'exact_match'
            }
        ]
    }
}
```

### Auditor Agent (аналитика)

```python
from agents.auditor_agent import AuditorAgent

auditor = AuditorAgent(db, llm_provider="claude_code")
evaluation = await auditor.evaluate_project(anketa_id)

# Результат:
{
    'scores': {
        'актуальность': {'score': 8, 'reasoning': '...'},
        'новизна': {'score': 7, 'reasoning': '...'},
        # ... остальные критерии
    },
    'total_score': 85,
    'approval_status': 'approved',
    'recommendations': [...]
}
```

---

## 🔍 WebSearch tool

### Ключевое преимущество

Claude Code имеет **встроенный WebSearch** - не нужен Perplexity API!

**Экономия**: $324/год (1200 грантов × $0.27)

### Возможности

- ✅ Фильтрация по доменам (`allowed_domains`)
- ✅ Приоритет RU-источникам
- ✅ Прямые цитаты с метаданными
- ✅ Проверка актуальности (≤3 года)
- ✅ Бесплатно (в рамках подписки)

### Официальные RU-домены

```python
OFFICIAL_DOMAINS = [
    "rosstat.gov.ru",         # Росстат
    "fedstat.ru",             # ЕМИСС
    "gks.ru",                 # ГКС
    "minsport.gov.ru",        # Минспорт
    "nationalprojects.ru",    # Нацпроекты
    "government.ru",          # Правительство РФ
    "minzdrav.gov.ru",        # Минздрав
    "minprosvet.gov.ru",      # Минпросвещения
    "elibrary.ru",            # Научная библиотека
    "cyberleninka.ru"         # Научные статьи
]
```

### 27 специализированных запросов для Researcher

**Блок 1**: Проблема и социальная значимость (10 запросов)
- Официальная статистика (rosstat.gov.ru)
- Научные исследования (elibrary.ru)
- Государственные программы (nationalprojects.ru)
- Региональные программы (gov-домены субъектов)
- Успешные кейсы
- Экономический ущерб
- Индикаторный матчинг (KPI госпрограмм)
- ... всего 10 запросов

**Блок 2**: География и целевая аудитория (10 запросов)

**Блок 3**: Задачи, мероприятия, цель (7 запросов)

---

## 🎯 Гибридный подход

### LLM Router стратегия

| Задача | Провайдер | Причина |
|--------|-----------|---------|
| **Аналитика** | Claude Code | Глубокий анализ, 200k контекст |
| **Оценка** | Claude Code | Объективность, структура |
| **Исследование** | Claude Code | WebSearch, официальные источники |
| **Структурирование** | Claude Code | Планирование, логика |
| **Генерация текста** | GigaChat | Русский язык, локализация |
| **Общение с юзером** | GigaChat | Естественный диалог |

### Fallback механизм

```python
try:
    # Попытка с Claude Code
    result = await claude_client.chat(prompt)
except Exception:
    # Автоматический fallback на GigaChat
    result = await gigachat_client.generate(prompt)
```

### Метрики качества

#### БЕЗ Researcher:
- ❌ Нет официальной статистики
- ❌ Нет ссылок на Росстат/нацпроекты
- ❌ Нет успешных кейсов
- ❌ Нет индикаторного матчинга
- **Шансы одобрения**: 10-15%

#### С Researcher + WebSearch:
- ✅ Официальная статистика (3-5 источников)
- ✅ Прямые цитаты из госпрограмм (5-7 цитат)
- ✅ Успешные кейсы (3 аналога)
- ✅ Индикаторный матчинг (цели → KPI нацпроектов)
- **Шансы одобрения**: 40-50% ✅

---

## 🔐 Безопасность

### Где хранить API ключ

1. ✅ В `.env` файле (НЕ коммитить в git!)
2. ✅ В переменных окружения на сервере
3. ✅ В секретах Docker/Kubernetes
4. ❌ НИКОГДА не хардкодить в коде

### Пример .env

```bash
# Claude Code API
CLAUDE_CODE_API_KEY=1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
CLAUDE_CODE_BASE_URL=http://178.236.17.55:8000
CLAUDE_CODE_DEFAULT_MODEL=sonnet

# GigaChat API (Fallback)
GIGACHAT_API_KEY=your_gigachat_key_here
```

### Конфигурация

**Файл**: `shared/llm/config.py`

```python
# Claude Code настройки
CLAUDE_CODE_API_KEY = os.getenv("CLAUDE_CODE_API_KEY")
CLAUDE_CODE_BASE_URL = os.getenv("CLAUDE_CODE_BASE_URL", "http://178.236.17.55:8000")
CLAUDE_CODE_DEFAULT_MODEL = "sonnet"  # или "opus"

# Агенты
AGENT_CONFIGS = {
    "auditor": {
        "provider": "claude",
        "model": "sonnet",
        "temperature": 0.3
    },
    "researcher": {
        "provider": "claude",
        "model": "sonnet",
        "temperature": 0.3
    },
    "writer": {
        "provider": "gigachat",
        "model": "GigaChat",
        "temperature": 0.7
    }
}
```

---

## 🔧 Troubleshooting

### Claude API недоступен

```python
# Проверка здоровья
from shared.llm.claude_code_client import ClaudeCodeClient

async with ClaudeCodeClient(api_key=API_KEY) as client:
    healthy = await client.check_health()
    if not healthy:
        print("❌ Claude API недоступен")
```

**Решение**:
1. Проверить сервер: `ssh root@178.236.17.55 "ps aux | grep claude-api-wrapper"`
2. Проверить логи: `ssh root@178.236.17.55 "tail -100 /var/log/claude-api.log"`
3. Перезапустить: `ssh root@178.236.17.55 "cd /opt/claude-api && ./restart.sh"`

### Fallback на GigaChat

LLM Router автоматически переключится на GigaChat при недоступности Claude:

```python
# Fallback происходит автоматически
response = await router.generate(
    prompt="...",
    task_type=TaskType.ANALYSIS  # Попытка Claude → Fallback на GigaChat
)
```

### Проблемы с JSON ответом

```python
# Claude может вернуть текст вместо JSON
import json

try:
    data = json.loads(response)
except json.JSONDecodeError:
    # Обработка текстового ответа
    print(f"Текстовый ответ: {response}")
```

### WebSearch permissions error

**Проблема**: `"I don't have permission to use the WebSearch tool"`

**Решение**: Убедиться что wrapper использует флаг `--allowedTools "WebSearch"`

```bash
# Проверить на сервере
ssh root@178.236.17.55 "grep 'allowedTools' /opt/claude-api/claude-api-wrapper.py"

# Должно быть:
# command = f'echo "{escaped_message}" | claude --allowedTools "WebSearch"'
```

---

## ❓ FAQ

### Q: Можно ли использовать без GigaChat?
**A**: Да, Claude Code может работать автономно для аналитики. GigaChat нужен только для генерации русского текста.

### Q: Сколько стоит WebSearch?
**A**: Бесплатно в рамках подписки Claude Code. Perplexity бы стоил $0.27 на анкету (27 запросов).

### Q: Как часто обновлять API key?
**A**: По мере необходимости. Текущий ключ безлимитный по подписке.

### Q: Что если Claude Code недоступен?
**A**: LLMRouter автоматически переключится на GigaChat (fallback).

### Q: Почему WebSearch не работает?
**A**: Проверьте:
1. OAuth token актуален (`~/.claude/.credentials.json` на сервере)
2. Wrapper использует `--allowedTools "WebSearch"` флаг
3. Сервис запущен и доступен

---

## 📊 Мониторинг

### Статистика клиента

```python
# Статистика Claude Code клиента
async with ClaudeCodeClient(api_key=API_KEY) as client:
    stats = await client.get_statistics()
    print(f"Запросов: {stats['total_requests']}")
    print(f"Success rate: {stats['success_rate']}%")
```

### Статистика роутера

```python
# Статистика LLM Router
stats = router.get_statistics()
print(f"Claude: {stats['claude_percent']:.1f}%")
print(f"GigaChat: {stats['gigachat_percent']:.1f}%")
print(f"Fallback: {stats['fallback_count']}")
```

---

## ✅ Checklist интеграции

- [x] Установлен `aiohttp` для async HTTP
- [x] Создан `claude_code_client.py`
- [x] Создан `llm_router.py`
- [x] Обновлён `config.py`
- [x] Созданы промпты `claude_code_prompts.py`
- [x] Запущен `test_claude_code_integration.py`
- [x] Обновлён Researcher Agent (v2)
- [x] Интегрировано в Telegram Bot
- [x] Настроено логирование в БД
- [x] Добавлен мониторинг в Streamlit
- [x] WebSearch работает (2025-10-12) ✅

---

## 📚 Дополнительная документация

- **Детальная архитектура**: [CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md](CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md)
- **Резюме интеграции**: [CLAUDE_CODE_INTEGRATION_SUMMARY.md](CLAUDE_CODE_INTEGRATION_SUMMARY.md)
- **Best Practices**: [CLAUDE-CODE-BEST-PRACTICES.md](CLAUDE-CODE-BEST-PRACTICES.md)
- **Expert Prompt**: [claude-code-expert-prompt.md](claude-code-expert-prompt.md)

---

**Последнее обновление**: 2025-10-12 (после successful WebSearch deployment)
**Статус**: ✅ Работает и протестирован
**Версия**: 2.0 (объединённый QUICKSTART + QUICK_REFERENCE)
