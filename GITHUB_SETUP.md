# 📋 Настройка GitHub для автоматического деплоя

## 1. Секреты для GitHub Actions

Перейдите в настройки репозитория:
https://github.com/otinoff/GrantService/settings/secrets/actions

Добавьте следующие секреты:

### Обязательные секреты:
- `VPS_HOST` - IP адрес вашего сервера (например: 5.35.88.251)
- `VPS_USER` - имя пользователя на сервере (обычно: root)
- `VPS_PORT` - SSH порт сервера (обычно: 22)
- `VPS_SSH_KEY` - приватный SSH ключ для доступа к серверу

### Как получить SSH ключ:
1. На локальной машине сгенерируйте SSH ключ:
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/grantservice_deploy
   ```

2. Скопируйте публичный ключ на сервер:
   ```bash
   ssh-copy-id -i ~/.ssh/grantservice_deploy.pub root@YOUR_SERVER_IP
   ```

3. Скопируйте содержимое приватного ключа:
   ```bash
   cat ~/.ssh/grantservice_deploy
   ```

4. Добавьте это содержимое в секрет `VPS_SSH_KEY`

---

## 2. Структура на сервере

Убедитесь, что на сервере есть:

### Директория проекта:
```
/var/GrantService/
```

### Systemd сервисы:
1. **grantservice-bot.service** - для Telegram бота
2. **grantservice-admin.service** - для Streamlit админки

### Пример systemd сервиса для бота:
```ini
[Unit]
Description=GrantService Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/GrantService/telegram-bot
ExecStart=/usr/bin/python3 /var/GrantService/telegram-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Пример systemd сервиса для админки:
```ini
[Unit]
Description=GrantService Admin Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/GrantService/web-admin
ExecStart=/usr/local/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 3. Автоматический деплой

После настройки, каждый пуш в ветки `main` или `Dev` будет автоматически:
1. Скачивать последние изменения на сервер
2. Обновлять зависимости
3. Перезапускать сервисы
4. Проверять статус

---

## 4. Ручной деплой

Вы также можете запустить деплой вручную:
1. Перейдите во вкладку Actions: https://github.com/otinoff/GrantService/actions
2. Выберите workflow "Deploy GrantService to VPS"
3. Нажмите "Run workflow"

---

*Документ создан: 18.09.2025*