# ✅ Pre-Deploy Checklist

**ПРИМЕНЯТЬ ПЕРЕД КАЖДЫМ DEPLOY!**

**Iteration:** _______
**Date:** _______
**Deployer:** _______

---

## 🔍 1. CODE REVIEW (5 минут)

### Git Diff:
```bash
git diff --cached
```

- [ ] Прочитал ВСЕ изменения построчно
- [ ] Понимаю каждое изменение
- [ ] Убрал debug код (print, console.log, etc.)
- [ ] Убрал закомментированный код
- [ ] Проверил TODO комментарии
- [ ] Убрал лишние пробелы и пустые строки

### Critical Questions:

#### Method Names:
- [ ] Правильные ли имена методов?
  - ⚠️ Проверить: не `generate_grant()` вместо `write()`?
  - ⚠️ Проверить: метод существует в классе?

#### Parameters:
- [ ] Правильные ли типы параметров?
  - ⚠️ Проверить: не `str` вместо `dict`?
  - ⚠️ Проверить: не `int` вместо `str`?

#### Parameter Names:
- [ ] Правильные ли имена параметров?
  - ⚠️ Проверить: `anketa_data` (dict) vs `anketa_id` (str)
  - ⚠️ Проверить: `user_id` vs `telegram_id`

#### Return Types:
- [ ] Правильные ли return types?
  - ⚠️ Проверить: что метод возвращает?
  - ⚠️ Проверить: соответствует ли использованию?

---

## 🗄️ 2. DATABASE CHANGES (если есть)

### SQL Queries:
- [ ] Проверил SQL syntax (no typos)
- [ ] Правильные column names:
  - ⚠️ `sessions` table → `telegram_id` (NOT user_id)
  - ⚠️ `grants` table → `user_id` (NOT telegram_id)
  - ⚠️ `users` table → check schema
- [ ] Есть WHERE clause (для UPDATE/DELETE)
- [ ] Проверил на тестовых данных (если возможно)

### Database Methods:
- [ ] Метод использует правильные column names
- [ ] Есть exception handling для DB errors
- [ ] Есть logging для ошибок

---

## 🔗 3. INTEGRATION POINTS (если есть)

### API Calls:
- [ ] Правильные имена методов API
  - ⚠️ ProductionWriter: `write()` NOT `generate_grant()`
  - ⚠️ ExpertAgent: check method names
  - ⚠️ GigaChat/Qdrant: check API methods

### Parameters:
- [ ] Правильные типы передаваемых параметров
  - ⚠️ Dict vs String
  - ⚠️ List vs String
  - ⚠️ Int vs String

### Return Values:
- [ ] Правильная обработка return values
  - ⚠️ String vs Dict
  - ⚠️ None handling
  - ⚠️ Error handling

---

## 🧪 4. LOCAL TESTING (10 минут)

### Run Tests:
```bash
pytest tests/ -v --tb=short
```

- [ ] Все существующие тесты проходят
- [ ] Новые тесты созданы (для критического кода)
- [ ] Проверил edge cases

### Manual Testing (если нет автоматических тестов):
- [ ] Проверил что новый код работает
- [ ] Проверил что не сломал старый код
- [ ] Проверил error cases

---

## 🛡️ 5. ERROR HANDLING

- [ ] Есть try/except для внешних вызовов:
  - Database queries
  - API calls (GigaChat, Qdrant)
  - File operations
  - Network operations

- [ ] Ошибки логируются:
  ```python
  logger.error(f"Error in method_name: {e}")
  ```

- [ ] Понятные error messages для пользователя:
  ```python
  await update.message.reply_text("❌ Произошла ошибка...")
  ```

---

## 📝 6. COMMIT MESSAGE

### Quality Check:
- [ ] Commit message осмысленное
- [ ] Описывает ЧТО и ЗАЧЕМ
- [ ] Формат: `<type>(iteration<N>): <description>`

### Good Examples:
```
fix(iteration34): Change ProductionWriter.generate_grant() to write()
feat(iteration35): Add interview completion logic
test(iteration35): Add tests for grant handler methods
```

### Bad Examples:
```
fix bug          ❌
update code      ❌
changes          ❌
```

---

## 🚀 7. DEPLOY (5 минут)

### Pre-Deploy:
- [ ] ВСЕ пункты 1-6 выполнены ✅
- [ ] Закоммитил изменения
- [ ] Запушил на GitHub

