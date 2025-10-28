# Iteration Workflow - Complete Guide

**Дата:** 2025-10-29
**Источник:** Iterations 60-62 опыт
**Статус:** ✅ Production-tested

---

## 🎯 Полный цикл Iteration

```
PLAN (15%) → DEVELOP (60%) → TEST (15%) → DEPLOY (5%) → DOCUMENT (5%)
```

**Total time:** 15-60 минут для hotfix, 2-8 часов для feature

---

## 📝 Phase 1: PLAN (15%)

### 1.1 Создать директорию iteration

```bash
mkdir iterations/Iteration_XX_Feature_Name
cd iterations/Iteration_XX_Feature_Name
```

**Naming convention:**
- `Iteration_XX` - порядковый номер (60, 61, 62...)
- `Feature_Name` - CamelCase описание (`Fix_Research_Results_Parsing`)

### 1.2 Создать 00_PLAN.md

**Template:**
```markdown
# Iteration XX: Feature Name

**Date:** YYYY-MM-DD HH:MM MSK
**Status:** 🔧 IN PROGRESS
**Priority:** 🔥 CRITICAL / ⚡ HIGH / 📋 MEDIUM / 💡 LOW
**Parent:** Iteration YY - Parent Feature (если есть)

---

## 🐛 Problem / 🎯 Goal

[Описание проблемы или цели]

**User Report:** [Если есть]
**Root Cause:** [Если найден]

---

## 📊 Impact

### Before Fix:
- [Что не работает]
- [Проблемы пользователей]

### After Fix:
- [Что будет работать]
- [Улучшения]

---

## 🎯 Solution

### Step 1: [Название шага]

**File:** `path/to/file.py`

**Change:**
\```python
# BEFORE:
old_code

# AFTER:
new_code
\```

---

## 📝 Implementation Plan

### Phase 1: Code Fix (X min)
- [ ] Task 1
- [ ] Task 2

### Phase 2: Testing (X min)
- [ ] Test 1
- [ ] Test 2

### Phase 3: Deployment (X min)
- [ ] Deploy step 1
- [ ] Deploy step 2

---

## ✅ Success Criteria

- [ ] Criteria 1
- [ ] Criteria 2
- [ ] User verification

---

## 📁 Files to Modify

**Modified:**
1. `file1.py` - description
2. `file2.py` - description

**Created:**
3. `iterations/Iteration_XX/00_PLAN.md`
4. `iterations/Iteration_XX/SUCCESS.md`

---

## 📅 Timeline

**Start:** YYYY-MM-DD HH:MM MSK
**Estimated:** XX minutes
**ETA:** YYYY-MM-DD HH:MM MSK
```

### 1.3 Анализ проблемы

**Шаги:**
1. Прочитать user report / issue
2. Найти affected files (grep, search)
3. Понять data flow (откуда → куда данные)
4. Локализовать root cause (конкретная строка кода)
5. Разработать solution (минимальное изменение)

**Tools:**
```bash
# Поиск по коду
grep -r "функция_название" .

# Поиск по файлам
find . -name "*keyword*"

# История изменений
git log --oneline -n 20
git show commit_hash
```

---

## 💻 Phase 2: DEVELOP (60%)

### 2.1 Создать ветку (опционально)

```bash
git checkout -b iteration-xx-feature-name
```

**Или работать в master** (для hotfix)

### 2.2 Применить изменения

**Читаем файл:**
```bash
# Claude Code - используй Read tool
Read(file_path="path/to/file.py")
```

**Применяем Edit:**
```bash
# Claude Code - используй Edit tool
Edit(
    file_path="path/to/file.py",
    old_string="старый код",
    new_string="новый код"
)
```

**Best practices:**
- ✅ Делай минимальные изменения
- ✅ Добавляй комментарии с номером iteration
- ✅ Сохраняй форматирование кода
- ✅ Не меняй несвязанный код

**Example:**
```python
# ITERATION 62 FIX: Extract answer from nested 'result.summary'
result = query_data.get('result', {})
answer = result.get('summary', 'N/A')
```

### 2.3 Проверить изменения

```bash
git diff
```

**Проверить:**
- [ ] Только нужные файлы изменены
- [ ] Нет случайных изменений (whitespace, форматирование)
- [ ] Комментарии добавлены
- [ ] Синтаксис корректен

---

## 🧪 Phase 3: TEST (15%)

