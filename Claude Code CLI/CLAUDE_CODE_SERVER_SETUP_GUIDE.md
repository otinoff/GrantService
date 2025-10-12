# Claude Code API Server - Setup & Configuration Guide

**Дата**: 2025-10-08
**Для**: Deployment Manager / System Administrator
**От**: Grant Architect
**Приоритет**: 🔴 КРИТИЧЕСКИЙ
**Статус**: ⚠️ Сервер частично работает, /chat endpoint падает с 500

---

## 📋 Краткое Резюме Проблемы

**Что работает**:
- ✅ Сервер доступен: `http://178.236.17.55:8000`
- ✅ Health check: `/health` возвращает 200 OK
- ✅ Models endpoint: `/models` работает корректно
- ✅ Авторизация: Bearer token проходит

**Что НЕ работает**:
- ❌ Chat endpoint: `/chat` возвращает 500 Internal Server Error
- ❌ WebSearch функционал недоступен (зависит от /chat)
- ❌ Researcher Agent не может выполнять запросы

**Критичность**:
- Блокирует работу Researcher Agent
- Блокирует WebSearch интеграцию
- Блокирует повышение качества грантов с 10-15% до 40-50%

---

## 🔍 Диагностика

### 1. Health Endpoint (✅ Работает)

```bash
curl -s http://178.236.17.55:8000/health
```

**Ответ**:
```json
{
  "status": "healthy",
  "claude_code": "available",
  "claude_version": "2.0.5 (Claude Code)",
  "active_sessions": 15,
  "timestamp": "2025-10-08T10:40:49.489221"
}
```

**Вывод**: Сервер запущен и отвечает.

### 2. Models Endpoint (✅ Работает)

```bash
curl -s -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  http://178.236.17.55:8000/models
```

**Ответ**:
```json
{
  "models": [
    {
      "id": "sonnet",
      "name": "Claude Sonnet 4.5",
      "description": "Быстрая модель для большинства задач"
    },
    {
      "id": "opus",
      "name": "Claude Opus 4",
      "description": "Мощная модель для сложных задач"
    }
  ]
}
```

**Вывод**: Авторизация работает, модели определены.

### 3. Chat Endpoint (❌ НЕ работает)

```bash
curl -s -X POST http://178.236.17.55:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","model":"sonnet","temperature":0.7}'
```

**Ответ**:
```json
{
  "detail": "500: Claude Code ������: "
}
```

**HTTP Status**: 500 Internal Server Error

**Вывод**: Сервер не может обработать запрос к Claude API.

---

## 🎯 Задачи для Настройки

### Задача 1: Проверить Логи Сервера (ПРИОРИТЕТ 1)

**Цель**: Выяснить точную причину 500 ошибки.

**Команды**:
```bash
# Проверить логи Claude Code сервера
journalctl -u claude-code-api -f --since "10 minutes ago"

# ИЛИ если логи в файле
tail -f /var/log/claude-code/error.log
tail -f /var/log/claude-code/access.log

# ИЛИ Docker логи
docker logs claude-code-api --tail 100 -f
```

**Что искать**:
- Ошибки подключения к Anthropic API
- API key errors
- Timeout errors
- SSL/TLS certificate errors
- Network errors

**Ожидаемые проблемы**:
1. `anthropic.APIConnectionError: Could not connect to Anthropic API`
2. `anthropic.AuthenticationError: Invalid API key`
3. `anthropic.RateLimitError: Rate limit exceeded`
4. `SSL: CERTIFICATE_VERIFY_FAILED`

---

### Задача 2: Проверить Anthropic API Key (ПРИОРИТЕТ 1)

**Цель**: Убедиться, что на сервере настроен валидный Anthropic API ключ.

**Где искать конфигурацию**:
```bash
# Проверить переменные окружения
echo $ANTHROPIC_API_KEY

# Проверить конфигурационный файл
cat /etc/claude-code/config.yml
cat /opt/claude-code/.env
cat ~/.config/claude-code/config.json

# Проверить Docker environment
docker inspect claude-code-api | grep -A 10 "Env"
```

**Что должно быть**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Как проверить ключ напрямую**:
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**Если ключ невалиден**:
1. Получить новый ключ: https://console.anthropic.com/settings/keys
2. Обновить конфигурацию сервера
3. Перезапустить сервис

---

### Задача 3: Проверить Подключение к Anthropic API (ПРИОРИТЕТ 1)

**Цель**: Убедиться, что сервер может достучаться до api.anthropic.com.

