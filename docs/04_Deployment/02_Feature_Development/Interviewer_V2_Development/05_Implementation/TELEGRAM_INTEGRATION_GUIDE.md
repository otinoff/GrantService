# Telegram Integration Guide - Reference Points Framework

**Date:** 2025-10-20
**Version:** 1.0
**Status:** ✅ **READY FOR INTEGRATION**

---

## 📋 Overview

Reference Points Framework теперь готов к интеграции с Telegram Bot!

Создана специальная **асинхронная версия** для Telegram, которая работает по событийной модели (event-driven):
- Пользователь нажимает кнопку → получает вопрос
- Пользователь отвечает → система обрабатывает → следующий вопрос
- Прогресс → финальный аудит → результаты

---

## 🚀 Что создано

### 1. TelegramInteractiveInterview
**File:** `telegram-bot/telegram_interactive_interview.py`

Адаптированная версия для Telegram с методами:

```python
from telegram_interactive_interview import TelegramInteractiveInterview

# Создать интервью
interview = TelegramInteractiveInterview(db, user_data)

# Step-by-step process
question = await interview.get_next_question()  # Получить вопрос
await interview.process_answer(answer)          # Обработать ответ
progress = interview.get_progress()             # Прогресс
is_done = interview.is_complete()               # Завершено?
results = await interview.get_results()         # Результаты
```

### 2. InteractiveInterviewHandler
**File:** `telegram-bot/handlers/interactive_interview_handler.py`

Handler для Telegram Bot с командами:
- `/start_interview` - Начать интервью
- `/continue` - Продолжить/следующий вопрос
- `/stop_interview` - Остановить
- `/progress` - Показать прогресс

---

## 🔧 Интеграция с Telegram Bot

### Шаг 1: Добавить handler в main.py

Добавьте в начало `telegram-bot/main.py`:

```python
# После импортов
from handlers.interactive_interview_handler import InteractiveInterviewHandler

class GrantServiceBot:
    def __init__(self):
        # ... существующий код ...

        # НОВОЕ: Interactive Interview Handler
        self.interview_handler = InteractiveInterviewHandler(
            db=self.db,
            admin_chat_id=self.admin_chat_id
        )
```

### Шаг 2: Добавить команды

В метод `setup_handlers()` добавьте:

```python
def setup_handlers(self, application: Application):
    # ... существующие handlers ...

    # НОВОЕ: Interactive Interview V2
    application.add_handler(CommandHandler(
        "start_interview_v2",
        self.handle_start_interview_v2
    ))

    application.add_handler(CommandHandler(
        "continue",
        self.handle_continue_interview
    ))

    application.add_handler(CommandHandler(
        "stop_interview",
        self.handle_stop_interview
    ))

    application.add_handler(CommandHandler(
        "progress",
        self.handle_show_progress
    ))

    # Обработчик текстовых сообщений (для ответов)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        self.handle_interview_message
    ))
```

### Шаг 3: Реализовать методы

Добавьте в класс `GrantServiceBot`:

```python
async def handle_start_interview_v2(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Начать интервью V2 с Reference Points"""
    user_id = update.effective_user.id

    # Подготовить user_data
    user_data = {
        'telegram_id': user_id,
        'username': update.effective_user.username,
        'first_name': update.effective_user.first_name,
        'grant_fund': 'fpg'  # Или из контекста
    }

    # Запустить интервью
    await self.interview_handler.start_interview(
        update,
        context,
        user_data
    )

async def handle_continue_interview(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Продолжить интервью - получить следующий вопрос"""
    await self.interview_handler.continue_interview(update, context)

async def handle_stop_interview(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Остановить интервью"""
    await self.interview_handler.stop_interview(update, context)

async def handle_show_progress(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Показать прогресс интервью"""
    await self.interview_handler.show_progress(update, context)

async def handle_interview_message(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Обработать текстовое сообщение (возможно ответ на вопрос)"""
    user_id = update.effective_user.id

    # Проверить есть ли активное интервью
    if self.interview_handler.is_interview_active(user_id):
        await self.interview_handler.handle_message(update, context)
    else:
        # Обычная обработка сообщения (существующая логика)
        await self.handle_text_message(update, context)
```

