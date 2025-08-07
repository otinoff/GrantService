# Структура базы данных GrantService

## Общая информация

**Файл базы данных:** `/var/GrantService/data/grantservice.db`  
**Тип БД:** SQLite3  
**Кодировка:** UTF-8  
**Часовой пояс:** GMT+7 (Кемерово)

## Таблицы

### 1. interview_questions - Вопросы интервью

**Назначение:** Хранение вопросов для интервью с пользователями

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Первичный ключ | PRIMARY KEY, AUTOINCREMENT |
| `question_number` | INTEGER | Номер вопроса | NOT NULL |
| `question_text` | TEXT | Текст вопроса | NOT NULL |
| `field_name` | VARCHAR(100) | Имя поля для сохранения ответа | NOT NULL |
| `question_type` | VARCHAR(50) | Тип вопроса | DEFAULT 'text' |
| `options` | TEXT | JSON строка с вариантами ответов | NULL |
| `hint_text` | TEXT | Подсказка к вопросу | NULL |
| `is_required` | BOOLEAN | Обязательный вопрос | DEFAULT 1 |
| `follow_up_question` | TEXT | Дополнительный вопрос | NULL |
| `validation_rules` | TEXT | JSON строка с правилами валидации | NULL |
| `is_active` | BOOLEAN | Активен ли вопрос | DEFAULT 1 |
| `created_at` | TIMESTAMP | Дата создания | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Дата обновления | DEFAULT CURRENT_TIMESTAMP |

**Индексы:**
- `idx_questions_number` - по полю `question_number`
- `idx_questions_active` - по полю `is_active`

### 2. users - Пользователи

**Назначение:** Хранение информации о пользователях Telegram

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Первичный ключ | PRIMARY KEY, AUTOINCREMENT |
| `telegram_id` | BIGINT | ID пользователя в Telegram | UNIQUE, NOT NULL |
| `username` | VARCHAR(100) | Username в Telegram | NULL |
| `first_name` | VARCHAR(100) | Имя пользователя | NULL |
| `last_name` | VARCHAR(100) | Фамилия пользователя | NULL |
| `registration_date` | TIMESTAMP | Дата регистрации | DEFAULT CURRENT_TIMESTAMP |
| `last_active` | TIMESTAMP | Последняя активность | DEFAULT CURRENT_TIMESTAMP |
| `total_sessions` | INTEGER | Общее количество сессий | DEFAULT 0 |
| `completed_applications` | INTEGER | Завершенные заявки | DEFAULT 0 |
| `is_active` | BOOLEAN | Активен ли пользователь | DEFAULT 1 |

**Индексы:**
- `idx_users_telegram_id` - по полю `telegram_id`

### 3. sessions - Сессии пользователей

**Назначение:** Хранение сессий работы пользователей с системой

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Первичный ключ | PRIMARY KEY, AUTOINCREMENT |
| `telegram_id` | BIGINT | ID пользователя | FOREIGN KEY → users(telegram_id) |
| `current_step` | VARCHAR(50) | Текущий шаг в процессе | NULL |
| `status` | VARCHAR(30) | Статус сессии | DEFAULT 'active' |
| `conversation_history` | TEXT | JSON строка с историей чата | NULL |
| `collected_data` | TEXT | JSON строка с собранными данными | NULL |
| `interview_data` | TEXT | JSON строка с данными интервью | NULL |
| `audit_result` | TEXT | JSON строка с результатом аудита | NULL |
| `plan_structure` | TEXT | JSON строка со структурой плана | NULL |
| `final_document` | TEXT | Финальный документ | NULL |
| `project_name` | VARCHAR(300) | Название проекта | NULL |
| `started_at` | TIMESTAMP | Время начала сессии | DEFAULT CURRENT_TIMESTAMP |
| `completed_at` | TIMESTAMP | Время завершения сессии | NULL |
| `last_activity` | TIMESTAMP | Последняя активность | DEFAULT CURRENT_TIMESTAMP |
| `total_messages` | INTEGER | Общее количество сообщений | DEFAULT 0 |
| `ai_requests_count` | INTEGER | Количество запросов к ИИ | DEFAULT 0 |

**Индексы:**
- `idx_sessions_telegram_id` - по полю `telegram_id`

## Вопросы по умолчанию

Система автоматически создает 7 базовых вопросов:

1. **Название проекта** (3-7 слов)
2. **Описание проекта** (суть в 20-500 символов)
3. **Регион реализации** (город/область)
4. **Описание проблемы** (30+ символов)
5. **Целевая аудитория** (20+ символов)
6. **Главная цель** (10+ символов)
7. **Конкретные задачи** (30+ символов)

## Основные методы

### Управление вопросами
- `get_active_questions()` - получить все активные вопросы
- `get_question_by_number()` - получить вопрос по номеру
- `validate_answer()` - валидация ответа
- `create_question()` - создать новый вопрос
- `update_question()` - обновить вопрос
- `delete_question()` - удалить вопрос (мягкое удаление)

### Управление пользователями
- `register_user()` - регистрация пользователя
- `get_all_users()` - получить всех пользователей
- `get_users_statistics()` - статистика по пользователям

### Управление сессиями
- `create_session()` - создать новую сессию
- `get_user_sessions()` - получить сессии пользователя
- `get_session_progress()` - прогресс заполнения
- `get_active_sessions()` - активные сессии
- `get_completed_sessions()` - завершенные сессии
- `save_user_answer()` - сохранить ответ пользователя

## Особенности

1. **Временные зоны:** Все временные метки сохраняются в часовом поясе Кемерово (GMT+7)
2. **JSON данные:** Сложные данные хранятся в JSON формате в текстовых полях
3. **Мягкое удаление:** Вопросы не удаляются физически, а помечаются как неактивные
4. **Валидация:** Встроенная система валидации ответов с настраиваемыми правилами
5. **Прогресс:** Автоматический расчет прогресса заполнения анкеты

## Создание и инициализация

```python
from database import GrantServiceDatabase

# Создание экземпляра БД
db = GrantServiceDatabase()

# Инициализация таблиц и добавление вопросов по умолчанию
db.init_database()
db.insert_default_questions()
```

## Глобальный экземпляр

В конце файла создается глобальный экземпляр БД:
```python
db = GrantServiceDatabase()
``` 