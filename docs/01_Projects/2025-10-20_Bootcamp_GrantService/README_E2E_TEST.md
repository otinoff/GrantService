# 🚀 E2E Test - GigaChat-Max для Sber500 Bootcamp

**Статус:** ✅ Готов к запуску локально
**Дата:** 2025-10-23
**Цель:** Демонстрация использования пакетных токенов GigaChat-Max

---

## 📊 Что готово

### ✅ Полностью готово:

1. **Анкета партнёра** (Наталья)
   - Файл: `test_data/natalia_anketa_20251012.json`
   - Проект: "Стрельба из лука - спортивно-патриотическое воспитание"
   - Статус: Completed, все поля заполнены

2. **Credentials (.env.local)**
   - ✅ PostgreSQL (remote БД на 5.35.88.251:5434)
   - ✅ GigaChat API Key
   - ✅ Perplexity API Key

3. **База знаний буткэмпа** (Qdrant)
   - Коллекция: `sber500_bootcamp`
   - Документов: 15
   - Команда поиска: `python scripts/search_bootcamp.py`

4. **План Деплоя 6**
   - Файл: `DEPLOY_6_PLAN.md`
   - Статус: Детальный план готов

### ⚠️ Production testing:

**Researcher V2** - ✅ Работает:
- 27 экспертных запросов
- Время: ~6 минут
- Status: SUCCESS

**Writer V2** - ⚠️ Требует доработки:
- Проблема: неправильная структура input_data
- Решение: известно (см. DEPLOY_6_PLAN.md)

---

## 🎯 Что делать СЕЙЧАС

### Вариант А: Быстрая проверка (5 минут)

Проверить что все credentials на месте:

```bash
cd C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService

# 1. Проверить анкету
type test_data\natalia_anketa_20251012.json

# 2. Проверить credentials
type .env.local

# 3. Проверить базу знаний буткэмпа
cd scripts
python search_bootcamp.py "токены gigachat"
python search_bootcamp.py "критерии топ50"
```

### Вариант Б: Полный E2E тест (локально)

**Требует:**
- Python 3.10+
- Доступ к remote БД (5.35.88.251:5434)
- Dependencies установлены

**Шаги:**

```bash
# 1. Загрузить environment
# (На Windows через PowerShell)
Get-Content .env.local | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}

# 2. Установить dependencies (если нужно)
cd C:\SnowWhiteAI\GrantService
pip install -r requirements.txt

# 3. Запустить E2E тест
cd C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\scripts
python run_e2e_local_windows.py
```

**Ожидаемый результат:**
- Подключение к БД ✅
- Researcher: 27 запросов ⏳ (~6 минут)
- Writer: генерация через GigaChat-Max ⏳ (~1 минута)
- Метрики сохранены в `test_results/`

---

## 📂 Структура проекта

```
01_Projects/2025-10-20_Bootcamp_GrantService/
├── .env.local                          ← Credentials для локальной работы
├── DEPLOY_6_PLAN.md                    ← Детальный план
├── README_E2E_TEST.md                  ← Этот файл
├── BOOTCAMP_KNOWLEDGE_BASE_SUMMARY.md  ← Описание базы знаний
│
├── test_data/
│   └── natalia_anketa_20251012.json    ← Анкета партнёра
│
├── scripts/
│   ├── run_e2e_local_windows.py        ← E2E тест (локально)
│   ├── search_bootcamp.py              ← Поиск по базе знаний
│   ├── add_technical_docs.py           ← Добавить техдокументацию
│   └── setup_knowledge_base.bat        ← Setup базы знаний
│
└── test_results/
    └── e2e_metrics_*.json              ← Результаты тестов
```

---

## 🎯 Следующие шаги

### Приоритет 1: Отладка Writer V2

**Проблема:**
Writer V2 ожидает `input_data: Dict`, а мы передаём `anketa_id: str`

