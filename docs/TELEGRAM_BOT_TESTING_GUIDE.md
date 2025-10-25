# Telegram Bot Testing Guide - База Знаний

## Как тестировать Telegram ботов БЕЗ участия человека

### Подход #1: Unit Tests с Мокированными Updates (БЕЗ реального Telegram)

#### Библиотеки:
- `pytest` - основной фреймворк
- встроенные моки PTB

#### Пример создания фейкового Update:

```python
import pytest
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

async def test_start_command():
    # Создаём фейковый Update
    update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=123, type='private'),
            from_user=User(id=123, first_name='Test', is_bot=False),
            text='/start'
        )
    )

    # Мокируем Context
    context = ContextTypes.DEFAULT_TYPE()

    # Вызываем handler
    await bot.start_command(update, context)

    # Проверяем что бот ответил
    assert update.message.reply_text.called
```

#### Прямой вызов process_update:

```python
from telegram.ext import Application

async def test_message_handler():
    app = Application.builder().token("TEST_TOKEN").build()

    # Создаём фейковый Update
    update = create_fake_update(text="Привет!")

    # Обрабатываем напрямую БЕЗ Telegram
    await app.process_update(update)

    # Проверяем результат
    assert "ответ бота" in результат
```

#### Мокирование Bot.send_message:

```python
from unittest.mock import AsyncMock

async def test_send_message():
    # Мокируем отправку сообщений
    bot.send_message = AsyncMock()

    # Вызываем функцию
    await handle_user_message(update, context)

    # Проверяем что send_message был вызван
    bot.send_message.assert_called_once_with(
        chat_id=123,
        text="Ожидаемый текст"
    )
```

---

### Подход #2: Integration Tests с симуляцией пользователя (С реальным Telegram)

#### Библиотеки:
- `Telethon` - userbot (имитирует реального пользователя)
- `Pyrogram` - альтернатива Telethon
- `tgintegration` - готовая библиотека для тестов
- `pytest-asyncio` - для async тестов

#### Setup для Telethon:

1. Получить `api_id` и `api_hash`:
   - Зайти на https://my.telegram.org/
   - API development tools
   - Создать приложение

2. Установить библиотеки:
```bash
pip install telethon pytest pytest-asyncio
```

#### Пример теста с Telethon:

```python
import pytest
from telethon import TelegramClient
from telethon.sessions import StringSession

@pytest.fixture
async def client():
    """Создаём userbot клиента"""
    client = TelegramClient(
        StringSession(),
        api_id=YOUR_API_ID,
        api_hash=YOUR_API_HASH
    )
    await client.start()
    yield client
    await client.disconnect()

@pytest.mark.asyncio
async def test_bot_start_command(client):
    """Тест команды /start"""

    # Создаём conversation с ботом
    async with client.conversation('@your_bot') as conv:
        # Отправляем команду
        await conv.send_message('/start')

        # Ждём ответа
        response = await conv.get_response()

        # Проверяем ответ
        assert 'Привет' in response.text
```

#### Пример теста диалога с ботом:

```python
@pytest.mark.asyncio
async def test_interview_flow(client):
    """Тест полного интервью"""

    async with client.conversation('@your_bot') as conv:
        # 1. Начинаем интервью
        await conv.send_message('/start_interview')
        response = await conv.get_response()
        assert 'Здравствуйте' in response.text

        # 2. Продолжаем
        await conv.send_message('/continue')
        question = await conv.get_response()
        assert 'проект' in question.text.lower()

        # 3. Отвечаем на вопрос
        await conv.send_message('Литературный проект для Кемерово')

        # 4. Ждём следующий вопрос
        next_question = await conv.get_response(timeout=10)
        assert len(next_question.text) > 0  # Бот должен ответить
```

---

### Подход #3: Использование tgintegration

#### Установка:
```bash
pip install tgintegration
```

#### Пример:

```python
from tgintegration import BotController
import pytest

@pytest.fixture
async def bot_controller():
    """Создаём контроллер бота"""
    controller = BotController(
        peer='@your_bot',
        client=TelegramClient(...),
        max_wait=15  # секунд
    )
    await controller.initialize()
    yield controller
    await controller.clear_chat()

@pytest.mark.asyncio
async def test_with_tgintegration(bot_controller):
    # Отправить команду и получить ответ
    async with bot_controller.collect(count=1) as response:
        await bot_controller.send_command('/start')

    # Проверить ответ
    assert response.num_messages == 1
    assert 'Привет' in response.messages[0].text
```

---

## Сравнение подходов

| Подход | Скорость | Реалистичность | Сложность | Когда использовать |
|--------|----------|----------------|-----------|-------------------|
| Unit Tests (моки) | ⚡⚡⚡ Очень быстро | ⭐ Низкая | 🟢 Простая | Тесты логики handlers |
| Integration (Telethon) | ⚡ Медленно | ⭐⭐⭐ Высокая | 🟡 Средняя | E2E тесты, проверка UI |
| tgintegration | ⚡⚡ Средне | ⭐⭐⭐ Высокая | 🟢 Простая | Готовое решение |

---

## Структура тестов для нашего бота

### Файловая структура:
```
GrantService/
├── telegram-bot/
│   ├── main.py
│   ├── handlers/
│   │   └── interactive_interview_handler.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py              # Fixtures
│       ├── unit/
│       │   ├── test_handlers.py     # Unit тесты handlers
│       │   └── test_interview.py    # Unit тесты интервью
│       └── integration/
│           ├── test_flow_e2e.py     # E2E тесты
│           └── test_interview_e2e.py # E2E интервью
```

