# План реализации настоящего E2E теста для агентов
**Дата**: 2025-10-06
**Цель**: Создать тест, который вызывает РЕАЛЬНЫЕ агенты с РЕАЛЬНЫМИ LLM

---

## 🎯 Что такое НАСТОЯЩИЙ E2E тест

### Отличия от текущих тестов:

| Аспект | Текущие тесты (Fake) | Настоящий E2E |
|--------|---------------------|---------------|
| Данные | Hardcoded в тесте | Генерируются LLM |
| Агенты | Моки (fake results) | Реальные классы |
| LLM вызовы | НЕТ | ДА (GigaChat/Claude) |
| Время выполнения | <3 сек | 30-60 сек |
| Результат | Предсказуемый | Варьируется |
| Стоимость | $0 | ~$0.50 за запуск |

---

## 📊 Полный цикл E2E теста

### Шаг 1: Подготовка данных (Hardcoded ответы)
```python
# Реальные ответы на 24 вопроса анкеты
GRANT_ANSWERS = {
    "project_name": "ТехноЦентр Кемерово - Инновационное образование для молодежи",
    "project_goal": "Создание современного образовательного центра для развития IT-компетенций молодежи Кузбасса",
    "target_audience": "Школьники и студенты 14-25 лет, интересующиеся программированием, робототехникой и 3D-технологиями",
    "project_duration": "12 месяцев",
    "budget": "2500000",
    "expected_results": [
        "Обучение 250+ участников",
        "Создание 15+ технологических проектов",
        "Трудоустройство 40% выпускников",
        "Открытие 3 филиалов в Кемеровской области"
    ],
    "innovation": "Применение методики проектного обучения с использованием VR/AR технологий",
    "social_impact": "Снижение молодежной безработицы на 15%, развитие IT-экосистемы региона",
    "sustainability": "Коммерческие курсы, корпоративное обучение, аренда пространства для хакатонов",
    "team_experience": "Команда из 7 человек с опытом в образовании и IT от 5 до 20 лет",
    # ... остальные 16 полей
}
```

### Шаг 2: Вызов Interviewer Agent
```python
from agents.interviewer_agent import InterviewerAgent

# Создаем агента с реальным DB
interviewer = InterviewerAgent(db)

# Создаем сессию и сохраняем ответы
session_id = interviewer.start_interview(telegram_id=999999999)

for question_id, answer in GRANT_ANSWERS.items():
    interviewer.save_answer(session_id, question_id, answer)

interviewer.complete_interview(session_id)
```

### Шаг 3: Вызов Auditor Agent (РЕАЛЬНЫЙ LLM)
```python
from agents.auditor_agent import AuditorAgent

auditor = AuditorAgent(db)

# ✅ ВАЖНО: Вызывает НАСТОЯЩИЙ GigaChat/Claude
audit_result = auditor.analyze_project(session_id)

# Результат:
# {
#   'approval_status': 'approved',
#   'average_score': 8.5,
#   'strengths': ['Четкая целевая аудитория', 'Реалистичный бюджет', ...],
#   'weaknesses': ['Недостаточно метрик оценки', ...],
#   'recommendations': ['Добавить KPI для каждой задачи', ...]
# }
```

### Шаг 4: Вызов Planner Agent (РЕАЛЬНЫЙ LLM)
```python
from agents.planner_agent import PlannerAgent

planner = PlannerAgent(db)

# ✅ ВАЖНО: Вызывает НАСТОЯЩИЙ GigaChat/Claude
plan = planner.create_structure(session_id, audit_result)

# Результат:
# {
#   'sections': [
#     {'name': 'Актуальность', 'word_count': 800, 'key_points': [...]},
#     {'name': 'Цели и задачи', 'word_count': 600, ...},
#     {'name': 'Методология', 'word_count': 1200, ...},
#     # ... 8 секций
#   ],
#   'total_word_count': 6500
# }
```

### Шаг 5: Вызов Researcher Agent (Perplexity API)
```python
from agents.researcher_agent import ResearcherAgent

researcher = ResearcherAgent(db)

# ✅ ВАЖНО: Реальный поиск через Perplexity
research_data = researcher.find_similar_grants(session_id)

# Результат:
# {
#   'similar_grants': [
#     {'title': 'IT-лаборатория Томск', 'amount': 3000000, 'success': True},
#     {'title': 'Технопарк Новосибирск', 'amount': 5000000, ...},
#   ],
#   'grant_funds': [
#     {'name': 'Фонд президентских грантов', 'max_amount': 10000000, 'requirements': [...]},
#   ],
#   'statistics': {'average_approval_rate': 0.35, ...}
# }
```

