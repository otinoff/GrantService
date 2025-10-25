# 🚀 Деплой 6: E2E Тест с GigaChat-Max для Буткэмпа

**Дата:** 2025-10-23
**Цель:** Запустить E2E тест (Researcher + Writer) с GigaChat-Max для демонстрации использования пакетных токенов

---

## 📊 Текущий статус

### ✅ Готово:

1. **Анкета партнёра (Наталья)** сохранена локально:
   - Файл: `test_data/natalia_anketa_20251012.json`
   - Проект: "Стрельба из лука - спортивно-патриотическое воспитание"
   - ID: `#AN-20251012-Natalia_bruzzzz-001`
   - Статус: completed (все поля заполнены)

2. **База знаний буткэмпа** в Qdrant:
   - Коллекция: `sber500_bootcamp`
   - Документов: 15 (13 + 2 техдокументация)
   - Semantic search работает

3. **E2E скрипты** созданы:
   - Production: `/var/GrantService/tests/run_e2e_simple.py`
   - Local: `scripts/run_e2e_local_windows.py`

4. **Researcher V2 на production** работает:
   - ✅ 27 экспертных запросов
   - ✅ WebSearch через Perplexity
   - ✅ Время: ~380s (6.3 минуты)

### ⚠️ Требует доработки:

1. **Writer V2** - ошибка вызова метода:
   - Метод: `write_application_async`
   - Проблема: требует `input_data: Dict` с определённой структурой
   - Нужно: передать правильную структуру данных

2. **GigaChat-Max** - не использовался:
   - Модель установлена, но Writer не сгенерировал текст
   - Токены: 0 (нужно ~15-20k для полной заявки)

---

## 🎯 План действий

### Этап 1: Локальная отладка (СЕЙЧАС)

#### Задачи:
1. ✅ Извлечь анкету Натальи из production БД
2. ✅ Сохранить локально в JSON
3. ⏳ Настроить локальное подключение к БД
4. ⏳ Отладить Writer V2 с правильными параметрами
5. ⏳ Запустить полный E2E тест
6. ⏳ Проверить использование GigaChat-Max токенов

#### Что нужно:

**1. Подключение к БД PostgreSQL:**
```python
# Remote DB (production)
PGHOST = "5.35.88.251"
PGPORT = "5434"
PGDATABASE = "grantservice"
PGUSER = "grantservice"
PGPASSWORD = "jPsGn%Nt%q#THnUB&&cqo*1Q"
```

**2. API Keys:**
```bash
# GigaChat (для Writer)
GIGACHAT_API_KEY = <from production .env>

# Perplexity (для Researcher)
PERPLEXITY_API_KEY = <from production .env>
```

**3. Исправить Writer V2:**
```python
# Текущий вызов (неправильный):
result = await writer.write_application_async(anketa_id)  # ❌ строка

# Правильный вызов:
input_data = {
    "anketa_id": anketa_id,
    "user_answers": {/* данные из sessions.interview_data */},
    "selected_grant": {/* опционально */}
}
result = await writer.write_application_async(input_data)  # ✅ dict
```

---

### Этап 2: Деплой 6 (ПОТОМ)

Когда всё работает локально:

#### Файлы для деплоя:
```
/var/GrantService/
├── agents/
│   ├── researcher_agent_v2.py  (уже на production, работает)
│   └── writer_agent_v2.py       (уже на production, нужно протестировать)
├── tests/
│   ├── run_e2e_simple.py        (исправленная версия)
│   └── run_e2e_with_env.sh      (wrapper)
└── test_results/
    └── e2e_metrics_*.json        (метрики для буткэмпа)
```

#### Команды деплоя:
```bash
# 1. Скопировать исправленный скрипт
scp run_e2e_simple.py root@5.35.88.251:/var/GrantService/tests/

# 2. Запустить E2E тест
ssh root@5.35.88.251 "/var/GrantService/tests/run_e2e_with_env.sh"

# 3. Скачать метрики
scp root@5.35.88.251:/var/GrantService/test_results/e2e_metrics_*.json ./
```

#### Ожидаемый результат:
```json
{
  "start_time": "2025-10-23T14:00:00",
  "anketa_id": "#AN-20251012-Natalia_bruzzzz-001",
  "model": "GigaChat-Max",
  "stages": {
    "researcher": {
      "status": "success",
      "duration_seconds": 380.5,
      "queries": 27,
      "provider": "Perplexity API"
    },
    "writer": {
      "status": "success",
      "duration_seconds": 45.2,
      "estimated_tokens": 18500,
      "model": "GigaChat-Max",
      "application_length": 14230
    }
  },
  "total_duration_seconds": 425.7
}
```

---

