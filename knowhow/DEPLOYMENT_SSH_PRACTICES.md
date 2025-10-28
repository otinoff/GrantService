# Практики Deployment через SSH

**Дата:** 2025-10-29
**Источник:** Iteration 62 - Research Results Parsing Fix
**Статус:** ✅ Проверено в production

---

## 🔑 SSH Deployment с Ключами

### Проблема

При автоматическом deployment через SSH возникают ошибки:
- `Host key verification failed`
- `Permission denied (publickey,password)`
- Невозможность создать `~/.ssh/known_hosts`

### Решение

**1. Использовать явный путь к SSH-ключу:**
```bash
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251 "команда"
```

**2. Отключить проверку host key (для автоматизации):**
```bash
ssh -i "C:\Users\Андрей\.ssh\id_rsa" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    root@5.35.88.251 "команда"
```

**3. Полный deployment workflow:**
```bash
# 1. Git pull на production
ssh -i "C:\Users\Андрей\.ssh\id_rsa" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    root@5.35.88.251 "cd /var/GrantService && git pull origin master"

# 2. Restart service
ssh -i "C:\Users\Андрей\.ssh\id_rsa" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    root@5.35.88.251 "systemctl restart grantservice-bot"

# 3. Check status
ssh -i "C:\Users\Андрей\.ssh\id_rsa" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    root@5.35.88.251 "systemctl status grantservice-bot --no-pager -l"
```

### Опции SSH

**Критичные для Windows + Git Bash:**
- `-i "путь\к\ключу"` - явный путь к private key
- `-o StrictHostKeyChecking=no` - пропустить проверку host key
- `-o UserKnownHostsFile=/dev/null` - не пытаться сохранить host key

**Для production мониторинга:**
- `--no-pager` - не использовать less/more
- `-l` - показать полные логи systemctl

---

## 🔍 Диагностика SSH Проблем

### Тест 1: Проверка ключа
```bash
ls "C:\Users\Андрей\.ssh"
# Должно быть: id_rsa, id_rsa.pub
```

### Тест 2: Проверка соединения
```bash
ssh -i "C:\Users\Андрей\.ssh\id_rsa" \
    -o ConnectTimeout=10 \
    root@5.35.88.251 "echo 'OK'"
```

### Тест 3: Проверка git на сервере
```bash
ssh root@5.35.88.251 "cd /var/GrantService && git status"
```

---

## 📋 Deployment Checklist

**Перед deployment:**
- [ ] Код протестирован локально
- [ ] Git commit сделан
- [ ] Git push выполнен
- [ ] SSH-ключ доступен

**Deployment:**
- [ ] `git pull origin master` на production
- [ ] Проверить merge conflicts (если есть - `git stash` → `pull` → `stash pop`)
- [ ] `systemctl restart grantservice-bot`
- [ ] `systemctl status` показывает `active (running)`

**После deployment:**
- [ ] Проверить логи: нет критичных ошибок
- [ ] Функциональный тест: базовая операция работает
- [ ] Уведомить команду о deployment

---

## 🚨 Troubleshooting

### Ошибка: "Permission denied"

**Причина:** SSH не видит ключ

**Решение:**
```bash
# Явно указать ключ
ssh -i "C:\Users\Андрей\.ssh\id_rsa" ...
```

### Ошибка: "Host key verification failed"

**Причина:** known_hosts не существует или недоступен

**Решение:**
```bash
# Отключить проверку
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ...
```

### Ошибка: "Could not create directory"

**Причина:** Windows права доступа + кириллица в пути

**Решение:**
```bash
# Использовать /dev/null для known_hosts
ssh -o UserKnownHostsFile=/dev/null ...
```

### Git pull не работает (diverged branches)

**Причина:** Локальные изменения на production сервере

**Решение:**
```bash
ssh root@5.35.88.251 "cd /var/GrantService && git stash && git pull origin master"
```

---

## 🎯 Best Practices

### 1. Всегда используй timeout
```bash
ssh -o ConnectTimeout=10 ...
```

### 2. Проверяй статус после restart
```bash
ssh root@5.35.88.251 "systemctl restart service && sleep 2 && systemctl status service"
```

### 3. Логи в одну строку для clarity
```bash
systemctl status service --no-pager -l
```

### 4. Используй explicit key path в Windows
```bash
# ❌ НЕ РАБОТАЕТ в Git Bash Windows:
ssh root@server "..."

# ✅ РАБОТАЕТ:
ssh -i "C:\Users\Username\.ssh\id_rsa" root@server "..."
```

### 5. Stash перед pull если есть изменения
```bash
# Проверить статус
git status

# Если есть изменения - сохранить
git stash

# Pull
git pull origin master

# Вернуть изменения (если нужно)
git stash pop
```

---

## 📦 Production Server Info

**Server:** `root@5.35.88.251`
**Project Path:** `/var/GrantService`
**Service Name:** `grantservice-bot.service`
**Python:** `/var/GrantService/venv/bin/python`
**Logs:** `journalctl -u grantservice-bot -n 50 --no-pager`

---

## 🧪 Пример из Iteration 62

**Задача:** Deploy фикса исследования на production

**Команды выполненные:**
```bash
# 1. Local commit & push
git add shared/telegram_utils/file_generators.py iterations/Iteration_62_Fix_Research_Results_Parsing/
git commit -m "fix(research): Extract answer from result.summary (Iteration 62)"
git push origin master

# 2. Production pull (с stash из-за локальных изменений)
ssh -i "C:\Users\Андрей\.ssh\id_rsa" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    root@5.35.88.251 "cd /var/GrantService && git stash && git pull origin master"

# 3. Restart bot
ssh -i "C:\Users\Андрей\.ssh\id_rsa" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    root@5.35.88.251 "systemctl restart grantservice-bot && sleep 2 && systemctl status grantservice-bot --no-pager -l"
```

**Результат:**
```
● grantservice-bot.service - GrantService Telegram Bot
     Active: active (running) since Tue 2025-10-28 18:24:13 UTC
   Main PID: 503113
     Memory: 106.9M
```

**Deployment time:** ~45 seconds (pull + restart)

---

## 🔗 Related Knowhow

- `knowhow/DATA_STRUCTURE_DEBUGGING.md` - Debugging nested dicts
- `knowhow/ITERATION_WORKFLOW.md` - Complete iteration workflow
- `.env.example` - SSH key configuration

---

**Автор:** Claude Code
**Дата:** 2025-10-29
**Iteration:** 62
**Status:** ✅ Production-tested
