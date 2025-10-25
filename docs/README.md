# GrantService Project - Проект верхнего уровня

## О проекте

**GrantService** - AI-powered платформа для автоматизации создания грантовых заявок в Фонд президентских грантов (ФПГ).

**Миссия:** Помочь неравнодушным людям формализовать свои идеи, оформить по требованиям ФПГ и получить финансирование.

**Проблема:** Сложно читать все методические материалы, часто получают отказ. Финансирование получают "правильные", а не самые идейные.

---

## Структура проекта

```
GrantService_Project/
├── 00_Project_Info/          # Описание проекта, видение, архитектура
├── 01_Projects/              # Подпроекты и инициативы
│   └── 2025-10-20_Bootcamp/  # Текущий активный проект
├── 02_Research/              # Исследования, база знаний ФПГ
├── 03_Business/              # Бизнес-модель, финансы
├── 04_Reports/               # Отчеты и презентации
├── 05_Marketing/             # Маркетинг и коммуникации
├── 06_Archive/               # Архив старых материалов
└── _Agent_Work/              # Рабочая папка для AI агентов
```

---

## Расположение кода приложения

**Путь:** `C:\SnowWhiteAI\GrantService\`

**Репозиторий:** [GitHub - GrantService](https://github.com/yourusername/GrantService)

**Production:** http://5.35.88.251:8501

См. подробнее: [APPLICATION_LOCATION.md](APPLICATION_LOCATION.md)

---

## Текущие активные проекты

### 🔥 Буткемп "GrantService: AI-интервьюер"
**Папка:** `01_Projects/2025-10-20_Bootcamp_GrantService/`

**Цель:** Обучение и тестирование интерактивного AI-интервьюера для сбора информации о проектах.

**Статус:** Активный

---

## Workflow системы

1. **Анкетирование интервьюером** - Сбор информации о проекте (15 вопросов + уточняющие)
2. **Research агент** - Проверка актуальности, создание корпуса данных по теме
3. **Auditor агент** - Оценка качества анкеты и проекта (1-10 баллов)
4. **Planner агент** - Структурирование заявки
5. **Writer агент** - Написание грантовой заявки (Claude Opus 4)

---

## AI Агенты

- **InteractiveInterviewerAgent** (GigaChat) - Интерактивное интервью
- **ResearcherAgent** (Claude Sonnet 4.5 + WebSearch) - Исследования
- **AuditorAgent** (Claude Sonnet 4.5) - Аудит заявок
- **PlannerAgent** (Claude Sonnet 4.5) - Планирование структуры
- **WriterAgent** (Claude Opus 4) - Генерация текста заявки

---

## Технологический стек

- **Backend:** Python 3.9+, PostgreSQL
- **AI:** Claude Code API, GigaChat API
- **Bot:** python-telegram-bot
- **Admin:** Streamlit
- **Infrastructure:** n8n workflows, Docker, Qdrant (векторная БД)

---

## Контакты

**Разработчик:** Nikolay Stepanov
**Консультант:** Andrey Otinov (@otinoff)
**Email:** otinoff@gmail.com

---

**Создано:** 2025-10-20
**Версия:** 1.0
