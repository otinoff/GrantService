# Telegram Bot Architecture Research

## Проблемы и Решения

### Проблема #1: Event Loop Blocking (РЕШЕНО ✅)
**Симптом**: Бот не обрабатывает входящие сообщения пока ждет ответа пользователя

**Причина**: `conduct_interview()` блокировал весь event loop через `await answer_queue.get()`

**Решение**:
```python
# ПЛОХО - блокирует event loop
result = await agent.conduct_interview(...)

# ХОРОШО - запускает в background task
async def run_interview():
    result = await agent.conduct_interview(...)

asyncio.create_task(run_interview())
```

**Статус**: Исправлено в commit, бот теперь обрабатывает сообщения ✅

---

### Проблема #2: Progress Bar Spam (ТЕКУЩАЯ)
**Симптом**: Бот отправляет progress bars вместо следующих вопросов

**Логи**:
```
17:47:18 - [ANSWER] User: для жителей Кемреово литерарный проект
17:47:18 - sendMessage (progress bar)
17:47:18 - [WAITING] Waiting for answer
```

**Гипотеза**: Агент обрабатывает каждое сообщение как новый ответ, даже если уже обработал предыдущий

**TODO**: Исследовать логику `conduct_interview()` - почему не генерирует новый вопрос после получения ответа

---

## Best Practices for Telegram Bots

### Async Architecture

#### 1. **Never Block Event Loop**
```python
# BAD
answer = input("Wait for user")  # Blocks!

# GOOD
answer = await asyncio.Queue().get()  # Non-blocking wait
```

#### 2. **Use Background Tasks for Long Operations**
```python
async def long_operation():
    # LLM calls, database queries, etc.
    result = await heavy_processing()
    await send_result(result)

# Start in background, don't await
asyncio.create_task(long_operation())
```

#### 3. **Message Handler Architecture**
```python
# Pattern: Single handler for all text messages
application.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    handle_message
))

# Route inside handler based on state
async def handle_message(update, context):
    user_id = update.effective_user.id

    # Check different states
    if interview_active(user_id):
        await handle_interview_message(...)
    elif waiting_for_payment(user_id):
        await handle_payment_message(...)
    else:
        await show_main_menu(...)
```

---

## State Management Patterns

### Pattern 1: In-Memory Dictionary (CURRENT)
```python
# Simple but lost on restart
active_interviews = {
    user_id: {
        'agent': agent,
        'answer_queue': asyncio.Queue(),
        'state': 'waiting_answer'
    }
}
```

**Pros**: Fast, simple
**Cons**: Lost on restart, no persistence

### Pattern 2: Database State
```python
# Persistent across restarts
db.save_interview_state(user_id, {
    'current_question': 5,
    'answers': {...},
    'state': 'waiting_answer'
})
```

**Pros**: Persistent, survives restarts
**Cons**: Slower, needs cleanup

### Pattern 3: Redis State (BEST)
```python
# Fast AND persistent
redis.setex(
    f'interview:{user_id}',
    3600,  # TTL 1 hour
    json.dumps(state)
)
```

**Pros**: Fast, persistent, auto-cleanup
**Cons**: Extra dependency

---

## Conversation Flow Patterns

### Pattern 1: Linear Flow
```
Question 1 → Answer 1 → Question 2 → Answer 2 → ... → End
```
Simple but inflexible

### Pattern 2: State Machine (CURRENT)
```
INIT → EXPLORING → DEEPENING → VALIDATING → FINALIZING
```
Flexible but complex

### Pattern 3: Reference Points (CURRENT V2)
```
P0 Critical → P1 Important → P2 Desirable → P3 Optional
```
Adaptive, prioritizes essential info

---

## Queue-Based Answer Collection

### Current Architecture:
```
[User sends message]
     ↓
[Telegram → main.py handle_message]
     ↓
[interview_handler.handle_message]
     ↓
[answer_queue.put(answer)]  ← Non-blocking
     ↓
[Background Task awaiting queue.get()]  ← Blocking (but in background)
     ↓
[Process answer → Generate next question]
```

**Key**: Main event loop never blocks, only background task blocks

---

## Debugging Techniques

### 1. DEBUG Logging at Every Step
```python
logger.info(f"[DEBUG MAIN] handle_message called for user {user_id}")
logger.info(f"[DEBUG MAIN] Authorization check: {is_authorized}")
logger.info(f"[DEBUG MAIN] Interview active: {is_active}")
```

### 2. Track Message Flow
```python
logger.info(f"[WAITING] Waiting for answer from user {user_id}")
logger.info(f"[ANSWER] User {user_id}: {answer[:50]}...")
logger.info(f"[RECEIVED] Got answer from queue")
```

### 3. Monitor getUpdates vs Processing
```bash
# Should see both:
getUpdates "HTTP/1.1 200 OK"  # Receiving messages
[DEBUG MAIN] handle_message called  # Processing messages
```

---

## Common Pitfalls

### ❌ Pitfall 1: Awaiting in Sync Code
```python
def sync_function():
    result = await async_call()  # SyntaxError!
```

### ❌ Pitfall 2: Not Handling Concurrent Users
```python
# BAD - one global queue for all users
global_queue = asyncio.Queue()

# GOOD - queue per user
user_queues = {user_id: asyncio.Queue()}
```

### ❌ Pitfall 3: Forgetting to Clean Up State
```python
# Memory leak if interview never finishes
self.active_interviews[user_id] = {...}

# Fix: Add timeout or /stop command
async def cleanup_old_interviews():
    for user_id, data in list(self.active_interviews.items()):
        if time_since(data['started']) > 1_HOUR:
            del self.active_interviews[user_id]
```

---

## Next Steps

1. ✅ Fix event loop blocking (DONE)
2. 🔄 Fix progress bar spam (IN PROGRESS)
3. ⏳ Add state persistence (TODO)
4. ⏳ Add interview timeout (TODO)
5. ⏳ Add better error handling (TODO)

---

## References

- python-telegram-bot docs: https://docs.python-telegram-bot.org/
- Asyncio patterns: https://docs.python.org/3/library/asyncio-task.html
- State machine patterns: FSM (Finite State Machine)

---

**Generated**: 2025-10-21
**Status**: Active Research
