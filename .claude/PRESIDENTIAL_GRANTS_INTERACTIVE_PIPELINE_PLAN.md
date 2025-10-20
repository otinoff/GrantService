# План реализации интерактивного pipeline для президентских грантов

**Дата создания**: 2025-10-12
**Автор**: Grant Service Architect Agent
**Статус**: В разработке (локально, БЕЗ коммита в git)

---

## 1. АНАЛИЗ ТЕКУЩЕЙ АРХИТЕКТУРЫ

### 1.1 Существующие агенты

| Агент | Версия | LLM Provider | Статус | Назначение |
|-------|--------|--------------|--------|------------|
| **InterviewerAgent** | v1 | GigaChat | ✅ Работает | Создание вопросов для интервью |
| **AuditorAgent** | v1 | Claude Code | ⚠️ API проблемы | Анализ качества заявки (1-10 баллов) |
| **ResearcherAgent** | v2 | Claude + Perplexity | ✅ Работает | 27 экспертных WebSearch запросов |
| **WriterAgent** | v2 | Claude Opus | ⚠️ API проблемы | Генерация грантовой заявки |
| **ReviewerAgent** | v1 | Claude Sonnet | ⚠️ API проблемы | Финальная оценка готовности |

### 1.2 Проблемы

1. **Claude Code API Server**: OAuth токен истёк на сервере 178.236.17.55:8000
   - `/health` ✅ работает
   - `/models` ✅ работает
   - `/chat` ❌ 500 Internal Server Error
   - **Решение**: Переключить на GigaChat для критических агентов

2. **Аудитор не интегрирован в интервью**: Работает как standalone, а нужен интерактивный аудит

3. **Отсутствует E2E тест для президентских грантов**: Есть тесты для других фондов, но не для ФПГ

4. **WebSearch для фонда**: Нужна специализированная реализация для поиска информации о президентских грантах

---

## 2. ЦЕЛЕВАЯ АРХИТЕКТУРА

### 2.1 Интерактивный Pipeline (4 этапа)

