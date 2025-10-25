#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Flow Manager for Iteration 43

Manages COMPLETE interview flow:
- Phase 1: Hardcoded questions (as in production interview_handler.py)
- Phase 2: Adaptive questions (InteractiveInterviewerAgentV2)

This orchestrates the FULL USER EXPERIENCE as they encounter in production.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import asyncio

from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
from agents.synthetic_user_simulator import SyntheticUserSimulator

logger = logging.getLogger(__name__)


# Hardcoded questions from production interview_handler.py
HARDCODED_QUESTIONS = [
    {
        "id": "user_name",
        "text": "Скажите, как Ваше имя, как я могу к Вам обращаться?",
        "field_name": "user_name",
        "required": True,
        "phase": "hardcoded"
    },
    {
        "id": "organization",
        "text": "Расскажите о вашей организации",
        "field_name": "organization_description",
        "required": True,
        "phase": "hardcoded"
    }
]


class FullFlowManager:
    """
    Manages complete interview flow with both hardcoded and adaptive phases

    This class orchestrates the FULL production flow:
    1. Hardcoded questions (name, organization)
    2. Adaptive questions (InteractiveInterviewerAgentV2)

    All questions and answers are logged to dialog_history.
    """

    def __init__(
        self,
        db,
        llm_provider: str = 'gigachat',
        qdrant_host: str = '5.35.88.251',
        qdrant_port: int = 6333
    ):
        """
        Initialize Full Flow Manager

        Args:
            db: Database instance
            llm_provider: LLM provider ('gigachat', 'openai', etc.)
            qdrant_host: Qdrant host for semantic search
            qdrant_port: Qdrant port
        """
        self.db = db
        self.llm_provider = llm_provider
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port

        logger.info("FullFlowManager initialized")
        logger.info(f"LLM Provider: {llm_provider}")
        logger.info(f"Qdrant: {qdrant_host}:{qdrant_port}")

    async def _ask_hardcoded_questions(
        self,
        user_simulator: SyntheticUserSimulator,
        dialog_history: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Ask hardcoded questions (Phase 1)

        Args:
            user_simulator: SyntheticUserSimulator instance
            dialog_history: List to append dialog messages to

        Returns:
            Dict with hardcoded responses: {'user_name': '...', 'organization_description': '...'}
        """
        logger.info("=" * 80)
        logger.info("PHASE 1: HARDCODED QUESTIONS")
        logger.info("=" * 80)

        hardcoded_data = {}

        for i, question_config in enumerate(HARDCODED_QUESTIONS, 1):
            question_id = question_config['id']
            question_text = question_config['text']
            field_name = question_config['field_name']

            # Log question
            logger.info(f"\n[Q{i}] INTERVIEWER (hardcoded): {question_text}")
            dialog_history.append({
                "role": "interviewer",
                "text": question_text,
                "timestamp": datetime.now().isoformat(),
                "phase": "hardcoded",
                "question_id": question_id
            })

            # Generate answer using SyntheticUserSimulator
            answer = await user_simulator.answer_question(question_text, field_name)

            # Log answer
            logger.info(f"[A{i}] USER: {answer[:200]}...")
            dialog_history.append({
                "role": "user",
                "text": answer,
                "timestamp": datetime.now().isoformat(),
                "phase": "hardcoded",
                "field_name": field_name
            })

            # Store in hardcoded_data
            hardcoded_data[field_name] = answer

        logger.info(f"\n[PHASE 1] Completed: {len(HARDCODED_QUESTIONS)} hardcoded questions")
        return hardcoded_data

    async def _conduct_adaptive_interview(
        self,
        user_data: Dict[str, Any],
        user_simulator: SyntheticUserSimulator,
        dialog_history: List[Dict[str, Any]],
        hardcoded_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Conduct adaptive interview (Phase 2)

        Args:
            user_data: User data dict
            user_simulator: SyntheticUserSimulator instance
            dialog_history: List to append dialog messages to
            hardcoded_data: Data from hardcoded questions

        Returns:
            Interview result from InteractiveInterviewerAgentV2
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: ADAPTIVE QUESTIONS (InteractiveInterviewerAgentV2)")
        logger.info("=" * 80)

        # Enrich user_data with hardcoded responses
        user_data_enriched = {
            **user_data,
            'user_name': hardcoded_data.get('user_name', ''),
            'organization_description': hardcoded_data.get('organization_description', '')
        }

        # Create InteractiveInterviewerAgentV2
        interviewer = InteractiveInterviewerAgentV2(
            db=self.db,
            llm_provider=self.llm_provider,
            qdrant_host=self.qdrant_host,
            qdrant_port=self.qdrant_port
        )

        # Track question number for adaptive phase
        adaptive_question_count = [0]

        # Callback for asking questions
        async def callback_ask_question(question: str) -> str:
            """
            Callback for InteractiveInterviewer to ask questions
            """
            # Skip if question is None
            if question is None:
                return "Mock answer for hardcoded question"

            adaptive_question_count[0] += 1
            question_num = len(HARDCODED_QUESTIONS) + adaptive_question_count[0]

            # Log question
            logger.info(f"\n[Q{question_num}] INTERVIEWER (adaptive): {question}")
            dialog_history.append({
                "role": "interviewer",
                "text": question,
                "timestamp": datetime.now().isoformat(),
                "phase": "adaptive"
            })

            # Infer field name from question content
            field_name = self._infer_field_name(question)

            # Generate answer
            answer = await user_simulator.answer_question(question, field_name)

            # Log answer
            logger.info(f"[A{question_num}] USER: {answer[:200]}...")
            dialog_history.append({
                "role": "user",
                "text": answer,
                "timestamp": datetime.now().isoformat(),
                "phase": "adaptive",
                "field_name": field_name
            })

            return answer

        # Conduct adaptive interview
        interview_result = await interviewer.conduct_interview(
            user_data=user_data_enriched,
            callback_ask_question=callback_ask_question
        )

        logger.info(f"\n[PHASE 2] Completed: {adaptive_question_count[0]} adaptive questions")

        return interview_result

    def _infer_field_name(self, question: str) -> str:
        """
        Infer field name from question content using keyword matching

        Args:
            question: Question text

        Returns:
            Inferred field name
        """
        question_lower = question.lower()

        if "назыв" in question_lower or "сут" in question_lower or "цел" in question_lower:
            return "project_essence"
        elif "проблем" in question_lower:
            return "problem_description"
        elif "аудитор" in question_lower or "целев" in question_lower:
            return "target_audience"
        elif "бюджет" in question_lower or "финанс" in question_lower:
            return "budget"
        elif "результат" in question_lower or "эффект" in question_lower:
            return "expected_results"
        elif "календар" in question_lower or "срок" in question_lower or "план" in question_lower:
            return "calendar_plan"
        elif "партнер" in question_lower or "команд" in question_lower:
            return "partners"
        else:
            return "general_info"

    async def conduct_full_interview(
        self,
        user_data: Dict[str, Any],
        user_simulator: SyntheticUserSimulator
    ) -> Dict[str, Any]:
        """
        Conduct COMPLETE interview with both phases

        This is the MAIN METHOD that orchestrates the full flow.

        Args:
            user_data: User data dict with telegram_id, username, grant_fund, etc.
            user_simulator: SyntheticUserSimulator instance

        Returns:
            {
                'dialog_history': [...],  # Full conversation history
                'hardcoded_data': {...},  # Data from Phase 1
                'interview_result': {...},  # Result from Phase 2
                'anketa': {...},  # Anketa data
                'audit_score': float,  # Audit score
                'session_id': int,  # Session ID
                'hardcoded_questions_asked': int,
                'adaptive_questions_asked': int,
                'total_questions_asked': int
            }
        """
        logger.info("=" * 80)
        logger.info("FULL FLOW INTERVIEW - STARTING")
        logger.info("=" * 80)
        logger.info(f"User: {user_data.get('username', 'N/A')}")
        logger.info(f"Grant Fund: {user_data.get('grant_fund', 'N/A')}")
        logger.info(f"Region: {user_data.get('region', 'N/A')}")
        logger.info("=" * 80)

        # Initialize dialog history
        dialog_history = []

        start_time = datetime.now()

        # Phase 1: Hardcoded questions
        hardcoded_data = await self._ask_hardcoded_questions(
            user_simulator,
            dialog_history
        )

        # Phase 2: Adaptive questions
        interview_result = await self._conduct_adaptive_interview(
            user_data,
            user_simulator,
            dialog_history,
            hardcoded_data
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Extract results
        anketa = interview_result.get('anketa', {})
        audit_score = interview_result.get('audit_score', 0)
        adaptive_questions_asked = interview_result.get('questions_asked', 0)

        # Save dialog_history to database
        session_id = anketa.get('session_id')
        if session_id:
            self.db.update_session_dialog_history(session_id, dialog_history)
            logger.info(f"[SUCCESS] Dialog history saved to session {session_id}")

        # Calculate statistics
        hardcoded_questions_asked = len(HARDCODED_QUESTIONS)
        total_questions_asked = hardcoded_questions_asked + adaptive_questions_asked

        logger.info("\n" + "=" * 80)
        logger.info("FULL FLOW INTERVIEW - COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Hardcoded questions: {hardcoded_questions_asked}")
        logger.info(f"Adaptive questions: {adaptive_questions_asked}")
        logger.info(f"Total questions: {total_questions_asked}")
        logger.info(f"Dialog messages: {len(dialog_history)}")
        logger.info(f"Audit score: {audit_score}/100")
        logger.info(f"Processing time: {processing_time:.2f}s")
        logger.info("=" * 80)

        return {
            'dialog_history': dialog_history,
            'hardcoded_data': hardcoded_data,
            'interview_result': interview_result,
            'anketa': anketa,
            'audit_score': audit_score,
            'session_id': session_id,
            'hardcoded_questions_asked': hardcoded_questions_asked,
            'adaptive_questions_asked': adaptive_questions_asked,
            'total_questions_asked': total_questions_asked,
            'processing_time': processing_time
        }
