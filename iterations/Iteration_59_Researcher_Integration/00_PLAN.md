# Iteration 59: Researcher Integration in Pipeline

**Date:** 2025-10-28
**Status:** 🚧 IN PROGRESS
**Priority:** P1 - HIGH (Feature Enhancement)
**Related:** Iteration_52 (Interactive Pipeline), test_researcher_claude_code.py ✅

---

## 📋 Overview

**Goal:** Интегрировать ResearcherAgent в полный pipeline между Auditor и Writer

**User Impact:**
- ✅ Гранты усилятся реальной статистикой и данными
- ✅ Поиск через Claude Code WebSearch (gov.ru, rosstat.gov.ru)
- ✅ Writer получает research_results для создания более качественных заявок

**Current Pipeline:**
```
Interview → Audit → Writer → Review
```

**New Pipeline:**
```
Interview → Audit → 🆕 Research → Writer → Review
```

---

## 🔍 Root Cause Analysis

### Current State

**File:** `telegram-bot/handlers/interactive_pipeline_handler.py`

**После Audit (строка 325-346):**
```python
# Создать кнопку "Начать написание гранта"
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton(
        "✍️ Начать написание гранта",
        callback_data=f"start_grant:anketa:{anketa_id}"
    )]
])
```

**В Writer (строка 441):**
```python
grant_content = await writer.write(anketa_data=anketa_data)
# ← Получает только anketa_data, БЕЗ research_results!
```

### What's Missing

1. **No Research Step:** Нет сбора данных между Audit и Writer
2. **No Claude Code WebSearch:** Не используется $200 подписка для поиска
3. **No Statistics:** Гранты пишутся без реальной статистики и источников
4. **Weak Arguments:** Аргументация слабая без данных

---

## 🎯 Solution

### Architecture

**New Pipeline Flow:**
```
1. Interviewer → собирает анкету
   ↓
2. Auditor → проверяет анкету
   ↓
3. 🆕 Researcher → ищет данные через Claude Code WebSearch
   ├─ Input: user_answers (проблема, ЦА, решение)
   ├─ Process: WebSearch по gov.ru, rosstat.gov.ru
   ├─ Output: research_results (статистика, цитаты, источники)
   └─ Save: research_results в БД
   ↓
4. Writer → пишет грант
   ├─ Input: anketa_data + research_results
   └─ Output: grant усиленный реальными данными
   ↓
5. Reviewer → проверяет грант
```

### Changes Required

**1. File:** `telegram-bot/handlers/interactive_pipeline_handler.py`

**Change 1:** Изменить кнопку после Audit (строка 325-346)

```python
# BEFORE:
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton(
        "✍️ Начать написание гранта",
        callback_data=f"start_grant:anketa:{anketa_id}"
    )]
])

# AFTER:
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton(
        "🔍 Начать исследование",  # ← NEW BUTTON!
        callback_data=f"start_research:anketa:{anketa_id}"
    )]
])
```

**Change 2:** Добавить новый метод `handle_start_research()`

