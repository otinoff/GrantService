# Решение проблемы "Invalid API key � Fix external API key"

**Дата:** 2025-10-12
**Источник:** WebSearch по официальным источникам Anthropic и GitHub Issues
**Статус проблемы:** Известная проблема, особенно на macOS и SSH соединениях

---

## 🔴 Проблема

```json
{
  "response": "Invalid API key � Fix external API key",
  "status": "success"
}
```

**Описание:**
- Endpoint `/chat` работает (Status: 200)
- API wrapper успешно запущен на сервере
- НО Anthropic OAuth token на сервере невалидный или истёк

---

## 📋 Причины проблемы

### 1. OAuth Token не сохранился (macOS/SSH)
OAuth аутентификация завершилась успешно, но auth token не был сохранён в keychain или `~/.claude/.credentials.json`

**Симптомы:**
- После успешного логина `/login`
- `/status` показывает "Auth Token: none"
- Особенно частая проблема на macOS и SSH соединениях

### 2. Token истёк
OAuth tokens имеют срок действия и требуют обновления через `refreshToken`

**Симптомы:**
- Ранее всё работало
- Сейчас получаете 401 или "Invalid API key"
- Прошло значительное время с момента последней аутентификации

### 3. Неправильный формат credentials
Файл `~/.claude/.credentials.json` повреждён или содержит неправильные данные

**Симптомы:**
- После обновления credentials вручную
- После копирования credentials с другой машины

### 4. API Key vs OAuth конфликт
Claude Code не может определить какой метод аутентификации использовать

**Симптомы:**
- Ошибка: "Expected either apiKey or authToken to be set"
- Установлены оба: ANTHROPIC_API_KEY env variable И OAuth credentials

---

## ✅ Решения

### Решение 1: Обновить OAuth credentials на сервере (РЕКОМЕНДУЕТСЯ)

**Шаг 1:** Получить актуальный credentials.json с локальной машины

**Windows (локально):**
```bash
# Найти credentials.json (может быть в разных местах)
dir C:\Users\%USERNAME%\.claude\.credentials.json /s
type C:\Users\Андрей\.claude\.credentials.json
```

**Linux/macOS (локально):**
```bash
cat ~/.claude/.credentials.json
```

**Шаг 2:** Скопировать credentials на сервер

```bash
# Через SCP
scp C:\Users\Андрей\.claude\.credentials.json root@178.236.17.55:/root/.claude/

# Или вручную через SSH
ssh root@178.236.17.55
nano /root/.claude/.credentials.json
# Вставить содержимое, сохранить (Ctrl+O, Enter, Ctrl+X)
```

**Шаг 3:** Проверить формат credentials

```json
{
  "accessToken": "sk-ant-oat01-...",
  "refreshToken": "sk-ant-ort01-...",
  "expiresAt": 1728123456789,
  "scopes": ["user:inference", "user:profile"]
}
```

**ВАЖНО:**
- `accessToken` - текущий токен доступа (может истечь)
- `refreshToken` - токен для обновления (долгосрочный)
- `expiresAt` - Unix timestamp в миллисекундах
- Если `expiresAt` в прошлом - нужен refresh

**Шаг 4:** Перезапустить Claude Code API wrapper

```bash
ssh root@178.236.17.55

# Найти процесс
ps aux | grep claude-api-wrapper

# Убить процесс
pkill -f claude-api-wrapper

# Перезапустить wrapper (путь может отличаться)
cd /root/claude-api-wrapper  # или где у вас wrapper
nohup python3 claude-api-wrapper.py &

# Проверить логи
tail -50 /var/log/claude-api.log  # если есть логирование
```

**Шаг 5:** Проверить работу

```bash
# Локально
curl -X POST http://178.236.17.55:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -d '{"message":"Напиши слово TEST","model":"sonnet","temperature":0.3}'
```

**Ожидаемый результат:**
```json
{
  "response": "TEST",
  "session_id": "...",
  "model": "sonnet",
  "timestamp": "...",
  "status": "success"
}
```

---

### Решение 2: Использовать API Key вместо OAuth

