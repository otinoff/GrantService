# План: Trainer Agent - Агент-тестировщик функциональности

**Дата создания:** 2025-10-17
**Статус:** 📋 ПЛАНИРОВАНИЕ
**Приоритет:** 🔥 ВЫСОКИЙ

---

## Концепция

**Trainer Agent** - внутренний системный агент для тестирования ФУНКЦИОНАЛЬНОСТИ других агентов.

### Ответственность:

✅ **Что делает Trainer:**
- Тестирует запуск агентов (нет критических ошибок)
- Проверяет интеграции (Expert Agent, Database, LLM)
- Валидирует результаты (все поля заполнены)
- Измеряет производительность (время выполнения)
- Генерирует тестовые данные (анкеты, кейсы)

❌ **Что НЕ делает Trainer:**
- Не оценивает СОДЕРЖАНИЕ грантов (это Reviewer Agent)
- Не пишет гранты (это Writer Agent)
- Не исследует данные (это Researcher Agent)

---

## Архитектура

### Расположение в проекте:

```
agents/
├── writer_agent_v2.py       # Пишет гранты
├── researcher_agent_v2.py   # Исследует данные
├── reviewer_agent.py        # Оценивает содержание
├── interviewer_agent.py     # Проводит интервью
├── expert_agent/            # База знаний ФПГ
│   └── expert_agent.py
└── trainer_agent/           # ← НОВЫЙ
    ├── __init__.py
    ├── trainer_agent.py     # Основной класс
    ├── test_cases/          # Тестовые данные
    │   ├── writer_tests.json
    │   ├── researcher_tests.json
    │   └── general_anketas.json
    └── reports/             # Отчеты о тестах
        └── 2025-10-17_writer_test.md
```

### Класс TrainerAgent:

```python
from base_agent import BaseAgent
from expert_agent import ExpertAgent
import time
import json

class TrainerAgent(BaseAgent):
    """
    Агент-тренировщик для тестирования функциональности других агентов

    Версия: 1.0 (MVP)
    """

    def __init__(self, db):
        super().__init__("trainer", db)
        self.expert_agent = None  # Опционально для проверки интеграций

    # ========================================
    # ОСНОВНЫЕ МЕТОДЫ ТЕСТИРОВАНИЯ
    # ========================================

    def test_writer_functionality(self, test_case: Dict = None) -> Dict:
        """
        Тестирует функциональность Writer Agent V2

        Args:
            test_case: Тестовый кейс или None для генерации случайного

        Returns:
            {
                'status': 'passed' | 'failed',
                'agent': 'writer_v2',
                'test_name': 'basic_functionality',
                'execution_time': 125.3,
                'errors': [],
                'warnings': [],
                'checks': {
                    'can_initialize': True,
                    'has_expert_agent': True,
                    'can_generate_grant': True,
                    'result_is_valid': True,
                    'saved_to_db': True,
                    'execution_time_ok': True
                },
                'checks_passed': 6,
                'checks_total': 6,
                'timestamp': '2025-10-17 13:40:00'
            }
        """

    def test_researcher_functionality(self, test_queries: List[str] = None) -> Dict:
        """Тестирует функциональность Researcher Agent"""

    def test_all_agents(self) -> Dict:
        """Запускает тесты для всех агентов"""

    # ========================================
    # ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ
    # ========================================

    def generate_test_anketa(self,
                            project_type: str = "sport",
                            difficulty: str = "medium") -> Dict:
        """
        Генерирует тестовую анкету для проверки агентов

        Args:
            project_type: "sport", "education", "culture", "social"
            difficulty: "easy", "medium", "hard"

        Returns:
            Dict с полями анкеты
        """

    def generate_test_research_results(self, anketa: Dict) -> Dict:
        """Генерирует фейковые research_results для теста Writer"""

    # ========================================
    # ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ
    # ========================================

    def validate_writer_result(self, result: Dict) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность результата Writer Agent

        Checks:
        - status == 'success'
        - application содержит все 9 разделов
        - quality_score присутствует
        - citations > 0
        - tables > 0

        Returns:
            (is_valid, errors)
        """

    def validate_researcher_result(self, result: Dict) -> Tuple[bool, List[str]]:
        """Проверяет валидность результата Researcher"""

    # ========================================
    # ОТЧЕТЫ И ЛОГИРОВАНИЕ
    # ========================================

    def save_test_report(self,
                        agent_name: str,
                        results: Dict,
                        format: str = "markdown") -> str:
        """
        Сохраняет отчет о тестировании

        Args:
            agent_name: Имя протестированного агента
            results: Результаты тестов
            format: "markdown" или "json"

        Returns:
            Путь к сохраненному отчету
        """

    def get_test_history(self,
                        agent_name: str = None,
                        limit: int = 10) -> List[Dict]:
        """Получает историю тестов из БД"""

    # ========================================
    # УТИЛИТЫ
    # ========================================

    def measure_execution_time(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Измеряет время выполнения функции"""
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return result, duration
```

