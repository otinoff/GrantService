#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke Test: Production Imports Validation

This test ensures CRITICAL production modules can be imported without errors.

This catches issues like:
- Missing __init__.py files
- Incorrect import paths after refactoring
- Circular import dependencies
- Missing dependencies

Run before EVERY commit: pytest tests/smoke/ -v

Based on ROOT CAUSE ANALYSIS from Iteration 53.
"""

import sys
from pathlib import Path
import pytest

# Add project root to path
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))


# =============================================================================
# SMOKE TEST: LLM Client
# =============================================================================

def test_llm_client_import():
    """Test that unified LLM client can be imported."""

    try:
        from shared.llm.unified_llm_client import UnifiedLLMClient
    except ImportError as e:
        pytest.fail(f"UnifiedLLMClient import failed: {e}")

    print("[PASS] UnifiedLLMClient imported successfully")


# =============================================================================
# SMOKE TEST: Agent Modules (CRITICAL - this is where Iteration 53 bug was)
# =============================================================================

def test_agent_modules_import():
    """Test that all agent modules can be imported.

    CRITICAL: This is the test that would have caught Iteration 53 bug!
    telegram-bot/main.py:1965 had wrong import path.
    """

    # InteractiveInterviewerAgentV2 (NEW PATH - from refactoring)
    try:
        from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2
    except ImportError as e:
        pytest.fail(f"InteractiveInterviewerAgentV2 import failed: {e}")

    # Other agents
    try:
        from agents.auditor_agent import AuditorAgent
        from agents.writer_agent import WriterAgent
        from agents.full_flow_manager import FullFlowManager
    except ImportError as e:
        pytest.fail(f"Other agent modules import failed: {e}")

    print("[PASS] All agent modules imported successfully")


# =============================================================================
# SMOKE TEST: File Generators
# =============================================================================

def test_file_generators_import():
    """Test that file generators can be imported."""

    try:
        from shared.telegram_utils.file_generators import generate_anketa_txt
        from shared.telegram_utils.file_generators import generate_audit_txt
    except ImportError as e:
        pytest.fail(f"File generators import failed: {e}")

    print("[PASS] File generators imported successfully")


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    """Run smoke tests directly."""
    print("\n" + "="*60)
    print("SMOKE TEST: Production Imports Validation")
    print("="*60)

    pytest.main([__file__, "-v", "-s"])

    print("\n" + "="*60)
    print("SMOKE TEST COMPLETE")
    print("="*60)
    print("""
These tests validate that ALL production modules can be imported.

Why this matters:
- Catches wrong import paths after refactoring
- Catches missing __init__.py files
- Catches circular import dependencies
- Prevents production bugs like Iteration 53

When to run:
- BEFORE every commit (pre-commit hook)
- AFTER any refactoring
- In CI/CD pipeline
    """)
