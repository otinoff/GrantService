# Iteration 29 - ПОЛНЫЙ E2E С PERPLEXITY RESEARCHER

**Дата:** 2025-10-24
**Статус:** 🚀 IN PROGRESS
**Цель:** Полный E2E тест с РЕАЛЬНЫМ Perplexity Researcher

---

## 🎯 ЦЕЛЬ ITERATION 29

**Запустить ПОЛНЫЙ грантовый поток БЕЗ ОСТАНОВКИ:**
```
Perplexity Researcher → Writer V2 (GigaChat) → Auditor (GigaChat)
```

**Получить 3 готовых документа:**
1. ✅ Research results - 27 запросов про стрельбу из лука (Perplexity!)
2. ✅ Полная заявка - 30,000+ символов с ПРАВИЛЬНЫМИ цитатами (ПРО ЛУК!)
3. ✅ Auditor положительное заключение - score ≥ 80%, can_submit = true

**НЕ ОСТАНАВЛИВАЕМСЯ пока не получим ВСЕ 3 результата!**

---

## 📋 LESSONS FROM ITERATION 28

### ❌ Что пошло не так в Iteration 28?

1. **Writer использовал СТАРЫЕ research results из БД**
   - Mock research не сработал
   - Заявка написана про Росстат вместо стрельбы из лука
   - **Решение:** Запустить РЕАЛЬНОГО Researcher (Perplexity)

2. **Auditor score 0% (GigaChat rate limit)**
   - Слишком много запросов подряд
   - **Решение:** Добавить delay 10 секунд между Writer и Auditor

3. **Expert Agent не подключился к Qdrant**
   - Qdrant не запущен
   - **Решение:** Это НЕ критично, Writer работает и без него

### ✅ Что работало хорошо?

1. ✅ Writer V2 генерирует заявки
2. ✅ Auditor анализирует заявки
3. ✅ Система интеграции работает
4. ✅ Экспорт документов работает
5. ✅ LLM logging без дублирования

---

## 🔧 ПЛАН ITERATION 29

### Этапы (БЕЗ ОСТАНОВКИ!)

1. ✅ Создать план Iteration 29 (этот файл)
2. ⏳ Создать test_e2e_with_perplexity_researcher.py
3. ⏳ STAGE 1: Researcher Agent (Perplexity) - 6-7 минут
   - 27 экспертных запросов про стрельбу из лука
   - Сохранить research results в БД
   - Экспортировать research_results.json
4. ⏳ STAGE 2: Writer V2 (GigaChat) - 1-2 минуты
   - Загрузить research results из БД
   - Написать заявку ПРО ЛУК (не Росстат!)
   - Экспортировать grant_application.md
5. ⏳ DELAY: 10 секунд (avoid GigaChat rate limit)
6. ⏳ STAGE 3: Auditor (GigaChat) - 30 секунд
   - Проанализировать заявку
   - Score ≥ 80%
   - Экспортировать audit_report.json
7. ⏳ VALIDATION: Проверить все 3 документа
8. ⏳ Создать Iteration 29 FINAL REPORT

---

## 📊 EXPECTED RUNTIME

| Stage | Time | Tokens | API Cost |
|-------|------|--------|----------|
| **Researcher (Perplexity)** | 6-7 min | 15,000-20,000 | ~300 руб |
| **Writer V2 (GigaChat)** | 1-2 min | 8,000-10,000 | ~160 руб |
| **Delay** | 10 sec | 0 | 0 |
| **Auditor (GigaChat)** | 30 sec | 3,000-4,000 | ~60 руб |
| **TOTAL** | **~9 min** | **~30,000** | **~520 руб** |

---

## ✅ SUCCESS CRITERIA

### Минимальные требования (MUST HAVE)

1. ✅ **Researcher завершился успешно**
   - 27+ запросов выполнено через Perplexity API
   - Все запросы ПРО СТРЕЛЬБУ ИЗ ЛУКА (не Росстат!)
   - Research results сохранены в БД
   - research_results.json экспортирован

2. ✅ **Writer написал заявку про ЛУК**
   - Загрузил research results из БД (те что создал Researcher!)
   - Заявка содержит цитаты про стрельбу из лука
   - Длина ≥ 30,000 символов
   - grant_application.md экспортирован

3. ✅ **Auditor дал положительное заключение**
   - Overall score ≥ 80% (vs 0% в Iteration 28)
   - Completeness ≥ 8.0/10
   - Quality ≥ 8.0/10
   - Compliance ≥ 8.0/10
   - **can_submit = true**
   - audit_report.json экспортирован

4. ✅ **Все 3 документа экспортированы**
   ```
   test_results/iteration_29_e2e_results/
   ├─ research_results_*.json
   ├─ grant_application_GA_*.md
   └─ audit_report_*.json
   ```

---

## 🚀 IMPLEMENTATION

### Файл: test_e2e_with_perplexity_researcher.py

