Привет, Андрей! Давайте посмотрим на проект GrantService в папке web-admin. Сначала проверим структуру проекта и основные файлы.
```bash
date
```
Ran tool
Отлично! Вижу интересную структуру проекта web-admin. Давайте подробнее изучим основные компоненты:
Ran tool
Ran tool
Ran tool
Ran tool
Теперь давайте посмотрим на основные файлы конфигурации и структуру:
Read file: /var/GrantService/web-admin/requirements.txt
Read file: /var/GrantService/web-admin/main_admin.py
Read file: /var/GrantService/web-admin/admin_panel_fastapi.py
Теперь давайте посмотрим на backend структуру:
Ran tool
Ran tool
Ran tool
Ran tool
Давайте посмотрим на ключевые страницы и понимание архитектуры:
Read file: /var/GrantService/web-admin/pages/🏠_Главная.py
Read file: /var/GrantService/web-admin/utils/database.py
Давайте посмотрим на остальную часть database.py и некоторые другие ключевые файлы:
Read file: /var/GrantService/web-admin/utils/database.py
Read file: /var/GrantService/web-admin/backend/models/question.py
Read file: /var/GrantService/web-admin/pages/👥_Пользователи.py
Теперь давайте проверим виртуальное окружение и посмотрим на логи:
```bash
ls -la /var/GrantService/web-admin/venv/
```
Read file: /var/GrantService/web-admin/nohup.out
```bash
ps aux | grep -E "(streamlit|uvicorn|python.*admin)" | grep -v grep
```
Теперь давайте посмотрим на некоторые ключевые аналитические файлы:
Read file: /var/GrantService/web-admin/pages/🔬_Аналитика_исследователя.py
Read file: /var/GrantService/web-admin/utils/charts.py
Ran tool
Отлично! Теперь давайте создам общий анализ проекта GrantService web-admin:
Ran tool
## 🏆 Обзор проекта GrantService Web-Admin

Андрей, отличный проект! [[memory:3912903]] Проект GrantService имеет правильную архитектуру с изолированным виртуальным окружением. Вот подробный анализ:

### 📊 **Архитектура системы**

**Двухуровневая админ панель:**
1. **Streamlit Dashboard** (порт 8501) - основной интерфейс
2. **FastAPI Server** (порт 8000) - API бэкенд

### 🎯 **Ключевые компоненты**

**Frontend (Streamlit):**
- 📱 **Главная панель** - статистика системы, метрики
- 👥 **Управление пользователями** - прогресс анкет, экспорт данных
- 🔬 **Аналитика исследователя** - интеграция с Perplexity AI
- ❓ **Управление вопросами** - конструктор интервью
- 🧑‍💼 **Agent Prompts** - управление промптами ИИ

**Backend (FastAPI):**
- REST API для статуса бота
- Аналитические endpoint'ы
- Интеграция с Telegram API

**Database Layer:**
- SQLite база данных
- Утилиты для работы с данными
- Система логирования

### 💻 **Текущее состояние**

✅ **Работает стабильно:**
- Streamlit сервер активен (PID 841)
- FastAPI сервер запущен (PID 840) 
- Виртуальное окружение настроено
- Зависимости установлены

### 🔧 **Техническая оценка**

**Сильные стороны:**
- Модульная архитектура с разделением на страницы
- Правильное использование venv [[memory:3912903]]
- Качественная система логирования
- Интеграция с внешними API (Telegram, Perplexity)
- Современный стек: FastAPI + Streamlit + Plotly

**Рекомендации для улучшения:**
1. Добавить мониторинг логов (папка logs пустая)
2. Настроить автоматический restart при сбоях
3. Добавить резервное копирование базы данных
4. Реализовать систему уведомлений об ошибках

### 📈 **Функциональность**

Система предоставляет полноценное управление грантовым сервисом:
- Мониторинг пользователей и их прогресса
- Аналитика использования ИИ-исследователя
- Управление интервью и вопросами
- Статистика и визуализация данных

Проект готов к продуктивному использованию! Нужно что-то конкретное проанализировать или улучшить?

---

## 🔧 Управление сервисами

### 📋 Системные сервисы GrantService:

