# Phase 2: Edge Cases Testing

**Duration:** 1 day
**Priority:** 🔴 HIGH
**Prerequisites:** Phase 1 integration tests passing
**Status:** Ready to Execute

---

## 🎯 Goal

**Test error scenarios and edge cases with AUTOMATED tests (not manual!).**

**Why AFTER Phase 1:**
- Phase 1 validated happy path works
- Phase 2 validates error handling works
- All automated - no manual intervention

---

## 📋 Edge Cases to Cover

### 1. Double-Click Prevention
**Scenario:** User clicks "Начать аудит" button twice in quick succession

**Expected:** Second click ignored, show "Already in progress" message

**Why important:** Prevents duplicate agent runs, wasted resources

### 2. Timeout Handling
**Scenario:** Agent takes >5 minutes (simulated with sleep)

**Expected:** Show timeout message, allow retry, don't crash

**Why important:** Prevents users waiting forever

### 3. Agent Error Handling
**Scenario:** Agent returns error or exception

**Expected:** Show user-friendly error, log technical details, allow retry

**Why important:** Graceful degradation, no crashes

### 4. Concurrent Users
**Scenario:** 2 different users start pipeline simultaneously

**Expected:** Both work independently, no conflicts, correct data isolation

**Why important:** Multi-user support, production readiness

### 5. Invalid State Transitions
**Scenario:** User tries to skip steps (e.g., click "Review" before "Audit")

**Expected:** Show "Invalid step" message, don't allow

**Why important:** Enforce correct workflow, data integrity

### 6. Database Unavailable
**Scenario:** Database connection fails or times out

**Expected:** Show error, don't crash, retry on next request

**Why important:** Resilience, graceful degradation

---

## 📝 Test Implementation

### File: `tests/integration/test_pipeline_edge_cases.py`

