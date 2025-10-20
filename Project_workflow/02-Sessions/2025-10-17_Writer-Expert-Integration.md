# Сессия: Интеграция Writer Agent + Expert Agent + План Trainer Agent

**Дата:** 2025-10-17
**Токенов использовано:** ~120k / 200k
**Статус:** 🔄 В ПРОЦЕССЕ

---

## 📋 Выполнено в этой сессии

### 1. Исправление документации (n8n → реальная архитектура) ✅

**Проблема:** Документация упоминала n8n, которого нет в проекте

**Решение:**
- ✅ Удалены упоминания n8n из `STATUS.md`
- ✅ Удалены упоминания n8n из `ARCHITECTURE.md` (v1.0.3)
- ✅ Перемещена папка `n8n-workflows/` в `doc/archive/`
- ✅ Создан `ARCHITECTURE_CLEANUP_2025-10-17.md` с объяснением
- ✅ Обновлен `CHANGELOG.md` (v1.0.8)

**Реальная архитектура:**
- Systemd services для автоматизации
- Python API для взаимодействия агентов
- Expert Agent как центральная база знаний

---

### 2. Интеграция Writer Agent V2 + Expert Agent ✅

**Цель:** Writer Agent использует векторную базу знаний ФПГ при генерации грантов

**Изменения в `agents/writer_agent_v2.py`:**

```python
# 1. Инициализация Expert Agent
def __init__(self, db, llm_provider):
    # ...
    self.expert_agent = ExpertAgent()  # НОВОЕ
    logger.info("✅ Writer V2: Expert Agent подключен")

# 2. Метод получения требований ФПГ
def _get_fpg_requirements(self, section: str = "") -> List[Dict]:
    """Получить требования ФПГ из векторной БД"""
    questions = {
        "problem": "Какие требования к разделу 'Описание проблемы'?",
        "goal": "Какие требования к формулировке цели?",
        "general": "Какие общие требования к заявке ФПГ?"
    }

    results = self.expert_agent.query_knowledge(
        question=questions.get(section, questions["general"]),
        fund="fpg",
        top_k=3,
        min_score=0.4
    )
    return results

# 3. Использование в промптах Stage 1
async def _stage1_planning_async(self, ...):
    # Получаем требования от Expert Agent
    fpg_requirements = self._get_fpg_requirements("general")
    fpg_requirements_problem = self._get_fpg_requirements("problem")

    # Добавляем в промпт
    planning_prompt = f"""
    ТРЕБОВАНИЯ ФПГ (из официальной базы знаний):
    {fpg_knowledge}

    КОНТЕКСТ ПРОЕКТА:
    ...
    """
```

**Результат:**
- Writer Agent теперь знает требования ФПГ из векторной БД
- При планировании (Stage 1) запрашивает релевантные требования
- Промпты обогащаются актуальными знаниями

---

### 3. План создания Trainer Agent 📋

**Архитектурное решение:**

✅ **Trainer Agent = внутренний системный агент** (как Expert Agent)
✅ **НЕ Claude Code agent** из `.claude/agents/`
✅ **Расположение:** `agents/trainer_agent/trainer_agent.py`

**Разделение ответственности:**

```
┌─────────────────────────────────────────────────────┐
│  Trainer Agent                                      │
│  ├─ Тестирует ФУНКЦИОНАЛЬНОСТЬ                     │
│  ├─ Проверяет запуск агентов                       │
│  ├─ Проверяет интеграции (Expert, DB)             │
│  └─ Проверяет валидность результата                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Reviewer Agent (уже существует)                   │
│  ├─ Проверяет СОДЕРЖАНИЕ грантов                   │
│  ├─ Оценивает качество текста                      │
│  └─ Дает рекомендации по улучшению                 │
└─────────────────────────────────────────────────────┘
```

**Минимальная версия Trainer Agent (MVP):**

