# Архитектура системы ГрантСервис
## Техническая документация и реализация

**Версия:** 1.0  
**Дата создания:** 10 июля 2025  
**Статус:** Планирование завершено, готово к разработке  

---

## 🎯 **ОБЩАЯ АРХИТЕКТУРА СИСТЕМЫ**

### **Компоненты системы:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   n8n Workflows │    │  Web Admin Panel│
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Management)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GigaChat API  │    │   PostgreSQL    │    │   File Storage  │
│   (AI Engine)   │    │   (Database)    │    │   (Documents)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Поток данных:**
1. **Пользователь** → Telegram Bot (интерфейс)
2. **Telegram Bot** → n8n Workflows (бизнес-логика)
3. **n8n** → GigaChat API (ИИ-обработка)
4. **n8n** → PostgreSQL (сохранение данных)
5. **n8n** → File Storage (документы)
6. **Web Admin** → PostgreSQL (управление)

---

## 🤖 **TELEGRAM BOT (Frontend)**

### **Технологии:**
- **Framework:** python-telegram-bot v20+
- **Язык:** Python 3.9+
- **Хостинг:** Beget VPS

### **Функциональность:**
- **Команды:** `/start`, `/interview`, `/status`, `/help`
- **Этапы работы:** 4 агента (Интервьюер → Аудитор → Планировщик → Писатель)
- **Файлы:** Экспорт в Word/PDF форматах

### **Структура проекта:**
```
telegram-bot/
├── main.py              # Основной файл бота
├── handlers/            # Обработчики команд
│   ├── start.py        # Команда /start
│   ├── interview.py    # Агент-интервьюер
│   ├── auditor.py      # Агент-аудитор
│   ├── planner.py      # Агент-планировщик
│   └── writer.py       # Агент-писатель
├── services/           # Бизнес-логика
│   ├── gigachat.py     # Интеграция с GigaChat
│   ├── database.py     # Работа с БД
│   └── documents.py    # Генерация документов
├── config/             # Конфигурация
│   └── settings.py     # Настройки
└── requirements.txt    # Зависимости
```

### **API Endpoints (n8n webhooks):**
```
POST /webhook/telegram/start
POST /webhook/telegram/interview
POST /webhook/telegram/auditor
POST /webhook/telegram/planner
POST /webhook/telegram/writer
```

---

## ⚙️ **N8N WORKFLOWS (Backend)**

### **Технологии:**
- **Platform:** n8n.io
- **Хостинг:** Railway ($5/месяц) или Beget VPS
- **Интеграции:** GigaChat API, PostgreSQL, Telegram

### **Основные Workflows:**

#### **1. User Registration Workflow**
```
Telegram Webhook → Validate User → Create DB Record → Send Welcome
```

#### **2. Interview Agent Workflow**
```
User Input → GigaChat API → Save Response → Next Question → Update Progress
```

#### **3. Auditor Agent Workflow**
```
Project Data → GigaChat Analysis → Generate Report → Save Results
```

#### **4. Planner Agent Workflow**
```
Audit Results → GigaChat Planning → Create Structure → Save Plan
```

#### **5. Writer Agent Workflow**
```
Project Plan → GigaChat Writing → Generate Document → Export File
```

### **Переменные окружения:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token
GIGACHAT_API_KEY=your_gigachat_key
DATABASE_URL=postgresql://user:pass@host:port/db
WEBHOOK_URL=https://your-n8n-instance.com
```

---

## 🌐 **WEB ADMIN PANEL (Management)**

### **Технологии:**
- **Frontend:** Vue.js 3 + Bootstrap 5
- **Backend:** FastAPI (Python)
- **База данных:** PostgreSQL
- **Хостинг:** Beget VPS

### **Структура проекта:**
```
web-admin/
├── frontend/           # Vue.js приложение
│   ├── src/
│   │   ├── components/ # Vue компоненты
│   │   ├── views/      # Страницы
│   │   ├── router/     # Маршрутизация
│   │   └── store/      # Vuex store
│   └── public/         # Статические файлы
├── backend/            # FastAPI сервер
│   ├── app/
│   │   ├── api/        # API endpoints
│   │   ├── models/     # Pydantic модели
│   │   ├── services/   # Бизнес-логика
│   │   └── database/   # Работа с БД
│   └── main.py         # Точка входа
└── docker-compose.yml  # Контейнеризация
```

### **Основные страницы:**

#### **1. Dashboard (Главная)**
- Статистика использования системы
- Графики активности пользователей
- Последние созданные заявки
- Системные уведомления

#### **2. Prompt Manager (Управление промптами)**
- CRUD операции с промптами агентов
- Версионирование промптов
- Тестирование промптов
- A/B тестирование

#### **3. User Management (Пользователи)**
- Список всех пользователей
- Роли и права доступа
- Статистика по пользователям
- Блокировка/разблокировка

#### **4. Analytics (Аналитика)**
- Детальная аналитика использования
- Конверсия по этапам
- Время выполнения заявок
- Качество результатов

#### **5. System Monitoring (Мониторинг)**
- Логи системы
- Ошибки и исключения
- Производительность API
- Использование ресурсов

### **API Endpoints:**
```python
# Аутентификация
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/me

