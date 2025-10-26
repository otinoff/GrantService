# Iteration 50: End-to-End Integration Test (Full Flow)

**Дата создания:** 2025-10-26
**Статус:** 🟡 PLANNING
**Предыдущая итерация:** Iteration 49 - Reviewer Agent Testing ✅ COMPLETED
**Цель:** Создать полный end-to-end тест: Interview → Audit → Writer → 6 текстовых файлов в папке итерации

---

## 🎯 Sprint Goal

> **Создать сквозной end-to-end интеграционный тест с полным циклом обработки 2 анкет через InterviewerAgent → AuditorAgent → WriterAgent с сохранением всех промежуточных результатов в файлы.**

**Context:**
- У нас есть рабочие агенты: InterviewerAgent, AuditorAgent, WriterAgent, ReviewerAgent
- Iteration 47 протестировал WriterAgent на готовых анкетах (2 заявки созданы)
- Iteration 49 протестировал ReviewerAgent с векторной БД
- Нужен ПОЛНЫЙ цикл с созданием новых анкет через InterviewerAgent
- По методологии: `C:\SnowWhiteAI\cradle\Know-How\TESTING-METHODOLOGY.md` (Section 9 - Integration Testing)

**Input:**
- Синтетические ответы для InterviewerAgent (2 набора: MEDIUM + HIGH качества)
- PostgreSQL БД для сохранения промежуточных результатов
- GigaChat API для всех агентов

**Expected Output (6 файлов):**
1. `ANKETA_1_MEDIUM.txt` - анкета из Interview #1
2. `ANKETA_2_HIGH.txt` - анкета из Interview #2
3. `AUDIT_1_MEDIUM.txt` - аудит анкеты #1
4. `AUDIT_2_HIGH.txt` - аудит анкеты #2
5. `GRANT_1_MEDIUM.txt` - грантовая заявка из анкеты #1
6. `GRANT_2_HIGH.txt` - грантовая заявка из анкеты #2

---

## 📋 Success Criteria

### Обязательные (Must Have):

1. ✅ **2 новых интервью созданы через InterviewerAgent**
   - Полный цикл вопросы-ответы (10+ вопросов)
   - Синтетические ответы разного качества (MEDIUM vs HIGH)
   - Сохранение в БД с уникальными anketa_id
   - Экспорт в текстовые файлы (ANKETA_1_MEDIUM.txt, ANKETA_2_HIGH.txt)

2. ✅ **2 аудита созданы через AuditorAgent**
   - Загрузка анкет из БД по anketa_id
   - Полный аудит по 10 критериям
   - Оценка качества (score + recommendations)
   - Сохранение в БД + экспорт в файлы (AUDIT_1_MEDIUM.txt, AUDIT_2_HIGH.txt)

3. ✅ **2 грантовые заявки написаны через WriterAgent**
   - Загрузка анкет + аудитов из БД
   - Генерация полных заявок (30K+ chars)
   - Сохранение в БД + экспорт в файлы (GRANT_1_MEDIUM.txt, GRANT_2_HIGH.txt)

4. ✅ **Все промежуточные результаты в БД**
   - anketas таблица: 2 записи
   - audits таблица: 2 записи
   - grant_applications таблица: 2 записи
   - Связи по anketa_id корректны

5. ✅ **6 текстовых файлов в папке итерации**
   - `iterations/Iteration_50_E2E_Full_Flow/ANKETA_1_MEDIUM.txt`
   - `iterations/Iteration_50_E2E_Full_Flow/ANKETA_2_HIGH.txt`
   - `iterations/Iteration_50_E2E_Full_Flow/AUDIT_1_MEDIUM.txt`
   - `iterations/Iteration_50_E2E_Full_Flow/AUDIT_2_HIGH.txt`
   - `iterations/Iteration_50_E2E_Full_Flow/GRANT_1_MEDIUM.txt`
   - `iterations/Iteration_50_E2E_Full_Flow/GRANT_2_HIGH.txt`

### Желательные (Nice to Have):

6. ⚪ Сравнительная таблица MEDIUM vs HIGH
7. ⚪ Метрики по каждому этапу (время, длина текста, оценки)
8. ⚪ Автоматическая валидация бизнес-логики (HIGH > MEDIUM quality)

---

## 📊 Задачи (Tasks)

### 1. Анализ существующих тестов (20 min) ⏸️

