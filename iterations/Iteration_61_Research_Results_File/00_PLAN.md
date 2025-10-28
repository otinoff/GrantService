# Iteration 61: Research Results File Generation

**Date:** 2025-10-28 23:30 MSK
**Status:** 🔧 IN PROGRESS
**Parent:** Iteration 60 - Researcher WebSearch Fix

---

## 🎯 Goal

Add research results `.txt` file generation following project nomenclature, similar to `audit_{audit_id}.txt` and `grant_{grant_id}.txt`.

**User Request**: "нам надо файл как во всех других этапаъх" (we need a file like in all other stages)

---

## 📊 Problem

Currently research step completes but doesn't send a readable `.txt` file to user via Telegram, breaking the consistency:

```
✅ Interview → sends anketa_{anketa_id}.txt
✅ Audit → sends audit_{audit_id}.txt
❌ Research → NO FILE (just database save)
✅ Writer → sends grant_{grant_id}.txt
✅ Review → sends review_{review_id}.txt
```

---

## 📐 Nomenclature (from doc/NOMENCLATURE.md)

### Research ID Format
```
{anketa_id}-RS-{counter:03d}
```

**Example**:
```
#AN-20251011-ekaterina_maksimova-001-RS-001
```

### Research File Name
```
research_{research_id.replace('#', '')}.txt
```

**Example**:
```
research_AN-20251011-ekaterina_maksimova-001-RS-001.txt
```

---

## 📝 Implementation Plan

### Step 1: Add `generate_research_txt()` Function

**File**: `shared/telegram_utils/file_generators.py`

**Function signature**:
```python
def generate_research_txt(research_data: Dict[str, Any]) -> str:
    """
    Generate research results as human-readable text file

    Args:
        research_data: Research results from database with fields:
            - research_id: str (e.g., #AN-20251011-user-001-RS-001)
            - anketa_id: str
            - results: Dict with 'block1', 'metadata', etc.
            - created_at: datetime
            - llm_provider: str

    Returns:
        str: Formatted text content
    """
```

**Pattern** (following `generate_audit_txt()` structure):
```python
def generate_research_txt(research_data: Dict[str, Any]) -> str:
    """Generate research results as text file"""

    lines = []
    lines.append("=" * 60)
    lines.append("РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ")
    lines.append("=" * 60)
    lines.append("")

    # Metadata
    research_id = research_data.get('research_id', 'N/A')
    anketa_id = research_data.get('anketa_id', 'N/A')
    created_at = research_data.get('created_at', 'N/A')

    lines.append(f"ID исследования: {research_id}")
    lines.append(f"ID анкеты: {anketa_id}")
    lines.append(f"Дата: {created_at}")
    lines.append("")

    # Results summary
    results = research_data.get('results', {})
    metadata = results.get('metadata', {})
    sources_count = metadata.get('sources_count', 0)
    total_queries = metadata.get('total_queries', 0)

    lines.append("=" * 60)
    lines.append("СТАТИСТИКА")
    lines.append("=" * 60)
    lines.append(f"📊 Найдено источников: {sources_count}")
    lines.append(f"📄 Выполнено запросов: {total_queries}")
    lines.append("")

    # Block 1 results
    block1 = results.get('block1', {})
    queries = block1.get('queries', [])

    if queries:
        lines.append("=" * 60)
        lines.append("РЕЗУЛЬТАТЫ ПОИСКА")
        lines.append("=" * 60)
        lines.append("")

        for i, query_data in enumerate(queries, 1):
            query_text = query_data.get('query', 'N/A')
            answer = query_data.get('answer', 'N/A')
            sources = query_data.get('sources', [])

            lines.append(f"--- ЗАПРОС {i} ---")
            lines.append(f"Вопрос: {query_text}")
            lines.append("")
            lines.append("Ответ:")
            lines.append(answer)
            lines.append("")

            if sources:
                lines.append("Источники:")
                for source in sources:
                    lines.append(f"  - {source}")
                lines.append("")

    lines.append("=" * 60)
    lines.append("Powered by Claude Code WebSearch")
    lines.append("=" * 60)

    return "\n".join(lines)
```

### Step 2: Update Pipeline Handler

**File**: `telegram-bot/handlers/interactive_pipeline_handler.py`

**Add import**:
```python
from shared.telegram_utils.file_generators import generate_research_txt
```

**Add file generation after research completes** (around line 480):
```python
# Generate and send research results file
try:
    # Fetch research_data from database
    research_data = self.db.get_research_by_anketa(anketa_id)

    if research_data:
        # Generate .txt file
        research_txt_content = generate_research_txt(research_data)

        # Create filename following nomenclature
        research_id = research_data.get('research_id', '')
        filename = f"research_{research_id.replace('#', '')}.txt"

        # Send file to user
        file_bytes = research_txt_content.encode('utf-8')
        await update.message.reply_document(
            document=io.BytesIO(file_bytes),
            filename=filename,
            caption="📄 Результаты исследования готовы!"
        )
except Exception as e:
    logger.error(f"Failed to send research file: {e}")
    # Don't fail the whole pipeline - file is optional
```

### Step 3: Add Database Method (if needed)

**File**: `data/database/researcher.py` or `data/database/models.py`

Check if method exists:
```python
def get_research_by_anketa(self, anketa_id: str) -> Dict[str, Any]:
    """Get latest research for anketa"""
```

If not exists, add it.

---

## ✅ Success Criteria

- [ ] `generate_research_txt()` function added to `file_generators.py`
- [ ] Function follows same pattern as `generate_audit_txt()`, `generate_grant_txt()`
- [ ] Pipeline handler sends `.txt` file after research completes
- [ ] File name follows nomenclature: `research_AN-YYYYMMDD-user-001-RS-001.txt`
- [ ] File contains: research_id, anketa_id, sources count, queries, answers
- [ ] Production test: User receives file via Telegram ✅

---

## 📊 Impact

**Before Iteration 61**:
```
User clicks "🔍 Начать исследование"
  ↓
Bot shows: "📊 Найдено источников: 2, 📄 Результатов поиска: 3"
  ↓
NO FILE SENT ❌
```

**After Iteration 61**:
```
User clicks "🔍 Начать исследование"
  ↓
Bot shows: "📊 Найдено источников: 2, 📄 Результатов поиска: 3"
  ↓
Bot sends: research_AN-20251028-user-001-RS-001.txt ✅
```

---

## 🔗 Related

- **Parent**: Iteration 60 - Researcher WebSearch Fix
- **Nomenclature**: doc/NOMENCLATURE.md
- **File Generators**: shared/telegram_utils/file_generators.py
- **Next**: Iteration 62 - Expand to 27 queries (full research)

---

**Created**: 2025-10-28 23:30 MSK
**Priority**: HIGH (user explicitly requested)
