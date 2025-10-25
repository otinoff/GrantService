# ⚡ Quick Test Guide - ProductionWriter

**Date:** 2025-10-24
**Bot:** @grant_service_bot
**Status:** ✅ READY FOR TESTING

---

## 🎯 Quick Start (3 minutes)

### Step 1: Открыть бота

```
Telegram → @grant_service_bot → /start
```

### Step 2: Пройти интервью (если нет анкеты)

```
Нажать кнопку "🆕 Интервью V2"
Ответить на вопросы (~5 минут)
```

### Step 3: Сгенерировать грант

```
/generate_grant
```

**Ожидаемый результат:**
```
🚀 Начинаю генерацию грантовой заявки...

📋 Анкета: AN-20251024-001
⏱ Это займет ~2-3 минуты

Я пришлю уведомление когда заявка будет готова!
```

### Step 4: Получить грант

**Через 2-3 минуты:**
```
✅ Грантовая заявка готова!

📋 Анкета: AN-20251024-001
🆔 Grant ID: GA-20251024-XXXXXXXX

📊 Статистика:
• Символов: 44,000
• Слов: 6,500
• Секций: 10
• Время генерации: 130.2s

Используйте /get_grant для получения заявки.
```

**Получить грант:**
```
/get_grant
```

**Результат:** Получите текст грантовой заявки (разбитый на части если >4000 символов)

---

## 📋 All Commands

### 1. `/generate_grant` - Создать грант

**Без параметров (использует последнюю анкету):**
```
/generate_grant
```

**С указанием анкеты:**
```
/generate_grant AN-20251024-001
```

**Когда использовать:**
- После прохождения интервью
- Когда нужна новая версия гранта
- После редактирования анкеты

### 2. `/get_grant` - Получить грант

**Без параметров (последний грант):**
```
/get_grant
```

**С указанием анкеты:**
```
/get_grant AN-20251024-001
```

**Когда использовать:**
- После генерации
- Для повторного просмотра
- Для копирования текста

### 3. `/list_grants` - Список грантов

```
/list_grants
```

**Показывает:**
- Все ваши грантовые заявки
- Grant ID
- Anketa ID
- Количество символов
- Дата создания
- Статус

---

## 🧪 Test Scenarios

### Scenario 1: Happy Path ✅

```
1. /start
2. Кнопка "🆕 Интервью V2"
3. Пройти интервью до конца
4. /generate_grant
5. Дождаться уведомления (2-3 мин)
6. /get_grant
```

**Expected:** Получить полный грант ~44K символов

### Scenario 2: Без анкеты ❌

```
1. Новый пользователь
2. /generate_grant
```

**Expected:**
```
❌ У вас нет завершенных анкет.
Пожалуйста, сначала пройдите интервью командой /start
```

### Scenario 3: Повторная генерация ⚠️

```
1. /generate_grant AN-20251024-001
2. Дождаться завершения
3. /generate_grant AN-20251024-001 (еще раз)
```

**Expected:**
```
✅ Для анкеты AN-20251024-001 уже есть готовая грантовая заявка!

📊 Статистика:
• Символов: 44,000
• Слов: 6,500
...

Используйте /get_grant AN-20251024-001 для получения заявки.
```

### Scenario 4: Чужая анкета ❌

```
1. /generate_grant AN-20251024-OTHER-USER
```

**Expected:**
```
❌ Анкета AN-20251024-OTHER-USER не принадлежит вам.
```

### Scenario 5: Параллельная генерация ⏳

```
1. /generate_grant
2. /generate_grant (сразу же)
```

**Expected:**
```
⏳ У вас уже запущена генерация гранта.
Пожалуйста, дождитесь завершения текущей генерации.
```

---

## 📊 What to Check

### During Generation:

- ✅ Progress notification sent
- ✅ Bot remains responsive
- ✅ No errors in logs
- ✅ Generation completes within 2-3 minutes

### After Generation:

- ✅ Success notification received
- ✅ Statistics shown (chars, words, time)
- ✅ Admin notification sent (if configured)
- ✅ Grant saved to database

### When Getting Grant:

- ✅ Grant text received
- ✅ Automatic splitting if >4000 chars
- ✅ All sections present (10 sections)
- ✅ Status updated to 'sent_to_user'

---

## 🐛 Known Issues

### None Yet! 🎉

Если найдете проблемы:
1. Скопируйте error message
2. Отправьте администратору
3. Проверьте логи: `journalctl -u grantservice-bot -f`

---

## 📞 Support

### Logs:

```bash
# SSH to server
ssh root@5.35.88.251

# Check logs
sudo journalctl -u grantservice-bot -f | grep -i grant

# Check bot status
sudo systemctl status grantservice-bot
```

### Database:

```bash
# Connect
psql -h localhost -p 5434 -U grantservice -d grantservice

# Check grants
SELECT grant_id, anketa_id, user_id, status, character_count, created_at
FROM grants
ORDER BY created_at DESC
LIMIT 10;

# Check sessions
SELECT anketa_id, user_id, status, completed_at
FROM sessions
WHERE status = 'completed'
ORDER BY completed_at DESC
LIMIT 10;
```

---

## ✅ Test Checklist

### Basic:

- [ ] `/generate_grant` без анкет → error
- [ ] `/generate_grant` с анкетой → success
- [ ] `/get_grant` → grant received
- [ ] `/list_grants` → list shown

### Advanced:

- [ ] Long grant (>4000 chars) → auto split
- [ ] Parallel generation → blocked
- [ ] Existing grant → not regenerated
- [ ] Wrong anketa_id → error
- [ ] Other user anketa → error

### Performance:

- [ ] Generation time ~2-3 min
- [ ] Bot responsive during generation
- [ ] No memory leaks
- [ ] No errors in logs

### Integration:

- [ ] User LLM preference used
- [ ] Qdrant queries executed
- [ ] PostgreSQL connected
- [ ] Admin notifications sent
- [ ] Database updated correctly

---

**Status:** ✅ READY FOR TESTING
**Created:** 2025-10-24
**Next:** Start testing!
