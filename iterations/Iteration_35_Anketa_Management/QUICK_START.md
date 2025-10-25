# Iteration 35 - Quick Start Guide

**Время:** 4-6 часов
**Разработка:** Локально (БЕЗ deploy сегодня!)
**Методология:** Cradle OS ✅

---

## 🎯 ЧТО ДЕЛАЕМ

### 4 новые команды для Telegram бота:

1. **`/my_anketas`** - Список всех анкет пользователя
2. **`/delete_anketa`** - Удаление анкеты с подтверждением
3. **`/audit_anketa`** - Аудит качества анкеты
4. **Integration** - Проверка аудита в `/generate_grant`

---

## 📋 ПЛАН РАБОТЫ (по Cradle Methodology)

### ✅ Сегодня сделано:
- [x] План создан (`00_Plan.md`)
- [x] Архитектура спроектирована
- [x] Методология применена

### 🔄 Следующие шаги (в следующую сессию):

#### Phase 1: Database (1 час)
```
File: data/database/models.py

Add methods:
- get_user_anketas()
- delete_anketa()
- get_audit_by_session_id()
- get_audit_by_anketa_id()
```

#### Phase 2: Bot Handler (2-3 часа)
```
File: telegram-bot/handlers/anketa_management_handler.py (NEW)

Implement:
- my_anketas command
- delete_anketa command
- audit_anketa command
- callback handlers
```

#### Phase 3: Integration (1 час)
```
File: telegram-bot/handlers/grant_handler.py

Add:
- Audit check before generation
- Block if rejected
- Warn if needs_revision
```

#### Phase 4: Tests (1 час)
```
File: tests/test_anketa_management.py (NEW)

Write:
- Unit tests for DB methods
- Integration tests for commands
- Manual testing checklist
```

---

## 🧬 МЕТОДОЛОГИЯ CRADLE

### Принципы которые применяем:

**1. Гомеостаз (Testing):**
- ✅ Пишем тесты ПЕРЕД deploy
- ✅ Тестируем локально
- ✅ Pre-Deploy Checklist обязателен

**2. Метаболизм (Small Changes):**
- ✅ 4 команды = 4 малых фичи
- ✅ Поэтапная разработка
- ✅ Частые коммиты

**3. Иммунитет (Quality Control):**
- ✅ Auditor интеграция
- ✅ Code review перед deploy
- ✅ Error handling везде

---

## 📂 СТРУКТУРА ФАЙЛОВ

```
Iteration_35_Anketa_Management/
├── 00_Plan.md ✅ (готов)
├── QUICK_START.md ✅ (этот файл)
├── 01_Implementation/ (создать)
│   ├── anketa_management_handler.py
│   ├── database_methods.py
│   └── grant_handler_integration.py
├── 02_Tests/ (создать)
│   └── test_anketa_management.py
└── 03_Report.md (после завершения)
```

---

## 🚀 КАК НАЧАТЬ (следующая сессия)

### Step 1: Setup (5 мин)
```bash
cd C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\Iteration_35_Anketa_Management

# Создать папки
mkdir 01_Implementation
mkdir 02_Tests
```

### Step 2: Database Methods (1 час)
- Открыть `00_Plan.md`
- Скопировать код методов
- Добавить в `data/database/models.py`
- Сохранить

### Step 3: Bot Handler (2-3 часа)
- Создать `telegram-bot/handlers/anketa_management_handler.py`
- Скопировать код из плана
- Адаптировать под проект
- Сохранить

### Step 4: Integration (1 час)
- Открыть `telegram-bot/handlers/grant_handler.py`
- Добавить audit check
- Сохранить

### Step 5: Register Commands (15 мин)
```python
# In telegram-bot/main.py

from handlers.anketa_management_handler import AnketaManagementHandler

# Create handler
anketa_handler = AnketaManagementHandler(db)

# Register commands
app.add_handler(CommandHandler('my_anketas', anketa_handler.my_anketas))
app.add_handler(CommandHandler('delete_anketa', anketa_handler.delete_anketa))
app.add_handler(CommandHandler('audit_anketa', anketa_handler.audit_anketa))
app.add_handler(CallbackQueryHandler(anketa_handler.callback_handler))
```

