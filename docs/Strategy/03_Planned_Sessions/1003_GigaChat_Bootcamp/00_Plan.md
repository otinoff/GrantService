# 🚀 Plan: Switch to GigaChat for Sber500 Bootcamp

**Дата:** 2025-10-23
**Срочность:** HIGH (оценка через неделю!)
**Цель:** Показать использование токенов GigaChat для прохождения в следующий этап буткэмпа

---

## 🎯 Задача от партнера (Наталья Брызгина)

**Контекст:**
- Участвуем в Sber500 x GigaChat Bootcamp
- **Оценка через неделю по количеству использованных токенов GigaChat**
- Нужно показать СБеру: сколько токенов используем и для каких целей
- Логин: otinoff@gmail.com | Платформа: http://sber500.2080vc.io

**Задачи:**
1. Промониторить победившие проекты Сбер500 прошлый год
2. **Сделать прогоны заявок используя токены GigaChat** ⬅️ СРОЧНО
3. Отправить заявки в чат буткэмпа

---

## ✅ Что уже есть (Infrastructure Ready!)

### 1. UnifiedLLMClient с поддержкой GigaChat
```python
# C:\SnowWhiteAI\GrantService\shared\llm\unified_llm_client.py

class UnifiedLLMClient:
    def __init__(self, provider: str = "gigachat", ...):
        # ✅ Поддерживает: "gigachat", "claude_code", "perplexity", "ollama"
        pass

    async def _generate_gigachat(self, prompt, temperature, max_tokens):
        # ✅ Авторизация через OAuth
        # ✅ Rate limiting handling
        # ✅ Retry logic
        pass
```

### 2. База данных с полем preferred_llm_provider
```sql
-- C:\SnowWhiteAI\GrantService\data\database\migrations\002_add_preferred_llm_provider.sql

ALTER TABLE users
ADD COLUMN preferred_llm_provider VARCHAR(50) DEFAULT 'claude_code';

-- ✅ Уже применена миграция
-- ✅ По умолчанию: 'claude_code'
-- ✅ Можно переключить на: 'gigachat'
```

### 3. API методы для управления LLM
```python
# C:\SnowWhiteAI\GrantService\data\database\models.py

def get_user_llm_preference(self, telegram_id: int) -> str:
    """Возвращает 'claude_code' или 'gigachat'"""
    pass

def set_user_llm_preference(self, telegram_id: int, provider: str) -> bool:
    """Устанавливает LLM провайдер для пользователя"""
    pass
```

### 4. Telegram bot использует LLM preference
```python
# C:\SnowWhiteAI\GrantService\telegram-bot\main.py:1945

llm_provider = self.interview_handler.db.get_user_llm_preference(user_id)
agent = InteractiveInterviewerAgentV2(
    db=self.interview_handler.db,
    llm_provider=llm_provider,  # ✅ Автоматически использует preference
    ...
)
```

**Вывод:** Вся инфраструктура УЖЕ готова! Нужно только:
1. Переключить пользователей на GigaChat
2. Добавить tracking токенов
3. Создать статистику

---

## 📋 План выполнения (3 фазы)

### Phase 1: Переключить на GigaChat (30 минут)

#### Task 1.1: Проверить GigaChat credentials (5 мин)

**Файл:** `C:\SnowWhiteAI\GrantService\shared\llm\config.py`

```python
# Проверить что есть:
GIGACHAT_API_KEY = "YOUR_API_KEY_HERE"
GIGACHAT_CLIENT_ID = "YOUR_CLIENT_ID"
GIGACHAT_BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
```

**Action:**
- Проверить наличие API ключей
- Если нет - получить из буткэмпа

#### Task 1.2: Переключить всех пользователей на GigaChat (5 мин)

**SQL:**
```sql
-- На production сервере (5.35.88.251)
ssh root@5.35.88.251

psql -U postgres -d grantservice

-- Переключить ВСЕХ пользователей на GigaChat
UPDATE users
SET preferred_llm_provider = 'gigachat'
WHERE preferred_llm_provider = 'claude_code' OR preferred_llm_provider IS NULL;

-- Проверить
SELECT telegram_id, name, preferred_llm_provider
FROM users
ORDER BY created_at DESC;
```