**Преимущества:**
- Более стабильно (не истекает так часто)
- Проще в настройке
- Работает везде (не зависит от keychain)

**Недостатки:**
- Тарифицируется по кредитам (не Claude Max subscription)
- Нужно вручную пополнять баланс

**Как настроить:**

**Шаг 1:** Получить API Key

1. Зайти на https://console.anthropic.com/
2. Перейти в Settings → API Keys
3. Создать новый ключ "Create Key"
4. Скопировать ключ (начинается с `sk-ant-api03-...`)

**Шаг 2:** Настроить на сервере

```bash
ssh root@178.236.17.55

# Установить env variable
export ANTHROPIC_API_KEY="sk-ant-api03-ВАШ_КЛЮЧ"

# Сделать постоянным (добавить в ~/.bashrc)
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-ВАШ_КЛЮЧ"' >> ~/.bashrc
```

**Шаг 3:** Обновить wrapper чтобы использовал ANTHROPIC_API_KEY

Модифицировать `claude-api-wrapper.py`:

```python
import os

# Проверяем переменную окружения
api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key:
    # Использовать API key напрямую
    client = Anthropic(api_key=api_key)
else:
    # Fallback на OAuth credentials
    client = Anthropic()  # Использует ~/.claude/.credentials.json
```

**Шаг 4:** Перезапустить wrapper (см. Решение 1, Шаг 4)

---

### Решение 3: Переключить Writer Agent на Perplexity (ВРЕМЕННОЕ)

Если нужно срочно, пока чините OAuth:

**В `shared/llm/config.py`:**

```python
"writer": {
    "provider": "perplexity",  # Работает стабильно
    "model": "sonar",          # Llama 3.3 70B, 1200 tokens/sec
    "temperature": 0.7,
    "max_tokens": 8000
},
```

**Преимущества:**
- Работает сразу (Perplexity API key валидный)
- Быстрая генерация (1200 tokens/sec)
- Качественные тексты (Llama 3.3 70B)

**Недостатки:**
- Не используется Claude Max subscription
- Тратится Perplexity API quota

---

### Решение 4: Использовать apiKeyHelper для автообновления

Настроить автоматическое обновление токена:

**В Claude Code settings:**

```json
{
  "apiKeyHelper": "/path/to/refresh-token-script.sh",
  "apiKeyHelperTtl": 300000  // 5 минут
}
```

**Скрипт `refresh-token-script.sh`:**

```bash
#!/bin/bash
# Читаем credentials
CREDS_FILE="$HOME/.claude/.credentials.json"
REFRESH_TOKEN=$(jq -r '.refreshToken' "$CREDS_FILE")
EXPIRES_AT=$(jq -r '.expiresAt' "$CREDS_FILE")

# Проверяем истёк ли токен
NOW=$(date +%s)000  # Миллисекунды
if [ "$EXPIRES_AT" -lt "$NOW" ]; then
    # Обновляем через Anthropic OAuth API
    curl -X POST https://api.anthropic.com/v1/oauth/token \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$REFRESH_TOKEN\",\"grant_type\":\"refresh_token\"}" \
      > /tmp/new_token.json

    # Обновляем credentials.json
    jq -s '.[0] * .[1]' "$CREDS_FILE" /tmp/new_token.json > "${CREDS_FILE}.tmp"
    mv "${CREDS_FILE}.tmp" "$CREDS_FILE"
fi

# Возвращаем актуальный accessToken
jq -r '.accessToken' "$CREDS_FILE"
```

**Сделать исполняемым:**

```bash
chmod +x /path/to/refresh-token-script.sh
```

---

## 🔍 Диагностика проблемы

### Проверка 1: Проверить credentials файл

```bash
ssh root@178.236.17.55
cat /root/.claude/.credentials.json | jq .
```

**Что искать:**
- Есть ли файл вообще?
- Правильный ли формат JSON?
- Есть ли `accessToken`, `refreshToken`, `expiresAt`?
- `expiresAt` в будущем или прошлом?

### Проверка 2: Тест аутентификации напрямую

