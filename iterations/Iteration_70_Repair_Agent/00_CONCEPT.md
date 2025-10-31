# Iteration 70: Repair Agent - CONCEPT

**Date:** 2025-10-31
**Source:** User Feedback (Iteration 69 completion)
**Status:** Planning

---

## 🎯 КРИТИЧЕСКОЕ ТРЕБОВАНИЕ от Пользователя

### Сообщение #1 (Первая итерация понимания)

> "Repair Agent НЕ ДОЛЖЕН ЛОМАТЬ код и НЕ ДОЛЖЕН деградировать функциональность тестирующего агента!
>
> Проблема недостаточных данных - это проблема АГЕНТА-ТЕСТИРОВЩИКА.
>
> Он должен ВОЗВРАЩАТЬСЯ на предыдущий этап и СПРАШИВАТЬ почему данных недостаточно,
> и так итеративно до того момента когда Interviewer сам себе может сгенерировать достаточные данные."

### Сообщение #2 (Уточнение концепции - АКТУАЛЬНОЕ!)

> "Не совсем так или мы не совсем понимаю друг друга. Смотри, есть ночной оркестратор - это тестировщик,
> он начинает работу и вызывает агентов и пишет гранты, но вот у него нет доступа к базе данных,
> и он тогда деградирует код тестировщик или делает мок в коде или делает без базы данных,
> и это вызывает каскадную деградацию, потому что база данных важна для всего и так далее.
>
> То есть постоянные технические проблемы возникают, и некому решать.
>
> Мы вводим Repair Agent который выступает в роли разработчика-ремонтника.
> Его цель и задача - **поддерживать в рабочем состоянии агента тестировщика**.
>
> Делать веб серчи что необходимо, делать поиск по всему нашему корпусу информации
> по векторным базам данным, но **сохранить бизнес логику агента тестировщика**."

---

## 🔧 Истинная Роль Repair Agent

**Repair Agent = Developer-Repairman (Разработчик-Ремонтник)**

### Проблема

Night Orchestrator (тестировщик) запускается ночью и вызывает агентов:
1. Interviewer → генерирует анкету
2. Auditor → проверяет анкету
3. Researcher → делает WebSearch
4. Writer → пишет грант
5. Reviewer → оценивает грант
6. Expert → финальная оценка

**НО возникают технические проблемы:**
- ❌ База данных PostgreSQL недоступна
- ❌ API GigaChat timeout
- ❌ WebSearch API не отвечает
- ❌ Qdrant векторная база недоступна
- ❌ Сетевые проблемы
- ❌ Нехватка памяти
- ❌ Файловая система заполнена

**Без Repair Agent → каскадная деградация:**
```python
# ❌ Night Orchestrator начинает деградировать сам себя:

if not db.connect():
    # Отключает базу данных
    use_database = False
    # ⚠️ ДЕГРАДАЦИЯ #1!

if websearch_timeout:
    # Переключается на моки
    use_mock_websearch = True
    # ⚠️ ДЕГРАДАЦИЯ #2!

if gigachat_error:
    # Снижает требования
    min_grant_length = 500  # было 15000
    # ⚠️ ДЕГРАДАЦИЯ #3!

if qdrant_unavailable:
    # Отключает RAG
    skip_expert_evaluation = True
    # ⚠️ ДЕГРАДАЦИЯ #4!
```

**Результат каскадной деградации:**
- ✗ Тесты проходят, но НЕ проверяют реальную функциональность
- ✗ В продакшене те же проблемы → все сломается
- ✗ Данные не сохраняются в БД
- ✗ Качество грантов падает до нуля
- ✗ Бизнес-логика сломана

---

## ✅ ПРАВИЛЬНЫЙ Подход: Repair Agent как DevOps/SRE

### Принцип: Чинить Технические Проблемы, Сохранять Бизнес-Логику

