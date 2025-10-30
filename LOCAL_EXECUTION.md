# Local Execution - Test Engineer Agent

**Запускай агента локально, работай с production кодом, получай результаты на локальной машине!**

---

## 🎯 Зачем это нужно?

### Проблема:
- Запуск на production → результаты на сервере → нужен SSH для просмотра
- Нет tracking токенов
- Нет локальных artifacts

### Решение:
- **Код:** Production (SSH к 5.35.88.251)
- **Execution:** Remote (на production сервере)
- **Artifacts:** Local (твоя машина, `test_artifacts/`)
- **Tracking:** Токены, стоимость, баланс

---

## 🚀 Quick Start

### Простой запуск (Mock WebSearch):

```bash
python run_test_local.py
```

### С реальным WebSearch:

```bash
python run_test_local.py --real
```

### Без token tracking:

```bash
python run_test_local.py --no-tokens
```

---

## 📊 Что получаешь?

### После запуска создается папка:

```
test_artifacts/
└── test_20251030_170530/
    ├── results.json       # Полные результаты (JSON)
    ├── SUMMARY.md         # Краткий отчет с токенами ⭐
    ├── stdout.log         # Вывод агента
    └── stderr.log         # Ошибки
```

### SUMMARY.md содержит:

```markdown
# Test Run: 20251030_170530

**Date:** 2025-10-30 17:05:30

## Execution
- **Mode:** Remote (SSH to 5.35.88.251)
- **Duration:** 154.3s
- **Status:** success

## Token Usage
- **Spent Today:** 12,450 tokens
- **Remaining Today:** 87,550 tokens
- **Daily Limit:** 100,000 tokens
- **Utilization:** 12.5%

## Steps
- **STEP 1 (Interview):** success (10.2s)
- **STEP 2 (Audit):** success (41.6s)
- **STEP 3 (Research):** success (102.5s)
- **STEP 4 (Writer):** success (0.0s)
```

---

## 🔧 Архитектура

```
┌────────────────────┐
│  Твоя машина       │
│  (Windows)         │
│                    │
│  run_test_local.py │
└─────────┬──────────┘
          │ SSH
          ▼
┌────────────────────────────┐
│  Production Server         │
│  5.35.88.251               │
│                            │
│  ┌──────────────────────┐ │
│  │ TestEngineerAgent    │ │
│  │ (с --output-json)    │ │
│  └──────────┬───────────┘ │
│             │              │
│  ┌──────────▼───────────┐ │
│  │ PostgreSQL           │ │
│  │ (production DB)      │ │
│  └──────────────────────┘ │
└────────────┬───────────────┘
             │ JSON results
             ▼
┌────────────────────────────┐
│  Твоя машина               │
│  test_artifacts/           │
│  └── test_XXX/             │
│      ├── results.json      │
│      ├── SUMMARY.md ⭐     │
│      ├── stdout.log        │
│      └── stderr.log        │
└────────────────────────────┘
```

---

## 💰 Token Tracking

### Откуда берутся данные?

**Запрос к production DB:**
```sql
SELECT SUM(tokens_used)
FROM llm_call_logs
WHERE created_at > NOW() - INTERVAL '1 day';
```

### Что отслеживается:

1. **spent_today** - потрачено сегодня
2. **remaining_today** - осталось до лимита
3. **daily_limit** - дневной лимит (100,000)
4. **utilization_pct** - процент использования

### Пример вывода:

```
💰 Token Usage:
   Spent today: 12,450 tokens
   Remaining: 87,550 tokens
   Utilization: 12.5%
```

---

## 📂 Структура результатов

### results.json

```json
{
  "test_id": "20251030_170530",
  "timestamp": "2025-10-30T17:05:30",
  "status": "success",
  "execution": {
    "mode": "remote",
    "duration_sec": 154.3,
    "ssh_host": "5.35.88.251",
    "timestamp": "2025-10-30T17:05:30"
  },
  "tokens": {
    "spent_today": 12450,
    "remaining_today": 87550,
    "daily_limit": 100000,
    "utilization_pct": 12.5
  },
  "steps": {
    "STEP 1 (Interview)": {
      "status": "success",
      "duration_sec": 10.2,
      "anketa_id": "#AN-E2E-20251030170530-999999001"
    },
    "STEP 2 (Audit)": {
      "status": "success",
      "duration_sec": 41.6,
      "score": 0.0
    },
    ...
  },
  "validations": {
    "fix_15": {
      "status": "passed",
      "grant_length": 62000,
      "threshold": 15000
    }
  }
}
```

---

## 🔍 Как это работает?

### 1. Local Script (run_test_local.py)