### Step 6: Local Testing (1 час)
```bash
# Run bot locally
python telegram-bot/main.py

# Test commands:
/my_anketas
/delete_anketa
/audit_anketa
/generate_grant
```

### Step 7: Write Tests (1 час)
- Создать `tests/test_anketa_management.py`
- Написать unit tests
- Запустить: `pytest tests/test_anketa_management.py`

---

## ✅ PRE-DEPLOY CHECKLIST (применить ПЕРЕД deploy)

### 1. Code Review (5 мин)
- [ ] Прочитать все изменения
- [ ] Проверить имена методов
- [ ] Проверить типы параметров
- [ ] Проверить SQL column names
- [ ] Убрать debug код

### 2. Testing (10 мин)
- [ ] Все unit tests прошли
- [ ] Локальное тестирование прошло
- [ ] Проверены edge cases

### 3. Database (5 мин)
- [ ] SQL queries правильные
- [ ] Column names правильные
- [ ] CASCADE delete настроен

### 4. Integration (5 мин)
- [ ] Audit check работает
- [ ] Block/warn логика правильная
- [ ] Error handling везде

### 5. Deploy (5 мин)
- [ ] Git commit
- [ ] Git push
- [ ] Deploy to production
- [ ] Check logs

---

## 🎯 SUCCESS CRITERIA

### Must Have:
- [x] Plan ready ✅
- [ ] Database methods work
- [ ] All 4 commands work
- [ ] Tests pass
- [ ] Pre-Deploy Checklist applied
- [ ] Deployed to production
- [ ] User tested

### Nice to Have:
- [ ] Detailed audit display
- [ ] Pagination for many anketas
- [ ] Export audit to PDF
- [ ] Analytics dashboard

---

## 📊 EXPECTED RESULTS

**Quality Control:**
- ✅ 100% anketas audited before generation
- ✅ 0% grants generated on garbage data
- ✅ Users get clear recommendations

**Usability:**
- ✅ Users can manage anketas
- ✅ Users know quality before generation
- ✅ Clear UI/UX

**Performance:**
- First audit: +30s (acceptable)
- Cached audit: +0.1s (excellent)
- Overall: Quality > Speed

---

## 🐛 EDGE CASES TO TEST

1. **No anketas:** `/my_anketas` with 0 anketas
2. **Many anketas:** Pagination needed?
3. **Delete in-progress anketa:** Allow?
4. **Audit while generating:** Block?
5. **Re-audit:** Should update or create new?
6. **Delete audited anketa:** Cascade delete audit?

---

## 💡 TIPS

### Development:
- Работай поэтапно (по одной команде)
- Тестируй каждую команду сразу
- Используй logging для debug
- Сохраняй изменения часто

### Testing:
- Тестируй на РЕАЛЬНЫХ данных
- Проверь все кнопки
- Проверь все edge cases
- Запиши что работает/не работает

### Before Deploy:
- Применить Pre-Deploy Checklist
- Запустить все тесты
- Проверить логи
- Сделать backup БД

---

## 📞 QUICK REFERENCE

### Files to Create:
```
telegram-bot/handlers/anketa_management_handler.py
tests/test_anketa_management.py
```

### Files to Modify:
```
data/database/models.py
telegram-bot/handlers/grant_handler.py
telegram-bot/main.py
```

### Commands to Add:
```
/my_anketas
/delete_anketa
/audit_anketa
```

---

## 🔄 WORKFLOW (по методологии)

```
1. План ✅ (готов)
   ↓
2. Код (следующая сессия)
   ↓
3. Тесты (следующая сессия)
   ↓
4. Локальное тестирование (следующая сессия)
   ↓
5. Pre-Deploy Checklist
   ↓
6. Deploy
   ↓
7. User testing
   ↓
8. Report
```

---

**NEXT ACTION:** Начать Phase 1 (Database Methods) в следующую сессию

**STATUS:** READY TO START
**TIME:** 4-6 hours estimated
**METHODOLOGY:** Cradle OS Applied ✅

🧬 **Grow Fast, Stay Healthy!**
