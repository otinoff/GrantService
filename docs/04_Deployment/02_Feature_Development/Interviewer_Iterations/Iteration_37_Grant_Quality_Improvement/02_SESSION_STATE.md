# Iteration 37 - Session State Snapshot

**Created:** 2025-10-25
**Time:** Phase 2 Start
**Status:** 🚀 READY TO IMPLEMENT

---

## 📍 WHERE WE ARE

**Iteration:** 37 - Grant Quality Improvement
**Phase:** Phase 2 Complete - Starting Testing
**Methodology:** Project Evolution (Метаболизм - small commits)

---

## ✅ COMPLETED

### Phase 1: Diagnostic (1 hour) ✅
- [x] Analyzed `create_test_anketa()` - 19 fields, good data
- [x] Analyzed AuditorAgent prompts - expects `{application_text}` (TEXT not JSON)
- [x] Found ProductionWriter - works correctly, generates 30K formatted text
- [x] **ROOT CAUSE IDENTIFIED:**
  - AuditorAgent expects formatted grant TEXT
  - Currently receives raw anketa JSON
  - Result: 0.0/10 scores

**Diagnostic Report:** `01_DIAGNOSTIC_FINDINGS.md`

---

## 🎯 CURRENT TASK

### Phase 2: Two-Stage Quality Control Implementation

**Decision made:** Implement full quality pipeline with TWO gates:

```
GATE 1: AnketaValidator (validates INPUT - anketa JSON)
  ↓
ProductionWriter (generates grant text)
  ↓
GATE 2: AuditorAgent (audits OUTPUT - grant TEXT)
```

**Why Two-Stage:**
- ✅ Validate input (don't process garbage)
- ✅ Audit output (verify quality)
- ✅ Collect RL data at both stages
- ✅ Proper architecture per user request

---

## 📋 IMPLEMENTATION PLAN

### Commit 1: Create AnketaValidator (40 min) ✅ DONE
**File:** `C:\SnowWhiteAI\GrantService\agents\anketa_validator.py`
**Lines:** ~100
**What:**
- New class `AnketaValidator`
- Validates anketa JSON before generation
- LLM prompt designed for JSON input
- Returns: score, issues, can_proceed

**Spec:**
```python
class AnketaValidator:
    """
    Validates anketa data quality BEFORE generation

    Checks:
    - Required fields exist
    - Sufficient detail (min lengths)
    - Coherence (LLM evaluation)
    """

    async def validate(self, anketa_data: dict) -> dict:
        """
        Returns: {
            'valid': bool,
            'score': 0-10,
            'issues': [list of problems],
            'can_proceed': bool,
            'recommendations': [what to improve]
        }
        """
```

---

### Commit 2: Integrate Stage 1 - /audit_anketa (20 min) ✅ DONE
**File:** `telegram-bot/handlers/anketa_management_handler.py`
**Lines:** ~30
**What:**
- Use AnketaValidator instead of AuditorAgent
- Check anketa JSON quality
- Return validation results

---

### Commit 3: Integrate Stage 2 - /generate_grant (30 min) ✅ DONE
**File:** `telegram-bot/handlers/grant_handler.py`
**Lines:** ~40
**What:**
- Stage 1: AnketaValidator (check input)
- Generate: ProductionWriter (create text)
- Stage 2: AuditorAgent (audit output)
- Both gates must pass

---

### Commit 4: Testing (20 min) ← **NOW**
**What:**
- Test /audit_anketa with test data
- Test /generate_grant full pipeline
- Verify scores ≥7.0/10
- Log both gates data

---

## 📊 EXPECTED RESULTS

**Before (Current):**
- Audit score: 0.0/10
- Generation blocked
- No quality control

**After (Implementation):**
- Gate 1 (AnketaValidator): 7-8/10 on good anketa
- Gate 2 (AuditorAgent): 7-9/10 on generated text
- Quality data logged for RL
- Garbage blocked at input

---

## 🗂️ FILES TO CREATE/MODIFY

**Create:**
1. `C:\SnowWhiteAI\GrantService\agents\anketa_validator.py` (new, ~100 lines)

**Modify:**
2. `telegram-bot/handlers/anketa_management_handler.py` (~30 lines)
3. `telegram-bot/handlers/grant_handler.py` (~40 lines)

**Total:** ~170 lines (Метаболизм ✅)

---

## 💾 KEY DECISIONS

1. **Two-Stage QA** - User requested quality checks at each pipeline stage
2. **AnketaValidator** - New agent for JSON validation (separate from AuditorAgent)
3. **AuditorAgent** - Keep for TEXT audit (after generation)
4. **RL Data** - Log results from both gates
5. **Methodology** - 4 small commits (Метаболизм)

---

## 🔗 RELATED FILES

**Diagnostic:**
- `01_DIAGNOSTIC_FINDINGS.md` - Root cause analysis

**Code to reference:**
- `agents/auditor_agent.py` - Example agent structure
- `agents/production_writer.py` - How to use LLM
- `shared/llm/unified_llm_client.py` - LLM client

**Database:**
- `agent_prompts` table - Where to store AnketaValidator prompts

---

## 🚀 NEXT IMMEDIATE STEP

**CREATE:** `agents/anketa_validator.py`

**Structure:**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AnketaValidator - Validates anketa data quality before generation

ITERATION 37: Two-Stage Quality Control
GATE 1: Validate INPUT (anketa JSON)

Purpose: Prevent garbage from entering generation pipeline
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add paths
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))