### Шаг 4: Обновить главное меню

Добавьте кнопку для V2 интервью:

```python
keyboard = [
    [InlineKeyboardButton("🆕 Интервью V2 (Adaptive)", callback_data="start_interview_v2")],
    [InlineKeyboardButton("📝 Интервью V1 (Classic)", callback_data="start_interview")],
    # ... остальные кнопки ...
]
```

### Шаг 5: Обработать callback

```python
elif callback_data == "start_interview_v2":
    # Начать V2 интервью
    await query.message.reply_text(
        "Запускаю адаптивное интервью...\n"
        "Используйте /continue для начала."
    )

    # Или сразу запустить
    await self.handle_start_interview_v2(update, context)
```

---

## 📝 Пример использования

### Для пользователя:

```
Пользователь: /start_interview_v2

Бот: Здравствуйте! 👋
     Я помогу вам оформить заявку на грант...
     Готовы начать? Нажмите /continue

Пользователь: /continue

Бот: Расскажите, пожалуйста, что конкретно делает ваш проект?

Пользователь: Наш проект создает инклюзивные пространства для детей...

Бот: Спасибо! Обрабатываю ваш ответ...
     [Следующий вопрос...]

Пользователь: /progress

Бот: [████████████░░░░░░░░] 10/13 разделов (76.9%)

     ✓ Критичная информация
     ✓ Важная информация

     Осталось уточняющих вопросов: 3

...

Бот: [EXCELLENT] Интервью завершено!

     Оценка: 85/100
     Статус: Отлично!

     Задано вопросов: 12
     Уточняющих вопросов: 3
     Время: 450.2 секунд
```

---

## 🗂 Структура файлов

```
GrantService/
├── telegram-bot/
│   ├── telegram_interactive_interview.py  # ✅ НОВЫЙ - Async wrapper для Telegram
│   ├── handlers/
│   │   └── interactive_interview_handler.py  # ✅ НОВЫЙ - Telegram handler
│   └── main.py  # TODO: Добавить интеграцию
│
├── agents/
│   ├── reference_points/  # ✅ Core framework
│   │   ├── __init__.py
│   │   ├── reference_point.py
│   │   ├── reference_point_manager.py
│   │   ├── adaptive_question_generator.py
│   │   └── conversation_flow_manager.py
│   │
│   ├── interactive_interviewer_agent_v2.py  # ✅ Full agent (для standalone)
│   └── auditor_agent.py  # Используется для финального аудита
│
└── shared/
    └── llm/  # UnifiedLLMClient для генерации вопросов
```

---

## ⚙️ Конфигурация

### Environment Variables

Убедитесь что в `config/.env` есть:

```bash
# Claude Code (для генерации вопросов)
CLAUDE_CODE_API_KEY=your_key
CLAUDE_CODE_MODEL=sonnet

# Qdrant (для контекста ФПГ)
QDRANT_HOST=5.35.88.251
QDRANT_PORT=6333
QDRANT_COLLECTION=knowledge_sections

# Telegram
TELEGRAM_BOT_TOKEN=your_token
ADMIN_CHAT_ID=your_admin_chat
```

### Database

Интервью сохраняет данные в ту же структуру БД что и V1:
- `sessions` - сессии пользователей
- `interview_data` (JSON) - ответы на вопросы
- `audit_score` - оценка аудита

---

## 🧪 Тестирование

### Локальное тестирование

```bash
cd telegram-bot
python telegram_interactive_interview.py
```

Должно показать симуляцию интервью с mock ответами.

### Тестирование с реальным ботом

1. Запустите бота локально:
```bash
cd telegram-bot
python main.py
```

2. В Telegram:
```
/start_interview_v2
/continue
[Ответить на вопрос]
/progress
[Продолжить отвечать]
```

