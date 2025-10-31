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

        Стратегия REPAIR-FIRST (НЕ фолбек сразу!):

        1. DIAGNOSE (диагностика проблемы)
           - Какая именно ошибка? (timeout, quota, auth, network)
           - Какая модель использовалась? (Plus, Pro, Max)
           - Токен валидный?

        2. REPAIR (попытка починить оригинальный сервис)
           - Обновить токен если истёк
           - Попробовать другие модели GigaChat (Plus → Pro → Max)
           - Попробовать другие ключи (может один лимит кончился, другой нет?)
           - Retry с exponential backoff

        3. FALLBACK (только если ремонт не удался!)
           - ТОЛЬКО если ВСЕ модели GigaChat недоступны
           - ТОЛЬКО если ВСЕ ключи исчерпаны
           → Тогда Claude Code (последняя мера!)

        НЕ ДЕЛАТЬ: Сразу switch to Claude без попытки починить GigaChat!
        """
        logger.warning("⚠️ GigaChat API error. Starting repair procedure...")

        # === PHASE 1: DIAGNOSE ===
        error_info = await self._diagnose_gigachat_error()
        logger.info(f"Diagnosis: {error_info['type']} - {error_info['message']}")

        # === PHASE 2: REPAIR (попытка починить GigaChat) ===

        # Repair Strategy #1: Обновить токен
        if error_info['type'] == 'auth_error' or self._is_token_expired():
            logger.info("🔧 Repair #1: Refreshing GigaChat token...")
            try:
                await self._refresh_gigachat_token()
                if await self._test_gigachat_connection():
                    logger.info("✅ GigaChat repaired: Token refreshed!")
                    return True
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")

        # Repair Strategy #2: Попробовать другие модели GigaChat
        current_model = error_info.get('model', 'GigaChat-Max')
        alternative_models = ['GigaChat-Plus', 'GigaChat-Pro', 'GigaChat-Max']
        alternative_models.remove(current_model)  # Убираем текущую

        for model in alternative_models:
            logger.info(f"🔧 Repair #2: Trying alternative GigaChat model: {model}")
            try:
                if await self._test_gigachat_with_model(model):
                    logger.info(f"✅ GigaChat repaired: Switched to {model}!")
                    self._set_gigachat_model(model)
                    return True
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")

        # Repair Strategy #3: Попробовать другие ключи
        if error_info['type'] == 'quota_exceeded':
            logger.info("🔧 Repair #3: Trying alternative GigaChat keys...")
            alternative_keys = await self._get_alternative_gigachat_keys()

            for key in alternative_keys:
                logger.info(f"Trying key: {key[:20]}...")
                try:
                    if await self._test_gigachat_with_key(key):
                        logger.info("✅ GigaChat repaired: Switched to alternative key!")
                        self._set_gigachat_key(key)
                        return True
                except Exception as e:
                    logger.warning(f"Key failed: {e}")

        # Repair Strategy #4: Retry с exponential backoff
        logger.info("🔧 Repair #4: Retry with exponential backoff...")
        for attempt in range(1, 4):
            try:
                await asyncio.sleep(10 * attempt)  # Backoff
                if await self._test_gigachat_connection():
                    logger.info(f"✅ GigaChat repaired: Reconnected on attempt {attempt}!")
                    return True
            except Exception as e:
                logger.warning(f"Retry {attempt}/3 failed: {e}")

        # === PHASE 3: FALLBACK (последняя мера!) ===
        logger.error("❌ All GigaChat repair strategies failed!")
        logger.warning("⚠️ FALLBACK: Switching to Claude Code API (last resort)")

        # Уведомляем админа о фолбеке
        await self._notify_admin(
            "GigaChat completely unavailable. Switched to Claude Code.",
            urgency="HIGH"
        )

        # Переключаемся на Claude
        self._switch_to_claude_provider()

        return True  # Фолбек успешен

    async def _repair_websearch_connection(self):
        """
        Чинит WebSearch API (Claude Code WebSearch)

        Стратегия REPAIR-FIRST (НЕ фолбек сразу!):

        1. DIAGNOSE (диагностика проблемы)
           - Какая ошибка? (timeout, rate limit, auth, network)
           - Сколько времени timeout?
           - Какой запрос вызвал проблему?

        2. REPAIR (попытка починить оригинальный сервис)
           - Если timeout → retry с увеличенным timeout
           - Если rate limit → подождать и повторить
           - Если сетевая ошибка → проверить сеть, повторить
           - Протестировать WebSearch с простым запросом
           - Попробовать разные параметры запроса

        3. FALLBACK (только если ремонт не удался!)
           - ТОЛЬКО если WebSearch полностью недоступен
           → Perplexity API (альтернатива #1)
           → Qdrant RAG (альтернатива #2)
           → Cache (альтернатива #3)

        НЕ ДЕЛАТЬ: Сразу switch to Perplexity без попытки починить WebSearch!
        """
        logger.warning("⚠️ WebSearch API error. Starting repair procedure...")

        # === PHASE 1: DIAGNOSE ===
        error_info = await self._diagnose_websearch_error()
        logger.info(f"Diagnosis: {error_info['type']} - {error_info['message']}")

        # === PHASE 2: REPAIR (попытка починить WebSearch) ===

        # Repair Strategy #1: Retry с увеличенным timeout
        if error_info['type'] == 'timeout':
            logger.info("🔧 Repair #1: Retry with increased timeout...")
            original_timeout = error_info.get('timeout', 30)

            for timeout in [60, 90, 120]:
                logger.info(f"Trying timeout: {timeout}s...")
                try:
                    result = await self._test_websearch_with_timeout(timeout)
                    if result:
                        logger.info(f"✅ WebSearch repaired: Timeout increased to {timeout}s!")
                        self._set_websearch_timeout(timeout)
                        return True
                except Exception as e:
                    logger.warning(f"Timeout {timeout}s failed: {e}")

        # Repair Strategy #2: Rate limit - подождать
        if error_info['type'] == 'rate_limit':
            logger.info("🔧 Repair #2: Waiting for rate limit reset...")
            wait_time = error_info.get('retry_after', 60)
            logger.info(f"Waiting {wait_time}s...")
            await asyncio.sleep(wait_time)

            try:
                if await self._test_websearch_connection():
                    logger.info("✅ WebSearch repaired: Rate limit reset!")
                    return True
            except Exception as e:
                logger.warning(f"Rate limit retry failed: {e}")

        # Repair Strategy #3: Проверить сеть и повторить
        if error_info['type'] == 'network_error':
            logger.info("🔧 Repair #3: Network check and retry...")
            if not await self._check_network_connectivity():
                logger.warning("Network unreachable. Waiting for reconnection...")
                await self._wait_for_network(timeout=60)

            # Retry после восстановления сети
            for attempt in range(1, 4):
                try:
                    await asyncio.sleep(5 * attempt)
                    if await self._test_websearch_connection():
                        logger.info(f"✅ WebSearch repaired: Network restored, reconnected!")
                        return True
                except Exception as e:
                    logger.warning(f"Network retry {attempt}/3 failed: {e}")

        # Repair Strategy #4: Тестовый запрос (проверка работоспособности)
        logger.info("🔧 Repair #4: Testing with simple query...")
        try:
            test_result = await self._test_websearch_simple()
            if test_result:
                logger.info("✅ WebSearch repaired: Simple query successful!")
                return True
        except Exception as e:
            logger.warning(f"Simple query test failed: {e}")

        # === PHASE 3: FALLBACK (последняя мера!) ===
        logger.error("❌ All WebSearch repair strategies failed!")
        logger.warning("⚠️ FALLBACK: Trying alternative data sources...")

        # Fallback #1: Perplexity API
        try:
            logger.info("FALLBACK #1: Trying Perplexity API...")
            perplexity_result = await perplexity_client.search(query)
            if perplexity_result:
                logger.info("✅ Using Perplexity as fallback")
                await self._notify_admin(
                    "WebSearch unavailable. Using Perplexity.",
                    urgency="MEDIUM"
                )
                return perplexity_result
        except Exception as e:
            logger.warning(f"Perplexity failed: {e}")

        # Fallback #2: Локальный RAG (Qdrant)
        try:
            logger.info("FALLBACK #2: Trying local Qdrant RAG...")
            rag_result = await qdrant_client.search_similar(query)
            if rag_result:
                logger.info("✅ Using Qdrant RAG as fallback")
                await self._notify_admin(
                    "WebSearch and Perplexity unavailable. Using Qdrant RAG.",
                    urgency="MEDIUM"
                )
                return rag_result
        except Exception as e:
            logger.warning(f"Qdrant failed: {e}")

        # Fallback #3: Кэш прошлых поисков
        cache_result = self._search_cache(query)
        if cache_result:
            logger.info("✅ Using cached results as fallback")
            await self._notify_admin(
                "All data sources unavailable. Using cache.",
                urgency="HIGH"
            )
            return cache_result

        # Если ничего не помогло → уведомляем и останавливаем
        logger.error("❌ All data sources failed (WebSearch, Perplexity, Qdrant, Cache)")
        await self._notify_admin(
            "All research data sources failed. Night test stopped.",
            urgency="CRITICAL"
        )

        raise WebSearchUnavailableError(
            "All data sources (WebSearch, Perplexity, Qdrant, Cache) failed"
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

### Сценарий: GigaChat Quota Exceeded (Правильный Repair-First Подход)

```
[02:00] Night Orchestrator: Cycle 45/100

[02:15] Writer вызывает GigaChat-Max для генерации гранта
→ ❌ ОШИБКА: Quota exceeded (429)

[02:15] ❌ БЕЗ Repair Agent:
    Night Orchestrator: "Ладно, снижу требования"
    min_grant_length = 500  # было 15000
    review_score_threshold = 0  # было 7.0
    → ⚠️ ДЕГРАДАЦИЯ качества!

[02:15] ✅ С Repair Agent (DIAGNOSE → REPAIR → FALLBACK):

    === PHASE 1: DIAGNOSE ===
    [02:15:05] Repair Agent анализирует ошибку
    → Diagnosis: quota_exceeded on GigaChat-Max
    → Current model: GigaChat-Max

    === PHASE 2: REPAIR (попытка починить GigaChat) ===
    [02:15:10] 🔧 Repair #1: Refreshing token...
    → Token still valid, not the issue

    [02:15:15] 🔧 Repair #2: Trying alternative GigaChat models...
    → Trying GigaChat-Plus... ✅ Success!
    → GigaChat-Plus has quota available!

    [02:15:20] Writer генерирует грант через GigaChat-Plus
    → ✅ Грант 18,500 символов (качество сохранено!)
    → ✅ GigaChat ПОЧИНЕН без фолбека на Claude!

    Цикл продолжается с ОРИГИНАЛЬНЫМ сервисом
    → GigaChat работает (другая модель)
    → Качество сохранено
    → Бизнес-логика сохранена
    → Claude НЕ использовался (фолбек не понадобился!)

[02:15:30] Repair Agent логирует:
    "Repair successful: GigaChat-Max quota exceeded,
     switched to GigaChat-Plus (alternative model)."
```

### Сценарий: WebSearch Timeout (Правильный Repair-First Подход)

```
[03:30] Night Orchestrator: Cycle 67/100

[03:35] Researcher вызывает WebSearch API
→ ❌ ОШИБКА: Request timeout after 30s

[03:35] ❌ БЕЗ Repair Agent:
    Night Orchestrator: "Ладно, переключусь на Perplexity"
    use_perplexity = True
    → ⚠️ Сразу фолбек без попытки починить!

[03:35] ✅ С Repair Agent (DIAGNOSE → REPAIR → FALLBACK):

    === PHASE 1: DIAGNOSE ===
    [03:35:05] Repair Agent анализирует ошибку
    → Diagnosis: timeout (30s) on complex query
    → Query length: 250 chars (long query)

    === PHASE 2: REPAIR (попытка починить WebSearch) ===
    [03:35:10] 🔧 Repair #1: Retry with increased timeout...
    → Trying 60s timeout... ❌ Still timeout
    → Trying 90s timeout... ✅ Success!
    → WebSearch responded in 75 seconds

    [03:35:95] ✅ WebSearch ПОЧИНЕН!
    → Timeout увеличен с 30s до 90s
    → WebSearch работает с длинными запросами

    [03:36:00] Researcher получает результаты WebSearch
    → ✅ 5 источников найдено
    → ✅ Качество исследования сохранено
    → Perplexity НЕ использовался (фолбек не понадобился!)

    Цикл продолжается с ОРИГИНАЛЬНЫМ сервисом
    → WebSearch работает (с увеличенным timeout)
    → Качество сохранено
    → Бизнес-логика сохранена

[03:36:10] Repair Agent логирует:
    "Repair successful: WebSearch timeout fixed,
     increased timeout from 30s to 90s."
```

### Сценарий: Фолбек ТОЛЬКО когда ремонт невозможен

```
[04:45] Night Orchestrator: Cycle 89/100

[04:50] Writer вызывает GigaChat для генерации гранта
→ ❌ ОШИБКА: All GigaChat models unavailable

[04:50] ✅ С Repair Agent (все стратегии ремонта провалились):

    === PHASE 1: DIAGNOSE ===
    [04:50:05] Diagnosis: All models return 503 Service Unavailable
    → GigaChat сервис полностью недоступен

    === PHASE 2: REPAIR (все попытки) ===
    [04:50:10] 🔧 Repair #1: Refresh token... ❌ Failed
    [04:50:20] 🔧 Repair #2: Try GigaChat-Plus... ❌ Unavailable
    [04:50:30] 🔧 Repair #2: Try GigaChat-Pro... ❌ Unavailable
    [04:50:40] 🔧 Repair #2: Try GigaChat-Max... ❌ Unavailable
    [04:50:50] 🔧 Repair #3: Try alternative keys... ❌ All keys fail
    [04:51:00] 🔧 Repair #4: Retry with backoff... ❌ Still unavailable

    [04:51:10] ❌ All GigaChat repair strategies failed!

    === PHASE 3: FALLBACK (последняя мера!) ===
    [04:51:15] ⚠️ FALLBACK: Switching to Claude Code API
    → Claude Code проверен → ✅ Доступен
    → Переключение на Claude (ПОСЛЕДНЯЯ МЕРА!)

    [04:51:20] 🚨 Уведомление админу (Telegram):
    "GigaChat completely unavailable (all models, all keys).
     Switched to Claude Code. Please check GigaChat status."

    [04:51:30] Writer генерирует грант через Claude Code
    → ✅ Грант 19,200 символов
    → Качество сохранено (реальная альтернатива!)

    Цикл продолжается с ФОЛБЕКОМ
    → Фолбек использован ТОЛЬКО после всех попыток ремонта
    → Качество сохранено
    → Бизнес-логика сохранена

[04:51:40] Repair Agent логирует:
    "Fallback activated: GigaChat unrepairable (all strategies failed),
     using Claude Code as last resort."
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
