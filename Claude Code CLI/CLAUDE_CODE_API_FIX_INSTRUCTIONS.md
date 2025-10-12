# Claude Code API - Инструкции по Исправлению для Deployment Manager

**Дата**: 2025-10-08
**Для**: @deployment-manager agent
**От**: AI Integration Specialist
**Приоритет**: 🔴 КРИТИЧЕСКИЙ
**Время на исправление**: 15-30 минут

---

## 📋 Краткое Описание Проблемы

**Проблема**: `/chat` endpoint на сервере Claude Code API (http://178.236.17.55:8000) возвращает 500 Internal Server Error.

**Причина** (90% вероятность): Отсутствует или невалиден `ANTHROPIC_API_KEY` в конфигурации сервера.

**Влияние**: Блокирует работу Researcher Agent, AI агентов, снижает качество грантов.

**Диагностический отчет**: `.claude/CLAUDE_CODE_API_DIAGNOSTIC_REPORT.md`

---

## 🎯 Задача

Подключиться к серверу `178.236.17.55` по SSH, найти и исправить проблему с Claude Code API, чтобы `/chat` endpoint заработал.

---

## 📝 Пошаговая Инструкция

### ШАГ 1: Подключение к серверу

```bash
ssh user@178.236.17.55
```

**Если нужен ключ**:
```bash
ssh -i /path/to/key.pem user@178.236.17.55
```

**❓ Если не знаешь логин/пароль**:
- Спроси у пользователя: "Какой логин и пароль для SSH на 178.236.17.55?"
- Или: "Где находится SSH ключ для сервера 178.236.17.55?"

---

### ШАГ 2: Найти Claude Code сервис

Проверь, как запущен сервер - systemd, Docker или PM2:

```bash
# Проверить systemd
sudo systemctl list-units | grep -i claude
sudo systemctl status claude-code-api

# Проверить Docker
docker ps | grep -i claude
docker ps -a | grep -i claude

# Проверить PM2/Node.js
pm2 list | grep -i claude

# Проверить процессы
ps aux | grep -i claude
ps aux | grep -i anthropic
```

**Запиши результат** - это определит дальнейшие действия.

---

### ШАГ 3: Посмотреть логи (САМОЕ ВАЖНОЕ!)

В логах будет точная ошибка!

#### Если systemd:
```bash
sudo journalctl -u claude-code-api -n 100 --no-pager
sudo journalctl -u claude-code-api -f  # real-time логи
```

#### Если Docker:
```bash
docker logs claude-code-api --tail 100
docker logs claude-code-api -f  # real-time логи
```

#### Если PM2:
```bash
pm2 logs claude-code-api --lines 100
```

#### Если файловые логи:
```bash
# Найти лог файлы
find /var/log -name "*claude*" 2>/dev/null
find /opt -name "*.log" -path "*/claude*" 2>/dev/null

# Прочитать
sudo tail -n 100 /var/log/claude-code/error.log
sudo tail -n 100 /var/log/claude-code/access.log
```

**🔍 Что искать в логах**:
- `AuthenticationError: Invalid API key`
- `APIConnectionError: Could not connect to Anthropic API`
- `SSL: CERTIFICATE_VERIFY_FAILED`
- `RateLimitError: Rate limit exceeded`
- Любой Python traceback с ключевыми словами "anthropic", "api", "error"

**📝 Запиши найденную ошибку** - она подскажет точное решение!

---

### ШАГ 4: Найти конфигурационный файл

Нужно найти, где хранится `ANTHROPIC_API_KEY`:

```bash
# Поиск конфигов
find /etc -name "*claude*" 2>/dev/null
find /opt -name "*claude*" 2>/dev/null
find /root -name "*claude*" 2>/dev/null
find /home -name "*claude*" 2>/dev/null

# Поиск .env файлов
find / -name ".env" -path "*/claude*" 2>/dev/null
find / -name "config.yml" -path "*/claude*" 2>/dev/null
find / -name "config.json" -path "*/claude*" 2>/dev/null
```

**Типичные пути**:
- `/etc/claude-code/.env`
- `/opt/claude-code/.env`
- `/root/.config/claude-code/config.json`
- `/home/user/claude-code/.env`
- Docker: рядом с `docker-compose.yml`

#### Если systemd:
```bash
# Проверить переменные окружения сервиса
sudo systemctl show claude-code-api | grep -i env
sudo systemctl show claude-code-api | grep -i anthropic

# Посмотреть unit файл
sudo systemctl cat claude-code-api
```

#### Если Docker:
```bash
# Проверить environment variables
docker inspect claude-code-api | grep -A 20 "Env"

# Найти docker-compose.yml
find / -name "docker-compose.yml" -path "*/claude*" 2>/dev/null

# Посмотреть docker-compose.yml
cat /path/to/docker-compose.yml
```

**📝 Запиши путь к конфигу** - туда нужно будет добавить/обновить ключ.

---

### ШАГ 5: Проверить текущий ANTHROPIC_API_KEY

```bash
# Прочитать конфиг (примеры)
cat /etc/claude-code/.env
cat /opt/claude-code/.env
cat ~/.config/claude-code/config.json

# ИЛИ grep по файлу
grep ANTHROPIC_API_KEY /etc/claude-code/.env
```

**Что должно быть**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**❌ Проблемы**:
1. Переменная отсутствует → **нужно добавить**
2. Значение пустое или "YOUR_API_KEY_HERE" → **нужно заменить**
3. Ключ неправильного формата (не начинается с `sk-ant-`) → **нужно заменить**

---

### ШАГ 6: Получить валидный ANTHROPIC_API_KEY

**❓ Спроси у пользователя**:
```
Мне нужен валидный ANTHROPIC_API_KEY для настройки сервера.

Можешь:
1. Дать существующий ключ (формат: sk-ant-api03-...)
2. Создать новый ключ здесь: https://console.anthropic.com/settings/keys

Какой ключ использовать?
```

**ВАЖНО**: Ключ должен начинаться с `sk-ant-api03-` (это формат Anthropic API v3)

---

### ШАГ 7: Обновить конфигурацию

#### Если конфиг в .env файле:

```bash
# Открыть редактор
sudo nano /etc/claude-code/.env

# Добавить или обновить строку:
ANTHROPIC_API_KEY=sk-ant-api03-ПОЛУЧЕННЫЙ_КЛЮЧ_ОТ_ПОЛЬЗОВАТЕЛЯ

# Сохранить: Ctrl+O, Enter, Ctrl+X
```

#### Если конфиг в docker-compose.yml:

```bash
# Открыть редактор
sudo nano /path/to/docker-compose.yml

# Найти секцию environment: или env_file:
# Добавить или обновить:
environment:
  - ANTHROPIC_API_KEY=sk-ant-api03-ПОЛУЧЕННЫЙ_КЛЮЧ

# Сохранить: Ctrl+O, Enter, Ctrl+X
```

#### Если конфиг в systemd unit:

```bash
# Редактировать unit файл
sudo systemctl edit --full claude-code-api

# Найти секцию [Service]
# Добавить или обновить:
[Service]
Environment="ANTHROPIC_API_KEY=sk-ant-api03-ПОЛУЧЕННЫЙ_КЛЮЧ"

# Сохранить: Ctrl+O, Enter, Ctrl+X

# Перезагрузить systemd
sudo systemctl daemon-reload
```

---

### ШАГ 8: Проверить валидность ключа (ВАЖНО!)

Перед перезапуском сервиса, убедись что ключ работает:

```bash
# Тест прямого запроса к Anthropic API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-api03-ПОЛУЧЕННЫЙ_КЛЮЧ" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 50,
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

**Ожидаемый результат**:
```json
{
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "Hello!"}],
  ...
}
```

**❌ Если ошибка**:
- `401 Unauthorized` → Ключ невалиден, получи новый от пользователя
- `429 Too Many Requests` → Rate limit исчерпан, нужен upgrade плана
- `Connection error` → Проблемы с сетью (смотри ШАГ 10)

**✅ Если 200 OK** → Ключ работает, можно перезапускать сервис!

---

### ШАГ 9: Перезапустить Claude Code сервис

#### Если systemd:
```bash
sudo systemctl restart claude-code-api
sudo systemctl status claude-code-api

