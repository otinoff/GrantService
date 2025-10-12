"""
Stage Tracking System for Grant Application Funnel
Tracks application progress through: Interviewer → Auditor → Researcher → Writer → Reviewer
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

# Import database helpers
try:
    from utils.postgres_helper import execute_query as _execute_query, execute_update as _execute_update
except ImportError:
    from postgres_helper import execute_query as _execute_query, execute_update as _execute_update

# Stage configuration
STAGES = ['interviewer', 'auditor', 'researcher', 'writer', 'reviewer']

STAGE_EMOJI = {
    'interviewer': '📝',
    'auditor': '✅',
    'researcher': '🔍',
    'writer': '✍️',
    'reviewer': '🔎',
    'completed': '🎉'
}

STAGE_NAMES = {
    'interviewer': 'Interviewer',
    'auditor': 'Auditor',
    'researcher': 'Researcher',
    'writer': 'Writer',
    'reviewer': 'Reviewer',
    'completed': 'Completed'
}


def get_stage_emoji(stage: str) -> str:
    """Get emoji for stage"""
    return STAGE_EMOJI.get(stage, '❓')


def get_stage_name(stage: str) -> str:
    """Get display name for stage"""
    return STAGE_NAMES.get(stage, stage.title())


def get_stage_progress(current_stage: str, agents_passed: List[str]) -> int:
    """Calculate progress percentage based on completed stages"""
    total_stages = len(STAGES)
    completed_stages = len(agents_passed)
    return int((completed_stages / total_stages) * 100)


def format_stage_badge(current_stage: str, agents_passed: List[str]) -> str:
    """
    Format stage progress as a badge string
    Example: "📝 INT → ✅ AUD → 🔍 RES → 🔄 WR → ⏸️ REW"
    """
    badge_parts = []

    for stage in STAGES:
        emoji = get_stage_emoji(stage)
        short_name = stage[:3].upper()

        if stage in agents_passed:
            # Completed stage
            status = f"✅ {short_name}"
        elif stage == current_stage:
            # Current stage (in progress)
            status = f"🔄 {short_name}"
        else:
            # Not started yet
            status = f"⏸️ {short_name}"

        badge_parts.append(status)

    return " → ".join(badge_parts)


def format_stage_progress_compact(anketa_id: str, current_stage: str, agents_passed: List[str]) -> str:
    """
    Compact format for displaying in lists
    Example: "📋 ANK-20251004-user-014 [✅ INT → ✅ AUD → 🔄 RES]"
    """
    emoji = get_stage_emoji(current_stage)
    progress_pct = get_stage_progress(current_stage, agents_passed)

    return f"📋 {anketa_id} [{emoji} {current_stage.upper()[:3]} - {progress_pct}%]"


def update_stage(anketa_id: str, new_stage: str) -> bool:
    """
    Update session stage and track history

    Args:
        anketa_id: Anketa ID to update
        new_stage: New stage name

    Returns:
        True if update successful
    """
    try:
        # Get current stage info
        query_get = """
            SELECT current_stage, agents_passed, stage_history
            FROM sessions
            WHERE anketa_id = %s
        """
        result = _execute_query(query_get, (anketa_id,))

        if not result or len(result) == 0:
            return False

        row = result[0]
        current_stage = row['current_stage']
        agents_passed = row['agents_passed']
        stage_history = row['stage_history']

        # Initialize if null
        if agents_passed is None:
            agents_passed = []
        if stage_history is None:
            stage_history = []

        # Add current stage to agents_passed if not already there
        if current_stage and current_stage not in agents_passed:
            agents_passed.append(current_stage)

        # Add transition to stage_history
        transition = {
            'from_stage': current_stage,
            'to_stage': new_stage,
            'timestamp': datetime.now().isoformat()
        }
        stage_history.append(transition)

        # Update session
        query_update = """
            UPDATE sessions
            SET
                current_stage = %s,
                agents_passed = %s,
                stage_history = %s,
                stage_updated_at = NOW()
            WHERE anketa_id = %s
        """

        _execute_update(
            query_update,
            (new_stage, agents_passed, json.dumps(stage_history), anketa_id)
        )

        return True

    except Exception as e:
        print(f"Error updating stage: {e}")
        return False


def get_stage_info(anketa_id: str) -> Optional[Dict]:
    """
    Get complete stage information for an anketa

    Returns:
        Dict with anketa_id, current_stage, agents_passed, progress_percentage, stage_emoji
    """
    try:
        query = """
            SELECT
                anketa_id,
                current_stage,
                agents_passed,
                stage_history,
                stage_updated_at
            FROM sessions
            WHERE anketa_id = %s
        """

        result = _execute_query(query, (anketa_id,))

        if not result or len(result) == 0:
            return None

        row = result[0]
        anketa_id = row['anketa_id']
        current_stage = row['current_stage']
        agents_passed = row['agents_passed']
        stage_history = row['stage_history']
        updated_at = row['stage_updated_at']

        if agents_passed is None:
            agents_passed = []

        progress = get_stage_progress(current_stage or 'interviewer', agents_passed)

        return {
            'anketa_id': anketa_id,
            'current_stage': current_stage or 'interviewer',
            'agents_passed': agents_passed,
            'stage_history': stage_history or [],
            'progress_percentage': progress,
            'stage_emoji': get_stage_emoji(current_stage or 'interviewer'),
            'stage_name': get_stage_name(current_stage or 'interviewer'),
            'updated_at': updated_at,
            'badge': format_stage_badge(current_stage or 'interviewer', agents_passed)
        }

    except Exception as e:
        print(f"Error getting stage info: {e}")
        return None


def get_all_stages_summary() -> Dict[str, int]:
    """
    Get summary of all applications by stage

    Returns:
        Dict with stage counts: {'interviewer': 10, 'auditor': 5, ...}
    """
    try:
        query = """
            SELECT
                current_stage,
                COUNT(*) as count
            FROM sessions
            WHERE anketa_id IS NOT NULL
            GROUP BY current_stage
            ORDER BY current_stage
        """

        results = _execute_query(query)

        summary = {stage: 0 for stage in STAGES}
        summary['completed'] = 0

        for row in results:
            stage, count = row
            if stage in summary:
                summary[stage] = count

        return summary

    except Exception as e:
        print(f"Error getting stages summary: {e}")
        return {}


def is_stage_completed(agents_passed: List[str], stage: str) -> bool:
    """Check if a specific stage is completed"""
    return stage in agents_passed


def get_next_stage(current_stage: str) -> Optional[str]:
    """Get the next stage in the funnel"""
    try:
        current_index = STAGES.index(current_stage)
        if current_index < len(STAGES) - 1:
            return STAGES[current_index + 1]
        else:
            return 'completed'
    except ValueError:
        return None


def get_previous_stage(current_stage: str) -> Optional[str]:
    """Get the previous stage in the funnel"""
    try:
        current_index = STAGES.index(current_stage)
        if current_index > 0:
            return STAGES[current_index - 1]
        else:
            return None
    except ValueError:
        return None


# Example usage:
if __name__ == "__main__":
    # Test badge formatting
    test_anketa = "ANK-20251004-theperipherals-014"
    test_stage = "researcher"
    test_passed = ["interviewer", "auditor"]

    print("Stage Tracking System Test")
    print("=" * 60)
    print(f"\nAnketa ID: {test_anketa}")
    print(f"Current Stage: {test_stage}")
    print(f"Agents Passed: {test_passed}")
    print(f"\nProgress: {get_stage_progress(test_stage, test_passed)}%")
    print(f"\nBadge: {format_stage_badge(test_stage, test_passed)}")
    print(f"\nCompact: {format_stage_progress_compact(test_anketa, test_stage, test_passed)}")
    print(f"\nNext Stage: {get_next_stage(test_stage)}")
    print(f"Previous Stage: {get_previous_stage(test_stage)}")
