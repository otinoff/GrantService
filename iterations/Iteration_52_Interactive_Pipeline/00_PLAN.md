# Iteration 52: Interactive Step-by-Step Grant Pipeline

**Status:** 🚧 IN PROGRESS
**Started:** 2025-10-26
**Priority:** HIGH (UX improvement)
**Estimated Time:** 6 hours (1 day)
**Methodology:** Project Evolution + Testing Methodology

---

## 🎯 Goal

Transform the grant generation flow from "black box" to transparent, interactive step-by-step process with file checkpoints at each stage.

**Current Flow (Iteration 51):**
```
User completes anketa → [waiting 10 minutes...] → Grant appears
```

**Target Flow (Iteration 52):**
```
1. User completes anketa → receives anketa.txt + button "Начать аудит"
2. User clicks button → [audit runs] → receives audit.txt + button "Начать написание гранта"
3. User clicks button → [grant generation] → receives grant.txt + button "Сделать ревью"
4. User clicks button → [review runs] → receives review.txt + "Готово!"
```

---

## 📊 Benefits

1. **Transparency:** User sees each step
2. **Control:** Can pause between stages
3. **Artifacts:** All intermediate files saved
4. **Confidence:** Progress visibility
5. **Debug:** Easier to identify where problems occur

---

## 📋 Scope

### In Scope ✅

1. **File Generators:**
   - `generate_anketa_txt()` - readable anketa summary
   - `generate_audit_txt()` - audit results
   - `generate_grant_txt()` - full grant application
   - `generate_review_txt()` - review results

2. **Telegram Bot Updates:**
   - After anketa: send file + "Начать аудит" button
   - After audit: send file + "Начать написание гранта" button
   - After grant: send file + "Сделать ревью" button
   - After review: send file + "Готово" message

3. **State Machine:**
   - Track user progress (anketa_completed → audit_requested → grant_requested → review_requested)
   - Store in database: `user_pipeline_state`

4. **Tests:**
   - Unit tests for file generators
   - Integration tests for bot handlers
   - E2E test for full pipeline

### Out of Scope ❌

- UI/UX design changes (keep current layout)
- PDF generation (use .txt files for now)
- Progress bar (future iteration)
- Multi-language support (Russian only)
- Cancel/restart flow (future iteration)

---

## 📐 Architecture

### State Machine

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       v
┌──────────────────┐
│ ANKETA_COMPLETED │ → Send anketa.txt + button "Начать аудит"
└──────┬───────────┘
       │ User clicks button
       v
┌──────────────────┐
│ AUDIT_REQUESTED  │ → Run audit → Send audit.txt + button "Начать написание гранта"
└──────┬───────────┘
       │ User clicks button
       v
┌──────────────────┐
│ GRANT_REQUESTED  │ → Run writer → Send grant.txt + button "Сделать ревью"
└──────┬───────────┘
       │ User clicks button
       v
┌──────────────────┐
│ REVIEW_REQUESTED │ → Run reviewer → Send review.txt + "Готово!"
└──────┬───────────┘
       │
       v
┌──────────────┐
│   COMPLETE   │
└──────────────┘
```

### File Formats

**anketa.txt:**
```
ЗАПОЛНЕННАЯ АНКЕТА

Название проекта: [project_name]
Организация: [organization]
Описание: [description]
...

Дата заполнения: [timestamp]
ID анкеты: [anketa_id]
```

**audit.txt:**
```
РЕЗУЛЬТАТЫ АУДИТА АНКЕТЫ

ID анкеты: [anketa_id]
Дата аудита: [timestamp]

ОЦЕНКА: [score]/10

ПРОБЛЕМЫ:
1. [issue_1]
2. [issue_2]

РЕКОМЕНДАЦИИ:
1. [recommendation_1]
2. [recommendation_2]

Статус: [approved/needs_work]
```

**grant.txt:**
```
ГРАНТОВАЯ ЗАЯВКА

Проект: [project_name]
Дата создания: [timestamp]

=== ПРОБЛЕМА ===
[problem_text]

=== РЕШЕНИЕ ===
[solution_text]

=== БЮДЖЕТ ===
[budget_text]

...

Всего символов: [count]
ID заявки: [grant_id]
```

**review.txt:**
```
РЕЗУЛЬТАТЫ РЕВЬЮ ГРАНТОВОЙ ЗАЯВКИ

ID заявки: [grant_id]
Дата ревью: [timestamp]

