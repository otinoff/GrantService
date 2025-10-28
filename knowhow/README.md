# GrantService Knowhow

**Практические знания и best practices из реальной разработки**

Эта директория содержит практический опыт, полученный при разработке GrantService. Каждый документ основан на реальных проблемах и их решениях, проверенных в production.

---

## 📚 Документы

### 🚀 [DEPLOYMENT_SSH_PRACTICES.md](DEPLOYMENT_SSH_PRACTICES.md)

**Что внутри:**
- SSH deployment через ключи в Windows
- Решение `Host key verification failed`
- Работа с `git stash` на production
- Полный deployment workflow
- Troubleshooting guide

**Когда использовать:**
- Деплоишь изменения на production
- Проблемы с SSH соединением
- Git conflicts на сервере

**Из iteration:** 62 - Research Results Parsing Fix

**Ключевые команды:**
```bash
# SSH с явным ключом
ssh -i "C:\Users\Андрей\.ssh\id_rsa" -o StrictHostKeyChecking=no root@5.35.88.251

# Deployment
ssh root@5.35.88.251 "cd /var/GrantService && git stash && git pull origin master"
ssh root@5.35.88.251 "systemctl restart grantservice-bot"
```

---

### 🔍 [DATA_STRUCTURE_DEBUGGING.md](DATA_STRUCTURE_DEBUGGING.md)

**Что внутри:**
- Debugging nested dictionaries
- Extraction patterns (flat, nested, list of dicts)
- Методология поиска data structure mismatches
- Best practices для `.get()` и defaults
- Real example: N/A bug fix

**Когда использовать:**
- Данные не извлекаются (показывает N/A, None)
- KeyError в dict операциях
- Mismatch между API и parser
- Проектирование data structures

**Из iteration:** 62 - Research Results Parsing Fix

**Ключевые паттерны:**
```python
# ❌ BAD
answer = data['result']['summary']

# ✅ GOOD
result = data.get('result', {})
answer = result.get('summary', 'N/A')
```

---

### 📋 [ITERATION_WORKFLOW.md](ITERATION_WORKFLOW.md)

**Что внутри:**
- Полный цикл iteration: PLAN → DEVELOP → TEST → DEPLOY → DOCUMENT
- Templates для 00_PLAN.md и SUCCESS.md
- Git workflow best practices
- Checklists для каждой фазы
- Metrics и timing для hotfix vs feature

**Когда использовать:**
- Начинаешь новую iteration
- Нужен template для документации
- Deployment checklist
- Оценка времени на задачу

**Из iterations:** 60-62 experience

**Quick reference:**
```bash
# Hotfix (15-30 min)
mkdir iterations/Iteration_XX && vim 00_PLAN.md
# Apply fix
git commit && git push
ssh root@5.35.88.251 "cd /var/GrantService && git pull && systemctl restart grantservice-bot"
vim SUCCESS.md
```

---

## 🎯 Как использовать Knowhow

### Scenario 1: Deployment на production

1. Открой [DEPLOYMENT_SSH_PRACTICES.md](DEPLOYMENT_SSH_PRACTICES.md)
2. Найди секцию "Full deployment workflow"
3. Скопируй команды, замени на свои значения
4. Выполни deployment checklist

### Scenario 2: Debugging data extraction

1. Открой [DATA_STRUCTURE_DEBUGGING.md](DATA_STRUCTURE_DEBUGGING.md)
2. Пройди "Debugging Checklist" (6 шагов)
3. Примени правильный extraction pattern
4. Добавь unit test для проверки

### Scenario 3: Начало новой iteration

1. Открой [ITERATION_WORKFLOW.md](ITERATION_WORKFLOW.md)
2. Скопируй template для 00_PLAN.md
3. Следуй 5 фазам: PLAN → DEVELOP → TEST → DEPLOY → DOCUMENT
4. По завершении скопируй template для SUCCESS.md

---

## 📈 Когда добавлять новый Knowhow

