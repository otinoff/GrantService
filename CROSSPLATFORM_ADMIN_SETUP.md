# 🚀 Кроссплатформенная админка GrantService

## ✅ Выполненные изменения

### 1. Создан модуль конфигурации путей
- **Файл:** `config/paths.py`
- **Функционал:**
  - Автоматическое определение ОС (Windows/Linux/Mac)
  - Динамическая установка путей в зависимости от ОС
  - Централизованное управление всеми путями проекта

### 2. Обновлены файлы админки
Все файлы теперь используют кроссплатформенные пути:
- `web-admin/pages/🏠_Главная.py`
- `web-admin/utils/auth.py`
- `web-admin/utils/database.py`
- `web-admin/auth_pages.py`
- `web-admin/main_admin.py`

### 3. Изменения в коде
Заменены хардкод пути:
- **Было:** `/var/GrantService` (только Linux)
- **Стало:** автоматическое определение через `config.paths`

## 📋 Как запустить админку

### Windows (ваша система)

#### Вариант 1: Новый батник (рекомендуется)
```batch
cd C:\SnowWhiteAI\GrantService
run_admin.bat
```

#### Вариант 2: Тестовый батник
```batch
cd C:\SnowWhiteAI\GrantService
run_streamlit_test.bat
```

#### Вариант 3: Ручной запуск
```batch
cd C:\SnowWhiteAI\GrantService\web-admin
streamlit run main_admin.py
```

### Linux/Ubuntu

```bash
cd /var/GrantService/web-admin
streamlit run main_admin.py
```

## 🔧 Установка зависимостей

### Первый запуск - установите пакеты:
```batch
pip install -r C:\SnowWhiteAI\GrantService\requirements_streamlit.txt
```

### Необходимые пакеты:
- streamlit>=1.28.0
- qrcode>=7.4.2
- Pillow>=10.0.0
- requests>=2.31.0
- python-dateutil>=2.8.2

## 🎯 Преимущества кроссплатформенного подхода

1. **Один код для всех ОС** - работает на Windows и Linux без изменений
2. **Автоматическое определение ОС** - не нужна ручная настройка
3. **Централизованная конфигурация** - все пути в одном месте
4. **Легкий деплой** - код работает на сервере без правок

## 🛠️ Структура путей

### Windows
```
C:\SnowWhiteAI\GrantService\
├── config\
│   └── paths.py          # Конфигурация путей
├── web-admin\
│   ├── main_admin.py     # Главный файл админки
│   ├── pages\
│   │   └── 🏠_Главная.py # Страницы админки
│   └── utils\
│       ├── auth.py       # Авторизация
│       └── database.py   # Работа с БД
└── data\                 # База данных
```

### Linux
```
/var/GrantService/
├── config/
│   └── paths.py
├── web-admin/
│   ├── main_admin.py
│   ├── pages/
│   └── utils/
└── data/
```

## ⚠️ Возможные проблемы и решения

### Проблема 1: Ошибка импорта модуля config
**Решение:** Убедитесь, что файл `config/paths.py` создан

### Проблема 2: Не находит базу данных
**Решение:** Проверьте наличие файла в `data/grant_service.db`

### Проблема 3: Ошибка авторизации
**Решение:** Проверьте настройки Telegram бота и токены

## 📝 Отладка

При запуске вы увидите информацию об ОС и путях:
```
🖥️ Обнаружена ОС: Windows
📁 Базовый путь проекта: C:\SnowWhiteAI\GrantService
📁 Путь к web-admin: C:\SnowWhiteAI\GrantService\web-admin
📁 Путь к данным: C:\SnowWhiteAI\GrantService\data
```

## ✨ Результат

Теперь админка работает:
- ✅ На Windows (вашей системе разработки)
- ✅ На Linux/Ubuntu (продакшн сервере)
- ✅ Без изменения кода при деплое
- ✅ С автоматическим определением путей

## 🚀 Быстрый старт

1. Откройте командную строку
2. Перейдите в папку проекта:
   ```batch
   cd C:\SnowWhiteAI\GrantService
   ```
3. Запустите админку:
   ```batch
   run_admin.bat
   ```
4. Откройте браузер: http://localhost:8501

---

**Автор:** Система GrantService  
**Версия:** 2.0 (кроссплатформенная)  
**Дата:** 2025