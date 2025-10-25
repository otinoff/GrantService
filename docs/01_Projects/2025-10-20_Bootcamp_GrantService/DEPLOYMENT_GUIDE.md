# DEPLOYMENT GUIDE - ProductionWriter
## Quick Start для Production Deployment

**Дата:** 2025-10-24
**Статус:** ✅ PRODUCTION READY

---

## 🚀 QUICK START (5 минут)

### Step 1: Проверка окружения

```bash
# 1. Проверить Python dependencies
pip list | grep -E "qdrant-client|psycopg2|sentence-transformers"

# Если чего-то нет:
pip install qdrant-client psycopg2-binary sentence-transformers

# 2. Проверить Qdrant server
curl http://5.35.88.251:6333/collections/knowledge_sections

# Expected output: {"result": {...}, "status": "ok"}

# 3. Проверить PostgreSQL
psql -h localhost -U postgres -d grantservice -c "SELECT COUNT(*) FROM knowledge_sections;"

# Expected output: 46 (или больше)
```

### Step 2: Environment Variables

Создать файл `.env` в корне проекта:

```bash
# GigaChat API
GIGACHAT_CREDENTIALS=<your_base64_credentials>
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# PostgreSQL (for Expert Agent)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=root
POSTGRES_DB=grantservice

# Qdrant (server)
QDRANT_HOST=5.35.88.251
QDRANT_PORT=6333

# Rate Limiting
RATE_LIMIT_DELAY=6
```

### Step 3: Test ProductionWriter

```bash
# Запустить тест
cd C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService
python scripts/test_production_writer.py

# Expected output:
# ✅ TEST COMPLETED SUCCESSFULLY
# Duration: ~130s
# Character count: 44,553
# Exit code: 0
```

### Step 4: Integration with Telegram Bot

```python
# В файле handlers/grant_handler.py

from lib.production_writer import ProductionWriter

async def generate_grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler: /generate_grant <anketa_id>
    """
    # 1. Parse anketa_id
    try:
        anketa_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: /generate_grant <anketa_id>")
        return

    # 2. Load anketa from DB
    anketa_data = context.bot_data['db'].load_anketa(anketa_id)

    if not anketa_data:
        await update.message.reply_text(f"❌ Anketa {anketa_id} not found")
        return

    # 3. Send status
    status_msg = await update.message.reply_text(
        "⏳ Генерирую грантовую заявку...\n"
        "Это займёт ~2 минуты"
    )

    # 4. Initialize ProductionWriter
    writer = ProductionWriter(
        llm_provider='gigachat',
        qdrant_host=os.getenv('QDRANT_HOST', '5.35.88.251'),
        qdrant_port=int(os.getenv('QDRANT_PORT', 6333)),
        rate_limit_delay=int(os.getenv('RATE_LIMIT_DELAY', 6)),
        db=context.bot_data['db']
    )

    # 5. Generate grant application
    try:
        import time
        start_time = time.time()

        grant_application = await writer.write(anketa_data)

        duration = time.time() - start_time

        # 6. Save to DB
        grant_id = context.bot_data['db'].save_grant_application(
            anketa_id=anketa_id,
            content=grant_application,
            char_count=len(grant_application)
        )

        # 7. Update status
        await status_msg.edit_text(
            f"✅ Заявка готова!\n\n"
            f"📊 Статистика:\n"
            f"• Длина: {len(grant_application):,} символов\n"
            f"• Время: {duration:.1f} секунд\n"
            f"• Секций: 10\n\n"
            f"Отправляю файл..."
        )

        # 8. Send file
        from io import BytesIO

        file_content = grant_application.encode('utf-8')
        file = BytesIO(file_content)
        file.name = f"grant_{grant_id}.md"

        await update.message.reply_document(
            document=file,
            filename=f"grant_{grant_id}.md",
            caption=f"📄 Грантовая заявка #{grant_id}\n"
                    f"Длина: {len(grant_application):,} символов"
        )

    except Exception as e:
        logger.error(f"Failed to generate grant: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка генерации:\n{str(e)}\n\n"
            f"Попробуйте позже или обратитесь к администратору"
        )


# Регистрация handler
application.add_handler(CommandHandler("generate_grant", generate_grant_command))
```

---

## 📋 PRODUCTION CHECKLIST

### Pre-deployment

- [ ] Все dependencies установлены
- [ ] Qdrant server доступен (5.35.88.251:6333)
- [ ] PostgreSQL доступен (localhost:5432)
- [ ] GigaChat credentials настроены
- [ ] Environment variables загружены
- [ ] Test script проходит успешно

### Deployment

- [ ] ProductionWriter интегрирован в Telegram Bot
- [ ] Handler `/generate_grant` добавлен
- [ ] Logging настроен
- [ ] Error handling добавлен
- [ ] Протестировано на dev bot

### Post-deployment

- [ ] Мониторинг ошибок (первые 24 часа)
- [ ] Сбор метрик (duration, length, success rate)
- [ ] User feedback collection
- [ ] Performance optimization (если нужно)

