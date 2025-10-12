# Claude Code CLI - Центральная Документация

**Дата создания**: 2025-10-08
**Статус**: ✅ Работает (после исправления credentials)
**Сервер**: http://178.236.17.55:8000

---

## 📋 Содержание

1. [Общий Обзор](#общий-обзор)
2. [Архитектура](#архитектура)
3. [Структура Папки](#структура-папки)
4. [Быстрый Старт](#быстрый-старт)
5. [Документация](#документация)
6. [История Проблем](#история-проблем)

---

## 🎯 Общий Обзор

Это централизованная документация по интеграции Claude Code CLI в проект GrantService.

### Что такое Claude Code CLI?

**Claude Code** - это терминальный AI-помощник для программирования от Anthropic. В нашем проекте он используется через HTTP API wrapper для:

- 🔍 **Researcher Agent** - веб-поиск и анализ грантовых программ
- 📝 **Writer Agent** - улучшение качества заявок на гранты
- 🔎 **Auditor Agent** - оценка и проверка заявок
- 🤖 **AI Агенты** - интеллектуальная обработка данных

### Ключевые Компоненты

```
GrantService (Python)
    ↓
HTTP API (178.236.17.55:8000)
    ↓
Claude Code CLI (subprocess)
    ↓
Anthropic API (api.anthropic.com)
```

### Текущий Статус

- ✅ Сервер работает (после 2025-10-08)
- ✅ OAuth credentials обновлены
- ✅ Все endpoint'ы работают:
  - `/health` - Health check
  - `/models` - Список моделей
  - `/chat` - Основной endpoint для общения
  - `/code` - Генерация кода
- ✅ Python клиент протестирован и работает
- ✅ Subscription: **Max** (20x rate limits)

---

## 🏗️ Архитектура

### Схема Взаимодействия

```
┌─────────────────────┐
│  GrantService       │
│  (Python Client)    │
└──────────┬──────────┘
           │ HTTP Request
           ↓
┌─────────────────────┐
│  FastAPI Wrapper    │
│  (178.236.17.55)    │
└──────────┬──────────┘
           │ subprocess.run()
           ↓
┌─────────────────────┐
│  Claude Code CLI    │
│  (local install)    │
└──────────┬──────────┘
           │ OAuth Token
           ↓
┌─────────────────────┐
│  Anthropic API      │
│  (api.anthropic.com)│
└─────────────────────┘
```

### Ключевые Технические Детали

**Сервер:**
- IP: `178.236.17.55`
- Port: `8000`
- Процесс: Python 3 (PID: 60291)
- Пользователь: `root`
- Claude Code версия: `2.0.5`

**Авторизация:**
- API Key (для HTTP wrapper): `1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732`
- OAuth Access Token (для Claude CLI): `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`
- Expires: 1759950304394 (октябрь 2025)

**Модели:**
- `sonnet` - Claude Sonnet 4.5 (быстрая)
- `opus` - Claude Opus 4 (мощная)

---

## 📁 Структура Папки

```
Claude Code CLI/
├── README.md                       # ← Вы здесь
│
├── 01-Documentation/               # Основная документация
│   ├── CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md  # Детальная архитектура
│   ├── CLAUDE_CODE_INTEGRATION_SUMMARY.md       # Сводка интеграции
│   ├── CLAUDE_CODE_QUICK_START.md               # Быстрый старт (объединённый)
│   ├── CLAUDE-CODE-BEST-PRACTICES.md            # Лучшие практики
│   └── claude-code-expert-prompt.md             # Промпт для экспертов
│
├── 02-Server/                      # Серверная часть
│   ├── claude-api-wrapper.py       # FastAPI wrapper (текущий)
│   ├── flask-claude-wrapper.py     # Flask альтернатива
│   └── Deploy-ClaudeAPI.ps1        # Deployment script
│
├── 03-Client/                      # Клиентская часть
│   ├── claude_code_client.py       # Python клиент (используется в GrantService)
│   └── claude-client-example.py    # Пример использования
│
├── 04-Tests/                       # Тестовые скрипты
│   ├── test_claude_api.py          # Основной тест API
│   ├── test_claude_api_settings.py # Тест настроек
│   └── test_claude_code_integration.py # Интеграционный тест
│
├── 05-Diagnostics/                 # Диагностика и исправления
│   ├── CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md
│   ├── CLAUDE_CODE_API_FIX_INSTRUCTIONS.md
│   ├── CLAUDE_CODE_SERVER_CHECK.md
│   ├── CLAUDE_CODE_SERVER_SETUP_GUIDE.md
│   ├── ANTHROPIC_API_KEY_FOUND.md
│   ├── CLAUDE_CODE_API_SETTINGS_ADDED.md
│   └── CLAUDE_CODE_WEBSEARCH_FOR_RESEARCHER.md
│
├── 06-Examples/                    # Примеры использования
│   ├── claude_code_prompts.py      # Промпты для агентов
│   └── auditor_agent_claude.py     # Пример Auditor Agent
│
└── 07-Config/                      # Конфигурационные файлы
    └── claude-oauth.json           # Пример OAuth конфигурации
```

---

## 🚀 Быстрый Старт

### 1. Проверка Работоспособности

```bash
# Health check
curl http://178.236.17.55:8000/health

# Список моделей
curl -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  http://178.236.17.55:8000/models

# Тест чата
curl -X POST http://178.236.17.55:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","model":"sonnet"}'
```

### 2. Использование Python Клиента

```python
from shared.llm.claude_code_client import ClaudeCodeClient

# Создать клиент
client = ClaudeCodeClient(
    api_url="http://178.236.17.55:8000",
    api_key="1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732"
)

# Отправить сообщение
response = client.chat("Привет, помоги мне написать грантовую заявку")
print(response)
```

### 3. Запуск Тестов

```bash
# Из корня проекта
cd C:\SnowWhiteAI\GrantService

# Основной тест
python test_claude_api.py

# Должен вывести: TEST PASSED: Claude API works!
```

---

## 📚 Документация

### Основные Документы

#### 🎯 Начало Работы
- **[CLAUDE_CODE_QUICK_START.md](01-Documentation/CLAUDE_CODE_QUICK_START.md)** - Быстрый старт и справка (объединённый документ)

#### 🏗️ Архитектура
- **[CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md](01-Documentation/CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md)** - Детальная архитектура
- **[CLAUDE_CODE_INTEGRATION_SUMMARY.md](01-Documentation/CLAUDE_CODE_INTEGRATION_SUMMARY.md)** - Сводка интеграции

#### 📖 Best Practices
- **[CLAUDE-CODE-BEST-PRACTICES.md](01-Documentation/CLAUDE-CODE-BEST-PRACTICES.md)** - Лучшие практики использования
- **[claude-code-expert-prompt.md](01-Documentation/claude-code-expert-prompt.md)** - Промпт для экспертов

### Серверная Часть

#### 🖥️ API Wrapper
- **[claude-api-wrapper.py](02-Server/claude-api-wrapper.py)** - FastAPI wrapper (текущий)
  - Endpoints: `/health`, `/models`, `/chat`, `/code`
  - Использует subprocess для вызова Claude CLI
  - Поддерживает авторизацию через Bearer token

#### 🚀 Deployment
- **[Deploy-ClaudeAPI.ps1](02-Server/Deploy-ClaudeAPI.ps1)** - PowerShell скрипт для деплоя
- **[flask-claude-wrapper.py](02-Server/flask-claude-wrapper.py)** - Flask альтернатива (не используется)

### Клиентская Часть

#### 📡 Python Клиент
- **[claude_code_client.py](03-Client/claude_code_client.py)** - Основной клиент
  - Класс: `ClaudeCodeClient`
  - Методы: `chat()`, `code()`, `get_models()`, `health_check()`
  - Используется в Researcher, Writer, Auditor агентах

#### 📝 Примеры
- **[claude-client-example.py](03-Client/claude-client-example.py)** - Примеры использования

### Тестирование

#### 🧪 Тесты
- **[test_claude_api.py](04-Tests/test_claude_api.py)** - Основной тест API
  - Проверяет подключение
  - Тестирует /chat endpoint
  - Выводит результат в консоль

- **[test_claude_code_integration.py](04-Tests/test_claude_code_integration.py)** - Интеграционный тест
- **[test_claude_api_settings.py](04-Tests/test_claude_api_settings.py)** - Тест настроек

### Диагностика

#### 🔧 Troubleshooting
- **[CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md](05-Diagnostics/CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md)** - Детальный диагностический отчет (2025-10-08)
- **[CLAUDE_CODE_API_FIX_INSTRUCTIONS.md](05-Diagnostics/CLAUDE_CODE_API_FIX_INSTRUCTIONS.md)** - Инструкции по исправлению проблем
- **[CLAUDE_CODE_SERVER_CHECK.md](05-Diagnostics/CLAUDE_CODE_SERVER_CHECK.md)** - Чеклист проверки сервера
- **[CLAUDE_CODE_SERVER_SETUP_GUIDE.md](05-Diagnostics/CLAUDE_CODE_SERVER_SETUP_GUIDE.md)** - Полное руководство по настройке

#### 🔑 Credentials
- **[ANTHROPIC_API_KEY_FOUND.md](05-Diagnostics/ANTHROPIC_API_KEY_FOUND.md)** - Найденные OAuth credentials

### Примеры

#### 💡 Использование в Агентах
- **[claude_code_prompts.py](06-Examples/claude_code_prompts.py)** - Промпты для агентов
- **[auditor_agent_claude.py](06-Examples/auditor_agent_claude.py)** - Пример Auditor Agent

---

## 🔧 История Проблем и Решений

### Проблема #1: 500 Error на /chat endpoint (2025-10-08)

**Симптомы:**
- `/health` и `/models` работали
- `/chat` возвращал `500 Internal Server Error`
- Сообщение: `{"detail":"500: Claude Code ошибка: "}`

**Причина:**
- На сервере были **устаревшие** OAuth credentials
- Claude CLI не мог аутентифицироваться с Anthropic API

**Решение:**
1. Нашли актуальные credentials в `C:\Users\Андрей\.claude\.credentials.json`
2. Обновили credentials на сервере: `/root/.claude/.credentials.json`
3. Перезапустили API wrapper процесс

**Результат:** ✅ Все endpoint'ы работают

**Документы:**
- [CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md](05-Diagnostics/CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md)
- [CLAUDE_CODE_SERVER_CHECK.md](05-Diagnostics/CLAUDE_CODE_SERVER_CHECK.md)
- [ANTHROPIC_API_KEY_FOUND.md](05-Diagnostics/ANTHROPIC_API_KEY_FOUND.md)

### Lesson Learned

**OAuth токены имеют срок действия!**
- Текущий токен expires: октябрь 2025
- При приближении даты истечения нужно обновить credentials
- Процедура обновления описана в [CLAUDE_CODE_SERVER_CHECK.md](05-Diagnostics/CLAUDE_CODE_SERVER_CHECK.md)

---

## 📞 Поддержка

### Если что-то не работает:

1. **Проверьте Health Check:**
   ```bash
   curl http://178.236.17.55:8000/health
   ```

2. **Запустите тест:**
   ```bash
   python test_claude_api.py
   ```

3. **Проверьте документацию:**
   - [CLAUDE_CODE_SERVER_CHECK.md](05-Diagnostics/CLAUDE_CODE_SERVER_CHECK.md) - Чеклист проверки
   - [CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md](05-Diagnostics/CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md) - Детальная диагностика

4. **Проверьте логи на сервере:**
   ```bash
   ssh root@178.236.17.55
   tail -f /var/log/claude-api.log
   ```

---

## 🎯 Критерии Успеха

После настройки все должно работать:

- ✅ `/health` → `200 OK` (status: healthy)
- ✅ `/models` → `200 OK` (список моделей)
- ✅ `/chat` → `200 OK` (ответ от Claude)
- ✅ `test_claude_api.py` → `TEST PASSED`
- ✅ Researcher Agent может выполнять WebSearch
- ✅ AI агенты могут генерировать контент

---

## 📊 Метрики

**Subscription Type:** Max (20x rate limits)
- Превышает Pro в 20 раз
- Достаточно для production использования
- Оптимальное соотношение цена/производительность

**Модели:**
- **Sonnet 4.5** - для быстрых задач (researcher, writer)
- **Opus 4** - для сложных задач (auditor, анализ)

---

## 🚀 Roadmap

### Ближайшие Задачи:
- [ ] Настроить мониторинг expires_at токена
- [ ] Добавить автоматическое обновление OAuth токена
- [ ] Реализовать retry логику в клиенте
- [ ] Добавить rate limiting на стороне клиента

### Долгосрочные Планы:
- [ ] Миграция на systemd service (сейчас простой процесс)
- [ ] Настроить логирование и мониторинг
- [ ] Добавить метрики использования (Prometheus/Grafana)
- [ ] Реализовать caching слой для частых запросов

---

**Последнее обновление:** 2025-10-08
**Статус:** ✅ Полностью функционально
**Maintainer:** AI Integration Specialist

---

## 🔗 Полезные Ссылки

- [Anthropic Console](https://console.anthropic.com)
- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [API Reference](https://docs.anthropic.com/en/api)
- [GrantService Repository](C:\SnowWhiteAI\GrantService)

---

**Это живой документ. Обновляйте его при изменении конфигурации или архитектуры!** 📝