ОБЩАЯ ОЦЕНКА: [score]/10

СИЛЬНЫЕ СТОРОНЫ:
1. [strength_1]
2. [strength_2]

СЛАБЫЕ СТОРОНЫ:
1. [weakness_1]
2. [weakness_2]

РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:
1. [recommendation_1]
2. [recommendation_2]

Статус: [approved/rejected]
```

---

## 📋 Tasks Breakdown

### Phase 1: Preparation (30 min) ✅ IN PROGRESS

**Tasks:**
- [x] Create iteration folder
- [x] Write 00_PLAN.md
- [ ] Define button callback data format
- [ ] Plan database schema changes

**Deliverables:**
- [x] This plan document
- [ ] Callback data spec
- [ ] DB migration plan

---

### Phase 2: File Generators (1 hour)

**Module:** `shared/telegram/file_generators.py`

**Functions:**
```python
def generate_anketa_txt(anketa: Anketa) -> str:
    """Generate readable anketa summary as text file"""
    pass

def generate_audit_txt(audit_result: AuditResult) -> str:
    """Generate audit results as text file"""
    pass

def generate_grant_txt(grant: Grant) -> str:
    """Generate full grant application as text file"""
    pass

def generate_review_txt(review: ReviewResult) -> str:
    """Generate review results as text file"""
    pass
```

**Tests:** `tests/unit/test_file_generators.py`
```python
def test_generate_anketa_txt():
    """Unit: anketa → text format"""
    pass

def test_generate_audit_txt():
    """Unit: audit → text format"""
    pass

# ... etc
```

**Acceptance Criteria:**
- ✅ All 4 generators implemented
- ✅ Unit tests pass
- ✅ Text files are human-readable (not JSON dumps!)
- ✅ Include metadata (ID, timestamp)

**Commit:** `feat(iteration-52): Add file generators for pipeline checkpoints`

---

### Phase 3: Telegram Bot - Anketa Handler (45 min)

**File:** `telegram-bot/handlers/anketa_handler.py`

**Changes:**
```python
async def on_anketa_complete(user_id: int, anketa_id: int):
    """Called when user finishes anketa"""

    # Generate file
    anketa = db.get_anketa(anketa_id)
    txt_content = generate_anketa_txt(anketa)

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(txt_content)
        file_path = f.name

    # Send file
    await bot.send_document(
        chat_id=user_id,
        document=open(file_path, 'rb'),
        filename=f"anketa_{anketa_id}.txt",
        caption="✅ Анкета заполнена!\n\nГотовы начать аудит?"
    )

    # Send button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Начать аудит", callback_data=f"start_audit:{anketa_id}")]
    ])
    await bot.send_message(user_id, "Нажмите кнопку, когда будете готовы:", reply_markup=keyboard)

    # Update state
    db.update_user_state(user_id, "ANKETA_COMPLETED")

    # Cleanup temp file
    os.unlink(file_path)
```

**Tests:** `tests/integration/test_anketa_handler.py`

**Acceptance Criteria:**
- ✅ File sent as Telegram document
- ✅ Button displayed
- ✅ State updated in DB

**Commit:** `feat(iteration-52): Add anketa → audit button with file checkpoint`

---

### Phase 4: Telegram Bot - Audit Handler (45 min)

**File:** `telegram-bot/handlers/audit_handler.py`

**Handler:**
```python
@dp.callback_query_handler(lambda c: c.data.startswith('start_audit:'))
async def handle_start_audit_button(callback_query: CallbackQuery):
    """Handle 'Начать аудит' button click"""

    # Parse callback data
    anketa_id = int(callback_query.data.split(':')[1])
    user_id = callback_query.from_user.id

    # Check state
    state = db.get_user_state(user_id)
    if state != "ANKETA_COMPLETED":
        await callback_query.answer("Сначала завершите анкету!")
        return

    # Acknowledge button click
    await callback_query.answer("Запускаем аудит...")

    # Run audit
    await bot.send_message(user_id, "⏳ Запускаю аудит анкеты...")

    auditor = AuditorAgent(db=db)
    audit_result = await auditor.audit_anketa_async(anketa_id)

    # Generate file
    txt_content = generate_audit_txt(audit_result)

    # Send file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(txt_content)
        file_path = f.name

    await bot.send_document(
        chat_id=user_id,
        document=open(file_path, 'rb'),
        filename=f"audit_{anketa_id}.txt",
        caption=f"✅ Аудит завершен!\n\nОценка: {audit_result.score}/10"
    )

    # Send button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Начать написание гранта", callback_data=f"start_grant:{anketa_id}")]
    ])
    await bot.send_message(user_id, "Готовы создать грант?", reply_markup=keyboard)

    # Update state
    db.update_user_state(user_id, "AUDIT_COMPLETED")

    os.unlink(file_path)