### 3.1 Local Testing

**Unit test (если применимо):**
```bash
pytest tests/unit/test_feature.py -v
```

**Integration test:**
```bash
pytest tests/integration/test_workflow.py -v
```

**Manual test:**
1. Запустить локально
2. Воспроизвести bug/scenario
3. Проверить что fix работает

### 3.2 Smoke Test

```python
# Быстрая проверка основной функции
def test_smoke():
    result = function_with_fix()
    assert result is not None
    assert result != 'N/A'  # Не default value
```

### 3.3 Edge Cases

Проверить:
- [ ] Пустые данные (`{}`, `[]`, `None`)
- [ ] Отсутствующие ключи в dict
- [ ] Неправильный тип данных
- [ ] Очень большие данные

---

## 🚀 Phase 4: DEPLOY (5%)

### 4.1 Git Commit

```bash
# Stage files
git add file1.py file2.py iterations/Iteration_XX/

# Commit with message
git commit -m "fix(component): Short description (Iteration XX)

- Detail 1
- Detail 2
- Detail 3

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"

# Push
git push origin master  # или branch
```

**Commit message format:**
- `fix(component):` - bug fix
- `feat(component):` - new feature
- `refactor(component):` - code refactoring
- `docs:` - documentation only
- `test:` - tests only

### 4.2 Production Deployment

**Pre-deployment check:**
```bash
# Check production git status
ssh root@5.35.88.251 "cd /var/GrantService && git status"
```

**If clean:**
```bash
ssh root@5.35.88.251 "cd /var/GrantService && git pull origin master"
```

**If dirty (local changes):**
```bash
ssh root@5.35.88.251 "cd /var/GrantService && git stash && git pull origin master"
```

**Restart service:**
```bash
ssh root@5.35.88.251 "systemctl restart grantservice-bot"
```

**Check status:**
```bash
ssh root@5.35.88.251 "systemctl status grantservice-bot --no-pager -l"
```

**Expected:**
```
● grantservice-bot.service
     Active: active (running)
     Memory: ~100M
```

### 4.3 Production Verification

**Check logs:**
```bash
ssh root@5.35.88.251 "journalctl -u grantservice-bot -n 50 --no-pager"
```

**Look for:**
- ✅ `Application started`
- ✅ No critical errors
- ✅ Handlers initialized
- ❌ Tracebacks, exceptions

**Functional test:**
1. Telegram bot отвечает
2. Базовая операция работает
3. Fix применён (проверить конкретную функцию)

---

## 📄 Phase 5: DOCUMENT (5%)

### 5.1 Создать SUCCESS.md

**Template:**
```markdown
# Iteration XX: Feature Name - SUCCESS

**Date:** YYYY-MM-DD HH:MM MSK
**Duration:** XX minutes
**Status:** ✅ DEPLOYED TO PRODUCTION

---

## 🎯 Problem Solved

[Краткое описание проблемы]

**Solution:** [Краткое описание решения]

---

## 📝 Changes Made

### File 1: `path/to/file.py`

**Lines XX-YY:**

**BEFORE:**
\```python
old_code
\```

**AFTER:**
\```python
new_code
\```

---

## ✅ Deployment Steps

### 1. Code Changes
- [x] Fixed file1.py
- [x] Updated file2.py

### 2. Git Commit & Push
\```bash
git add ...
git commit -m "..."
git push origin master
\```

**Commit:** `hash`

### 3. Production Deployment
\```bash
ssh root@5.35.88.251
cd /var/GrantService
git pull origin master
systemctl restart grantservice-bot
\```

**Bot Status:** active (running)

---

## 📊 Impact

**Before:**
- [Что не работало]

**After:**
- [Что теперь работает]

---

## ✅ Verification Checklist

- [x] Code deployed
- [x] Bot restarted
- [x] No errors in logs
- [ ] User verification (pending)

---

## 🔗 Related Iterations

**Parent:** Iteration YY
**This:** Iteration XX
**Next:** Iteration ZZ (planned)

---

**Created by:** Claude Code
**Date:** YYYY-MM-DD HH:MM MSK
**Status:** ✅ DEPLOYED
```

### 5.2 Update project tracking

**Update files:**
- `SESSION_YYYY-MM-DD.md` - add iteration to session log
- `README.md` - update current iteration (if major)
- `knowhow/` - add lessons learned (if applicable)