**Команды**:
```bash
# Проверить DNS
nslookup api.anthropic.com

# Проверить HTTPS подключение
curl -I https://api.anthropic.com/v1/messages

# Проверить с сервера (если SSH доступ)
ssh user@178.236.17.55 "curl -I https://api.anthropic.com/v1/messages"

# Проверить файрвол
iptables -L -n | grep -i 443
ufw status
```

**Что должно работать**:
- DNS резолвинг api.anthropic.com → IP адрес
- HTTPS доступ (port 443) к api.anthropic.com
- TLS/SSL handshake успешный

**Если проблемы с сетью**:
1. Открыть port 443 для исходящих соединений
2. Добавить api.anthropic.com в whitelist файрвола
3. Проверить proxy настройки (если используется)

---

### Задача 4: Перезапустить Claude Code Service (ПРИОРИТЕТ 2)

**Цель**: Применить изменения после исправления конфигурации.

**Команды**:

**Если systemd**:
```bash
# Проверить статус
sudo systemctl status claude-code-api

# Перезапустить
sudo systemctl restart claude-code-api

# Проверить логи
sudo journalctl -u claude-code-api -f

# Включить автозапуск
sudo systemctl enable claude-code-api
```

**Если Docker**:
```bash
# Проверить статус
docker ps | grep claude-code

# Перезапустить контейнер
docker restart claude-code-api

# Пересоздать контейнер (если изменена конфигурация)
docker-compose down
docker-compose up -d

# Проверить логи
docker logs claude-code-api -f
```

**Если PM2/Node.js**:
```bash
# Проверить статус
pm2 list

# Перезапустить
pm2 restart claude-code-api

# Проверить логи
pm2 logs claude-code-api
```

---

### Задача 5: Проверить Версию Claude Code (ПРИОРИТЕТ 3)

**Цель**: Убедиться, что используется актуальная версия с поддержкой /chat endpoint.

**Текущая версия**: `2.0.5 (Claude Code)`

**Команды**:
```bash
# Проверить версию
claude-code --version

# Обновить до последней версии
pip install --upgrade claude-code
# ИЛИ
npm install -g @anthropic-ai/claude-code@latest
```

**Минимальная требуемая версия**: 2.0.0+

---

### Задача 6: Проверить Rate Limits (ПРИОРИТЕТ 3)

**Цель**: Убедиться, что не исчерпан лимит API запросов.

**Проверить в Anthropic Console**:
1. Открыть: https://console.anthropic.com/settings/usage
2. Проверить текущее использование
3. Проверить лимиты плана

**Типичные лимиты**:
- **Free Tier**: 5 RPM (requests per minute)
- **Tier 1**: 50 RPM
- **Tier 2**: 1000 RPM

**Если лимит исчерпан**:
1. Подождать 1 минуту (rate limit обновляется)
2. Upgrade плана подписки
3. Настроить retry механизм с exponential backoff

---

## 🛠 Полная Процедура Настройки

### Шаг 1: SSH подключение к серверу

```bash
ssh user@178.236.17.55
```

### Шаг 2: Найти Claude Code сервис

```bash
# Проверить процессы
ps aux | grep -i claude
ps aux | grep -i anthropic

# Проверить systemd services
systemctl list-units | grep -i claude

# Проверить Docker контейнеры
docker ps -a | grep -i claude

# Проверить PM2 процессы
pm2 list
```

### Шаг 3: Найти конфигурацию

```bash
# Искать конфиги
find /etc -name "*claude*" 2>/dev/null
find /opt -name "*claude*" 2>/dev/null
find ~ -name "*claude*" 2>/dev/null

# Искать .env файлы
find / -name ".env" -path "*/claude*" 2>/dev/null

# Проверить Docker Compose файл
find / -name "docker-compose.yml" -path "*/claude*" 2>/dev/null
```

### Шаг 4: Проверить и обновить API ключ

```bash
# Редактировать конфиг (пример)
sudo nano /etc/claude-code/.env

# Добавить/обновить:
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxx
ANTHROPIC_API_URL=https://api.anthropic.com
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Шаг 5: Перезапустить сервис

```bash
# Systemd
sudo systemctl restart claude-code-api

# Docker
docker restart claude-code-api

# PM2
pm2 restart claude-code-api
```

### Шаг 6: Проверить логи

```bash
# Смотреть логи в реальном времени
sudo journalctl -u claude-code-api -f