### Шаг 6: Вызов Writer Agent (РЕАЛЬНЫЙ LLM генерирует текст)
```python
from agents.writer_agent import WriterAgent

writer = WriterAgent(db, llm_provider='gigachat')  # или 'claude_code'

# ✅ ВАЖНО: НАСТОЯЩАЯ генерация текста через LLM
grant = writer.write_grant(
    session_id=session_id,
    structure=plan,
    research=research_data,
    target_fund='Фонд президентских грантов'
)

# Результат:
# {
#   'grant_id': 'GRANT_12345',
#   'grant_title': 'ТехноЦентр Кемерово - Инновационное образование для молодежи',
#   'grant_content': '# ГРАНТОВАЯ ЗАЯВКА\n\n## 1. АКТУАЛЬНОСТЬ ПРОЕКТА\n\nВ условиях... [6500+ слов]',
#   'quality_score': 9.2,
#   'word_count': 6834,
#   'tokens_used': 12450,
#   'cost': 0.45  # USD
# }
```

### Шаг 7: Проверка результата
```python
# Проверяем что грант создан
assert grant['grant_id'] is not None
assert len(grant['grant_content']) > 5000, "Грант должен быть полноценным (5000+ символов)"
assert grant['quality_score'] >= 8.0, "Качество должно быть высоким"

# Проверяем структуру
assert '## 1. АКТУАЛЬНОСТЬ ПРОЕКТА' in grant['grant_content']
assert '## 2. ЦЕЛИ И ЗАДАЧИ' in grant['grant_content']
assert '## 3. МЕТОДОЛОГИЯ' in grant['grant_content']
assert 'Фонд президентских грантов' in grant['grant_content']

# Проверяем сохранение в БД
saved_grant = db.execute_query(
    "SELECT * FROM grants WHERE grant_id = %s",
    (grant['grant_id'],)
)
assert len(saved_grant) == 1
assert saved_grant[0]['status'] == 'completed'
```

---

## 🔧 Что нужно доработать для E2E теста

### 1. Агенты должны поддерживать LLM клиенты
```python
# agents/writer_agent.py
class WriterAgent:
    def __init__(self, db, llm_client=None):
        self.db = db
        self.llm_client = llm_client or self._create_default_llm()

    def write_grant(self, session_id, structure, research):
        # Формируем промпт
        prompt = self._build_prompt(session_id, structure, research)

        # Вызываем LLM
        response = self.llm_client.generate(
            prompt=prompt,
            max_tokens=8000,
            temperature=0.7
        )

        return response
```

### 2. Промпты должны быть настраиваемыми
```python
# agents/prompts/writer_grant_template.txt
Ты - эксперт по написанию грантовых заявок для {fund_name}.

КОНТЕКСТ ПРОЕКТА:
{project_context}

СТРУКТУРА ЗАЯВКИ:
{structure}

ИССЛЕДОВАНИЕ:
{research_data}

ЗАДАНИЕ:
Напиши полноценную грантовую заявку на {word_count} слов, следуя структуре выше.
Используй профессиональный язык, конкретные цифры, ссылайся на исследование.

ТРЕБОВАНИЯ:
- Формат: Markdown
- Объем: {word_count}±10% слов
- Стиль: Официально-деловой
- Фокус: Социальная значимость, инновационность, устойчивость
```

### 3. Создать систему управления промптами в БД
```sql
-- Таблица для хранения промптов
CREATE TABLE agent_prompts (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,  -- 'writer', 'auditor', etc.
    prompt_type VARCHAR(50) NOT NULL,  -- 'grant_template', 'audit_template', etc.
    prompt_text TEXT NOT NULL,
    variables JSONB,  -- {'fund_name': 'string', 'word_count': 'int'}
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индекс для быстрого поиска
CREATE INDEX idx_agent_prompts_active ON agent_prompts(agent_name, prompt_type, is_active);
```

---

## 🎨 UI для редактирования промптов (web-admin)

### Страница "🤖 Агенты" → Вкладка каждого агента

#### Пример для Writer Agent:

