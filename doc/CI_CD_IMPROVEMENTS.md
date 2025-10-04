# CI/CD Improvements - GitHub Actions

**Дата**: 2025-10-04
**Версия**: 2.0
**Статус**: ✅ Готово к применению

---

## 🎯 Что было улучшено

### 1. ✅ Pre-deployment тесты (критично!)

**До**: Код деплоился без проверки
**После**: Запускаются автоматические тесты ПЕРЕД деплоем

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - Run 3 критичных интеграционных теста
    - test_complete_application_flow
    - test_get_total_users
    - test_can_connect_to_postgresql
```

**Результат**: Если хотя бы 1 тест упал - деплой блокируется ❌

---

### 2. 🚀 Telegram уведомления

**Группа**: -4930683040 (Грантсервис)

**Уведомления**:
- 🚀 **Deployment started** - начало деплоя (после прохождения тестов)
- ✅ **Deployment success** - успешный деплой со статусом всех сервисов
- ❌ **Tests failed** - тесты упали, деплой заблокирован
- ❌ **Deployment failed** - деплой упал, выполнен rollback

**Пример уведомления**:
```
✅ GrantService Deployment SUCCESS

📦 Branch: master
💬 Commit: fix: update database schema
👤 Author: otinoff

🤖 Bot: Running
💻 Admin: Running
🌐 HTTPS: OK

⏱ Deploy time: ~30s
```

---

### 3. 🧪 Smoke tests после деплоя

**Автоматические проверки**:
- ✅ Bot service is running
- ✅ Admin service is running
- ✅ HTTP endpoint (port 8550): 200 OK
- ✅ HTTPS endpoint: 200 OK
- ✅ Database connectivity
- ✅ Bot token is not placeholder

**Если хоть одна проверка упала** → автоматический rollback

---

### 4. 🔄 Автоматический rollback

**До**: При ошибке деплоя сервисы ломались, нужен был manual fix
**После**: Автоматический откат к предыдущему коммиту

```bash
# Rollback sequence:
1. git reset --hard HEAD~1
2. Clear Python cache
3. Restart services
4. Verify services are running
5. Notify in Telegram
```

---

## 📋 Что нужно сделать для запуска

### Шаг 1: Добавить GitHub Secret

Нужно добавить один секрет: `TELEGRAM_BOT_TOKEN`

**Вариант 1 - Использовать существующий бот**:
```bash
# SSH на сервер
ssh root@5.35.88.251

# Получить токен
cat /var/GrantService/config/.env | grep TELEGRAM_BOT_TOKEN
# Скопировать значение токена
```

**Вариант 2 - Через GitHub CLI**:
```bash
# Если токен: 7686393933:AAG_example_token_here
gh secret set TELEGRAM_BOT_TOKEN --body "7686393933:AAG_example_token_here"
```

**Вариант 3 - Через веб-интерфейс**:
1. GitHub → Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `TELEGRAM_BOT_TOKEN`
4. Value: `<вставить токен>`
5. Add secret

### Шаг 2: Проверить что бот в группе

```bash
# Отправить тестовое сообщение
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=-4930683040" \
  -d "text=CI/CD test notification"
```

Должно прийти сообщение в группу "Грантсервис".

### Шаг 3: Коммит и push

```bash
git add .github/workflows/deploy-grantservice.yml
git add .github/SETUP_SECRETS.md
git add CI_CD_IMPROVEMENTS.md

git commit -m "feat: Optimize CI/CD with tests, notifications and auto-rollback

- Add pre-deployment integration tests (blocks deploy if failed)
- Add smoke tests after deployment (HTTP, HTTPS, services)
- Add Telegram notifications to group -4930683040
- Add automatic rollback on deployment failure
- Update workflow documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin master
```

### Шаг 4: Проверить деплой

1. Перейти в GitHub → Actions
2. Посмотреть запущенный workflow
3. Проверить что пришли уведомления в Telegram

---

## 📊 Новая структура деплоя

### Весь процесс (если всё ОК):

```
1. Push в GitHub
   ↓
2. GitHub Actions запускается
   ↓
3. JOB: test
   ├─ Установка Python
   ├─ Установка зависимостей
   ├─ Запуск 3 интеграционных тестов
   └─ ✅ Все тесты прошли
   ↓