```

**Tests:** `tests/integration/test_audit_handler.py`

**Acceptance Criteria:**
- ✅ Button callback handled
- ✅ Audit runs
- ✅ File sent
- ✅ Next button displayed

**Commit:** `feat(iteration-52): Add audit → grant button handler`

---

### Phase 5: Telegram Bot - Grant Handler (45 min)

**File:** `telegram-bot/handlers/grant_handler.py`

**Handler:**
```python
@dp.callback_query_handler(lambda c: c.data.startswith('start_grant:'))
async def handle_start_grant_button(callback_query: CallbackQuery):
    """Handle 'Начать написание гранта' button click"""

    anketa_id = int(callback_query.data.split(':')[1])
    user_id = callback_query.from_user.id

    # Check state
    state = db.get_user_state(user_id)
    if state != "AUDIT_COMPLETED":
        await callback_query.answer("Сначала завершите аудит!")
        return

    await callback_query.answer("Запускаем генерацию гранта...")

    # Run writer
    await bot.send_message(user_id, "⏳ Генерирую грантовую заявку... (это займет 2-3 минуты)")

    writer = ProductionWriter(db=db)
    grant = await writer.generate_grant_async(anketa_id)

    # Generate file
    txt_content = generate_grant_txt(grant)

    # Send file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(txt_content)
        file_path = f.name

    await bot.send_document(
        chat_id=user_id,
        document=open(file_path, 'rb'),
        filename=f"grant_{grant.id}.txt",
        caption=f"✅ Грант создан!\n\nРазмер: {len(grant.content)} символов"
    )

    # Send button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Сделать ревью", callback_data=f"start_review:{grant.id}")]
    ])
    await bot.send_message(user_id, "Хотите проверить качество?", reply_markup=keyboard)

    # Update state
    db.update_user_state(user_id, "GRANT_COMPLETED")

    os.unlink(file_path)
```

**Tests:** `tests/integration/test_grant_handler.py`

**Acceptance Criteria:**
- ✅ Grant generation works
- ✅ File sent
- ✅ Review button displayed

**Commit:** `feat(iteration-52): Add grant → review button handler`

---

### Phase 6: Telegram Bot - Review Handler (45 min)

**File:** `telegram-bot/handlers/review_handler.py`

**Handler:**
```python
@dp.callback_query_handler(lambda c: c.data.startswith('start_review:'))
async def handle_start_review_button(callback_query: CallbackQuery):
    """Handle 'Сделать ревью' button click"""

    grant_id = int(callback_query.data.split(':')[1])
    user_id = callback_query.from_user.id

    # Check state
    state = db.get_user_state(user_id)
    if state != "GRANT_COMPLETED":
        await callback_query.answer("Сначала создайте грант!")
        return

    await callback_query.answer("Запускаем ревью...")

    # Run reviewer
    await bot.send_message(user_id, "⏳ Анализирую качество гранта...")

    reviewer = ReviewerAgent(db=db)
    review = await reviewer.review_grant_async(grant_id)

    # Generate file
    txt_content = generate_review_txt(review)

    # Send file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(txt_content)
        file_path = f.name

    await bot.send_document(
        chat_id=user_id,
        document=open(file_path, 'rb'),
        filename=f"review_{grant_id}.txt",
        caption=f"✅ Ревью завершено!\n\nОценка: {review.score}/10"
    )

    # Final message (no more buttons)
    await bot.send_message(
        user_id,
        "🎉 Процесс завершен!\n\nВсе файлы сохранены. Вы можете скачать их из истории чата."
    )

    # Update state
    db.update_user_state(user_id, "PIPELINE_COMPLETE")

    os.unlink(file_path)