```python
class TrainerAgent(BaseAgent):
    """Агент для тестирования функциональности других агентов"""

    def __init__(self, db):
        super().__init__("trainer", db)

    # ОСНОВНАЯ ФУНКЦИЯ
    def test_writer_functionality(self, test_case: Dict) -> Dict:
        """
        Тестирует функциональность Writer Agent

        Проверки:
        1. ✅ Запуск без ошибок
        2. ✅ Интеграция с Expert Agent
        3. ✅ Возврат валидного результата
        4. ✅ Все обязательные поля заполнены
        5. ✅ Сохранение в БД
        6. ✅ Время < 3 минут

        Returns:
            {
                'status': 'passed' | 'failed',
                'errors': [],
                'warnings': [],
                'execution_time': 120.5,
                'checks_passed': 6,
                'checks_total': 6
            }
        """

    # ВСПОМОГАТЕЛЬНЫЕ
    def generate_test_anketa(self, project_type: str) -> Dict:
        """Генерирует тестовую анкету"""

    def validate_result(self, result: Dict) -> bool:
        """Проверяет валидность результата агента"""

    def save_test_report(self, agent_name: str, results: Dict):
        """Сохраняет отчет о тестировании"""
```

**Интеграция с системой:**

1. **Backend API** (для админки):
```python
@app.post("/api/test/writer")
async def test_writer():
    trainer = TrainerAgent(db)
    results = trainer.test_writer_functionality(test_case)
    return results
```

2. **Web Admin кнопка:**
```python
# streamlit
if st.button("🧪 Протестировать Writer Agent"):
    trainer = TrainerAgent(db)
    with st.spinner("Тестирование..."):
        results = trainer.test_writer_functionality(test_case)
    st.json(results)
```

3. **CI/CD проверки:**
```bash
# В GitHub Actions
python -c "from trainer_agent import TrainerAgent; trainer = TrainerAgent(); assert trainer.test_all_agents()['status'] == 'passed'"
```

---

## 🎯 Архитектурные инсайты

### 1. Expert Agent как Knowledge Hub

**Концепция:**
- Expert Agent = центральная база знаний о требованиях ФПГ
- Все агенты (Writer, Researcher, Reviewer) обращаются к нему
- Векторный поиск (Qdrant) для семантического поиска
- PostgreSQL для структурированных данных

**Преимущества:**
- Единый источник правды о требованиях
- Легко обновлять знания (один раз для всех)
- Семантический поиск по контексту запроса

### 2. Разделение Trainer vs Reviewer

**Trainer Agent:**
- Функциональные тесты (запуск, ошибки, интеграции)
- Быстрые проверки (< 1 минуты)
- Автоматические в CI/CD

**Reviewer Agent:**
- Оценка содержания грантов
- Глубокий анализ качества текста
- Рекомендации по улучшению
- Медленнее (требует LLM анализа)

### 3. Системные агенты vs Claude Code агенты

**Внутренние (системные):**
- `agents/writer_agent_v2.py`
- `agents/researcher_agent_v2.py`
- `agents/reviewer_agent.py`
- `expert_agent/expert_agent.py` ← существует
- `trainer_agent/trainer_agent.py` ← планируется

**Внешние (Claude Code):**
- `.claude/agents/test-engineer.md` ← для разработки
- `.claude/agents/grant-architect.md` ← для архитектуры
- `.claude/agents/deployment-manager.md` ← для деплоя

**Разница:**
- Системные = часть продакшн кода, вызываются из бэкенда
- Внешние = помощники при разработке (Claude Code CLI)

---

## 📊 Текущий статус Expert Agent

**База знаний:**
- ✅ PostgreSQL: 17 разделов ФПГ
- ✅ Qdrant: 17 векторов (384d, multilingual)
- ✅ Sentence Transformer: paraphrase-multilingual-MiniLM-L12-v2
- ✅ Средняя релевантность: 0.47-0.80 (отлично)

**Примеры запросов (протестировано):**
1. "Какие требования к названию проекта?" → 0.719 релевантность
2. "Как правильно описать целевую аудиторию?" → 0.477 релевантность
3. "Что нужно указать в разделе О проекте?" → 0.730 релевантность

**Источник данных:**
- Файл: `fpg_docs_2025/UNIFIED_KNOWLEDGE_BASE.md` (330KB)
- Разделы: 15 официальных статей с сайта ФПГ
- Загрузчик: `expert_agent/load_fpg_knowledge.py`

---

## 🚀 Следующие шаги

### Немедленные (сегодня):
1. ⏳ Создать `trainer_agent/trainer_agent.py` (MVP)
2. ⏳ Реализовать `test_writer_functionality()`
3. ⏳ Протестировать Writer + Expert интеграцию
4. ⏳ Сохранить результаты тестов

