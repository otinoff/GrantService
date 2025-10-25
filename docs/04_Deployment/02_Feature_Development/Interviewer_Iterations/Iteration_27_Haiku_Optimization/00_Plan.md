# Iteration 27: Haiku Optimization + Simplified Architecture

**Дата создания:** 2025-10-23
**Статус:** PLANNED
**Приоритет:** HIGH
**Время:** ~4 часа

---

## 🎯 Цель

Ускорить интервьюер в **3-4 раза** и удешевить в **10 раз** через:
1. Переход с Sonnet 4.5 на Haiku 3.5
2. Упрощение архитектуры (убрать Qdrant из hot path)
3. Оптимизация промптов

---

## 💡 Обоснование

### Текущая проблема:
- Вопросы генерируются 5-8 секунд
- User feedback: "медленновато вопросы идут"
- Дорого (~$0.02 на вопрос)
- Сложная архитектура (Qdrant semantic search каждый раз)

### Инсайт:
**Интервьюер - это сборщик структурированных данных, а не творческий писатель!**

Ему не нужно:
- ❌ Semantic search по 100 примерам каждый раз
- ❌ Сложное рассуждение (Sonnet overkill)
- ❌ Творческая генерация

Ему нужно:
- ✅ Знать 13 reference points (статично в промпте)
- ✅ Видеть что собрано / что не хватает
- ✅ Задать следующий логичный вопрос
- ✅ Переспросить если ответ неполный

**Для этого достаточно Haiku!**

---

## 📊 Ожидаемые результаты

### Performance:
| Метрика | До (Sonnet) | После (Haiku) | Улучшение |
|---------|-------------|---------------|-----------|
| Latency на вопрос | 5-8s | 1.5-2s | **-60-75%** |
| Cost на вопрос | ~$0.02 | ~$0.002 | **-90%** |
| Архитектура | Сложная | Простая | Легче поддерживать |

### Quality:
- Ожидается: достаточная (для структурированного сбора данных)
- Риск: может быть чуть менее "умная" для edge cases
- Mitigation: A/B тест, fallback на Sonnet для сложных случаев

---

## 🏗️ Архитектура

### ❌ Текущая (Iteration 26):
```
На каждый вопрос:
├─ Qdrant semantic search: 0.5-1s
│  └─ Поиск по 100+ примерам вопросов
├─ Gaps analysis: 0.5s
│  └─ Какие поля не заполнены
├─ Sonnet LLM: 4-6s
│  └─ Генерация вопроса с примерами
└─ Total: 5-8s

Cost: $0.02 per question
```

### ✅ Новая (Iteration 27):
```
На каждый вопрос:
├─ Static structure in prompt: 0s
│  └─ 13 reference points описаны в промпте
├─ Gaps analysis: 0.5s
│  └─ Какие поля не заполнены
├─ Haiku LLM: 1-1.5s
│  └─ Генерация вопроса (простая задача)
└─ Total: 1.5-2s

Cost: $0.002 per question
```

**Что убираем:**
- ❌ Qdrant semantic search из hot path
- ❌ Сложный prompt с примерами
- ❌ Sonnet (overkill для этой задачи)

**Что добавляем:**
- ✅ Статичное описание 13 reference points в промпте
- ✅ Четкие инструкции для Haiku
- ✅ Топ-10 примеров вшиты в промпт (без поиска)

---

## 📋 План выполнения

### Phase 1: Switch to Haiku (1 час)

**Задача:** Переключить модель с Sonnet на Haiku

**Файлы:**
```python
# C:\SnowWhiteAI\GrantService\agents\reference_points\adaptive_question_generator.py

# Было:
LLM_MODEL = "claude-3-5-sonnet-20241022"

# Стало:
LLM_MODEL = "claude-3-5-haiku-20241022"
```

**Тест:**
- Запустить один вопрос
- Проверить latency: должно быть ~1.5-2s
- Проверить качество: достаточно ли хорошо?

---

### Phase 2: Remove Qdrant from hot path (1 час)

**Задача:** Убрать semantic search, добавить статичную структуру в промпт

**Изменения:**

**Убрать:**
```python
# adaptive_question_generator.py: _get_fpg_context()
# Эта функция делает semantic search в Qdrant каждый раз
# Больше не нужна!
```