# Проверить логи
sudo journalctl -u claude-code-api -f
```

#### Если Docker:
```bash
# Перезапуск контейнера
docker restart claude-code-api

# ИЛИ полный пересбор (если изменили docker-compose.yml)
cd /path/to/docker-compose
docker-compose down
docker-compose up -d

# Проверить логи
docker logs claude-code-api -f
```

#### Если PM2:
```bash
pm2 restart claude-code-api
pm2 logs claude-code-api
```

**🔍 Смотри логи** - должно быть что-то вроде:
- "Claude Code API started"
- "Connected to Anthropic API"
- "Server listening on port 8000"
- **НЕ должно быть** "AuthenticationError" или "APIConnectionError"

---

### ШАГ 10: Проверить что /chat endpoint работает

#### На сервере (локально):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","model":"sonnet","temperature":0.7}'
```

**Ожидаемый результат**:
```json
{
  "response": "Hello! How can I help you today?",
  "session_id": "...",
  "tokens_used": 15
}
```

**❌ Если всё ещё 500** → вернись к ШАГ 3 (логи) и найди новую ошибку

**✅ Если 200 OK** → ОТЛИЧНО! Теперь проверь извне...

#### С локальной машины:

Попроси пользователя запустить:
```bash
cd C:\SnowWhiteAI\GrantService
python test_claude_api.py
```

**Ожидаемый результат**:
```
================================================================================
TEST PASSED: Claude API works!
================================================================================
```

---

### ШАГ 11: Проверить подключение к api.anthropic.com (если всё ещё не работает)

Если после установки валидного ключа всё равно 500:

```bash
# Проверить DNS
nslookup api.anthropic.com
dig api.anthropic.com

# Проверить HTTPS подключение
curl -I https://api.anthropic.com/v1/messages
curl -v https://api.anthropic.com/v1/messages

# Проверить файрвол
sudo iptables -L -n | grep -i 443
sudo ufw status
```

