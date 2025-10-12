# Детальная Инструкция: Настройка Claude Code CLI Wrapper на 178.236.17.55

**Дата создания:** 2025-10-12
**Версия:** 1.0
**Статус:** PRODUCTION READY
**Сервер:** 178.236.17.55

---

## 📋 Содержание

1. [Требования](#требования)
2. [Шаг 1: Установка Claude CLI](#шаг-1-установка-claude-cli)
3. [Шаг 2: OAuth Авторизация](#шаг-2-oauth-авторизация)
4. [Шаг 3: Проверка Работоспособности](#шаг-3-проверка-работоспособности)
5. [Шаг 4: Установка Зависимостей Python](#шаг-4-установка-зависимостей-python)
6. [Шаг 5: Создание Wrapper Скрипта](#шаг-5-создание-wrapper-скрипта)
7. [Шаг 6: Тестирование Wrapper](#шаг-6-тестирование-wrapper)
8. [Шаг 7: Настройка Systemd Service](#шаг-7-настройка-systemd-service)
9. [Шаг 8: Финальное Тестирование](#шаг-8-финальное-тестирование)
10. [Troubleshooting](#troubleshooting)
11. [Мониторинг](#мониторинг)
12. [Backup и Восстановление](#backup-и-восстановление)

---

## Требования

### Сервер
- **IP:** 178.236.17.55
- **OS:** Ubuntu 22.04 или новее
- **User:** root (или sudo доступ)
- **Доступ:** SSH ключ или пароль
- **Сеть:** НЕ российский IP (Claude доступен)

### Программное Обеспечение
- Python 3.12+
- Node.js 18+ (для Claude CLI)
- curl, wget (обычно уже установлены)

### Доступы
- SSH доступ к серверу 178.236.17.55
- Anthropic Max subscription ($200/мес)
- Браузер для OAuth авторизации

---

## Шаг 1: Установка Claude CLI

### 1.1 Подключение к Серверу

```bash
# С локальной машины
ssh root@178.236.17.55
```

**Что проверить:**
- ✅ SSH подключение успешно
- ✅ Вы видите приглашение командной строки

### 1.2 Проверка Node.js

```bash
# Проверить версию Node.js
node --version
```

**Ожидаемый результат:**
```
v18.20.8 или новее
```

**Если Node.js НЕ установлен:**

```bash
# Установка Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Проверка установки
node --version
npm --version
```

### 1.3 Установка Claude CLI

```bash
# Установка глобально через npm
npm install -g @anthropic-ai/claude-code

# Проверка установки
claude --version
```

**Ожидаемый результат:**
```
2.0.5 (Claude Code)
```

**Если команда не найдена:**

```bash
# Найти где установлен
which claude

# Если не нашли - проверить npm global path
npm config get prefix
# Должно быть: /usr или /usr/local

# Добавить в PATH если нужно
export PATH=$PATH:/usr/local/bin
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
```

---

## Шаг 2: OAuth Авторизация

### 2.1 Запуск Авторизации

```bash
# На сервере 178.236.17.55
claude login
```

**Что произойдёт:**

Вы увидите примерно такое:

```
To authenticate, please open this URL in your browser:

https://claude.ai/oauth/authorize?client_id=...&response_type=code&...

Waiting for authentication...
```

### 2.2 Авторизация в Браузере

**ВАЖНО:** Браузер должен быть на машине С доступом к Claude (не заблокирован).

**Варианты:**

#### Вариант A: Локальный Браузер (РЕКОМЕНДУЕТСЯ)

1. **Скопируйте URL** из терминала
2. **Откройте на локальной машине** в браузере
3. **Авторизуйтесь** через Anthropic аккаунт:
   - Email/пароль
   - Или Google OAuth
4. **Подтвердите доступ** к Max subscription
5. **Дождитесь сообщения** "Authentication successful"

#### Вариант B: SSH Туннель (если вариант A не работает)

```bash
# На локальной машине (НЕ на сервере!)
ssh -L 8080:localhost:8080 root@178.236.17.55

# В другом терминале на сервере
claude login --port 8080

# Откройте в локальном браузере
# http://localhost:8080
```

### 2.3 Проверка Credentials

```bash
# Проверить что файл создан
ls -la ~/.claude/.credentials.json
```

**Ожидаемый результат:**
```
-rw-r--r-- 1 root root 364 Oct 12 14:19 /root/.claude/.credentials.json
```

**Проверить содержимое (безопасно - без секретов):**

```bash
cat ~/.claude/.credentials.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
oauth = data.get('claudeAiOauth', {})
print(f\"Subscription: {oauth.get('subscriptionType')}\")
print(f\"Expires: {oauth.get('expiresAt')}\")
print(f\"Scopes: {oauth.get('scopes')}\")
"
```

**Ожидаемый результат:**
```
Subscription: max
Expires: 1760293563957
Scopes: ['user:inference', 'user:profile']
```

**Проверить что не истёк:**

```bash
python3 -c "
import json, time
with open('/root/.claude/.credentials.json') as f:
    data = json.load(f)
expires = data['claudeAiOauth']['expiresAt'] / 1000
now = time.time()
remaining = (expires - now) / 86400
print(f'Токен действителен ещё {remaining:.1f} дней')
if remaining < 1:
    print('⚠️ ВНИМАНИЕ: Токен скоро истечёт!')
elif remaining < 0:
    print('❌ ОШИБКА: Токен истёк!')
else:
    print('✅ Токен валиден')
"
```

---

## Шаг 3: Проверка Работоспособности

### 3.1 Тест Headless Режима

```bash
# Простой тест
claude -p "Напиши одно слово: ТЕСТ"
```

**Ожидаемый результат:**
```
ТЕСТ
```

**Если ошибка "Invalid OAuth token":**
- Повторить Шаг 2 (OAuth авторизация)

**Если ошибка "Command not found":**
- Повторить Шаг 1.3 (установка + PATH)

### 3.2 Тест JSON Output

```bash
# Тест с JSON форматом
claude -p --output-format json "Напиши одно слово: УСПЕХ"
```

**Ожидаемый результат:** JSON объект типа:
```json
{
  "type": "result",
  "subtype": "success",
  "result": "УСПЕХ",
  "duration_ms": 2708,
  "total_cost_usd": 0.00607365,
  "usage": {
    "input_tokens": 3,
    "output_tokens": 6,
    ...
  }
}
```

**Если выдаёт текст вместо JSON:**
- Проверьте версию: `claude --version` (должна быть 2.0+)
- Обновите: `npm update -g @anthropic-ai/claude-code`

### 3.3 Тест Сложного Промпта

```bash
# Генерация текста
claude -p "Write one professional sentence about AI in healthcare."
```

**Ожидаемый результат:** Качественный английский текст

---

## Шаг 4: Установка Зависимостей Python

### 4.1 Проверка Python

```bash
# Версия Python
python3 --version
```

**Ожидаемый результат:**
```
Python 3.12.x или 3.11.x
```

### 4.2 Установка FastAPI и Uvicorn

```bash
# Попытка обычной установки
pip3 install fastapi uvicorn
```

**Если ошибка "externally-managed-environment":**

```bash
# Установка с флагом
pip3 install fastapi uvicorn --break-system-packages
```

**Проверка установки:**

```bash
python3 -c "import fastapi; import uvicorn; print('FastAPI OK')"
```

**Ожидаемый результат:**
```
FastAPI OK
```

---

## Шаг 5: Создание Wrapper Скрипта

### 5.1 Создать Директорию (опционально)

```bash
# Создать папку для wrapper (опционально)
mkdir -p /opt/claude-wrapper
cd /opt/claude-wrapper
```

**ИЛИ использовать /root:**

```bash
cd /root
```

### 5.2 Создать Скрипт

```bash
# Создать файл wrapper
cat > /root/claude_wrapper.py << 'EOF'
#!/usr/bin/env python3
"""
Claude Code Wrapper Server
Предоставляет HTTP API для Claude CLI headless mode
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
import asyncio
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "sonnet"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {
        "status": "healthy",
        "service": "Claude Code Wrapper",
        "server": "178.236.17.55",
        "oauth": "max_subscription"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Чат с Claude через локальный CLI"""
    try:
        logger.info(f"📨 Request: {len(request.message)} chars, model={request.model}")

        # Формируем команду
        cmd = [
            "claude",
            "-p",
            "--output-format", "json",
            request.message
        ]

        logger.info(f"🚀 Starting Claude CLI...")

        # Запускаем через subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Ждём результат (с таймаутом)
        timeout = min(request.max_tokens / 10, 120) if request.max_tokens else 60

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            raise HTTPException(status_code=504, detail="Claude CLI timeout")

        # Проверяем код возврата
        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            logger.error(f"❌ CLI error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"CLI error: {error_msg}")

        # Парсим JSON ответ
        output = stdout.decode("utf-8")
        response_data = json.loads(output)

        # Извлекаем результат
        if response_data.get("type") == "result" and response_data.get("subtype") == "success":
            result = response_data.get("result", "").strip()

            logger.info(f"✅ Response: {len(result)} chars, ${response_data.get('total_cost_usd', 0):.4f}")

            return {
                "response": result,
                "model": request.model,
                "session_id": None,
                "usage": response_data.get("usage", {}),
                "cost": response_data.get("total_cost_usd", 0),
                "duration_ms": response_data.get("duration_ms", 0)
            }
        else:
            error = response_data.get("error", "Unknown error")
            raise HTTPException(status_code=500, detail=f"Claude error: {error}")

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {e}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
```

### 5.3 Сделать Исполняемым

```bash
chmod +x /root/claude_wrapper.py
```

### 5.4 Проверить Файл

```bash
# Проверить что создан
ls -lh /root/claude_wrapper.py
```

**Ожидаемый результат:**
```
-rwxr-xr-x 1 root root 3.5K Oct 12 15:43 /root/claude_wrapper.py
```

---

## Шаг 6: Тестирование Wrapper

### 6.1 Запуск Wrapper Вручную

```bash
# Запустить в фоне
nohup python3 /root/claude_wrapper.py > /tmp/claude_wrapper.log 2>&1 &

# Подождать 2 секунды
sleep 2

# Проверить что запустился
ps aux | grep claude_wrapper | grep -v grep
```

**Ожидаемый результат:** Процесс python3 запущен

### 6.2 Проверить Логи

```bash
tail -20 /tmp/claude_wrapper.log
```

**Ожидаемый результат:**
```
INFO:     Started server process [184295]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 6.3 Тест Health Endpoint

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Ожидаемый результат:**
```json
{
  "status": "healthy",
  "service": "Claude Code Wrapper",
  "server": "178.236.17.55",
  "oauth": "max_subscription"
}
```

**Если ошибка "Connection refused":**
- Проверить что wrapper запущен: `ps aux | grep claude_wrapper`
- Проверить логи: `tail /tmp/claude_wrapper.log`
- Проверить порт: `netstat -tulpn | grep 8000`

### 6.4 Тест Chat Endpoint

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Напиши одно слово: РАБОТАЕТ", "model": "sonnet", "max_tokens": 100}' \
  | python3 -m json.tool
```

**Ожидаемый результат:**
```json
{
  "response": "РАБОТАЕТ",
  "model": "sonnet",
  "session_id": null,
  "usage": {
    "input_tokens": 4,
    "output_tokens": 7,
    ...
  },
  "cost": 0.00607365,
  "duration_ms": 2708
}
```

### 6.5 Тест Сложного Запроса

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a professional sentence about artificial intelligence in healthcare.",
    "model": "opus",
    "max_tokens": 200
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['response'])"
```

**Ожидаемый результат:** Качественный английский текст

### 6.6 Остановка Тестового Wrapper

```bash
# Найти PID
ps aux | grep claude_wrapper | grep -v grep

# Убить процесс
pkill -f claude_wrapper.py

# Или
killall -9 python3  # ОСТОРОЖНО! Убьёт все python процессы
```

---

## Шаг 7: Настройка Systemd Service

### 7.1 Создать Service Файл

```bash
cat > /etc/systemd/system/claude-wrapper.service << 'EOF'
[Unit]
Description=Claude Code API Wrapper
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/claude_wrapper.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/claude-wrapper.log
StandardError=append:/var/log/claude-wrapper.log

# Ограничения ресурсов (опционально)
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF
```

**Объяснение параметров:**

- `After=network.target` - запускать после сети
- `Type=simple` - простой процесс
- `Restart=always` - автоматически перезапускать при падении
- `RestartSec=10` - ждать 10 секунд перед перезапуском
- `StandardOutput/Error` - логи в /var/log/claude-wrapper.log
- `MemoryLimit=512M` - не более 512MB RAM
- `CPUQuota=50%` - не более 50% CPU

### 7.2 Перезагрузить Systemd

```bash
systemctl daemon-reload
```

### 7.3 Включить Автозапуск

```bash
systemctl enable claude-wrapper.service
```

**Ожидаемый результат:**
```
Created symlink /etc/systemd/system/multi-user.target.wants/claude-wrapper.service → /etc/systemd/system/claude-wrapper.service.
```

### 7.4 Запустить Service

```bash
systemctl start claude-wrapper.service
```

### 7.5 Проверить Статус

```bash
systemctl status claude-wrapper.service --no-pager
```

**Ожидаемый результат:**
```
● claude-wrapper.service - Claude Code API Wrapper
     Loaded: loaded (/etc/systemd/system/claude-wrapper.service; enabled; preset: enabled)
     Active: active (running) since Sun 2025-10-12 15:48:23 UTC; 2s ago
   Main PID: 185111 (python3)
      Tasks: 1 (limit: 4655)
     Memory: 30.2M (peak: 30.2M)
        CPU: 625ms
     CGroup: /system.slice/claude-wrapper.service
             └─185111 /usr/bin/python3 /root/claude_wrapper.py

Oct 12 15:48:23 ctytdjxzil systemd[1]: Started claude-wrapper.service - Claude Code API Wrapper.
```

**Ключевые строки:**

- `Active: active (running)` ✅ - работает
- `Loaded: ... enabled` ✅ - автозапуск включён

**Если ошибка:**

```bash
# Посмотреть детали ошибки
journalctl -u claude-wrapper.service -n 50 --no-pager
```

### 7.6 Проверить Логи

```bash
tail -20 /var/log/claude-wrapper.log
```

---

## Шаг 8: Финальное Тестирование

### 8.1 Тест с Локального Сервера

```bash
# На сервере 178.236.17.55
curl -s http://localhost:8000/health
```

**Ожидаемый результат:** `{"status":"healthy",...}`

### 8.2 Тест с Внешнего IP

**С локальной машины (Windows/Mac/Linux):**

```bash
curl -s http://178.236.17.55:8000/health
```

**Ожидаемый результат:** `{"status":"healthy",...}`

**Если ошибка "Connection refused":**

Проверить firewall на сервере:

```bash
# На сервере 178.236.17.55
ufw status

# Если порт заблокирован
ufw allow 8000/tcp
ufw reload
```

### 8.3 Тест с Production Сервера

```bash
# На production сервере 5.35.88.251
ssh root@5.35.88.251
curl -s http://178.236.17.55:8000/health
```

**Ожидаемый результат:** `{"status":"healthy",...}`

### 8.4 Тест Генерации Текста

**С локальной машины:**

```bash
curl -X POST http://178.236.17.55:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a one-sentence summary of quantum computing.",
    "model": "opus",
    "max_tokens": 150
  }'
```

**Ожидаемый результат:** JSON с качественным текстом про квантовые компьютеры

### 8.5 Проверка Автозапуска

**Тест перезагрузки:**

```bash
# На сервере 178.236.17.55
systemctl reboot
```

**После перезагрузки (подождать 1-2 минуты):**

```bash
# Подключиться снова
ssh root@178.236.17.55

# Проверить что запустился автоматически
systemctl status claude-wrapper.service
```

**Ожидаемый результат:** `Active: active (running)`

**Проверить что API работает:**

```bash
curl -s http://localhost:8000/health
```

---

## Troubleshooting

### Проблема 1: OAuth Истёк

**Симптомы:**
```
Error 401: Unauthorized
Token expired
```

**Решение:**

```bash
# Перелогиниться
claude login

# Следовать инструкциям OAuth (Шаг 2)

# Перезапустить wrapper
systemctl restart claude-wrapper.service
```

### Проблема 2: Wrapper Не Запускается

**Симптомы:**
```
systemctl status claude-wrapper.service
Active: failed
```

**Диагностика:**

```bash
# Смотреть детальные ошибки
journalctl -u claude-wrapper.service -n 100 --no-pager

# Проверить логи
tail -50 /var/log/claude-wrapper.log

# Попытаться запустить вручную
python3 /root/claude_wrapper.py
```

**Частые причины:**

1. **FastAPI не установлен:**
   ```bash
   pip3 install fastapi uvicorn --break-system-packages
   ```

2. **Claude CLI не найден:**
   ```bash
   which claude
   # Если пусто - установить (Шаг 1)
   ```

3. **Порт 8000 занят:**
   ```bash
   netstat -tulpn | grep 8000
   # Убить процесс на 8000 или изменить порт в wrapper
   ```

### Проблема 3: Connection Refused Извне

**Симптомы:**
```bash
curl http://178.236.17.55:8000/health
curl: (7) Failed to connect to 178.236.17.55 port 8000: Connection refused
```

**Решение:**

```bash
# Проверить что wrapper слушает на 0.0.0.0 (не 127.0.0.1)
netstat -tulpn | grep 8000

# Должно быть:
# tcp  0  0  0.0.0.0:8000  0.0.0.0:*  LISTEN  185111/python3

# Если 127.0.0.1:8000 - проверить код wrapper
# uvicorn.run(app, host="0.0.0.0", port=8000)  ← должно быть 0.0.0.0

# Проверить firewall
ufw status
ufw allow 8000/tcp
```

### Проблема 4: Wrapper Медленно Отвечает

**Симптомы:**
- Запросы занимают >30 секунд
- Timeouts

**Решение:**

```bash
# Проверить нагрузку сервера
top

# Проверить memory
free -h

# Проверить Claude CLI
claude -p "test" --output-format json

# Увеличить ресурсы в systemd
nano /etc/systemd/system/claude-wrapper.service
# Изменить:
# MemoryLimit=1G
# CPUQuota=100%

systemctl daemon-reload
systemctl restart claude-wrapper.service
```

### Проблема 5: JSON Parse Error

**Симптомы:**
```
Invalid JSON response
```

**Решение:**

```bash
# Тестировать Claude CLI напрямую
claude -p "test" --output-format json

# Проверить версию
claude --version
# Должна быть 2.0+

# Обновить если нужно
npm update -g @anthropic-ai/claude-code
```

---

## Мониторинг

### Проверка Здоровья

**Скрипт мониторинга:**

```bash
cat > /root/check_claude_wrapper.sh << 'EOF'
#!/bin/bash

# Проверка здоровья Claude Wrapper

echo "=== Claude Wrapper Health Check ==="
echo "Date: $(date)"
echo ""

# 1. Systemd status
echo "1. Systemd Status:"
systemctl is-active claude-wrapper.service
echo ""

# 2. HTTP health
echo "2. HTTP Health:"
curl -s -f http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ HTTP OK"
else
    echo "❌ HTTP FAILED"
fi
echo ""

# 3. Test request
echo "3. Test Request:"
RESPONSE=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Write one word: OK","model":"sonnet","max_tokens":10}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','ERROR'))")

if [ "$RESPONSE" == "OK" ]; then
    echo "✅ Claude API OK"
else
    echo "⚠️ Response: $RESPONSE"
fi
echo ""

# 4. OAuth expiry
echo "4. OAuth Expiry:"
python3 << PYTHON
import json, time
try:
    with open('/root/.claude/.credentials.json') as f:
        data = json.load(f)
    expires = data['claudeAiOauth']['expiresAt'] / 1000
    remaining = (expires - time.time()) / 86400
    print(f"✅ Valid for {remaining:.1f} days")
    if remaining < 7:
        print("⚠️ WARNING: Expiring soon!")
except Exception as e:
    print(f"❌ ERROR: {e}")
PYTHON
echo ""

# 5. Resource usage
echo "5. Resource Usage:"
ps aux | grep claude_wrapper | grep -v grep | awk '{print "CPU: "$3"% MEM: "$4"%"}'
echo ""

echo "=== End Health Check ==="
EOF

chmod +x /root/check_claude_wrapper.sh
```

**Запуск проверки:**

```bash
/root/check_claude_wrapper.sh
```

### Автоматический Мониторинг (Cron)

```bash
# Добавить в cron - проверка каждый час
crontab -e

# Добавить строку:
0 * * * * /root/check_claude_wrapper.sh >> /var/log/claude-wrapper-health.log 2>&1
```

### Логи

**Просмотр в реальном времени:**

```bash
# Wrapper логи
tail -f /var/log/claude-wrapper.log

# Systemd журнал
journalctl -u claude-wrapper.service -f

# Все вместе
tail -f /var/log/claude-wrapper.log /var/log/syslog
```

**Ротация логов:**

```bash
cat > /etc/logrotate.d/claude-wrapper << 'EOF'
/var/log/claude-wrapper.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0640 root root
    postrotate
        systemctl reload claude-wrapper.service > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

## Backup и Восстановление

### Backup

**Что бэкапить:**

1. **OAuth credentials:**
   ```bash
   cp /root/.claude/.credentials.json /root/claude-credentials-backup-$(date +%Y%m%d).json
   ```

2. **Wrapper script:**
   ```bash
   cp /root/claude_wrapper.py /root/claude_wrapper-backup-$(date +%Y%m%d).py
   ```

3. **Systemd service:**
   ```bash
   cp /etc/systemd/system/claude-wrapper.service /root/claude-wrapper-service-backup-$(date +%Y%m%d).service
   ```

**Полный backup скрипт:**

```bash
cat > /root/backup_claude.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/root/claude-backups
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p $BACKUP_DIR

# Backup files
cp /root/.claude/.credentials.json $BACKUP_DIR/credentials-$DATE.json
cp /root/claude_wrapper.py $BACKUP_DIR/wrapper-$DATE.py
cp /etc/systemd/system/claude-wrapper.service $BACKUP_DIR/service-$DATE.service

echo "✅ Backup completed: $BACKUP_DIR/"
ls -lh $BACKUP_DIR/ | tail -3
EOF

chmod +x /root/backup_claude.sh
```

### Восстановление

**Если OAuth потерян:**

```bash
# Восстановить из backup
cp /root/claude-backups/credentials-YYYYMMDD.json /root/.claude/.credentials.json

# Или перелогиниться
claude login
```

**Если wrapper script повреждён:**

```bash
# Восстановить из backup
cp /root/claude-backups/wrapper-YYYYMMDD.py /root/claude_wrapper.py

# Перезапустить
systemctl restart claude-wrapper.service
```

**Полное восстановление:**

```bash
#!/bin/bash
# Скрипт полного восстановления

echo "🔄 Восстановление Claude Wrapper..."

# 1. Остановить service
systemctl stop claude-wrapper.service

# 2. Восстановить файлы
LATEST_CREDENTIALS=$(ls -t /root/claude-backups/credentials-*.json | head -1)
LATEST_WRAPPER=$(ls -t /root/claude-backups/wrapper-*.py | head -1)
LATEST_SERVICE=$(ls -t /root/claude-backups/service-*.service | head -1)

cp $LATEST_CREDENTIALS /root/.claude/.credentials.json
cp $LATEST_WRAPPER /root/claude_wrapper.py
cp $LATEST_SERVICE /etc/systemd/system/claude-wrapper.service

# 3. Перезагрузить и запустить
systemctl daemon-reload
systemctl start claude-wrapper.service
systemctl status claude-wrapper.service

echo "✅ Восстановление завершено"
```

---

## Быстрый Чеклист

### После Установки

- [ ] Claude CLI установлен: `claude --version`
- [ ] OAuth авторизован: `ls ~/.claude/.credentials.json`
- [ ] Headless работает: `claude -p "test"`
- [ ] Python зависимости: `python3 -c "import fastapi"`
- [ ] Wrapper создан: `ls /root/claude_wrapper.py`
- [ ] Systemd service: `systemctl status claude-wrapper`
- [ ] Health endpoint: `curl http://localhost:8000/health`
- [ ] Chat endpoint: работает
- [ ] Внешний доступ: `curl http://178.236.17.55:8000/health`
- [ ] Автозапуск: `systemctl is-enabled claude-wrapper`
- [ ] Backup создан: `ls /root/claude-backups/`

### Регулярные Проверки (еженедельно)

- [ ] Проверить OAuth: `/root/check_claude_wrapper.sh`
- [ ] Проверить логи: `tail /var/log/claude-wrapper.log`
- [ ] Проверить disk space: `df -h`
- [ ] Сделать backup: `/root/backup_claude.sh`

### Перед Истечением OAuth (за неделю)

- [ ] Проверить дату истечения
- [ ] Подготовить browser доступ
- [ ] Перелогиниться: `claude login`
- [ ] Сделать backup нового токена

---

## Контакты и Поддержка

**Сервер:** 178.236.17.55
**Wrapper Port:** 8000
**Systemd Service:** claude-wrapper.service

**Документация:**
- Claude Code: https://docs.claude.com/en/docs/claude-code
- FastAPI: https://fastapi.tiangolo.com/
- Systemd: `man systemd.service`

**Логи:**
- Wrapper: `/var/log/claude-wrapper.log`
- Systemd: `journalctl -u claude-wrapper.service`

**Важные файлы:**
- OAuth: `/root/.claude/.credentials.json`
- Script: `/root/claude_wrapper.py`
- Service: `/etc/systemd/system/claude-wrapper.service`
- Health check: `/root/check_claude_wrapper.sh`
- Backup: `/root/backup_claude.sh`

---

**Версия документации:** 1.0
**Дата:** 2025-10-12
**Тестировано на:** Ubuntu 22.04, Python 3.12, Claude CLI 2.0.5
**Статус:** ✅ PRODUCTION READY
