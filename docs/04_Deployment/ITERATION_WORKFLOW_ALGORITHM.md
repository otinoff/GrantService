# 🔄 Алгоритм Проведения Итерации

**Версия:** 1.0
**Дата:** 2025-10-24
**Статус:** ACTIVE TEMPLATE

---

## 📋 Структура Итерации

```
Iteration_XX_Name/
├── 01_Plan.md              # План итерации
├── 02_Implementation/      # Код и изменения
├── 03_Local_Testing/       # Локальное тестирование
└── 04_Results.md           # Результаты

Deploy_XX_Name/
├── 01_Deploy_Info.md       # Информация о деплое
├── 02_Production_Testing/  # Тесты на продакшене
└── 03_Results.md           # Результаты деплоя
```

---

## 🔑 Ключевые Учетные Данные

### Production Server
```
Host: 5.35.88.251
User: root
SSH Key: C:\Users\Андрей\.ssh\id_rsa
SSH Config: C:\Users\Андрей\.ssh\config
```

### PostgreSQL Production
```
Host: localhost (на сервере)
Port: 5434
User: grantservice
Password: jPsGn%Nt%q#THnUB&&cqo*1Q
Database: grantservice
```

### GigaChat API
```
Base URL: https://gigachat.devices.sberbank.ru/api/v1
Auth URL: https://ngw.devices.sberbank.ru:9443/api/v2/oauth
API Key: OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5OjJlY2ZlZjg0LWViOWYtNGQ2Ni04ODllLTJlZmVmY2MyMTlmYQ==
Client ID: 967330d4-e5ab-4fca-a8e8-12a7d510d249
Scope: GIGACHAT_API_PERS

Models:
- GigaChat-Max (1.9M tokens by package)
- GigaChat-Pro (2.0M tokens by package)
- GigaChat-Lite (2.0M tokens by package)
```

### Claude Code API
```
Base URL: http://178.236.17.55:8000
API Key: 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
Models: sonnet, opus
```

### Qdrant
```
Production: 5.35.88.251:6333
Collection: knowledge_sections
```

### Telegram Bot
```
Username: @grant_service_bot
Admin Chat ID: (from config)
```

### GitHub
```
Repository: https://github.com/otinoff/GrantService
Branch: master
Local Path: C:\SnowWhiteAI\GrantService
```

---

## 🎯 Полный Workflow Итерации

### Phase 1: Planning (30-60 min)

**1.1 Определить задачу:**
```markdown
- Читаем CURRENT_STATUS.md
- Определяем что нужно сделать
- Проверяем предыдущую итерацию
```

**1.2 Создать план:**
```bash
# Создать папку итерации
mkdir "C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\Iteration_XX_Name"

# Создать 01_Plan.md
# Включить:
# - Цели
# - Задачи
# - Ожидаемые результаты
# - Критерии успеха
```

**1.3 Обновить CURRENT_STATUS.md:**
```markdown
## 🎯 Current Iteration
**Iteration XX:** Name
**Status:** 🔄 IN PROGRESS
**Previous:** Iteration (XX-1)
```

---

### Phase 2: Implementation (1-3 hours)

**2.1 Написать код:**
```bash
# Открыть проект
cd C:\SnowWhiteAI\GrantService

# Проверить бранч
git status
git branch

# Внести изменения в файлы
# Следовать плану из 01_Plan.md
```

**2.2 Проверить изменения:**
```bash
# Список изменений
git status

# Посмотреть diff
git diff agents/production_writer.py
git diff data/database/models.py
```

---

### Phase 3: Local Testing (30-60 min)

**3.1 Создать тестовую папку:**
```bash
mkdir "Iteration_XX/03_Local_Testing"
```

**3.2 Написать тесты:**
```python
# test_iteration_XX.py
import sys
sys.path.insert(0, 'C:\\SnowWhiteAI\\GrantService')

# Импорты
from agents.production_writer import ProductionWriter
from data.database.models import Database

# Тест 1: Проверить инициализацию
def test_initialization():
    writer = ProductionWriter(llm_provider='gigachat')
    assert writer.llm_client.model == "GigaChat-Max"

# Тест 2: Проверить SQL запросы
def test_sql_queries():
    db = Database()
    anketa = db.get_latest_completed_anketa(5032079932)
    assert anketa is not None
```

**3.3 Запустить тесты:**
```bash
# Локально
python test_iteration_XX.py

# Результаты сохранить в 03_Results.md
```

**3.4 Проверить schema (если работа с БД):**
```bash
# Подключиться к локальной БД
PGPASSWORD=root psql -h localhost -p 5433 -U postgres -d grantservice

# Проверить структуру
\d sessions
\d grants
\d users

# Проверить FK constraints
\d+ grants
```

---

### Phase 4: Git Commit (15 min)