```
┌──────────────────────────────────────────────────────────────────┐
│  ЭТАП 1: INTERACTIVE INTERVIEW + AUDIT (Интервью + Аудит)        │
├──────────────────────────────────────────────────────────────────┤
│  Агент: InterviewerAgent (GigaChat)                              │
│  ├─ Фаза 1.1: Сбор информации (15 вопросов)                      │
│  │   - Проект, цели, задачи, методология                         │
│  │   - География, целевая аудитория, команда                     │
│  │   - Бюджет, партнеры, устойчивость                            │
│  │                                                                │
│  ├─ Фаза 1.2: ИНТЕРАКТИВНЫЙ АУДИТ (AuditorAgent встроен)         │
│  │   - Анализ ответов в реальном времени                         │
│  │   - Оценка по 10 критериям (1-10 баллов)                      │
│  │   - Интерактивные уточняющие вопросы                          │
│  │   - "Ваш бюджет кажется завышенным, объясните статью X"       │
│  │   - "Риски описаны поверхностно, добавьте конкретику"         │
│  │                                                                │
│  └─ Результат:                                                    │
│      - Заполненная анкета (24 поля)                              │
│      - Audit score (1-100 баллов)                                │
│      - Рекомендации по улучшению                                 │
│      - Артефакты: anketa_{project}_audit.md + .pdf               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  ЭТАП 2: RESEARCH + WEBSEARCH (Исследование)                     │
├──────────────────────────────────────────────────────────────────┤
│  Агент: ResearcherAgentV2 (Claude Sonnet + Perplexity)           │
│  ├─ Блок 1: Профильные запросы (10 запросов)                     │
│  │   - "статистика по {тематике} в {регионе}"                    │
│  │   - "успешные кейсы {проекта} в России"                       │
│  │   - "госпрограммы по {направлению}"                           │
│  │                                                                │
│  ├─ Блок 2: Контекстные запросы (10 запросов)                    │
│  │   - "проблемы {целевой аудитории}"                            │
│  │   - "исследования о {теме проекта}"                           │
│  │   - "нормативная база для {проекта}"                          │
│  │                                                                │
│  ├─ Блок 3: Целевые запросы (7 запросов)                         │
│  │   - "индикаторы эффективности {проекта}"                      │
│  │   - "бюджет аналогичных проектов"                             │
│  │   - "партнерские организации в {регионе}"                     │
│  │                                                                │
│  └─ Специализированный запрос:                                   │
│      - "Фонд президентских грантов требования + направления"     │
│      - allowed_domains: ['prezidentskiegranty.ru', 'gov.ru']     │
│      - Извлечение критериев оценки ФПГ                           │
│                                                                  │
│  Результат:                                                       │
│    - 27 блоков research_results (JSONB)                          │
│    - 117+ источников с цитатами                                  │
│    - Артефакты: research_{project}.md + .pdf                     │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  ЭТАП 3: GRANT WRITING (Написание заявки)                        │
├──────────────────────────────────────────────────────────────────┤
│  Агент: WriterAgentV2 (GigaChat - переключен с Claude)           │
│  ├─ Входные данные:                                              │
│  │   - Анкета (24 поля)                                          │
│  │   - Research results (27 блоков)                              │
│  │   - Audit recommendations                                     │
│  │                                                                │
│  ├─ Генерация 9 разделов (форма ФПГ):                            │
│  │   1. Название проекта                                         │
│  │   2. География проекта                                        │
│  │   3. Обоснование актуальности                                 │
│  │   4. Цели и задачи проекта                                    │
│  │   5. Описание проекта (методология)                           │
│  │   6. Календарный план                                         │
│  │   7. Ожидаемые результаты и индикаторы                        │
│  │   8. Бюджет проекта                                           │
│  │   9. Команда и партнеры                                       │
│  │                                                                │
│  ├─ Требования к контенту:                                       │
│  │   - Минимум 10 цитат из research (официальные источники)      │
│  │   - Минимум 2 таблицы (план-график, бюджет)                   │
│  │   - Статистика по региону/теме                                │
│  │   - Ссылки на госпрограммы                                    │
│  │                                                                │
│  └─ Результат:                                                    │
│      - Грантовая заявка 15000-20000 символов                     │
│      - Артефакты: grant_{nomenclature}.md + .pdf                 │
│      - Номенклатура: #AN-YYYYMMDD-username-NNN                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  ЭТАП 4: FINAL REVIEW (Финальная проверка)                       │
├──────────────────────────────────────────────────────────────────┤
│  Агент: ReviewerAgent (GigaChat - переключен с Claude)           │
│  ├─ Оценка по 4 критериям:                                       │
│  │   1. Доказательная база (40%): Цитаты, статистика, источники │
│  │   2. Структура (30%): Полнота разделов, логика                │
│  │   3. Индикаторный матчинг (20%): Соответствие требованиям ФПГ │
│  │   4. Экономика (10%): Обоснованность бюджета                  │
│  │                                                                │
│  ├─ Расчет вероятности одобрения:                                │
│  │   - Weighted score (0-10)                                     │
│  │   - Approval probability (15-50%)                             │
│  │   - Формула: 15 + (score * 4.375)                             │
│  │                                                                │
│  ├─ Финальные рекомендации:                                      │
│  │   - Сильные стороны                                           │
│  │   - Слабые стороны                                            │
│  │   - Приоритетные улучшения                                    │
│  │                                                                │
│  └─ Результат:                                                    │
│      - Review report (MD + PDF)                                  │
│      - Готовность к подаче (yes/no)                              │
│      - Артефакты: review_{nomenclature}.md + .pdf                │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Ключевые изменения

#### 2.2.1 Интеграция Auditor в Interviewer

**ДО** (standalone):
```python
# Интервью
interviewer = InterviewerAgent(db, llm_provider="gigachat")
anketa = await interviewer.conduct_interview(user_id)

