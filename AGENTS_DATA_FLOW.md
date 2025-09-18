# 🤖 АГЕНТЫ GRANTSERVICE: ВХОДНЫЕ И ВЫХОДНЫЕ ДАННЫЕ

## 📊 ОБЩАЯ АРХИТЕКТУРА ПОТОКА ДАННЫХ

```
Заявка сайт → Оплата → Интервьюер → Аналитик → Исследователь → Писатель → Аудитор → Готовая заявка
```

## 🎯 ДЕТАЛЬНОЕ ОПИСАНИЕ АГЕНТОВ

### 1. 🤖 ИНТЕРВЬЮЕР (TELEGRAM БОТ)

**🎯 Назначение:** Программный опрос пользователя через Telegram бота

**📥 ВХОДНЫЕ ДАННЫЕ:**
```json
{
  "user_id": 123456789,
  "application_id": "app_001",
  "payment_status": "completed",
  "grant_type": "startup",
  "initial_data": {
    "project_name": "Название проекта",
    "description": "Краткое описание",
    "requested_amount": 1000000
  }
}
```

**⚙️ ПРОЦЕСС ОБРАБОТКИ:**
- Загрузка конфигурируемых вопросов из БД
- Последовательный опрос пользователя (10-20 вопросов)
- Валидация ответов
- Сохранение промежуточных результатов

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "interview_id": "int_001",
  "user_id": 123456789,
  "application_id": "app_001",
  "interview_status": "completed",
  "questionnaire": {
    "question_1": {
      "question": "Опишите ваш проект",
      "answer": "Разрабатываю ИИ-платформу для...",
      "answer_type": "text",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "question_2": {
      "question": "Какая сумма нужна?",
      "answer": "1000000 рублей",
      "answer_type": "number",
      "timestamp": "2024-01-15T10:32:00Z"
    },
    "question_3": {
      "question": "Размер команды?",
      "answer": "5 человек",
      "answer_type": "number",
      "timestamp": "2024-01-15T10:34:00Z"
    }
    // ... до 20 вопросов
  },
  "completion_percentage": 100,
  "interview_duration_minutes": 15,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:45:00Z"
}
```

---

### 2. 📊 АНАЛИТИК

**🎯 Назначение:** Анализ готовности анкеты и принятие решения о дальнейшем движении

**📥 ВХОДНЫЕ ДАННЫЕ:**
```json
{
  "interview_id": "int_001",
  "questionnaire": {
    // Анкета с ответами от интервьюера
  },
  "analysis_criteria": {
    "min_completion_percentage": 80,
    "required_questions": ["question_1", "question_2", "question_3"],
    "quality_threshold": 0.7
  }
}
```

**⚙️ ПРОЦЕСС ОБРАБОТКИ:**
- Анализ полноты анкеты
- Проверка качества ответов
- Оценка готовности к исследованию
- Принятие решения (передать дальше / вернуть на доп. вопросы)

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "analysis_id": "anal_001",
  "interview_id": "int_001",
  "analysis_status": "passed", // "passed" | "needs_more_questions" | "rejected"
  "analysis_score": 0.85,
  "completeness_score": 0.9,
  "quality_score": 0.8,
  "decision": "pass_to_researcher",
  "feedback": {
    "strengths": ["Полная информация о проекте", "Четкие финансовые планы"],
    "weaknesses": ["Недостаточно деталей о команде"],
    "recommendations": ["Можно передавать исследователю"]
  },
  "additional_questions_needed": [], // Если нужны доп. вопросы
  "next_agent": "researcher",
  "created_at": "2024-01-15T10:50:00Z"
}
```

---

### 3. 🔍 ИССЛЕДОВАТЕЛЬ

**🎯 Назначение:** Проведение исследования на основе анкеты с использованием LLM

**📥 ВХОДНЫЕ ДАННЫЕ:**
```json
{
  "analysis_id": "anal_001",
  "questionnaire": {
    // Анкета с ответами от интервьюера
  },
  "research_prompts": {
    "market_research": "Проведи анализ рынка для проекта...",
    "competitor_analysis": "Найди конкурентов в области...",
    "grant_opportunities": "Найди подходящие гранты для...",
    "success_factors": "Определи факторы успеха для..."
  },
  "llm_settings": {
    "provider": "gigachat",
    "model": "GigaChat-Pro",
    "temperature": 0.3,
    "max_tokens": 2000
  }
}
```