### Deploy Command:
```bash
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251 "cd /var/GrantService && git pull origin master && sudo systemctl restart grantservice-bot"
```

### Post-Deploy:
- [ ] Проверил logs на ошибки:
  ```bash
  ssh root@5.35.88.251 "sudo journalctl -u grantservice-bot --since '1 minute ago'"
  ```

- [ ] Проверил status сервиса:
  ```bash
  ssh root@5.35.88.251 "sudo systemctl status grantservice-bot --no-pager"
  ```

- [ ] Нет errors в логах (или понятно почему есть)

---

## 📊 8. POST-DEPLOY VERIFICATION

### Functional Test:
- [ ] Основной функционал работает
- [ ] Новая фича работает (если добавлена)
- [ ] User может использовать бот

### Performance:
- [ ] Сервис отвечает быстро
- [ ] Memory usage в норме
- [ ] No performance degradation

---

## 🐛 COMMON BUGS PREVENTION

### Based on Real History:

#### Iteration 34 Bug:
```
❌ Called: writer.generate_grant()
✅ Should call: writer.write()

Checklist catches this at:
→ "Правильные ли имена методов?"
→ "Метод существует в классе?"
```

#### Iteration 33 Bugs:
```
❌ Used: user_id in sessions table
✅ Should use: telegram_id

Checklist catches this at:
→ "Правильные column names?"
→ "sessions table → telegram_id"
```

#### Iteration 26.3:
```
❌ No exception handling
✅ Added try/except

Checklist catches this at:
→ "Есть try/except для внешних вызовов?"
```

---

## ⏱️ TIME INVESTMENT

| Step | Time | Value |
|------|------|-------|
| Code Review | 5 min | Catch method/param errors |
| Database Check | 2 min | Catch SQL errors |
| Integration Check | 2 min | Catch API errors |
| Local Testing | 10 min | Catch functional bugs |
| Error Handling | 2 min | Prevent production crashes |
| Commit Message | 1 min | Better git history |
| Deploy | 5 min | Safe deployment |
| **TOTAL** | **~30 min** | **Prevent 2-4 hours of debugging** |

**ROI:** 30 min investment → 2-4 hours saved = **400-800% ROI!**

---

## ✅ SUCCESS CRITERIA

### This checklist is successful if:

- ✅ Applied before EVERY deploy
- ✅ All items checked
- ✅ Bugs caught BEFORE production
- ✅ Production deploys succeed first time
- ✅ No emergency hotfixes needed

---

## 📈 TRACKING

### Record in CURRENT_STATUS.md:

```markdown
## Recent Iterations

### Iteration 34:
- Checklist applied: ✅ Yes
- All items checked: ✅ Yes
- Bugs caught: 0 (code already pushed)
- Deploy successful: ✅ Yes
- Post-deploy issues: 0

### Iteration 35:
- Checklist applied: ✅ Yes
- All items checked: ✅ Yes
- Bugs caught: 2 (parameter type, missing exception)
- Deploy successful: ✅ Yes
- Post-deploy issues: 0
```

---

## 🔄 CONTINUOUS IMPROVEMENT

### After Each Deployment:

1. **If bug found AFTER deploy:**
   - Add item to checklist to catch this type of bug
   - Update "Common Bugs Prevention" section

2. **If checklist caught bug BEFORE deploy:**
   - ✅ Success! Document in CURRENT_STATUS.md
   - Share learning with team/Cradle

3. **If step takes too long:**
   - Optimize the step
   - But DON'T skip it!

---

## 📞 QUICK REFERENCE

### Before EVERY commit:
1. Read git diff
2. Answer critical questions
3. Check error handling

### Before EVERY deploy:
1. Run through this checklist
2. Mark all items
3. Deploy ONLY when all ✅

### After EVERY deploy:
1. Check logs
2. Verify functionality
3. Document in CURRENT_STATUS.md

---

**Remember:**

💡 15 minutes of checking > 2 hours of debugging
💡 Checklist is not overhead, it's prevention
💡 Every bug caught before production = time saved

---

**Status:** READY TO USE
**Apply to:** Every iteration starting from Iteration 34
**Estimated time:** 15-30 minutes per deploy
**Expected result:** 0 preventable bugs in production

✅ **Use this checklist BEFORE your next deploy!**
