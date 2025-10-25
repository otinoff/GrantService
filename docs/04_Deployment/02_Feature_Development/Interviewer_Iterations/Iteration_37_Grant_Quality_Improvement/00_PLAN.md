# Iteration 37: Grant Application Quality Improvement

**Created:** 2025-10-25
**Type:** Feature Enhancement + Bug Fix
**Priority:** P0-CRITICAL
**Estimated Time:** 3-4 hours
**Methodology Principle:** Метаболизм (small improvements to Writer pipeline)

---

## 🎯 PROBLEM

**Current situation:**
Тестовая анкета получает очень низкие оценки от AuditorAgent:
- Общая оценка: **0.0/10**
- Полнота: **4.0/10**
- Ясность: **0/10**
- Выполнимость: **0/10**
- Инновационность: **0/10**
- Качество: **2.6/10**

**Рекомендации аудитора:**
1. Дополнить недостающие разделы: title, summary, implementation
2. Усилить разделы: title, summary, problem
3. Детализировать структуру бюджета
4. Усилить соответствие требованиям гранта

**Root Cause Analysis:**

Проверим 3 возможные причины:

**Гипотеза 1:** Тестовые данные в `/create_test_anketa` неполные
- Проверить: какие поля заполняет команда
- Сравнить с требованиями AuditorAgent

**Гипотеза 2:** AuditorAgent проверяет поля которых нет в анкете
- Проверить: что именно проверяет auditor
- Изучить промпты auditor_agent

**Гипотеза 3:** WriterAgent (если используется) генерирует плохо
- Проверить: как генерируется заявка
- Проверить промпты writer_agent

**Impact:**
- ❌ Пользователи не могут сгенерировать качественные заявки
- ❌ Audit блокирует `/generate_grant` при низком score
- ❌ Sber500 bootcamp: плохая демонстрация возможностей

---

## 🎯 SOLUTION

**Approach:**

### Phase 1: Диагностика (1 час)
1. **Проверить тестовые данные** в `create_test_anketa()`
   - Какие поля заполняются?
   - Что ожидает AuditorAgent?
   - Mapping между anketa fields и audit requirements

2. **Изучить AuditorAgent логику**
   - Какие критерии проверяются?
   - Промпты из БД (agent_prompts table)
   - Что означает каждая оценка (completeness, clarity, etc.)?

3. **Проверить ProductionWriter** (если используется)
   - Как генерируется заявка из анкеты?
   - Используются ли все поля анкеты?

### Phase 2: Улучшение данных (1 час)
1. **Дополнить `create_test_anketa()`**
   - Добавить недостающие поля
   - Более детальные ответы
   - Соответствие требованиям ФПГ

2. **Создать валидацию анкеты**
   - Проверка обязательных полей перед audit
   - Warning если данных недостаточно

### Phase 3: Улучшение Writer (1-2 часа)
1. **Проверить ProductionWriter промпты**
   - Генерирует ли title, summary, implementation?
   - Использует ли все разделы анкеты?

2. **Улучшить генерацию**
   - Добавить недостающие секции
   - Улучшить промпты для качества

### Phase 4: Тестирование (30 мин)
1. Создать новую тестовую анкету
2. Запустить audit
3. Проверить что оценка >7.0/10

**Why this approach:**
- Методичный анализ от данных к генерации
- Исправляем причину, а не симптомы
- Каждая фаза = отдельный commit (метаболизм)

---

## 📋 TASKS

### Phase 1: Диагностика ✅ COMPLETE
- [x] Task 1.1: Прочитать `create_test_anketa()` - какие поля? (15min)
- [x] Task 1.2: Прочитать AuditorAgent промпты из БД (15min)
- [x] Task 1.3: Mapping: anketa fields → audit criteria (15min)
- [x] Task 1.4: Проверить ProductionWriter (если используется) (15min)
- [x] Task 1.5: Создать диагностический отчёт (30min)

**ROOT CAUSE FOUND:** AuditorAgent ожидает форматированный текст заявки, но получает raw JSON анкеты!
**Report:** `01_DIAGNOSTIC_FINDINGS.md`

### Phase 2: Улучшение данных
- [ ] Task 2.1: Дополнить `create_test_anketa()` недостающими полями (30min)
- [ ] Task 2.2: Создать валидацию обязательных полей (30min)

### Phase 3: Улучшение Writer (если нужно)
- [ ] Task 3.1: Проверить Writer промпты (30min)
- [ ] Task 3.2: Добавить генерацию title, summary, implementation (30min)
- [ ] Task 3.3: Улучшить секции problem, budget (30min)