```python
async def handle_start_research(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Callback handler для кнопки "Начать исследование"

    Actions:
    1. Получает anketa_data из БД
    2. Запускает ResearcherAgent с Claude Code WebSearch
    3. Сохраняет research_results в БД (session.research_data)
    4. Отправляет краткий отчет пользователю
    5. Показывает кнопку "Начать написание гранта"
    """
    query = update.callback_query
    user_id = query.from_user.id

    # Parse: "start_research:anketa:ANK123"
    callback_data = query.data
    parts = callback_data.split(':')

    if len(parts) != 3 or parts[0] != 'start_research':
        await query.answer("❌ Неверный формат данных", show_alert=True)
        return

    anketa_id = parts[2]

    logger.info(f"[PIPELINE] User {user_id} clicked 'Start Research' for {anketa_id}")

    await query.answer("⏳ Запускаем исследование...")

    try:
        # Получить данные анкеты
        anketa_session = self.db.get_session_by_anketa_id(anketa_id)
        if not anketa_session:
            await query.message.reply_text("❌ Анкета не найдена")
            return

        # Парсим interview_data
        import json
        if isinstance(anketa_session['interview_data'], str):
            anketa_data = json.loads(anketa_session['interview_data'])
        else:
            anketa_data = anketa_session['interview_data']

        # Отправить сообщение о начале исследования
        await query.message.reply_text(
            "🔍 Запускаю исследование...\n\n"
            "Поиск данных через Claude Code WebSearch:\n"
            "• Статистика по теме проекта\n"
            "• Данные о целевой аудитории\n"
            "• Официальные источники (Росстат, министерства)\n\n"
            "⏱️ Это займет 30-60 секунд."
        )

        # Создать ResearcherAgent
        from agents.researcher_agent import ResearcherAgent

        researcher = ResearcherAgent(db=self.db, llm_provider='claude_code')

        # Формируем input для Researcher
        research_input = {
            'description': anketa_data.get('project_description', ''),
            'problem': anketa_data.get('problem', ''),
            'target_audience': anketa_data.get('target_audience', ''),
            'llm_provider': 'claude_code',
            'session_id': anketa_session.get('id')
        }

        # Запускаем исследование
        research_result = await researcher.research_grant_async(research_input)

        if not research_result or research_result.get('status') != 'success':
            await query.message.reply_text(
                "❌ Не удалось выполнить исследование"
            )
            return

        # Сохранить research_results в БД
        self.db.update_session_field(
            anketa_id,
            'research_data',
            json.dumps(research_result, ensure_ascii=False)
        )

        # Отправить краткий отчет
        sources_count = len(research_result.get('sources', []))
        results_count = research_result.get('total_results', 0)

        await query.message.reply_text(
            f"✅ Исследование завершено!\n\n"
            f"📊 Найдено источников: {sources_count}\n"
            f"📄 Результатов поиска: {results_count}\n\n"
            f"Данные будут использованы при написании гранта."
        )

        # Создать кнопку "Начать написание гранта"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✍️ Начать написание гранта",
                callback_data=f"start_grant:anketa:{anketa_id}"
            )]
        ])

        await query.message.reply_text(
            text=(
                "📝 Готовы создать грантовую заявку?\n\n"
                "Генератор создаст заявку С ИСПОЛЬЗОВАНИЕМ найденных данных:\n"
                "• Описание проблемы с реальной статистикой\n"
                "• Обоснование с официальными источниками\n"
                "• Цели и показатели на основе данных\n\n"
                "⏱️ Это займет 2-3 минуты.\n\n"
                "Нажмите кнопку когда будете готовы:"
            ),
            reply_markup=keyboard
        )

        logger.info(f"[OK] Research complete for user {user_id}")

    except Exception as e:
        logger.error(f"[ERROR] Failed to run research: {e}")
        import traceback
        traceback.print_exc()
        await query.message.reply_text(
            "❌ Произошла ошибка при исследовании. Попробуйте позже."
        )
```

**Change 3:** Изменить `handle_start_grant()` чтобы получать research_results

```python
# BEFORE (строка 441):
grant_content = await writer.write(anketa_data=anketa_data)

# AFTER:
# Получить research_results из БД
research_data = anketa_session.get('research_data')
if research_data:
    if isinstance(research_data, str):
        research_results = json.loads(research_data)
    else:
        research_results = research_data
else:
    research_results = {}

# Передать в Writer
grant_content = await writer.write(
    anketa_data=anketa_data,
    research_results=research_results  # ← ADD THIS!
)
```

**2. File:** `agents/production_writer.py`

**Check:** Verify `write()` method signature accepts `research_results`

```python
async def write(
    self,
    anketa_data: Dict[str, Any],
    research_results: Optional[Dict[str, Any]] = None  # ← Should exist
) -> str:
    """
    Write grant using anketa_data AND research_results
    """
    # ...
```