### 5.3 Notify team

**If production deployment:**
- Уведомить пользователей о fix/feature
- Обновить changelog
- Написать в чат команды

---

## ⚡ Quick Reference

### Hotfix (15-30 min)

```bash
# 1. PLAN (5 min)
mkdir iterations/Iteration_XX
vim iterations/Iteration_XX/00_PLAN.md

# 2. DEVELOP (10 min)
# Apply fix using Claude Code tools

# 3. DEPLOY (5 min)
git add . && git commit -m "fix: ..." && git push
ssh root@5.35.88.251 "cd /var/GrantService && git pull && systemctl restart grantservice-bot"

# 4. DOCUMENT (5 min)
vim iterations/Iteration_XX/SUCCESS.md
```

### Feature (2-8 hours)

```bash
# 1. PLAN (30 min)
# Research, design, write detailed plan

# 2. DEVELOP (1-6 hours)
# Implement, write tests, refactor

# 3. TEST (30 min)
pytest tests/

# 4. DEPLOY (15 min)
# Git workflow, production deployment

# 5. DOCUMENT (15 min)
# SUCCESS.md, knowhow, session log
```

---

## 📋 Checklists

### Pre-Commit Checklist

- [ ] Code changes are minimal
- [ ] Comments added (with iteration number)
- [ ] No unrelated changes
- [ ] `git diff` reviewed
- [ ] Syntax correct (no obvious errors)

### Pre-Deployment Checklist

- [ ] Tests passing (if applicable)
- [ ] Git commit done
- [ ] Git push successful
- [ ] Production git status checked
- [ ] Backup plan ready (git revert)

### Post-Deployment Checklist

- [ ] Bot restarted successfully
- [ ] No errors in logs
- [ ] Functional test passed
- [ ] SUCCESS.md created
- [ ] Team notified (if needed)

---

## 🎯 Iteration Metrics

**Track for improvement:**
- **Planning time:** Сколько времени на анализ и plan
- **Development time:** Coding + testing
- **Deployment time:** Git + production deploy
- **Total time:** От создания PLAN.md до SUCCESS.md

**Iteration 62 example:**
- Planning: 3 min
- Development: 5 min
- Deployment: 10 min (с SSH troubleshooting)
- Documentation: 7 min
- **Total: 25 minutes** (hotfix)

---

## 💡 Best Practices

### 1. Start small

- ✅ Minimal viable fix
- ✅ Single responsibility per iteration
- ❌ Don't combine unrelated changes

### 2. Document immediately

- ✅ Write 00_PLAN.md before coding
- ✅ Write SUCCESS.md right after deploy
- ❌ Don't wait until "later"

### 3. Test before deploy

- ✅ At least smoke test locally
- ✅ Integration test if possible
- ❌ Don't deploy untested code

### 4. Deploy incrementally

- ✅ Deploy one iteration at a time
- ✅ Verify each deployment
- ❌ Don't deploy multiple iterations without testing

### 5. Learn and improve

- ✅ Add to knowhow/ if reusable
- ✅ Update methodology based on experience
- ❌ Don't repeat same mistakes

---

## 🔗 Related Knowhow

- `knowhow/DEPLOYMENT_SSH_PRACTICES.md` - SSH deployment details
- `knowhow/DATA_STRUCTURE_DEBUGGING.md` - Debugging nested data
- `cradle/PROJECT-EVOLUTION-METHODOLOGY.md` - High-level methodology
- `cradle/GRANTSERVICE-LESSONS-LEARNED.md` - Project-specific lessons

---

## 🧪 Example: Iteration 62

**Problem:** Research results showing N/A instead of real data

**Timeline:**
- 01:05 - Created 00_PLAN.md (3 min)
- 01:08 - Applied fix to file_generators.py (5 min)
- 01:10 - Git commit & push (2 min)
- 01:15 - Production deployment (5 min, with SSH troubleshooting)
- 01:20 - Created SUCCESS.md (5 min)
- 01:25 - Created knowhow docs (15 min)
- **Total: 35 minutes** (including documentation)

**Files changed:** 1 file modified, 2 docs created, 625 lines added

**Result:** ✅ Critical bug fixed, deployed, documented

---

**Автор:** Claude Code
**Дата:** 2025-10-29
**Source:** Iterations 60-62 experience
**Status:** ✅ Living document (continuously updated)