### Phase 4: Тестирование
- [ ] Task 4.1: Создать улучшенную тестовую анкету (10min)
- [ ] Task 4.2: Запустить `/audit_anketa` (10min)
- [ ] Task 4.3: Проверить score ≥7.0/10 (10min)

**Total estimated time:** 3-4 hours

---

## 📊 SUCCESS CRITERIA

**Must Have:**
- [x] Понятна причина низких оценок
- [ ] Тестовая анкета содержит все обязательные поля
- [ ] Audit score ≥7.0/10 для тестовых данных
- [ ] Валидация предупреждает о недостающих полях

**Nice to Have:**
- [ ] Audit score ≥8.5/10 (excellent)
- [ ] Automated validation перед audit
- [ ] Documentation: какие поля нужны для хорошей оценки

---

## 🔄 METHODOLOGY APPLICATION

**Which principle:**
- [x] Метаболизм (small frequent changes)
  - Phase 1 = understand
  - Phase 2 = improve data
  - Phase 3 = improve generation
  - Phase 4 = test
  - Each phase = separate commit

- [x] Гомеостаз (stability through testing)
  - Test after each phase
  - Validate before audit

**How applied:**
- Маленькие улучшения в несколько этапов
- Каждое улучшение тестируется
- Commit после каждой фазы

---

## 🐛 BUGS TO INVESTIGATE

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Audit score 0.0/10 для тестовых данных | High | Investigating |
| 2 | Missing fields: title, summary, implementation | High | To Fix |
| 3 | Ясность/Выполнимость/Инновационность = 0/10 | High | To Fix |

---

## ⏱️ TIME TRACKING

| Task | Estimated | Actual | Notes |
|------|-----------|--------|-------|
| Phase 1: Диагностика | 1h | | |
| Phase 2: Улучшение данных | 1h | | |
| Phase 3: Улучшение Writer | 1-2h | | |
| Phase 4: Тестирование | 30min | | |
| **Total** | **3.5-4h** | | |

---

## 📝 DIAGNOSTIC PLAN

### Step 1: Проверить что в тестовой анкете
```python
# Прочитать C:\SnowWhiteAI\GrantService\telegram-bot\handlers\anketa_management_handler.py
# Функция create_test_anketa()
# Список полей:
```

### Step 2: Проверить что проверяет Auditor
```sql
-- Промпты из БД
SELECT prompt_key, prompt_text
FROM agent_prompts
WHERE agent_type = 'auditor';
```

### Step 3: Mapping
```
Anketa Field          → Audit Criterion
--------------------- → -----------------
project_name          → title?
project_description   → summary?
problem               → problem section
budget                → budget section
...
```

---

## 🔗 RELATED

**Previous iteration:** Iteration 36 - Methodology Cleanup ✅
**Related:** Iteration 35 - Anketa Management (audit integration)

**Methodology:**
- Template: `@Development/ITERATION_TEMPLATE.md` ✅
- Principles: Метаболизм (small changes) + Гомеостаз (testing)

**Files to check:**
- `telegram-bot/handlers/anketa_management_handler.py:745-883` (create_test_anketa)
- `agents/auditor_agent.py` (audit logic)
- Database: `agent_prompts` table
- `agents/production_writer.py` (if used for generation)

---

## 🚀 QUICK START

**Step 1: Начать диагностику**
```bash
# Прочитать create_test_anketa
code telegram-bot/handlers/anketa_management_handler.py:745

# Проверить БД промпты
PGPASSWORD=root psql -h localhost -p 5432 -U postgres -d grantservice -c "SELECT prompt_key FROM agent_prompts WHERE agent_type='auditor';"
```

**Step 2: После диагностики - улучшить**

**Step 3: Тестировать**
```
/create_test_anketa
/audit_anketa
→ Check score ≥7.0/10
```

---

## ✅ PRE-DEPLOY CHECKLIST

(Use after implementation)

- [ ] All tasks completed
- [ ] Audit score ≥7.0/10 for test data
- [ ] Tests pass
- [ ] Documentation updated

Reference: `@Development/PRE_DEPLOY_CHECKLIST.md`

---

**Template Used:** ITERATION_TEMPLATE.md v1.0 ✅
**Created:** 2025-10-25
**Status:** 📋 READY TO START
**Methodology:** Project Evolution (Метаболизм + Гомеостаз)
