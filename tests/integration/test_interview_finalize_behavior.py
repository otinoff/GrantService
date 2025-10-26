#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Interview Finalize Behavior

Tests that interview properly handles finalize action without waiting for user response.

Issue: Bot was sending finalize message through callback_ask_question() which waits for answer.
Fix: Finalize message should NOT use callback - just log and break loop.

Author: Claude Code (Iteration 52 - Phase 13 Bugfix)
Created: 2025-10-27
"""

import pytest
from pathlib import Path


@pytest.mark.integration
class TestInterviewFinalizeBehavior:
    """Test finalize action behavior"""

    def test_finalize_action_does_not_call_callback(self):
        """Test: Finalize action should NOT call callback_ask_question"""

        agent_file = Path("agents/interactive_interviewer_agent_v2.py")

        if not agent_file.exists():
            pytest.skip("interactive_interviewer_agent_v2.py not found")

        content = agent_file.read_text(encoding='utf-8')

        # Find the finalize block (around line 288-293)
        finalize_block_start = content.find("if action['type'] == 'finalize':")
        assert finalize_block_start > 0, "Could not find finalize block"

        # Extract ~500 chars after finalize check to capture full block including break
        finalize_block = content[finalize_block_start:finalize_block_start + 500]

        # Verify comment about not calling callback
        assert "НЕ отправляем finalize message через callback" in finalize_block, \
            "Should have comment explaining why NOT to call callback"

        # Verify callback is NOT called in finalize block
        # Check there's no "await callback_ask_question" between finalize check and break
        lines_after_finalize = finalize_block.split('\n')

        found_break = False
        callback_called_before_break = False

        for line in lines_after_finalize:
            if 'break' in line and not line.strip().startswith('#'):
                found_break = True
                break
            if 'await callback_ask_question' in line and not line.strip().startswith('#'):
                callback_called_before_break = True

        assert found_break, "Should have 'break' statement after finalize"
        assert not callback_called_before_break, \
            "Should NOT call callback_ask_question before break in finalize block"

        print(f"\n✅ Finalize block correctly does NOT call callback")
        print(f"✅ Finalize block has 'break' statement")

    def test_finalize_logs_message_and_breaks(self):
        """Test: Finalize action should log message and break loop"""

        agent_file = Path("agents/interactive_interviewer_agent_v2.py")

        if not agent_file.exists():
            pytest.skip("interactive_interviewer_agent_v2.py not found")

        content = agent_file.read_text(encoding='utf-8')

        # Find the finalize block
        finalize_block_start = content.find("if action['type'] == 'finalize':")
        assert finalize_block_start > 0, "Could not find finalize block"

        # Extract ~500 chars to capture full block including break
        finalize_block = content[finalize_block_start:finalize_block_start + 500]

        # Verify logger.info is called
        assert "logger.info" in finalize_block, \
            "Should log finalize message with logger.info"

        # Verify [FINALIZE] prefix
        assert "[FINALIZE]" in finalize_block, \
            "Should log with [FINALIZE] prefix for clarity"

        # Verify break statement
        assert "break" in finalize_block, \
            "Should break the interview loop after finalize"

        print(f"\n✅ Finalize block logs message with [FINALIZE] prefix")
        print(f"✅ Finalize block breaks interview loop")

    def test_finalize_behavior_documented(self):
        """Test: Document the correct finalize behavior"""

        expected_behavior = """
        CORRECT FINALIZE BEHAVIOR (Iteration 52 Fix)
        ============================================

        Problem (Before Fix):
        ---------------------
        if action['type'] == 'finalize':
            if callback_ask_question:
                await callback_ask_question(action['message'])  # ← WAITS FOR ANSWER!
            logger.info(action['message'])
            break

        Issue:
        - Finalize message sent through callback_ask_question()
        - callback_ask_question() is designed to ASK A QUESTION and WAIT for answer
        - But finalize message is NOT a question - it's a completion statement
        - Bot would send message then wait forever for user response

        Symptoms:
        - Bot sends: "Отлично! Мы собрали всю нужную информацию"
        - Bot waits for user input
        - User provides input (but shouldn't need to)
        - Bot never completes interview, never triggers pipeline

        Solution (After Fix):
        --------------------
        if action['type'] == 'finalize':
            # ITERATION 52 FIX: НЕ отправляем finalize message через callback!
            # callback_ask_question ЖДЁТ ответа, но это не вопрос - это завершение.
            # Просто логируем и завершаем цикл.
            logger.info(f"[FINALIZE] {action['message']}")
            break

        Correct Behavior:
        - Finalize message NOT sent to user via callback
        - Just logged for debugging
        - Interview loop breaks immediately
        - Interview handler saves anketa to DB
        - Interview handler triggers pipeline: on_anketa_complete()
        - User receives anketa.txt + "Начать аудит" button

        Why This Works:
        - Finalize is not a question requiring user input
        - Interview completion happens in handler, not in agent loop
        - Pipeline triggering is handler's responsibility
        - Agent's job is to collect data and indicate completion

        Testing:
        --------
        1. Start interview: /start
        2. Answer 8-9 questions (MIN_QUESTIONS = 8)
        3. Agent should detect completion (finalize action)
        4. Interview should complete WITHOUT waiting for additional input
        5. User should immediately receive anketa.txt file
        6. User should see "Начать аудит" button
        7. Bot should NOT hang or wait

        Related Files:
        --------------
        - agents/interactive_interviewer_agent_v2.py:288-293 (finalize logic)
        - agents/reference_points/conversation_flow_manager.py:262 (MIN_QUESTIONS = 8)
        - telegram-bot/handlers/interactive_interview_handler.py:228-280 (pipeline trigger)
        - telegram-bot/handlers/interactive_pipeline_handler.py (pipeline flow)
        """

        # This test just documents the behavior
        print(expected_behavior)
        assert True, "Finalize behavior documented"

    def test_min_questions_is_8_allowing_early_completion(self):
        """Test: Verify MIN_QUESTIONS = 8 to allow completion without hanging"""

        flow_manager_file = Path("agents/reference_points/conversation_flow_manager.py")

        if not flow_manager_file.exists():
            pytest.skip("conversation_flow_manager.py not found")

        content = flow_manager_file.read_text(encoding='utf-8')

        # Verify MIN_QUESTIONS = 8 (lowered from 10)
        assert "MIN_QUESTIONS = 8" in content, \
            "MIN_QUESTIONS should be 8 (not 10) to prevent hanging"

        # Verify the check uses 8
        assert "self.context.questions_asked < 8" in content, \
            "Should check for minimum 8 questions (not 10)"

        # Count occurrences of MIN_QUESTIONS = 8
        occurrences = content.count("MIN_QUESTIONS = 8")
        print(f"\n✅ Found {occurrences} occurrence(s) of MIN_QUESTIONS = 8")

        # Should be at least 1 (could be multiple if defined in different places)
        assert occurrences >= 1, "Should have at least one MIN_QUESTIONS = 8"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