```python
"""
Edge case tests for interactive pipeline.

All tests are AUTOMATED - no manual Telegram interaction!
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from telegram import Update, CallbackQuery, User, Message, Chat
from telegram.ext import ContextTypes

# Production imports
from telegram-bot.handlers.interactive_pipeline_handler import InteractivePipelineHandler
from shared.state_machine.pipeline_state import PipelineState


# ============================================================
# Test 1: Double-Click Prevention
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_double_click_prevention(test_db, test_anketa, mock_telegram_update):
    """
    Test that clicking button twice doesn't start duplicate processes.

    Flow:
    1. User clicks "Начать аудит"
    2. State changes to AUDIT_IN_PROGRESS
    3. User clicks again (impatient)
    4. Second click rejected with message
    5. Only one audit runs
    """

    # Arrange: Create pipeline handler
    handler = InteractivePipelineHandler(db=test_db)

    # Create mock callback query
    callback_query = create_mock_callback_query(
        user_id=12345,
        data=f"start_audit:anketa:{test_anketa['id']}"
    )

    # Mock update and context
    update = create_mock_update(callback_query=callback_query)
    context = create_mock_context()

    # Act: First click (should start audit)
    await handler.handle_start_audit(update, context)

    # Assert: State changed to in_progress
    user_state = test_db.get_user_pipeline_state(12345)
    assert user_state == PipelineState.AUDIT_IN_PROGRESS.value

    # Act: Second click (should be rejected)
    await handler.handle_start_audit(update, context)

    # Assert: Got "already in progress" message
    assert callback_query.answer.called
    answer_call = callback_query.answer.call_args
    assert 'already' in answer_call[1]['text'].lower() or \
           'уже' in answer_call[1]['text'].lower()

    # Assert: Only ONE audit started (check audit count in DB)
    audits = test_db.get_audits_for_anketa(test_anketa['id'])
    assert len(audits) == 1, "Should only start one audit"

    print("✅ Double-click prevention test passed!")


# ============================================================
# Test 2: Timeout Handling
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_timeout_handling(test_db, test_anketa, mock_telegram_update):
    """
    Test that long-running agent is handled gracefully.

    Flow:
    1. User starts audit
    2. Agent takes >5 minutes (simulated)
    3. User sees timeout message
    4. Can retry
    """

    # Arrange: Create pipeline handler
    handler = InteractivePipelineHandler(db=test_db)

    # Mock agent that takes forever
    with patch('agents.auditor_agent.AuditorAgent.audit_application_async') as mock_audit:
        # Simulate 6-minute delay (over timeout threshold)
        async def slow_audit(*args, **kwargs):
            await asyncio.sleep(360)  # 6 minutes
            return {'status': 'success'}

        mock_audit.side_effect = slow_audit

        # Create mock callback
        callback_query = create_mock_callback_query(
            user_id=12345,
            data=f"start_audit:anketa:{test_anketa['id']}"
        )
        update = create_mock_update(callback_query=callback_query)
        context = create_mock_context()

        # Act: Start audit (will timeout)
        # Note: In real implementation, use asyncio.wait_for with timeout=300 (5 min)
        try:
            await asyncio.wait_for(
                handler.handle_start_audit(update, context),
                timeout=5.0  # 5 seconds for test (simulate 5 min)
            )
        except asyncio.TimeoutError:
            # Expected: timeout occurred
            pass

        # Assert: User received timeout message
        # Check that message was sent
        assert context.bot.send_message.called
        message_call = context.bot.send_message.call_args
        assert 'timeout' in message_call[1]['text'].lower() or \
               'время' in message_call[1]['text'].lower()

        # Assert: State allows retry
        user_state = test_db.get_user_pipeline_state(12345)
        assert user_state != PipelineState.AUDIT_IN_PROGRESS.value  # Not stuck!

    print("✅ Timeout handling test passed!")


# ============================================================
# Test 3: Agent Error Handling
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_error_handling(test_db, test_anketa, mock_telegram_update):
    """
    Test that agent errors are handled gracefully.

    Flow:
    1. User starts audit
    2. AuditorAgent raises exception
    3. User sees friendly error message (not technical traceback)
    4. Error logged with details
    5. Can retry
    """

    # Arrange: Create pipeline handler
    handler = InteractivePipelineHandler(db=test_db)

    # Mock agent that raises error
    with patch('agents.auditor_agent.AuditorAgent.audit_application_async') as mock_audit:
        # Simulate agent error
        mock_audit.side_effect = Exception("GigaChat API rate limit exceeded")

        callback_query = create_mock_callback_query(
            user_id=12345,
            data=f"start_audit:anketa:{test_anketa['id']}"
        )
        update = create_mock_update(callback_query=callback_query)
        context = create_mock_context()

        # Act: Start audit (will fail)
        await handler.handle_start_audit(update, context)

        # Assert: User received friendly error message (NOT technical)
        assert context.bot.send_message.called
        message_call = context.bot.send_message.call_args
        error_text = message_call[1]['text']

        # Should NOT contain technical details
        assert 'Exception' not in error_text
        assert 'Traceback' not in error_text
        assert 'rate limit' not in error_text  # Technical detail

        # Should contain user-friendly message
        assert 'ошибка' in error_text.lower() or 'error' in error_text.lower()
        assert 'попробуйте' in error_text.lower() or 'retry' in error_text.lower()

        # Assert: Error logged with technical details
        # (Check logs or error tracking system)

        # Assert: State allows retry (not stuck in error state)
        user_state = test_db.get_user_pipeline_state(12345)
        assert user_state == PipelineState.ANKETA_COMPLETED.value  # Back to start of audit

    print("✅ Agent error handling test passed!")


# ============================================================
# Test 4: Concurrent Users
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_users(test_db, mock_telegram_update):
    """
    Test that multiple users can use pipeline simultaneously.

    Flow:
    1. User A starts audit for anketa_A
    2. User B starts audit for anketa_B (simultaneously)
    3. Both complete successfully
    4. No data leakage (A doesn't see B's data)
    """

    # Arrange: Create pipeline handler
    handler = InteractivePipelineHandler(db=test_db)

    # Create two test anketas
    anketa_a = {'id': 'anketa_user_a', 'user_id': 1001, 'project_name': 'Project A'}
    anketa_b = {'id': 'anketa_user_b', 'user_id': 1002, 'project_name': 'Project B'}

    test_db.save_anketa(anketa_a)
    test_db.save_anketa(anketa_b)

    # Mock GigaChat to return different results for each user
    with patch('agents.auditor_agent.AuditorAgent.audit_application_async') as mock_audit:
        # Return different scores for each anketa
        async def audit_with_id(input_data):
            anketa_id = input_data['anketa_id']
            if anketa_id == 'anketa_user_a':
                return {'status': 'success', 'audit_details': {'score': 7.5, 'strengths': ['A']}}
            else:
                return {'status': 'success', 'audit_details': {'score': 8.5, 'strengths': ['B']}}

        mock_audit.side_effect = audit_with_id

        # Create callbacks for both users
        callback_a = create_mock_callback_query(user_id=1001, data=f"start_audit:anketa:anketa_user_a")
        callback_b = create_mock_callback_query(user_id=1002, data=f"start_audit:anketa:anketa_user_b")

        update_a = create_mock_update(callback_query=callback_a)
        update_b = create_mock_update(callback_query=callback_b)

        context_a = create_mock_context()
        context_b = create_mock_context()

        # Act: Start both audits concurrently
        await asyncio.gather(
            handler.handle_start_audit(update_a, context_a),
            handler.handle_start_audit(update_b, context_b)
        )

        # Assert: Both completed successfully
        audit_a = test_db.get_audit_by_anketa_id('anketa_user_a')
        audit_b = test_db.get_audit_by_anketa_id('anketa_user_b')

        assert audit_a is not None
        assert audit_b is not None

        # Assert: No data leakage (each got their own data)
        assert audit_a['score'] == 7.5
        assert audit_b['score'] == 8.5
        assert audit_a['strengths'] == ['A']
        assert audit_b['strengths'] == ['B']

        # Assert: States are independent
        state_a = test_db.get_user_pipeline_state(1001)
        state_b = test_db.get_user_pipeline_state(1002)
        assert state_a == PipelineState.AUDIT_COMPLETED.value
        assert state_b == PipelineState.AUDIT_COMPLETED.value

    print("✅ Concurrent users test passed!")


# ============================================================
# Test 5: Invalid State Transitions
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_state_transitions(test_db, test_anketa, mock_telegram_update):
    """
    Test that users can't skip pipeline steps.

    Flow:
    1. User has completed anketa (state: ANKETA_COMPLETED)
    2. User tries to click "Начать ревью" (skip audit + grant)
    3. Should be rejected with "Invalid step" message
    4. State unchanged
    """

    # Arrange: Create pipeline handler
    handler = InteractivePipelineHandler(db=test_db)

    # Set user state to ANKETA_COMPLETED (just finished interview)
    test_db.set_user_pipeline_state(12345, PipelineState.ANKETA_COMPLETED.value)

    # Create callback for REVIEW (skipping audit and grant!)
    callback_query = create_mock_callback_query(
        user_id=12345,
        data=f"start_review:grant:test_grant_id"
    )
    update = create_mock_update(callback_query=callback_query)
    context = create_mock_context()

    # Act: Try to start review (invalid transition)
    await handler.handle_start_review(update, context)

    # Assert: Got "invalid step" message
    assert callback_query.answer.called or context.bot.send_message.called

    if callback_query.answer.called:
        answer_call = callback_query.answer.call_args
        message = answer_call[1]['text']
    else:
        message_call = context.bot.send_message.call_args
        message = message_call[1]['text']

    assert 'invalid' in message.lower() or \
           'неверн' in message.lower() or \
           'сначала' in message.lower()

    # Assert: State unchanged (still at ANKETA_COMPLETED)
    user_state = test_db.get_user_pipeline_state(12345)
    assert user_state == PipelineState.ANKETA_COMPLETED.value

    # Assert: Review NOT started
    reviews = test_db.get_reviews_for_user(12345)
    assert len(reviews) == 0

    print("✅ Invalid state transitions test passed!")


# ============================================================
# Test 6: Database Unavailable
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_unavailable(test_anketa, mock_telegram_update):
    """
    Test graceful handling when database is unavailable.

    Flow:
    1. User starts audit
    2. Database connection fails
    3. User sees error message (not crash)
    4. System logs error
    5. Can retry when DB back
    """

    # Arrange: Create pipeline handler with broken DB
    with patch('data.database.DatabaseClient') as MockDB:
        # Mock DB that raises connection error
        mock_db = MockDB.return_value
        mock_db.get_user_pipeline_state.side_effect = Exception("Connection refused")
        mock_db.save_audit.side_effect = Exception("Connection refused")

        handler = InteractivePipelineHandler(db=mock_db)

        callback_query = create_mock_callback_query(
            user_id=12345,
            data=f"start_audit:anketa:{test_anketa['id']}"
        )
        update = create_mock_update(callback_query=callback_query)
        context = create_mock_context()

        # Act: Try to start audit (DB fails)
        try:
            await handler.handle_start_audit(update, context)
        except Exception:
            # Should NOT raise exception to user!
            pytest.fail("Handler should not raise exception, should handle gracefully")

        # Assert: User received error message
        assert context.bot.send_message.called
        message_call = context.bot.send_message.call_args
        error_text = message_call[1]['text']

        # Should contain user-friendly message
        assert 'ошибка' in error_text.lower() or 'error' in error_text.lower()
        assert 'база' in error_text.lower() or 'database' in error_text.lower()
        assert 'попробуйте' in error_text.lower() or 'retry' in error_text.lower()

        # Should NOT crash bot
        # (If we got here, test passed - bot didn't crash)

    print("✅ Database unavailable test passed!")


# ============================================================
# Helper Functions
# ============================================================

def create_mock_callback_query(user_id: int, data: str):
    """Create mock Telegram CallbackQuery"""
    query = AsyncMock(spec=CallbackQuery)
    query.data = data
    query.from_user = User(id=user_id, first_name="Test", is_bot=False)
    query.message = Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=user_id, type="private")
    )
    query.answer = AsyncMock()
    return query


def create_mock_update(callback_query=None):
    """Create mock Telegram Update"""
    update = MagicMock(spec=Update)
    update.callback_query = callback_query
    update.effective_user = callback_query.from_user if callback_query else None
    update.effective_chat = callback_query.message.chat if callback_query else None
    return update


def create_mock_context():
    """Create mock Telegram Context"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_document = AsyncMock()
    return context
```

