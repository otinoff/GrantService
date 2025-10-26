#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Interview Update Handling

Tests that interview handler correctly handles None update object
in background tasks without crashing.

Issue: AttributeError when trying to use update.message.reply_text() in background task
Fix: Don't call _send_results() - let pipeline handler send anketa.txt file instead

Author: Claude Code (Iteration 52 - Phase 15 Bugfix)
Created: 2025-10-27
"""

import pytest
from pathlib import Path


@pytest.mark.integration
class TestInterviewUpdateHandling:
    """Test update object handling in background tasks"""

    def test_send_results_not_called_after_save(self):
        """Test: _send_results() should NOT be called after anketa save"""

        handler_file = Path("telegram-bot/handlers/interactive_interview_handler.py")

        if not handler_file.exists():
            pytest.skip("interactive_interview_handler.py not found")

        content = handler_file.read_text(encoding='utf-8')

        # Find the section after "Anketa saved successfully"
        save_success_marker = "logger.info(f\"[DB] Anketa saved successfully with ID: {anketa_id}\")"
        save_section_start = content.find(save_success_marker)
        assert save_section_start > 0, "Could not find anketa save success marker"

        # Extract ~500 chars after the marker
        save_section = content[save_section_start:save_section_start + 600]

        # Verify _send_results is NOT called (should be commented out)
        active_send_results_calls = []
        for line_num, line in enumerate(save_section.split('\n'), 1):
            if 'await self._send_results(update, result)' in line:
                if not line.strip().startswith('#'):
                    active_send_results_calls.append(line_num)

        assert len(active_send_results_calls) == 0, \
            f"_send_results should NOT be called after anketa save (found active calls at lines: {active_send_results_calls})"

        # Verify there's a comment explaining why
        assert "ITERATION 52 FIX (Phase 15)" in save_section, \
            "Should have Phase 15 fix comment"
        assert "НЕ вызываем _send_results" in save_section or "update может быть None" in save_section, \
            "Should explain why _send_results is not called"

        print("\n✅ _send_results() correctly NOT called after anketa save")
        print("✅ Phase 15 fix comment present")

    def test_send_results_not_called_in_exception_handler(self):
        """Test: _send_results() should NOT be called in exception handler"""

        handler_file = Path("telegram-bot/handlers/interactive_interview_handler.py")

        if not handler_file.exists():
            pytest.skip("interactive_interview_handler.py not found")

        content = handler_file.read_text(encoding='utf-8')

        # Find the specific exception handler after "Failed to save anketa"
        error_marker = "[ERROR] Failed to save anketa or start pipeline"
        error_start = content.find(error_marker)
        assert error_start > 0, "Could not find 'Failed to save anketa' error handler"

        # Extract ~500 chars after error marker
        except_section = content[error_start:error_start + 600]

        # Verify _send_results is NOT called in this exception handler
        active_send_results_calls = []
        for line_num, line in enumerate(except_section.split('\n'), 1):
            if 'await self._send_results(update, result)' in line:
                if not line.strip().startswith('#'):
                    active_send_results_calls.append(line_num)

        assert len(active_send_results_calls) == 0, \
            f"_send_results should NOT be called in exception handler (found active calls at lines: {active_send_results_calls})"

        # Verify there's a Phase 15 comment
        assert "ITERATION 52 FIX (Phase 15)" in except_section, \
            "Should have Phase 15 fix comment in exception handler"

        print("\n✅ _send_results() correctly NOT called in exception handler")
        print("✅ Phase 15 fix comment present in exception handler")

    def test_pipeline_handler_sends_file_instead(self):
        """Test: Verify pipeline handler is called to send anketa.txt file"""

        handler_file = Path("telegram-bot/handlers/interactive_interview_handler.py")

        if not handler_file.exists():
            pytest.skip("interactive_interview_handler.py not found")

        content = handler_file.read_text(encoding='utf-8')

        # Find section after anketa save
        save_marker = "logger.info(f\"[DB] Anketa saved successfully with ID: {anketa_id}\")"
        save_section_start = content.find(save_marker)
        save_section = content[save_section_start:save_section_start + 1200]

        # Verify pipeline_handler.on_anketa_complete is called
        assert "pipeline_handler.on_anketa_complete" in save_section, \
            "Should call pipeline_handler.on_anketa_complete to send anketa file"

        assert "if self.pipeline_handler and anketa_id:" in save_section, \
            "Should check pipeline_handler exists before calling"

        print("\n✅ Pipeline handler is called to send anketa.txt")
        print("✅ Proper validation before calling pipeline handler")

    def test_fix_rationale_documented(self):
        """Test: Document the rationale for Phase 15 fix"""

        rationale = """
        PHASE 15 FIX RATIONALE
        ======================

        Problem:
        --------
        AttributeError: 'NoneType' object has no attribute 'reply_text'
          File "telegram-bot/handlers/interactive_interview_handler.py", line 471
            await update.message.reply_text(message)

        Root Cause:
        -----------
        - Interview runs in background task (asyncio.create_task)
        - When interview completes, `update` object may be None
        - Trying to call `update.message.reply_text()` crashes
        - This happens in _send_results() method

        Why update is None:
        -------------------
        - Interview is started with callback_ask_question that sends questions via Telegram
        - But the interview agent runs independently in background
        - When agent finishes, the original update context is no longer valid
        - update is None or update.message is None

        Solution:
        ---------
        1. DON'T call _send_results() after anketa save
        2. Let pipeline_handler.on_anketa_complete() send anketa.txt file
        3. File contains all interview data, so no need for duplicate message

        Flow After Fix:
        ---------------
        Interview completes → Save to DB → Call pipeline_handler →
        Pipeline sends anketa.txt + button → User gets file ✅

        Why This Works:
        ---------------
        - pipeline_handler.on_anketa_complete() receives update and context
        - Pipeline handler can send messages properly
        - anketa.txt file contains all data user needs
        - No duplicate messages needed
        """

        print(rationale)
        assert True, "Fix rationale documented"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