---

## 🔧 TROUBLESHOOTING

### Problem 1: Qdrant connection failed

**Error:**
```
ConnectionError: Cannot connect to Qdrant at 5.35.88.251:6333
```

**Solution:**
```bash
# 1. Проверить доступность
curl http://5.35.88.251:6333

# 2. Проверить firewall
ping 5.35.88.251

# 3. Fallback to local Qdrant (если server недоступен)
docker run -p 6333:6333 qdrant/qdrant
```

### Problem 2: GigaChat rate limit

**Error:**
```
HTTP 529: Service Overloaded
```

**Solution:**
```python
# Увеличить delay
writer = ProductionWriter(
    rate_limit_delay=10  # было 6
)
```

### Problem 3: PostgreSQL connection failed

**Error:**
```
psycopg2.OperationalError: connection to server failed
```

**Solution:**
```bash
# 1. Проверить PostgreSQL running
pg_isready

# 2. Проверить credentials
psql -h localhost -U postgres -d grantservice

# 3. Создать DB если не существует
createdb -U postgres grantservice
```

### Problem 4: Generation too slow (>180s)

**Причина:** GigaChat API медленно отвечает

**Solution:**
```python
# Уменьшить max_tokens per section
async with self.llm_client as client:
    section_content = await client.generate_text(
        prompt=prompt,
        max_tokens=3000  # было 4000
    )
```

### Problem 5: Low quality output

**Причина:** Anketa data неполные

**Solution:**
```python
# Добавить validation перед генерацией
def validate_anketa(anketa_data: Dict) -> bool:
    required_fields = [
        ('Основная информация', 'Название проекта'),
        ('Суть проекта', 'Проблема'),
        ('География', 'Регион'),
        ('Целевая аудитория', 'Описание')
    ]

    for section, field in required_fields:
        if not anketa_data.get(section, {}).get(field):
            raise ValueError(f"Missing required field: {section}.{field}")

    return True

# Use в handler
try:
    validate_anketa(anketa_data)
    grant = await writer.write(anketa_data)
except ValueError as e:
    await update.message.reply_text(f"❌ Анкета неполная: {e}")
```

---

## 📊 MONITORING & METRICS

### Key Metrics to Track

```python
# В handler после генерации
metrics = {
    "grant_id": grant_id,
    "anketa_id": anketa_id,
    "duration_seconds": duration,
    "character_count": len(grant_application),
    "word_count": len(grant_application.split()),
    "sections_generated": 10,
    "qdrant_queries": 5,  # или динамически считать
    "timestamp": datetime.now().isoformat(),
    "user_id": update.effective_user.id
}

# Save to DB or logs
logger.info(f"Grant generated: {json.dumps(metrics)}")
```

### Expected Metrics (healthy state)

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| Duration | 130s | 90-180s |
| Character count | 44,000 | 30,000-60,000 |
| Success rate | 100% | >95% |
| Error rate | 0% | <5% |

---

## 🔄 ROLLBACK PLAN

Если ProductionWriter не работает в production:

### Step 1: Immediate fallback

```python
# В handler добавить fallback
try:
    writer = ProductionWriter(...)
    grant = await writer.write(anketa_data)
except Exception as e:
    logger.error(f"ProductionWriter failed: {e}")

    # FALLBACK to Iteration 30
    from standalone_writer import StandaloneWriter

    writer_v30 = StandaloneWriter(llm_provider='gigachat')
    grant = await writer_v30.write(
        project_data=extract_project_data(anketa_data),
        research_results={}  # empty
    )
```

### Step 2: Diagnose issue

```bash
# 1. Check logs
tail -f logs/production_writer_*.log

# 2. Check Qdrant
curl http://5.35.88.251:6333/collections/knowledge_sections

# 3. Check PostgreSQL
psql -h localhost -U postgres -d grantservice -c "SELECT COUNT(*) FROM knowledge_sections;"

# 4. Test manually
python scripts/test_production_writer.py
```

### Step 3: Fix & redeploy

```bash
# 1. Fix code
# 2. Test locally
python scripts/test_production_writer.py

# 3. Commit & push
git add lib/production_writer.py
git commit -m "Fix: <issue description>"
git push origin main

# 4. Deploy
# 5. Monitor
```

---

## ✅ SUCCESS CRITERIA

**ProductionWriter считается успешно deployed если:**

1. ✅ Success rate >= 95% (first 100 requests)
2. ✅ Average duration <= 180 seconds
3. ✅ Average length >= 30,000 characters
4. ✅ No critical errors in logs
5. ✅ User satisfaction >= 80%

---

## 📞 SUPPORT

**Если возникли проблемы:**

1. Проверить [Troubleshooting](#troubleshooting)
2. Посмотреть logs в `logs/production_writer_*.log`
3. Проверить [Iteration 31 Final Report](reports/Iteration_31_FINAL_REPORT.md)
4. Откатиться на Iteration 30 если критично

---

**Deployment Guide подготовлен:** 2025-10-24
**Claude Code - Ready for Production** ✅