```python
#!/usr/bin/env python3
"""
ITERATION 29 - FULL E2E TEST with Perplexity Researcher
Цель: Получить 3 полных документа БЕЗ ОСТАНОВКИ
"""

async def main():
    # STAGE 1: Researcher (Perplexity) - 6-7 min
    log("🔍 STAGE 1: RESEARCHER AGENT (Perplexity)")
    researcher = ResearcherAgentV2(websearch_provider='perplexity')
    research_result = await researcher.research(anketa_data)

    research_id = research_result['research_id']
    log(f"✅ Research completed: {research_id}")
    export_research_results(research_id)

    # STAGE 2: Writer V2 (GigaChat) - 1-2 min
    log("✍️ STAGE 2: WRITER AGENT (GigaChat-2-Max)")
    writer = WriterAgentV2(db=db, llm_provider='gigachat')
    write_result = await writer.write_application_async(input_data)

    grant_id = write_result['application_number']
    log(f"✅ Grant completed: {grant_id}")
    export_grant_application(grant_id)

    # DELAY: 10 seconds (avoid rate limit)
    log("⏳ Waiting 10 seconds to avoid GigaChat rate limit...")
    await asyncio.sleep(10)

    # STAGE 3: Auditor (GigaChat) - 30 sec
    log("📊 STAGE 3: AUDITOR AGENT (GigaChat-2-Max)")
    auditor = AuditorAgent(db=db, llm_provider='gigachat')
    audit_result = await auditor.audit_application_async(audit_input)

    overall_score = audit_result['overall_score']
    can_submit = audit_result['can_submit']
    log(f"✅ Audit completed: score={overall_score}%, can_submit={can_submit}")
    export_audit_report(grant_id, audit_result)

    # VALIDATION
    validate_all_3_documents(research_id, grant_id, overall_score)
```

---

## 🎯 KEY IMPROVEMENTS vs Iteration 28

| Issue (Iter 28) | Solution (Iter 29) |
|-----------------|-------------------|
| ❌ Mock research не сработал | ✅ РЕАЛЬНЫЙ Perplexity Researcher |
| ❌ Заявка про Росстат | ✅ Research про стрельбу из лука |
| ❌ Auditor 0% (rate limit) | ✅ 10-second delay перед Auditor |
| ❌ Writer загрузил старые research | ✅ Researcher создаст НОВЫЕ research в БД |
| ⚠️ Expert Agent упал (Qdrant) | ⚠️ Не критично, Writer работает без него |

---

## 📝 КРИТИЧЕСКИЕ МОМЕНТЫ

### 1. **Perplexity API Key должен быть в .env.local**

```bash
PERPLEXITY_API_KEY=pplx-xxxxx
```

### 2. **Anketa ID должен быть уникальным**

```python
anketa_id = f"#AN-ITER29-{datetime.now().strftime('%Y%m%d%H%M%S')}"
```

Чтобы Writer загрузил СВЕЖИЕ research results, а не старые.

### 3. **Researcher ДОЛЖЕН использовать Perplexity**

```python
researcher = ResearcherAgentV2(websearch_provider='perplexity')
```

НЕ GigaChat + Qdrant! (нет данных о луке в векторной базе)

### 4. **Delay 10 секунд между Writer и Auditor**

```python
await asyncio.sleep(10)
```

Чтобы избежать GigaChat rate limit.

---

## 📚 ПОЧЕМУ PERPLEXITY ДЛЯ RESEARCHER?

### ✅ Perplexity - ПРАВИЛЬНЫЙ выбор

**Преимущества:**
1. ✅ **Контекст реального мира** - веб-поиск в реальном времени
2. ✅ **Актуальные данные** - статистика 2024-2025, турниры, федерации
3. ✅ **Автоматические цитаты** - ссылки на источники включены
4. ✅ **Online search** - Росстат, спортивные федерации, новости
5. ✅ **Большой контекст** - 128k tokens (весь research поместится)

**Для Researcher нужно:**
- Статистика по стрельбе из лука (актуальная!)
- Данные федерации стрельбы из лука России
- Турниры и соревнования 2024-2025
- Польза для детей (научные исследования)
- Лучшие практики обучения

**Всё это есть в ИНТЕРНЕТЕ, но НЕТ в нашей Qdrant БД!**

### ❌ GigaChat + Qdrant - НЕПРАВИЛЬНО для Researcher

**Проблемы:**
1. ❌ **НЕТ контекста реального мира** - только то что мы загрузили
2. ❌ **Старые данные** - Qdrant содержит то что добавлено вручную
3. ❌ **Нет актуальной статистики** - нужно вручную обновлять
4. ❌ **Ограниченный scope** - только наши документы

**Qdrant хорош для:**
- Требования грантов ФПГ (статичные документы)
- Технические спецификации (наши docs)
- Внутренние базы знаний

**Qdrant НЕ подходит для:**
- ❌ Актуальная статистика о спорте
- ❌ Новости и события 2024-2025
- ❌ Научные исследования о стрельбе из лука
- ❌ Веб-поиск

---

## 🔍 TROUBLESHOOTING

### Problem: Researcher упал с ошибкой Perplexity API

**Solution:**
1. Проверить PERPLEXITY_API_KEY в .env.local
2. Проверить баланс API
3. Проверить rate limit (100 запросов/минуту)

### Problem: Writer всё равно использует старые research

**Solution:**
1. Проверить что Researcher сохранил results в БД
2. Проверить anketa_id совпадает
3. Очистить старые research results из БД если нужно

### Problem: Auditor снова 0% (rate limit)

**Solution:**
1. Увеличить delay до 15-20 секунд
2. Использовать другую модель для Auditor (Claude?)
3. Добавить exponential backoff

---

## 🎯 NEXT STEPS (AUTO EXECUTE)

1. ✅ Создать план Iteration 29 (этот файл) - DONE
2. ⏳ Создать test_e2e_with_perplexity_researcher.py
3. ⏳ ЗАПУСТИТЬ тест БЕЗ ОСТАНОВКИ (9 минут)
4. ⏳ Получить 3 экспортированных документа
5. ⏳ Проверить score ≥ 80%
6. ⏳ Создать Iteration 29 FINAL REPORT

---

**Статус:** 🚀 STARTING NOW
**Created:** 2025-10-24
**Author:** Claude Code
**Motto:** НЕ ОСТАНАВЛИВАЕМСЯ ПОКА НЕ ПОЛУЧИМ ВСЕ 3 ДОКУМЕНТА!
