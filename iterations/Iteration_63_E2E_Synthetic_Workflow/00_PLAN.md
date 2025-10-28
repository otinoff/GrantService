# Iteration 63: End-to-End Synthetic Workflow (5 Complete Cycles)

**Date:** 2025-10-29 02:00 MSK
**Status:** 🔧 IN PROGRESS
**Priority:** 🔥 HIGH (E2E pipeline validation)
**Parent:** Iteration 62 - Research Results Parsing Fix
**Estimated Time:** 2-3 hours

---

## 🎯 Goal

Сгенерировать **5 синтетических анкет** и провести каждую через **ПОЛНЫЙ workflow**:

```
GENERATE → AUDIT → RESEARCH → WRITER → REVIEW → EMBEDDINGS (опц.)
```

Каждый этап:
- ✅ Сохраняется в БД с правильными ID
- ✅ Генерирует .txt файл по nomenclature
- ✅ Использует реальных агентов (не моки)
- ✅ Проверяет интеграцию всех компонентов

**Result:** 5 анкет × 6 этапов = **25 файлов** + БД + embeddings (опц.)

---

## 📊 Workflow Diagram

```
┌────────────────────────────────────────────────────────────┐
│  ЦИКЛ 1-5: Каждая анкета проходит полный pipeline         │
└────────────────────────────────────────────────────────────┘

1️⃣ GENERATE SYNTHETIC ANKETA
   │
   ├─ SyntheticUserSimulator генерирует ответы (10 полей)
   ├─ Сохраняет в sessions таблицу (synthetic=TRUE)
   ├─ Сохраняет Q&A в interview_qa (10-15 turns)
   ├─ Генерирует ID: #AN-YYYYMMDD-synthetic_user_N-001
   └─ Файл: anketa_AN-YYYYMMDD-synthetic_user_N-001.txt

   ↓

2️⃣ AUDIT
   │
   ├─ AuditorAgent анализирует анкету
   ├─ Проверяет полноту, качество, соответствие
   ├─ Сохраняет в audits таблицу
   ├─ Генерирует ID: #AN-...-AU-001
   └─ Файл: audit_AN-YYYYMMDD-synthetic_user_N-001-AU-001.txt

   ↓

3️⃣ RESEARCH
   │
   ├─ ResearcherAgent делает 3 WebSearch запроса
   ├─ Claude Code WebSearch → реальные данные
   ├─ Сохраняет в researcher_research таблицу
   ├─ Генерирует ID: #AN-...-RS-001
   └─ Файл: research_AN-YYYYMMDD-synthetic_user_N-001-RS-001.txt

   ↓

4️⃣ WRITER
   │
   ├─ WriterAgent создаёт грант (используя audit + research)
   ├─ Генерирует grant application (3000-5000 слов)
   ├─ Сохраняет в grants таблицу
   ├─ Генерирует ID: #AN-...-GR-001
   └─ Файл: grant_AN-YYYYMMDD-synthetic_user_N-001-GR-001.txt

   ↓

5️⃣ REVIEW
   │
   ├─ ReviewerAgent проверяет грант
   ├─ Оценка (0-10), рекомендации, финальный текст
   ├─ Сохраняет в reviews таблицу
   ├─ Генерирует ID: #AN-...-RV-001
   └─ Файл: review_AN-YYYYMMDD-synthetic_user_N-001-RV-001.txt

   ↓

6️⃣ GENERATE EMBEDDINGS (OPTIONAL)
   │
   ├─ GigaChat Embeddings для grant text
   ├─ Сохраняет vectors в Qdrant (collection: grants_synthetic)
   ├─ Метаданные: session_id, quality_level, region, topic
   ├─ Использует GigaChat Embeddings API
   └─ Точка в Qdrant с полным контекстом

   Flag: --with-embeddings

═══════════════════════════════════════════════════════════════
РЕЗУЛЬТАТ: 5 циклов × 5 файлов + embeddings (опц.)
        = 25 .txt файлов + БД + Qdrant (5 точек)
═══════════════════════════════════════════════════════════════
```

---

## 📋 Tasks

### Phase 1: Create E2E Script (Core)

**File:** `scripts/e2e_synthetic_workflow.py`

**Structure:**
- `generate_synthetic_anketa()` - Step 1
- `run_audit()` - Step 2
- `run_research()` - Step 3
- `run_writer()` - Step 4
- `run_review()` - Step 5
- `generate_embeddings()` - Step 6 (optional)
- `run_full_cycle()` - Orchestrator
- `main()` - CLI

**CLI:**
```bash
# Без embeddings (быстрее)
python scripts/e2e_synthetic_workflow.py --cycles 5

# С embeddings (полный набор данных)
python scripts/e2e_synthetic_workflow.py --cycles 5 --with-embeddings

# Тест 1 цикла
python scripts/e2e_synthetic_workflow.py --cycles 1
```

---

### Phase 2: Telegram Admin Commands (Optional)

**Админ команды в боте для запуска генерации:**

```
/admin_generate - Сгенерировать 1 анкету через полный workflow
/admin_generate_n <N> - Сгенерировать N анкет
/admin_list_synthetic - Показать список synthetic anketas
/admin_stats - Статистика synthetic generation
```

**Handler:** `telegram-bot/handlers/admin_synthetic_handler.py`

**Integration:**
- Проверка admin прав (is_admin)
- Async запуск e2e_synthetic_workflow
- Progress updates в Telegram
- Отправка summary после completion

**Example:**
```
User: /admin_generate_n 5

Bot: 🤖 Запускаю генерацию 5 анкет...

Bot: [1/5] Генерирую анкету... ✅
     [1/5] Аудит... ✅
     [1/5] Исследование... ✅
     [1/5] Грант... ✅
     [1/5] Ревью... ✅

Bot: ✅ Завершено!
     • 5 анкет сгенерировано
     • 25 файлов создано
     • IDs: #AN-20251029-synthetic_user_001 - 005
     • Время: 55 минут
```

**Deferred to:** Iteration 64 (или после успешного Phase 1)

---

## ✅ Success Criteria

**Core (required):**
- [ ] Script created
- [ ] 1 cycle test passes (5 files)
- [ ] 5 cycles complete (25 files)
- [ ] All IDs correct
- [ ] All files generated
- [ ] Research shows real data (NOT N/A!)

**Embeddings (optional with --with-embeddings):**
- [ ] GigaChat Embeddings integration
- [ ] 5 vectors saved to Qdrant
- [ ] Collection: grants_synthetic created
- [ ] Metadata includes: session_id, quality, region, topic
- [ ] Can query semantically similar grants

---

## 🗂️ Output

```
data/synthetic_corpus_2025-10-29/
├── cycle_1/
│   ├── anketa_AN-20251029-synthetic_user_001.txt
│   ├── audit_...txt
│   ├── research_...txt
│   ├── grant_...txt
│   └── review_...txt
├── cycle_2/
├── cycle_3/
├── cycle_4/
├── cycle_5/
└── summary.json
```

---

**Created:** 2025-10-29 02:00 MSK
**Status:** 🔧 IN PROGRESS
