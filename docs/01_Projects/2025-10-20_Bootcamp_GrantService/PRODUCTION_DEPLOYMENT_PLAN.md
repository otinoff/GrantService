# 🚀 PRODUCTION DEPLOYMENT PLAN
## ProductionWriter → Server 178.236.17.55

**Дата:** 2025-10-24
**Production Server:** 178.236.17.55
**Status:** ✅ READY TO DEPLOY

---

## 📋 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ ЧТО УЖЕ РАБОТАЕТ

**На локали (разработка):**
- ✅ ProductionWriter (44K символов за 2 минуты)
- ✅ Qdrant server (5.35.88.251:6333)
- ✅ PostgreSQL (localhost:5432)
- ✅ Expert Agent integration
- ✅ GigaChat API
- ✅ Все тесты прошли (exit code 0)

**На production сервере (178.236.17.55):**
```
Проверим что есть:
- FastAPI сервер (claude_wrapper_178_production.py)
- Claude Code CLI OAuth Max subscription
- WebSearch support
- БД PostgreSQL
```

---

## 🎯 FLUENT WORKFLOW (Целевой)

### Схема автоматической генерации

```
1. ПОЛЬЗОВАТЕЛЬ
   └─> Заполняет анкету (Telegram Bot / Web interface)
       └─> Сохраняется в PostgreSQL

2. АВТОМАТИЧЕСКИЙ ТРИГГЕР
   └─> При завершении анкеты → вызывается ProductionWriter

3. PRODUCTIONWRITER
   ├─> Загружает anketa_data из БД
   ├─> Генерирует 10 секций (Qdrant + GigaChat)
   ├─> Токены тратятся (~130 секунд)
   └─> Заявка готова (44K символов)

4. АВТОМАТИЧЕСКАЯ ОТПРАВКА
   ├─> Пользователю (Telegram / Email)
   └─> В рабочий чат админов (уведомление)

5. АДМИНЫ
   └─> Видят новую заявку в рабочем чате
       └─> Могут одобрить/редактировать
```

---

## 🔧 ЧТО НУЖНО СДЕЛАТЬ

### Phase 1: Подготовка Production Environment (1 час)

#### 1.1 Проверить Production Server

```bash
# SSH на production
ssh user@178.236.17.55

# Проверить зависимости
python3 -c "import qdrant_client, psycopg2, sentence_transformers; print('OK')"

# Если нет - установить
pip3 install qdrant-client psycopg2-binary sentence-transformers

# Проверить Qdrant доступность
curl http://5.35.88.251:6333/collections/knowledge_sections

# Проверить PostgreSQL
psql -h localhost -U postgres -d grantservice -c "SELECT COUNT(*) FROM knowledge_sections;"
```

#### 1.2 Скопировать ProductionWriter на сервер

```bash
# На локальной машине
scp C:/SnowWhiteAI/GrantService_Project/01_Projects/2025-10-20_Bootcamp_GrantService/lib/production_writer.py \
    user@178.236.17.55:/path/to/GrantService/agents/

scp C:/SnowWhiteAI/GrantService/expert_agent/expert_agent.py \
    user@178.236.17.55:/path/to/GrantService/expert_agent/
```

#### 1.3 Настроить Environment Variables

```bash
# На production сервере
nano /path/to/GrantService/.env

# Добавить:
GIGACHAT_CREDENTIALS=<production_credentials>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
QDRANT_HOST=5.35.88.251
QDRANT_PORT=6333
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<production_password>
POSTGRES_DB=grantservice
RATE_LIMIT_DELAY=6
```

---

### Phase 2: Интеграция в FastAPI (2 часа)

#### 2.1 Создать новый endpoint `/generate_grant`

