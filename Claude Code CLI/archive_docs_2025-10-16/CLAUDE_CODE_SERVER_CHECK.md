# Claude Code Server - Checklist для проверки

**Дата**: 2025-10-08
**Задача**: Проверить что credentials скопированы правильно и API wrapper работает

---

## 📋 Checklist для проверки

### ✅ Шаг 1: Проверить SSH доступ

```bash
ssh user@178.236.17.55
# Заменить 'user' на реальный логин
```

**Нужно узнать:**
- Логин пользователя для SSH
- Пароль или путь к SSH ключу

---

### ✅ Шаг 2: Проверить что Claude Code установлен

```bash
# На сервере выполнить:
claude --version

# Должно вернуть:
# 2.0.5 (Claude Code) или похожее
```

**Если ошибка "command not found"**:
- Claude Code не установлен на сервере
- Нужна установка: `npm install -g @anthropic-ai/claude-code`

---

### ✅ Шаг 3: Проверить credentials на сервере

```bash
# Проверить существование файла
ls -la ~/.claude/.credentials.json

# Посмотреть содержимое
cat ~/.claude/.credentials.json

# Должно быть примерно:
# {"claudeAiOauth":{"accessToken":"sk-ant-oat01-...","refreshToken":"sk-ant-ort01-..."}}
```

**Что проверить:**
- [ ] Файл существует
- [ ] Содержит `accessToken` начинающийся с `sk-ant-oat01-`
- [ ] Содержит `refreshToken` начинающийся с `sk-ant-ort01-`
- [ ] Содержит `subscriptionType: "max"`

---

### ✅ Шаг 4: Сравнить с локальным файлом

**На локальной машине** (Windows):
```powershell
# Вычислить хэш локального файла
Get-FileHash "C:\Users\Андрей\.claude\.credentials.json" -Algorithm MD5

# Или посмотреть содержимое
cat "C:\Users\Андрей\.claude\.credentials.json"
```

**На сервере**:
```bash
# Вычислить хэш серверного файла
md5sum ~/.claude/.credentials.json

# Или
cat ~/.claude/.credentials.json
```

**Хэши должны совпадать!**

---

### ✅ Шаг 5: Найти пользователя API wrapper

```bash
# Найти процесс API wrapper
ps aux | grep -i claude
ps aux | grep -i wrapper
ps aux | grep "8000"

# Systemd сервис
sudo systemctl status claude-code-api
# Смотреть строку "Main PID" и "User"

# Docker
docker ps | grep claude
docker inspect claude-code-api | grep User

# PM2
pm2 list
pm2 info claude-code-api
```

**Запиши пользователя**: `___________` (например: `claude-api`, `root`, `ubuntu`)

---

### ✅ Шаг 6: Скопировать credentials для нужного пользователя

**Если API wrapper запущен от другого пользователя** (не твоего):

```bash
# Узнали что wrapper запущен от пользователя 'claude-api'

# Создать директорию для его credentials
sudo mkdir -p /home/claude-api/.claude

# Скопировать файл
sudo cp ~/.claude/.credentials.json /home/claude-api/.claude/

# Установить правильные права
sudo chown claude-api:claude-api /home/claude-api/.claude/.credentials.json
sudo chmod 600 /home/claude-api/.claude/.credentials.json

# Проверить
sudo -u claude-api cat /home/claude-api/.claude/.credentials.json
```

**Если wrapper запущен от root**:
```bash
sudo mkdir -p /root/.claude
sudo cp ~/.claude/.credentials.json /root/.claude/
sudo chmod 600 /root/.claude/.credentials.json
```

---

### ✅ Шаг 7: Проверить переменные окружения wrapper

**Systemd**:
```bash
# Посмотреть конфиг сервиса
sudo systemctl cat claude-code-api

# Найти Environment= или EnvironmentFile=
# Убедиться что НЕ установлена старая ANTHROPIC_API_KEY
```

**Docker**:
```bash
# Проверить environment variables
docker inspect claude-code-api | grep -A 20 Env

# Убедиться что HOME=/home/claude-api или правильный путь
```

---

### ✅ Шаг 8: Перезапустить wrapper

**Systemd**:
```bash
sudo systemctl restart claude-code-api
sudo systemctl status claude-code-api

# Смотреть логи в реальном времени
sudo journalctl -u claude-code-api -f
```

**Docker**:
```bash
docker restart claude-code-api
docker logs claude-code-api -f
```

**PM2**:
```bash
pm2 restart claude-code-api
pm2 logs claude-code-api
```

