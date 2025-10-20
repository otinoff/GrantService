#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  workflow  Interactive Interviewer V2

   :
1. 
2.   
3.  
4.  
5. 

Author: Claude Code
Date: 2025-10-20
"""

import sys
import os
from pathlib import Path

# Setup paths
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))

import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.saved_data = {}

    def save_anketa(self, anketa_data):
        self.saved_data['anketa'] = anketa_data
        return "TEST-ANKETA-001"


class MockUser:
    """Mock user with predefined answers"""
    def __init__(self):
        self.answers = [
            # RP 1:  
            "        . "
            "         .",

            # RP 2: 
            "  -    . "
            "   ,    .",

            # RP 3:  
            "  -      7-14    . "
            "   150   .",

            # RP 4: 
            "      , "
            "      .",

            # RP 5: 
            "   - 1,500,000 .",

            # RP 6:  
            " :  (600,000),  (500,000), "
            " (300,000),  (100,000).",

            # RP 7: 
            ": 150   ,    80% , "
            "   .",

            # RP 8: 
            ": 2 , 1  , 2 . "
            "      -  5 .",

            # RP 9: 
            ":  -,  , "
            " .",

            # RP 10: 
            ":   (  ), "
            "  ( ).",

            #    
            ",  .",
            "  .",
            "."
        ]
        self.answer_index = 0

    async def answer(self, question: str) -> str:
        """  """
        if self.answer_index < len(self.answers):
            answer = self.answers[self.answer_index]
            self.answer_index += 1
        else:
            answer = ",  ."

        await asyncio.sleep(0.1)  #    
        return answer


async def test_v2_interview_workflow():
    """
      workflow V2 
    """
    print("\n" + "=" * 80)
    print("TEST: AUTOMATED WORKFLOW - Interactive Interviewer V2")
    print("=" * 80 + "\n")

    # Import V2 agent
    try:
        from interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
        print(" InteractiveInterviewerAgentV2 imported")
    except Exception as e:
        print(f" Failed to import: {e}")
        return False

    # Initialize mock database
    db = MockDatabase()
    print(" Mock database initialized")

    # Initialize mock user
    user = MockUser()
    print(" Mock user initialized (13 answers ready)")

    # Initialize V2 agent
    print("\n[1/5] Initializing V2 Agent...")
    try:
        agent = InteractiveInterviewerAgentV2(
            db=db,
            llm_provider="claude_code",
            qdrant_host="localhost",  # Will fail gracefully
            qdrant_port=6333
        )
        print(" Agent initialized")
    except Exception as e:
        print(f" Agent initialization failed: {e}")
        return False

    # Prepare user data
    user_data = {
        'telegram_id': 999999,
        'username': 'test_user',
        'first_name': 'Test',
        'grant_fund': 'fpg'
    }

    # Callback for asking questions
    async def ask_question_callback(question: str) -> str:
        """Callback   """
        print(f"\n[BOT] {question}")
        answer = await user.answer(question)
        print(f"[USER] {answer[:100]}...")
        return answer

    # Run interview
    print("\n[2/5] Starting interview...")
    try:
        result = await agent.conduct_interview(
            user_data=user_data,
            callback_ask_question=ask_question_callback
        )
        print(" Interview completed")
    except Exception as e:
        print(f" Interview failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Validate results
    print("\n[3/5] Validating results...")

    checks = []

    # Check 1: Anketa exists
    if 'anketa' in result:
        print(f" Anketa created")
        checks.append(True)
    else:
        print(f" Anketa missing")
        checks.append(False)

    # Check 2: Audit score
    if 'audit_score' in result:
        score = result['audit_score']
        print(f" Audit score: {score}/100")
        checks.append(score > 0)
    else:
        print(f" Audit score missing")
        checks.append(False)

    # Check 3: Questions asked
    if 'questions_asked' in result:
        questions = result['questions_asked']
        print(f" Questions asked: {questions}")
        checks.append(questions > 0)
    else:
        print(f" Questions asked missing")
        checks.append(False)

    # Check 4: Time tracking
    if 'processing_time' in result:
        time = result['processing_time']
        print(f" Processing time: {time:.1f}s")
        checks.append(time > 0)
    else:
        print(f" Processing time missing")
        checks.append(False)

    # Summary
    print("\n[4/5] Test summary...")
    passed = sum(checks)
    total = len(checks)
    print(f"Checks passed: {passed}/{total}")

    # Final validation
    print("\n[5/5] Final validation...")

    if result.get('questions_asked', 0) > 0:
        print(" Interview asked questions")
    else:
        print(" CRITICAL: No questions were asked!")
        return False

    if result.get('audit_score', 0) >= 50:
        print(" Audit score reasonable")
    else:
        print("  WARNING: Audit score low")

    print("\n" + "=" * 80)
    if all(checks):
        print(" ALL TESTS PASSED - V2 WORKFLOW WORKING!")
    else:
        print("  SOME TESTS FAILED - CHECK LOGS ABOVE")
    print("=" * 80 + "\n")

    # Print summary
    print(" RESULTS SUMMARY:")
    print(f"  - Questions asked: {result.get('questions_asked', 0)}")
    print(f"  - Follow-ups asked: {result.get('follow_ups_asked', 0)}")
    print(f"  - Audit score: {result.get('audit_score', 0)}/100")
    print(f"  - Processing time: {result.get('processing_time', 0):.1f}s")
    print(f"  - Conversation state: {result.get('conversation_state', 'unknown')}")

    return all(checks)


async def main():
    """Main entry point"""
    success = await test_v2_interview_workflow()

    if success:
        print("\n V2 Interview Workflow Test: PASSED")
        sys.exit(0)
    else:
        print("\n V2 Interview Workflow Test: FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