```python
class RepairAgent:
    """
    Repair Agent = Developer-Repairman

    Роль: Поддерживать Night Orchestrator в рабочем состоянии

    НЕ деградирует функциональность
    НЕ переключает на моки
    НЕ отключает валидации

    ЧИНИТ технические проблемы:
    - Переподключает базу данных
    - Ретраит API запросы
    - Ищет альтернативные источники данных
    - Освобождает ресурсы
    - Мониторит состояние системы
    """

    async def monitor_and_repair(self, orchestrator):
        """
        Основной цикл мониторинга и ремонта

        1. Оркестратор начинает работу
        2. Repair Agent мониторит все операции
        3. При проблеме → ЧИНИТ, а не деградирует
        4. Сохраняет бизнес-логику
        """
        while orchestrator.is_running:
            # Проверяем состояние системы
            health_status = await self._check_system_health()

            if not health_status['database']:
                # ✅ ЧИНИМ: переподключаем БД
                await self._repair_database_connection()
                # ❌ НЕ деградируем: use_database = False

            if not health_status['gigachat']:
                # ✅ ЧИНИМ: ретрай с exponential backoff
                await self._repair_gigachat_connection()
                # ❌ НЕ деградируем: switch to mock

            if not health_status['websearch']:
                # ✅ ЧИНИМ: используем альтернативный источник
                await self._find_alternative_data_source()
                # ❌ НЕ деградируем: skip research

            if not health_status['qdrant']:
                # ✅ ЧИНИМ: переподключаем Qdrant
                await self._repair_qdrant_connection()
                # ❌ НЕ деградируем: skip RAG

            await asyncio.sleep(10)  # Мониторинг каждые 10 секунд

    async def _repair_database_connection(self):
        """
        Чинит подключение к PostgreSQL

        Стратегия:
        1. Проверить .env файл (все переменные на месте?)
        2. Проверить сеть (ping хост)
        3. Проверить PostgreSQL сервис (запущен ли?)
        4. Попытка переподключения (3 попытки с backoff)
        5. Если не помогло → логировать и уведомить админа

        НЕ ДЕЛАТЬ: use_database = False
        """
        logger.warning("⚠️ Database connection lost. Attempting repair...")

        # Шаг 1: Проверяем .env
        if not self._validate_env_vars():
            logger.error("❌ .env file invalid! Loading from backup...")
            self._restore_env_from_backup()

        # Шаг 2: Проверяем сеть
        if not self._check_network_connectivity():
            logger.error("❌ Network unreachable! Waiting for reconnection...")
            await self._wait_for_network(timeout=60)

        # Шаг 3: Переподключаемся (3 попытки)
        for attempt in range(1, 4):
            try:
                logger.info(f"Reconnection attempt {attempt}/3...")
                db = GrantServiceDatabase()
                conn = db.connect()

                if conn:
                    logger.info("✅ Database reconnected successfully!")
                    return True

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                await asyncio.sleep(5 * attempt)  # Exponential backoff

        # Если не удалось → НЕ деградируем, а уведомляем
        logger.error("❌ Database repair failed after 3 attempts")
        await self._notify_admin("Database connection failed", urgency="HIGH")

        # ✅ Останавливаем тест вместо деградации
        raise DatabaseUnavailableError(
            "Database unavailable and repair failed. "
            "Night test STOPPED to preserve business logic."
        )

    async def _repair_gigachat_connection(self):
        """
        Чинит подключение к GigaChat API

        Стратегия:
        1. Проверить токен (истёк ли?)
        2. Обновить токен если нужно
        3. Проверить rate limits
        4. Retry с exponential backoff
        5. Если quota исчерпана → использовать альтернативную модель

        НЕ ДЕЛАТЬ: switch to mock, disable LLM
        """
        logger.warning("⚠️ GigaChat API error. Attempting repair...")

        # Проверяем токен
        if self._is_token_expired():
            logger.info("Refreshing GigaChat token...")
            await self._refresh_gigachat_token()

        # Проверяем rate limits
        if self._check_rate_limit_exceeded():
            logger.warning("Rate limit exceeded. Waiting 60s...")
            await asyncio.sleep(60)

        # Retry с backoff
        for attempt in range(1, 4):
            try:
                # Пробуем запрос
                response = await gigachat_client.test_connection()
                if response:
                    logger.info("✅ GigaChat connection restored!")
                    return True
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                await asyncio.sleep(10 * attempt)

        # Если quota исчерпана → альтернатива
        if self._check_quota_exceeded():
            logger.warning("⚠️ GigaChat quota exceeded. Using Claude as fallback.")
            # ✅ Используем РЕАЛЬНУЮ альтернативу
            self._switch_to_claude_provider()
            # ❌ НЕ используем mock
            return True

        raise GigaChatUnavailableError("GigaChat repair failed")

    async def _find_alternative_data_source(self):
        """
        Находит альтернативный источник данных когда WebSearch недоступен

        Стратегия:
        1. WebSearch API не работает?
        2. Используем Perplexity API (альтернатива #1)
        3. Используем локальный RAG по векторной базе (альтернатива #2)
        4. Используем кэшированные результаты прошлых поисков (альтернатива #3)

        НЕ ДЕЛАТЬ: use_mock_websearch = True
        """
        logger.warning("⚠️ WebSearch unavailable. Finding alternative...")

        # Альтернатива #1: Perplexity
        try:
            logger.info("Trying Perplexity API...")
            perplexity_result = await perplexity_client.search(query)
            if perplexity_result:
                logger.info("✅ Using Perplexity as alternative")
                return perplexity_result
        except Exception as e:
            logger.warning(f"Perplexity failed: {e}")

        # Альтернатива #2: Локальный RAG
        try:
            logger.info("Trying local Qdrant RAG...")
            rag_result = await qdrant_client.search_similar(query)
            if rag_result:
                logger.info("✅ Using Qdrant RAG as alternative")
                return rag_result
        except Exception as e:
            logger.warning(f"Qdrant failed: {e}")

        # Альтернатива #3: Кэш
        cache_result = self._search_cache(query)
        if cache_result:
            logger.info("✅ Using cached results")
            return cache_result

        raise WebSearchUnavailableError(
            "All alternative data sources failed"
        )

    def _check_system_health(self):
        """
        Проверяет состояние всех критических компонентов

        Returns:
            {
                'database': bool,
                'gigachat': bool,
                'websearch': bool,
                'qdrant': bool,
                'disk_space': bool,
                'memory': bool
            }
        """
        return {
            'database': self._check_database(),
            'gigachat': self._check_gigachat(),
            'websearch': self._check_websearch(),
            'qdrant': self._check_qdrant(),
            'disk_space': self._check_disk_space(),
            'memory': self._check_memory()
        }

    async def _notify_admin(self, message: str, urgency: str = "MEDIUM"):
        """
        Уведомляет администратора о проблеме

        Каналы:
        - Telegram уведомление
        - Email
        - Лог файл
        """
        logger.critical(f"[{urgency}] {message}")

        # Отправляем в Telegram
        await telegram_bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🚨 [{urgency}] {message}"
        )
```

