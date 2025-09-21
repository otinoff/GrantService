# 🚀 Руководство по запуску админки GrantService

## ✅ Выполненные работы

### 1. Кроссплатформенность
- ✅ Создан модуль `config/paths.py` для автоматического определения путей на Windows/Linux
- ✅ Все файлы в `web-admin/pages/` обновлены для работы на обеих ОС
- ✅ Удалены hardcoded пути `/var/GrantService`
- ✅ Добавлена автоматическая настройка путей импорта

### 2. Исправленные файлы
- 🏠_Главная.py
- ❓_Вопросы_интервью.py 
- ✍️_Writer_Agent.py
- 📄_Грантовые_заявки.py
- 📊_Общая_аналитика.py
- 🔍_Researcher_Agent.py
- 📋_Анкеты_пользователей.py
- И все остальные файлы через скрипт `fix_all_pages.py`

### 3. Созданные вспомогательные файлы
- `run_admin.py` - главный файл запуска с правильной настройкой путей
- `start_admin.bat` - удобный батник для Windows
- `test_imports.py` - скрипт диагностики импортов
- `fix_all_pages.py` - автоматическое исправление всех страниц

## 📝 Как запускать админку

### Вариант 1: Через батник (рекомендуется для Windows)
```bash
cd C:\SnowWhiteAI\GrantService
start_admin.bat
```

### Вариант 2: Через Python напрямую
```bash
cd C:\SnowWhiteAI\GrantService
python run_admin.py
```

### Вариант 3: Стандартный запуск Streamlit (может не работать)
```bash
cd C:\SnowWhiteAI\GrantService
streamlit run web-admin/pages/🏠_Главная.py
```

## ⚠️ Важные замечания

### Проблема с импортами
Streamlit запускает страницы в особом контексте, что может нарушать импорты. Решение:
1. Используйте `run_admin.py` - он правильно настраивает все пути
2. Если возникают ошибки импорта, запустите `test_imports.py` для диагностики

### Структура импортов
- Все страницы теперь импортируют из `utils.auth`, а не из `web_admin.utils.auth`
- Пути добавляются динамически в зависимости от ОС
- Файл `web-admin/utils/__init__.py` содержит все необходимые экспорты

### База данных
- База данных автоматически инициализируется при запуске
- Путь к БД определяется через `config/paths.py`
- На Windows: `C:\SnowWhiteAI\GrantService\data\grant_service.db`
- На Linux: `/var/GrantService/data/grant_service.db`

## 🔧 Если что-то не работает

### 1. Проверьте установку зависимостей:
```bash
pip install streamlit pandas
```

### 2. Запустите диагностику:
```bash
python test_imports.py
```

### 3. Проверьте наличие всех файлов:
- `/config/paths.py` - должен существовать
- `/web-admin/utils/auth.py` - должен существовать  
- `/web-admin/utils/__init__.py` - должен существовать
- `/data/database.py` - должен существовать

### 4. При ошибках импорта:
- Убедитесь, что используете `run_admin.py` для запуска
- Проверьте, что Python может найти все модули через `test_imports.py`

## 📱 Доступ к админке

После успешного запуска:
1. Откройте браузер
2. Перейдите по адресу: http://localhost:8501
3. Войдите используя токен авторизации из Telegram бота

## 🛠️ Дополнительные скрипты

### fix_all_pages.py
Автоматически исправляет все файлы в pages/ для кроссплатформенности:
```bash
python fix_all_pages.py
```

### test_imports.py
Проверяет корректность всех импортов:
```bash
python test_imports.py
```

## 📄 Изменения в коде

Основные изменения во всех файлах pages/*.py:

**Было:**
```python
sys.path.append('/var/GrantService')
from web_admin.utils.auth import is_user_authorized
spec = importlib.util.spec_from_file_location(
    "login_page", 
    "/var/GrantService/web-admin/pages/🔐_Вход.py"
)
```

**Стало:**
```python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)
sys.path.insert(0, parent_dir)

from utils.auth import is_user_authorized
spec = importlib.util.spec_from_file_location(
    "login_page", 
    os.path.join(current_dir, "🔐_Вход.py")
)
```

---
**Админка теперь полностью кроссплатформенная и готова к запуску на Windows и Linux!**