**⚙️ ПРОЦЕСС ОБРАБОТКИ:**
- Анализ рынка и конкурентов
- Поиск подходящих грантов
- Исследование требований и критериев
- Анализ факторов успеха
- Сбор статистики и данных

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "research_id": "res_001",
  "analysis_id": "anal_001",
  "research_status": "completed",
  "market_analysis": {
    "market_size": "1.2 млрд рублей",
    "growth_rate": "15% в год",
    "key_trends": ["ИИ-технологии", "Автоматизация"],
    "market_maturity": "growing"
  },
  "competitor_analysis": {
    "competitors": [
      {
        "name": "Конкурент 1",
        "strengths": ["Большая команда", "Финансирование"],
        "weaknesses": ["Медленная разработка"],
        "market_share": "25%"
      }
    ],
    "competitive_advantages": ["Уникальная технология", "Быстрый выход на рынок"]
  },
  "grant_opportunities": [
    {
      "grant_name": "Фонд развития ИИ",
      "amount": "500000-2000000",
      "deadline": "2024-03-15",
      "match_percentage": 85,
      "requirements": ["ИИ-проект", "Инновационность"],
      "success_rate": "12%"
    }
  ],
  "success_factors": [
    "Инновационность решения",
    "Четкий план реализации",
    "Опытная команда",
    "Рыночный потенциал"
  ],
  "research_metadata": {
    "sources_used": 15,
    "processing_time_seconds": 45,
    "llm_provider": "gigachat",
    "tokens_used": 1500
  },
  "created_at": "2024-01-15T11:00:00Z"
}
```

---

### 4. ✍️ ПИСАТЕЛЬ

**🎯 Назначение:** Создание бета-версии заявки на основе данных исследования

**📥 ВХОДНЫЕ ДАННЫЕ:**
```json
{
  "research_id": "res_001",
  "questionnaire": {
    // Анкета с ответами от интервьюера
  },
  "research_data": {
    // Результаты исследования
  },
  "writing_prompts": {
    "executive_summary": "Создай краткое резюме проекта...",
    "project_description": "Опиши проект подробно...",
    "methodology": "Опиши методологию реализации...",
    "budget_justification": "Обоснуй бюджет проекта...",
    "timeline": "Создай план реализации..."
  },
  "llm_settings": {
    "provider": "gigachat",
    "model": "GigaChat-Pro",
    "temperature": 0.4,
    "max_tokens": 3000
  }
}
```

**⚙️ ПРОЦЕСС ОБРАБОТКИ:**
- Создание структуры заявки
- Написание разделов по промптам
- Интеграция данных исследования
- Форматирование и структурирование

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "writing_id": "wrt_001",
  "research_id": "res_001",
  "writing_status": "completed",
  "beta_application": {
    "executive_summary": "Проект представляет собой инновационную ИИ-платформу...",
    "project_description": "Наш проект направлен на создание...",
    "problem_statement": "В настоящее время существует проблема...",
    "solution": "Мы предлагаем решение, основанное на...",
    "methodology": "Проект будет реализован в три этапа...",
    "timeline": {
      "phase_1": "Январь-Март 2024: Разработка прототипа",
      "phase_2": "Апрель-Июнь 2024: Тестирование",
      "phase_3": "Июль-Сентябрь 2024: Внедрение"
    },
    "budget": {
      "total_amount": 1000000,
      "breakdown": {
        "development": 400000,
        "testing": 200000,
        "marketing": 200000,
        "operations": 200000
      }
    },
    "team": {
      "project_manager": "Иван Иванов",
      "technical_lead": "Петр Петров",
      "team_size": 5
    },
    "expected_outcomes": [
      "Создание работающего прототипа",
      "Привлечение 1000 пользователей",
      "Получение патента"
    ]
  },
  "writing_metadata": {
    "sections_completed": 8,
    "total_words": 2500,
    "processing_time_seconds": 120,
    "llm_provider": "gigachat",
    "tokens_used": 2800
  },
  "created_at": "2024-01-15T11:30:00Z"
}
```

---

### 5. 🔍 АУДИТОР

**🎯 Назначение:** Финальная проверка и аудит бета-версии заявки

**📥 ВХОДНЫЕ ДАННЫЕ:**
```json
{
  "writing_id": "wrt_001",
  "beta_application": {
    // Бета-версия заявки от писателя
  },
  "questionnaire": {
    // Анкета с ответами от интервьюера
  },
  "research_data": {
    // Данные исследования
  },
  "audit_criteria": {
    "completeness_threshold": 0.9,
    "quality_threshold": 0.8,
    "consistency_threshold": 0.85,
    "grant_match_threshold": 0.7
  },
  "llm_settings": {
    "provider": "gigachat",
    "model": "GigaChat-Pro",
    "temperature": 0.2,
    "max_tokens": 2000
  }
}
```