- [x] Прочитать `tests/integration/test_write_two_grants.py` (Iteration 47)
- [x] Прочитать методологию `TESTING-METHODOLOGY.md`
- [ ] Найти InterviewerAgent integration test (если есть)
- [ ] Найти AuditorAgent integration test
- [ ] Понять формат сохранения в БД

### 2. Подготовка синтетических ответов (30 min) ⏸️

**Файл:** `tests/fixtures/synthetic_interview_responses.py`

```python
# Synthetic responses для InterviewerAgent
MEDIUM_QUALITY_RESPONSES = {
    "organization": "Центр молодежных проектов",
    "project_name": "Научная лаборатория для школьников",
    "problem": "В нашем городе нет мест для научных экспериментов для школьников",
    "solution": "Создать научную лабораторию с современным оборудованием",
    "budget": "500000 рублей на оборудование и аренду",
    # ... остальные 7 полей
}

HIGH_QUALITY_RESPONSES = {
    "organization": "Ассоциация молодых ученых Новосибирска",
    "project_name": "Образовательный центр робототехники и программирования для молодежи",
    "problem": "В Новосибирской области отсутствуют доступные образовательные программы...",
    "solution": "Создание современного образовательного центра с 5 направлениями...",
    "budget": "2500000 рублей детализированный бюджет по статьям расходов...",
    # ... более детальные и длинные ответы
}
```

### 3. Создать E2E тестовый скрипт (60 min) ⏸️

**Файл:** `tests/integration/test_e2e_full_flow.py`

**Структура теста:**

```python
import pytest
from agents.interviewer_agent import InterviewerAgent  # или InteractiveInterviewerV2
from agents.auditor_agent import AuditorAgent
from agents.writer_agent import WriterAgent
from tests.fixtures.synthetic_interview_responses import MEDIUM_QUALITY_RESPONSES, HIGH_QUALITY_RESPONSES

@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
class TestE2EFullFlow:
    """End-to-End: Interview → Audit → Writer → Files"""

    def test_phase_1_create_two_interviews(self, db, output_dir):
        """Phase 1: Create 2 interviews (MEDIUM + HIGH)"""

        # INTERVIEW #1 (MEDIUM)
        interviewer = InterviewerAgent(db=db)
        anketa_1 = interviewer.run_with_synthetic_responses(
            responses=MEDIUM_QUALITY_RESPONSES
        )
        assert anketa_1.id is not None
        assert anketa_1.status == "completed"

        # Export to file
        anketa_1_file = output_dir / "ANKETA_1_MEDIUM.txt"
        export_anketa_to_file(anketa_1, anketa_1_file)
        assert anketa_1_file.exists()

        # INTERVIEW #2 (HIGH)
        anketa_2 = interviewer.run_with_synthetic_responses(
            responses=HIGH_QUALITY_RESPONSES
        )
        assert anketa_2.id is not None

        # Export to file
        anketa_2_file = output_dir / "ANKETA_2_HIGH.txt"
        export_anketa_to_file(anketa_2, anketa_2_file)
        assert anketa_2_file.exists()

        # Save IDs for next phase
        return {
            'anketa_1_id': anketa_1.id,
            'anketa_2_id': anketa_2.id
        }

    def test_phase_2_audit_two_anketas(self, db, output_dir, test_phase_1_create_two_interviews):
        """Phase 2: Audit 2 anketas"""

        anketa_ids = test_phase_1_create_two_interviews

        auditor = AuditorAgent(db=db)

        # AUDIT #1 (MEDIUM)
        audit_1 = auditor.audit_anketa(anketa_id=anketa_ids['anketa_1_id'])
        assert audit_1['overall_score'] > 0

        # Export to file
        audit_1_file = output_dir / "AUDIT_1_MEDIUM.txt"
        export_audit_to_file(audit_1, audit_1_file)

        # AUDIT #2 (HIGH)
        audit_2 = auditor.audit_anketa(anketa_id=anketa_ids['anketa_2_id'])
        assert audit_2['overall_score'] > audit_1['overall_score']  # HIGH > MEDIUM

        # Export to file
        audit_2_file = output_dir / "AUDIT_2_HIGH.txt"
        export_audit_to_file(audit_2, audit_2_file)

        return {
            'audit_1': audit_1,
            'audit_2': audit_2,
            **anketa_ids
        }

    def test_phase_3_write_two_grants(self, db, output_dir, test_phase_2_audit_two_anketas):
        """Phase 3: Write 2 grant applications"""

        data = test_phase_2_audit_two_anketas

        writer = WriterAgent(db=db)

        # GRANT #1 (MEDIUM)
        grant_1 = writer.write_from_anketa(anketa_id=data['anketa_1_id'])
        assert len(grant_1['content']) > 30000

        # Export to file
        grant_1_file = output_dir / "GRANT_1_MEDIUM.txt"
        export_grant_to_file(grant_1, grant_1_file)

        # GRANT #2 (HIGH)
        grant_2 = writer.write_from_anketa(anketa_id=data['anketa_2_id'])
        assert len(grant_2['content']) > len(grant_1['content'])  # HIGH > MEDIUM

        # Export to file
        grant_2_file = output_dir / "GRANT_2_HIGH.txt"
        export_grant_to_file(grant_2, grant_2_file)

        # Final validation
        assert (output_dir / "ANKETA_1_MEDIUM.txt").exists()
        assert (output_dir / "ANKETA_2_HIGH.txt").exists()
        assert (output_dir / "AUDIT_1_MEDIUM.txt").exists()
        assert (output_dir / "AUDIT_2_HIGH.txt").exists()
        assert (output_dir / "GRANT_1_MEDIUM.txt").exists()
        assert (output_dir / "GRANT_2_HIGH.txt").exists()

        print("\n✅ E2E Test COMPLETED: 6 files created")
```

