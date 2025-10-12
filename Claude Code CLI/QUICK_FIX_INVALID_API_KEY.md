# Quick Fix: Invalid API Key для Claude Code

**Время на решение:** 5-10 минут
**Сложность:** Средняя

---

## 🎯 Быстрое решение (прямо сейчас)

### Вариант 1: Обновить OAuth credentials (5 минут)

```bash
# Шаг 1: На Windows (локально) - найти credentials
type C:\Users\Андрей\.claude\.credentials.json

# Шаг 2: Скопировать на сервер
scp C:\Users\Андрей\.claude\.credentials.json root@178.236.17.55:/root/.claude/

# Шаг 3: Перезапустить API wrapper на сервере
ssh root@178.236.17.55
pkill -f claude-api-wrapper
cd /root/claude-api-wrapper
nohup python3 claude-api-wrapper.py &

# Шаг 4: Проверить
curl -X POST http://178.236.17.55:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -d '{"message":"TEST","model":"sonnet"}'
```

**Ожидаемый результат:**
```json
{"response":"TEST","status":"success"}
```

---

### Вариант 2: Использовать Perplexity (2 минуты)

Временно, пока чините OAuth:

**Файл:** `C:\SnowWhiteAI\GrantService\shared\llm\config.py`

```python
"writer": {
    "provider": "perplexity",  # ← Изменить с "claude" на "perplexity"
    "model": "sonar",
    "temperature": 0.7,
    "max_tokens": 8000
},
```

**Перезапустить сервисы:**
```bash
# Перезапустить Telegram bot или что использует Writer Agent
```

---

## 🔍 Диагностика за 2 минуты

```bash
# 1. Проверить health
curl http://178.236.17.55:8000/health

# 2. Проверить credentials на сервере
ssh root@178.236.17.55 "cat /root/.claude/.credentials.json | jq ."

# 3. Проверить когда истекает токен
ssh root@178.236.17.55 'cat /root/.claude/.credentials.json | jq -r ".expiresAt" | xargs -I {} date -d @$(({}/ 1000))'

# 4. Тест запроса
curl -X POST http://178.236.17.55:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -d '{"message":"Скажи одно слово TEST","model":"sonnet","temperature":0.3}'
```

---

## 📋 Checklist устранения проблемы

- [ ] Endpoint `/health` работает? (Status: 200)
- [ ] Файл `~/.claude/.credentials.json` существует на сервере?
- [ ] `expiresAt` в будущем? (не истёк токен)
- [ ] API wrapper запущен? (`ps aux | grep claude-api-wrapper`)
- [ ] Тест `/chat` возвращает текст, а не "Invalid API key"?

---

## 🆘 Если ничего не помогло

1. **Переключить на Perplexity** (Вариант 2 выше) - работает 100%

2. **Получить новый OAuth token:**
   ```bash
   # На локальной машине
   claude logout
   claude login
   # Скопировать новый credentials.json на сервер
   ```

3. **Использовать API Key вместо OAuth:**
   ```bash
   # Получить на https://console.anthropic.com/
   # Установить на сервере
   export ANTHROPIC_API_KEY="sk-ant-api03-..."
   ```

---

## 📞 Подробная инструкция

См. полный guide: `INVALID_API_KEY_FIX_GUIDE.md` в этой же папке

---

**Дата:** 2025-10-12
**Версия:** 1.0
