# 🏛️ Архитектура системы авторизации GrantService

## 📊 Общая схема архитектуры

```
┌─────────────────────────────────────────────────────────────┐
│                      ПОЛЬЗОВАТЕЛЬ                            │
│                                                              │
│  1. Отправляет /get_access в Telegram                       │
│  2. Получает токен и ссылку                                 │
│  3. Переходит по ссылке в браузере                         │
└────────────┬───────────────────────┬────────────────────────┘
             │                       │
             ▼                       ▼
┌─────────────────────────┐   ┌──────────────────────────────┐
│    TELEGRAM BOT         │   │    STREAMLIT ADMIN           │
├─────────────────────────┤   ├──────────────────────────────┤
│ Команды:                │   │ Авторизация:                 │
│ • /get_access           │   │ • Проверка токена из URL     │
│ • /revoke_access        │   │ • Ручной ввод токена         │
│ • /my_access            │   │ • Создание сессии            │
│                         │   │                              │
│ Генерация токена:       │   │ Интерфейс:                   │
│ • token_timestamp_hex   │   │ • Dashboard                  │
│ • Срок: 24 часа        │   │ • Управление анкетами        │
│ • Привязка к ID         │   │ • Аналитика                  │
└───────────┬─────────────┘   └──────────┬───────────────────┘
            │                             │
            ▼                             ▼
┌──────────────────────────────────────────────────────────────┐
│                     БАЗА ДАННЫХ (SQLite)                      │
├──────────────────────────────────────────────────────────────┤
│ Таблица users:              │ Таблица auth_logs:            │
│ • telegram_id               │ • user_id                     │
│ • login_token               │ • action                      │
│ • role (admin/editor/user)  │ • timestamp                   │
│ • permissions               │ • success                     │
└──────────────────────────────────────────────────────────────┘
```

## 🔐 Компоненты системы

### 1. Telegram Bot (`telegram-bot/main.py`)

#### Команды управления токенами:
- **`/get_access`** - Генерация токена доступа к админ-панели
- **`/revoke_access`** - Отзыв активного токена
- **`/my_access`** - Информация о текущем доступе и роли
- **`/login`** - Псевдоним для /get_access (совместимость)
- **`/admin`** - Доступ для администраторов

#### Формат токена:
```python
token = f"token_{timestamp}_{random_hex}"
# Пример: token_1734567890_abc123def456789...
```

### 2. База данных (`data/database/`)

#### Структура таблиц:

**users:**
```sql
telegram_id BIGINT UNIQUE NOT NULL
username VARCHAR(100)
first_name VARCHAR(100) 
last_name VARCHAR(100)
login_token VARCHAR(255)     -- Токен для авторизации
role VARCHAR(20)             -- admin/editor/viewer/user
permissions TEXT             -- JSON массив разрешений
```

**auth_logs:**
```sql
user_id INTEGER
action VARCHAR(50)           -- generate_token/login_success/logout
ip_address VARCHAR(45)
user_agent TEXT
success BOOLEAN
error_message TEXT
created_at TIMESTAMP
```

**page_permissions:**
```sql
page_name VARCHAR(100)       -- Название страницы
required_role VARCHAR(20)    -- Минимальная роль
required_permissions TEXT    -- Необходимые разрешения
description TEXT
is_active BOOLEAN
```

### 3. Streamlit Admin Panel (`web-admin/`)

#### Файловая структура:
```
web-admin/
├── __init__.py
├── auth_pages.py        # Страницы авторизации
└── streamlit_app.py     # Главное приложение
```

#### Функции авторизации:
- Автоматическая через URL параметр: `?token=XXX`
- Ручной ввод токена через форму
- Проверка срока действия (24 часа)
- Сохранение сессии в st.session_state

## 🔄 Процесс авторизации

### Шаг 1: Запрос доступа
```
Пользователь → Telegram Bot
Команда: /get_access
```

### Шаг 2: Проверка прав
```python
def is_user_authorized(user_id):
    # Проверка в списке разрешенных пользователей
    return user_id in ALLOWED_USERS
```

### Шаг 3: Генерация токена
```python
def generate_login_token():
    timestamp = int(time.time())
    random_hex = secrets.token_hex(16)
    return f"token_{timestamp}_{random_hex}"
```

### Шаг 4: Сохранение в БД
```sql
UPDATE users 
SET login_token = ? 
WHERE telegram_id = ?
```

### Шаг 5: Отправка ссылки
```
Бот → Пользователь
Ссылка: http://localhost:8501?token=XXX
Срок действия: 24 часа
```