---

## 🚀 Deployment на Production

### Шаг 1: Push к GitHub

```bash
cd C:\SnowWhiteAI\GrantService

# Add новые файлы
git add agents/reference_points/
git add agents/interactive_interviewer_agent_v2.py
git add telegram-bot/telegram_interactive_interview.py
git add telegram-bot/handlers/interactive_interview_handler.py
git add test_interactive_interviewer_v2.py

# Commit
git commit -m "feat: Add Reference Points Framework for adaptive interviews

- Implemented 4 core modules (ReferencePoint, Manager, QuestionGenerator, FlowManager)
- Created InteractiveInterviewerAgentV2 with Qdrant integration
- Added Telegram async wrapper for event-driven bot integration
- 13 FPG reference points with P0-P3 priorities
- Max 5 follow-up questions with smart prioritization
- Comprehensive tests and documentation

Ready for production deployment."

# Push
git push origin master
```

### Шаг 2: Deploy на сервер

```bash
# SSH на production
ssh root@5.35.88.251

# Navigate to project
cd /var/GrantService

# Pull latest
git pull origin master

# Restart bot
systemctl restart grantservice-bot

# Check status
systemctl status grantservice-bot

# Check logs
tail -f /var/log/grantservice-bot.log
```

### Шаг 3: Verify Qdrant

```bash
# На сервере проверить Qdrant
curl http://localhost:6333/collections/knowledge_sections

# Должно вернуть info о коллекции с 31 точками
```

### Шаг 4: Test на production

В Telegram боте на production:
```
/start_interview_v2
```

---

## 🐛 Troubleshooting

### Проблема: "No module named 'llm'"

**Решение:** Проверьте пути в sys.path:

```python
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
```

### Проблема: "Qdrant unavailable"

**Решение:** Проверьте подключение:

```bash
# На сервере
curl http://5.35.88.251:6333
```

Если не работает - перезапустите Qdrant:

```bash
systemctl restart qdrant
```

### Проблема: Интервью завершается сразу

**Решение:** Проверьте что состояние инициализируется как EXPLORING:

```python
self.flow_manager.context.current_state = ConversationState.EXPLORING
```

### Проблема: Бесконечная рекурсия

**Решение:** Убедитесь что используется цикл, а не рекурсия:

```python
while iteration < max_iterations:
    # ...
```

---

## 📊 Сравнение V1 vs V2

| Feature | V1 (Classic) | V2 (Reference Points) |
|---------|--------------|------------------------|
| **Вопросы** | 15 фиксированных | 13 RPs + до 5 уточнений |
| **Адаптация** | Нет | Да (контекст, уровень) |
| **Qdrant** | Нет | Да (база ФПГ) |
| **Skip Logic** | Нет | Да (умный пропуск) |
| **Время** | 30-40 мин | 20-30 мин |
| **Quality** | Средняя | Высокая |

---

## ✅ Checklist для интеграции

- [ ] Добавить `InteractiveInterviewHandler` в main.py
- [ ] Добавить команды `/start_interview_v2`, `/continue`, `/stop_interview`, `/progress`
- [ ] Реализовать методы обработки
- [ ] Добавить кнопку V2 в главное меню
- [ ] Протестировать локально
- [ ] Push на GitHub
- [ ] Deploy на production
- [ ] Протестировать на production
- [ ] Мониторинг логов
- [ ] Собрать feedback от пользователей

---

## 📖 Дополнительные материалы

- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Полное описание реализации
- [CONCEPTUAL_KNOWLEDGE.md](../00_Project_Info/CONCEPTUAL_KNOWLEDGE.md) - Концептуальные основы
- [NEW_ARCHITECTURE_REFERENCE_POINTS.md](../00_Project_Info/NEW_ARCHITECTURE_REFERENCE_POINTS.md) - Архитектура

---

**Создано:** 2025-10-20
**Готово к интеграции!** 🚀