---

## База данных

### Новая таблица: trainer_test_results

```sql
CREATE TABLE IF NOT EXISTS trainer_test_results (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,  -- TR-20251017-001
    agent_name VARCHAR(50) NOT NULL,       -- writer_v2, researcher_v2
    test_type VARCHAR(50) NOT NULL,        -- functionality, integration
    status VARCHAR(20) NOT NULL,           -- passed, failed, warning
    execution_time FLOAT,                  -- секунды
    checks_passed INTEGER,
    checks_total INTEGER,
    errors TEXT[],                         -- массив ошибок
    warnings TEXT[],                       -- массив предупреждений
    test_data JSONB,                       -- входные данные теста
    result_data JSONB,                     -- результаты агента
    metadata JSONB,                        -- доп. информация
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_trainer_agent ON trainer_test_results(agent_name);
CREATE INDEX idx_trainer_status ON trainer_test_results(status);
CREATE INDEX idx_trainer_created ON trainer_test_results(created_at DESC);
```

---

## Интеграции

### 1. Backend API

```python
# В FastAPI или Flask
from trainer_agent import TrainerAgent

@app.post("/api/test/writer")
async def test_writer_agent():
    """Endpoint для тестирования Writer Agent"""
    trainer = TrainerAgent(db)
    results = trainer.test_writer_functionality()
    return {
        "status": results['status'],
        "checks_passed": results['checks_passed'],
        "checks_total": results['checks_total'],
        "execution_time": results['execution_time'],
        "report_url": f"/api/reports/{results['test_id']}"
    }

@app.get("/api/test/history/{agent_name}")
async def get_test_history(agent_name: str):
    """История тестов агента"""
    trainer = TrainerAgent(db)
    history = trainer.get_test_history(agent_name, limit=20)
    return {"history": history}
```

### 2. Web Admin (Streamlit)

```python
# В web-admin/pages/Тестирование.py
import streamlit as st
from trainer_agent import TrainerAgent

st.title("🧪 Тестирование Агентов")

# Выбор агента
agent = st.selectbox("Агент:", ["Writer V2", "Researcher V2", "Reviewer"])

# Кнопка запуска
if st.button(f"▶️ Протестировать {agent}"):
    trainer = TrainerAgent(db)

    with st.spinner(f"Тестирование {agent}..."):
        if agent == "Writer V2":
            results = trainer.test_writer_functionality()
        elif agent == "Researcher V2":
            results = trainer.test_researcher_functionality()

    # Результаты
    if results['status'] == 'passed':
        st.success(f"✅ Все тесты пройдены ({results['checks_passed']}/{results['checks_total']})")
    else:
        st.error(f"❌ Тесты провалены")

    # Детали
    st.json(results)

    # История
    st.subheader("История тестов")
    history = trainer.get_test_history(agent_name=agent.lower().replace(" ", "_"))
    st.dataframe(history)
```