**Если нет подключения**:

```bash
# Открыть исходящие соединения на port 443
sudo ufw allow out 443/tcp
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# Перезапустить сервис
sudo systemctl restart claude-code-api
```

---

### ШАГ 12: Финальная проверка

После успешного исправления проверь все endpoints:

```bash
# Health
curl http://178.236.17.55:8000/health

# Models
curl -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  http://178.236.17.55:8000/models

# Chat
curl -X POST http://178.236.17.55:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Test","model":"sonnet"}'
```

**Все должны вернуть 200 OK!**

---

## 🎯 Критерии Успеха

После исправления:

- ✅ `/health` возвращает 200 OK
- ✅ `/models` возвращает 200 OK
- ✅ `/chat` возвращает 200 OK с ответом Claude
- ✅ `python test_claude_api.py` проходит успешно
- ✅ Логи не содержат ошибок AuthenticationError/APIConnectionError

---

## 📝 Отчёт о Выполнении

После завершения работы создай краткий отчёт:

```markdown
# Claude Code API - Отчёт об Исправлении

**Дата**: 2025-10-08
**Исполнитель**: @deployment-manager

## Что было сделано

1. Подключение к серверу: [описание]
2. Обнаруженная проблема: [из логов]
3. Примененное решение: [что изменил]
4. Результат: [статус endpoints]

## Конфигурация

- Тип сервиса: [systemd/Docker/PM2]
- Путь к конфигу: [путь]
- ANTHROPIC_API_KEY: [первые 20 символов]...

## Тесты

- Health endpoint: [✅/❌]
- Models endpoint: [✅/❌]
- Chat endpoint: [✅/❌]
- Python test: [✅/❌]

## Статус

[✅ ИСПРАВЛЕНО / ❌ ПРОБЛЕМА ОСТАЕТСЯ]

## Рекомендации

[Любые рекомендации по мониторингу, документации и т.д.]
```

Сохрани отчёт в `.claude/agents/deployment-manager/reports/claude_code_api_fix_2025-10-08.md`

---

## ⚠️ Возможные Проблемы

### Проблема 1: Нет sudo прав

**Решение**: Попроси у пользователя:
- sudo пароль
- ИЛИ попроси выполнить команды от его имени
- ИЛИ попроси root доступ

---

### Проблема 2: Не можешь найти конфиг

**Решение**:
```bash
# Найти процесс Claude Code
ps aux | grep claude

# Посмотреть аргументы запуска (покажет путь к конфигу)
ps aux | grep claude | head -1

# Найти все .env файлы
find / -name ".env" 2>/dev/null | grep -i claude
```

---

### Проблема 3: Ключ валиден, но /chat всё равно 500

**Возможные причины**:
1. Кэш конфигурации не обновился → перезагрузи сервер: `sudo reboot`
2. Другая ошибка в коде сервера → посмотри полный traceback в логах
3. Проблемы с SSL сертификатами → проверь: `curl -vvv https://api.anthropic.com`

---

### Проблема 4: Rate Limit исчерпан

**Симптом**: В логах "RateLimitError: Rate limit exceeded"

**Решение**:
1. Проверь usage: https://console.anthropic.com/settings/usage
2. Подожди 1 минуту (лимит обновляется каждую минуту)
3. Если постоянно превышается → нужен upgrade плана
4. Попроси пользователя: "Нужен upgrade Anthropic API tier, текущий лимит исчерпан"

---

## 📞 Когда Обращаться к Пользователю

**Обязательно спроси у пользователя**:

1. SSH доступ:
   - "Какой логин/пароль для SSH на 178.236.17.55?"
   - "Где находится SSH ключ?"

2. API ключ:
   - "Какой ANTHROPIC_API_KEY использовать?"
   - "Можешь создать новый ключ: https://console.anthropic.com/settings/keys"

3. Если проблема не решается:
   - "Проверь пожалуйста логи: [приложи логи]"
   - "Нужна ли помощь системного администратора?"

---

## 🚀 После Успешного Исправления

1. **Проверь Researcher Agent**:
   ```bash
   cd C:\SnowWhiteAI\GrantService
   python test_researcher_websearch.py
   ```

2. **Проверь интеграцию**:
   ```bash
   python test_claude_code_integration.py
   ```

3. **Обнови документацию**:
   - Добавь информацию о ANTHROPIC_API_KEY в deployment docs
   - Обнови QUICK_START если нужно

4. **Сообщи об успехе**:
   ```
   ✅ Claude Code API исправлен!

   Результаты:
   - /health: OK
   - /models: OK
   - /chat: OK
   - Python test: PASSED

   Researcher Agent готов к работе!
   ```

---

**Время выполнения**: 15-30 минут
**Приоритет**: 🔴 КРИТИЧЕСКИЙ
**Следующий шаг**: Начинай с ШАГ 1 (SSH подключение)

**Удачи! 🚀**

---

**Создано**: 2025-10-08
**Автор**: AI Integration Specialist
**Для**: @deployment-manager agent