```python
import anthropic
import os

# Тест с OAuth credentials
try:
    client = anthropic.Anthropic()  # Использует ~/.claude/.credentials.json
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=10,
        messages=[{"role": "user", "content": "TEST"}]
    )
    print("✅ OAuth работает:", message.content[0].text)
except Exception as e:
    print("❌ OAuth ошибка:", e)

# Тест с API key
try:
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{"role": "user", "content": "TEST"}]
        )
        print("✅ API Key работает:", message.content[0].text)
except Exception as e:
    print("❌ API Key ошибка:", e)
```

### Проверка 3: Логи wrapper

```bash
ssh root@178.236.17.55

# Проверить логи (если настроено логирование)
tail -100 /var/log/claude-api.log

# Или запустить wrapper в foreground для отладки
cd /root/claude-api-wrapper
python3 claude-api-wrapper.py
# Смотрим что печатается при запросе
```

### Проверка 4: Health check

```bash
curl http://178.236.17.55:8000/health
```

**Ожидаемый результат:**
```json
{
  "status": "healthy",
  "claude_code": "available",
  "claude_version": "2.0.5 (Claude Code)",
  "active_sessions": 0,
  "features": ["chat", "code", "websearch"]
}
```

---

## 📚 Структура credentials.json (детально)

```json
{
  // Текущий access token (истекает через ~1 час после выдачи)
  "accessToken": "sk-ant-oat01-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

  // Refresh token (долгосрочный, используется для получения новых accessToken)
  "refreshToken": "sk-ant-ort01-YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",

  // Unix timestamp в МИЛЛИСЕКУНДАХ когда accessToken истекает
  // Например: 1728840000000 = 2024-10-13 18:00:00
  "expiresAt": 1728840000000,

  // Разрешения (scopes) для OAuth token
  "scopes": [
    "user:inference",  // Доступ к API для инференса
    "user:profile"     // Доступ к профилю пользователя
  ]
}
```

**Как проверить когда истекает:**

```bash
# На сервере (Linux)
EXPIRES_AT=$(cat ~/.claude/.credentials.json | jq -r '.expiresAt')
EXPIRES_DATE=$(date -d @$(($EXPIRES_AT / 1000)))
echo "Token истекает: $EXPIRES_DATE"

# Сколько осталось времени
NOW=$(date +%s)
DIFF=$((($EXPIRES_AT / 1000) - $NOW))
echo "Осталось секунд: $DIFF"
echo "Осталось часов: $(($DIFF / 3600))"
```

**На Windows (PowerShell):**

```powershell
$creds = Get-Content "$env:USERPROFILE\.claude\.credentials.json" | ConvertFrom-Json
$expiresAt = [DateTimeOffset]::FromUnixTimeMilliseconds($creds.expiresAt)
Write-Host "Token истекает: $expiresAt"

$now = [DateTimeOffset]::UtcNow
$remaining = $expiresAt - $now
Write-Host "Осталось: $($remaining.TotalHours) часов"
```

---

## 🔄 Процедура обновления токена вручную

Если refreshToken ещё валидный, можно получить новый accessToken:

**Шаг 1:** Извлечь refreshToken

```bash
REFRESH_TOKEN=$(cat ~/.claude/.credentials.json | jq -r '.refreshToken')
echo $REFRESH_TOKEN
```

**Шаг 2:** Запросить новый токен у Anthropic

```bash
curl -X POST https://api.anthropic.com/v1/oauth/token \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\",
    \"grant_type\": \"refresh_token\"
  }"
```

**Ответ:**

```json
{
  "access_token": "sk-ant-oat01-НОВЫЙ_ТОКЕН",
  "refresh_token": "sk-ant-ort01-НОВЫЙ_REFRESH_ТОКЕН",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**Шаг 3:** Обновить credentials.json

```bash
# Создать новый credentials.json
cat > ~/.claude/.credentials.json <<EOF
{
  "accessToken": "sk-ant-oat01-НОВЫЙ_ТОКЕН",
  "refreshToken": "sk-ant-ort01-НОВЫЙ_REFRESH_ТОКЕН",
  "expiresAt": $(date -d '+1 hour' +%s)000,
  "scopes": ["user:inference", "user:profile"]
}
EOF
```

**Шаг 4:** Перезапустить wrapper (см. Решение 1, Шаг 4)

---

## 🚨 Частые ошибки

### Ошибка 1: "There was an error parsing the body"

**Причина:** Неправильный формат JSON в запросе к `/chat`

**Решение:**

```bash
# ❌ Неправильно (curl без правильных кавычек)
curl -d {"message":"test"} http://...