```python
from tester.remote_executor import RemoteExecutor

executor = RemoteExecutor()
results = executor.execute_remote_test(
    use_mock_websearch=True,
    track_tokens=True
)
```

### 2. Remote Executor (tester/remote_executor.py)

- Подключается по SSH
- Запускает `python3 tester/agent.py --output-json`
- Парсит JSON output
- Запрашивает token usage из DB
- Сохраняет все локально

### 3. Test Engineer Agent (tester/agent.py)

- Выполняет E2E тест
- С флагом `--output-json` выводит:

```
```json
{
  "test_id": "...",
  "status": "success",
  ...
}
```
```

---

## ⚙️ Конфигурация

### SSH Settings (в remote_executor.py):

```python
ssh_host = "5.35.88.251"
ssh_user = "root"
ssh_key = r"C:\Users\Андрей\.ssh\id_rsa"
remote_path = "/var/GrantService"
```

### DB Credentials (в remote_executor.py):

```bash
export PGHOST=localhost
export PGPORT=5434
export PGDATABASE=grantservice
export PGUSER=grantservice
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
```

### Artifacts Location:

```python
local_artifacts_dir = "test_artifacts/"  # Рядом с GrantService/
```

---

## 🐛 Troubleshooting

### SSH Connection Failed

```bash
# Проверь ключ
ls -la ~/.ssh/id_rsa

# Проверь доступ
ssh -i ~/.ssh/id_rsa root@5.35.88.251 "echo OK"
```

### JSON Parse Error

```bash
# Проверь output агента вручную
ssh root@5.35.88.251 "cd /var/GrantService && python3 tester/agent.py --output-json"
```

### Token Tracking Failed

```bash
# Проверь доступ к DB
ssh root@5.35.88.251 \
  "PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql -h localhost -p 5434 -U grantservice -d grantservice -c 'SELECT 1;'"
```

---

## 📈 Примеры использования

### 1. Быстрый тест (Mock WebSearch)

```bash
python run_test_local.py
```

**Результат:**
```
✅ TEST PASSED

🔧 Steps:
   ✅ STEP 1 (Interview): 10.2s
   ✅ STEP 2 (Audit): 41.6s
   ✅ STEP 3 (Research): 102.5s
   ✅ STEP 4 (Writer): 0.0s

💰 Token Usage:
   Spent today: 12,450 tokens
   Remaining: 87,550 tokens
   Utilization: 12.5%

📁 Artifacts saved to:
   test_artifacts/test_20251030_170530/
```

### 2. Full E2E (Real WebSearch)

```bash
python run_test_local.py --real
```

**Внимание:** Может занять 5+ минут из-за WebSearch!

### 3. Только код, без токенов

```bash
python run_test_local.py --no-tokens
```

---

## 🎯 Преимущества

### ✅ Что работает:

1. **Production Code** - тестируешь реальный код
2. **Production DB** - реальная база данных
3. **Local Artifacts** - результаты на твоей машине
4. **Token Tracking** - видишь сколько потратил
5. **Rich Metadata** - duration, status, steps
6. **Easy Access** - просто открой SUMMARY.md

### ⚠️ Ограничения:

1. Нужен SSH доступ к production
2. Нужны credentials для DB
3. Timeout 10 минут (можно увеличить)

---

## 🔄 Workflow

### Типичный рабочий процесс:

```bash
# 1. Запусти тест
python run_test_local.py

# 2. Дождись завершения (2-3 минуты)

# 3. Открой результаты
cd test_artifacts/test_XXXXXX/
cat SUMMARY.md

# 4. Анализируй
cat results.json | jq '.steps'

# 5. Если нужно - посмотри логи
cat stdout.log
cat stderr.log
```

---

## 📚 API Reference

### RemoteExecutor

```python
from tester.remote_executor import RemoteExecutor

executor = RemoteExecutor(
    ssh_host="5.35.88.251",
    ssh_user="root",
    ssh_key=r"C:\Users\Андрей\.ssh\id_rsa",
    remote_path="/var/GrantService",
    local_artifacts_dir="test_artifacts"
)

results = executor.execute_remote_test(
    use_mock_websearch=True,  # Mock WebSearch
    track_tokens=True          # Track token usage
)

print(results["tokens"]["spent_today"])
```

---

## 🎉 Итого

**Теперь ты можешь:**

✅ Запускать агента локально
✅ Тестировать production код
✅ Получать результаты на локальной машине
✅ Видеть сколько токенов потрачено
✅ Отслеживать баланс
✅ Анализировать каждый шаг

**Просто запусти:**
```bash
python run_test_local.py
```

И получи полный отчет в `test_artifacts/`!

---

**Created:** 2025-10-30
**Related:** Iteration 67 (RAG), Iteration 68 (User Simulator)