1. **`grantservice-bot.service`** - Telegram Bot (основной бот)
2. **`grantservice-web-admin.service`** - FastAPI сервер (порт 8000)
3. **`grantservice-webadmin.service`** - Streamlit панель (порт 8501)

### 🚀 Команды управления:

#### 🔄 Полный перезапуск всех сервисов:
```bash
# Перезапуск всех компонентов GrantService
systemctl restart grantservice-bot.service
systemctl restart grantservice-web-admin.service  
systemctl restart grantservice-webadmin.service
```

#### 📊 Проверка статуса:
```bash
# Проверка всех сервисов
systemctl status grantservice-*.service

# Проверка отдельных компонентов
systemctl status grantservice-webadmin.service      # Streamlit
systemctl status grantservice-web-admin.service     # FastAPI
systemctl status grantservice-bot.service           # Telegram Bot
```

#### 🛑 Остановка/запуск:
```bash
# Остановка
systemctl stop grantservice-webadmin.service
systemctl stop grantservice-web-admin.service

# Запуск
systemctl start grantservice-webadmin.service
systemctl start grantservice-web-admin.service
```

#### 📝 Просмотр логов systemd:
```bash
# Логи Streamlit админ панели
journalctl -u grantservice-webadmin.service -f

# Логи FastAPI сервера
journalctl -u grantservice-web-admin.service -f

# Логи Telegram бота
journalctl -u grantservice-bot.service -f
```

### 🔍 Мониторинг процессов:
```bash
# Проверка запущенных процессов
ps aux | grep -E "(streamlit|uvicorn|python.*admin)" | grep -v grep

# Проверка портов
netstat -tlnp | grep -E "(8000|8501)"
```

---

## 📋 Система логирования v2.0

### 📁 Расположение логов:
- **Системные логи:** `/var/GrantService/web-admin/logs/`
- **Основные компоненты:** `web_admin.log`, `database.log`, `api.log`
- **Только ошибки:** `*_errors.log`
- **Дневная ротация:** `*_daily.log`

### 🎛️ Web-интерфейс мониторинга:
- **URL:** http://your-domain:8501
- **Страница:** 📋 Мониторинг логов
- **Возможности:** просмотр, фильтрация, скачивание, анализ ошибок

### 🚨 При ошибках JS (MIME type):
1. **Очистить кэш браузера** (Ctrl+F5)
2. **Перезапустить Streamlit:** `systemctl restart grantservice-webadmin.service`
3. **Проверить nginx конфигурацию** для статических файлов
4. **Проверить логи:** `/var/GrantService/web-admin/logs/web_admin_errors.log`

---

*Последнее обновление: 15.08.2025 - добавлена система логирования v2.0*

graph TB
    subgraph "GrantService Web Admin Architecture"
        direction TB
        
        subgraph "Frontend Layer"
            SL[Streamlit Dashboard<br/>Port 8501]
            FE[Frontend/React<br/>src/views/]
        end
        
        subgraph "Backend Layer"
            FA[FastAPI Server<br/>Port 8000]
            API[Backend API<br/>api/questions.py]
            SRV[Services<br/>question_service.py]
        end
        
        subgraph "Data Layer"
            DB[(SQLite Database<br/>GrantService.db)]
            UTIL[Utils<br/>database.py<br/>charts.py<br/>logger.py]
        end
        
        subgraph "Core Features"
            USR["👥 Users Management"]
            ANL["🔬 Researcher Analytics"]
            QST["❓ Questions Management"] 
            PRO["🧑‍💼 Agent Prompts"]
            TST["🧪 Test Prompts"]
        end
        
        SL --> USR
        SL --> ANL
        SL --> QST
        SL --> PRO
        SL --> TST
        
        FA --> API
        API --> SRV
        SRV --> DB
        
        USR --> UTIL
        ANL --> UTIL
        QST --> UTIL
        UTIL --> DB
        
        FE -.-> FA
        SL -.-> FA
    end
    
    subgraph "External"
        TG[Telegram Bot<br/>Main Service]
        PX[Perplexity AI<br/>Research Service]
    end
    
    FA --> TG
    ANL --> PX
    
    style SL fill:#e1f5fe
    style FA fill:#f3e5f5
    style DB fill:#e8f5e8
    style TG fill:#fff3e0
    style PX fill:#fce4ec