#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Interview Database Save

Tests that interview handler correctly saves anketa to database
using the right functions.

Issue: interview_handler was using non-existent create_interview_session()
Fix: Use get_or_create_session() and update_session_data()

Author: Claude Code (Iteration 52 - Phase 14 Bugfix)
Created: 2025-10-27
"""

import pytest
from pathlib import Path


@pytest.mark.integration
class TestInterviewDatabaseSave:
    """Test database save functionality"""

    def test_correct_database_functions_imported(self):
        """Test: Interview handler imports correct database functions"""

        handler_file = Path("telegram-bot/handlers/interactive_interview_handler.py")

        if not handler_file.exists():
            pytest.skip("interactive_interview_handler.py not found")

        content = handler_file.read_text(encoding='utf-8')

        # Verify correct imports (not the wrong one)
        assert "from data.database import get_or_create_session, update_session_data" in content, \
            "Should import get_or_create_session and update_session_data"

        # Verify WRONG import is NOT present (or commented out)
        wrong_import_lines = []
        for line_num, line in enumerate(content.split('\n'), 1):
            if 'from data.database import create_interview_session' in line and not line.strip().startswith('#'):
                wrong_import_lines.append(line_num)

        assert len(wrong_import_lines) == 0, \
            f"Should NOT import create_interview_session (found at lines: {wrong_import_lines})"

        print("\n✅ Correct database functions imported")
        print("✅ No incorrect create_interview_session import found")

    def test_anketa_save_workflow_correct(self):
        """Test: Interview handler uses correct workflow to save anketa"""

        handler_file = Path("telegram-bot/handlers/interactive_interview_handler.py")

        if not handler_file.exists():
            pytest.skip("interactive_interview_handler.py not found")

        content = handler_file.read_text(encoding='utf-8')

        # Find the anketa save section
        save_section_start = content.find("# ITERATION 52 FIX (Phase 14):")
        assert save_section_start > 0, "Could not find Phase 14 fix section"

        # Extract ~2000 chars after the fix comment to include full workflow
        save_section = content[save_section_start:save_section_start + 2000]

        # Verify step 1: get_or_create_session call
        assert "session_data = get_or_create_session(user_id)" in save_section, \
            "Should call get_or_create_session(user_id)"

        # Verify step 2: get session_id
        assert "session_id = session_data.get('id')" in save_section, \
            "Should extract session_id from session_data"

        # Verify step 3: generate anketa_id
        assert "anketa_id = " in save_section, \
            "Should generate anketa_id"
        assert "anketa_" in save_section, \
            "anketa_id should have 'anketa_' prefix"

        # Verify step 4: prepare update_data dict
        assert "update_data = {" in save_section, \
            "Should prepare update_data dictionary"
        assert "'interview_data'" in save_section, \
            "update_data should include interview_data"
        assert "'anketa_id'" in save_section, \
            "update_data should include anketa_id"
        assert "'completion_status': 'completed'" in save_section, \
            "update_data should mark completion_status as completed"

        # Verify step 5: call update_session_data
        assert "success = update_session_data(session_id, update_data)" in save_section, \
            "Should call update_session_data(session_id, update_data)"

        # Verify error handling
        assert "if not session_data:" in save_section, \
            "Should check if session_data is None"
        assert "if not success:" in save_section, \
            "Should check if update_session_data succeeded"

        print("\n✅ Correct workflow for saving anketa:")
        print("  1. get_or_create_session(user_id)")
        print("  2. Extract session_id")
        print("  3. Generate anketa_id")
        print("  4. Prepare update_data")
        print("  5. Call update_session_data()")
        print("  6. Error handling present")

    def test_database_functions_exist_in_module(self):
        """Test: Verify database functions actually exist in data.database module"""

        try:
            from data.database import get_or_create_session, update_session_data

            # Check they are callable
            assert callable(get_or_create_session), \
                "get_or_create_session should be callable"
            assert callable(update_session_data), \
                "update_session_data should be callable"

            print("\n✅ get_or_create_session is callable")
            print("✅ update_session_data is callable")

        except ImportError as e:
            pytest.fail(f"Failed to import database functions: {e}")

    def test_create_interview_session_does_not_exist(self):
        """Test: Verify create_interview_session does NOT exist (that was the bug)"""

        try:
            from data.database import create_interview_session
            pytest.fail("create_interview_session should NOT exist in data.database!")
        except ImportError:
            # Expected - this function does not exist
            print("\n✅ create_interview_session correctly does NOT exist")
            pass

    def test_fix_documentation_present(self):
        """Test: Verify fix is documented with ITERATION 52 FIX comment"""

        handler_file = Path("telegram-bot/handlers/interactive_interview_handler.py")

        if not handler_file.exists():
            pytest.skip("interactive_interview_handler.py not found")

        content = handler_file.read_text(encoding='utf-8')

        # Verify fix comment
        assert "ITERATION 52 FIX (Phase 14)" in content, \
            "Fix should be documented with ITERATION 52 FIX (Phase 14) comment"

        # Verify explanation
        fix_section = content[content.find("ITERATION 52 FIX (Phase 14)"):content.find("ITERATION 52 FIX (Phase 14)") + 500]
        assert "Сохранить через БД правильно" in fix_section or "правильные функции БД" in fix_section, \
            "Fix should explain the correction"

        print("\n✅ Fix documented with ITERATION 52 FIX (Phase 14)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