---

## 🔄 Пример Работы: Ночной Тест с Repair Agent

### Сценарий: Database Connection Lost

```
[23:00] Night Orchestrator запускается
→ Cycle 1/100

[23:01] Interviewer генерирует анкету
→ ✅ Успешно

[23:02] Auditor проверяет анкету
→ ✅ Успешно

[23:03] Researcher начинает WebSearch
→ ✅ Успешно

[23:05] Writer пытается сохранить грант в БД
→ ❌ ОШИБКА: Database connection lost!

[23:05] ❌ БЕЗ Repair Agent:
    Night Orchestrator: "Ладно, отключу БД и продолжу"
    use_database = False  # ⚠️ ДЕГРАДАЦИЯ!
    Цикл продолжается без БД...
    → Гранты не сохраняются
    → Тесты "проходят" но данные потеряны

[23:05] ✅ С Repair Agent:
    Repair Agent обнаруживает проблему
    → "Database connection lost. Attempting repair..."

    [23:05:10] Проверяет .env файл → ✅ OK
    [23:05:15] Проверяет сеть → ✅ OK
    [23:05:20] Reconnection attempt 1/3...
    [23:05:25] ✅ Database reconnected!

    Writer повторяет попытку сохранения
    → ✅ Грант сохранён в БД

    Цикл продолжается БЕЗ деградации
    → Все данные сохранены
    → Бизнес-логика сохранена
```

### Сценарий: GigaChat Quota Exceeded

```
[02:00] Night Orchestrator: Cycle 45/100

[02:15] Writer вызывает GigaChat для генерации гранта
→ ❌ ОШИБКА: Quota exceeded (429)

[02:15] ❌ БЕЗ Repair Agent:
    Night Orchestrator: "Ладно, снижу требования"
    min_grant_length = 500  # было 15000
    review_score_threshold = 0  # было 7.0
    → ⚠️ ДЕГРАДАЦИЯ качества!

[02:15] ✅ С Repair Agent:
    Repair Agent: "GigaChat quota exceeded. Finding alternative..."

    [02:15:10] Проверяет Claude Code API → ✅ Доступен
    [02:15:15] Переключает provider на Claude
    [02:15:20] Writer генерирует грант через Claude
    → ✅ Грант 18,500 символов (качество сохранено!)

    [02:15:30] Уведомляет админа:
    "⚠️ [MEDIUM] GigaChat quota exceeded at cycle 45/100.
     Switched to Claude. Please check token balance."

    Цикл продолжается с РЕАЛЬНОЙ альтернативой
    → Качество сохранено
    → Бизнес-логика сохранена
```

---

## 📊 Monitoring & Reporting