```python
# Добавить в claude_wrapper_178_production.py

from agents.production_writer import ProductionWriter
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Endpoint для генерации заявки
@app.post("/generate_grant")
async def generate_grant(anketa_id: int):
    """
    Генерация грантовой заявки из анкеты

    Args:
        anketa_id: ID анкеты в БД

    Returns:
        {
            "grant_id": int,
            "content": str,
            "character_count": int,
            "duration_seconds": float,
            "status": "success"
        }
    """
    try:
        logger.info(f"📝 Generating grant for anketa_id={anketa_id}")

        # 1. Загрузить анкету из БД
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB')
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT anketa_data
            FROM anketas
            WHERE id = %s
        """, (anketa_id,))

        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail=f"Anketa {anketa_id} not found")

        anketa_data = result[0]  # JSON field

        # 2. Инициализировать ProductionWriter
        writer = ProductionWriter(
            llm_provider='gigachat',
            qdrant_host=os.getenv('QDRANT_HOST', '5.35.88.251'),
            qdrant_port=int(os.getenv('QDRANT_PORT', 6333)),
            postgres_host=os.getenv('POSTGRES_HOST'),
            postgres_port=int(os.getenv('POSTGRES_PORT')),
            postgres_user=os.getenv('POSTGRES_USER'),
            postgres_password=os.getenv('POSTGRES_PASSWORD'),
            postgres_db=os.getenv('POSTGRES_DB'),
            rate_limit_delay=int(os.getenv('RATE_LIMIT_DELAY', 6))
        )

        # 3. Генерировать заявку
        import time
        start_time = time.time()

        grant_content = await writer.write(anketa_data)

        duration = time.time() - start_time

        # 4. Сохранить в БД
        cursor.execute("""
            INSERT INTO grant_applications
            (anketa_id, content, character_count, duration_seconds, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
        """, (anketa_id, grant_content, len(grant_content), duration))

        grant_id = cursor.fetchone()[0]
        conn.commit()

        # 5. Отправить уведомление в Telegram admin chat
        await send_admin_notification(
            f"✅ Новая заявка #{grant_id}\n"
            f"Анкета: {anketa_id}\n"
            f"Длина: {len(grant_content):,} символов\n"
            f"Время: {duration:.1f}s"
        )

        logger.info(f"✅ Grant {grant_id} generated: {len(grant_content)} chars in {duration:.1f}s")

        return {
            "grant_id": grant_id,
            "content": grant_content,
            "character_count": len(grant_content),
            "duration_seconds": duration,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"❌ Failed to generate grant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


# Helper для отправки в admin chat
async def send_admin_notification(message: str):
    """
    Отправить уведомление в Telegram admin chat
    """
    import aiohttp

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

    if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.warning("⚠️ Telegram credentials not set, skipping notification")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    async with aiohttp.ClientSession() as session:
        await session.post(url, json={
            "chat_id": ADMIN_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })
```

#### 2.2 Создать таблицу в БД (если нет)

```sql
-- На production сервере
psql -h localhost -U postgres -d grantservice

-- Создать таблицу для анкет
CREATE TABLE IF NOT EXISTS anketas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    anketa_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Создать таблицу для заявок
CREATE TABLE IF NOT EXISTS grant_applications (
    id SERIAL PRIMARY KEY,
    anketa_id INTEGER REFERENCES anketas(id),
    content TEXT NOT NULL,
    character_count INTEGER,
    duration_seconds FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    sent_to_user_at TIMESTAMP,
    approved_at TIMESTAMP
);

-- Создать индексы
CREATE INDEX IF NOT EXISTS idx_anketas_user_id ON anketas(user_id);
CREATE INDEX IF NOT EXISTS idx_anketas_status ON anketas(status);
CREATE INDEX IF NOT EXISTS idx_grants_anketa_id ON grant_applications(anketa_id);
CREATE INDEX IF NOT EXISTS idx_grants_status ON grant_applications(status);
```

---

### Phase 3: Автоматизация Workflow (1 час)

#### 3.1 Триггер на завершение анкеты

```python
# Добавить endpoint для завершения анкеты
@app.post("/anketa/{anketa_id}/complete")
async def complete_anketa(anketa_id: int):
    """
    Завершить заполнение анкеты и автоматически сгенерировать заявку
    """
    try:
        # 1. Обновить статус анкеты
        conn = psycopg2.connect(...)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE anketas
            SET status = 'completed', updated_at = NOW()
            WHERE id = %s
        """, (anketa_id,))
        conn.commit()

        # 2. АВТОМАТИЧЕСКИ запустить генерацию
        grant_result = await generate_grant(anketa_id)

        # 3. Отправить пользователю
        await send_grant_to_user(
            anketa_id=anketa_id,
            grant_id=grant_result['grant_id'],
            grant_content=grant_result['content']
        )

        return {
            "anketa_id": anketa_id,
            "status": "completed",
            "grant_id": grant_result['grant_id'],
            "message": "Заявка сгенерирована и отправлена"
        }

    except Exception as e:
        logger.error(f"❌ Failed to complete anketa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_grant_to_user(anketa_id: int, grant_id: int, grant_content: str):
    """
    Отправить готовую заявку пользователю
    """
    # Получить user_id из anketa
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM anketas WHERE id = %s", (anketa_id,))
    user_id = cursor.fetchone()[0]

    # Отправить через Telegram Bot
    import aiohttp

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    # Создать файл
    file_content = grant_content.encode('utf-8')

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    form = aiohttp.FormData()
    form.add_field('chat_id', str(user_id))
    form.add_field('document', file_content,
                   filename=f'grant_{grant_id}.md',
                   content_type='text/markdown')
    form.add_field('caption',
                   f"✅ Ваша грантовая заявка готова!\n\n"
                   f"📊 Длина: {len(grant_content):,} символов\n"
                   f"🎯 ID заявки: {grant_id}")

    async with aiohttp.ClientSession() as session:
        await session.post(url, data=form)

    logger.info(f"✅ Grant {grant_id} sent to user {user_id}")
```

