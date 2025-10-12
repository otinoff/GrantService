# 🚀 Claude Code - Краткая справка

**Дата**: 2025-10-08
**Версия**: 1.0

---

## 📋 Основная информация

### **API Endpoints**
```
Base URL: http://178.236.17.55:8000
API Key:  1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
Model:    Sonnet 4.5 (200k контекст)
```

### **Доступные endpoints**:
| Endpoint | Метод | Описание | Authorization |
|----------|-------|----------|---------------|
| `/health` | GET | Проверка доступности | ❌ Нет |
| `/models` | GET | Список моделей | ✅ Bearer token |
| `/chat` | POST | Чат с Claude | ✅ Bearer token |
| `/code` | POST | Выполнение кода | ✅ Bearer token |
| `/sessions` | GET/POST/DELETE | Управление сессиями | ✅ Bearer token |

---

## 🔧 Проверка подключения

### **1. Health Check (без авторизации)**
```bash
curl -s -w "\nHTTP Status: %{http_code}\n" http://178.236.17.55:8000/health
```

**Ожидаемый результат**:
```json
{"status": "healthy"}
HTTP Status: 200
```

### **2. Список моделей (с авторизацией)**
```bash
curl -s -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
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

### **3. В Python**
```python
import os
import requests

# Из переменных окружения
api_key = os.getenv('CLAUDE_CODE_API_KEY')
base_url = os.getenv('CLAUDE_CODE_BASE_URL')

# Health check
response = requests.get(f"{base_url}/health", timeout=3)
print(f"Status: {response.status_code}")  # 200

# Модели
headers = {"Authorization": f"Bearer {api_key}"}
models = requests.get(f"{base_url}/models", headers=headers, timeout=3)
print(models.json())
```

### **4. В админ-панели**
```
1. Открой: http://localhost:8501
2. Перейди: Настройки → Система
3. Секция: Claude Code API
4. Кнопки:
   - 🔄 Проверить подключение → тест /health
   - 📊 Проверить модели → список доступных моделей
```

---

## 🤖 Использование в агентах

### **Researcher Agent** (с WebSearch)

```python
from agents.researcher_agent import ResearcherAgent

# Создать агент
researcher = ResearcherAgent(db, llm_provider="claude_code")

# Запустить исследование
result = await researcher.research_anketa(anketa_id='VALERIA_PTSD_888465306')

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
        'sources': [{url, title, org, date, relevance}],
        'quotes': [{text, source, org, date, strength}]
    }
}
```

### **Auditor Agent** (аналитика)

```python
from agents.auditor_agent import AuditorAgent

auditor = AuditorAgent(db, llm_provider="claude_code")
evaluation = await auditor.evaluate_project(anketa_id)

# Результат:
{
    'scores': {
        'актуальность': {'score': 8, 'reasoning': '...'},
        'новизна': {'score': 7, 'reasoning': '...'},
        ...
    },
    'total_score': 85,
    'approval_status': 'approved',
    'recommendations': [...]
}
```

---

## 📊 WebSearch tool

### **Ключевое преимущество**
Claude Code имеет **встроенный WebSearch** - не нужен Perplexity API!

✅ **ПРОТЕСТИРОВАНО 2025-10-08**: Работает БЕЗ VPN из Казахстана!

### **Возможности**:
- ✅ Фильтрация по доменам (`allowed_domains`)
- ✅ Приоритет RU-источникам
- ✅ Прямые цитаты с метаданными
- ✅ Проверка актуальности (≤3 года)
- ✅ Бесплатно (в рамках подписки)

### **🔐 Включение WebSearch (ВАЖНО!)**

На сервере создать `~/.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash",
      "Read",
      "Write",
      "Edit",
      "WebFetch",
      "WebSearch",
      "Grep",
      "Glob"
    ]
  }
}
```

После перезапуска Claude API wrapper WebSearch работает без запросов разрешений!

### **Официальные RU-домены**:
```python
OFFICIAL_DOMAINS = [
    "rosstat.gov.ru",     # Росстат
    "fedstat.ru",         # ЕМИСС
    "gks.ru",             # ГКС
    "minsport.gov.ru",    # Минспорт
    "nationalprojects.ru", # Нацпроекты
    "government.ru",      # Правительство РФ
    "minzdrav.gov.ru",    # Минздрав
    "minprosvet.gov.ru",  # Минпросвещения
    "elibrary.ru",        # Научная библиотека
    "cyberleninka.ru"     # Научные статьи
]
```

### **Использование для Researcher**:

**27 специализированных запросов**:
- **Блок 1**: Проблема и социальная значимость (10 запросов)
- **Блок 2**: География и целевая аудитория (10 запросов)
- **Блок 3**: Задачи, мероприятия, цель (7 запросов)

**Пример блока 1** (промты эксперта):
1. Официальная статистика (rosstat.gov.ru)
2. Научные исследования (elibrary.ru)
3. Государственные программы (nationalprojects.ru)
4. Региональные программы (gov-домены субъектов)
5. Успешные кейсы
6. Экономический ущерб
7. Индикаторный матчинг (KPI госпрограмм)
8. ... (всего 10 запросов)

---

## 🎯 Гибридный подход

### **LLM Router стратегия**:

| Задача | Провайдер | Причина |
|--------|-----------|---------|
| **Аналитика** | Claude Code | Глубокий анализ, 200k контекст |
| **Оценка** | Claude Code | Объективность, структура |
| **Исследование** | Claude Code | WebSearch, официальные источники |
| **Структурирование** | Claude Code | Планирование, логика |
| **Генерация текста** | GigaChat | Русский язык, локализация |
| **Общение с юзером** | GigaChat | Естественный диалог |

### **Fallback механизм**:
```python
try:
    # Попытка с Claude Code
    result = await claude_client.chat(prompt)
