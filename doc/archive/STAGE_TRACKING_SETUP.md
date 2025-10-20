# Stage Tracking System - Setup Guide

## Overview
Система отслеживания прохождения заявок через воронку агентов с единым tracking ID.

## Архитектура

### Tracking ID Format
```
ANK-20251004-theperipherals-014
```
- **ANK** - Anketa prefix
- **20251004** - Date (YYYYMMDD)
- **theperipherals** - Username
- **014** - Sequential number

### Agents Pipeline
```
📝 Interviewer → ✅ Auditor → 🔍 Researcher → ✍️ Writer → 🔎 Reviewer → 🎉 Completed
```

## Database Changes

### Migration 006: Stage Tracking
File: `database/migrations/006_add_stage_tracking.sql`

**Sessions table** - новые поля:
- `current_stage VARCHAR(50)` - текущий этап (interviewer, auditor, researcher, writer, reviewer)
- `agents_passed TEXT[]` - массив пройденных агентов
- `stage_history JSONB` - история переходов с timestamp
- `stage_updated_at TIMESTAMP` - когда обновлялся stage

**Grant_applications table**:
- `anketa_id VARCHAR(50)` - FK к sessions.anketa_id
- `current_stage VARCHAR(50)` - текущий stage
- `agents_passed TEXT[]` - пройденные агенты

**Grants table**:
- `current_stage VARCHAR(50)` - reviewer or completed
- `agents_passed TEXT[]` - все пройденные агенты
- `review_score INTEGER` - оценка рецензента (1-10)
- `review_feedback TEXT` - заключение рецензента
- `final_status VARCHAR(30)` - approved, needs_revision, rejected

### Helper Functions
- `update_session_stage(anketa_id, new_stage)` - обновить stage и записать в history
- `get_stage_progress(anketa_id)` - получить полную информацию о прогрессе

## Python Module

### Stage Tracker
File: `web-admin/utils/stage_tracker.py`

**Functions:**
```python
from utils.stage_tracker import (
    format_stage_badge,              # Полный badge со всеми стадиями
    format_stage_progress_compact,   # Компактный формат для списков
    get_stage_emoji,                 # Emoji для стадии
    get_stage_name,                  # Название стадии
    get_stage_progress,              # Прогресс в %
    update_stage,                    # Обновить stage в БД
    get_stage_info,                  # Полная информация о stage
    get_next_stage,                  # Следующая стадия
    get_previous_stage               # Предыдущая стадия
)
```

**Usage Example:**
```python
# Get stage info
stage_info = get_stage_info(execute_query, 'ANK-20251004-user-014')
# Returns: {
#   'anketa_id': 'ANK-20251004-user-014',
#   'current_stage': 'researcher',
#   'agents_passed': ['interviewer', 'auditor'],
#   'progress_percentage': 40,
#   'stage_emoji': '🔍',
#   'badge': '✅ INT → ✅ AUD → 🔄 RES → ⏸️ WR → ⏸️ REW'
# }

# Update stage
update_stage(execute_query, 'ANK-20251004-user-014', 'writer')
```

## UI Integration

### Main Agents Page
**Location:** `web-admin/pages/🤖_Агенты.py`

**Features:**
1. **Stage Funnel Summary** (top of page)
   - Metrics by stage (сколько заявок на каждом этапе)
   - Recent applications with stage badges
   - Example: `📋 ANK-20251004-user-014 [🔍 RES - 40%]`

2. **Interviewer Tab → Интервью**
   - Shows anketa_id in title
   - Format: `📝 📋 ANK-20251004-user-014 - @username (15/24 ответов)`

3. **Other Agent Tabs**
   - Similar display with anketa_id
   - Can track same application across all agents

## Apply Migration

### Option 1: Via psql (Recommended)
```bash
# Windows
cd C:\SnowWhiteAI\GrantService
set PGPASSWORD=1256
psql -U postgres -d grantservice -f database\migrations\006_add_stage_tracking.sql
```

### Option 2: Via Python script
```bash
python apply_migration_006.py
```

### Option 3: Manual SQL
Open pgAdmin or psql and execute:
```sql
\i C:/SnowWhiteAI/GrantService/database/migrations/006_add_stage_tracking.sql
```

## Verification

After applying migration, verify:

```sql
-- Check sessions have stage fields
SELECT anketa_id, current_stage, agents_passed, stage_updated_at
FROM sessions
WHERE anketa_id IS NOT NULL
LIMIT 5;

-- Test helper function
SELECT * FROM get_stage_progress('ANK-20251004-theperipherals-014');

-- Update stage test
SELECT update_session_stage('ANK-20251004-theperipherals-014', 'researcher');
```

## Next Steps

1. **Apply Migration** - Run SQL migration on database
2. **Restart Streamlit** - Refresh browser to see changes
3. **Test UI** - Check stage funnel summary on Agents page
4. **Agent Integration** - Update agent code to call `update_stage()` after completion

## Benefits

✅ **Unified Tracking** - Single anketa_id через весь pipeline
✅ **Progress Visibility** - See where each application is in the funnel
✅ **Stage History** - Complete audit trail of stage transitions
✅ **Easy Filtering** - Query by current_stage or agents_passed
✅ **UI Integration** - Automatic badges and progress indicators

## Future Enhancements

- [ ] Auto-advance stages when agent completes work
- [ ] Stage timeout alerts (e.g., stuck in researcher for 3+ days)
- [ ] Funnel analytics (conversion rates, bottlenecks)
- [ ] Stage-based notifications to users
- [ ] Rollback/retry failed stages

---

**Version:** 1.0
**Created:** 2025-10-07
**Author:** Grant Architect + Claude Code