**4.1 Добавить файлы:**
```bash
cd C:\SnowWhiteAI\GrantService

# Добавить ТОЛЬКО измененные файлы (не qdrant_storage!)
git add agents/production_writer.py
git add data/database/models.py
git add telegram-bot/handlers/grant_handler.py
```

**4.2 Создать коммит:**
```bash
git commit -m "fix: Iteration XX - Brief description

Fixes:
1. Description of fix 1
2. Description of fix 2
3. Description of fix 3

Impact:
- What changed
- What improved

Deploy: #XX
Iteration: XX"
```

**4.3 Пушнуть на GitHub:**
```bash
git push origin master

# Проверить на GitHub
# https://github.com/otinoff/GrantService/commits/master
```

---

### Phase 5: Production Deployment (30 min)

**5.1 Создать папку деплоя:**
```bash
mkdir "C:\SnowWhiteAI\GrantService_Project\Development\03_Deployment\Deploy_XX_Name"
```

**5.2 SSH подключение:**
```bash
# Проверить ключи
ls -la C:\Users\Андрей\.ssh

# Подключиться
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251
```

**5.3 Pull код:**
```bash
# На production сервере
cd /var/GrantService
git pull origin master

# Проверить что скачалось
git log -1
git diff HEAD~1
```

**5.4 Применить миграции (если есть):**
```bash
# Подключиться к PostgreSQL
PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql -h localhost -p 5434 -U grantservice -d grantservice

# Применить миграцию
\i database/migrations/014_update_grants_for_production_writer.sql

# Проверить результат
\d grants
```

**5.5 Перезапустить services:**
```bash
# Перезапуск бота
sudo systemctl restart grantservice-bot

# Проверить статус
sudo systemctl status grantservice-bot --no-pager

# Проверить логи
sudo journalctl -u grantservice-bot -f -n 50
```

**5.6 Проверить что работает:**
```bash
# Проверить процессы
ps aux | grep python

# Проверить порты
netstat -tulpn | grep 6333  # Qdrant
netstat -tulpn | grep 5434  # PostgreSQL

# Проверить логи на ошибки
sudo journalctl -u grantservice-bot --since "5 minutes ago" | grep -i error
```

---

### Phase 6: Production Testing (30-60 min)

**6.1 Создать тестовую папку:**
```bash
mkdir "Deploy_XX/02_Production_Testing"
```

**6.2 E2E тест через Telegram:**
```markdown
1. Открыть бота @grant_service_bot
2. Отправить /start
3. Пройти интервью (минимум 10 вопросов)
4. Дождаться завершения
5. Отправить /generate_grant
6. Дождаться генерации (60-180 сек)
7. Проверить /get_grant
8. Проверить /list_grants
```

**6.3 Проверить БД:**
```bash
# SSH на сервер
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251

# Подключиться к PostgreSQL
PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql -h localhost -p 5434 -U grantservice -d grantservice

# Проверить сессию
SELECT anketa_id, telegram_id, status, completed_at
FROM sessions
WHERE telegram_id = 5032079932
ORDER BY started_at DESC LIMIT 3;

# Проверить grant
SELECT grant_id, anketa_id, user_id, status, character_count, created_at
FROM grants
WHERE user_id = 5032079932
ORDER BY created_at DESC LIMIT 3;
```

**6.4 Проверить логи:**
```bash
# Логи за последние 10 минут
sudo journalctl -u grantservice-bot --since "10 minutes ago"

# Поиск ошибок
sudo journalctl -u grantservice-bot --since "10 minutes ago" | grep -i error

# Поиск WARNING
sudo journalctl -u grantservice-bot --since "10 minutes ago" | grep -i warning
```

**6.5 Проверить GigaChat токены:**
```markdown
1. Открыть: https://developers.sber.ru/studio/workspaces
2. Проверить статистику токенов
3. Убедиться что используется GigaChat-Max (по пакетам)
4. Проверить что не списывается Lite (по подписке)
```

---

### Phase 7: Documentation (30 min)

**7.1 Завершить Iteration_XX:**
```markdown
# Создать Iteration_XX/04_Results.md

## ✅ Что Сделано
- Список выполненных задач

## 🐛 Найденные Баги
- Список багов (если есть)

## 📊 Результаты
- Метрики
- Время выполнения
- Quality score

## ✅ Success Criteria
- [x] Criterion 1
- [x] Criterion 2
```

**7.2 Завершить Deploy_XX:**
```markdown
# Создать Deploy_XX/01_Deploy_Info.md

## 📦 What Was Deployed
- Git commit hash
- Files changed
- Lines added/removed

## ✅ Successful Parts
- What works

## ❌ Failed Parts (if any)
- What doesn't work
- Bugs found

## 📊 Deploy Statistics
- Time taken
- Downtime
- Services status

## 🧪 Testing Results
- E2E test results
- Production metrics
```