# Отдельный аудит (НЕ интерактивный)
auditor = AuditorAgent(db, llm_provider="claude_code")
audit_result = await auditor.audit_application(anketa)
```

**ПОСЛЕ** (интерактивный):
```python
# Интервью с встроенным аудитом
interviewer = InteractiveInterviewerAgent(db, llm_provider="gigachat")
result = await interviewer.conduct_interview_with_audit(user_id)
# result содержит:
# - anketa (24 поля)
# - audit_score (1-100)
# - interactive_feedback (уточняющие вопросы)
# - recommendations (что улучшить)
```

**Механизм**:
1. Пользователь отвечает на 15 базовых вопросов
2. После каждого блока (5 вопросов) → INTERIM AUDIT
3. Агент задаёт уточняющие вопросы:
   - "Ваш бюджет 1.5 млн, но не указаны статьи. Расшифруйте?"
   - "Риски описаны общо. Какие конкретно риски видите?"
4. Финальный аудит после 15 вопросов
5. Сохранение анкеты + audit_score в БД

#### 2.2.2 WebSearch для фонда президентских грантов

**Новый запрос в ResearcherAgentV2**:

```python
# Специализированный запрос №28 (дополнительный)
PRESIDENTIAL_GRANTS_FUND_QUERY = """
Фонд президентских грантов 2025:
- Основные направления финансирования
- Критерии оценки заявок
- Требования к оформлению
- Примеры одобренных проектов

Источники: только официальные (prezidentskiegranty.ru, gov.ru)
"""

# Выполнение через Perplexity WebSearch
result = await websearch_router.websearch(
    query=PRESIDENTIAL_GRANTS_FUND_QUERY,
    allowed_domains=['prezidentskiegranty.ru', 'gov.ru', 'kremlin.ru'],
    max_results=10
)
```

**Извлечение данных**:
- Направления ФПГ (социальная поддержка, культура, спорт и т.д.)
- Критерии оценки (актуальность, новизна, методология и т.д.)
- Индикаторы эффективности
- Примеры успешных заявок

#### 2.2.3 Переключение Writer и Reviewer на GigaChat

**Файл**: `shared/llm/config.py`

```python
# ДО (НЕ РАБОТАЕТ из-за OAuth проблемы)
AGENT_CONFIGS = {
    "writer": {
        "provider": "claude",  # ❌
        "model": "opus",
        "temperature": 0.7,
        "max_tokens": 16000
    },
    "reviewer": {
        "provider": "claude",  # ❌
        "model": "sonnet",
        "temperature": 0.5,
        "max_tokens": 8000
    }
}

# ПОСЛЕ (РАБОТАЕТ)
AGENT_CONFIGS = {
    "writer": {
        "provider": "gigachat",  # ✅
        "model": "GigaChat",
        "temperature": 0.7,
        "max_tokens": 8000  # GigaChat лимит
    },
    "reviewer": {
        "provider": "gigachat",  # ✅
        "model": "GigaChat",
        "temperature": 0.5,
        "max_tokens": 8000
    }
}
```

---

## 3. РЕАЛИЗАЦИЯ

### 3.1 Файлы для создания/модификации

| Файл | Действие | Описание |
|------|----------|----------|
| `agents/interactive_interviewer_agent.py` | 🆕 СОЗДАТЬ | Интерактивный интервьюер с встроенным аудитом |
| `agents/presidential_grants_researcher.py` | 🆕 СОЗДАТЬ | Специализация ResearcherV2 для ФПГ |
| `shared/llm/config.py` | ✏️ ИЗМЕНИТЬ | Переключить writer/reviewer на GigaChat |
| `tests/integration/test_archery_club_fpg_e2e.py` | 🆕 СОЗДАТЬ | E2E тест "Лучные клубы Кемерово" |
| `scripts/generate_archery_grant_local.py` | 🆕 СОЗДАТЬ | Локальный скрипт для запуска pipeline |
| `utils/artifact_saver.py` | 🆕 СОЗДАТЬ | Сохранение MD + PDF артефактов |

### 3.2 Порядок реализации

#### ШАГ 1: Создать InteractiveInterviewerAgent (2-3 часа)

**Файл**: `agents/interactive_interviewer_agent.py`

**Класс**: `InteractiveInterviewerAgent(BaseAgent)`

**Методы**:
```python
async def conduct_interview_with_audit(self, user_id: int) -> Dict[str, Any]:
    """
    Основной метод: интервью + интерактивный аудит

    Returns:
        {
            'anketa': {...},  # 24 поля
            'audit_score': 75,  # 1-100
            'audit_details': {...},  # по 10 критериям
            'recommendations': [...],  # улучшения
            'interactive_feedback': [...]  # уточняющие вопросы
        }
    """

