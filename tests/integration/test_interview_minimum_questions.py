#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Interview Minimum Questions Logic

Tests that interview properly handles minimum 10 questions requirement
and doesn't hang when it reaches 9 questions.

Author: Claude Code (Iteration 52 - Debug)
Created: 2025-10-27
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.integration
@pytest.mark.asyncio
class TestInterviewMinimumQuestions:
    """Test minimum questions logic"""

    async def test_interview_with_9_answers_should_ask_10th(self):
        """Test: Interview with 9 answers should ask 10th question before finalizing"""

        # Import agent
        from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

        # Mock DB
        mock_db = MagicMock()

        # Create agent
        agent = InteractiveInterviewerAgentV2(
            db=mock_db,
            llm_provider="mock",  # Use mock to avoid real LLM calls
            qdrant_host="localhost",
            qdrant_port=6333
        )

        # Track questions asked
        questions_asked = []
        answers_given = []

        # Mock callback that auto-answers
        async def mock_ask_question(question: str) -> str:
            questions_asked.append(question)

            # Auto-answer with generic response
            answer = f"Mock answer {len(answers_given) + 1}"
            answers_given.append(answer)

            # Log
            print(f"\nQ{len(questions_asked)}: {question[:50]}...")
            print(f"A{len(answers_given)}: {answer}")

            return answer

        # Mock user data
        user_data = {
            'telegram_id': 999999,
            'username': 'test_user',
            'grant_fund': 'Фонд президентских грантов',
            'first_name': 'Test',
            'last_name': 'User'
        }

        # Run interview with mocked callback
        try:
            result = await agent.conduct_interview(
                user_data=user_data,
                callback_ask_question=mock_ask_question
            )

            # Check results
            print(f"\n=== RESULT ===")
            print(f"Questions asked: {len(questions_asked)}")
            print(f"Answers given: {len(answers_given)}")
            print(f"Audit score: {result.get('audit_score', 0)}")
            print(f"Conversation state: {result.get('conversation_state')}")

            # Assertions
            assert len(questions_asked) >= 10, \
                f"Interview should ask at least 10 questions, but only asked {len(questions_asked)}"

            assert result.get('questions_asked', 0) >= 10, \
                f"Result should report >= 10 questions, but reported {result.get('questions_asked')}"

            assert result.get('conversation_state') == 'finalizing', \
                f"Conversation should be in 'finalizing' state, but is '{result.get('conversation_state')}'"

        except Exception as e:
            print(f"\n=== ERROR ===")
            print(f"Questions asked before error: {len(questions_asked)}")
            print(f"Error: {e}")
            raise

    async def test_can_finalize_with_9_questions_returns_false(self):
        """Test: _should_finalize() should return False with 9 questions"""

        from agents.reference_points.conversation_flow_manager import ConversationFlowManager, ConversationContext
        from agents.reference_points.reference_point_manager import ReferencePointManager

        # Mock RP manager
        mock_rp_manager = MagicMock(spec=ReferencePointManager)

        # Create flow manager
        flow_manager = ConversationFlowManager(rp_manager=mock_rp_manager)

        # Set questions_asked to 9
        flow_manager.context.questions_asked = 9

        # Check _should_finalize (private method)
        can_finalize = flow_manager._should_finalize()

        print(f"\nQuestions asked: {flow_manager.context.questions_asked}")
        print(f"Can finalize: {can_finalize}")

        assert can_finalize == False, "Should not finalize with only 9 questions"

    async def test_can_finalize_with_10_questions_returns_true(self):
        """Test: _should_finalize() should return True with 10 questions (if other conditions met)"""

        from agents.reference_points.conversation_flow_manager import ConversationFlowManager, ConversationState
        from agents.reference_points.reference_point_manager import ReferencePointManager

        # Mock RP manager with good progress
        mock_rp_manager = MagicMock(spec=ReferencePointManager)
        mock_progress = MagicMock()
        mock_progress.critical_completed = True
        mock_progress.important_completed = True
        mock_progress.overall_completion = 0.85
        mock_rp_manager.get_progress.return_value = mock_progress

        # Create flow manager
        flow_manager = ConversationFlowManager(rp_manager=mock_rp_manager)

        # Set questions_asked to 10
        flow_manager.context.questions_asked = 10

        # Check _should_finalize
        can_finalize = flow_manager._should_finalize()

        print(f"\nQuestions asked: {flow_manager.context.questions_asked}")
        print(f"Can finalize: {can_finalize}")
        print(f"Progress: {mock_progress.overall_completion}")

        assert can_finalize == True, "Should finalize with 10 questions and good progress"

    def test_minimum_questions_constant_is_10(self):
        """Test: Verify MIN_QUESTIONS is set to 10 in code"""

        from pathlib import Path

        flow_manager_file = Path("agents/reference_points/conversation_flow_manager.py")

        if not flow_manager_file.exists():
            pytest.skip("conversation_flow_manager.py not found")

        content = flow_manager_file.read_text(encoding='utf-8')

        # Check for MIN_QUESTIONS = 10
        assert "MIN_QUESTIONS = 10" in content, "MIN_QUESTIONS should be set to 10"

        # Check for the < 10 check
        assert "self.context.questions_asked < 10" in content, \
            "Should check for minimum 10 questions"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
