# GrantService Scripts

Коллекция utility скриптов для deployment, testing и database management.

## 📂 Скрипты

### 🔄 Database Sync

## ⚡ Автоматическая синхронизация (NEW!)

**С версии 2025-10-03**: База данных автоматически синхронизируется при каждом запуске `launcher.py` на Windows!

```bash
# Просто запусти launcher и БД автоматически обновится:
python launcher.py
# или
admin.bat
```

**Вывод**:
```
============================================================
GRANTSERVICE ADMIN LAUNCHER
============================================================
Syncing database from production...
✓ Database synced successfully (0.5 MB)

Setting up environment...
```

**Поведение**:
- ✅ Автоматически при каждом запуске на Windows
- ⏱️ Добавляет ~3 секунды к запуску
- 🔄 Fallback к локальной копии если нет интернета
- 🔒 Только на Windows (не на production сервере)

---

## Ручная синхронизация

## Использование

### Windows:
```bash
# С автоматическим backup локальной БД
scripts\sync_database.bat

# Без backup (перезаписать локальную БД)
scripts\sync_database.bat --no-backup
```

### Linux/Mac:
```bash
# С автоматическим backup локальной БД
./scripts/sync_database.sh

# Без backup (перезаписать локальную БД)
./scripts/sync_database.sh --no-backup
```

### Прямая команда (универсальная):
```bash
scp root@5.35.88.251:/var/GrantService/data/grantservice.db data/grantservice.db
```

## Что делает скрипт

1. **Backup текущей БД** - сохраняет локальную БД в `data/backups/` (если не указан `--no-backup`)
2. **Download с production** - копирует актуальную БД с сервера через SCP
3. **Показывает статистику** - размер файла, количество записей (если доступен sqlite3)

## Структура backup

Backup файлы сохраняются с timestamp:
```
data/backups/
├── grantservice_backup_20251003_145530.db
├── grantservice_backup_20251003_163022.db
└── grantservice_backup_20251003_215100.db
```

## Очистка старых backup

### Windows:
```bash
del data\backups\grantservice_backup_*
```

### Linux/Mac:
```bash
rm data/backups/grantservice_backup_*
```

## Требования

- **SSH доступ** к серверу `root@5.35.88.251` (ключи должны быть настроены)
- **scp** установлен в системе

## Безопасность

⚠️ **ВАЖНО**: Скачанная БД содержит персональные данные пользователей (telegram_id, имена, сообщения). Не коммить в Git, не передавать третьим лицам!

Файл `data/grantservice.db` включён в `.gitignore`.

## Troubleshooting

### SSH connection failed
```bash
# Проверить доступность сервера
ping 5.35.88.251

# Проверить SSH подключение
ssh root@5.35.88.251 "echo Connection OK"
```

### Permission denied
Убедись что SSH ключи настроены:
```bash
ssh-copy-id root@5.35.88.251
```

## Пример вывода

```
=========================================
Database Sync - Production to Local
=========================================

Creating backup of local database...
✓ Backup created: data/backups/grantservice_backup_20251003_215100.db
  Size: 464 KB

Downloading database from production server...
Server: root@5.35.88.251
Remote: /var/GrantService/data/grantservice.db

✓ Database downloaded successfully!
  Size: 464 KB

Database Statistics:
  Users: 4
  Sessions: 16

=========================================
Sync completed successfully!
=========================================

Backups stored in: data/backups
Total backups: 3
```

---

## 🌐 Headless Browser Testing

### `headless_check.py`

Автоматическая проверка всех страниц admin panel через headless browser (Playwright).

**Использование**:
```bash
# Установка Playwright (один раз)
pip install playwright
playwright install chromium

# Локальная проверка
python scripts/headless_check.py

# Проверка на production
scp scripts/headless_check.py root@5.35.88.251:/tmp/
ssh root@5.35.88.251 "python3 /tmp/headless_check.py"
```

**Что проверяется**:
- ✅ HTTP 200 на всех страницах
- ✅ Наличие ключевого текста
- ✅ Отсутствие ImportError/ModuleNotFoundError
- ✅ Страница загружается за <15 секунд

**Пример вывода**:
```
============================================================
🌐 Headless Browser Tests - GrantService Admin
============================================================

Testing Dashboard... ✅ OK
Testing Grants... ✅ OK
Testing Users... ✅ OK
Testing Analytics... ✅ OK
Testing Agents... ✅ OK
Testing Settings... ✅ OK

============================================================
Results: 6/6 passed, 0 failed
✅ All pages working correctly!
============================================================
```

### `quick_pages_check.sh`

Быстрая проверка страниц через curl (без Playwright).

**Использование**:
```bash
# Локально
bash scripts/quick_pages_check.sh

# На production
ssh root@5.35.88.251 "bash /var/GrantService/scripts/quick_pages_check.sh"
```

**Пример вывода**:
```
=========================================
Quick Pages Check - GrantService Admin
=========================================

✅ [200] Dashboard
✅ [200] Grants
✅ [200] Users
✅ [200] Analytics
✅ [200] Agents
✅ [200] Settings

=========================================
Results: 6/6 passed, 0 failed
✅ All pages responding!
=========================================
```

---

## 🚀 Deployment Scripts

### `deploy_pythonpath_fix.sh`

Деплой PYTHONPATH fix на production сервер - добавляет переменные окружения в systemd service.

**Использование**:
```bash
bash scripts/deploy_pythonpath_fix.sh
```

**Что делает**:
1. Бэкапит текущий service файл
2. Добавляет PYTHONPATH в systemd
3. Перезагружает daemon
4. Рестартит grantservice-admin
5. Проверяет статус и логи

---

**Последнее обновление**: 2025-10-03
**Версия**: 2.0.0