async def _ask_question_block(self, block_num: int, questions: List[str]) -> Dict[str, str]:
    """Блок из 5 вопросов"""

async def _interim_audit(self, partial_answers: Dict[str, str]) -> Dict[str, Any]:
    """Промежуточный аудит после блока"""

async def _ask_clarifying_questions(self, audit_result: Dict[str, Any]) -> Dict[str, str]:
    """Уточняющие вопросы на основе аудита"""

async def _final_audit(self, full_anketa: Dict[str, Any]) -> Dict[str, Any]:
    """Финальный аудит всей анкеты"""
```

**Интеграция AuditorAgent**:
```python
def __init__(self, db, llm_provider: str = "gigachat"):
    super().__init__("interactive_interviewer", db, llm_provider)

    # Встроенный аудитор
    self.auditor = AuditorAgent(db, llm_provider="gigachat")  # Переключен на GigaChat
```

**Flow**:
1. Блок 1 (вопросы 1-5) → Interim Audit → Clarifying Questions
2. Блок 2 (вопросы 6-10) → Interim Audit → Clarifying Questions
3. Блок 3 (вопросы 11-15) → Interim Audit → Clarifying Questions
4. Final Audit → Recommendations → Save to DB

#### ШАГ 2: Создать PresidentialGrantsResearcher (1-2 часа)

**Файл**: `agents/presidential_grants_researcher.py`

**Класс**: `PresidentialGrantsResearcher(ResearcherAgentV2)`

**Дополнительный запрос**:
```python
async def _websearch_fund_requirements(self) -> Dict[str, Any]:
    """
    Запрос №28: Требования ФПГ

    Returns:
        {
            'directions': [...],  # направления финансирования
            'criteria': [...],  # критерии оценки
            'indicators': [...],  # индикаторы эффективности
            'examples': [...]  # успешные заявки
        }
    """

    query = """
    Фонд президентских грантов 2025:
    - Основные направления финансирования
    - Критерии оценки заявок
    - Требования к оформлению
    - Примеры одобренных проектов

    Только официальные источники
    """

    result = await self.websearch_router.websearch(
        query=query,
        allowed_domains=['prezidentskiegranty.ru', 'gov.ru', 'kremlin.ru'],
        max_results=10
    )

    return self._parse_fund_requirements(result)
```

**Переопределение метода**:
```python
async def conduct_research_async(self, anketa_id: str) -> Dict[str, Any]:
    """
    Переопределяем базовый метод:
    27 стандартных запросов + 1 специализированный для ФПГ
    """

    # Вызов базового метода (27 запросов)
    base_result = await super().conduct_research_async(anketa_id)

    # Дополнительный запрос для ФПГ
    fund_data = await self._websearch_fund_requirements()

    # Объединение результатов
    base_result['research_results']['fund_requirements'] = fund_data

    return base_result
