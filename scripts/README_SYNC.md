# Database Sync Scripts

Скрипты для синхронизации production базы данных на локальную машину для разработки.

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

**Последнее обновление**: 2025-10-03
**Версия**: 1.0.0
