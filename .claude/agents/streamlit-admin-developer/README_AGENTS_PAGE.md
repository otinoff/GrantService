# 🤖 AI Agents Page - Developer Guide

## 📍 Файл
`web-admin/pages/🤖_Агенты.py` (v3.0.0)

## 🎯 Назначение
Единая страница управления всеми 5 AI агентами системы GrantService.

---

## 📊 Структура страницы

```
🤖 AI Агенты (главная страница)
│
├── TAB 1: 📝 Interviewer Agent
│   ├── Статистика (4 метрики)
│   ├── Управление промптами
│   └── Будущие улучшения
│
├── TAB 2: ✅ Auditor Agent
│   ├── Статистика (4 метрики)
│   ├── Критерии оценки (5 критериев)
│   └── Управление промптами
│
├── TAB 3: 📐 Planner Agent
│   ├── Статистика (3 метрики)
│   ├── Шаблоны структур
│   └── Управление промптами
│
├── TAB 4: 🔍 Researcher Agent ⭐
│   ├── SUB-TAB 1: 📊 Статистика
│   ├── SUB-TAB 2: 🔬 Исследования (с фильтрами!)
│   └── SUB-TAB 3: 💰 Аналитика расходов
│
└── TAB 5: ✍️ Writer Agent
    ├── SUB-TAB 1: 📊 Статистика
    └── SUB-TAB 2: 📝 Тексты (с фильтрами!)
```

---

## 🔧 Ключевые функции

### get_agent_statistics(agent_type, _db, days=30)
Получает статистику по агенту из БД за последние N дней.

**Пример:**
```python
stats = get_agent_statistics('interviewer', db)
# Возвращает: {'total': 10, 'completed': 8, 'avg_progress': 85.5, ...}
```

### get_researcher_investigations(_db, filters=None)
Получает список всех исследований Researcher Agent.

**Возвращает:** List[Dict] с полями:
- research_id, anketa_id, username, user_id
- status, llm_provider, model
- created_at, completed_at
- research_results

### get_writer_generated_texts(_db, filters=None)
Получает список всех текстов Writer Agent.

**Возвращает:** List[Dict] с полями:
- id, grant_id, user_id, status
- created_at, updated_at, quality_score

---

## 🎨 UI Rendering Functions

### render_interviewer_tab()
Отображает таб Interviewer Agent: статистика + промпты.

### render_auditor_tab()
Отображает таб Auditor Agent: статистика + критерии + промпты.

### render_planner_tab()
Отображает таб Planner Agent: статистика + шаблоны + промпты.

### render_researcher_tab()
Главная функция для Researcher - создает 3 sub-tabs.

### render_researcher_statistics()
Sub-tab 1: метрики работы Researcher.

### render_researcher_investigations()
Sub-tab 2: таблица всех исследований с 4 фильтрами:
- Статус (все/completed/pending/processing/error)
- Период (все/сегодня/неделя/месяц)
- Провайдер (все/perplexity/gigachat/ollama)
- Пользователь (username или ID)

### render_researcher_cost_analytics()
Sub-tab 3: аналитика расходов на Perplexity API:
- Баланс аккаунта
- API Requests по моделям
- Input Tokens статистика

### render_writer_tab()
Главная функция для Writer - создает 2 sub-tabs.

### render_writer_statistics()
Sub-tab 1: метрики работы Writer.

### render_writer_texts()
Sub-tab 2: таблица всех текстов с 3 фильтрами:
- Статус (все/completed/draft/error)
- Период (все/сегодня/неделя/месяц)
- Лимит записей (10-100)

---

## 💾 Работа с базой данных

### Подключение
```python
db = get_database()  # GrantServiceDatabase
admin_db = get_admin_database()  # AdminDatabase
```

### SQL запросы
```python
# Interviewer stats
result = db.execute_query("""
    SELECT COUNT(*) as total, ...
    FROM sessions
    WHERE started_at >= datetime('now', '-30 days')
""")

# Writer texts
result = db.execute_query("""
    SELECT id, grant_id, user_id, status, ...
    FROM grants
    ORDER BY created_at DESC
    LIMIT 50
""")
```

### Researcher через ORM
```python
# Исследования
investigations = db.get_all_research(limit=100)

# Статистика
stats = db.get_research_statistics()
```

---

## 🔄 Session State

### Используемые ключи:
```python
st.session_state.agent_results = {}  # Результаты работы агентов
st.session_state.selected_research_id = None  # Выбранное исследование
st.session_state.selected_anketa_id = None  # Выбранная анкета
st.session_state.selected_research_export = None  # Экспорт исследования
```