**Решение:**
```python
# Было (неправильно):
result = await writer.write_application_async(anketa_id)

# Должно быть:
input_data = {
    "anketa_id": anketa_id,
    "user_answers": {/* данные из sessions.interview_data */},
    "selected_grant": {}  # optional
}
result = await writer.write_application_async(input_data)
```

**Файл для правки:**
- `scripts/run_e2e_local_windows.py` (функция `run_writer`)

### Приоритет 2: Локальный тест

После исправления Writer V2:
1. Запустить полный E2E тест локально
2. Проверить использование GigaChat-Max токенов
3. Собрать метрики
4. Если работает → Деплой 6 на production

### Приоритет 3: Деплой 6

Когда локальный тест работает:
- Деплой исправленной версии на production
- Запуск на production
- Финальные метрики для буткэмпа

---

## 📊 Ожидаемые метрики

### Target для одной заявки:

```json
{
  "anketa_id": "#AN-20251012-Natalia_bruzzzz-001",
  "model": "GigaChat-Max",
  "stages": {
    "researcher": {
      "status": "success",
      "duration_seconds": 380,
      "queries": 27,
      "provider": "Perplexity API"
    },
    "writer": {
      "status": "success",
      "duration_seconds": 45,
      "estimated_tokens": 18500,
      "model": "GigaChat-Max"
    }
  },
  "total_duration_seconds": 425
}
```

### Target для недели (буткэмп):

- **1 заявка** = ~18,500 токенов GigaChat-Max
- **Target** = 1,000,000 токенов
- **Нужно** = ~54 заявки
- **Реально** = 50-70 заявок ✅

---

## 🔑 Ключевая информация

### Database (PostgreSQL):
```
Host: 5.35.88.251
Port: 5434
Database: grantservice
User: grantservice
Password: jPsGn%Nt%q#THnUB&&cqo*1Q
```

### GigaChat API:
```
Key: OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5Ojk4MmM0NjIyLTU3OWQtNDYxNi04YzVlLWIyMTY3YTZlNzI0NQ==
Model: GigaChat-Max
Tokens available: 2,000,000 (из пакета)
```

### Perplexity API:
```
Key: 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
Usage: WebSearch для Researcher (27 запросов)
```

---

## 💡 Полезные команды

### Проверка базы знаний:
```bash
cd scripts
python search_bootcamp.py "баланс токенов"
python search_bootcamp.py "топ50 преимущества"
python search_bootcamp.py "воркшопы метрики"
```

### Проверка БД (remote):
```bash
# PowerShell (установить переменные)
$env:PGHOST="5.35.88.251"
$env:PGPORT="5434"
$env:PGUSER="grantservice"
$env:PGPASSWORD="jPsGn%Nt%q#THnUB&&cqo*1Q"

# Проверка подключения (если psql установлен)
psql -h 5.35.88.251 -p 5434 -U grantservice -d grantservice -c "SELECT count(*) FROM sessions;"
```

---

## ✅ Готовность к запуску

- [✅] Анкета партнёра загружена
- [✅] Credentials настроены (.env.local)
- [✅] База знаний буткэмпа создана
- [✅] План Деплоя 6 готов
- [⏳] Writer V2 требует доработки (input_data structure)
- [⏳] Локальный E2E тест не запускался
- [⏳] Метрики не собраны

**Готовность:** 70%
**Блокер:** Writer V2 input_data structure
**ETA до готовности:** 1-2 часа работы

---

## 🎉 Итог

**Готово для запуска:**
- ✅ Все credentials на месте
- ✅ База знаний работает
- ✅ Researcher V2 протестирован (работает на production)
- ⚠️ Writer V2 требует небольшой правки

**Следующий шаг:**
1. Исправить `input_data` в `run_writer()` функции
2. Запустить локальный E2E тест
3. Если работает → Деплой 6
4. **Готово для буткэмпа!** 🚀

---

**Вопросы?** Всё описано в `DEPLOY_6_PLAN.md`
