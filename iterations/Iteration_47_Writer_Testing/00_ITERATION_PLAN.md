# Iteration 47: Writer Agent Testing - План

**Дата создания:** 2025-10-26
**Статус:** 🟡 IN PROGRESS
**Предыдущая итерация:** Iteration 46 - Audit Testing ✅
**Цель:** Протестировать writer_agent на двух анкетах и сгенерировать 2 PDF грантовые заявки

---

## 🎯 Sprint Goal

> **Запустить writer_agent на двух готовых анкетах (MEDIUM и HIGH quality) и сгенерировать 2 PDF грантовые заявки.**

**Success Criteria:**
- ✅ 2 грантовые заявки сгенерированы (для MEDIUM и HIGH качества)
- ✅ 2 PDF файла созданы и сохранены
- ✅ HIGH заявка детальнее и качественнее MEDIUM
- ✅ Результаты сохранены в БД (PostgreSQL `grant_applications`)
- ✅ Использован GigaChat-Pro (2M токенов доступно)

---

## 📋 Задачи (Tasks)

### 1. Pre-Flight Checks (5 min) ⏸️
- [ ] PostgreSQL доступна (grant_applications table exists?)
- [ ] GigaChat Pro API работает (2M tokens available)
- [ ] Writer Agent доступен (agents/writer_agent.py)
- [ ] PDF генератор работает (StageReportGenerator)

### 2. Подготовка данных (10 min) ⏸️
- [ ] Извлечь anketa + audit результаты для Interview #1
- [ ] Извлечь anketa + audit результаты для Interview #2
- [ ] Проверить формат данных для writer_agent

### 3. Запуск генерации (30 min) ⏸️
- [ ] Запустить writer_agent для Interview #1 (MEDIUM)
- [ ] Запустить writer_agent для Interview #2 (HIGH)
- [ ] Сохранить полные grant applications

### 4. Генерация PDF (15 min) ⏸️
- [ ] Сгенерировать PDF для Grant #1 (MEDIUM)
- [ ] Сгенерировать PDF для Grant #2 (HIGH)
- [ ] Сохранить в iterations/Iteration_47_Writer_Testing/

### 5. Анализ результатов (15 min) ⏸️
- [ ] Сравнить качество: MEDIUM vs HIGH
- [ ] Проверить детальность и структуру
- [ ] Документировать findings

### 6. Документация (10 min) ⏸️
- [ ] Создать ITERATION_47_SUMMARY.md
- [ ] Git commit

**Estimated Time:** ~85 min (1.5 hours)

---

## 🔄 Методология: 5-Step Workflow

### STEP 1: PLAN (15% = 13 min) ✅ CURRENT
- [x] Создать 00_ITERATION_PLAN.md
- [ ] Оценить capacity (80% features / 20% tech debt)
- [ ] Определить success criteria

### STEP 2: DEVELOP (Daily commits)
- [ ] Написать test script `test_write_two_grants.py`
- [ ] Запустить writer для двух интервью
- [ ] Сгенерировать PDF

### STEP 3: INTEGRATE (CI checks)
- [ ] Валидация PDF файлов
- [ ] Проверка сохранения в БД

### STEP 4: DEPLOY
- N/A (тестовая итерация)

### STEP 5: MEASURE (Metrics)
- [ ] Grant quality (MEDIUM vs HIGH)
- [ ] PDF generation time
- [ ] Token usage (GigaChat Pro)

---

## 📊 Ожидаемые метрики

### Grant Quality (гипотеза):
```
MEDIUM quality:
  - Базовая структура
  - Меньше деталей в бюджете и команде
  - Короче (10-15 страниц PDF)

HIGH quality:
  - Детальная структура
  - Полный бюджет с обоснованием
  - Подробная команда
  - Длиннее (20-30 страниц PDF)
```

### Execution time:
```
Target: <5 минут per grant
Acceptable: <10 минут per grant
```

### GigaChat Pro usage:
```
Tokens per grant: ~50K-100K tokens
Total: ~100K-200K tokens (из 2M available)
```

---

## 🎓 Learning Goals

1. **Понять writer_agent logic:**
   - Как формируется структура заявки?
   - Какие секции генерируются?
   - Как используются данные из аудита?

2. **Валидация качества:**
   - HIGH quality создаёт более детальную заявку? ✅
   - Writer использует рекомендации аудита? ✅

3. **Improvement opportunities:**
   - Нужно ли добавить новые секции?
   - Нужно ли улучшить промпты?
   - Нужно ли изменить формат PDF?

---

## 🔗 Связь с Iteration 46

**Input data:**
- `iterations/Iteration_45_Full_Flow_Testing/INTERVIEW_1_ANKETA_MEDIUM_QUALITY.txt`
- `iterations/Iteration_45_Full_Flow_Testing/INTERVIEW_2_ANKETA_HIGH_QUALITY.txt`
- Audit results from Iteration 46 (score, recommendations)

**Reuse:**
- Те же анкеты, что прошли Audit Testing
- Результаты аудита используются как контекст для writer

---

## 📁 Deliverables

### Code:
- `tests/integration/test_write_two_grants.py` - тестовый скрипт

### Data:
- `grant_application_medium.pdf`
- `grant_application_high.pdf`
- PostgreSQL `grant_applications` table (2 records)

### Documentation:
- `00_ITERATION_PLAN.md` (этот файл)
- `ITERATION_47_SUMMARY.md` - итоги

---

## ⚠️ Риски

1. **Writer agent может не работать:**
   - Mitigation: Pre-flight checks + fallback to manual generation

2. **PDF generator может не работать:**
   - Mitigation: Сохранить в Markdown/HTML как fallback

3. **GigaChat Pro rate limit:**
   - Mitigation: Использовать последовательные запросы (не параллельные)

4. **Размер заявки слишком большой:**
   - Mitigation: Ограничить длину секций в промптах

---

## 🚀 Quick Start

```bash
# 1. Pre-Flight Checks
python tests/integration/test_write_two_grants.py --mode preflight

# 2. Run Writer
python -m pytest tests/integration/test_write_two_grants.py -v -s

# 3. Check PDFs
ls iterations/Iteration_47_Writer_Testing/*.pdf
```

---

## 📌 References

- **Testing Methodology:** `docs/TESTING-METHODOLOGY-GRANTSERVICE.md`
- **Previous Iteration:** `iterations/Iteration_46_Audit_Testing/`
- **Writer Agent:** `agents/writer_agent.py`
- **Anketas:**
  - `iterations/Iteration_45_Full_Flow_Testing/INTERVIEW_1_ANKETA_MEDIUM_QUALITY.txt`
  - `iterations/Iteration_45_Full_Flow_Testing/INTERVIEW_2_ANKETA_HIGH_QUALITY.txt`

---

## ✅ Checklist

**Planning:**
- [x] Create 00_ITERATION_PLAN.md
- [ ] Read writer_agent.py to understand generation logic
- [ ] Define test script structure

**Execution:**
- [ ] Pre-Flight Checks
- [ ] Load anketa data + audit results
- [ ] Run writer for Interview #1
- [ ] Run writer for Interview #2
- [ ] Generate 2 PDFs
- [ ] Compare results

**Documentation:**
- [ ] Create ITERATION_47_SUMMARY.md
- [ ] Git commit

---

**Status:** 🟡 READY TO START
**Next Step:** Create test_write_two_grants.py
**Created:** 2025-10-26