# Проверить последние ошибки
sudo journalctl -u claude-code-api --since "5 minutes ago" | grep -i error
```

### Шаг 7: Протестировать /chat endpoint

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Test message","model":"sonnet","temperature":0.7}'
```

**Ожидаемый результат**:
```json
{
  "response": "Test response from Claude",
  "session_id": "...",
  "tokens_used": 50
}
```

---

## 📝 Конфигурационный Файл (Пример)

### `.env` или `config.yml`

```yaml
# Anthropic API Configuration
ANTHROPIC_API_KEY: sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_URL: https://api.anthropic.com
ANTHROPIC_API_VERSION: 2023-06-01

# Claude Code Server Configuration
SERVER_HOST: 0.0.0.0
SERVER_PORT: 8000
LOG_LEVEL: INFO

# Model Configuration
DEFAULT_MODEL: claude-3-5-sonnet-20241022
DEFAULT_TEMPERATURE: 0.7
DEFAULT_MAX_TOKENS: 4000

# Rate Limiting
RATE_LIMIT_RPM: 50
RATE_LIMIT_TOKENS_PER_MIN: 40000

# Security
API_KEY: 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
ALLOWED_ORIGINS: ["*"]

# Features
ENABLE_WEBSEARCH: true
ENABLE_CODE_EXECUTION: true
ENABLE_SESSIONS: true

# Logging
LOG_DIR: /var/log/claude-code
LOG_FILE: claude-code-api.log
ERROR_LOG_FILE: claude-code-error.log
```

---

## 🔧 Troubleshooting Checklist

### Checklist для проверки:

- [ ] Сервер доступен (ping, /health endpoint)
- [ ] Anthropic API ключ настроен в конфиге
- [ ] Anthropic API ключ валиден (тест через curl)
- [ ] Сеть позволяет подключение к api.anthropic.com (curl test)
- [ ] Нет rate limit ошибок (проверить usage в console)
- [ ] Логи не показывают ошибок (journalctl/docker logs)
- [ ] Версия Claude Code актуальная (2.0.0+)
- [ ] /chat endpoint возвращает 200 OK (curl test)
- [ ] WebSearch работает (тест с запросом)

### Если всё ещё не работает:

1. **Проверить порты**:
```bash
netstat -tulpn | grep 8000
lsof -i :8000
```

2. **Проверить права доступа**:
```bash
ls -la /var/log/claude-code/
ls -la /etc/claude-code/
```

3. **Переустановить сервис**:
```bash
# Systemd
sudo systemctl stop claude-code-api
sudo apt remove claude-code  # или pip uninstall
sudo apt install claude-code # или pip install
sudo systemctl start claude-code-api

# Docker
docker-compose down
docker-compose pull
docker-compose up -d
```

---

## 🎯 Критерии Успеха

После настройки должны работать:

1. **Health Check**:
```bash
curl http://178.236.17.55:8000/health
# → {"status": "healthy"}
```

2. **Chat Endpoint**:
```bash
curl -X POST http://178.236.17.55:8000/chat \
  -H "Authorization: Bearer ..." \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","model":"sonnet"}'
# → {"response": "Hello! How can I help you?", ...}
```

3. **Python Test**:
```bash
cd C:\SnowWhiteAI\GrantService
python test_claude_api.py
# → TEST PASSED: Claude API works!
```

4. **Researcher Agent Test**:
```bash
python test_researcher_websearch.py
# → SUCCESS: Research completed!
```

---

## 📞 Контакты

**Если проблемы сохраняются**:

1. Проверить документацию Anthropic:
   - https://docs.anthropic.com/claude/reference/getting-started-with-the-api

2. Проверить Claude Code documentation:
   - https://github.com/anthropics/claude-code

3. Открыть issue в GitHub:
   - https://github.com/anthropics/claude-code/issues

4. Обратиться в Anthropic Support:
   - support@anthropic.com

---

## 📊 Ожидаемый Результат

После успешной настройки:

- ✅ `/chat` endpoint возвращает 200 OK
- ✅ WebSearch функционал работает
- ✅ Researcher Agent выполняет запросы
- ✅ Сохранение результатов в БД работает
- ✅ Качество грантов повышается с 10-15% до 40-50%

**Время на настройку**: 30-60 минут
**Приоритет**: 🔴 КРИТИЧЕСКИЙ
**Блокирует**: Researcher Agent, WebSearch, Quality Improvement

---

**Создано**: 2025-10-08
**Автор**: Grant Architect
**Статус**: Ready for Deployment Manager