---

### Phase 4: Testing на Production (30 минут)

```bash
# 1. Тест health check
curl http://178.236.17.55:8000/health

# 2. Создать тестовую анкету
curl -X POST http://178.236.17.55:8000/test/create_anketa \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "anketa_data": {
      "Основная информация": {
        "Название проекта": "Test Project"
      },
      "Суть проекта": {
        "Проблема": "Test problem"
      }
    }
  }'

# Expected output:
# {"anketa_id": 1, "status": "created"}

# 3. Завершить анкету (автоматически генерирует заявку)
curl -X POST http://178.236.17.55:8000/anketa/1/complete

# Expected output:
# {
#   "anketa_id": 1,
#   "status": "completed",
#   "grant_id": 1,
#   "message": "Заявка сгенерирована и отправлена"
# }

# 4. Проверить что заявка создана
curl http://178.236.17.55:8000/grant/1

# Expected output:
# {
#   "grant_id": 1,
#   "content": "# Заявка на получение...",
#   "character_count": 44553,
#   "status": "success"
# }
```

---

## 📊 DEPLOYMENT CHECKLIST

### Pre-deployment

- [ ] Проверить production server доступность
- [ ] Установить dependencies (qdrant-client, sentence-transformers, psycopg2)
- [ ] Скопировать ProductionWriter на сервер
- [ ] Настроить environment variables
- [ ] Проверить Qdrant connectivity (5.35.88.251:6333)
- [ ] Проверить PostgreSQL (localhost:5432)
- [ ] Создать таблицы БД (anketas, grant_applications)

### Deployment

- [ ] Добавить `/generate_grant` endpoint в FastAPI
- [ ] Добавить `/anketa/{id}/complete` endpoint
- [ ] Добавить helper functions (send_admin_notification, send_grant_to_user)
- [ ] Restart FastAPI server
- [ ] Проверить logs

### Testing

- [ ] Health check passed
- [ ] Create test anketa
- [ ] Complete anketa → auto-generate grant
- [ ] Check grant sent to user
- [ ] Check admin notification sent
- [ ] Verify БД records

### Post-deployment

- [ ] Monitor logs (first 24 hours)
- [ ] Track metrics (duration, character_count, success_rate)
- [ ] Collect user feedback
- [ ] Optimize if needed

---

## 🔥 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### Fluent Workflow после deployment

```
ПОЛЬЗОВАТЕЛЬ                    СИСТЕМА                        АДМИНЫ
    |                               |                              |
    | 1. Заполняет анкету          |                              |
    |----------------------------->|                              |
    |                               | 2. Сохранение в БД          |
    |                               | 3. Вызов ProductionWriter   |
    |                               | 4. Генерация (130s)         |
    |                               | 5. Сохранение заявки        |
    |<-----------------------------|                              |
    | 6. Получает файл .md          |----------------------------->|
    |    (Telegram/Email)           | 7. Уведомление в admin chat |
    |                               |                              |
    |                               |                              |
```

### Метрики успеха

| Метрика | Target | Текущий тест |
|---------|--------|--------------|
| Время генерации | < 180s | ✅ 130s |
| Длина заявки | > 30,000 chars | ✅ 44,553 chars |
| Success rate | > 95% | ✅ 100% (0 ошибок) |
| User satisfaction | > 80% | TBD (после deployment) |

---

## 🚨 ROLLBACK PLAN

Если что-то пошло не так:

```bash
# 1. Отключить автоматическую генерацию
# Закомментировать в /anketa/{id}/complete:
# grant_result = await generate_grant(anketa_id)

# 2. Использовать manual generation
# Админы вручную вызывают /generate_grant

# 3. Проверить logs
tail -f /var/log/grantservice/production.log

# 4. Откатить код если критично
git revert <commit_hash>
systemctl restart fastapi
```

---

## 📞 SUPPORT

**После deployment мониторим:**

1. **Logs:** `/var/log/grantservice/`
2. **Metrics:** Duration, character_count, success_rate
3. **Errors:** Qdrant connectivity, GigaChat rate limits
4. **User feedback:** Telegram admin chat

**Документация:**
- [Iteration 31 Report](reports/Iteration_31_FINAL_REPORT.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Production Writer Code](lib/production_writer.py)

---

**Deployment Plan подготовлен:** 2025-10-24
**Production Server:** 178.236.17.55
**Status:** ✅ READY TO DEPLOY

**NEXT STEP:** Подключиться к серверу и начать Phase 1