```

#### ШАГ 3: Переключить Writer и Reviewer на GigaChat (5 минут)

**Файл**: `shared/llm/config.py`

```python
AGENT_CONFIGS = {
    "interviewer": {
        "provider": "gigachat",  # Уже использует
        "model": "GigaChat",
        "temperature": 0.7,
        "max_tokens": 8000
    },
    "auditor": {
        "provider": "gigachat",  # ✏️ ИЗМЕНИТЬ с claude_code
        "model": "GigaChat",
        "temperature": 0.5,
        "max_tokens": 8000
    },
    "researcher": {
        "provider": "claude",  # Оставляем для LLM
        "model": "sonnet",  # WebSearch через Perplexity
        "temperature": 0.6,
        "max_tokens": 16000
    },
    "writer": {
        "provider": "gigachat",  # ✏️ ИЗМЕНИТЬ с claude
        "model": "GigaChat",
        "temperature": 0.7,
        "max_tokens": 8000
    },
    "reviewer": {
        "provider": "gigachat",  # ✏️ ИЗМЕНИТЬ с claude
        "model": "GigaChat",
        "temperature": 0.5,
        "max_tokens": 8000
    }
}
```

#### ШАГ 4: Создать E2E тест (2-3 часа)

**Файл**: `tests/integration/test_archery_club_fpg_e2e.py`

**Тестовые данные**:
```python
ARCHERY_CLUB_DATA = {
    "telegram_id": 999888777666,
    "username": "archery_kemerovo",
    "first_name": "Иван",
    "last_name": "Петров",
    "email": "ivan@archery-kemerovo.ru",
    "phone": "+79001234567",

    # Проект
    "project_name": "Развитие стрельбы из лука в Кемерово",
    "project_goal": "Создание сети лучных клубов для вовлечения молодёжи в традиционные виды спорта",
    "target_audience": "Молодёжь 14-25 лет, семьи с детьми, любители исторической реконструкции",

    "project_description": """
    Комплексный проект по развитию стрельбы из лука в Кемеровской области:
    1. Открытие 3 лучных клубов в разных районах города
    2. Организация соревнований и мастер-классов
    3. Привлечение 500+ участников в первый год
    4. Сохранение традиций исторической стрельбы из лука
    """,

    "problem_statement": """
    В Кемерово отсутствует инфраструктура для занятий стрельбой из лука.
    Молодёжь не имеет доступа к этому традиционному виду спорта.
    Исторические традиции лучного боя забываются.
    """,

    "budget": "800000",
    "grant_fund": "Фонд президентских грантов",
    "geography": "Кемерово, Кемеровская область"
}
```

**Тест**:
```python
async def test_archery_club_full_pipeline():
    """
    E2E тест: Лучные клубы Кемерово

    Этапы:
    1. Interactive Interview + Audit
    2. Research (27 + 1 запросов)
    3. Grant Writing
    4. Final Review

    Артефакты (MD + PDF):
    - anketa_archery_kemerovo_audit.md
    - research_archery_kemerovo.md
    - grant_AN-20251012-archery_kemerovo-001.md
    - review_AN-20251012-archery_kemerovo-001.md
    """

    # Setup
    db = GrantServiceDatabase()
    artifacts_dir = Path("grants_output/archery_kemerovo")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ЭТАП 1: Interactive Interview + Audit
    logger.info("=" * 80)
    logger.info("ЭТАП 1: INTERACTIVE INTERVIEW + AUDIT")
    logger.info("=" * 80)

    interviewer = InteractiveInterviewerAgent(db, llm_provider="gigachat")
    interview_result = await interviewer.conduct_interview_with_audit(
        user_data=ARCHERY_CLUB_DATA
    )

    anketa = interview_result['anketa']
    audit_score = interview_result['audit_score']

    # Сохранить артефакты
    await save_artifact(
        data=interview_result,
        filename="anketa_archery_kemerovo_audit",
        output_dir=artifacts_dir,
        formats=['md', 'pdf']
    )

    logger.info(f"✅ Анкета создана, audit score: {audit_score}/100")

    # ЭТАП 2: Research
    logger.info("=" * 80)
    logger.info("ЭТАП 2: RESEARCH + WEBSEARCH")
    logger.info("=" * 80)

    researcher = PresidentialGrantsResearcher(
        db,
        llm_provider="claude",
        websearch_provider="perplexity"
    )

    research_result = await researcher.conduct_research_async(
        anketa_id=anketa['id']
    )

    # Сохранить артефакты
    await save_artifact(
        data=research_result,
        filename="research_archery_kemerovo",
        output_dir=artifacts_dir,
        formats=['md', 'pdf']
    )

    logger.info(f"✅ Исследование завершено: {research_result['total_queries']} запросов")

    # ЭТАП 3: Grant Writing
    logger.info("=" * 80)
    logger.info("ЭТАП 3: GRANT WRITING")
    logger.info("=" * 80)

    writer = WriterAgentV2(db, llm_provider="gigachat")
    grant_result = await writer.write_grant_async(
        anketa_id=anketa['id'],
        research_results=research_result['research_results']
    )

    nomenclature = grant_result['nomenclature']

    # Сохранить артефакты
    await save_artifact(
        data=grant_result,
        filename=f"grant_{nomenclature}",
        output_dir=artifacts_dir,
        formats=['md', 'pdf']
    )

    logger.info(f"✅ Грант создан: {nomenclature}")

    # ЭТАП 4: Final Review
    logger.info("=" * 80)
    logger.info("ЭТАП 4: FINAL REVIEW")
    logger.info("=" * 80)

    reviewer = ReviewerAgent(db, llm_provider="gigachat")
    review_result = await reviewer.review_grant_async(
        grant_content=grant_result['content'],
        research_results=research_result['research_results'],
        user_answers=anketa
    )

    approval_probability = review_result['approval_probability']

    # Сохранить артефакты
    await save_artifact(
        data=review_result,
        filename=f"review_{nomenclature}",
        output_dir=artifacts_dir,
        formats=['md', 'pdf']
    )

    logger.info(f"✅ Финальная оценка: {approval_probability}% вероятность одобрения")

    # Финальный отчёт
    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Артефакты сохранены в: {artifacts_dir}")
    logger.info(f"- anketa_archery_kemerovo_audit.md + .pdf")
    logger.info(f"- research_archery_kemerovo.md + .pdf")
    logger.info(f"- grant_{nomenclature}.md + .pdf")
    logger.info(f"- review_{nomenclature}.md + .pdf")

    # Assertions
    assert audit_score >= 60, f"Audit score слишком низкий: {audit_score}"
    assert len(research_result['research_results']) == 28, "Должно быть 28 блоков (27 + 1 ФПГ)"
    assert approval_probability >= 40, f"Вероятность одобрения слишком низкая: {approval_probability}"