```

**Tests:** `tests/integration/test_review_handler.py`

**Acceptance Criteria:**
- ✅ Review runs
- ✅ File sent
- ✅ Final message displayed
- ✅ State = COMPLETE

**Commit:** `feat(iteration-52): Add grant → review handler (final step)`

---

### Phase 7: State Machine (1 hour)

**Files:**
- `telegram-bot/state_machine.py` (update)
- Database migration

**States:**
```python
class PipelineState(Enum):
    IDLE = "idle"
    ANKETA_IN_PROGRESS = "anketa_in_progress"
    ANKETA_COMPLETED = "anketa_completed"
    AUDIT_COMPLETED = "audit_completed"
    GRANT_COMPLETED = "grant_completed"
    PIPELINE_COMPLETE = "pipeline_complete"
```

**Database:**
```sql
-- Migration: add user_pipeline_state column
ALTER TABLE users
ADD COLUMN pipeline_state VARCHAR(50) DEFAULT 'idle';

CREATE INDEX idx_users_pipeline_state ON users(pipeline_state);
```

**Functions:**
```python
def get_user_state(user_id: int) -> PipelineState:
    """Get current pipeline state for user"""
    pass

def update_user_state(user_id: int, new_state: PipelineState):
    """Update user's pipeline state"""
    pass

def can_transition(current: PipelineState, target: PipelineState) -> bool:
    """Validate state transition"""
    pass
```

**Tests:** `tests/unit/test_state_machine.py`

**Acceptance Criteria:**
- ✅ States defined
- ✅ DB migration applied
- ✅ Transition validation works
- ✅ Unit tests pass

**Commit:** `feat(iteration-52): Add state machine for interactive pipeline`

---

### Phase 8: Integration Tests (1 hour)

**File:** `tests/integration/test_interactive_pipeline.py`

**Tests:**
```python
@pytest.mark.integration
async def test_anketa_to_audit_flow(test_bot, test_db):
    """Integration: Anketa → Audit button works"""

    # Complete anketa
    anketa = await complete_test_anketa(test_bot, user_id=123)

    # Check file sent
    messages = await test_bot.get_messages(123)
    last_doc = messages[-1].document
    assert "anketa" in last_doc.file_name

    # Check button
    last_msg = messages[-1]
    assert "Начать аудит" in str(last_msg.reply_markup)

    # Click button
    await test_bot.click_button(123, "start_audit")

    # Check audit ran
    messages = await test_bot.get_messages(123)
    last_doc = messages[-1].document
    assert "audit" in last_doc.file_name

@pytest.mark.integration
async def test_full_pipeline_integration(test_bot, test_db):
    """Integration: Full pipeline anketa → audit → grant → review"""

    # Step 1: Anketa
    anketa = await complete_test_anketa(test_bot, user_id=123)
    await test_bot.click_button(123, "start_audit")

    # Step 2: Audit
    await asyncio.sleep(5)  # Wait for audit
    await test_bot.click_button(123, "start_grant")

    # Step 3: Grant
    await asyncio.sleep(60)  # Wait for grant (longer)
    await test_bot.click_button(123, "start_review")

    # Step 4: Review
    await asyncio.sleep(10)  # Wait for review

    # Check state
    state = test_db.get_user_state(123)
    assert state == "PIPELINE_COMPLETE"

    # Check all 4 files sent
    messages = await test_bot.get_messages(123)
    docs = [m.document for m in messages if m.document]
    assert len(docs) == 4
    assert any("anketa" in d.file_name for d in docs)
    assert any("audit" in d.file_name for d in docs)
    assert any("grant" in d.file_name for d in docs)
    assert any("review" in d.file_name for d in docs)
