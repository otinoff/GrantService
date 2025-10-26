# State Machine - Interactive Grant Pipeline

## States

```python
class PipelineState(Enum):
    """Pipeline states for user journey"""

    IDLE = "idle"
    # User is not in any pipeline

    ANKETA_IN_PROGRESS = "anketa_in_progress"
    # User is filling out anketa via InterviewerAgent

    ANKETA_COMPLETED = "anketa_completed"
    # Anketa filled, waiting for user to click "Начать аудит"

    AUDIT_COMPLETED = "audit_completed"
    # Audit finished, waiting for user to click "Начать написание гранта"

    GRANT_COMPLETED = "grant_completed"
    # Grant generated, waiting for user to click "Сделать ревью"

    PIPELINE_COMPLETE = "pipeline_complete"
    # All stages done, user can start new pipeline or exit
```

---

## State Diagram

```
┌─────────────┐
│    IDLE     │ ← User not in pipeline
└──────┬──────┘
       │ /start command
       │ InterviewerAgent begins
       v
┌──────────────────────┐
│ ANKETA_IN_PROGRESS   │ ← User answering questions
└──────┬───────────────┘
       │ All questions answered
       │ Send anketa.txt + button "Начать аудит"
       v
┌──────────────────────┐
│ ANKETA_COMPLETED     │ ← Waiting for user action
└──────┬───────────────┘
       │ User clicks "Начать аудит" button
       │ AuditorAgent runs
       │ Send audit.txt + button "Начать написание гранта"
       v
┌──────────────────────┐
│ AUDIT_COMPLETED      │ ← Waiting for user action
└──────┬───────────────┘
       │ User clicks "Начать написание гранта" button
       │ ProductionWriter runs (2-3 min)
       │ Send grant.txt + button "Сделать ревью"
       v
┌──────────────────────┐
│ GRANT_COMPLETED      │ ← Waiting for user action
└──────┬───────────────┘
       │ User clicks "Сделать ревью" button
       │ ReviewerAgent runs
       │ Send review.txt + "Готово!" message
       v
┌──────────────────────┐
│ PIPELINE_COMPLETE    │ ← All done!
└──────┬───────────────┘
       │ User can /start again
       v
┌─────────────┐
│    IDLE     │ ← Back to start
└─────────────┘
```

---

## State Transitions

### Valid Transitions

| From | To | Trigger |
|------|------|---------|
| IDLE | ANKETA_IN_PROGRESS | User sends /start |
| ANKETA_IN_PROGRESS | ANKETA_COMPLETED | InterviewerAgent finishes |
| ANKETA_COMPLETED | AUDIT_COMPLETED | User clicks "Начать аудит" |
| AUDIT_COMPLETED | GRANT_COMPLETED | User clicks "Начать написание гранта" |
| GRANT_COMPLETED | PIPELINE_COMPLETE | User clicks "Сделать ревью" |
| PIPELINE_COMPLETE | IDLE | User sends /start (new pipeline) |

### Invalid Transitions (Rejected)

- IDLE → AUDIT_COMPLETED (must complete anketa first)
- ANKETA_COMPLETED → GRANT_COMPLETED (must run audit first)
- AUDIT_COMPLETED → PIPELINE_COMPLETE (must generate grant first)
- etc.

**Error Message:** "❌ Сначала завершите предыдущий шаг!"

---

## Implementation

### Database Storage

```sql
-- users table
pipeline_state VARCHAR(50) DEFAULT 'idle'
anketa_id_in_progress INTEGER DEFAULT NULL
pipeline_started_at TIMESTAMP DEFAULT NULL
```

### Python Code

```python
# shared/state_machine/pipeline_state.py

from enum import Enum
from typing import Optional

class PipelineState(Enum):
    IDLE = "idle"
    ANKETA_IN_PROGRESS = "anketa_in_progress"
    ANKETA_COMPLETED = "anketa_completed"
    AUDIT_COMPLETED = "audit_completed"
    GRANT_COMPLETED = "grant_completed"
    PIPELINE_COMPLETE = "pipeline_complete"


class PipelineStateMachine:
    """Manages user pipeline state transitions"""

    VALID_TRANSITIONS = {
        PipelineState.IDLE: [PipelineState.ANKETA_IN_PROGRESS],
        PipelineState.ANKETA_IN_PROGRESS: [PipelineState.ANKETA_COMPLETED],
        PipelineState.ANKETA_COMPLETED: [PipelineState.AUDIT_COMPLETED],
        PipelineState.AUDIT_COMPLETED: [PipelineState.GRANT_COMPLETED],
        PipelineState.GRANT_COMPLETED: [PipelineState.PIPELINE_COMPLETE],
        PipelineState.PIPELINE_COMPLETE: [PipelineState.IDLE],
    }

    def __init__(self, db):
        self.db = db

    def get_state(self, user_id: int) -> PipelineState:
        """Get current state for user"""
        state_str = self.db.get_user_pipeline_state(user_id)
        return PipelineState(state_str)

    def can_transition(
        self,
        user_id: int,
        target_state: PipelineState
    ) -> bool:
        """Check if transition is valid"""
        current_state = self.get_state(user_id)
        valid_targets = self.VALID_TRANSITIONS.get(current_state, [])
        return target_state in valid_targets

    def transition(
        self,
        user_id: int,
        target_state: PipelineState,
        anketa_id: Optional[int] = None
    ) -> bool:
        """Transition to new state (with validation)"""

        if not self.can_transition(user_id, target_state):
            logger.warning(
                f"Invalid state transition for user {user_id}: "
                f"{self.get_state(user_id)} → {target_state}"
            )
            return False

        # Update database
        self.db.update_user_pipeline_state(
            user_id=user_id,
            new_state=target_state.value,
            anketa_id=anketa_id
        )

        logger.info(
            f"State transition for user {user_id}: "
            f"{self.get_state(user_id)} → {target_state}"
        )

        return True
```