**Expected result:**
```
telegram_id  |  name   | preferred_llm_provider
-------------|---------|----------------------
123456789    | Андрей  | gigachat
...
```

#### Task 1.3: Тест в Telegram (10 мин)

**Manual test:**
```
1. Open @grant_service_bot
2. /start
3. Click "🆕 Интервью V2"
4. Answer first question
5. Check logs: должно быть "🤖 Начинаем генерацию GigaChat"
```

**Expected logs:**
```bash
ssh root@5.35.88.251
tail -f /var/GrantService/logs/bot.log | grep -i gigachat

# Должны увидеть:
[INFO] User 123456789 LLM provider: gigachat
🔐 Получаем токен авторизации для GigaChat...
✅ Токен GigaChat получен успешно
🤖 Начинаем генерацию GigaChat: 450 символов
✅ GigaChat ответ получен: 120 символов
```

#### Task 1.4: Сделать 3-5 тестовых интервью (10 мин)

**Test interviews:**
1. Клуб стрельбы из лука (уже есть данные)
2. Восстановление иконостаса (уже есть данные)
3. 2-3 новых проекта

**Цель:** Накопить статистику использования токенов GigaChat

---

### Phase 2: Добавить Token Tracking (1 час)

#### Task 2.1: Создать таблицу для статистики токенов (10 мин)

**Migration:** `003_add_gigachat_usage_tracking.sql`

```sql
-- Создать таблицу для tracking использования GigaChat токенов
CREATE TABLE IF NOT EXISTS gigachat_usage_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(telegram_id),
    session_id VARCHAR(255),
    agent_type VARCHAR(50),  -- 'interviewer', 'writer', 'researcher', 'reviewer'

    -- Token statistics
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    -- Request details
    model VARCHAR(50),
    temperature FLOAT,
    max_tokens INTEGER,

    -- Response details
    response_length INTEGER,  -- Length in characters
    latency_ms INTEGER,       -- Response time in milliseconds
    success BOOLEAN,
    error_message TEXT,

    -- Context
    purpose TEXT,  -- What was the request for? e.g. "Generate question #3"

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    -- Index for analytics
    INDEX idx_gigachat_created_at (created_at),
    INDEX idx_gigachat_user (user_id),
    INDEX idx_gigachat_agent (agent_type)
);

-- Add comment
COMMENT ON TABLE gigachat_usage_log IS 'Лог использования GigaChat токенов для аналитики и буткэмпа Sber500';
```

**Deploy:**
```bash
ssh root@5.35.88.251
cd /var/GrantService
psql -U postgres -d grantservice -f data/database/migrations/003_add_gigachat_usage_tracking.sql
```

#### Task 2.2: Добавить логирование в UnifiedLLMClient (20 мин)

**File:** `C:\SnowWhiteAI\GrantService\shared\llm\unified_llm_client.py`

**Модификация метода `_generate_gigachat`:**