```

#### ШАГ 5: Создать утилиту для сохранения артефактов (1 час)

**Файл**: `utils/artifact_saver.py`

```python
async def save_artifact(
    data: Dict[str, Any],
    filename: str,
    output_dir: Path,
    formats: List[str] = ['md', 'pdf']
) -> Dict[str, Path]:
    """
    Сохранить артефакт в MD и/или PDF

    Args:
        data: Данные для сохранения
        filename: Имя файла (без расширения)
        output_dir: Директория для сохранения
        formats: Форматы ['md', 'pdf']

    Returns:
        {'md': Path, 'pdf': Path}
    """

    saved_files = {}

    # Генерация MD
    if 'md' in formats:
        md_content = _generate_markdown(data)
        md_path = output_dir / f"{filename}.md"
        md_path.write_text(md_content, encoding='utf-8')
        saved_files['md'] = md_path

    # Генерация PDF
    if 'pdf' in formats:
        pdf_path = output_dir / f"{filename}.pdf"
        await _generate_pdf(data, pdf_path)
        saved_files['pdf'] = pdf_path

    return saved_files
```

#### ШАГ 6: Создать локальный скрипт для запуска (30 минут)

**Файл**: `scripts/generate_archery_grant_local.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Локальный скрипт для генерации гранта "Лучные клубы Кемерово"

НЕ коммитить в git!
Только для локальной разработки и тестирования.

Usage:
    python scripts/generate_archery_grant_local.py