# Промпты
GET /api/prompts
POST /api/prompts
PUT /api/prompts/{id}
DELETE /api/prompts/{id}
POST /api/prompts/{id}/test

# Пользователи
GET /api/users
GET /api/users/{id}
PUT /api/users/{id}
DELETE /api/users/{id}

# Аналитика
GET /api/analytics/dashboard
GET /api/analytics/users
GET /api/analytics/applications
GET /api/analytics/performance

# Система
GET /api/system/logs
GET /api/system/health
GET /api/system/status
```

---

## 🧠 **GIGACHAT API (AI Engine)**

### **Интеграция:**
- **API Endpoint:** https://api.gigachat.ru/v1/chat/completions
- **Модель:** GigaChat-Max
- **Токены:** ~2000 на запрос
- **Стоимость:** ~50-100₽/месяц

### **Промпты агентов:**

#### **Агент-Интервьюер:**
```python
SYSTEM_PROMPT = """
Ты - эксперт по грантам, проводишь интервью для создания заявки.
Задавай последовательные вопросы:
1. Название и суть проекта  
2. Тип гранта и фонд
3. Целевая аудитория проекта
4. Бюджет и сроки реализации
5. Команда и компетенции
6. Уникальность и инновации

После каждого ответа задавай 1-2 уточняющих вопроса.
Собери полную информацию за 7-10 вопросов.
"""
```

#### **Агент-Аудитор:**
```python
SYSTEM_PROMPT = """
Ты - эксперт-аудитор грантовых проектов.
Анализируешь проект по критериям:

1. ИННОВАЦИОННОСТЬ (1-10): Насколько уникален проект?
2. РЕАЛИСТИЧНОСТЬ (1-10): Выполним ли план в срок/бюджет?  
3. КОМАНДА (1-10): Достаточно ли компетенций?
4. ВОЗДЕЙСТВИЕ (1-10): Масштаб пользы для аудитории
5. УСТОЙЧИВОСТЬ (1-10): Продолжится ли после гранта?

Дай общую оценку и 3-5 рекомендаций по улучшению.
"""
```

#### **Агент-Планировщик:**
```python
SYSTEM_PROMPT = """
Ты - эксперт по структурированию грантовых заявок.
На основе данных интервью создай детальный план заявки:

1. ТИТУЛЬНЫЙ ЛИСТ (название, сроки, бюджет)
2. АННОТАЦИЯ (краткое описание в 200 слов)  
3. АКТУАЛЬНОСТЬ (проблема, которую решаем)
4. ЦЕЛИ И ЗАДАЧИ (что достигнем, как измерим)
5. ПЛАН РЕАЛИЗАЦИИ (этапы, временные рамки)
6. БЮДЖЕТ (детальная смета расходов)
7. КОМАНДА (роли, компетенции, опыт)
8. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ (конкретные измеримые итоги)
9. УСТОЙЧИВОСТЬ (продолжение после завершения)
10. ПРИЛОЖЕНИЯ (документы, портфолио)
"""
```

#### **Агент-Писатель:**
```python
SYSTEM_PROMPT = """
Ты - профессиональный райтер грантовых заявок с опытом 10+ лет.
Пишешь убедительные тексты, которые выигрывают гранты.

На основе структуры создай полный текст заявки:
- Используй активный залог и конкретные факты
- Добавляй статистику и цифры для убедительности
- Пиши эмоционально, но профессионально  
- Подчеркивай уникальность и важность проекта
- Используй грантовую терминологию
- Объем каждого раздела 200-500 слов

Создавай тексты, которые побеждают в конкурсах!
"""
```

---

## 🗄️ **POSTGRESQL DATABASE**

### **Схема базы данных:**

#### **Таблица: users**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **Таблица: prompts**
```sql
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    prompt_text TEXT NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **Таблица: applications**
```sql
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255),
    grant_type VARCHAR(100),
    stage VARCHAR(50) DEFAULT 'interview',
    interview_data JSONB,
    audit_data JSONB,
    plan_data JSONB,
    final_document TEXT,
    is_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **Таблица: ai_requests**
```sql
CREATE TABLE ai_requests (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id),
    agent_type VARCHAR(50),
    prompt TEXT,
    response TEXT,
    tokens_used INTEGER,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### **Таблица: analytics**