### 4. Реализовать export helpers (20 min) ⏸️

```python
def export_anketa_to_file(anketa: Dict, file_path: Path):
    """Export anketa to readable text file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("АНКЕТА ГРАНТОВОЙ ЗАЯВКИ\n")
        f.write("="*80 + "\n\n")
        f.write(f"ID: {anketa['id']}\n")
        f.write(f"Организация: {anketa.get('organization')}\n")
        # ... все поля

def export_audit_to_file(audit: Dict, file_path: Path):
    """Export audit results to text file"""
    # Similar format

def export_grant_to_file(grant: Dict, file_path: Path):
    """Export grant application to text file"""
    # Full grant text
```

### 5. Запуск теста (10 min) ⏸️

```bash
# Run full E2E flow
python -m pytest tests/integration/test_e2e_full_flow.py -xvs --tb=short

# Expected time: ~20-30 minutes (2 interviews + 2 audits + 2 grants)
```

### 6. Валидация результатов (15 min) ⏸️

**По методологии (TESTING-METHODOLOGY.md, Section 9.2):**

```python
def validate_e2e_results(db, output_dir):
    """Validate E2E test results"""

    # 1. Database validation
    anketas = db.get_all_anketas()
    assert len(anketas) >= 2

    audits = db.get_all_audits()
    assert len(audits) >= 2

    grants = db.get_all_grant_applications()
    assert len(grants) >= 2

    # 2. File validation
    files = list(output_dir.glob("*.txt"))
    assert len(files) == 6

    # 3. Business logic validation
    # HIGH quality should score better than MEDIUM
    audit_1 = get_audit_by_quality(audits, "MEDIUM")
    audit_2 = get_audit_by_quality(audits, "HIGH")
    assert audit_2['score'] > audit_1['score']

    # 4. Content validation
    for file_path in files:
        content = file_path.read_text(encoding='utf-8')
        assert len(content) > 100  # Not empty
```

### 7. Документация (15 min) ⏸️

- [ ] Создать ITERATION_50_SUMMARY.md
- [ ] Git commit всех изменений
- [ ] Обновить README с примером E2E теста

**Estimated Time:** ~3 hours

---

## 🔄 Методология: TESTING-METHODOLOGY.md Alignment

### Core Principles Applied:

1. **Production Parity** (Principle 1)
   - Тест использует production imports (InterviewerAgent, AuditorAgent, WriterAgent)
   - Тест использует production БД (PostgreSQL)
   - Тест использует production LLM (GigaChat)

2. **E2E Testing** (Section 7 - Test Pyramid, 10%)
   - **Few tests** (1 comprehensive E2E test covering full flow)
   - **Full system** (все агенты задействованы)
   - **Realistic scenarios** (синтетические ответы симулируют реальных пользователей)
   - **One passing E2E test = high confidence** (методология, стр. 569)

3. **Integration Testing** (Section 9)
   - **Real dependencies** (PostgreSQL, GigaChat API)
   - **Contract validation** (агенты передают данные друг другу)
   - **End-to-end flow**: Interview → DB → Audit → DB → Writer → DB → Files

4. **Test Structure** (Section 9.2):
   ```python
   # 1. SETUP - fixtures (db, output_dir, synthetic_responses)
   # 2. EXECUTE - run agents
   # 3. VALIDATE TECHNICAL - result structure
   # 4. VALIDATE BUSINESS - quality differentiation (HIGH > MEDIUM)
   # 5. SAVE & VERIFY - files exported, DB records created
   ```