from shared.llm.unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)


class AnketaValidator:
    """
    Validates anketa JSON data quality

    Checks:
    1. Required fields present
    2. Sufficient detail (min lengths)
    3. Coherence and completeness (LLM check)

    Returns validation score and recommendations
    """

    # Required fields
    REQUIRED_FIELDS = [
        'project_name',
        'problem',
        'solution',
        'goals',
        'budget'
    ]

    # Minimum lengths (characters)
    MIN_LENGTHS = {
        'problem': 200,
        'solution': 150,
        'project_name': 10
    }

    def __init__(self, llm_provider: str = 'gigachat', db=None):
        self.llm_provider = llm_provider
        self.db = db
        self.llm_client = UnifiedLLMClient(provider=llm_provider)

    async def validate(self, anketa_data: Dict) -> Dict[str, Any]:
        """
        Validate anketa data quality

        Args:
            anketa_data: Anketa JSON dict

        Returns:
            {
                'valid': bool,
                'score': 0-10,
                'issues': [...],
                'can_proceed': bool,
                'recommendations': [...]
            }
        """
        # 1. Check required fields
        # 2. Check minimum lengths
        # 3. LLM coherence check
        # 4. Calculate score
        # 5. Return results
```

---

## ⏱️ TIME TRACKING

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| Phase 1: Diagnostic | 1h | 1h | ✅ Complete |
| Phase 2: Implementation | 2h | - | 🚀 Starting |
| - Commit 1: AnketaValidator | 40min | - | ← NOW |
| - Commit 2: /audit_anketa | 20min | - | Pending |
| - Commit 3: /generate_grant | 30min | - | Pending |
| - Commit 4: Testing | 20min | - | Pending |

---

## 🔄 RECOVERY INSTRUCTIONS

**If session crashes, continue from:**

1. Read this file: `02_SESSION_STATE.md`
2. Read diagnostic: `01_DIAGNOSTIC_FINDINGS.md`
3. Check current task: **Commit 1 - Create AnketaValidator**
4. Resume: Create `agents/anketa_validator.py`

**Context:**
- Working on Iteration 37
- Phase 1 complete (diagnostic done)
- Root cause: AuditorAgent expects TEXT, gets JSON
- Solution: Two-stage QA (AnketaValidator for JSON + AuditorAgent for TEXT)
- Currently: About to create AnketaValidator

---

**Saved:** 2025-10-25
**Iteration:** 37 - Grant Quality Improvement
**Phase:** 2 (Implementation Start)
**Next:** Create `anketa_validator.py`
