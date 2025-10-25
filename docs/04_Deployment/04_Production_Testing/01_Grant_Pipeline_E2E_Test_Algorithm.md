# Алгоритм E2E тестирования грантового потока

**Дата создания:** 2025-10-23
**Версия:** 1.0
**Статус:** ✅ ACTIVE

---

## 🎯 Цель

Создать полный E2E тест для проверки грантового потока от анкеты до положительного заключения Auditor.

**Целевая метрика:** Auditor Score ≥ 80% (can_submit = true)

---

## 📊 Грантовый поток (6 этапов)

```
┌─────────────────────────────────────────────────────────────┐
│                    GRANT PIPELINE E2E TEST                   │
└─────────────────────────────────────────────────────────────┘

Stage 1: Interview (24 вопроса)
   ↓
   Input: Пользователь отвечает на вопросы
   Output: sessions (anketa_id, answers_data)
   Database: sessions
   Status: completed

Stage 2: Auditor (оценка анкеты)
   ↓
   Input: sessions.answers_data
   Output: auditor_results (5 scores)
   Database: auditor_results
   Decision: approved (score ≥ 6) OR needs_revision (score < 6)

Stage 3: Planner (структура заявки)
   ↓
   Input: auditor_results, sessions
   Output: planner_structures (7 разделов)
   Database: planner_structures
   Mapping: questions → sections

Stage 4: Researcher (поиск данных)  ← ТУТ БЫЛА ПРОБЛЕМА!
   ↓
   Input: planner_structures, sessions.project_data
   Output: researcher_research (research_results)
   API: Perplexity API / Qdrant search
   Database: researcher_research

   ❗ ЭТО КРИТИЧЕСКИЙ ЭТАП!
   Writer ДОЛЖЕН получить research_results, иначе заявка будет:
   - Без специфики проекта
   - С неправильными цитатами
   - Оценка Auditor будет низкой (62% вместо 80%+)

Stage 5: Writer (генерация текста)
   ↓
   Input: sessions + planner_structures + researcher_research
   Output: grants (grant_content)
   LLM: GigaChat-2-Max
   Database: grants
   Quality check: completeness, citations, word count

Stage 6: Auditor (финальная оценка)
   ↓
   Input: grants.grant_content
   Output: auditor_results (final score)
   Target: score ≥ 80%, can_submit = true
```

---

## 🔍 Проблема Iteration 27

**Что мы сделали:**
- ✅ Запустили test_writer_only.py
- ✅ Writer сгенерировал заявку GA-20251023-42EC3885 (17,667 символов)
- ✅ Auditor оценил: 62.96% (Удовлетворительно)

**Почему оценка низкая?**

```python
# test_writer_only.py:98-101
input_data = {
    "anketa_id": ANKETA_ID,
    "user_answers": anketa.get("interview_data", {}),
    "selected_grant": {}  # ❌ НЕТ research_results!
}
```

**Проблемы в заявке:**
1. ❌ **Completeness: 4.0/10** - отсутствуют 6 из 10 разделов
2. ❌ **Compliance: 5.0/10** - цитаты про Росстат вместо стрельбы из лука
3. ❌ **Can Submit: false** - нельзя подавать

**Root Cause:**
- Writer работал БЕЗ данных от Researcher
- Не было специфики про стрельбу из лука
- Использовал общие фразы и старые цитаты из БД

---

## ✅ Решение: Полный E2E тест

### Алгоритм полного теста

```
┌─────────────────────────────────────────────────────────────┐
│          FULL E2E TEST ALGORITHM                            │
└─────────────────────────────────────────────────────────────┘

1. ПОДГОТОВКА (Setup)
   ├─ Загрузить анкету из БД (AN_20251012_Natalia_bruzzzz_001)
   ├─ Проверить наличие всех ответов (24/24)
   └─ Подготовить тестовое окружение

2. STAGE 1: RESEARCHER (6-7 минут)
   ├─ Извлечь проектные данные из анкеты:
   │  - Название проекта: "Школа стрельбы из лука"
   │  - Проблема: обучение детей стрельбе из лука
   │  - Целевая аудитория: дети 7-17 лет
   │  - География: Москва
   ├─ Сгенерировать 27 экспертных запросов:
   │  - 5 запросов про стрельбу из лука (техника, безопасность)
   │  - 5 запросов про федерацию и турниры
   │  - 5 запросов про обучение детей
   │  - 5 запросов про социальную значимость спорта
   │  - 4 запроса про статистику и данные
   │  - 3 запроса про лучшие практики
   ├─ Выполнить поиск через Perplexity API / Qdrant
   ├─ Структурировать результаты research_results
   └─ Сохранить в researcher_research

   ✅ Expected Output: research_results с 27 результатами поиска
   📊 Tokens: ~15,000-20,000 (Perplexity)
   ⏱️ Time: 6-7 минут

3. STAGE 2: WRITER (1-2 минуты)
   ├─ Собрать полный контекст:
   │  context = {
   │      "anketa": anketa.answers_data,
   │      "research_results": researcher_research.research_results,
   │      "selected_grant": grant_info
   │  }
   ├─ Запустить Writer V2 с ПОЛНЫМ контекстом
   ├─ Сгенерировать заявку через GigaChat-2-Max
   └─ Сохранить в grants

   ✅ Expected Output: Полная заявка (30,000+ символов)
   📊 Tokens: ~8,000-10,000 (GigaChat)
   ⏱️ Time: 1-2 минуты

4. STAGE 3: AUDITOR (30 секунд)
   ├─ Загрузить сгенерированную заявку
   ├─ Запустить Auditor Agent
   ├─ Получить детальную оценку:
   │  - Completeness (полнота)
   │  - Quality (качество)
   │  - Compliance (соответствие)
   │  - Citations (цитаты правильные?)
   ├─ Вычислить итоговый score
   └─ Сохранить отчёт в audit_report_*.json

   ✅ Expected Output: score ≥ 80%, can_submit = true
   📊 Tokens: ~3,000-4,000 (GigaChat)
   ⏱️ Time: 30 секунд

5. ВАЛИДАЦИЯ (Validation)
   ├─ Проверить все 3 документа существуют:
   │  - researcher_research (research_id)
   │  - grants (grant_id)
   │  - audit_report (report file)
   ├─ Проверить метрики:
   │  - Auditor score ≥ 80%
   │  - can_submit = true
   │  - Правильные цитаты (про стрельбу из лука!)
   │  - Все разделы заполнены (10/10)
   └─ Логировать результаты

6. ОТЧЁТ (Report)
   └─ Создать Iteration 27 FINAL REPORT с:
      - Research results (excerpt)
      - Generated grant (full text)
      - Auditor report (full analysis)
      - Success metrics
      - Next steps
```

