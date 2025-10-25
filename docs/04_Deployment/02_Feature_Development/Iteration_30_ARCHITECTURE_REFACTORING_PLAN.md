# Iteration 30 - Architecture Refactoring & Full E2E Test

**Дата:** 2025-10-24
**Статус:** 🚀 IN PROGRESS
**Цель:** Отделить Grant Pipeline от Telegram Bot + Full E2E test

---

## 🎯 ГЛАВНАЯ ЦЕЛЬ

**Сделать Grant Pipeline независимым от Telegram Bot!**

Должно работать:
```
JSON input → GrantPipeline → 3 текстовых файла (Researcher, Writer, Auditor)
```

**БЕЗ** необходимости в:
- Telegram Bot
- sessions table
- telegram_id
- anketa_id из БД

---

## 📋 TASKS ITERATION 30

### Task 1: Конфигурация ✅ DONE

**Файл:** `test_config.json`

**Ключевые настройки:**
```json
{
  "vector_database": {
    "qdrant": {
      "host": "5.35.88.251",  // ТОЛЬКО серверная!
      "port": 6333,
      "note": "НЕТ локальной Qdrant!"
    }
  },
  "llm": {
    "gigachat": {
      "rate_limit": {
        "delay_between_requests": 6,  // Fix 529 errors!
        "retry_attempts": 3
      }
    }
  },
  "testing": {
    "mode": "standalone",
    "requires_telegram": false,  // БЕЗ Telegram Bot!
    "use_json_input": true
  }
}
```

---

### Task 2: Decoupled Researcher (wrapper)

**Проблема:**
ResearcherAgentV2 ожидает anketa_id из БД (Telegram Bot workflow)

**Решение:**
Создать **wrapper** `StandaloneResearcher`:

```python
class StandaloneResearcher:
    """
    Standalone Researcher - работает БЕЗ БД и Telegram Bot
    """
    def __init__(self, websearch_provider='perplexity'):
        self.websearch_provider = websearch_provider

    async def research(self, project_data: Dict) -> Dict:
        """
        Args:
            project_data: {
                "project_name": "Стрельба из лука",
                "problem": "Обучение детей...",
                "target_audience": "дети 7-17 лет",
                "geography": "Кемерово",
                "goals": ["Развитие спорта", "Патриотизм"]
            }

        Returns:
            research_results: {
                "block1_problem": {...},
                "block2_geography": {...},
                "block3_goals": {...},
                "metadata": {
                    "total_queries": 27,
                    "websearch_provider": "perplexity"
                }
            }
        """
        # Generate 27 expert queries from project_data
        queries = self._generate_queries(project_data)

        # Execute websearch (Perplexity)
        results = await self._execute_websearch(queries)

        # Structure results
        research_results = self._structure_results(results, project_data)

        return research_results
```

**Преимущества:**
- ✅ Не зависит от БД
- ✅ Принимает dict (не anketa_id)
- ✅ Можно тестировать с JSON

---

### Task 3: Decoupled Writer (wrapper)

**Проблема:**
WriterAgentV2 загружает research_results из БД внутри себя

**Решение:**
Создать **wrapper** `StandaloneWriter`:

```python
class StandaloneWriter:
    """
    Standalone Writer - явные параметры, БЕЗ БД зависимостей
    """
    def __init__(self, llm_provider='gigachat', rate_limit_delay=6):
        self.llm_provider = llm_provider
        self.rate_limit_delay = rate_limit_delay

    async def write(
        self,
        project_data: Dict,
        research_results: Dict
    ) -> str:
        """
        Args:
            project_data: Данные проекта
            research_results: Результаты от Researcher

        Returns:
            grant_content: Полный текст заявки (str)
        """
        # Build context
        context = self._build_context(project_data, research_results)

        # Generate grant through LLM
        grant_content = await self._generate_grant(context)

        return grant_content
```

**Преимущества:**
- ✅ Явные зависимости (не hidden)
- ✅ Не загружает из БД
- ✅ Легко тестировать

---

### Task 4: Decoupled Auditor (wrapper + rate limit fix)

**Проблема:**
1. Auditor падает с 529 rate limit
2. Требует БД для сохранения

**Решение:**
Создать **wrapper** `StandaloneAuditor`:

```python
class StandaloneAuditor:
    """
    Standalone Auditor - с паузами для rate limit
    """
    def __init__(
        self,
        llm_provider='gigachat',
        rate_limit_delay=6,
        retry_attempts=3
    ):
        self.llm_provider = llm_provider
        self.rate_limit_delay = rate_limit_delay
        self.retry_attempts = retry_attempts

    async def audit(self, grant_content: str) -> Dict:
        """
        Args:
            grant_content: Текст заявки

        Returns:
            audit_result: {
                "overall_score": 0.85,
                "completeness_score": 8.5,
                "quality_score": 9.0,
                "compliance_score": 8.0,
                "can_submit": true,
                "recommendations": [...]
            }
        """
        # ВАЖНО: Пауза ПЕРЕД запросом!
        await asyncio.sleep(self.rate_limit_delay)

        # Analyze with retry logic
        for attempt in range(self.retry_attempts):
            try:
                audit_result = await self._analyze(grant_content)
                return audit_result
            except RateLimitError:
                if attempt < self.retry_attempts - 1:
                    wait_time = self.rate_limit_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

**FIX для 529 errors:**
- ✅ Delay 6 секунд ПЕРЕД каждым запросом
- ✅ Exponential backoff при ошибке
- ✅ 3 попытки retry

---

### Task 5: GrantPipeline Orchestrator

**Цель:**
Координировать Researcher → Writer → Auditor БЕЗ БД

```python
class GrantPipeline:
    """
    Orchestrator для полного грантового потока
    БЕЗ зависимости от Telegram Bot!
    """

    def __init__(self, config: Dict):
        self.config = config

        # Initialize agents
        self.researcher = StandaloneResearcher(
            websearch_provider=config['llm']['perplexity']['provider']
        )

        self.writer = StandaloneWriter(
            llm_provider='gigachat',
            rate_limit_delay=config['llm']['gigachat']['rate_limit']['delay_between_requests']
        )

        self.auditor = StandaloneAuditor(
            llm_provider='gigachat',
            rate_limit_delay=config['llm']['gigachat']['rate_limit']['delay_between_requests']
        )

    async def run(
        self,
        project_data: Dict,
        export_dir: Path
    ) -> Dict:
        """
        Запускает полный цикл: Researcher → Writer → Auditor

        Args:
            project_data: JSON данные проекта
            export_dir: Куда сохранять результаты

        Returns:
            {
                "researcher": {...},
                "writer": "...",
                "auditor": {...},
                "exported_files": [...]
            }
        """
        log("=" * 80)
        log("🚀 STARTING GRANT PIPELINE")
        log("=" * 80)

        # STAGE 1: Researcher (6-7 min)
        log("🔍 Stage 1/3: Researcher (Perplexity)")
        research_results = await self.researcher.research(project_data)

        # Export research
        research_file = export_dir / "1_research_results.json"
        with open(research_file, 'w', encoding='utf-8') as f:
            json.dump(research_results, f, indent=2, ensure_ascii=False)
        log(f"✅ Exported: {research_file.name}")

        # STAGE 2: Writer (1-2 min)
        log("✍️ Stage 2/3: Writer (GigaChat)")
        grant_content = await self.writer.write(project_data, research_results)

        # Export grant
        grant_file = export_dir / "2_grant_application.md"
        with open(grant_file, 'w', encoding='utf-8') as f:
            f.write(grant_content)
        log(f"✅ Exported: {grant_file.name}")

        # DELAY to avoid rate limit
        log(f"⏳ Waiting {self.config['llm']['gigachat']['rate_limit']['delay_between_requests']}s...")
        await asyncio.sleep(self.config['llm']['gigachat']['rate_limit']['delay_between_requests'])

        # STAGE 3: Auditor (30 sec)
        log("📊 Stage 3/3: Auditor (GigaChat)")
        audit_result = await self.auditor.audit(grant_content)

        # Export audit
        audit_file = export_dir / "3_audit_report.json"
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_result, f, indent=2, ensure_ascii=False)
        log(f"✅ Exported: {audit_file.name}")

        log("=" * 80)
        log("🎉 PIPELINE COMPLETED!")
        log(f"   Auditor score: {audit_result['overall_score'] * 100:.1f}%")
        log(f"   Can submit: {audit_result['can_submit']}")
        log("=" * 80)

        return {
            "researcher": research_results,
            "writer": grant_content,
            "auditor": audit_result,
            "exported_files": [research_file, grant_file, audit_file]
        }