---

## Usage Examples

### Example 1: User clicks "Начать аудит"

```python
@dp.callback_query_handler(lambda c: c.data.startswith('start_audit:'))
async def handle_start_audit(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    anketa_id = int(callback_query.data.split(':')[2])

    # Check state
    state_machine = PipelineStateMachine(db)

    if not state_machine.can_transition(user_id, PipelineState.AUDIT_COMPLETED):
        await callback_query.answer(
            "❌ Сначала завершите анкету!",
            show_alert=True
        )
        return

    # Run audit
    auditor = AuditorAgent(db=db)
    result = await auditor.audit_anketa_async(anketa_id)

    # Send file + button
    # ...

    # Transition state
    state_machine.transition(
        user_id=user_id,
        target_state=PipelineState.AUDIT_COMPLETED,
        anketa_id=anketa_id
    )
```

### Example 2: Check if user can start grant

```python
def can_start_grant(user_id: int) -> bool:
    """Check if user is ready to generate grant"""
    state_machine = PipelineStateMachine(db)
    current_state = state_machine.get_state(user_id)
    return current_state == PipelineState.AUDIT_COMPLETED
```

---

## Edge Cases

### 1. User clicks button twice

**Problem:** User clicks "Начать аудит" twice while audit is running

**Solution:**
```python
# Add lock in database or check if audit already exists
if db.get_audit_for_anketa(anketa_id):
    await callback_query.answer("⏳ Аудит уже запущен!")
    return
```

### 2. User starts new /start while in pipeline

**Problem:** User in AUDIT_COMPLETED state, sends /start again

**Solution:**
```python
if state != PipelineState.IDLE:
    await update.message.reply_text(
        "⚠️ У вас уже есть незавершенный процесс!\n\n"
        "Завершите текущий грант или используйте /cancel чтобы начать заново."
    )
    return
```

### 3. Database connection lost during transition

**Problem:** State update fails mid-transition

**Solution:**
```python
try:
    state_machine.transition(user_id, new_state)
except DatabaseError as e:
    logger.error(f"State transition failed: {e}")
    await callback_query.answer(
        "❌ Ошибка сервера. Попробуйте позже."
    )
    # Rollback any partial work
    return
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_state_machine.py

def test_valid_transitions():
    """Test all valid state transitions"""
    sm = PipelineStateMachine(mock_db)

    assert sm.can_transition(
        PipelineState.IDLE,
        PipelineState.ANKETA_IN_PROGRESS
    )

    assert sm.can_transition(
        PipelineState.ANKETA_COMPLETED,
        PipelineState.AUDIT_COMPLETED
    )

def test_invalid_transitions():
    """Test that invalid transitions are rejected"""
    sm = PipelineStateMachine(mock_db)

    assert not sm.can_transition(
        PipelineState.IDLE,
        PipelineState.GRANT_COMPLETED
    )

    assert not sm.can_transition(
        PipelineState.ANKETA_COMPLETED,
        PipelineState.PIPELINE_COMPLETE
    )
```

### Integration Tests

```python
# tests/integration/test_state_machine.py

@pytest.mark.integration
async def test_full_pipeline_state_flow(test_db):
    """Test complete state flow with real DB"""

    user_id = 123
    sm = PipelineStateMachine(test_db)

    # Start
    assert sm.get_state(user_id) == PipelineState.IDLE

    # Transition: IDLE → ANKETA_IN_PROGRESS
    sm.transition(user_id, PipelineState.ANKETA_IN_PROGRESS, anketa_id=1)
    assert sm.get_state(user_id) == PipelineState.ANKETA_IN_PROGRESS

    # Transition: ANKETA_IN_PROGRESS → ANKETA_COMPLETED
    sm.transition(user_id, PipelineState.ANKETA_COMPLETED, anketa_id=1)
    assert sm.get_state(user_id) == PipelineState.ANKETA_COMPLETED

    # ... etc for all transitions
```

---

## Metrics to Track

1. **State distribution:** How many users in each state?
2. **Completion rate:** % users who reach PIPELINE_COMPLETE
3. **Drop-off points:** Where do users abandon pipeline?
4. **Time per stage:** How long in each state?
5. **Error rate:** How often do invalid transitions occur?

**Query Example:**
```sql
SELECT
    pipeline_state,
    COUNT(*) as user_count,
    AVG(EXTRACT(EPOCH FROM (NOW() - pipeline_started_at))) / 60 as avg_minutes
FROM users
WHERE pipeline_state != 'idle'
GROUP BY pipeline_state
ORDER BY user_count DESC;
```

---

**Status:** ✅ Design Complete
**Next Step:** Implement PipelineStateMachine class
