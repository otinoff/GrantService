# GrantService

Система управления грантами с Telegram ботом и веб-админ панелью.

## Описание

GrantService - это комплексная система для проведения интервью и сбора заявок на гранты через Telegram бот с веб-административной панелью для управления вопросами и настройками.

## Компоненты

### 1. Telegram Bot (`telegram-bot/`)
- Интерактивное интервью с пользователями
- Динамические вопросы из базы данных
- Валидация ответов
- Подсказки и правила валидации

### 2. Веб-админ панель (`web-admin/`)
- Управление вопросами интервью
- Настройка подсказок и правил валидации
- Аналитика и мониторинг
- Редактор промптов

### 3. База данных (`data/`)
- SQLite база данных
- Таблицы: `interview_questions`, `users`, `sessions`
- Динамическое управление вопросами

## Установка и запуск

### Требования
- Python 3.8+
- Nginx
- Systemd

### Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd GrantService
```

2. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Установите зависимости:
```bash
# Для веб-админ панели
cd web-admin
pip install -r requirements.txt

# Для Telegram бота
cd ../telegram-bot
pip install -r requirements.txt
```

4. Настройте базу данных:
```bash
cd ../data
python init_questions_full.py
```

5. Настройте Nginx:
```bash
# Скопируйте конфигурацию
sudo cp nginx/grantservice.onff.ru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

6. Настройте systemd сервисы:
```bash
# Веб-админ панель
sudo cp systemd/grantservice-web-admin.service /etc/systemd/system/
sudo systemctl enable grantservice-web-admin
sudo systemctl start grantservice-web-admin

# Telegram бот
sudo cp systemd/grantservice-bot.service /etc/systemd/system/
sudo systemctl enable grantservice-bot
sudo systemctl start grantservice-bot
```

## Структура проекта

```
GrantService/
├── telegram-bot/          # Telegram бот
│   ├── main.py           # Основной файл бота
│   └── requirements.txt  # Зависимости бота
├── web-admin/            # Веб-админ панель
│   ├── main_admin.py     # Основной файл Streamlit
│   └── requirements.txt  # Зависимости веб-панели
├── data/                 # База данных и данные
│   ├── database.py       # Модуль работы с БД
│   ├── init_questions_full.py  # Инициализация вопросов
│   └── qwestions.md      # Список вопросов
├── nginx/                # Конфигурации Nginx
├── systemd/              # Systemd сервисы
└── README.md
```

## Функциональность

### Telegram Bot
- Автоматическое интервью с 24 вопросами
- Динамические подсказки
- Валидация ответов (длина текста, числовые значения)
- Сохранение сессий пользователей

### Веб-админ панель
- Управление вопросами (CRUD операции)
- Настройка подсказок и правил валидации
- Аналитика ответов пользователей
- Редактор промптов для AI

### База данных
- Хранение вопросов с метаданными
- Сессии пользователей
- Ответы и статистика

## Настройка

### Telegram Bot Token
Создайте файл `telegram-bot/config.py`:
```python
BOT_TOKEN = "your_bot_token_here"
```

### База данных
База данных автоматически создается при первом запуске. Для изменения вопросов используйте веб-админ панель или отредактируйте `data/init_questions_full.py`.

## Мониторинг

### Логи
- Telegram бот: `sudo journalctl -u grantservice-bot -f`
- Веб-панель: `sudo journalctl -u grantservice-web-admin -f`
- Nginx: `/var/log/nginx/grantservice.error.log`

### Статус сервисов
```bash
sudo systemctl status grantservice-bot
sudo systemctl status grantservice-web-admin
sudo systemctl status nginx
```

## Лицензия

MIT License 