```

---

### Task 6: Full E2E Test

**Файл:** `test_full_e2e_standalone.py`

```python
#!/usr/bin/env python3
"""
Iteration 30 - FULL E2E TEST (БЕЗ Telegram Bot!)

Input: JSON file
Output: 3 текстовых файла (Researcher, Writer, Auditor)
"""

async def main():
    # Load config
    config = load_config("test_config.json")

    # Load project data from JSON
    project_data = load_json("natalia_anketa_20251012.json")

    # Extract project info
    project_info = {
        "project_name": project_data['project_info']['name'],
        "problem": project_data['interview_data']['problem_description'],
        "target_audience": project_data['interview_data']['target_audience'],
        "geography": project_data['interview_data']['geography'],
        "goals": project_data['interview_data']['goals']
    }

    # Initialize pipeline
    pipeline = GrantPipeline(config)

    # RUN PIPELINE (БЕЗ ОСТАНОВКИ!)
    results = await pipeline.run(
        project_data=project_info,
        export_dir=Path("test_results/iteration_30_e2e_results")
    )

    # Summary
    print("\n" + "=" * 80)
    print("✅ E2E TEST COMPLETED!")
    print("=" * 80)
    print("\n📁 Exported files:")
    for f in results['exported_files']:
        print(f"   - {f.name}")
    print()
```

---

## 📊 EXPECTED RESULTS

После запуска E2E теста должны получить **3 файла**:

```
test_results/iteration_30_e2e_results/
├─ 1_research_results.json
│   └─ 27 запросов про стрельбу из лука (Perplexity)
│
├─ 2_grant_application.md
│   └─ Полная заявка 30,000+ символов (GigaChat)
│
└─ 3_audit_report.json
    └─ Оценка ≥ 80%, can_submit = true (GigaChat)
```

---

## ✅ SUCCESS CRITERIA

| Criterion | Target |
|-----------|--------|
| ✅ БЕЗ Telegram Bot | Не требуется |
| ✅ JSON input | project_data из файла |
| ✅ Researcher works | 27 queries Perplexity |
| ✅ Writer works | 30,000+ символов |
| ✅ Auditor works | score ≥ 80% |
| ✅ NO rate limit errors | 529 errors fixed |
| ✅ 3 exported files | research + grant + audit |

---

## 🔧 ARCHITECTURE

### BEFORE (Telegram Bot-centric):
```
Telegram Bot → sessions (anketa_id) → Researcher → Writer → Auditor
```

### AFTER (Decoupled):
```
JSON file → project_data → GrantPipeline → 3 files
                              ├─ Researcher (Perplexity)
                              ├─ Writer (GigaChat + delay)
                              └─ Auditor (GigaChat + delay)
```

---

## 🚀 IMPLEMENTATION STEPS

1. ✅ Создать test_config.json - DONE
2. ✅ Создать план Iteration 30 - DONE
3. ⏳ Создать StandaloneResearcher wrapper
4. ⏳ Создать StandaloneWriter wrapper
5. ⏳ Создать StandaloneAuditor wrapper (+ rate limit fix)
6. ⏳ Создать GrantPipeline orchestrator
7. ⏳ Создать test_full_e2e_standalone.py
8. ⏳ ЗАПУСТИТЬ E2E test (~9 минут)
9. ⏳ Получить 3 текстовых файла
10. ⏳ Создать Iteration 30 FINAL REPORT

---

## 📝 NOTES

### Rate Limit Fix (529 errors)

**Проблема:** GigaChat rate limit (~10 req/min)

**Решение:**
```python
# Delay ПЕРЕД каждым запросом к GigaChat
DELAY_BEFORE_REQUEST = 6  # seconds

# Writer finished
await asyncio.sleep(DELAY_BEFORE_REQUEST)

# Now safe to call Auditor
auditor.audit(grant_content)
```

**Exponential backoff:**
```python
for attempt in range(3):
    try:
        result = await llm_call()
        break
    except RateLimitError:
        wait = DELAY * (2 ** attempt)  # 6s, 12s, 24s
        await asyncio.sleep(wait)
```

---

**Автор:** Claude Code
**Дата:** 2025-10-24
**Статус:** 🚀 IN PROGRESS
**Duration:** ~2 hours