### 3. CI/CD Pipeline

```yaml
# .github/workflows/test-agents.yml
name: Test AI Agents

on: [push, pull_request]

jobs:
  test-agents:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Test Writer Agent
      run: |
        python -c "
        from trainer_agent import TrainerAgent
        from data.database.models import Database

        db = Database()
        trainer = TrainerAgent(db)

        results = trainer.test_writer_functionality()
        assert results['status'] == 'passed', f'Writer test failed: {results}'
        print(f'✅ Writer tests passed: {results[\"checks_passed\"]}/{results[\"checks_total\"]}')
        "

    - name: Test Researcher Agent
      run: |
        python -c "
        from trainer_agent import TrainerAgent
        trainer = TrainerAgent()
        results = trainer.test_researcher_functionality()
        assert results['status'] == 'passed'
        "
```

---

## Этапы реализации

### Фаза 1: MVP (1-2 дня) 🔥 ПРИОРИТЕТ

**Цель:** Минимально работающий Trainer для Writer Agent

✅ Задачи:
1. Создать `trainer_agent/trainer_agent.py` с базовым классом
2. Реализовать `test_writer_functionality()` с 6 проверками
3. Реализовать `generate_test_anketa()` для тестовых данных
4. Реализовать `validate_writer_result()`
5. Создать миграцию БД для `trainer_test_results`
6. Написать базовый тест: запуск → проверка → отчет

**Результат:** Можно запустить `trainer.test_writer_functionality()` и получить отчет

---

### Фаза 2: Интеграция с системой (2-3 дня)

✅ Задачи:
1. Создать FastAPI endpoint `/api/test/writer`
2. Добавить страницу в Web Admin "Тестирование"
3. Реализовать сохранение в БД
4. Создать dashboard с историей тестов
5. Добавить уведомления при провале тестов

**Результат:** Админы могут тестировать через веб-интерфейс

---

### Фаза 3: Расширение (1 неделя)

✅ Задачи:
1. Добавить тесты для Researcher Agent
2. Добавить тесты для Reviewer Agent
3. Реализовать `test_all_agents()`
4. Интегрировать в CI/CD
5. Создать автоматические ночные тесты

**Результат:** Все агенты тестируются автоматически

---

### Фаза 4: Продвинутые возможности (будущее)

💡 Идеи:
- Регрессионное тестирование (сравнение с предыдущими версиями)
- A/B тестирование промптов
- Автоматическое обучение на ошибках
- Synthetic data generation для тестов
- Performance benchmarking
- Stress testing (100+ одновременных запросов)

---

## Метрики успеха

### MVP считается успешным если:
- ✅ Trainer Agent запускается без ошибок
- ✅ test_writer_functionality() проходит на тестовых данных
- ✅ Результаты сохраняются в БД
- ✅ Генерируется читаемый отчет

### Полная система считается успешной если:
- ✅ Все агенты тестируются автоматически
- ✅ Тесты в CI/CD проходят стабильно
- ✅ Админы используют веб-интерфейс для тестирования
- ✅ История тестов помогает отслеживать регрессии

---

## Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| LLM недоступен во время теста | Средняя | Mock LLM для тестов |
| БД недоступна | Низкая | In-memory SQLite для тестов |
| Тест слишком долгий (> 5 мин) | Средняя | Timeout, параллельные тесты |
| Флаки тесты (нестабильные) | Высокая | Retry логика, фиксированные seed |

---

## Связанные документы

- [Writer Agent V2](../../agents/writer_agent_v2.py)
- [Expert Agent](../../expert_agent/expert_agent.py)
- [Reviewer Agent](../../agents/reviewer_agent.py)
- [Database Schema](../../database/migrations/)

---

**Следующий шаг:** Создать MVP Trainer Agent (Фаза 1)

---

*📝 План создан: 2025-10-17 13:40*