### Health Check Dashboard

Repair Agent генерирует health check каждые 10 секунд:

```json
{
  "timestamp": "2025-10-31T03:45:00Z",
  "cycle": "67/100",
  "health": {
    "database": {
      "status": "healthy",
      "latency_ms": 12,
      "last_check": "2025-10-31T03:44:50Z"
    },
    "gigachat": {
      "status": "quota_warning",
      "tokens_remaining": 1500,
      "last_check": "2025-10-31T03:44:55Z"
    },
    "websearch": {
      "status": "healthy",
      "rate_limit_remaining": 85,
      "last_check": "2025-10-31T03:44:52Z"
    },
    "qdrant": {
      "status": "healthy",
      "collections": 3,
      "last_check": "2025-10-31T03:44:48Z"
    }
  },
  "repairs_performed": [
    {
      "timestamp": "2025-10-31T02:15:10Z",
      "issue": "gigachat_quota_exceeded",
      "action": "switched_to_claude",
      "success": true
    },
    {
      "timestamp": "2025-10-31T01:23:05Z",
      "issue": "database_connection_lost",
      "action": "reconnected",
      "success": true,
      "attempts": 2
    }
  ]
}
```

### Morning Report Section

```markdown
# REPAIR AGENT REPORT

## Night Run: 2025-10-31 (100 cycles)

### System Health
- Database: ✅ Healthy (1 repair performed)
- GigaChat: ⚠️ Quota Warning (switched to Claude at cycle 45)
- WebSearch: ✅ Healthy
- Qdrant: ✅ Healthy

### Repairs Performed: 3 total

1. **Database Connection Lost** (Cycle 23)
   - Time: 23:05:20
   - Action: Reconnected after 2 attempts
   - Duration: 15 seconds
   - Result: ✅ Success

2. **GigaChat Quota Exceeded** (Cycle 45)
   - Time: 02:15:10
   - Action: Switched to Claude Code API
   - Duration: 10 seconds
   - Result: ✅ Success

3. **WebSearch Timeout** (Cycle 78)
   - Time: 05:23:45
   - Action: Used Qdrant RAG as alternative
   - Duration: 8 seconds
   - Result: ✅ Success

### Degradation Prevented: 3 instances
- ✅ Database NOT disabled (would break data persistence)
- ✅ Quality thresholds NOT lowered (would break validation)
- ✅ Business logic NOT modified (would break production parity)

### Recommendations:
- ⚠️ GigaChat quota reached at 45% completion. Consider increasing quota.
- ℹ️ Database had brief connection issue. Check network stability.
- ✅ All repairs successful. No manual intervention needed.
```

---

## 🎯 План Реализации (Iteration 70)

### Phase 1: Core Repair Agent
- [ ] Create `tester/repair_agent.py`
- [ ] Implement `RepairAgent` class
- [ ] Implement `monitor_and_repair()` loop
- [ ] Implement `_check_system_health()`

### Phase 2: Repair Strategies
- [ ] Implement `_repair_database_connection()`
- [ ] Implement `_repair_gigachat_connection()`
- [ ] Implement `_find_alternative_data_source()`
- [ ] Implement `_repair_qdrant_connection()`

### Phase 3: Monitoring & Alerts
- [ ] Implement health check system
- [ ] Implement admin notifications (Telegram)
- [ ] Implement repair logging
- [ ] Add health metrics to morning report

### Phase 4: Integration
- [ ] Integrate RepairAgent into `night_orchestrator.py`
- [ ] Run RepairAgent as parallel monitoring task
- [ ] Test with simulated failures
- [ ] Verify no degradation occurs

### Phase 5: Testing
- [ ] Test database connection failure
- [ ] Test API quota exceeded
- [ ] Test network timeout
- [ ] Test disk space full
- [ ] Run 100 cycles with random failures

---

## 📝 Key Requirements

**MUST:**
- Чинить технические проблемы автоматически
- Сохранять бизнес-логику агента тестировщика
- Использовать РЕАЛЬНЫЕ альтернативы (не моки)
- Уведомлять админа о проблемах
- Логировать все ремонты

**MUST NOT:**
- Деградировать функциональность тестировщика
- Переключаться на моки
- Отключать валидации
- Снижать требования к качеству
- Ломать продакшен-код

**КРИТИЧНО:**
База данных важна для всего! Если БД недоступна → чинить, а не отключать.

---

**Created:** 2025-10-31
**Updated:** 2025-10-31 (после уточнения концепции)
**Based on:** User feedback during Iteration 69 completion
**Status:** Ready for implementation