5. **AI/LLM-Specific Testing** (Section 10):
   - **Semantic validation** (не точное совпадение текстов, а проверка концепций)
   - **Rate limiting awareness** (delays между GigaChat calls)
   - **Structured output validation** (JSON fields, not exact text)
   - **Golden datasets** (synthetic responses как reference data)

---

## 📁 Location References

### Code Files:
- **InterviewerAgent:** `agents/interviewer_agent.py` или `agents/interactive_interviewer_v2.py`
- **AuditorAgent:** `agents/auditor_agent.py`
- **WriterAgent:** `agents/writer_agent.py`
- **Database:** `data/database/models.py`

### Test Files:
- **New E2E Test:** `tests/integration/test_e2e_full_flow.py` (создать)
- **Synthetic Data:** `tests/fixtures/synthetic_interview_responses.py` (создать)
- **Export Helpers:** `tests/integration/export_helpers.py` (создать)
- **Reference:** `tests/integration/test_write_two_grants.py` (Iteration 47)

### Output:
- **Iteration Folder:** `iterations/Iteration_50_E2E_Full_Flow/`
- **6 Files:** ANKETA_1_MEDIUM.txt, ANKETA_2_HIGH.txt, AUDIT_1_MEDIUM.txt, AUDIT_2_HIGH.txt, GRANT_1_MEDIUM.txt, GRANT_2_HIGH.txt

### Documentation:
- **Methodology:** `C:\SnowWhiteAI\cradle\Know-How\TESTING-METHODOLOGY.md`
- **GrantService Methodology:** `docs/TESTING-METHODOLOGY-GRANTSERVICE.md`

---

## ⚠️ Risks

1. **InterviewerAgent может не поддерживать синтетические ответы**
   - Mitigation: Изучить код, найти метод для программной подачи ответов
   - Fallback: Использовать готовые анкеты из Iteration 45/47

2. **GigaChat rate limit при последовательных вызовах**
   - Mitigation: Delays между фазами (6+ секунд)
   - Expected time: 20-30 minutes для полного теста

3. **AuditorAgent может не сохранять в БД автоматически**
   - Mitigation: Проверить метод `audit_anketa()`, добавить `save_to_db=True`
   - Fallback: Ручное сохранение после аудита

4. **WriterAgent требует research_data**
   - Mitigation: Передать пустой `research_data={}` (как в Iteration 47)
   - Fallback: Минимальный research_data если required

---

## 🚀 Quick Start

```bash
# 1. Создать папку итерации
mkdir -p iterations/Iteration_50_E2E_Full_Flow

# 2. Создать fixtures
# Редактировать: tests/fixtures/synthetic_interview_responses.py

# 3. Создать E2E тест
# Редактировать: tests/integration/test_e2e_full_flow.py

# 4. Запустить
python -m pytest tests/integration/test_e2e_full_flow.py -xvs

# 5. Проверить результаты
ls -lh iterations/Iteration_50_E2E_Full_Flow/*.txt
# Expected: 6 files (2 anketas + 2 audits + 2 grants)
```

---

## ✅ Checklist

**Planning:**
- [x] Create 00_ITERATION_PLAN.md
- [ ] Find InterviewerAgent code
- [ ] Find AuditorAgent code
- [ ] Understand DB save methods
- [ ] Design synthetic responses

**Execution:**
- [ ] Create synthetic_interview_responses.py
- [ ] Create test_e2e_full_flow.py
- [ ] Create export_helpers.py
- [ ] Phase 1: Interview (2 anketas created)
- [ ] Phase 2: Audit (2 audits created)
- [ ] Phase 3: Writer (2 grants created)
- [ ] All 6 files exported

**Validation:**
- [ ] Database records created (6 total)
- [ ] File content validation (not empty)
- [ ] Business logic validation (HIGH > MEDIUM)
- [ ] Production parity check

**Documentation:**
- [ ] Create ITERATION_50_SUMMARY.md
- [ ] Git commit
- [ ] Update README

---

**Status:** 🟡 READY TO START
**Next Step:** Find InterviewerAgent and analyze interview flow
**Created:** 2025-10-26
**Estimated Completion:** 2025-10-26 (same day, ~3 hours)
**Expected Result:** 6 текстовых файлов в `iterations/Iteration_50_E2E_Full_Flow/`