---

## 📝 Success Criteria

### Минимальные требования (MUST HAVE)

1. ✅ **Researcher отработал успешно**
   - research_results содержит 27+ результатов
   - Все запросы про стрельбу из лука (НЕ Росстат!)
   - Сохранено в researcher_research

2. ✅ **Writer получил research data**
   - input_data["research_results"] NOT NULL
   - Заявка содержит цитаты из research
   - grant_content ≥ 30,000 символов

3. ✅ **Auditor дал положительное заключение**
   - Overall score ≥ 80%
   - Completeness ≥ 8.0/10
   - Quality ≥ 8.0/10
   - Compliance ≥ 8.0/10
   - can_submit = true

4. ✅ **Все документы сохранены**
   - researcher_research в БД
   - grants в БД
   - audit_report_*.json в test_results/

### Целевые метрики (TARGET)

| Metric | Current (Iteration 27) | Target (Full E2E) |
|--------|------------------------|-------------------|
| Auditor Score | 62.96% | ≥ 80% |
| Completeness | 4.0/10 | ≥ 8.0/10 |
| Quality | 9.0/10 | ≥ 8.0/10 |
| Compliance | 5.0/10 | ≥ 8.0/10 |
| Can Submit | false | true |
| Grant Length | 17,667 chars | ≥ 30,000 chars |
| Sections Present | 4/10 | 10/10 |
| Citations Correct | 0% (Росстат!) | 100% (лук!) |

---

## 🚀 Implementation Plan

### Файлы для создания

1. **test_e2e_full_pipeline.py** (новый скрипт)
   - Запускает Researcher → Writer → Auditor
   - Использует реальную анкету AN_20251012_Natalia_bruzzzz_001
   - Полное логирование всех этапов
   - Сохранение всех 3 документов

2. **01_Grant_Pipeline_E2E_Test_Algorithm.md** (этот файл)
   - Полное описание алгоритма
   - Success criteria
   - Метрики качества

3. **02_E2E_Test_Results_Report.md** (после теста)
   - Результаты всех 3 этапов
   - Auditor final report
   - Recommendations

---

## ⚙️ Configuration

### Env Variables Required

```bash
# .env.local
POSTGRES_DB=grantservice_local
POSTGRES_USER=grantservice
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5434

# GigaChat (Writer + Auditor)
GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
GIGACHAT_API_KEY=your_key
GIGACHAT_MODEL=GigaChat-2-Max

# Perplexity (Researcher)
PERPLEXITY_API_KEY=your_key
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online
```

### Expected Runtime

| Stage | Time | Tokens | Cost (est.) |
|-------|------|--------|-------------|
| Researcher | 6-7 min | 15,000-20,000 | ~300 руб |
| Writer | 1-2 min | 8,000-10,000 | ~160 руб |
| Auditor | 30 sec | 3,000-4,000 | ~60 руб |
| **TOTAL** | **~8 min** | **~30,000** | **~520 руб** |

---

## 🐛 Known Issues & Solutions

### Issue #1: Writer без Researcher data (Iteration 27)

**Problem:** test_writer_only.py не передаёт research_results
**Impact:** Низкая оценка Auditor (62.96%)
**Solution:** Запустить полный E2E тест с Researcher

### Issue #2: GigaChat Rate Limit (429)

**Problem:** Слишком много запросов подряд
**Impact:** Auditor может упасть после Writer
**Solution:** Добавить delay 2-3 секунды между агентами

### Issue #3: Неправильные цитаты (Росстат вместо лука)

**Problem:** Writer использует старые research results из БД
**Impact:** Compliance score низкий
**Solution:** Очистить старые research results или генерировать новые

---

## 📚 Related Documents

- **BUSINESS_LOGIC.md** - полное описание грантового потока
- **AUTONOMOUS_TESTING_METHODOLOGY.md** - методология тестирования
- **LLM_Logging_Guide.md** - логирование LLM вызовов
- **Iteration_27_ROOT_CAUSE_FOUND.md** - анализ проблемы Writer

---

## 🎯 Next Steps

1. ✅ Создать алгоритм E2E тестирования (этот файл)
2. ⏳ Создать test_e2e_full_pipeline.py
3. ⏳ Запустить полный тест (Researcher → Writer → Auditor)
4. ⏳ Получить положительное заключение Auditor (80%+)
5. ⏳ Создать Iteration 27 FINAL REPORT

---

**Автор:** Claude Code
**Дата:** 2025-10-23
**Версия:** 1.0
**Статус:** ✅ READY FOR IMPLEMENTATION