**7.3 Обновить CURRENT_STATUS.md:**
```markdown
## 🎯 Current Iteration
**Iteration XX:** Name
**Status:** ✅ COMPLETED

## 📍 Where We Are
### Latest Completed Work:
**Iteration XX (Just Finished):**
- ✅ Task 1
- ✅ Task 2
- ✅ All tests passed

**Deploy #XX (Success):**
- ✅ Deployed successfully
- ✅ All services running
- ✅ E2E tests passed

## 📋 Next Steps (Iteration XX+1)
1. Next task
2. Next feature
```

**7.4 Обновить индекс документов:**
```markdown
# В INDEX_ALL_DOCS.md добавить:

## Iteration XX
- 📋 Plan: Iteration_XX/01_Plan.md
- 📝 Results: Iteration_XX/04_Results.md

## Deploy XX
- 🚀 Deploy Info: Deploy_XX/01_Deploy_Info.md
- 🧪 Testing: Deploy_XX/02_Production_Testing/
```

---

## 🔄 Workflow Diagram

```
┌─────────────────┐
│  1. PLANNING    │
│  Create Plan    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. CODING       │
│ Write Code      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. LOCAL TEST   │
│ Test Locally    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. GIT COMMIT   │
│ Push to GitHub  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. DEPLOYMENT   │
│ Deploy to Prod  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. PROD TEST    │
│ E2E Testing     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│7. DOCUMENTATION │
│ Update Docs     │
└─────────────────┘
```

---

## 📞 Quick Commands Cheat Sheet

### SSH Connection
```bash
# Connect to production
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251

# With StrictHostKeyChecking=no
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile="C:\Users\Андрей\.ssh\known_hosts" -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251
```

### PostgreSQL Production
```bash
# Connect
PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql -h localhost -p 5434 -U grantservice -d grantservice

# Check schema
\d sessions
\d grants
\d users

# Exit
\q
```

### Service Management
```bash
# Restart bot
sudo systemctl restart grantservice-bot

# Check status
sudo systemctl status grantservice-bot --no-pager

# View logs (live)
sudo journalctl -u grantservice-bot -f

# View logs (last 50 lines)
sudo journalctl -u grantservice-bot -n 50

# View logs (since time)
sudo journalctl -u grantservice-bot --since "10 minutes ago"
```

### Git Commands
```bash
# Local repository
cd C:\SnowWhiteAI\GrantService

# Check status
git status

# Add files
git add file1.py file2.py

# Commit
git commit -m "message"

# Push
git push origin master

# Pull on production
cd /var/GrantService && git pull origin master
```

### Check Production Status
```bash
# Services
systemctl status grantservice-bot --no-pager
systemctl status grantservice-admin --no-pager

# Processes
ps aux | grep python | grep -v grep

# Ports
netstat -tulpn | grep 6333  # Qdrant
netstat -tulpn | grep 5434  # PostgreSQL

# Disk space
df -h

# Memory
free -h
```

---

## 🎯 Success Criteria Template

```markdown
- [ ] Code написан и работает локально
- [ ] Local tests passed
- [ ] Git committed and pushed
- [ ] Deployed to production
- [ ] Services restarted successfully
- [ ] No errors in production logs
- [ ] E2E test passed on production
- [ ] Database updated correctly
- [ ] All features working as expected
- [ ] Documentation updated
- [ ] CURRENT_STATUS.md updated
```

---

## 🐛 Troubleshooting

### SSH Connection Failed
```bash
# Check SSH keys
ls -la C:\Users\Андрей\.ssh

# Test connection
ssh -vvv -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251

# Add to known_hosts
ssh-keyscan 5.35.88.251 >> C:\Users\Андрей\.ssh\known_hosts
```

### PostgreSQL Connection Failed
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Check port
netstat -tulpn | grep 5434

# Check password
cat /var/GrantService/config/.env | grep PGPASSWORD
```

### Service Won't Start
```bash
# Check logs
sudo journalctl -u grantservice-bot -n 100

# Check Python errors
sudo journalctl -u grantservice-bot | grep Traceback

# Test manually
cd /var/GrantService
source venv/bin/activate
python telegram-bot/main.py
```

### Git Pull Failed
```bash
# Check for uncommitted changes
git status

# Stash changes
git stash

# Pull
git pull origin master

# Apply stash
git stash pop
```

---

## 📊 Iteration Metrics

После каждой итерации собирать метрики:

```markdown
## Iteration XX Metrics

**Time:**
- Planning: XX min
- Coding: XX min
- Local Testing: XX min
- Deployment: XX min
- Production Testing: XX min
- Documentation: XX min
- **Total:** XX hours

**Code:**
- Files changed: XX
- Lines added: XXX
- Lines removed: XX
- Commits: X

**Bugs:**
- Found: X
- Fixed: X
- Remaining: X

**Production:**
- Downtime: XX seconds
- Services restarted: X
- Errors after deploy: X
```

---

**Last Updated:** 2025-10-24 07:10 UTC
**Status:** ✅ ACTIVE TEMPLATE
**Used in:** Iteration 33+
