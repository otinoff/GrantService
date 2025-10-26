# Integration Guide - Interactive Pipeline Handler

## Как интегрировать в main.py

### Шаг 1: Import handler

```python
# В начале main.py
from handlers.interactive_pipeline_handler import InteractivePipelineHandler
```

### Шаг 2: Инициализировать handler

```python
# В классе GrantServiceBot.__init__()
def __init__(self):
    # ... existing code ...

    # Initialize interactive pipeline handler
    self.pipeline_handler = InteractivePipelineHandler(db=self.db)
    logger.info("[OK] Interactive Pipeline Handler initialized")
```

### Шаг 3: Зарегистрировать callback handlers

```python
# В методе setup_handlers()
def setup_handlers(self):
    # ... existing handlers ...

    # Interactive Pipeline callbacks
    application.add_handler(CallbackQueryHandler(
        self.pipeline_handler.handle_start_audit,
        pattern=r"^start_audit:anketa:\w+$"
    ))

    application.add_handler(CallbackQueryHandler(
        self.pipeline_handler.handle_start_grant,
        pattern=r"^start_grant:anketa:\w+$"
    ))

    application.add_handler(CallbackQueryHandler(
        self.pipeline_handler.handle_start_review,
        pattern=r"^start_review:grant:\w+$"
    ))

    logger.info("[OK] Interactive Pipeline callbacks registered")
```

### Шаг 4: Вызвать on_anketa_complete

Найти строку где вызывается `show_completion_screen()` и заменить на:

```python
# БЫЛО:
# await self.show_completion_screen(update, context, anketa_id)

# СТАЛО:
await self.pipeline_handler.on_anketa_complete(
    update=update,
    context=context,
    anketa_id=anketa_id,
    session_data=session
)
```

Или можно модифицировать `show_completion_screen()` чтобы она вызывала pipeline handler:

```python
async def show_completion_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
    """Показать экран успешного завершения с interactive pipeline"""

    # Получить session
    user_id = update.effective_user.id
    session = self.get_user_session(user_id)

    # Вызвать pipeline handler
    await self.pipeline_handler.on_anketa_complete(
        update=update,
        context=context,
        anketa_id=anketa_id,
        session_data=session
    )
```

---

## Testing

### Manual Test Flow

1. **Start interview:**
   ```
   /start
   ```

2. **Complete anketa:**
   - Answer all questions
   - Receive `anketa.txt` file
   - See button "Начать аудит"

3. **Click "Начать аудит":**
   - Wait ~30 seconds
   - Receive `audit.txt` file
   - See button "Начать написание гранта"

4. **Click "Начать написание гранта":**
   - Wait ~2-3 minutes
   - Receive `grant.txt` file
   - See button "Сделать ревью"

5. **Click "Сделать ревью":**
   - Wait ~30 seconds
   - Receive `review.txt` file
   - See final message "Готово!"

### Check Files

All 4 files should be in chat history:
- ✅ `anketa_<id>.txt`
- ✅ `audit_<id>.txt`
- ✅ `grant_<id>.txt`
- ✅ `review_<id>.txt`

---

## Troubleshooting

### Issue: "Метод audit_anketa_async не найден"

**Fix:** Проверить что agents имеют async методы. Если нет - обернуть:

```python
# В interactive_pipeline_handler.py
import asyncio

async def handle_start_audit(self, ...):
    # Если метод sync:
    audit_result = await asyncio.to_thread(
        auditor.audit_anketa, anketa_id
    )

    # Или если метод уже async:
    audit_result = await auditor.audit_anketa_async(anketa_id)
```

### Issue: "Файл не отправляется"

**Check:**
1. Временный файл создается корректно
2. Encoding UTF-8 используется
3. Путь к файлу правильный
4. Telegram Bot API доступен

### Issue: "Callback handler не срабатывает"

**Check:**
1. Pattern regex правильный
2. Callback data совпадает с pattern
3. Handler зарегистрирован в application
4. Нет конфликтующих handlers

---

## Migration Path (без изменения main.py)

Если не хотите менять main.py, можно использовать feature flag:

```python
# В config/settings.py
INTERACTIVE_PIPELINE_ENABLED = os.getenv('INTERACTIVE_PIPELINE_ENABLED', 'false') == 'true'

# В show_completion_screen()
if INTERACTIVE_PIPELINE_ENABLED:
    await self.pipeline_handler.on_anketa_complete(...)
else:
    # Old behavior
    await self._show_old_completion_screen(...)
```

Тогда можно постепенно переключать пользователей:
- Dev: `INTERACTIVE_PIPELINE_ENABLED=true`
- Production: `INTERACTIVE_PIPELINE_ENABLED=false` (пока)
- После тестирования: `INTERACTIVE_PIPELINE_ENABLED=true` (везде)

---

## Next Steps

После интеграции:
1. ✅ Manual testing (test all 4 steps)
2. ✅ Check logs for errors
3. ✅ Test edge cases (double-click buttons, etc.)
4. ✅ Implement state machine (Phase 7)
5. ✅ Write integration tests (Phase 8)
6. ✅ Deploy to staging

---

**Status:** Ready for integration
**Est. Integration Time:** 30 minutes