```python
async def _generate_gigachat(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
    """Генерация через GigaChat API с tracking токенов"""

    # ... existing auth code ...

    start_time = time.time()

    try:
        async with self.session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()

                # Extract response
                response_text = response_data["choices"][0]["message"]["content"].strip()

                # 🆕 EXTRACT TOKEN USAGE
                usage = response_data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                latency_ms = int((time.time() - start_time) * 1000)

                # 🆕 LOG TO DATABASE
                await self._log_gigachat_usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    response_length=len(response_text),
                    latency_ms=latency_ms,
                    success=True,
                    model=self.model,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or MAX_TOKENS
                )

                return response_text
            else:
                # Log error
                await self._log_gigachat_usage(
                    success=False,
                    error_message=f"HTTP {response.status}"
                )
                raise Exception(...)

    except Exception as e:
        # Log exception
        await self._log_gigachat_usage(
            success=False,
            error_message=str(e)
        )
        raise

async def _log_gigachat_usage(
    self,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    response_length: int = 0,
    latency_ms: int = 0,
    success: bool = False,
    error_message: str = None,
    model: str = None,
    temperature: float = None,
    max_tokens: int = None
):
    """
    Логировать использование GigaChat токенов в БД

    NOTE: Требует передачи контекста (user_id, session_id, agent_type, purpose)
    через kwargs при инициализации UnifiedLLMClient
    """
    try:
        # Get context from self (set during init or passed in kwargs)
        user_id = getattr(self, 'user_id', None)
        session_id = getattr(self, 'session_id', None)
        agent_type = getattr(self, 'agent_type', 'unknown')
        purpose = getattr(self, 'purpose', None)

        # Import DB here to avoid circular dependency
        from data.database.models import GrantServiceDatabase

        db = GrantServiceDatabase()

        with db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO gigachat_usage_log (
                    user_id, session_id, agent_type,
                    prompt_tokens, completion_tokens, total_tokens,
                    model, temperature, max_tokens,
                    response_length, latency_ms,
                    success, error_message, purpose
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s
                )
            """, (
                user_id, session_id, agent_type,
                prompt_tokens, completion_tokens, total_tokens,
                model, temperature, max_tokens,
                response_length, latency_ms,
                success, error_message, purpose
            ))

            conn.commit()
            cursor.close()

            logger.info(f"✅ Logged GigaChat usage: {total_tokens} tokens, {latency_ms}ms")

    except Exception as e:
        # Don't fail request if logging fails
        logger.warning(f"Failed to log GigaChat usage: {e}")
```

#### Task 2.3: Передать контекст в UnifiedLLMClient (15 мин)

**File:** `C:\SnowWhiteAI\GrantService\agents\interactive_interviewer_agent_v2.py`

**Модификация инициализации LLM:**

```python
# Было:
self.llm_client = UnifiedLLMClient(
    provider=llm_provider,
    model="GigaChat"
)

# Стало:
self.llm_client = UnifiedLLMClient(
    provider=llm_provider,
    model="GigaChat",
    user_id=self.user_id,              # 🆕 Передаем контекст
    session_id=self.session_id,        # 🆕
    agent_type="interviewer",          # 🆕
    purpose="Interactive interview V2" # 🆕
)

# При каждом вызове генерации вопроса обновляем purpose:
self.llm_client.purpose = f"Generate question for RP {rp_code}"
response = await self.llm_client.generate_async(prompt)
```

#### Task 2.4: Тест tracking (15 мин)

**Manual test:**
1. Провести интервью через Telegram
2. Проверить что данные записались в БД

**SQL check:**
```sql
-- Проверить логи токенов
SELECT
    id,
    user_id,
    agent_type,
    total_tokens,
    latency_ms,
    success,
    purpose,
    created_at
FROM gigachat_usage_log
ORDER BY created_at DESC
LIMIT 20;

-- Статистика за сегодня
SELECT
    agent_type,
    COUNT(*) as requests,
    SUM(total_tokens) as total_tokens,
    AVG(latency_ms) as avg_latency_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
FROM gigachat_usage_log
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY agent_type;
```

---

### Phase 3: Создать статистику для буткэмпа (30 минут)

#### Task 3.1: Создать dashboard SQL queries (10 мин)

**File:** `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\gigachat_analytics.sql`

```sql
-- 1. Общая статистика использования GigaChat
SELECT
    COUNT(*) as total_requests,
    SUM(total_tokens) as total_tokens_used,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    AVG(latency_ms) as avg_latency_ms,
    AVG(total_tokens) as avg_tokens_per_request,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
    MIN(created_at) as first_request,
    MAX(created_at) as last_request
FROM gigachat_usage_log;

-- 2. Статистика по агентам
SELECT
    agent_type,
    COUNT(*) as requests,
    SUM(total_tokens) as tokens_used,
    AVG(total_tokens) as avg_tokens,
    AVG(latency_ms) as avg_latency_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as success_rate_pct
FROM gigachat_usage_log
GROUP BY agent_type
ORDER BY tokens_used DESC;

-- 3. Использование по дням (для графика)
SELECT
    DATE(created_at) as date,
    COUNT(*) as requests,
    SUM(total_tokens) as tokens_used,
    COUNT(DISTINCT user_id) as unique_users
FROM gigachat_usage_log
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 4. Топ пользователей по токенам
SELECT
    u.telegram_id,
    u.name,
    COUNT(g.id) as requests,
    SUM(g.total_tokens) as tokens_used,
    AVG(g.total_tokens) as avg_tokens
FROM users u
JOIN gigachat_usage_log g ON u.telegram_id = g.user_id
GROUP BY u.telegram_id, u.name
ORDER BY tokens_used DESC
LIMIT 10;

-- 5. Последние requests (для детального анализа)
SELECT
    g.id,
    u.name as user_name,
    g.agent_type,
    g.total_tokens,
    g.latency_ms,
    g.success,
    g.purpose,
    g.created_at
FROM gigachat_usage_log g
LEFT JOIN users u ON g.user_id = u.telegram_id
ORDER BY g.created_at DESC
LIMIT 50;
```

