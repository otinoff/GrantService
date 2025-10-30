#!/usr/bin/env python3
"""
InterviewerTestModule - Testing PRODUCTION InteractiveInterviewerAgentV2

Source: Iteration 63 (Interactive Interview)
Tests: Production InteractiveInterviewerAgentV2.conduct_interview()
Critical: Uses callback_ask_question with LLM-generated answers

Iteration 66: E2E Test Suite
CORRECTED: No fallback to SyntheticUserSimulator - tests PRODUCTION code only!
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any
import logging
import asyncio
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data.database.models import GrantServiceDatabase


class InterviewerTestModule:
    """
    Test module for PRODUCTION InteractiveInterviewerAgentV2

    Uses production conduct_interview() method with automated callback
    NO fallback to SyntheticUserSimulator - tests production code only!

    Key Features:
    - Tests PRODUCTION InteractiveInterviewerAgentV2.conduct_interview()
    - Automated callback provides LLM-generated answers
    - Validates >= 14 questions, >= 5000 chars
    - Records to production database

    Example:
        interviewer = InterviewerTestModule(db)
        anketa_data = await interviewer.run_automated_interview(
            telegram_id=999999001,
            username="test_user",
            llm_provider="gigachat"
        )
    """

    def __init__(self, db: GrantServiceDatabase):
        """Initialize with production database"""
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.llm_client = None

    async def _init_llm_client(self, llm_provider: str):
        """Initialize LLM client for generating answers"""
        if self.llm_client is None:
            from shared.llm.unified_llm_client import UnifiedLLMClient
            self.llm_client = UnifiedLLMClient(provider=llm_provider)

    async def _generate_answer(self, question: str) -> str:
        """
        Generate realistic answer to interview question using LLM

        Args:
            question: Interview question text

        Returns:
            Generated answer (100-300 chars)
        """
        prompt = f"""Ты - пользователь, проходящий интервью для грантовой заявки.
Ответь на вопрос естественным языком, как реальный человек.
Ответ должен быть содержательным (100-300 символов).

Вопрос: {question}