---

## 🚀 Running Tests

### Run All Edge Case Tests
```bash
pytest tests/integration/test_pipeline_edge_cases.py -v

# Expected output:
# test_double_click_prevention PASSED
# test_timeout_handling PASSED
# test_agent_error_handling PASSED
# test_concurrent_users PASSED
# test_invalid_state_transitions PASSED
# test_database_unavailable PASSED
# 6 passed in 12.3s
```

### Run Single Test
```bash
pytest tests/integration/test_pipeline_edge_cases.py::test_double_click_prevention -v -s
```

### Run Without Slow Tests
```bash
pytest tests/integration/test_pipeline_edge_cases.py -v -m "not slow"
# Skips timeout test (takes 5+ seconds)
```

---

## ✅ Success Criteria

**All tests must pass:**
- [ ] `test_double_click_prevention` - PASS
- [ ] `test_timeout_handling` - PASS
- [ ] `test_agent_error_handling` - PASS
- [ ] `test_concurrent_users` - PASS
- [ ] `test_invalid_state_transitions` - PASS
- [ ] `test_database_unavailable` - PASS

**Quality checks:**
- [ ] All tests deterministic (not flaky)
- [ ] Error messages user-friendly (no technical details leaked)
- [ ] No crashes (all errors handled gracefully)
- [ ] Logs contain technical details (for debugging)