**Добавить:**
```python
REFERENCE_POINTS_STRUCTURE = """
Грантовая анкета состоит из 13 полей (Reference Points):

rp_001: Название проекта (краткое, понятное)
rp_002: Суть проекта (2-3 предложения, основная идея)
rp_003: Проблема (какую социальную проблему решает)
rp_004: Целевая аудитория (кто получит пользу)
rp_005: География (где будет реализован)
rp_006: Цели (чего хотим достичь)
rp_007: Задачи (конкретные шаги)
rp_008: Мероприятия (что будем делать)
rp_009: Результаты (что получим)
rp_010: Партнеры (кто поможет)
rp_011: Команда (кто реализует)
rp_012: Бюджет (сколько нужно)
rp_013: Устойчивость (что будет после гранта)

ПРИМЕРЫ ХОРОШИХ ВОПРОСОВ:
- "Расскажите, в чем суть вашего проекта?"
- "Какую социальную проблему вы хотите решить?"
- "Кто ваша целевая аудитория? Сколько человек планируете охватить?"
- "Где будет реализован проект? В каком городе/регионе?"
"""

# Вшить в промпт к Haiku
```

**Тест:**
- Запустить вопрос без Qdrant
- Проверить что Haiku генерирует нормальные вопросы
- Latency должен быть ещё меньше (~1.5s)

---

### Phase 3: Optimize prompts for Haiku (1 час)

**Задача:** Переписать промпты под Haiku (короче, конкретнее)

**Принципы для Haiku:**
- ✅ Короткие четкие инструкции
- ✅ Конкретные примеры
- ✅ Без философии
- ✅ Структурированные задачи

**Пример нового промпта:**
```python
prompt = f"""
Ты интервьюер для грантовых заявок. Помогаешь собрать 13 полей анкеты.

{REFERENCE_POINTS_STRUCTURE}

ЧТО УЖЕ СОБРАНО:
{collected_fields_summary}

ЧТО ЕЩЁ НУЖНО:
{missing_fields_list}

ПОСЛЕДНИЙ ОТВЕТ ПОЛЬЗОВАТЕЛЯ:
"{user_answer}"

ИНСТРУКЦИЯ:
1. Если ответ неполный/неясный → переспроси конкретно (что именно уточнить)
2. Если ответ противоречит предыдущим → мягко укажи на противоречие
3. Если ответ полон → перейди к следующему полю из списка "Что ещё нужно"
4. Будь кратким, конкретным, вежливым
5. Не философствуй - помогай собрать факты

Задай следующий вопрос (одну фразу, без нумерации):
"""
```

**Сравнение:**
- Старый промпт с Sonnet: ~2000 токенов (с примерами из Qdrant)
- Новый промпт с Haiku: ~500 токенов (статичная структура)

**Экономия:** -75% tokens, -75% cost, -50% latency

---

### Phase 4: Testing (1 час)

**E2E Test:**
```python
# Использовать ту же анкету Екатерины Максимовой
# test_real_anketa_e2e.py

# Метрики:
- Total time: должно быть ~40-50s (было 108s)
- Latency per question: 1.5-2s (было 5-8s)
- Quality: субъективная оценка вопросов
```

**Unit Tests:**
```python
# test_haiku_question_generation.py

def test_haiku_generates_relevant_question():
    """Проверить что Haiku генерирует релевантный вопрос"""

def test_haiku_handles_short_answers():
    """Проверить что Haiku переспрашивает на короткие ответы"""

def test_haiku_performance():
    """Проверить latency < 2.5s"""
```

**Acceptance Criteria:**
- ✅ Latency < 2.5s per question
- ✅ E2E test проходит без ошибок
- ✅ Quality вопросов приемлемая (subjective)
- ✅ User happy ("не медленновато!")

---

## ⚠️ Риски и митигация

### Риск 1: Haiku может быть "глупее" чем Sonnet

**Вероятность:** Средняя (30%)

**Проявление:**
- Вопросы менее умные
- Не ловит противоречия
- Не адаптируется к контексту

**Mitigation:**
1. **A/B Test:** Запустить 5 интервью с Haiku, оценить quality
2. **Fallback:** Если quality недостаточна:
   - Haiku для simple questions (80% случаев)
   - Sonnet для complex reasoning (20% случаев)
   - Automatic routing по сложности

### Риск 2: Потеря примеров из Qdrant ухудшит качество

**Вероятность:** Низкая (20%)

**Проявление:**
- Вопросы шаблонные
- Не учитывают best practices

**Mitigation:**
1. Взять топ-10 лучших примеров из Qdrant
2. Вшить в промпт статически
3. Haiku увидит паттерны без semantic search

### Риск 3: Регрессия в production

**Вероятность:** Низкая (10%)

**Mitigation:**
1. Полное E2E тестирование перед деплоем
2. Canary deployment (50% traffic)
3. Rollback plan готов

---