**Добавляй новый документ если:**
- ✅ Решил нетривиальную проблему
- ✅ Нашел useful pattern для будущего
- ✅ Проблема может повториться
- ✅ Решение проверено в production

**НЕ добавляй если:**
- ❌ Одноразовая проблема
- ❌ Тривиальное решение (документация уже есть)
- ❌ Специфично для одного случая

**Template для нового knowhow:**
```markdown
# Topic Name

**Дата:** YYYY-MM-DD
**Источник:** Iteration XX - Feature Name
**Статус:** ✅ Production-tested

---

## 🐛 Problem / 🎯 Goal

[Описание проблемы или цели]

---

## 🔍 Solution

[Подробное решение с примерами кода]

---

## 📋 Step-by-Step Guide

1. Step 1
2. Step 2
3. Step 3

---

## 🎯 Best Practices

### 1. Practice name
- ✅ Good
- ❌ Bad

---

## 🧪 Real Example

[Пример из конкретной iteration]

---

## 🔗 Related Knowhow

- `knowhow/OTHER_DOC.md`

---

**Автор:** Claude Code
**Дата:** YYYY-MM-DD
**Iteration:** XX
**Status:** ✅ Production-tested
```

---

## 📊 Статистика Knowhow

**Всего документов:** 3 + README

**По источникам:**
- Iteration 62: 2 documents (SSH practices, Data debugging)
- Iterations 60-62: 1 document (Iteration workflow)

**Impact:**
- 🔥 Critical: 2 (Deployment, Data structures)
- 📋 High: 1 (Iteration workflow)

---

## 🔄 Обновление Knowhow

**Когда обновлять существующий документ:**
- Найден улучшенный способ
- Добавлен новый паттерн
- Обнаружен edge case
- Изменились best practices

**Процесс обновления:**
1. Открой документ
2. Добавь новую секцию или обнови существующую
3. Отметь дату обновления в header
4. Сохрани старую версию как `DOC_v1.md` (если major change)

**Example:**
```markdown
# Document Name

**Дата создания:** 2025-10-29
**Последнее обновление:** 2025-11-05
**Версия:** 2.0
```

---

## 🏆 Best Knowhow Practices

### 1. Write immediately after solving

Не откладывай - пиши knowhow сразу после успешного решения, пока всё свежо в памяти.

### 2. Include real code examples

Абстрактные объяснения забываются. Конкретные примеры кода - остаются.

### 3. Show both ❌ BAD and ✅ GOOD

Покажи что НЕ надо делать, а не только правильный способ.

### 4. Add checklist where applicable

Checklists = actionable steps. Легко следовать, сложно забыть шаг.

### 5. Link to iterations

Всегда указывай откуда взят опыт - это даёт context и возможность посмотреть полный example.

---

## 📚 Related Documentation

**Project Documentation:**
- `cradle/PROJECT-EVOLUTION-METHODOLOGY.md` - High-level methodology
- `cradle/TESTING-METHODOLOGY.md` - Testing strategies
- `cradle/GRANTSERVICE-LESSONS-LEARNED.md` - Project-specific lessons
- `iterations/` - Individual iteration docs

**External Resources:**
- [Git Best Practices](https://git-scm.com/book/en/v2)
- [Python Best Practices](https://peps.python.org/pep-0008/)
- [SSH Documentation](https://www.openssh.com/manual.html)

---

## 💬 Feedback

**Есть идея для нового knowhow документа?**

Создай issue или добавь в `knowhow/IDEAS.md`:
```markdown
## Idea: Topic Name

**Problem:** [Описание проблемы]
**Proposed solution:** [Предлагаемое решение]
**Priority:** High / Medium / Low
```

---

## 🎉 Knowhow Contributors

**Iteration 62:** Claude Code
- Created initial knowhow structure
- Documented SSH deployment practices
- Documented data structure debugging
- Created iteration workflow guide

**Future:** Your contributions here!

---

**Created:** 2025-10-29
**Last Updated:** 2025-10-29
**Documents:** 3 + README
**Status:** 🌱 Growing knowledge base