---

## Примеры тестов для нашего бота

### Unit Test - Проверка обработки ответа:

```python
# tests/unit/test_interview_handler.py

import pytest
from telegram import Update, Message, User, Chat
from handlers.interactive_interview_handler import InteractiveInterviewHandler

@pytest.fixture
def handler():
    return InteractiveInterviewHandler(db=mock_db)

@pytest.mark.asyncio
async def test_handle_message_puts_answer_in_queue(handler):
    """Тест что ответ кладётся в очередь"""

    # Setup
    user_id = 123
    handler.active_interviews[user_id] = {
        'answer_queue': asyncio.Queue()
    }

    # Create fake update
    update = create_fake_update(
        user_id=user_id,
        text="Литературный проект"
    )
    context = create_fake_context()

    # Execute
    await handler.handle_message(update, context)

    # Assert
    queue = handler.active_interviews[user_id]['answer_queue']
    answer = await queue.get()
    assert answer == "Литературный проект"
```

### Integration Test - Полный флоу:

```python
# tests/integration/test_interview_e2e.py

import pytest
from telethon import TelegramClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_interview_flow(telethon_client):
    """Тест полного интервью от /start до завершения"""

    async with telethon_client.conversation('@grantservice_bot') as conv:
        # 1. Старт
        await conv.send_message('/start_interview')
        greeting = await conv.get_response()
        assert 'Здравствуйте' in greeting.text

        # 2. Continue
        await conv.send_message('/continue')
        q1 = await conv.get_response()
        assert 'проект' in q1.text.lower()

        # 3. Отвечаем на 5 вопросов
        answers = [
            "Литературный проект для жителей Кемерово",
            "Недостаток культурных мероприятий",
            "Жители города, любители литературы",
            "Проведение литературных вечеров",
            "500000 рублей"
        ]

        for answer in answers:
            await conv.send_message(answer)
            response = await conv.get_response(timeout=15)

            # Проверяем что бот либо задал вопрос, либо показал прогресс
            assert len(response.text) > 0

        # 4. Проверяем завершение
        # (бот должен отправить summary с оценкой)
        # TODO: дождаться финального сообщения
```

---

## Mock Helpers (Вспомогательные функции)

```python
# tests/conftest.py

import pytest
from telegram import Update, Message, User, Chat
from datetime import datetime

def create_fake_update(user_id=123, text="/start", username="test_user"):
    """Создать фейковый Update"""
    return Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=user_id, type='private'),
            from_user=User(
                id=user_id,
                first_name='Test',
                username=username,
                is_bot=False
            ),
            text=text
        )
    )

def create_fake_context():
    """Создать фейковый Context"""
    from telegram.ext import ContextTypes
    return ContextTypes.DEFAULT_TYPE()

@pytest.fixture
async def mock_bot():
    """Мокированный Bot"""
    from unittest.mock import AsyncMock

    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot
```

---

## Запуск тестов

### Unit тесты (быстрые):
```bash
pytest tests/unit/ -v
```

### Integration тесты (медленные, требуют настройки):
```bash
pytest tests/integration/ -v --slow
```

### Все тесты:
```bash
pytest tests/ -v
```

### С покрытием:
```bash
pytest tests/ --cov=telegram-bot --cov-report=html
```

---

## CI/CD Integration

### GitHub Actions пример:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Run unit tests
      run: pytest tests/unit/ -v

    - name: Run integration tests
      if: github.event_name == 'push'
      env:
        TELEGRAM_API_ID: ${{ secrets.TELEGRAM_API_ID }}
        TELEGRAM_API_HASH: ${{ secrets.TELEGRAM_API_HASH }}
      run: pytest tests/integration/ -v
```

---

## Best Practices

### 1. Изолируйте тесты
```python
@pytest.fixture(autouse=True)
async def cleanup(handler):
    """Очистка после каждого теста"""
    yield
    handler.active_interviews.clear()
```

### 2. Используйте фикстуры
```python
@pytest.fixture
async def interview_handler(mock_db):
    return InteractiveInterviewHandler(db=mock_db)
```

### 3. Параметризуйте тесты
```python
@pytest.mark.parametrize("command,expected", [
    ("/start", "Привет"),
    ("/help", "Помощь"),
    ("/status", "Статус")
])
async def test_commands(command, expected, handler):
    update = create_fake_update(text=command)
    await handler.handle_message(update, context)
    assert expected in результат
```

### 4. Мокируйте внешние зависимости
```python
@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate_async.return_value = "Сгенерированный вопрос?"
    return llm
```

---

## Полезные ссылки

- [PTB Testing Docs](https://docs.python-telegram-bot.org/en/stable/testing.html)
- [PTB Wiki - Writing Tests](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Writing-Tests)
- [Telethon Docs](https://docs.telethon.dev/)
- [tgintegration](https://github.com/JosXa/tgintegration)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)

---

## Наши конкретные кейсы

### Тест #1: Проверка что handle_message вызывается
```python
async def test_handle_message_is_called():
    """Регрессионный тест для Bug #6"""
    # Этот тест проверяет что fix с asyncio.create_task работает
    pass  # TODO
```

### Тест #2: Проверка что ответы не спамят progress bars
```python
async def test_no_progress_bar_spam():
    """Регрессионный тест для Bug #2"""
    # TODO: проверить что после ответа приходит вопрос, а не progress bar
    pass
```

---

**Generated**: 2025-10-21
**Status**: Active Knowledge Base
**Next**: Implement unit tests for handlers
