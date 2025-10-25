# Getting Started - Как работать с проектом

## Структура создана! ✓

```
C:\SnowWhiteAI\
│
├── GrantService_Project/              # 🎯 ПРОЕКТ (бизнес, развитие)
│   ├── 00_Project_Info/               # Описание, видение, архитектура
│   │   ├── VISION.md
│   │   └── GETTING_STARTED.md
│   │
│   ├── 01_Projects/                   # 📁 Подпроекты
│   │   └── 2025-10-20_Bootcamp/       # 🔥 Активный: Буткемп
│   │       ├── 00_Project_Info/
│   │       ├── 01_Materials/
│   │       ├── 02_Participants/
│   │       ├── 03_Homework/
│   │       ├── 04_Reports/
│   │       └── README.md
│   │
│   ├── 02_Research/                   # Исследования
│   ├── 03_Business/                   # Бизнес-модель
│   ├── 04_Reports/                    # Отчеты
│   ├── 05_Marketing/                  # Маркетинг
│   ├── 06_Archive/                    # Архив
│   ├── _Agent_Work/                   # Работа AI агентов
│   │
│   ├── README.md                      # Главный README
│   └── APPLICATION_LOCATION.md        # Ссылка на код
│
└── GrantService/                      # 💻 КОД приложения
    ├── telegram-bot/
    ├── web-admin/
    ├── agents/
    └── ...
```

---

## Как использовать

### 1. Работа с проектом (GrantService_Project/)

**Это для:**
- Стратегического планирования
- Документирования развития
- Бизнес-анализа
- Подпроектов и инициатив
- Отчетов для стейкхолдеров

**Примеры задач:**
```bash
# Добавить новый подпроект
cd C:\SnowWhiteAI\GrantService_Project\01_Projects
mkdir 2025-11-XX_MVP_Launch

# Написать отчет о буткемпе
cd C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp\04_Reports
# создать weekly_report_1.md

# Обновить бизнес-модель
cd C:\SnowWhiteAI\GrantService_Project\03_Business
# редактировать pricing.md
```

---

### 2. Работа с кодом (GrantService/)

**Это для:**
- Разработки features
- Тестирования
- Деплоя
- Code review

**Примеры задач:**
```bash
# Запустить admin
cd C:\SnowWhiteAI\GrantService
python launcher.py

# Улучшить интервьюера
cd C:\SnowWhiteAI\GrantService\agents
# редактировать interactive_interviewer_agent.py

# Запустить тесты
cd C:\SnowWhiteAI\GrantService
pytest tests/
```

---

## Workflow для подпроектов

### Шаг 1: Создать новый подпроект

```bash
cd C:\SnowWhiteAI\GrantService_Project\01_Projects
mkdir 2025-XX-XX_Project_Name
cd 2025-XX-XX_Project_Name

# Создать структуру
mkdir 00_Project_Info 01_Materials 02_Data 03_Results 04_Reports _Archive
```

### Шаг 2: Создать README.md

```markdown
# Project Name

## Цель
...

## Задачи
1. ...
2. ...

## Timeline
- Week 1: ...
- Week 2: ...

## Метрики успеха
1. ...
2. ...
```

### Шаг 3: Работать в подпроекте

- Собирать материалы в `01_Materials/`
- Сохранять данные в `02_Data/`
- Писать отчеты в `04_Reports/`

### Шаг 4: По завершении

- Создать финальный отчет в `04_Reports/SUMMARY.md`
- Переместить в архив: `_Archive/`
- Обновить главный README

---

## Связь проект ↔ код

### Из проекта в код:

```markdown
# В PROJECT_INFO.md
Код реализации: `C:\SnowWhiteAI\GrantService\agents\interviewer.py`
```

### Из кода в проект:

```python
# В interviewer.py
"""
Документация проекта: C:\SnowWhiteAI\GrantService_Project\00_Project_Info\
Текущий буткемп: C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp\
"""
```

---

## Примеры сценариев

### Сценарий 1: Запуск буткемпа

1. Открыть: `01_Projects/2025-10-20_Bootcamp/`
2. Прочитать: `README.md`
3. Подготовить материалы в: `01_Materials/`
4. Добавить участников в: `02_Participants/`
5. Запустить интервью через код: `C:\SnowWhiteAI\GrantService\telegram-bot\`
6. Собрать результаты в: `04_Reports/`

### Сценарий 2: Презентация проекта

1. Открыть: `00_Project_Info/VISION.md`
2. Добавить слайды в: `05_Marketing/`
3. Создать демо через: `C:\SnowWhiteAI\GrantService\web-admin\`

### Сценарий 3: Разработка новой фичи

1. Написать план в: `01_Projects/2025-XX-XX_Feature_Name/`
2. Реализовать в коде: `C:\SnowWhiteAI\GrantService\agents\`
3. Задокументировать в: `01_Projects/.../04_Reports/`

---

## AI Agents работа

### Claude Code агенты

Когда Claude Code работает над задачами, используйте `_Agent_Work/` для:
- Временных файлов
- Анализа данных
- Черновиков документов

**Не коммитить в git!** (добавлено в .gitignore)

---

## Best Practices

1. **Один подпроект = одна папка** с датой создания
2. **README.md обязателен** в каждом подпроекте
3. **Ссылки между проектом и кодом** через APPLICATION_LOCATION.md
4. **Архивирование** завершенных подпроектов в `_Archive/`
5. **Регулярные отчеты** в `04_Reports/`

---

## Что дальше?

### Для буткемпа:
1. Заполнить `01_Materials/instructions.md`
2. Добавить примеры в `01_Materials/examples.md`
3. Рекрутировать участников
4. Запустить интервью
5. Собрать feedback в `04_Reports/`

### Для проекта:
1. Перенести документы из `GrantService/` в `00_Project_Info/`
2. Переместить `fpg_docs_2025/` в `02_Research/`
3. Создать бизнес-план в `03_Business/`
4. Написать презентацию в `05_Marketing/`

---

**Документ создан:** 2025-10-20
**Обновлен:** 2025-10-20