If not, add support for research_results parameter.

**3. Database Schema**

**Add field to sessions table:**
```sql
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS research_data JSONB;
```

Or if using TEXT:
```sql
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS research_data TEXT;
```

---

## 🧪 Testing

### Test 1: ResearcherAgent with Claude Code WebSearch

**File:** `test_researcher_claude_code.py` ✅ ALREADY CREATED AND PASSED

**Result:**
```
[SUCCESS] Claude Code WebSearch is WORKING!
Provider: claude_code
Total results: 3
Sources: rosstat.gov.ru
```

### Test 2: Full Pipeline Integration Test

**Create:** `test_pipeline_with_researcher.py`

```python
async def test_full_pipeline_with_researcher():
    """Test Interview → Audit → Research → Writer → Review"""

    # 1. Create mock anketa
    anketa_data = {
        'project_description': 'Проект для детей с инвалидностью',
        'problem': 'Нехватка адаптивных программ',
        'target_audience': 'Дети с инвалидностью 7-14 лет'
    }

    # 2. Run Researcher
    researcher = ResearcherAgent(db=None, llm_provider='claude_code')
    research_result = await researcher.research_grant_async({
        'description': anketa_data['project_description'],
        'problem': anketa_data['problem']
    })

    assert research_result['status'] == 'success'
    assert len(research_result['sources']) > 0
    print(f"[OK] Research found {len(research_result['sources'])} sources")

    # 3. Run Writer WITH research_results
    writer = ProductionWriter(...)
    grant = await writer.write(
        anketa_data=anketa_data,
        research_results=research_result
    )

    assert grant is not None
    assert len(grant) > 1000

    # 4. Check grant contains research data
    assert 'Росстат' in grant or 'статистика' in grant.lower()
    print(f"[OK] Grant includes research data")
```

### Test 3: Button Flow Test

**Manual Testing:**
1. Complete anketa → see "Начать аудит" button
2. Click "Начать аудит" → see audit.txt + "Начать исследование" button
3. Click "Начать исследование" → see research summary + "Начать написание гранта" button
4. Click "Начать написание гранта" → see grant.txt with research data
5. Click "Сделать ревью" → see review.txt

---

## 📦 Deployment

### Step 1: Update Database Schema

```bash
ssh root@5.35.88.251
cd /var/GrantService

# Add research_data column
PGPASSWORD=root psql -h localhost -U postgres -d grantservice -c "
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS research_data TEXT;
"
```

### Step 2: Update Code

```bash
# Local testing first
python test_researcher_claude_code.py  # ✅ PASSED
python test_pipeline_with_researcher.py  # TODO

# Commit changes
git add telegram-bot/handlers/interactive_pipeline_handler.py
git add agents/production_writer.py  # If changed
git add iterations/Iteration_59_Researcher_Integration/
git add test_pipeline_with_researcher.py

git commit -m "feat(pipeline): Add Researcher step between Audit and Writer

- Add handle_start_research() in pipeline handler
- Researcher uses Claude Code WebSearch for data gathering
- Research results saved in sessions.research_data
- Writer receives research_results for enhanced grant generation
- New button flow: Audit → Research → Grant → Review

Benefits:
- Grants now include real statistics from Rosstat, gov.ru
- Better argumentation with official sources
- Uses $200 Claude Code subscription effectively

Related: Iteration_59
Tested: test_researcher_claude_code.py PASSED"

git push origin master
```

### Step 3: Deploy to Production

```bash
ssh root@5.35.88.251
cd /var/GrantService

git pull origin master

# Restart bot
systemctl restart grantservice-bot
systemctl status grantservice-bot

# Check logs
journalctl -u grantservice-bot -f
```

### Step 4: User Verification

**Ask user to:**
1. Complete new anketa
2. Click through: Audit → Research → Grant
3. Verify grant contains statistics/sources
4. Check research summary shows sources count