**Что искать в логах**:
- ❌ "command not found: claude" → Claude не установлен
- ❌ "authentication failed" → credentials неверные
- ❌ "permission denied" → проблемы с правами
- ✅ "Server started" или "Listening on port 8000" → OK

---

### ✅ Шаг 9: Протестировать локально на сервере

```bash
# Health check
curl http://localhost:8000/health

# Models
curl -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  http://localhost:8000/models

# Chat (главный тест!)
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Say hello in Russian","model":"sonnet"}'
```

**Ожидаемый результат /chat**:
```json
{
  "response": "Привет! Как я могу помочь вам сегодня?",
  "session_id": "abc123...",
  "model": "sonnet",
  "timestamp": "2025-10-08T...",
  "status": "success"
}
```

**Если всё ещё 500**:
- Смотри логи wrapper (шаг 8)
- Проверь что Claude CLI работает: `claude --version`
- Попробуй запустить Claude вручную: `echo "Hello" | claude`

---

### ✅ Шаг 10: Протестировать с локальной машины

```bash
# Windows PowerShell:
cd C:\SnowWhiteAI\GrantService
python test_claude_api.py
```

**Ожидаемый результат**:
```
================================================================================
Testing Claude Code API
================================================================================

1. API URL: http://178.236.17.55:8000
2. API Key: 1f79b062cf00b8d28546...cc27aa0732

3. ClaudeCodeClient imported OK

4. Creating client...
   Client created OK

5. Sending test message...
   SUCCESS!
   Response length: 150 chars
   Response preview: Привет! Я Claude, AI-ассистент...

================================================================================
TEST PASSED: Claude API works!
================================================================================
```

---

## 🔍 Troubleshooting

### Проблема 1: "command not found: claude"

**Причина**: Claude Code не установлен на сервере

**Решение**:
```bash
# Установить Node.js (если нет)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Установить Claude Code
sudo npm install -g @anthropic-ai/claude-code

# Проверить
claude --version
```

---

### Проблема 2: "Authentication failed"

**Причина**: Credentials неправильные или не найдены

**Решение**:
```bash
# Проверить что файл читается
cat ~/.claude/.credentials.json

# Проверить формат
cat ~/.claude/.credentials.json | python3 -m json.tool

# Попробовать запустить Claude вручную
echo "Hello" | claude
# Если работает → проблема в wrapper
# Если не работает → проблема в credentials
```

---

### Проблема 3: Wrapper не видит credentials

**Причина**: Wrapper запущен от другого пользователя

**Решение**: Вернись к Шагу 6 и скопируй credentials для правильного пользователя

---

### Проблема 4: Permission denied

**Причина**: Неправильные права доступа

**Решение**:
```bash
# Для текущего пользователя
chmod 600 ~/.claude/.credentials.json

# Для пользователя wrapper
sudo chmod 600 /home/claude-api/.claude/.credentials.json
sudo chown claude-api:claude-api /home/claude-api/.claude/.credentials.json
```

---

## 📊 Финальная проверка

После всех шагов проверь:

- [ ] `claude --version` работает на сервере
- [ ] `cat ~/.claude/.credentials.json` показывает токены
- [ ] `/health` endpoint возвращает 200 OK
- [ ] `/models` endpoint возвращает список моделей
- [ ] `/chat` endpoint возвращает 200 OK (не 500!)
- [ ] `python test_claude_api.py` проходит успешно
- [ ] В логах wrapper нет ошибок

---

## ✅ Критерии успеха

```bash
# Все три команды должны вернуть 200 OK:
curl http://178.236.17.55:8000/health                        # ✅
curl -H "Authorization: Bearer ..." http://178.236.17.55:8000/models  # ✅
curl -X POST -H "Authorization: Bearer ..." -H "Content-Type: application/json" \
  -d '{"message":"test"}' http://178.236.17.55:8000/chat     # ✅ (было 500!)
```

---

## 📝 Отчет после проверки

После выполнения создай краткий отчет:

```markdown
# Отчет о проверке Claude Code Server

## Что нашел:
- Пользователь wrapper: _______
- Путь к credentials: _______
- Claude версия: _______

## Что исправил:
1. _______
2. _______

## Результат:
- [ ] Health: OK
- [ ] Models: OK
- [ ] Chat: OK / FAILED
- [ ] Python test: PASSED / FAILED

## Проблемы (если есть):
_______
```

---

**Готов к проверке!** 🚀 Начинай с Шага 1 (SSH подключение).