## 🔄 Rollback Plan

**Если что-то пошло не так:**

```bash
# Git rollback
git revert <commit_hash>

# Deploy
./deploy_to_production.sh

# Downtime: ~3 seconds
```

**Критерии для rollback:**
- Latency > 5s (хуже чем было)
- Error rate > 5%
- User complaints
- Quality явно хуже

---

## 📊 Success Metrics

### Performance:
- ✅ Latency per question: 1.5-2s (target)
- ✅ E2E interview: 40-50s total (было 108s)
- ✅ Cost per interview: -90%

### Quality:
- ✅ Questions relevant (subjective)
- ✅ Detects short/gibberish answers
- ✅ Completes interview successfully
- ✅ Audit score ≥ 8/10

### Business:
- ✅ User satisfaction: "быстро!"
- ✅ Completion rate ≥ 90%
- ✅ No increase in dropout rate

---

## 🗂️ Файлы для изменения

### Core:
```
C:\SnowWhiteAI\GrantService\agents\reference_points\
├── adaptive_question_generator.py
│   ├── Изменить: LLM_MODEL = "haiku"
│   ├── Убрать: _get_fpg_context() из hot path
│   └── Добавить: REFERENCE_POINTS_STRUCTURE
```

### Tests:
```
C:\SnowWhiteAI\GrantService\tests\
├── integration\
│   └── test_haiku_question_generation.py (new)
└── e2e\
    └── test_real_anketa_haiku.py (modify existing)
```

### Documentation:
```
C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\Iteration_27_Haiku_Optimization\
├── 00_Plan.md (этот файл)
├── 01_Implementation_Report.md (после Phase 1-3)
├── 02_Test_Results.md (после Phase 4)
└── 03_Final_Report.md (после деплоя)
```

---

## 💰 ROI Analysis

### Cost Savings:
```
Baseline (Sonnet):
- 10 questions per interview
- $0.02 per question
- Total: $0.20 per interview
- 100 interviews/month = $20/month

After Haiku:
- 10 questions per interview
- $0.002 per question
- Total: $0.02 per interview
- 100 interviews/month = $2/month

SAVINGS: $18/month = $216/year
```

### Time Savings (User):
```
Baseline:
- 10 questions × 8s = 80s waiting
- User perception: "медленновато"

After Haiku:
- 10 questions × 2s = 20s waiting
- User perception: "быстро!"

IMPROVEMENT: -75% perceived latency
```

### Development Time:
```
Investment: 4 hours
ROI: Infinite (improved UX, lower costs forever)
```

---

## 🎯 Next Steps

### Immediate:
1. Прочитать этот план
2. Обсудить с командой
3. Решить: делать или не делать?

### If GO:
1. Создать ветку `iteration-27-haiku`
2. Phase 1: Switch to Haiku (1h)
3. Phase 2: Remove Qdrant (1h)
4. Phase 3: Optimize prompts (1h)
5. Phase 4: Testing (1h)
6. Deploy to production

### If NO-GO:
1. Alternative: Question Prefetching (Iteration 27 original plan)
2. Keep Sonnet, но генерировать следующий вопрос в фоне

---

## 📚 References

**Related Documents:**
- `ITERATION_26.3_COMPLETE_SUMMARY.md` - Текущее состояние
- `Architecture_Analysis_Question_Generation.md` - Текущая архитектура
- `Strategy/00_Methodology/CLAUDE-SKILLS-METHODOLOGY.md` - Принцип "200 строк вместо 5000"

**User Feedback:**
> "супер мега!!! технология работает"
> "медленновато вопросы ответы идут"
> "можно как то кэшировать на опережение?"

**Decision:** Haiku + Simple Architecture вместо Prefetching

---

## 💡 Философия итерации

**Принцип Cradle OS:**
> "200 строк вместо 5000"

**Применение:**
- Убираем сложность (Qdrant search)
- Упрощаем модель (Haiku вместо Sonnet)
- Статичная структура вместо динамического поиска
- Результат: проще, быстрее, дешевле

**Инсайт:**
> "Интервьюер - это не философ, это консультант-сборщик данных"

Ему не нужен Sonnet. Ему нужна скорость и структура.

---

**Статус:** READY TO START
**Приоритет:** HIGH
**Время:** 4 hours
**Риск:** LOW-MEDIUM
**ROI:** EXCELLENT

**Следующий шаг:** Обсудить срочный вопрос, потом вернуться к этому плану! 🚀

---

**Создано:** 2025-10-23
**Автор:** Claude Code AI Assistant
**Версия:** 1.0
**Статус:** PLANNED