---

## 🎓 Lessons Learned

### Pattern: Pipeline Extension

**Problem:** Adding new step in middle of existing pipeline

**Solution:**
1. Change previous step's button (Audit → Research button)
2. Add new handler (handle_start_research)
3. Save intermediate results in DB (research_data)
4. Update next step to use new data (Writer gets research_results)

**Code Pattern:**
```python
# Previous step button
keyboard = InlineKeyboardMarkup([[
    InlineKeyboardButton("New Step", callback_data=f"start_new:{id}")
]])

# New handler
async def handle_start_new(...):
    result = await agent.execute()
    db.save_result(result)
    show_next_button()

# Next step updated
data = db.get_result()
await next_agent.execute(previous_data, new_data)
```

### Add to GRANTSERVICE-LESSONS-LEARNED.md

```markdown
## Pipeline Extension Pattern (Iteration_59)

**Problem:** Need to add Researcher between Audit and Writer

**Solution:**
1. Button Flow: Change Audit button to Research, Research button to Grant
2. Data Flow: Save research_results in DB, pass to Writer
3. Agent Integration: Researcher uses Claude Code WebSearch
4. Progressive Enhancement: Writer enhanced without breaking existing logic

**Result:**
- Grants improved with real statistics
- Claude Code WebSearch utilized ($200 subscription)
- No breaking changes to existing pipeline
```

---

## 📊 Expected Results

### Before (Without Researcher)

**Grant Content:**
```
ПРОБЛЕМА:
По нашим данным, дети с инвалидностью сталкиваются с нехваткой программ.

(generic statements, no statistics)
```

### After (With Researcher)

**Grant Content:**
```
ПРОБЛЕМА:
По данным Росстата за 2024 год, в России проживает более 700 тысяч детей
с инвалидностью [1]. При этом, согласно исследованию Минтруда, только
23% из них имеют доступ к адаптивным образовательным программам [2].

Источники:
[1] https://rosstat.gov.ru/folder/13964
[2] https://mintrud.gov.ru/...

(specific statistics with official sources)
```

---

## 📝 Files

### Created
- `iterations/Iteration_59_Researcher_Integration/00_PLAN.md` (this file)
- `test_researcher_claude_code.py` ✅ (already exists and passes)
- `test_pipeline_with_researcher.py` (TODO)

### Modified
- `telegram-bot/handlers/interactive_pipeline_handler.py` (add handle_start_research, change buttons)
- `agents/production_writer.py` (verify research_results support)
- Database schema (add sessions.research_data column)

### Related
- `shared/llm/websearch_router.py` - Claude Code WebSearch (v2.0)
- `agents/researcher_agent.py` - ResearcherAgent with claude_code provider

---

## ✅ Checklist

**Planning**
- [x] Created 00_PLAN.md
- [x] Tested Claude Code WebSearch (PASSED)
- [ ] Check ProductionWriter.write() signature
- [ ] Design database schema change

**Implementation**
- [ ] Add research_data column to sessions table
- [ ] Add handle_start_research() method
- [ ] Change Audit button to show Research
- [ ] Update Writer to receive research_results
- [ ] Test locally

**Testing**
- [x] test_researcher_claude_code.py (PASSED)
- [ ] test_pipeline_with_researcher.py
- [ ] Manual button flow test

**Deployment**
- [ ] Update database schema on production
- [ ] Commit and push changes
- [ ] Deploy to production
- [ ] Restart bot
- [ ] User verification

**Documentation**
- [ ] Update GRANTSERVICE-LESSONS-LEARNED.md
- [ ] Create SUCCESS.md
- [ ] Mark Iteration_59 as complete

---

**Created by:** Claude Code
**Date:** 2025-10-28
**Time:** 01:30 MSK
**Related:** Iteration_52 (Interactive Pipeline), test_researcher_claude_code.py ✅