4. JOB: deploy (runs only if tests pass)
   ├─ 📱 Уведомление: "Deployment started"
   ├─ SSH подключение к серверу
   ├─ Остановка сервисов
   ├─ Обновление кода
   ├─ Установка зависимостей
   ├─ Запуск сервисов
   ├─ Smoke tests (6 проверок)
   └─ ✅ Все проверки прошли
   ↓
5. 📱 Уведомление: "Deployment SUCCESS"
```

### Если что-то пошло не так:

```
1. Тесты упали
   ↓
2. 📱 Уведомление: "Tests FAILED - deployment blocked"
   ↓
3. Деплой не запускается
```

**ИЛИ**

```
1. Деплой прошел, но smoke tests упали
   ↓
2. Автоматический rollback
   ├─ git reset --hard HEAD~1
   ├─ Restart services
   └─ Verify services running
   ↓
3. 📱 Уведомление: "Deployment FAILED - rollback executed"
```

---

## 🎯 Преимущества новой системы

### Безопасность:
- ❌ Нельзя задеплоить код с упавшими тестами
- ✅ Автоматический rollback если что-то сломалось
- ✅ Всегда есть working version (предыдущий коммит)

### Скорость реакции:
- ⏱ Мгновенные уведомления в Telegram
- 📊 Сразу видно статус деплоя
- 🔍 Ссылка на логи в GitHub Actions

### Надежность:
- 🧪 6 smoke tests после каждого деплоя
- 🔐 Проверка критичных параметров (token, DB, HTTP)
- 📈 История всех деплоев в Actions

---

## 🔧 Мониторинг и отладка

### Где смотреть логи:

1. **GitHub Actions**:
   - https://github.com/otinoff/GrantService/actions
   - Видно все шаги, ошибки, время выполнения

2. **Telegram группа**:
   - Уведомления о каждом деплое
   - Статус сервисов
   - Ссылки на логи

3. **Сервер**:
   ```bash
   ssh root@5.35.88.251
   journalctl -u grantservice-bot -f
   journalctl -u grantservice-admin -f
   ```

### Если деплой упал:

1. Проверить уведомление в Telegram (есть ссылка на логи)
2. Открыть GitHub Actions → View run
3. Посмотреть на каком шаге упало
4. Rollback уже выполнен автоматически
5. Исправить проблему локально
6. Запустить тесты: `pytest tests/integration/ -v`
7. Если тесты ОК → push снова

---

## 📈 Метрики

### Время деплоя:

| Этап | Время | Критичность |
|------|-------|-------------|
| Tests | ~2-3 мин | ⚠️ Блокирует деплой |
| Deploy | ~30 сек | ✅ Быстро |
| Smoke tests | ~10 сек | ⚠️ Может вызвать rollback |
| **Total** | **~3-4 мин** | |

### Downtime:

- **Плановый**: ~8-10 сек (restart сервисов)
- **При rollback**: ~15-20 сек (reset + restart)
- **При ошибке без rollback (старая система)**: могло быть часы ❌

---

## 🎓 Best Practices

### ✅ DO:

1. **Запускай тесты локально** перед push:
   ```bash
   pytest tests/integration/ -v
   ```

2. **Проверяй уведомления в Telegram** после push

3. **Смотри логи в GitHub Actions** если что-то непонятно

4. **Деплой небольшими порциями** (1-3 изменения за раз)

### ❌ DON'T:

1. **Не игнорируй упавшие тесты** - если тест упал, значит есть проблема

2. **Не пуши в production без локальных тестов**

3. **Не деплой большие изменения** без manual check

4. **Не меняй config/.env** через Git (он в .gitignore)

---

## 🔮 Планы на будущее

### v2.1 (опционально):
- [ ] Headless browser tests для Streamlit страниц
- [ ] Performance metrics в уведомлениях
- [ ] Deploy preview для Dev ветки
- [ ] Canary deployment (постепенный rollout)

### v2.2:
- [ ] Integration с Sentry для error tracking
- [ ] Automatic database backups перед deploy
- [ ] Deploy scheduling (только в определенное время)

---

**Вопросы?** Пиши в группу "Грантсервис" или создай issue на GitHub.

**Документация**:
- `.github/workflows/deploy-grantservice.yml` - главный workflow
- `.github/SETUP_SECRETS.md` - инструкции по секретам
- `doc/DEPLOYMENT.md` - полная документация по деплою

---

*Создано: 2025-10-04*
*Автор: Claude Code (deployment-manager agent)*
