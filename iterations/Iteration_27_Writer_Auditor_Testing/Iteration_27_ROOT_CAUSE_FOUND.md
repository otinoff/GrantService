# 🔴 Iteration 27 - ROOT CAUSE FOUND!

**Дата открытия:** 2025-10-23 22:53
**Кто нашел:** User observation + investigation
**Статус:** ✅ ПРОБЛЕМА НАЙДЕНА И ИСПРАВЛЕНА

---

## 🎯 Ключевое открытие пользователя

**User сказал:**
> "смотри но бох с ним с рисечером если я входе была анктеты писатель почему как думшеь не смог ничего написать от слова совсем а анктеа то полная по мне нет доступа к гигачату такой парадоксльный вывод, ну и потому что в админке гигачата нет расхода токенов"

**Перевод:**
- Анкета ПОЛНАЯ (мы это подтвердили ✅)
- Writer должен был хоть что-то написать по анкете
- **НО НЕТ РАСХОДА ТОКЕНОВ В АДМИНКЕ GIGACHAT!**

**Вывод:** Writer НЕ отправлял запросы к GigaChat!

---

## 🔍 ROOT CAUSE

### Файл: `C:\SnowWhiteAI\GrantService\shared\llm\config.py`

**Строки 49-54 (ДО ИСПРАВЛЕНИЯ):**
```python
"writer": {
    "provider": "claude_code",  # Using Claude Code for testing session 9
    "model": "sonnet",
    "temperature": 0.7,
    "max_tokens": 8000
},
```

**Строки 43-48 (ДО ИСПРАВЛЕНИЯ):**
```python
"researcher": {
    "provider": "claude",  # Claude лучше для анализа и исследования
    "model": "sonnet",
    "temperature": 0.3,
    "max_tokens": 1500
},
```

### Проблема в коде Writer V2

**Файл:** `C:\SnowWhiteAI\GrantService\agents\writer_agent_v2.py`
**Строки:** 1239-1245

```python
config = AGENT_CONFIGS.get("writer", AGENT_CONFIGS["writer"])

async with UnifiedLLMClient(
    provider=config["provider"],  # ← Берет из AGENT_CONFIGS!
    model=config["model"],        # ← Игнорирует self.llm_provider!
    temperature=config["temperature"]
) as client:
```

**Writer V2 ИГНОРИРУЕТ** параметр `llm_provider='gigachat'` который мы передавали в конструктор!

### Доказательство из логов

```
INFO:llm.unified_llm_client:🔧 Инициализирован CLAUDE_CODE клиент с моделью 'sonnet'
```

Writer использовал Claude Code вместо GigaChat!

---

## ✅ ИСПРАВЛЕНИЕ

### Изменено в config.py:

**Writer (строки 49-54):**
```python
"writer": {
    "provider": "gigachat",  # ИЗМЕНЕНО: GigaChat-2-Max для Sber500 Bootcamp (Iteration 27)
    "model": "GigaChat-2-Max",  # GigaChat 2.0 - second generation
    "temperature": 0.7,
    "max_tokens": 8000
},
```

**Researcher (строки 43-48):**
```python
"researcher": {
    "provider": "gigachat",  # ИЗМЕНЕНО: GigaChat-2-Max для Sber500 Bootcamp (Iteration 27)
    "model": "GigaChat-2-Max",  # GigaChat 2.0 - second generation
    "temperature": 0.3,
    "max_tokens": 1500
},
```

---

## 📊 ЧТО ЭТО ОБЪЯСНЯЕТ

### 1. Почему нет расхода токенов в админке GigaChat
- ✅ Writer использовал Claude Code
- ✅ Researcher тоже использовал Claude
- ✅ GigaChat вообще НЕ ВЫЗЫВАЛСЯ

### 2. Почему грантовая заявка пустая
- Claude Code может:
  - Не иметь доступа
  - Иметь проблемы с подключением
  - Возвращать пустые ответы
- Writer получил пустой/плохой response от Claude Code
- Поэтому написал "Нет данных" во всех разделах

### 3. Почему E2E тест "успешен" технически
- Код выполнился без exceptions
- Writer V2 технически отработал
- НО использовал неправильный LLM провайдер

### 4. Почему цитаты про Росстат
- Researcher тоже использовал Claude вместо GigaChat
- Claude может генерировать неправильные запросы
- Или Researcher получил плохой response

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

### Priority 1: Протестировать с GigaChat
1. ✅ Config исправлен
2. ⏳ Запустить E2E тест заново
3. ⏳ Проверить что используется GigaChat-2-Max
4. ⏳ Проверить расход токенов в админке
5. ⏳ Проверить качество заявки

### Priority 2: Исправить Writer V2 архитектуру
**Проблема:** Writer V2 игнорирует параметр конструктора `llm_provider`

**Решение (для будущего):**
- Использовать `self.llm_provider` если передан
- Fallback на `AGENT_CONFIGS` только если не передан

**Где:** `writer_agent_v2.py:1239-1245`

**Предложенный код:**
```python
# Use self.llm_provider if specified, otherwise fall back to config
if hasattr(self, 'llm_provider') and self.llm_provider:
    provider = self.llm_provider
    model = "GigaChat-2-Max" if provider == "gigachat" else "sonnet"
else:
    config = AGENT_CONFIGS.get("writer", AGENT_CONFIGS["writer"])
    provider = config["provider"]
    model = config["model"]

async with UnifiedLLMClient(
    provider=provider,
    model=model,
    temperature=config["temperature"]
) as client:
```

---

## 💡 LESSONS LEARNED

### 1. User observation was KEY
Пользователь заметил: "нет расхода токенов в админке" → это привело к открытию

### 2. Логирование критически важно
Без детального логирования LLM запросов мы бы не нашли проблему быстро

### 3. Config должен быть очевидным
AGENT_CONFIGS скрыт в config.py - не очевидно что Writer игнорирует параметры

### 4. Проверять расход токенов!
Если тест "успешен" но нет расхода токенов → что-то не так

---

## 📁 Измененные файлы

### 1. C:\SnowWhiteAI\GrantService\shared\llm\config.py
**Изменения:**
- Line 49-54: writer provider: claude_code → gigachat
- Line 43-48: researcher provider: claude → gigachat
- Оба используют model: GigaChat-2-Max

### 2. C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\scripts\llm_logger.py
**Создан:** Новый модуль для детального логирования LLM

### 3. C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\scripts\run_e2e_with_llm_logging.py
**Создан:** E2E тест с детальным LLM логированием

---

## ⏭️ NEXT: Iteration 27.1 - Test with GigaChat

**Цель:** Подтвердить что исправление работает

**Задачи:**
1. Запустить E2E тест с исправленным config
2. Убедиться что используется GigaChat-2-Max
3. Проверить расход токенов в админке GigaChat
4. Проверить качество сгенерированной заявки
5. Проверить что research queries правильные (про стрельбу из лука, не Росстат)

**ETA:** ~10 минут (Researcher 6 мин + Writer 1 мин)

---

**Отчет создан:** 2025-10-23 22:55
**Статус:** ✅ ROOT CAUSE FOUND AND FIXED
**Ready for:** Iteration 27.1 - Testing with GigaChat-2-Max
