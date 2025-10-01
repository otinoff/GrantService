# Анализ инцидента с токеном бота

**Дата инцидента**: 2025-10-01
**Время**: 15:48-16:03 UTC
**Статус**: Решено ✅

## 🔍 Что произошло

### Timeline событий

1. **15:48 UTC** - GitHub Actions запустил deployment после commit `7b868de` (рефакторинг)
2. **15:49 UTC** - На сервере выполнен `git reset --hard origin/master`
3. **15:49 UTC** - Streamlit перезапустился с новым путем (`web-admin/app_main.py`) - **ОК** ✅
4. **15:49+ UTC** - Bot начал перезапускаться каждые 10 секунд с ошибкой "TELEGRAM_BOT_TOKEN не установлен" ❌
5. **16:03 UTC** - Токен восстановлен из бэкапа, bot запущен - **ОК** ✅

## 📂 Структура файлов конфигурации

### До инцидента
```
/var/GrantService/config/
├── .env              # Реальный токен (НЕ в Git, последнее изменение 18.07.2025)
├── config.env        # Placeholder токен (в Git, изменен 02.08.2025)
└── .env.example      # Шаблон (в Git)
```

### После git reset --hard
```
/var/GrantService/config/
├── .env              # УДАЛЕН (был в .gitignore)
├── config.env        # Перезаписан из Git (placeholder)
└── .env.example      # Обновлен из Git
```

### После восстановления
```
/var/GrantService/config/
├── .env              # ✅ Восстановлен из бэкапа (1 строка, 66 байт)
├── config.env        # Placeholder (не используется ботом)
└── .env.example      # Шаблон
```

## 🎯 Корневая причина

### Проблема #1: Защита data/ но не config/.env
GitHub Actions workflow защищал только директорию `data/`:

```bash
# Защита директории data/ от git clean
if [ -d "data" ]; then
    mv data /tmp/grantservice_data_safe
fi

# ... git reset --hard ...

# Восстановление data/
mv /tmp/grantservice_data_safe data
```

**НО** `config/.env` **НЕ** был защищен!

### Проблема #2: .gitignore скрывает файл
`.env` находится в `.gitignore`:
```gitignore
# Environment variables
.env
.env.local
.env.production
```

При `git reset --hard origin/master` Git удалил **untracked** файл `config/.env`.

### Проблема #3: Бот ищет config/.env, а не config/config.env
```python
# telegram-bot/main.py:50
@property
def env_path(self) -> str:
    return os.path.join(self.base_path, 'config', '.env')
```

Bot читает **только** `config/.env`, игнорируя `config/config.env`.

## 🛠️ Решение

### Текущее состояние (работает)
- ✅ `config/.env` восстановлен из бэкапа (реальный токен)
- ✅ Bot запущен и работает
- ✅ Streamlit запущен и работает

### Где сейчас токен
```
/var/GrantService/config/.env (66 байт)
TELEGRAM_BOT_TOKEN=7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo
```

### Что НЕ содержит токен
- ❌ `config/config.env` - содержит placeholder
- ❌ Git repository - `.env` в `.gitignore`
- ❌ GitHub - файл никогда не был в репозитории

## 🚨 План предотвращения

### 1. Защитить config/.env в deployment workflow

**Добавить в `.github/workflows/deploy-grantservice.yml`**:

```yaml
# ПЕРЕД git операциями
echo "Protecting config/.env..."
if [ -f "config/.env" ]; then
    cp config/.env /tmp/grantservice_env_safe
    echo "✓ Config backed up"
fi

# ... git reset --hard ...

# ПОСЛЕ git операций
echo "Restoring config/.env..."
if [ -f "/tmp/grantservice_env_safe" ]; then
    cp /tmp/grantservice_env_safe config/.env
    chmod 600 config/.env
    echo "✓ Config restored"
fi
```

### 2. Использовать systemd EnvironmentFile

**Уже реализовано в `scripts/setup_systemd_services.sh`**:
```ini
[Service]
EnvironmentFile=-/var/GrantService/config/.env
```

Флаг `-` означает "не падать если файл отсутствует".

### 3. Создать backup скрипт

**Скрипт `scripts/backup_secrets.sh`**:
```bash
#!/bin/bash
tar -czf /root/grantservice-secrets-$(date +%Y%m%d).tar.gz \
    /var/GrantService/config/.env \
    /var/GrantService/data/*.db
```

### 4. Добавить проверку в deployment

После deployment проверять наличие токена:
```bash
if ! grep -q "TELEGRAM_BOT_TOKEN=7685" config/.env 2>/dev/null; then
    echo "❌ ERROR: Token missing! Restoring from backup..."
    # Restore logic
fi
```

## 📊 Статистика инцидента

- **Downtime бота**: ~14 минут (15:49 - 16:03)
- **Downtime админки**: 0 минут (работала всё время)
- **Количество рестартов бота**: 66 попыток
- **Причина**: Человеческий фактор (недостаточная защита в CI/CD)
- **Потеря данных**: Нет (БД защищена)

## ✅ Извлеченные уроки

1. **Всегда защищать критичные config файлы** при `git reset --hard`
2. **Использовать systemd EnvironmentFile** вместо хардкода в сервисах
3. **Делать автоматические бэкапы** `.env` файлов
4. **Тестировать CI/CD** на staging перед production
5. **Логировать все операции** с конфигурационными файлами

## 🎯 Action Items

- [ ] Обновить GitHub Actions workflow для защиты `config/.env`
- [ ] Создать cron job для ежедневного бэкапа secrets
- [ ] Добавить мониторинг отсутствия токена
- [ ] Документировать процедуру восстановления
- [ ] Создать staging окружение для тестов

---

**Создано**: 2025-10-01
**Автор**: Claude Code
**Версия**: 1.0