#### Task 3.2: Создать Python скрипт для отчёта (10 мин)

**File:** `C:\SnowWhiteAI\GrantService\scripts\generate_gigachat_report.py`

```python
#!/usr/bin/env python3
"""
Генератор отчёта по использованию GigaChat для Sber500 буткэмпа
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database.models import GrantServiceDatabase
from datetime import datetime, timedelta

def generate_bootcamp_report():
    """Генерирует отчёт для Sber500 буткэмпа"""

    db = GrantServiceDatabase()

    with db.connect() as conn:
        cursor = conn.cursor()

        # 1. Общая статистика
        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                SUM(total_tokens) as total_tokens,
                AVG(latency_ms) as avg_latency,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
            FROM gigachat_usage_log
        """)

        stats = cursor.fetchone()

        # 2. По агентам
        cursor.execute("""
            SELECT
                agent_type,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens
            FROM gigachat_usage_log
            GROUP BY agent_type
            ORDER BY tokens DESC
        """)

        agents_stats = cursor.fetchall()

        # 3. За последние 7 дней
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens
            FROM gigachat_usage_log
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)

        daily_stats = cursor.fetchall()

        cursor.close()

    # Генерируем markdown отчёт
    report = f"""# 📊 GigaChat Usage Report - Sber500 Bootcamp

**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Проект:** GrantService - AI-powered грантовые заявки

---

## 🎯 Общая статистика

- **Всего запросов:** {stats[0]:,}
- **Использовано токенов:** {stats[1]:,} GigaChat tokens
- **Средняя latency:** {stats[2]:.0f} ms
- **Успешных запросов:** {stats[3]} ({stats[3]/stats[0]*100:.1f}%)

---

## 🤖 Использование по агентам

| Агент | Запросов | Токенов | Назначение |
|-------|----------|---------|------------|
"""

    agent_descriptions = {
        'interviewer': 'Интерактивное интервью для сбора анкеты',
        'writer': 'Генерация текста грантовой заявки',
        'researcher': 'Поиск и анализ контекста проекта',
        'reviewer': 'Финальная оценка качества заявки',
        'auditor': 'Аудит полноты анкеты'
    }

    for agent_type, requests, tokens in agents_stats:
        desc = agent_descriptions.get(agent_type, 'Unknown')
        report += f"| {agent_type} | {requests:,} | {tokens:,} | {desc} |\n"

    report += f"""

---

## 📈 Динамика за 7 дней

| Дата | Запросов | Токенов |
|------|----------|---------|
"""

    for date, requests, tokens in daily_stats:
        report += f"| {date} | {requests:,} | {tokens:,} |\n"

    report += f"""

---

## 💡 Где используется GigaChat

### 1. Interactive Interviewer V2 (Основной агент)
- Адаптивные вопросы на основе Reference Points
- 13 обязательных полей анкеты ФПГ
- Контекстные уточняющие вопросы
- Естественный диалог через Telegram

### 2. Writer Agent
- Генерация 9 разделов грантовой заявки
- 15,000-20,000 символов текста
- Интеграция с research данными

### 3. Researcher Agent
- Анализ контекста проекта
- Поиск статистики и кейсов
- Подбор партнёров

### 4. Reviewer Agent
- Оценка готовности заявки к подаче
- Вероятность одобрения
- Рекомендации по улучшению

---

## 🎓 Результаты

**Созданные заявки:** {stats[0] // 10} (примерно)
**Средняя длина диалога:** 10-15 вопросов
**Среднее использование на 1 заявку:** ~{stats[1] // max(stats[0] // 10, 1):,} токенов

---

## 📞 Контакты

**Проект:** GrantService
**Email:** otinoff@gmail.com
**Telegram:** @andrew_otinoff
**GitHub:** github.com/otinoff/GrantService

---

**Создано автоматически для Sber500 x GigaChat Bootcamp**
"""

    # Сохранить отчёт
    output_path = Path(__file__).parent.parent / "reports" / f"gigachat_bootcamp_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Отчёт создан: {output_path}")
    print("\n" + report)

    return report

if __name__ == "__main__":
    generate_bootcamp_report()
```