"""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_archery_club_fpg_e2e import test_archery_club_full_pipeline


async def main():
    print("=" * 80)
    print("Генерация гранта: Лучные клубы Кемерово")
    print("=" * 80)
    print()

    try:
        await test_archery_club_full_pipeline()
        print()
        print("=" * 80)
        print("✅ УСПЕШНО! Все артефакты созданы.")
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ОШИБКА: {e}")
        print("=" * 80)
        raise


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. ВРЕМЕННЫЕ ОЦЕНКИ

| Задача | Время | Приоритет |
|--------|-------|-----------|
| ШАГ 1: InteractiveInterviewerAgent | 2-3 часа | 🔴 HIGH |
| ШАГ 2: PresidentialGrantsResearcher | 1-2 часа | 🟡 MEDIUM |
| ШАГ 3: Переключение на GigaChat | 5 минут | 🔴 CRITICAL |
| ШАГ 4: E2E тест | 2-3 часа | 🔴 HIGH |
| ШАГ 5: Artifact Saver | 1 час | 🟡 MEDIUM |
| ШАГ 6: Локальный скрипт | 30 минут | 🟢 LOW |
| **ИТОГО** | **7-10 часов** | |

---

## 5. РИСКИ И МИТИГАЦИЯ

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Claude Code API не заработает | HIGH | HIGH | ✅ Переключились на GigaChat |
| GigaChat лимиты (8k tokens) | MEDIUM | MEDIUM | Разбить промпты на части |
| Perplexity WebSearch квота | LOW | MEDIUM | Добавить fallback на Claude Code WebSearch |
| Долгое время генерации | MEDIUM | LOW | Добавить progress indicators |

---

## 6. ПРОВЕРКА ГОТОВНОСТИ

### Чеклист перед запуском:

- [ ] ШАГ 1: `agents/interactive_interviewer_agent.py` создан
- [ ] ШАГ 2: `agents/presidential_grants_researcher.py` создан
- [ ] ШАГ 3: `shared/llm/config.py` изменён (writer/reviewer → GigaChat)
- [ ] ШАГ 4: `tests/integration/test_archery_club_fpg_e2e.py` создан
- [ ] ШАГ 5: `utils/artifact_saver.py` создан
- [ ] ШАГ 6: `scripts/generate_archery_grant_local.py` создан
- [ ] Все файлы НЕ добавлены в git (локально)
- [ ] Создана папка `grants_output/archery_kemerovo/`
- [ ] GigaChat API ключ в `.env`
- [ ] Perplexity API ключ в `.env`
- [ ] PostgreSQL доступна (5.35.88.251)

### Команды для запуска:

```bash
# Запуск E2E теста
pytest tests/integration/test_archery_club_fpg_e2e.py -v -s

# ИЛИ через локальный скрипт
python scripts/generate_archery_grant_local.py
```

---

## 7. ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### Структура артефактов:

```
grants_output/archery_kemerovo/
├── anketa_archery_kemerovo_audit.md
├── anketa_archery_kemerovo_audit.pdf
├── research_archery_kemerovo.md
├── research_archery_kemerovo.pdf
├── grant_AN-20251012-archery_kemerovo-001.md
├── grant_AN-20251012-archery_kemerovo-001.pdf
├── review_AN-20251012-archery_kemerovo-001.md
└── review_AN-20251012-archery_kemerovo-001.pdf
```

### Содержание артефактов:

#### 1. `anketa_archery_kemerovo_audit.md`
- 24 поля анкеты
- Оценка по 10 критериям (1-10 баллов)
- Интерактивные уточнения
- Рекомендации по улучшению
- Audit score: XX/100

#### 2. `research_archery_kemerovo.md`
- 27 блоков research (профильные, контекстные, целевые)
- 1 блок fund_requirements (ФПГ)
- 117+ источников
- Цитаты, статистика, кейсы

#### 3. `grant_AN-20251012-archery_kemerovo-001.md`
- 9 разделов (форма ФПГ)
- 15000-20000 символов
- 10+ цитат
- 2+ таблицы
- Статистика и госпрограммы

#### 4. `review_AN-20251012-archery_kemerovo-001.md`
- Оценка по 4 критериям
- Weighted score (0-10)
- Approval probability (40-50%)
- Сильные/слабые стороны
- Приоритетные улучшения

---

## 8. СЛЕДУЮЩИЕ ШАГИ (ПОСЛЕ ТЕСТИРОВАНИЯ)

1. ✅ Локальное тестирование завершено
2. 📝 Документирование результатов
3. 🔍 Code review
4. 🧪 Дополнительные тесты (другие темы)
5. 🚀 Подготовка к интеграции в production
6. 📤 Коммит и пуш в git (ТОЛЬКО после утверждения)

---

## 9. КОНТАКТЫ

**Автор плана**: Grant Service Architect Agent
**Дата**: 2025-10-12
**Статус**: Готов к реализации
**Версия**: 1.0

---

**ВАЖНО**: Всё локально, НЕ коммитить в git до завершения тестирования!