# ✅ Правильно (экранированный JSON)
curl -d '{"message":"test","model":"sonnet"}' http://...
```

### Ошибка 2: "Expected either apiKey or authToken to be set"

**Причина:** Claude Code не может определить метод аутентификации

**Решение:**

Выбрать ОДИН метод:

**Вариант А - OAuth:**
```bash
unset ANTHROPIC_API_KEY  # Убрать env variable
# Убедиться что ~/.claude/.credentials.json существует
```

**Вариант Б - API Key:**
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
# Удалить или переименовать ~/.claude/.credentials.json
```

### Ошибка 3: Token expired но refresh не работает

**Причина:** refreshToken тоже истёк (обычно через несколько месяцев)

**Решение:**

Нужна новая аутентификация:

```bash
# На локальной машине (где есть браузер)
claude login

# Скопировать новый ~/.claude/.credentials.json на сервер
scp ~/.claude/.credentials.json root@178.236.17.55:/root/.claude/
```

---

## 📊 Сравнение методов аутентификации

| Метод | Плюсы | Минусы | Рекомендуется для |
|-------|-------|--------|-------------------|
| **OAuth (Claude Max)** | • Включено в Max subscription<br>• Нет ограничений по запросам<br>• Высокие rate limits | • Может истечь<br>• Проблемы с SSH/keychain<br>• Сложнее настроить | Production с Max subscription |
| **API Key** | • Стабильно<br>• Легко настроить<br>• Работает везде | • Платно (по кредитам)<br>• Нужно пополнять баланс<br>• Ниже rate limits | Development, тестирование |
| **Hybrid (apiKeyHelper)** | • Автообновление OAuth<br>• Fallback на API key | • Сложная настройка<br>• Нужен скрипт | Advanced production setup |

---

## 🎯 Рекомендация для GrantService

**Текущая ситуация:**
- Writer Agent должен писать гранты
- Нужна стабильность
- Есть Claude Max subscription

**Рекомендуемое решение:**

1. **Краткосрочно (сегодня):**
   - Обновить credentials.json на сервере (Решение 1)
   - Проверить что Writer работает

2. **Среднесрочно (эта неделя):**
   - Настроить мониторинг expiry (скрипт проверки)
   - Добавить алерт за 7 дней до истечения
   - Создать backup API key на случай проблем

3. **Долгосрочно (следующий месяц):**
   - Настроить apiKeyHelper для автообновления
   - Добавить Hybrid mode (OAuth + API key fallback)
   - Документировать процедуру обновления

---

## 📞 Дополнительная помощь

### Официальные ресурсы:

- **Claude API Docs:** https://docs.claude.com/en/api/errors
- **Claude Code Issues:** https://github.com/anthropics/claude-code/issues
- **IAM Guide:** https://docs.claude.com/en/docs/claude-code/iam

### Полезные GitHub Issues:

- Invalid API key fix: https://github.com/anthropics/claude-code/issues/2356
- OAuth persistence: https://github.com/anthropics/claude-code/issues/5244
- API Key usage: https://github.com/anthropics/claude-code/issues/441

### Если ничего не помогло:

1. Собрать диагностику:
   ```bash
   # Версия Claude Code
   claude --version

   # Статус
   claude /status

   # Credentials
   cat ~/.claude/.credentials.json | jq .

   # Логи wrapper
   tail -100 /var/log/claude-api.log
   ```

2. Создать issue на GitHub с деталями

3. Контакт Anthropic Support: support@anthropic.com (с request-id из ответа API)

---

**Последнее обновление:** 2025-10-12
**Автор:** Claude Code Expert Agent
**Версия:** 1.0