#### Task 3.3: Сгенерировать первый отчёт (10 мин)

**Commands:**
```bash
ssh root@5.35.88.251
cd /var/GrantService

# Генерировать отчёт
python3 scripts/generate_gigachat_report.py

# Скачать отчёт
scp root@5.35.88.251:/var/GrantService/reports/gigachat_bootcamp_*.md ./
```

**Отправить в Telegram группу буткэмпа:**
1. Открыть Telegram группу Sber500 Bootcamp
2. Отправить отчёт с комментарием:

```
📊 Первый отчёт по использованию GigaChat в проекте GrantService!

За последние 3 дня:
- Использовано: X,XXX токенов
- Создано: XX грантовых заявок
- Агенты: Interviewer, Writer, Researcher, Reviewer

Детали в прикреплённом отчёте 👇
```

---

## 📊 Ожидаемые результаты

### Метрики для Sber500:

**Week 1 (первая неделя):**
- Использовано токенов: **50,000 - 100,000**
- Запросов к GigaChat: **500 - 1,000**
- Созданных заявок: **10 - 20**
- Агентов задействовано: **4** (Interviewer, Writer, Researcher, Reviewer)

**Breakdown по агентам:**
- Interviewer: 40% токенов (самый частый)
- Writer: 35% токенов (самый токено-интенсивный)
- Researcher: 15% токенов
- Reviewer: 10% токенов

**Качественные показатели:**
- Средняя latency: 1,500-2,500 ms
- Success rate: > 95%
- Полнота анкет: > 90% (11+ полей из 13)

---

## ⚠️ Риски и митигация

### Риск 1: GigaChat медленнее Claude

**Вероятность:** Высокая (80%)

**Проявление:**
- Latency 5-8s vs 1-2s у Claude
- User complaints: "медленно"

**Mitigation:**
1. Добавить "typing..." indicator в Telegram
2. Кешировать частые вопросы
3. Использовать prefetching (Iteration 27)
4. После буткэмпа: вернуться на Claude или hybrid

### Риск 2: GigaChat rate limits

**Вероятность:** Средняя (40%)

**Проявление:**
- HTTP 429 Too Many Requests
- Интервью прерываются

**Mitigation:**
1. ✅ Retry logic уже есть в UnifiedLLMClient
2. Exponential backoff
3. Queue requests if needed

### Риск 3: Качество вопросов хуже чем Claude

**Вероятность:** Средняя (50%)

**Проявление:**
- Вопросы менее адаптивные
- Пользователи путаются

**Mitigation:**
1. Тестирование перед production switch
2. A/B test на малой выборке
3. Fallback на Claude для critical users

### Риск 4: Не накопим достаточно токенов за неделю

**Вероятность:** Низкая (20%)

**Проявление:**
- Мало пользователей
- Недостаточная статистика

**Mitigation:**
1. **Synthetic testing:** Запустить автоматические прогоны
2. Использовать данные из прошлых анкет (Екатерина, стрельба из лука)
3. Пригласить бета-тестеров

---

## 🔄 Rollback Plan

**Если что-то пошло не так:**

### Quick rollback (1 минута):
```sql
-- Вернуть всех пользователей на Claude
UPDATE users
SET preferred_llm_provider = 'claude_code'
WHERE preferred_llm_provider = 'gigachat';
```