### Краткосрочные (эта неделя):
1. Добавить кнопку в Web Admin для тестирования
2. Создать таблицу `trainer_test_results` в БД
3. Интегрировать Trainer в CI/CD pipeline
4. Написать документацию Trainer Agent

### Среднесрочные (2 недели):
1. Расширить Trainer для Researcher Agent
2. Добавить автоматическое обучение на ошибках
3. Создать dashboard с метриками агентов
4. A/B тестирование разных версий промптов

---

## 💡 Идеи для будущего

### Trainer Agent Evolution:

**Фаза 1 (MVP):** Функциональные тесты
- Запуск, ошибки, валидация

**Фаза 2:** Регрессионное тестирование
- Сравнение с предыдущими версиями
- Детекция деградации качества

**Фаза 3:** Автоматическое обучение
- Анализ ошибок → обновление промптов
- A/B тестирование промптов
- Эволюция агентов на основе метрик

**Фаза 4:** Мета-агент
- Trainer управляет всеми агентами
- Оркестрация обучения
- Автоматическая оптимизация системы

---

## 📁 Файлы созданные/измененные

### Документация:
- `doc/ARCHITECTURE.md` v1.0.3 (удалены n8n)
- `doc/CHANGELOG.md` v1.0.8 (новая версия)
- `doc/archive/ARCHITECTURE_CLEANUP_2025-10-17.md` (объяснение)
- `STATUS.md` (обновлены разделы про интеграцию)

### Код:
- `agents/writer_agent_v2.py` (добавлена интеграция с Expert Agent)
  - Новый метод: `_get_fpg_requirements(section)`
  - Обновлен: `_stage1_planning_async()` с использованием Expert
  - Обновлен: `__init__()` с инициализацией Expert Agent

### Тесты (создан, но с ошибками импорта):
- `test_writer_with_expert.py` (нуждается в доработке)

---

## ⚠️ Известные проблемы

1. **Тестовый скрипт не работает:**
   - ImportError: cannot import Database
   - Нужен правильный импорт: `from data.database.models import Database`

2. **Writer Agent нуждается в GigaChat:**
   - Текущий provider: gigachat
   - Нужна настройка API key для тестов

3. **Trainer Agent еще не создан:**
   - План готов
   - Реализация в следующей сессии

---

## 📊 Метрики прогресса

**Expert Agent:**
- ✅ 100% - База данных создана (PostgreSQL + Qdrant)
- ✅ 100% - Данные загружены (17 разделов ФПГ)
- ✅ 100% - API функционирует
- ✅ 100% - Тесты пройдены (8/8 вопросов)

**Writer + Expert интеграция:**
- ✅ 100% - Метод интеграции добавлен
- ✅ 100% - Промпты обновлены
- ⏳ 50% - Тестирование (скрипт создан, не запущен)

**Trainer Agent:**
- ✅ 100% - Архитектура спланирована
- ✅ 100% - Концепция утверждена
- ⏳ 0% - Код реализован
- ⏳ 0% - Тесты пройдены

**Документация:**
- ✅ 100% - n8n упоминания удалены
- ✅ 100% - Архитектура актуализирована
- ✅ 100% - CHANGELOG обновлен

---

## 🎓 Ключевые обучающие моменты

1. **Документация должна соответствовать реальности:**
   - n8n был в документации, но не в коде
   - Важно регулярно проверять соответствие

2. **Разделение ответственности агентов:**
   - Trainer = функциональность
   - Reviewer = содержание
   - Expert = знания

3. **Системный подход vs скрипты:**
   - Лучше создать агента-тестировщика
   - Чем плодить разовые тестовые скрипты
   - Агент можно вызывать из админки, API, CI/CD

4. **Векторная база знаний - мощный инструмент:**
   - Expert Agent дает контекстуальные знания
   - Семантический поиск лучше чем keyword search
   - Легко обновлять и масштабировать

---

**Продолжение в следующей сессии:**
- Реализация Trainer Agent (MVP)
- Функциональный тест Writer + Expert
- Интеграция с Web Admin

---

*📝 Сессия сохранена: 2025-10-17 13:35*