---

## 📦 Зависимости

### Обязательные:
```python
streamlit>=1.25.0
pandas
plotly
```

### Модули GrantService:
```python
# Database
from data.database import GrantServiceDatabase
from utils.database import AdminDatabase

# UI Components
from utils.ui_helpers import render_page_header, render_metric_cards, render_tabs
from utils.agent_components import render_prompt_management

# Logger
from utils.logger import setup_logger
```

### Опциональные (для работы агентов):
```python
from agents.writer_agent import WriterAgent
from agents.researcher_agent import ResearcherAgent
from services.perplexity_service import PerplexityService
from data.database.prompts import get_prompts_by_agent, update_prompt
```

---

## 🧪 Тестирование

### Локальный запуск:
```bash
streamlit run "web-admin/pages/🤖_Агенты.py"
```

### Проверка компиляции:
```bash
python -m py_compile "web-admin/pages/🤖_Агенты.py"
```

### Тестовые сценарии:

#### 1. Проверка статистики Interviewer
- Открыть TAB "Interviewer"
- Проверить метрики: всего, завершено, прогресс, длительность
- Убедиться что промпты загружаются

#### 2. Проверка фильтров Researcher
- Открыть TAB "Researcher" -> SUB-TAB "Исследования"
- Применить фильтр по статусу = "completed"
- Применить фильтр по пользователю
- Убедиться что количество найденных исследований изменилось

#### 3. Проверка аналитики Researcher
- Открыть TAB "Researcher" -> SUB-TAB "Аналитика расходов"
- Проверить отображение баланса аккаунта
- Проверить API Requests по моделям
- Проверить Input Tokens статистику

#### 4. Проверка текстов Writer
- Открыть TAB "Writer" -> SUB-TAB "Тексты"
- Применить фильтр по статусу = "completed"
- Изменить лимит записей на 10
- Убедиться что отображается нужное количество

---

## 🚧 Known Issues

### 1. Researcher - Аналитика
**Проблема:** Графики расходов - заглушки
**Причина:** Требуется доработка Plotly интеграции
**Решение:** TODO в следующем спринте

### 2. Writer - Действия с текстами
**Проблема:** Кнопки "Просмотр", "Экспорт", "Редактировать" - заглушки
**Причина:** Требуется реализация работы с полным текстом
**Решение:** TODO в следующем спринте

### 3. Экспорт исследований
**Проблема:** Кнопка "Экспорт" не работает
**Причина:** Логика экспорта не перенесена из архивного файла
**Решение:** Портировать из `🔬_Исследования_исследователя.py`

---

## 🔐 Безопасность

### Аутентификация:
```python
from utils.auth import is_user_authorized
if not is_user_authorized():
    st.error("⛔ Не авторизован")
    st.stop()
```

### Доступ к БД:
- Все запросы через ORM или prepared statements
- Нет прямого SQL injection риска
- Используется read-only для просмотра данных

---

## 📝 Добавление нового агента

### 1. Добавить конфигурацию:
```python
AGENT_INFO['new_agent'] = {
    'name': 'New Agent',
    'emoji': '🆕',
    'description': 'Description',
    'status': 'active',
    'table': 'new_agent_table',
    'future': 'Future features'
}
```

### 2. Добавить функцию статистики:
```python
def render_new_agent_tab():
    st.markdown("### 🆕 New Agent")
    stats = get_agent_statistics('new_agent', db)
    # ... render metrics
    render_prompt_management('new_agent')
```

### 3. Добавить таб:
```python
agent_tabs = [..., "New Agent"]
agent_icons = [..., "🆕"]

# В main():
tab6 = st.tabs([...])
with tab6:
    render_new_agent_tab()
```

---

## 📚 Полезные ссылки

- [Streamlit Docs](https://docs.streamlit.io)
- [Plotly Python](https://plotly.com/python/)
- [Architecture Doc](../../doc/ARCHITECTURE.md)
- [Integration Report](../../doc/AGENTS_PAGE_INTEGRATION_REPORT.md)

---

## 👤 Контакты

**Вопросы по коду:**
- Создать issue в репозитории
- Написать в Telegram: @otinoff

**Баги:**
- Использовать систему логирования
- Проверить `web-admin/logs/agents_page.log`

---

**Версия:** 3.0.0
**Последнее обновление:** 2025-10-03
**Статус:** ✅ Production Ready