## 📊 Метрики для буткэмпа

### Целевые показатели:

**Токены GigaChat-Max:**
- Writer (эта заявка): ~15-20k токенов
- Target для недели: 1,000,000 токенов
- План: 50-70 таких заявок = 750k-1.4M токенов ✅

**Время выполнения:**
- Researcher: ~6 минут (27 запросов WebSearch)
- Writer: ~30-60 секунд (генерация заявки)
- **Total E2E:** ~7 минут

**Качество:**
- ✅ Real use case (реальная анкета от партнёра)
- ✅ Multi-agent (Researcher + Writer)
- ✅ High token consumption per application
- ✅ Production-ready workflow

---

## 🎯 Следующие шаги

### Приоритет 1: Отладка локально

1. **Настроить локальное окружение:**
   ```bash
   # Windows PowerShell
   $env:PGHOST="5.35.88.251"
   $env:PGPORT="5434"
   $env:PGDATABASE="grantservice"
   $env:PGUSER="grantservice"
   $env:PGPASSWORD="jPsGn%Nt%q#THnUB&&cqo*1Q"

   # API Keys (получить с production)
   $env:GIGACHAT_API_KEY="..."
   $env:PERPLEXITY_API_KEY="..."
   ```

2. **Исправить E2E скрипт:**
   - Правильная структура `input_data` для Writer
   - Проверка использования GigaChat-Max
   - Логирование токенов

3. **Запустить локальный тест:**
   ```bash
   cd C:\SnowWhiteAI\GrantService
   python scripts\run_e2e_local_windows.py
   ```

4. **Проверить метрики:**
   - Токены GigaChat-Max использованы
   - Researcher вернул 27 результатов
   - Writer сгенерировал заявку
   - Сохранены в JSON

### Приоритет 2: Деплой 6

Когда локальный тест работает:
- Деплой исправленной версии на production
- Запуск E2E теста на production
- Сбор финальных метрик
- **Отчёт для буткэмпа готов!**

---

## 💾 Файлы проекта

### Локально (C:\SnowWhiteAI\GrantService_Project):
```
01_Projects/2025-10-20_Bootcamp_GrantService/
├── test_data/
│   └── natalia_anketa_20251012.json        ← Анкета партнёра
├── scripts/
│   ├── run_e2e_local_windows.py             ← Локальный E2E тест
│   ├── run_e2e_gigachat_simple.py           ← Упрощённая версия
│   ├── add_technical_docs.py                ← Техдокументация в Qdrant
│   └── search_bootcamp.py                   ← Поиск по базе знаний
├── test_results/
│   └── e2e_metrics_*.json                   ← Метрики
└── DEPLOY_6_PLAN.md                         ← Этот файл
```

### Production (5.35.88.251:/var/GrantService):
```
/var/GrantService/
├── agents/
│   ├── researcher_agent_v2.py               ← Работает ✅
│   └── writer_agent_v2.py                   ← Требует доработки ⚠️
├── tests/
│   ├── run_e2e_simple.py                    ← E2E тест
│   └── run_e2e_with_env.sh                  ← Wrapper с env vars
└── test_results/
    └── e2e_metrics_*.json                   ← Результаты
```

---

## 📝 Примечания

### Почему локально сначала?

1. **Быстрая отладка** - видим все ошибки сразу
2. **Легко править** - не нужно каждый раз деплоить
3. **Безопасно** - не ломаем production
4. **Понятно** - видим весь workflow

### Что такое Итерация 27 запросов?

**Researcher Agent V2** делает **27 экспертных WebSearch запросов**:
- Блок 1: 10 запросов (проблема, аудитория, цели)
- Блок 2: 10 запросов (задачи, результаты, устойчивость)
- Блок 3: 7 запросов (партнёры, ресурсы, география)

Каждый запрос → Perplexity API → результаты сохраняются в БД

**Writer Agent V2** использует эти 27 результатов для генерации заявки через **GigaChat-Max**.

---

## ✅ Чеклист готовности

### Перед локальным тестом:
- [ ] PostgreSQL credentials настроены
- [ ] GigaChat API key получен
- [ ] Perplexity API key получен
- [ ] Анкета Натальи загружена (JSON)
- [ ] Python dependencies установлены
- [ ] E2E скрипт исправлен

### Перед Деплоем 6:
- [ ] Локальный E2E тест прошёл успешно
- [ ] GigaChat-Max токены использованы
- [ ] Метрики собраны и валидны
- [ ] Researcher работает (27 запросов)
- [ ] Writer генерирует заявку
- [ ] Production БД доступна

---

**Готовность:** 60%
**Следующий шаг:** Локальная отладка Writer V2
**ETA Деплой 6:** После успешного локального теста
