#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 42: Single Anketa Test
Tests ONE realistic interview with InteractiveInterviewerAgentV2 + SyntheticUserSimulator
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
import random
from datetime import datetime
from typing import Dict, List, Any
import logging
import json

# Database
from data.database.models import GrantServiceDatabase

# Agents
from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
from agents.synthetic_user_simulator import SyntheticUserSimulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PostgreSQL env
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'


async def test_single_anketa():
    """
    Test single realistic interview
    """
    logger.info("=" * 80)
    logger.info("ITERATION 42: SINGLE ANKETA TEST")
    logger.info("=" * 80)

    # Initialize database
    db = GrantServiceDatabase()
    test_user_id = 999999998

    # Context for interview
    context = {
        'region': 'Москва',
        'topic': 'молодёжь',
        'organization': 'АНО "Развитие"'
    }

    logger.info(f"Test User ID: {test_user_id}")
    logger.info(f"Context: {context}")
    logger.info(f"Quality Level: MEDIUM")

    # Create user simulator
    user_simulator = SyntheticUserSimulator(
        quality_level='medium',
        context=context
    )

    # Create interviewer agent
    interviewer = InteractiveInterviewerAgentV2(
        db=db,
        llm_provider='gigachat',
        qdrant_host='5.35.88.251',
        qdrant_port=6333
    )

    # Dialog history
    dialog_history = []
    question_count = [0]

    # Callback for interviewer to ask questions
    async def callback_ask_question(question: str) -> str:
        """
        Callback for InteractiveInterviewer to ask questions
        """
        # Skip if question is None
        if question is None:
            return "Mock answer for hardcoded question"

        # Log question
        logger.info(f"\n[INTERVIEWER] {question}")
        dialog_history.append({
            "role": "interviewer",
            "text": question,
            "timestamp": datetime.now().isoformat()
        })

        question_count[0] += 1

        # Infer field name from question content
        field_name = "general_info"
        if "сут" in question.lower() or "цел" in question.lower() or "назыв" in question.lower():
            field_name = "project_essence"
        elif "проблем" in question.lower():
            field_name = "problem_description"
        elif "аудитор" in question.lower() or "целев" in question.lower():
            field_name = "target_audience"
        elif "бюджет" in question.lower():
            field_name = "budget"
        elif "результат" in question.lower():
            field_name = "expected_results"

        # Generate answer
        answer = await user_simulator.answer_question(question, field_name)

        # Log answer
        logger.info(f"[USER (medium)] {answer[:200]}...")
        dialog_history.append({
            "role": "user",
            "text": answer,
            "timestamp": datetime.now().isoformat(),
            "field_name": field_name
        })

        return answer

    # Prepare user_data
    user_data = {
        'telegram_id': test_user_id,
        'username': 'iter42_single_test',
        'grant_fund': 'ФПГ',
        'region': context['region'],
        'organization': context['organization']
    }

    # Conduct interview
    try:
        start_time = datetime.now()

        interview_result = await interviewer.conduct_interview(
            user_data=user_data,
            callback_ask_question=callback_ask_question
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Extract results
        anketa = interview_result.get('anketa', {})
        audit_score = interview_result.get('audit_score', 0)
        questions_asked = interview_result.get('questions_asked', 0)

        logger.info("=" * 80)
        logger.info("INTERVIEW COMPLETED")
        logger.info(f"Questions asked: {questions_asked}")
        logger.info(f"Audit score: {audit_score}/100")
        logger.info(f"Processing time: {processing_time:.2f}s")
        logger.info(f"Dialog history length: {len(dialog_history)} messages")
        logger.info("=" * 80)

        # Save dialog_history to database
        session_id = anketa.get('session_id')
        if session_id:
            db.update_session_dialog_history(session_id, dialog_history)
            logger.info(f"[SUCCESS] Dialog history saved to session {session_id}")

        # Display dialog
        logger.info("\n" + "=" * 80)
        logger.info("DIALOG HISTORY (Question-Answer Pairs)")
        logger.info("=" * 80)

        for i, message in enumerate(dialog_history, 1):
            role = message.get('role', 'unknown')
            text = message.get('text', '')

            if role == 'interviewer':
                logger.info(f"\n[Q{(i+1)//2}] INTERVIEWER:")
                logger.info(f"    {text}")
            elif role == 'user':
                logger.info(f"\n[A{i//2}] USER:")
                if len(text) > 500:
                    logger.info(f"    {text[:500]}...")
                    logger.info(f"    [... truncated, total {len(text)} chars]")
                else:
                    logger.info(f"    {text}")

        # Save results
        result_data = {
            'test_user_id': test_user_id,
            'context': context,
            'anketa_id': anketa.get('anketa_id'),
            'session_id': session_id,
            'audit_score': audit_score,
            'questions_asked': questions_asked,
            'processing_time': processing_time,
            'dialog_history': dialog_history,
            'completed_at': datetime.now().isoformat()
        }

        result_file = f"iteration_42_single_anketa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n[SUCCESS] Results saved to: {result_file}")
        logger.info("\n[SUCCESS] Iteration 42 single anketa test completed!")

    except Exception as e:
        logger.error(f"\n[ERROR] Interview failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_single_anketa())
