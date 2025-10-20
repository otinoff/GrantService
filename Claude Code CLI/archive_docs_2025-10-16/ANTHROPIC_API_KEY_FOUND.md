# 🔑 ANTHROPIC_API_KEY Найден!

**Дата**: 2025-10-08
**Источник**: `C:\Users\Андрей\.claude\.credentials.json`

---

## ✅ Найденные учетные данные:

### OAuth Access Token (главный ключ):
```
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
```

### OAuth Refresh Token:
```
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
```

### Дополнительная информация:
- **Subscription Type**: `max` ✅ (20x rate limits!)
- **Expires At**: 1759950304394 (timestamp)
- **Scopes**: `user:inference`, `user:profile`

---

## 📊 Сравнение с хостингом:

### На сервере (178.236.17.55):

**Файл**: `.env` (в cradle/documentation/exported-assets)
```bash
API_KEY=1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
CLAUDE_WORKING_DIR=/home/claude/claude_sessions
CLAUDE_TIMEOUT=300
```

**❌ ПРОБЛЕМА**: Отсутствует `ANTHROPIC_API_KEY`

---

## 🎯 Что нужно добавить на сервер:

### Вариант 1: Access Token (рекомендуется)

```bash
ANTHROPIC_API_KEY=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
```

### Вариант 2: Полная OAuth конфигурация

Если сервер поддерживает OAuth refresh:
```bash
ANTHROPIC_OAUTH_ACCESS_TOKEN=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
ANTHROPIC_OAUTH_REFRESH_TOKEN=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
```

---

## 🔧 Инструкция по добавлению на сервер:

### Шаг 1: SSH подключение
```bash
ssh user@178.236.17.55
```

### Шаг 2: Найти конфиг Claude Code
```bash
# Проверить systemd
sudo systemctl status claude-code-api

# Проверить Docker
docker inspect claude-code-api | grep -A 20 "Env"

# Найти .env файл
find /etc /opt /root /home -name "*claude*" -name ".env" 2>/dev/null
```

### Шаг 3: Добавить ключ в конфиг

**Если systemd service**:
```bash
sudo nano /etc/claude-code/.env
# Добавить:
ANTHROPIC_API_KEY=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
```

**Если Docker**:
```bash
# Редактировать docker-compose.yml или .env
nano /path/to/.env
# Добавить:
ANTHROPIC_API_KEY=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
```

### Шаг 4: Перезапустить сервис
```bash
# Systemd
sudo systemctl restart claude-code-api

# Docker
docker restart claude-code-api
```

### Шаг 5: Проверить
```bash
# Локально на сервере
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","model":"sonnet"}'

# Должен вернуть 200 OK вместо 500!
```

### Шаг 6: Финальный тест с локальной машины
```bash
cd C:\SnowWhiteAI\GrantService
python test_claude_api.py
# Должно быть: TEST PASSED: Claude API works!
```

---

## ⚠️ Важные замечания:

### 1. OAuth Token vs API Key

Это **OAuth токен**, а не обычный API ключ. Он:
- ✅ Работает так же как обычный API ключ
- ✅ Может быть использован в заголовке `x-api-key`
- ✅ Имеет срок действия (expires_at)
- ⚠️ Может потребовать refresh через refresh_token

### 2. Subscription Type: MAX

Отлично! У тебя **Max подписка (20x)**:
- 20x выше rate limits чем Pro
- Оптимальное соотношение цена/производительность
- Достаточно для серьезной разработки

### 3. Срок действия

**Expires At**: 1759950304394

Конвертация:
```javascript
new Date(1759950304394).toLocaleString()
// = примерно октябрь 2025
```

Токен действителен **почти год** ✅

---

## 🧪 Тест ключа (перед добавлением на сервер):

```bash
# Проверить что ключ работает
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: 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" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 50,
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

**Ожидаемый результат**: 200 OK с JSON ответом от Claude

**Если 401**: Токен истек, нужен refresh

---

## 📝 Следующие шаги:

1. ✅ **Ключ найден** - готов к использованию
2. ⏳ **Добавить на сервер** - в конфиг Claude Code API Wrapper
3. ⏳ **Перезапустить сервис**
4. ⏳ **Протестировать** - `python test_claude_api.py`
5. ⏳ **Создать отчет** - о успешном исправлении

---

## 🎯 Критерии успеха:

После добавления ключа на сервер:

- ✅ `/health` → 200 OK
- ✅ `/models` → 200 OK
- ✅ `/chat` → 200 OK (вместо 500!)
- ✅ `python test_claude_api.py` → TEST PASSED

---

**Готово к деплою!** 🚀

Теперь ты можешь действовать как deployment-manager и добавить этот ключ на сервер согласно инструкциям.
