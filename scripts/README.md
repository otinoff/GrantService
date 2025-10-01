# GrantService Scripts

Коллекция утилитных скриптов для управления и обслуживания GrantService.

## 🚀 Deployment Scripts

### setup_systemd_services.sh
Создает systemd сервисы для Telegram бота и Streamlit админки.
```bash
sudo bash scripts/setup_systemd_services.sh
```

### update_admin_service.sh
Обновляет systemd сервис grantservice-admin с правильным путем к Streamlit приложению.
```bash
sudo bash scripts/update_admin_service.sh
```

**Используйте этот скрипт если:**
- Admin panel не запускается после деплоя
- Изменился entry point для Streamlit (app_main.py)
- Нужно быстро пересоздать сервис

## 🔧 Admin Panel Scripts

### run_admin.py
Запуск админ-панели локально (кросс-платформенный).
```bash
python scripts/run_admin.py
```

### run_admin.bat (Windows)
```cmd
scripts\run_admin.bat
```

### run_streamlit_admin.bat (Windows)
```cmd
scripts\run_streamlit_admin.bat
```

## 🤖 Bot Scripts

### restart_bot.bat / restart_bot.ps1 (Windows)
Перезапуск Telegram бота на Windows.
```cmd
scripts\restart_bot.bat
```
```powershell
scripts\restart_bot.ps1
```

### start_bot_windows.bat
Запуск бота в новом окне консоли (Windows).
```cmd
scripts\start_bot_windows.bat
```

### restart_server_bot.sh / restart_server_bot.py (Linux)
Перезапуск бота на сервере.
```bash
bash scripts/restart_server_bot.sh
# или
python3 scripts/restart_server_bot.py
```

## 💾 Database Scripts

### check_remote_db.py
Проверка подключения к удаленной БД PostgreSQL.
```bash
python scripts/check_remote_db.py
```

### check_remote_db_windows.py
Версия для Windows с дополнительными проверками.
```cmd
python scripts\check_remote_db_windows.py
```

### check_server_db.py
Проверка БД непосредственно на сервере.
```bash
python3 scripts/check_server_db.py
```

### check_users.py
Вывод списка пользователей из БД.
```bash
python scripts/check_users.py
```

## 🔄 Migration Scripts

### migrate_prompts_to_db.py
Миграция промптов AI-агентов в БД.
```bash
python scripts/migrate_prompts_to_db.py
```

### migrate_existing_anketas.py
Миграция существующих анкет после изменения схемы.
```bash
python scripts/migrate_existing_anketas.py
```

## 🧪 Testing Scripts

### run_test.bat
Запуск тестов (Windows).
```cmd
scripts\run_test.bat
```

### run_streamlit_test.bat / run_streamlit_test.sh
Запуск тестового Streamlit приложения.
```bash
# Windows
scripts\run_streamlit_test.bat

# Linux
bash scripts/run_streamlit_test.sh
```

## 🔧 Maintenance Scripts

### fix_all_imports.py
Исправление импортов во всех Python файлах.
```bash
python scripts/fix_all_imports.py
```

### fix_all_pages.py
Исправление страниц админ-панели.
```bash
python scripts/fix_all_pages.py
```

### fix_all_web_admin.ps1
Массовое исправление импортов в web-admin (PowerShell).
```powershell
scripts\fix_all_web_admin.ps1
```

### refactor_pages.py
Рефакторинг страниц с применением паттернов.
```bash
python scripts/refactor_pages.py
```

### set_admin.py
Установка прав администратора для пользователя.
```bash
python scripts/set_admin.py <telegram_id>
```

## 🐛 Debug Scripts

### debug_imports.py
Отладка проблем с импортами модулей.
```bash
python scripts/debug_imports.py
```

### batch_fix_imports.py
Пакетное исправление импортов.
```bash
python scripts/batch_fix_imports.py
```

## 📦 Quick Reference

### На продакшн сервере (Linux)
```bash
# Обновить systemd сервисы
sudo bash scripts/setup_systemd_services.sh

# Перезапустить бота
bash scripts/restart_server_bot.sh

# Проверить БД
python3 scripts/check_server_db.py

# Дать права админа
python3 scripts/set_admin.py 123456789
```

### На локальной машине (Windows)
```cmd
# Запустить админку
scripts\run_admin.bat

# Запустить бота
scripts\start_bot_windows.bat

# Проверить БД
python scripts\check_remote_db_windows.py

# Запустить тесты
scripts\run_test.bat
```

## 🚨 Troubleshooting

### Streamlit не запускается на сервере
```bash
# 1. Обновить сервис с правильным путем
sudo bash scripts/update_admin_service.sh

# 2. Проверить логи
journalctl -u grantservice-admin -n 50

# 3. Проверить зависимости
cd /var/GrantService/web-admin
pip install -r requirements.txt
```

### Бот не отвечает
```bash
# Проверить статус
sudo systemctl status grantservice-bot

# Перезапустить
sudo systemctl restart grantservice-bot

# Посмотреть логи
journalctl -u grantservice-bot -f
```

### Проблемы с БД
```bash
# Проверить подключение
python3 scripts/check_server_db.py

# Проверить пользователей
python3 scripts/check_users.py

# Запустить миграции
python3 scripts/migrate_prompts_to_db.py
```

---

**Примечание:** Все скрипты с расширением `.sh` должны иметь права на выполнение:
```bash
chmod +x scripts/*.sh
```