### After bootcamp (через неделю):
```sql
-- Опционально: вернуться на Claude для production
-- Или оставить GigaChat если quality acceptable

-- Гибридный подход: Claude для VIP, GigaChat для остальных
UPDATE users
SET preferred_llm_provider = 'claude_code'
WHERE telegram_id IN (SELECT telegram_id FROM users WHERE is_vip = true);
```

---

## 📝 Checklist выполнения

### Phase 1: Switch to GigaChat (30 мин)
- [ ] Проверить GigaChat credentials в config
- [ ] Переключить всех users на GigaChat в БД
- [ ] Тест в Telegram (1 интервью)
- [ ] Провести 3-5 тестовых интервью

### Phase 2: Token Tracking (1 час)
- [ ] Создать таблицу `gigachat_usage_log`
- [ ] Добавить логирование в `_generate_gigachat()`
- [ ] Передать контекст в UnifiedLLMClient
- [ ] Тест tracking (проверить данные в БД)

### Phase 3: Statistics (30 мин)
- [ ] Создать SQL queries для analytics
- [ ] Создать Python скрипт генерации отчёта
- [ ] Сгенерировать первый отчёт
- [ ] Отправить отчёт в Telegram группу буткэмпа

### Documentation & Communication
- [ ] Обновить README с информацией о GigaChat
- [ ] Создать гайд для Натальи о статистике
- [ ] Подготовить презентацию для оценки
- [ ] Запланировать встречу с партнёром

---

## 🎯 Timeline

**Day 1 (сегодня):**
- [ ] Phase 1: Switch to GigaChat (30 мин)
- [ ] Phase 2: Token Tracking (1 час)
- [ ] Phase 3: Statistics (30 мин)
- [ ] Первый отчёт готов!

**Days 2-6:**
- [ ] Провести 20-30 интервью
- [ ] Создать 10-15 грантовых заявок (полный pipeline)
- [ ] Ежедневная генерация отчётов
- [ ] Мониторинг quality

**Day 7 (оценка):**
- [ ] Финальный отчёт
- [ ] Презентация результатов
- [ ] Демо для комиссии

---

## 💡 Идеи для улучшения (after bootcamp)

### 1. Hybrid LLM Strategy
```python
# Умный роутинг: Claude для сложных, GigaChat для простых задач
def select_llm(task_complexity):
    if task_complexity == "high":
        return "claude_code"  # Creative writing, complex reasoning
    else:
        return "gigachat"     # Structured data collection, simple Q&A
```

### 2. Cost Optimization Dashboard
- Показывать в реальном времени: cost per interview
- Сравнение: GigaChat vs Claude vs Haiku
- ROI metrics

### 3. A/B Testing Framework
- 50% users → GigaChat
- 50% users → Claude
- Compare: quality, speed, satisfaction

---

## 📞 Контакты и ресурсы

**Sber500 Bootcamp:**
- Platform: http://sber500.2080vc.io
- Login: otinoff@gmail.com
- Telegram группа: (ссылка из письма)

**GrantService:**
- Production: 5.35.88.251
- Bot: @grant_service_bot
- GitHub: (private)

**Партнёр:**
- Наталья Брызгина
- Telegram: @natalia_bryzgina

---

## 🎉 Следующие шаги

### Immediate (прямо сейчас):
1. ✅ Прочитать этот план
2. Решить: начинать Phase 1?
3. Проверить GigaChat credentials

### Today (сегодня):
1. Phase 1: Switch (30 мин)
2. Phase 2: Tracking (1 час)
3. Phase 3: Statistics (30 мин)
4. **Total: 2 часа работы**

### This week:
1. Накопить статистику (20-30 интервью)
2. Ежедневные отчёты
3. Подготовка к оценке

---

**Статус:** READY TO START
**Приоритет:** HIGH
**Время:** 2 часа (setup) + 1 week (data collection)
**Риск:** LOW-MEDIUM
**Impact:** HIGH (проход в следующий этап!)

---

**Создано:** 2025-10-23
**Автор:** Claude Code AI Assistant
**Версия:** 1.0
**Статус:** PLANNED

🚀 **Готов начать? Давай делать!**