```

**Acceptance Criteria:**
- ✅ All integration tests pass
- ✅ Files sent correctly
- ✅ Buttons work
- ✅ State transitions validated

**Commit:** `test(iteration-52): Add integration tests for interactive pipeline`

---

### Phase 9: E2E Test (1 hour)

**File:** `tests/e2e/test_full_interactive_flow.py`

**Test:**
```python
@pytest.mark.e2e
@pytest.mark.slow
async def test_user_completes_full_pipeline_with_real_agents(
    real_bot,
    production_db,
    gigachat_client
):
    """E2E: Real user completing full pipeline with pauses"""

    user_id = 999999  # Test user

    # Phase 1: Complete anketa (real InterviewerAgent)
    from telegram_bot.handlers.anketa_handler import start_anketa_flow
    await start_anketa_flow(user_id)

    # Simulate user answering all questions
    test_answers = load_test_anketa_responses("high_quality")
    for question, answer in test_answers.items():
        await real_bot.send_message(user_id, answer)
        await asyncio.sleep(2)

    # Check: File + button received
    messages = await real_bot.get_chat_history(user_id, limit=5)
    assert any("anketa" in msg.document.file_name for msg in messages if msg.document)
    assert any("Начать аудит" in msg.text for msg in messages)

    # Phase 2: User clicks audit (REAL AuditorAgent)
    await real_bot.click_inline_button(user_id, "start_audit")
    await asyncio.sleep(30)  # Real audit takes time

    messages = await real_bot.get_chat_history(user_id, limit=5)
    assert any("audit" in msg.document.file_name for msg in messages if msg.document)

    # Phase 3: User clicks grant (REAL WriterAgent)
    await real_bot.click_inline_button(user_id, "start_grant")
    await asyncio.sleep(180)  # Real grant takes 2-3 minutes

    messages = await real_bot.get_chat_history(user_id, limit=5)
    assert any("grant" in msg.document.file_name for msg in messages if msg.document)

    # Phase 4: User clicks review (REAL ReviewerAgent)
    await real_bot.click_inline_button(user_id, "start_review")
    await asyncio.sleep(30)  # Real review takes time

    messages = await real_bot.get_chat_history(user_id, limit=5)
    assert any("review" in msg.document.file_name for msg in messages if msg.document)
    assert any("завершен" in msg.text.lower() for msg in messages)

    # Verify final state
    state = production_db.get_user_state(user_id)
    assert state == "PIPELINE_COMPLETE"

    print("✅ E2E Test PASSED: Full interactive pipeline with real agents")
```

**Acceptance Criteria:**
- ✅ E2E test passes with REAL agents (not mocks!)
- ✅ All 4 files generated
- ✅ All 3 buttons work
- ✅ User can pause between steps

**Commit:** `test(iteration-52): Add E2E test for full interactive pipeline`

---

### Phase 10: Documentation (30 min)

**Files:**
- `iterations/Iteration_52_Interactive_Pipeline/SUCCESS.md`
- `iterations/Iteration_52_Interactive_Pipeline/FLOW_DIAGRAM.md`
- Update `CLAUDE.md` (current iteration = 52)

**Content:**
- Summary of changes
- User flow diagram
- Screenshots (if possible)
- Metrics collected
- Known issues
- Future improvements

**Commit:** `docs(iteration-52): Complete iteration documentation`

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **File delivery** | 100% | All 4 files sent in tests |
| **Button functionality** | 100% | All 3 buttons trigger next step |
| **State transitions** | 100% valid | No invalid state changes |
| **Test coverage** | 80%+ | pytest --cov |
| **E2E test pass** | ✅ | Real agents complete full flow |
| **User feedback** | Positive | Manual testing with real users |

---

## 🚀 Deployment Plan

### Prerequisites
- ✅ Iteration 51 complete
- ✅ All tests pass
- ✅ DB migration ready

### Steps
1. Apply DB migration (add `pipeline_state` column)
2. Deploy updated bot code
3. Test with internal user (manual)
4. Enable for 5% users (canary)
5. Monitor for 24 hours
6. Expand to 100% users

### Rollback Plan
- Keep old bot code as backup
- Can disable buttons with feature flag: `INTERACTIVE_PIPELINE_ENABLED=false`
- Revert to Iteration 51 if issues

---

## 🐛 Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Buttons don't work | HIGH | Thorough integration tests |
| Files too large | MEDIUM | Compress or limit content |
| User confusion | MEDIUM | Clear button labels + messages |
| State machine bugs | HIGH | Unit tests for all transitions |
| Telegram API rate limits | LOW | Add delays between messages |

---

## 📝 Notes

- Use `.txt` files (not PDF) for simplicity
- Russian language only for now
- No "cancel" or "restart" flow (future iteration)
- No multi-user support yet (one pipeline per user)

---

## ✅ Definition of Done

- [ ] All 11 todos completed (see todo list)
- [ ] All unit tests pass (file generators, state machine)
- [ ] All integration tests pass (bot handlers)
- [ ] E2E test passes (full pipeline with real agents)
- [ ] Code reviewed
- [ ] Documentation complete
- [ ] DB migration applied
- [ ] Deployed to staging
- [ ] Tested manually
- [ ] Git committed

---

**Owner:** Claude Code
**Reviewer:** TBD
**Status:** 🚧 IN PROGRESS

**When to mark complete:** After all tasks done + tests pass + deployed