---

## 🐛 Common Issues

### Issue: Mock not working
```python
# BAD: Mock after import
from agents.auditor_agent import AuditorAgent
mock_audit = Mock()  # Too late!

# GOOD: Patch before use
with patch('agents.auditor_agent.AuditorAgent') as MockAuditor:
    # Now mock works
```

### Issue: Async mock not awaitable
```python
# BAD: Regular Mock
mock_func = Mock(return_value="result")
await mock_func()  # Error!

# GOOD: AsyncMock
mock_func = AsyncMock(return_value="result")
await mock_func()  # Works!
```

---

## 📊 Next Steps

**When Phase 2 complete (all 6 tests passing):**

1. ✅ Commit progress:
   ```bash
   git add tests/integration/test_pipeline_edge_cases.py
   git commit -m "test(iteration-53): Add Phase 2 edge case tests"
   ```

2. ✅ Update iteration log:
   ```markdown
   ## Phase 2 Complete ✅
   - All 6 edge case tests passing
   - Error handling validated
   - Ready for Phase 3
   ```

3. ✅ Move to Phase 3: Config Refactoring
   - Read `PHASE_3_CONFIG_REFACTORING.md`
   - Start unified config implementation

---

🤖 Generated with Claude Code - Phase 2 Edge Cases Guide
