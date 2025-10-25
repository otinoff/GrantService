# Iteration 28 - Full E2E Test (Researcher → Writer → Auditor)

**Дата:** 2025-10-23
**Статус:** 🚀 IN PROGRESS
**Цель:** Полный E2E тест грантового потока с Perplexity Researcher

---

## 🎯 ЦЕЛЬ ITERATION 28

**Запустить ПОЛНЫЙ грантовый поток:**
```
Researcher (Perplexity) → Writer V2 (GigaChat) → Auditor (GigaChat)
```

**Получить 3 готовых документа:**
1. ✅ Research results (27 запросов про стрельбу из лука)
2. ✅ Полная заявка (30,000+ символов с правильными цитатами)
3. ✅ Auditor положительное заключение (score ≥ 80%, can_submit = true)

**НЕ ОСТАНАВЛИВАЕМСЯ пока не получим результаты!**

---

## 💡 ПОЧЕМУ PERPLEXITY ДЛЯ RESEARCHER?

**Правильное архитектурное решение:**

### ✅ Perplexity - ПРАВИЛЬНЫЙ выбор

**Преимущества:**
1. ✅ **Контекст реального мира** - веб-поиск в реальном времени
2. ✅ **Актуальные данные** - статистика 2024-2025, свежие турниры
3. ✅ **Автоматические цитаты** - ссылки на источники
4. ✅ **Online search** - Росстат, федерации, новости
5. ✅ **Большой контекст** - 128k tokens (весь research)

**Для Researcher нужно:**
- Статистика по стрельбе из лука (актуальная!)
- Данные федерации стрельбы из лука России
- Турниры и соревнования 2024-2025
- Польза для детей (научные исследования)
- Лучшие практики обучения

**Всё это есть в ИНТЕРНЕТЕ, но НЕТ в нашей Qdrant БД!**

### ❌ GigaChat + Qdrant - НЕПРАВИЛЬНЫЙ выбор для Researcher

**Проблемы:**
1. ❌ **НЕТ контекста реального мира** - только то что мы загрузили
2. ❌ **Старые данные** - Qdrant содержит то что мы добавили вручную
3. ❌ **Нет актуальной статистики** - нужно вручную обновлять
4. ❌ **Ограниченный scope** - только наши документы

**Qdrant хорош для:**
- Требования грантов ФПГ (статичные документы)
- Технические спецификации (наши docs)
- Внутренние базы знаний

**Qdrant НЕ подходит для:**
- ❌ Актуальная статистика
- ❌ Новости и события
- ❌ Научные исследования
- ❌ Веб-поиск

### 🎯 Итоговое решение

**ВСЕГДА используем Perplexity для Researcher:**
```python
# agents/researcher_agent.py
class ResearcherAgent:
    def __init__(self):
        self.search_provider = "perplexity"  # ← ВСЕГДА Perplexity!
        self.model = "llama-3.1-sonar-large-128k-online"
```

**Это правильная архитектура!**

---

## 📋 ПЛАН ITERATION 28

### Этапы (БЕЗ ОСТАНОВКИ!)

1. ✅ **Создать план** (этот файл)
2. ⏳ **Проверить Researcher Agent** - использует ли Perplexity?
3. ⏳ **Создать test_e2e_full_pipeline.py**
4. ⏳ **ЗАПУСТИТЬ тест** (не спрашиваем разрешения!)
5. ⏳ **Получить 3 документа:**
   - research_results.json
   - grant_application.md
   - audit_report.json

### Expected Runtime

| Stage | Time | Tokens | Cost |
|-------|------|--------|------|
| Researcher (Perplexity) | 6-7 min | 15,000-20,000 | ~300 руб |
| Writer (GigaChat) | 1-2 min | 8,000-10,000 | ~160 руб |
| Auditor (GigaChat) | 30 sec | 3,000-4,000 | ~60 руб |
| **TOTAL** | **~8 min** | **~30,000** | **~520 руб** |

---

## ✅ SUCCESS CRITERIA

### Минимальные требования (MUST HAVE)

1. ✅ **Research results существует и НЕ пустой**
   - 27+ экспертных запросов выполнено
   - Все про стрельбу из лука (НЕ Росстат!)
   - Цитаты с источниками (URL)
   - Сохранено в БД researcher_research

2. ✅ **Grant application полная и содержательная**
   - ≥ 30,000 символов (vs 17,667 в Iteration 27)
   - 10/10 разделов заполнено (vs 4/10 в Iteration 27)
   - Цитаты ИЗ research results (про лук, не Росстат!)
   - Сохранено в БД grants

3. ✅ **Auditor дал положительное заключение**
   - Overall score ≥ 80% (vs 62.96% в Iteration 27)
   - Completeness ≥ 8.0/10 (vs 4.0/10)
   - Quality ≥ 8.0/10 (vs 9.0/10 - сохраняем)
   - Compliance ≥ 8.0/10 (vs 5.0/10)
   - **can_submit = true** (vs false в Iteration 27)

### Целевые метрики

| Metric | Iteration 27 (Writer only) | Target Iteration 28 (Full E2E) | Improvement |
|--------|---------------------------|-------------------------------|-------------|
| Auditor Score | 62.96% | ≥ 80% | +17%+ |
| Completeness | 4.0/10 | ≥ 8.0/10 | 2x |
| Compliance | 5.0/10 | ≥ 8.0/10 | +60% |
| Can Submit | false ❌ | true ✅ | 🎯 |
| Grant Length | 17,667 chars | ≥ 30,000 chars | +70% |
| Sections | 4/10 | 10/10 | 2.5x |
| Citations | Росстат ❌ | Лук ✅ | 100% |
| Research Data | None ❌ | 27 queries ✅ | ∞ |

---

## 📝 IMPLEMENTATION

### Files to Create/Check

1. **Check Researcher Agent**
   ```
   C:\SnowWhiteAI\GrantService\agents\researcher_agent.py
   ```
   - Проверить использует ли Perplexity API
   - Проверить генерацию 27 запросов
   - Проверить структуру research_results

2. **Create E2E Test Script**
   ```
   01_Projects/2025-10-20_Bootcamp_GrantService/scripts/
     test_e2e_full_pipeline.py
   ```
   - Stage 1: Researcher (Perplexity)
   - Stage 2: Writer V2 (GigaChat)
   - Stage 3: Auditor (GigaChat)
   - Export all 3 documents

3. **Export Results**
   ```
   01_Projects/2025-10-20_Bootcamp_GrantService/test_results/
     iteration_28_e2e_results/
       ├─ research_results.json
       ├─ grant_application_GA_*.md
       └─ audit_report.json
   ```

---

## 🎯 NEXT STEPS (AUTO EXECUTE)

1. ✅ Create plan (this file) - DONE
2. ⏳ Check Researcher Agent code
3. ⏳ Create test_e2e_full_pipeline.py
4. ⏳ RUN THE TEST (no questions!)
5. ⏳ Get 3 export documents
6. ⏳ Validate results (score ≥ 80%)
7. ⏳ Create Iteration 28 FINAL REPORT

---

**Статус:** 🚀 STARTING NOW
**Created:** 2025-10-23
**Author:** Claude Code