### Шаг 6: Вход в админку
```python
def check_token_from_url():
    token = st.query_params.get('token')
    user_data = db.validate_login_token(token)
    if user_data:
        st.session_state['authenticated'] = True
```

## 🛡️ Безопасность

### Защита токенов:
1. **Уникальность** - криптографически стойкая генерация
2. **Временность** - автоматическое истечение через 24 часа
3. **Привязка** - каждый токен привязан к telegram_id
4. **Отзыв** - возможность мгновенного отзыва

### Валидация токена:
```python
def validate_login_token(token):
    # 1. Проверка формата
    parts = token.split('_')
    if len(parts) < 3:
        return None
    
    # 2. Проверка времени
    token_timestamp = int(parts[1])
    current_time = int(time.time())
    if current_time - token_timestamp > 86400:  # 24 часа
        return None
    
    # 3. Поиск в БД
    user = find_user_by_token(token)
    return user
```

### Логирование:
- Все попытки входа записываются
- Успешные и неудачные авторизации
- IP-адреса и user agents
- Действия пользователей в системе

## 👥 Ролевая модель

### Иерархия ролей:
```
admin    (3) - Полный доступ ко всем функциям
  ↑
editor   (2) - Редактирование контента
  ↑
viewer   (1) - Только просмотр
  ↑
user     (0) - Базовый доступ
```

### Проверка прав:
```python
def can_access_page(user_id, page_name):
    user_role = get_user_role(user_id)
    page_requirements = get_page_requirements(page_name)
    
    # Админы имеют доступ везде
    if user_role == 'admin':
        return True
    
    # Проверка иерархии ролей
    return user_role_level >= required_role_level
```

## ⚙️ Настройка доступа

### 1. Конфигурация разрешенных пользователей:
```python
# config/constants.py
ALLOWED_USERS = [
    123456789,  # @user1
    987654321,  # @user2
]

ADMIN_USERS = [
    123456789,  # @admin1
]
```

### 2. Переменные окружения:
```bash
# .env
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_BASE_URL=http://localhost:8501
```

### 3. Инициализация ролей:
```python
# scripts/init_auth_roles.py
auth_manager.set_user_role(telegram_id, 'admin')
auth_manager.set_user_permissions(telegram_id, [
    'view_analytics',
    'edit_questions',
    'manage_users'
])
```

## 📁 Структура проекта

```
C:\SnowWhiteAI\GrantService\
│
├── telegram-bot/
│   ├── main.py                 # Основной файл бота
│   └── handlers/
│       └── auth_middleware.py  # Middleware авторизации
│
├── web-admin/
│   ├── __init__.py
│   ├── auth_pages.py          # Страницы авторизации
│   └── streamlit_app.py       # Главное приложение
│
├── data/
│   └── database/
│       ├── __init__.py
│       ├── models.py           # Модели БД
│       ├── auth.py             # Логика авторизации
│       └── grantservice.db     # SQLite база
│
├── config/
│   ├── constants.py            # Константы и списки пользователей
│   └── .env                    # Переменные окружения
│
└── scripts/
    └── init_auth_roles.py     # Скрипт инициализации ролей
```

## 🚀 Запуск системы

### 1. Запуск Telegram бота:
```bash
cd C:\SnowWhiteAI\GrantService
python telegram-bot/main.py
```

### 2. Запуск Streamlit админки:
```bash
cd C:\SnowWhiteAI\GrantService
streamlit run streamlit_app.py
```

### 3. Получение доступа:
1. Написать боту: `/get_access`
2. Получить ссылку с токеном
3. Перейти по ссылке
4. Начать работу в админке

## 📊 Преимущества архитектуры

### ✅ Простота:
- Не нужно запоминать пароли
- Вход в один клик
- Интеграция с Telegram

### ✅ Безопасность:
- Токены с ограниченным сроком
- Привязка к Telegram ID
- Полное логирование

### ✅ Гибкость:
- Легко добавлять пользователей
- Управление ролями через UI
- Расширяемая система разрешений

### ✅ Масштабируемость:
- SQLite для малых проектов
- Легко мигрировать на PostgreSQL
- Модульная архитектура

## 🔧 Дополнительные возможности

### Планируемые улучшения:
1. **Двухфакторная аутентификация** - подтверждение входа в боте
2. **QR-коды** - для быстрого входа с мобильных
3. **Одноразовые токены** - для критичных операций
4. **Уведомления** - о входах в систему
5. **API токены** - для программного доступа
6. **Сессии** - управление активными сессиями
7. **Аудит** - детальные отчеты по действиям

---

*Документация обновлена: 21.09.2024*
*Версия системы: 1.0.0*