**⚙️ ПРОЦЕСС ОБРАБОТКИ:**
- Проверка полноты заявки
- Оценка качества содержания
- Проверка соответствия требованиям гранта
- Анализ консистентности данных
- Генерация рекомендаций

**📤 ВЫХОДНЫЕ ДАННЫЕ:**
```json
{
  "audit_id": "aud_001",
  "writing_id": "wrt_001",
  "audit_status": "approved", // "approved" | "needs_revision" | "rejected"
  "overall_score": 0.87,
  "audit_results": {
    "completeness_score": 0.92,
    "quality_score": 0.85,
    "consistency_score": 0.88,
    "grant_match_score": 0.82
  },
  "strengths": [
    "Четкое описание проекта",
    "Обоснованный бюджет",
    "Реалистичный план реализации"
  ],
  "weaknesses": [
    "Недостаточно деталей о команде",
    "Слабое обоснование инновационности"
  ],
  "recommendations": [
    "Добавить информацию о ключевых членах команды",
    "Усилить раздел об инновационности",
    "Добавить риски проекта"
  ],
  "final_application": {
    // Финальная версия заявки с исправлениями
    "status": "ready_for_submission",
    "submission_deadline": "2024-03-15",
    "grant_name": "Фонд развития ИИ",
    "confidence_score": 0.87
  },
  "audit_metadata": {
    "processing_time_seconds": 60,
    "llm_provider": "gigachat",
    "tokens_used": 1800,
    "auditor_notes": "Заявка готова к подаче с небольшими улучшениями"
  },
  "created_at": "2024-01-15T12:00:00Z"
}
```

---

## 🔄 ОБРАТНЫЕ СВЯЗИ И ИСКЛЮЧЕНИЯ

### **Обратная связь от Аудитора к Интервьюеру:**
```json
{
  "feedback_type": "additional_questions_needed",
  "audit_id": "aud_001",
  "questions": [
    "Укажите опыт ключевых членов команды",
    "Опишите уникальность вашего решения",
    "Какие риски вы видите в проекте?"
  ],
  "priority": "high",
  "deadline": "2024-01-20T12:00:00Z"
}
```

### **Альтернативный путь (без оплаты):**
```json
{
  "path": "direct_audit",
  "application_data": "Минимальные данные",
  "result": "Рекомендации без полной обработки"
}
```

---

## 📊 МЕТРИКИ И МОНИТОРИНГ

### **Ключевые метрики для каждого агента:**
- Время обработки
- Количество токенов использовано
- Качество результата (score)
- Статус завершения
- Ошибки и исключения

### **Общие метрики системы:**
- Общее время обработки заявки
- Конверсия между этапами
- Успешность подачи заявок
- ROI системы

---

## 🔧 ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ

### **Форматы данных:**
- **Внутренний**: JSON для передачи между агентами
- **Хранение**: SQLite с JSON полями
- **API**: RESTful для внешних интеграций

### **Логирование:**
- Все действия агентов логируются
- Сохраняется полная история обработки
- Возможность отката к любому этапу

### **Масштабирование:**
- Каждый агент может работать независимо
- Возможность параллельной обработки
- Очереди для управления нагрузкой

---

## 🔐 СИСТЕМА АВТОРИЗАЦИИ

### **Настройка доступа:**
- **ADMIN_USERS**: Множество Telegram ID администраторов с полным доступом.
- **ALLOWED_USERS**: Множество разрешенных Telegram ID. Если пустое - доступ всем.

### **Проверка доступа:**
- Все команды и callback'и в Telegram боте проверяют авторизацию пользователя.
- Несанкционированные пользователи получают сообщение "Доступ запрещен".
- Все страницы Streamlit админки проверяют авторизацию через токены.

### **Конфигурация:**
Параметры авторизации задаются в `GrantService/telegram-bot/config/constants.py`.

### **Авторизация в Streamlit админке:**
- Пользователи получают ссылку авторизации через Telegram бот (`/login` или `/admin`).
- Ссылка содержит токен авторизации, действительный 24 часа.
- При переходе по ссылке создается сессия в Streamlit.
- Все страницы админки защищены от несанкционированного доступа.
- Администраторы имеют доступ к расширенным функциям.

### **Токены авторизации:**
- Формат: `token_<timestamp>_<random_hex>`
- Срок действия: 24 часа
- Хранение: В БД в поле `login_token` таблицы `users`
- Генерация: Через команды `/login` и `/admin` в Telegram боте