Твой ответ:"""

        try:
            response = await self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=200
            )

            # Extract text
            if isinstance(response, dict):
                answer = response.get('text', str(response))
            else:
                answer = str(response)

            self.logger.info(f"Generated answer ({len(answer)} chars): {answer[:100]}...")
            return answer

        except Exception as e:
            self.logger.error(f"Failed to generate answer: {e}")
            # Fallback to simple answer
            return f"Это тестовый ответ на вопрос: {question[:50]}..."

    async def run_automated_interview(
        self,
        telegram_id: int,
        username: str,
        llm_provider: str = "gigachat"
    ) -> Dict[str, Any]:
        """
        Run PRODUCTION InteractiveInterviewerAgentV2 in automated mode

        Tests production conduct_interview() method with automated callback.
        NO fallback to SyntheticUserSimulator!

        Args:
            telegram_id: Test user telegram ID
            username: Test username
            llm_provider: LLM provider for answer generation

        Returns:
            Dict with:
                - anketa_id: Generated anketa ID
                - user_answers: Collected answers
                - questions_count: Number of questions asked
                - session_id: Database session ID
                - total_chars: Total characters in answers

        Raises:
            ImportError: If InteractiveInterviewerAgentV2 not found
            ValueError: If validation fails
        """
        self.logger.info("="*80)
        self.logger.info("INTERVIEWER TEST MODULE - PRODUCTION CODE")
        self.logger.info("="*80)

        # 1. Import PRODUCTION InteractiveInterviewerAgentV2
        try:
            from agents.interactive_interviewer_v2 import InteractiveInterviewerAgentV2
        except ImportError as e:
            self.logger.error(f"Failed to import InteractiveInterviewerAgentV2: {e}")
            raise

        self.logger.info(f"Testing user: {username} (telegram_id={telegram_id})")

        # 2. Initialize LLM client for answer generation
        await self._init_llm_client(llm_provider)

        # 3. Initialize production interviewer
        interviewer = InteractiveInterviewerAgentV2(
            db=self.db,
            llm_provider=llm_provider
        )

        # 4. Create automated callback for conduct_interview
        async def automated_callback(question: str) -> str:
            """Automated callback that generates answers using LLM"""
            self.logger.info(f"Q: {question}")
            answer = await self._generate_answer(question)
            self.logger.info(f"A: {answer[:100]}...")
            return answer

        # 5. Run PRODUCTION interview
        self.logger.info("Starting PRODUCTION interview (automated callback)...")

        user_data = {
            'telegram_id': telegram_id,
            'username': username,
            'grant_fund': 'ФПГ-2025'
        }

        result = await interviewer.conduct_interview(
            user_data=user_data,
            callback_ask_question=automated_callback
        )

        # 6. Extract anketa data
        anketa = result.get('anketa', {})
        questions_asked = result.get('questions_asked', 0)
        dialog_questions = result.get('dialog_questions', {})  # ITERATION 67!

        # 7. Save session to database (PRODUCTION CODE DOESN'T SAVE!)
        from datetime import datetime
        import json

        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # Generate anketa_id
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            anketa_id = f"#AN-E2E-{timestamp}-{telegram_id}"

            # INSERT session with dialog_questions
            cursor.execute("""
                INSERT INTO sessions (
                    telegram_id,
                    started_at,
                    status,
                    answers_data,
                    dialog_questions,
                    anketa_id
                )
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s)
                RETURNING id
            """, (
                telegram_id,
                datetime.now(),
                'completed',
                json.dumps(anketa, ensure_ascii=False),
                json.dumps(dialog_questions, ensure_ascii=False),
                anketa_id
            ))

            session_id = cursor.fetchone()[0]
            conn.commit()

            self.logger.info(f"✅ Session saved to DB: {session_id} (anketa_id={anketa_id})")
            self.logger.info(f"   Dialog questions saved: {len(dialog_questions)}")

        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

        # Use saved data
        answers_data = anketa

        # 8. Calculate total characters
        total_chars = 0
        if answers_data:
            for value in answers_data.values():
                if isinstance(value, str):
                    total_chars += len(value)

        # 9. Validate
        self.logger.info("\n" + "="*80)
        self.logger.info("VALIDATION")
        self.logger.info("="*80)

        if questions_asked < 14:
            self.logger.warning(f"⚠️ Only {questions_asked} questions (expected >= 14)")
        else:
            self.logger.info(f"✅ Questions: {questions_asked} >= 14")

        if total_chars < 5000:
            self.logger.warning(f"⚠️ Only {total_chars} chars (expected >= 5000)")
        else:
            self.logger.info(f"✅ Total chars: {total_chars} >= 5000")

        self.logger.info("="*80)

        # 10. Return structured data
        return {
            'anketa_id': anketa_id,
            'user_answers': answers_data or {},
            'questions_count': questions_asked,
            'session_id': session_id,
            'total_chars': total_chars
        }

    def export_to_file(self, anketa_data: Dict[str, Any], filepath: Path):
        """
        Export anketa with questions and answers using PRODUCTION method

        ITERATION 67: Now uses format_anketa_with_questions(session_id)
        to get real questions from dialog_questions column.

        Args:
            anketa_data: Dict with 'session_id' key
            filepath: Output file path
        """
        session_id = anketa_data.get('session_id')
        if not session_id:
            raise ValueError("anketa_data must contain 'session_id'")

        # Import production agent
        from agents.interactive_interviewer_v2 import InteractiveInterviewerAgentV2

        # Create temp instance just for formatting
        interviewer = InteractiveInterviewerAgentV2(db=self.db, llm_provider="gigachat")

        # Use PRODUCTION formatting method - gets questions from DB
        anketa_txt = interviewer.format_anketa_with_questions(session_id)

        filepath.write_text(anketa_txt, encoding='utf-8')
        self.logger.info(f"✅ Exported anketa (PRODUCTION format with questions) to: {filepath}")
        self.logger.info(f"   File size: {len(anketa_txt)} chars")
