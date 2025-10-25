# Telegram Bot Testing Guide

Comprehensive guide for testing Telegram bots with python-telegram-bot.

## Version Migration: v13 → v20+

### Key Differences

| Aspect | v13 (Old) | v20+ (New) |
|--------|-----------|-----------|
| **Execution** | Synchronous | Asynchronous |
| **Handlers** | `def handler(update, context)` | `async def handler(update, context)` |
| **Bot calls** | `bot.send_message()` | `await bot.send_message()` |
| **Updater** | `Updater` class | `Application` class |
| **ParseMode** | `from telegram import ParseMode` | `from telegram.constants import ParseMode` |

### Migration Example

**v13 (Old):**
```python
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("Hello!", parse_mode=ParseMode.MARKDOWN)

updater = Updater("TOKEN")
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.start_polling()
```

**v20+ (New):**
```python
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler

async def start(update, context):
    await update.message.reply_text("Hello!", parse_mode=ParseMode.MARKDOWN)

application = Application.builder().token("TOKEN").build()
application.add_handler(CommandHandler("start", start))
await application.run_polling()
```

## Mocking Telegram API

### Basic Mock Setup

```python
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

@pytest.fixture
def mock_update():
    """Create mock Telegram Update object"""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.message.text = "/start"
    update.message.reply_text = AsyncMock()
    return update

@pytest.fixture
def mock_context():
    """Create mock CallbackContext"""
    context = MagicMock()
    context.bot = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    return context
```

### Testing Command Handlers

```python
@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    """Test /start command"""
    from handlers import start_handler

    await start_handler(mock_update, mock_context)

    # Verify reply was sent
    mock_update.message.reply_text.assert_called_once()

    # Verify message content
    call_args = mock_update.message.reply_text.call_args
    assert "Welcome" in call_args[0][0]
```

### Testing Bot Methods

```python
@pytest.mark.asyncio
async def test_send_notification():
    """Test sending notification via bot"""
    with patch('telegram.Bot.send_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message_id": 123}

        bot = Bot("fake_token")
        result = await bot.send_message(
            chat_id=12345,
            text="Test notification"
        )

        assert result["message_id"] == 123
        mock_send.assert_called_once_with(
            chat_id=12345,
            text="Test notification"
        )
```

## Conversation Flow Testing

### ConversationHandler States

```python
from telegram.ext import ConversationHandler

# Define states
NAME, AGE, EMAIL = range(3)

@pytest.mark.asyncio
async def test_conversation_flow(mock_update, mock_context):
    """Test multi-step conversation"""
    from handlers import ask_name, ask_age, ask_email, done

    # Step 1: Ask name
    mock_update.message.text = "/register"
    state = await ask_name(mock_update, mock_context)
    assert state == NAME

    # Step 2: Provide name, ask age
    mock_update.message.text = "John Doe"
    state = await ask_age(mock_update, mock_context)
    assert state == AGE
    assert mock_context.user_data["name"] == "John Doe"

    # Step 3: Provide age, ask email
    mock_update.message.text = "30"
    state = await ask_email(mock_update, mock_context)
    assert state == EMAIL

    # Step 4: Complete
    mock_update.message.text = "john@example.com"
    state = await done(mock_update, mock_context)
    assert state == ConversationHandler.END
```

## Inline Keyboards Testing

```python
@pytest.mark.asyncio
async def test_inline_keyboard_callback(mock_update, mock_context):
    """Test inline keyboard button callback"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    # Mock callback query
    callback_query = MagicMock()
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    callback_query.data = "option_1"

    mock_update.callback_query = callback_query

    from handlers import button_callback

    await button_callback(mock_update, mock_context)

    # Verify callback answered
    callback_query.answer.assert_called_once()

    # Verify message edited
    callback_query.edit_message_text.assert_called_once()
```

## Testing Database Integration

```python
@pytest.fixture
def test_db():
    """In-memory test database"""
    from data.database.models import Database
    db = Database(":memory:")
    db.init_tables()
    yield db
    db.close()

@pytest.mark.asyncio
async def test_save_user_from_telegram(test_db, mock_update):
    """Test saving Telegram user to database"""
    from handlers import register_user

    await register_user(mock_update, test_db)

    # Verify user saved
    user = test_db.get_user(12345)
    assert user is not None
    assert user["username"] == "testuser"
```

## Admin Notifications

```python
@pytest.mark.asyncio
async def test_admin_notification_on_new_application():
    """Test admin notification when new application submitted"""
    with patch('telegram.Bot.send_message', new_callable=AsyncMock) as mock_send:
        from admin_notifications import AdminNotifier

        notifier = AdminNotifier(
            token="fake_token",
            admin_chat_ids=[111, 222, 333]
        )

        application_data = {
            "title": "Test Project",
            "amount": 1000000,
            "user_id": 12345
        }

        await notifier.notify_new_application(application_data)

        # Verify all admins notified
        assert mock_send.call_count == 3

        # Verify message content
        call_text = mock_send.call_args_list[0][1]['text']
        assert "Test Project" in call_text
        assert "1000000" in call_text
```

## Error Handling

```python
@pytest.mark.asyncio
async def test_handler_error_handling(mock_update, mock_context):
    """Test error handling in handlers"""
    from handlers import error_handler

    # Simulate error
    mock_context.error = Exception("Test error")

    await error_handler(mock_update, mock_context)

    # Verify error logged
    mock_update.message.reply_text.assert_called_once_with(
        "Sorry, an error occurred. Please try again."
    )
```

## Best Practices

1. **Always use AsyncMock for v20+**
   ```python
   mock.send_message = AsyncMock()  # ✓ Correct
   mock.send_message = MagicMock()  # ✗ Won't work with await
   ```

2. **Test user input validation**
   ```python
   def test_invalid_email(mock_update):
       mock_update.message.text = "not-an-email"
       # Test handler rejects invalid input
   ```

3. **Mock external dependencies**
   ```python
   # Don't make real API calls in tests
   with patch('telegram.Bot.send_message'):
       # Test code here
   ```

4. **Test state transitions**
   ```python
   # Verify ConversationHandler states change correctly
   assert initial_state != final_state
   ```

## Common Issues

### Issue: `RuntimeError: no running event loop`

**Cause:** Calling async function without `await` or `asyncio.run()`

**Fix:**
```python
# In tests - use @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_func():
    await async_operation()

# In sync code - use asyncio.run()
import asyncio
asyncio.run(async_function())
```

### Issue: `TypeError: object MagicMock can't be used in 'await' expression`

**Cause:** Using `MagicMock` instead of `AsyncMock`

**Fix:**
```python
# Wrong
mock.method = MagicMock()

# Correct
from unittest.mock import AsyncMock
mock.method = AsyncMock()
```

### Issue: Tests pass locally but fail in CI

**Cause:** Different python-telegram-bot versions

**Fix:**
```txt
# requirements-test.txt
python-telegram-bot>=20.0
pytest>=7.0
pytest-asyncio>=0.21.0
```

---

**Last Updated:** 2025-10-22
**python-telegram-bot version:** 20+