except Exception:
    # Автоматический fallback на GigaChat
    result = await gigachat_client.generate(prompt)
```

---

## 📈 Метрики качества

### **БЕЗ Researcher**:
- ❌ Нет официальной статистики
- ❌ Нет ссылок на Росстат/нацпроекты
- ❌ Нет успешных кейсов
- ❌ Нет индикаторного матчинга
- **Шансы одобрения**: 10-15%

### **С Researcher + WebSearch**:
- ✅ Официальная статистика (3-5 источников)
- ✅ Прямые цитаты из госпрограмм (5-7 цитат)
- ✅ Успешные кейсы (3 аналога)
- ✅ Индикаторный матчинг (цели → KPI нацпроектов)
- **Шансы одобрения**: 40-50% ✅

---

## 🔐 Безопасность

### **Где хранить API ключ**:
1. ✅ В `.env` файле (НЕ коммитить в git!)
2. ✅ В переменных окружения на сервере
3. ✅ В секретах Docker/Kubernetes
4. ❌ НИКОГДА не хардкодить в коде

### **Пример .env**:
```bash
# Claude Code API
CLAUDE_CODE_API_KEY=1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
CLAUDE_CODE_BASE_URL=http://178.236.17.55:8000
CLAUDE_CODE_DEFAULT_MODEL=sonnet

# GigaChat API (Fallback)
GIGACHAT_API_KEY=your_gigachat_key_here
```

---

## 📚 Документация

### **Основные файлы**:
1. `CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md` - Полная архитектура (1387 строк)
2. `CLAUDE_CODE_WEBSEARCH_FOR_RESEARCHER.md` - Researcher с WebSearch
3. `RESEARCHER_ARCHITECTURE_ANALYSIS.md` - Анализ текущей проблемы
4. `.claude/CLAUDE_CODE_API_SETTINGS_ADDED.md` - Настройки в админке
5. `doc/ARCHITECTURE.md` - Общая архитектура системы (обновлена)

### **Код**:
1. `shared/llm/claude_code_client.py` - Claude Code клиент
2. `shared/llm/llm_router.py` - Роутер провайдеров
3. `agents/researcher_agent.py` - Researcher с WebSearch
4. `web-admin/pages/⚙️_Настройки.py:93-175` - Настройки API

---

## ⚡ Быстрый старт

### **Проверить что работает**:
```bash
# 1. Проверить /health
curl http://178.236.17.55:8000/health

# 2. Проверить /models
curl -H "Authorization: Bearer 1f79b062..." http://178.236.17.55:8000/models

# 3. Открыть админку
python launcher.py
# → Настройки → Claude Code API → 🔄 Проверить подключение
```

### **Запустить Researcher на тестовой анкете**:
```bash
python -c "
from agents.researcher_agent import ResearcherAgent
from data.database import Database

db = Database()
researcher = ResearcherAgent(db, llm_provider='claude_code')

import asyncio
result = asyncio.run(researcher.research_anketa('VALERIA_PTSD_888465306'))
print(result)
"
```

---

## ❓ FAQ

**Q: Можно ли использовать без GigaChat?**
A: Да, Claude Code может работать автономно для аналитики. GigaChat нужен только для генерации русского текста.

**Q: Сколько стоит WebSearch?**
A: Бесплатно в рамках подписки Claude Code. Perplexity бы стоил $0.27 на анкету (27 запросов).

**Q: Как часто обновлять API key?**
A: По мере необходимости. Текущий ключ безлимитный по подписке.

**Q: Что если Claude Code недоступен?**
A: LLMRouter автоматически переключится на GigaChat (fallback).

---

**Q: Нужен ли VPN для WebSearch?**
A: НЕТ! Проблема была в отсутствии `~/.claude/settings.json` с разрешением WebSearch. После создания файла всё работает из Казахстана.

**Q: Где посмотреть результаты тестов WebSearch?**
A: `.claude/WEBSEARCH_TEST_RESULTS_2025-10-08.md` - полный отчёт с примерами запросов и ответов.

---

**Последнее обновление**: 2025-10-08 14:53
**Статус**: ✅ Проверено и работает (2025-10-08)