```sql
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50),
    metric_value NUMERIC,
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 📁 **FILE STORAGE**

### **Структура хранения:**
```
/var/GrantService/storage/
├── documents/          # Готовые документы
│   ├── word/          # .docx файлы
│   ├── pdf/           # .pdf файлы
│   └── templates/     # Шаблоны документов
├── uploads/           # Загруженные файлы
│   ├── presentations/ # Презентации
│   ├── plans/         # Планы проектов
│   └── other/         # Прочие файлы
└── logs/              # Логи системы
    ├── telegram/      # Логи бота
    ├── n8n/           # Логи workflows
    └── web-admin/     # Логи админки
```

### **Форматы документов:**
- **Word (.docx):** Основной формат для заявок
- **PDF:** Для финальных версий
- **Templates:** Шаблоны для разных фондов

---

## 🔒 **БЕЗОПАСНОСТЬ**

### **Аутентификация:**
- JWT токены для веб-админки
- Telegram ID для бота
- Роли пользователей (user, admin, coordinator)

### **Защита данных:**
- HTTPS для всех соединений
- Хэширование паролей (bcrypt)
- Валидация всех входных данных
- Rate limiting для API

### **Соответствие требованиям:**
- Все данные на территории РФ
- Использование российской LLM (GigaChat)
- Согласие на обработку персональных данных

---

## 📊 **МОНИТОРИНГ И МЕТРИКИ**

### **Технические метрики:**
- Время ответа API (<2 секунд)
- Uptime сервиса (>99%)
- Использование ресурсов сервера
- Количество ошибок

### **Продуктовые метрики:**
- Количество активных пользователей
- Завершенных заявок
- Конверсия по этапам
- Среднее время создания заявки

### **Инструменты:**
- Логирование в файлы
- Health check endpoints
- Дашборд в веб-админке

---

## 🚀 **РАЗВЕРТЫВАНИЕ**

### **Инфраструктура:**
- **VPS:** Beget (российский провайдер)
- **Домен:** Поддомен от грантсервис.рф
- **SSL:** Let's Encrypt
- **Резервное копирование:** Ежедневные бэкапы

### **Контейнеризация:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  telegram-bot:
    build: ./telegram-bot
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./storage:/app/storage

  web-admin:
    build: ./web-admin
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - postgres

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=grantservice
      - POSTGRES_USER=grantservice
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 📋 **ПЛАН РАЗРАБОТКИ**

### **Фаза 1: MVP (16-30 июля)**
- ✅ Планирование и техзадание
- 🔄 Базовая разработка (16-23 июля)
- 📅 Завершение MVP (23-30 июля)

### **Фаза 2: Тестирование (1-15 августа)**
- Тестирование с 5-7 пользователями
- Сбор обратной связи
- Исправление багов

### **Фаза 3: Продакшн (1 сентября)**
- Полноценный запуск
- Маркетинг и привлечение пользователей
- Масштабирование

---

## 📞 **ПОДДЕРЖКА**

- **Разработчик:** Николай Степанов
- **Консультант:** Андрей Отинов (@otinoff)
- **Email:** otinoff@gmail.com
- **Документация:** /var/GrantService/docs/

---

**Документ создан:** 10 июля 2025  
**Последнее обновление:** 10 июля 2025  
**Статус:** Актуально 