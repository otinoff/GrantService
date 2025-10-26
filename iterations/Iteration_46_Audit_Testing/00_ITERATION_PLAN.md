# Iteration 46: Audit Testing - План

**Дата создания:** 2025-10-26
**Статус:** 🟡 IN PROGRESS
**Предыдущая итерация:** Iteration 45 - Full Flow Testing ✅
**Цель:** Протестировать аудит двух анкет (MEDIUM и HIGH quality) и проверить корректность scoring logic

---

## 🎯 Sprint Goal

> **Протестировать auditor_agent на двух готовых анкетах из Iteration 45 и выяснить, почему audit_score = 8.46/100 (слишком низкий).**

**Success Criteria:**
- ✅ 2 аудита выполнены (для MEDIUM и HIGH качества)
- ✅ Получены детальные audit reports с breakdown по критериям
- ✅ Выявлена причина низкого scoring (8.46/100 вместо 60-80/100)
- ✅ Документированы рекомендации по улучшению
- ✅ Результаты сохранены в БД (PostgreSQL `audit_results`)

---

## 📋 Задачи (Tasks)

### 1. Pre-Flight Checks (5 min) ⏸️
- [ ] PostgreSQL доступна (audit_results table exists?)
- [ ] GigaChat API работает (token valid)
- [ ] Qdrant доступен (философия для аудита)
- [ ] Есть доступ к dialog_history из Iteration 45

### 2. Подготовка данных (10 min) ⏸️
- [ ] Извлечь dialog_history для Interview #1 из БД
- [ ] Извлечь dialog_history для Interview #2 из БД
- [ ] Проверить формат данных для auditor_agent

### 3. Запуск аудита (20 min) ⏸️
- [ ] Запустить auditor_agent для Interview #1 (MEDIUM)
- [ ] Запустить auditor_agent for Interview #2 (HIGH)
- [ ] Сохранить полные audit reports

### 4. Анализ результатов (15 min) ⏸️
- [ ] Сравнить scores: MEDIUM vs HIGH (ожидаем HIGH > MEDIUM)
- [ ] Проанализировать breakdown по критериям
- [ ] Найти причину низкого scoring (8.46/100)
- [ ] Документировать findings

### 5. Документация (10 min) ⏸️
- [ ] Создать AUDIT_RESULTS.md с подробными отчётами
- [ ] Обновить ITERATION_46_SUMMARY.md
- [ ] Git commit

**Estimated Time:** ~60 min (1 hour)

---

## 🔄 Методология: 5-Step Workflow

### STEP 1: PLAN (15% = 9 min) ✅ CURRENT
- [x] Создать 00_ITERATION_PLAN.md
- [ ] Оценить capacity (80% features / 20% tech debt)
- [ ] Определить success criteria

### STEP 2: DEVELOP (Daily commits)
- [ ] Написать test script `test_audit_two_anketas.py`
- [ ] Запустить аудит для двух интервью
- [ ] Проанализировать результаты

### STEP 3: INTEGRATE (CI checks)
- [ ] Валидация результатов
- [ ] Проверка сохранения в БД

### STEP 4: DEPLOY
- N/A (тестовая итерация)

### STEP 5: MEASURE (Metrics)
- [ ] Audit scores (MEDIUM vs HIGH)
- [ ] Scoring breakdown по критериям
- [ ] Execution time

---

## 📊 Ожидаемые метрики

### Audit Scores (гипотеза):
```
MEDIUM quality: 50-60/100 (базовый уровень)
HIGH quality:   70-80/100 (хорошая заявка)

Actual (Iteration 45): 8.46/100 ❌ (требует расследования!)
```

### Критерии оценки (из auditor_agent):
- Полнота информации (completeness)
- Конкретность данных (specificity)
- Обоснованность (justification)
- Реалистичность бюджета (budget realism)
- Команда и опыт (team experience)
- Социальная значимость (social impact)

### Execution time:
```
Target: <30s per audit
Acceptable: <60s per audit
```

---

## 🎓 Learning Goals

1. **Понять auditor_agent logic:**
   - Как вычисляется итоговый score?
   - Какие критерии имеют наибольший вес?
   - Почему 8.46/100 вместо 60-80/100?

2. **Валидация качества:**
   - HIGH quality получает больше баллов, чем MEDIUM? ✅
   - Аудит детектит отсутствие конкретики в MEDIUM? ✅

3. **Improvement opportunities:**
   - Нужно ли калибровать scoring weights?
   - Нужно ли добавить новые критерии?
   - Нужно ли изменить threshold для "допуска к гранту"?

---

## 🔗 Связь с Iteration 45

**Input data:**
- `sessions.dialog_history` (JSONB) - 2 интервью
- Interview #1: Новосибирск, MEDIUM quality
- Interview #2: Екатеринбург, HIGH quality

**Reuse:**
- Те же анкеты, что успешно прошли Full Flow Test
- Уже в БД, не нужно генерировать заново

---

## 📁 Deliverables

### Code:
- `scripts/test_audit_two_anketas.py` - тестовый скрипт

### Data:
- `audit_report_interview_1_medium.json`
- `audit_report_interview_2_high.json`
- PostgreSQL `audit_results` table (2 records)

### Documentation:
- `00_ITERATION_PLAN.md` (этот файл)
- `AUDIT_RESULTS.md` - детальные отчёты
- `ITERATION_46_SUMMARY.md` - итоги

---

## ⚠️ Риски

1. **Auditor agent может не работать:**
   - Mitigation: Pre-flight checks + fallback to manual analysis

2. **Scoring logic может быть некорректной:**
   - Expected: Это именно то, что мы хотим выявить!
   - Mitigation: Документировать findings для будущего фикса

3. **БД может не иметь таблицы audit_results:**
   - Mitigation: Создать таблицу или сохранить в JSON

---

## 🚀 Quick Start

```bash
# 1. Pre-Flight Checks
python scripts/test_audit_two_anketas.py --mode preflight

# 2. Run Audit
python scripts/test_audit_two_anketas.py --interview 1 --interview 2

# 3. Analyze Results
python scripts/test_audit_two_anketas.py --mode analyze
```

---

## 📌 References

- **Testing Methodology:** `docs/TESTING-METHODOLOGY-GRANTSERVICE.md`
- **Previous Iteration:** `iterations/Iteration_45_Full_Flow_Testing/`
- **Auditor Agent:** `agents/auditor_agent.py`
- **Anketas:**
  - `iterations/Iteration_45_Full_Flow_Testing/INTERVIEW_1_ANKETA_MEDIUM_QUALITY.txt`
  - `iterations/Iteration_45_Full_Flow_Testing/INTERVIEW_2_ANKETA_HIGH_QUALITY.txt`

---

## ✅ Checklist

**Planning:**
- [x] Create 00_ITERATION_PLAN.md
- [ ] Read auditor_agent.py to understand scoring logic
- [ ] Define test script structure

**Execution:**
- [ ] Pre-Flight Checks
- [ ] Extract dialog_history from DB
- [ ] Run audit for Interview #1
- [ ] Run audit for Interview #2
- [ ] Compare results

**Documentation:**
- [ ] Create AUDIT_RESULTS.md
- [ ] Create ITERATION_46_SUMMARY.md
- [ ] Git commit

---

**Status:** 🟡 READY TO START
**Next Step:** Pre-Flight Checks + Read auditor_agent.py
**Created:** 2025-10-26