```python
# web-admin/pages/🤖_Агенты.py

def render_writer_prompts():
    """Раздел редактирования промптов Writer Agent"""

    st.markdown("### 📝 Промпты Writer Agent")

    # Получить активные промпты
    prompts = execute_query("""
        SELECT id, prompt_type, prompt_text, variables, version
        FROM agent_prompts
        WHERE agent_name = 'writer' AND is_active = TRUE
        ORDER BY prompt_type
    """)

    for prompt in prompts:
        with st.expander(f"📄 {prompt['prompt_type']} (v{prompt['version']})"):
            # Показать переменные
            if prompt['variables']:
                st.json(prompt['variables'])

            # Редактор промпта
            new_text = st.text_area(
                "Текст промпта:",
                value=prompt['prompt_text'],
                height=300,
                key=f"prompt_{prompt['id']}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("💾 Сохранить", key=f"save_{prompt['id']}"):
                    execute_update("""
                        UPDATE agent_prompts
                        SET prompt_text = %s,
                            version = version + 1,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (new_text, prompt['id']))
                    st.success("✅ Промпт обновлен!")
                    st.rerun()

            with col2:
                if st.button("🧪 Тестировать", key=f"test_{prompt['id']}"):
                    # Показать preview с подстановкой переменных
                    st.code(new_text.format(
                        fund_name="Фонд президентских грантов",
                        word_count=6500,
                        # ... остальные переменные
                    ))

            with col3:
                if st.button("↩️ Откатить", key=f"rollback_{prompt['id']}"):
                    # Откатить к предыдущей версии
                    pass
```

---

## 📦 Файлы для создания

### 1. Тест: `tests/integration/test_real_e2e_agents.py`
```python
@pytest.mark.integration
@pytest.mark.real_llm  # Требует API ключи
@pytest.mark.expensive  # Стоит денег
class TestRealE2EAgents:
    """Настоящий E2E тест с реальными вызовами LLM"""

    def test_full_grant_cycle_with_real_llm(self, db):
        """Полный цикл создания гранта через реальные агенты"""
        # ... код выше
```

### 2. Промпты: `agents/prompts/`
```
agents/prompts/
├── writer/
│   ├── grant_presidential_fund.txt
│   ├── grant_youth_fund.txt
│   └── grant_international.txt
├── auditor/
│   └── project_audit_template.txt
├── planner/
│   └── structure_template.txt
└── README.md
```

### 3. UI: Обновить `web-admin/pages/🤖_Агенты.py`
- Добавить раздел "📝 Промпты" для каждого агента
- Редактор с подсветкой синтаксиса
- Версионирование промптов
- Тестирование промптов

---

## ✅ Checklist реализации

### Phase 1: Подготовка (2-3 часа)
- [ ] Создать таблицу `agent_prompts` в БД
- [ ] Загрузить начальные промпты для всех агентов
- [ ] Обновить классы агентов для работы с промптами из БД

### Phase 2: E2E тест (3-4 часа)
- [ ] Создать `test_real_e2e_agents.py`
- [ ] Написать hardcoded ответы (24 вопроса)
- [ ] Реализовать вызов всех 5 агентов по цепочке
- [ ] Добавить проверки результата
- [ ] Запустить тест (потребуется API ключ GigaChat)

### Phase 3: UI для промптов (3-4 часа)
- [ ] Добавить раздел "Промпты" на страницу Агентов
- [ ] Реализовать редактор промптов
- [ ] Добавить preview и тестирование
- [ ] Версионирование промптов

### Phase 4: Тестирование (2 часа)
- [ ] Запустить E2E тест локально
- [ ] Проверить что грант генерируется корректно
- [ ] Оценить качество через UI
- [ ] Сохранить примеры грантов

---

## 💰 Стоимость E2E теста

### GigaChat:
- Auditor: ~500 tokens = $0.01
- Planner: ~800 tokens = $0.02
- Writer: ~8000 tokens = $0.20
- **Total: ~$0.23 за тест**

### Claude Code (если используем):
- Auditor: ~600 tokens = $0.03
- Planner: ~1000 tokens = $0.05
- Writer: ~10000 tokens = $0.50
- **Total: ~$0.58 за тест**

### Рекомендация:
Запускать E2E тесты **вручную** перед деплоем, не в CI/CD.

---

## 🎯 Ожидаемый результат

После реализации получим:
1. ✅ **Настоящий E2E тест** - реальные агенты, реальные LLM
2. ✅ **Реальные гранты** - качественный текст для фонда президентских грантов
3. ✅ **UI для промптов** - удобное редактирование без кода
4. ✅ **Версионирование** - можно откатить изменения
5. ✅ **Тестирование** - проверка промптов перед применением

---

**Следующий шаг**: Создать PR с этим планом и начать реализацию Phase 1.
