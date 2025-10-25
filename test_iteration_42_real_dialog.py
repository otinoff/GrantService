#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 42: Real Dialog Simulation Test
Simulates 10 realistic interviews with InteractiveInterviewerAgentV2 + SyntheticUserSimulator

Distribution: 3 low + 5 medium + 2 high quality
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
from agents.anketa_validator import AnketaValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PostgreSQL env
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'


class Iteration42RealDialogTest:
    """
    Test runner for 10 realistic dialogs using InteractiveInterviewerAgentV2
    """

    # Test configuration
    REGIONS = [
        'Москва', 'Санкт-Петербург', 'Кемеровская область',
        'Самара', 'Казань', 'Екатеринбург', 'Новосибирск',
        'Ростов-на-Дону', 'Уфа', 'Челябинск'
    ]

    TOPICS = [
        'молодёжь', 'культура', 'образование', 'спорт',
        'социальная поддержка', 'волонтёрство', 'искусство',
        'технологии', 'экология', 'наука'
    ]

    ORGANIZATIONS = [
        'АНО "Развитие"',
        'Фонд "Социальная поддержка"',
        'Ассоциация "Молодежные инициативы"',
        'Клуб "Образовательные проекты"',
        'Центр "Культурное наследие"'
    ]

    def __init__(self):
        """Initialize test environment"""
        self.db = GrantServiceDatabase()
        self.test_user_id = 999999998  # Iteration 42 test user
        self.results = {
            'low': [],
            'medium': [],
            'high': []
        }
        self.test_start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("ITERATION 42: REAL DIALOG SIMULATION TEST")
        logger.info("=" * 80)
        logger.info(f"Test User ID: {self.test_user_id}")
        logger.info(f"Target: 10 interviews (3 low + 5 medium + 2 high)")
        logger.info("=" * 80)

    def _generate_context(self) -> Dict[str, str]:
        """Generate random context for interview"""
        return {
            'region': random.choice(self.REGIONS),
            'topic': random.choice(self.TOPICS),
            'organization': random.choice(self.ORGANIZATIONS)
        }

    async def conduct_single_dialog(
        self,
        quality_level: str,
        interview_num: int
    ) -> Dict[str, Any]:
        """
        Conduct one realistic dialog between InteractiveInterviewer and SyntheticUserSimulator

        Args:
            quality_level: 'low' | 'medium' | 'high'
            interview_num: Interview number (1-10)

        Returns:
            Dialog result with anketa_id, audit_score, dialog_history
        """
        logger.info("=" * 80)
        logger.info(f"INTERVIEW #{interview_num} - Quality: {quality_level.upper()}")
        logger.info("=" * 80)

        # Generate context
        context = self._generate_context()
        logger.info(f"Context: {context}")

        # Create user simulator
        user_simulator = SyntheticUserSimulator(
            quality_level=quality_level,
            context=context
        )

        # Create interviewer agent
        interviewer = InteractiveInterviewerAgentV2(
            db=self.db,
            llm_provider='gigachat',  # Use GigaChat
            qdrant_host='5.35.88.251',  # Production Qdrant
            qdrant_port=6333
        )

        # Dialog history (will be filled during interview)
        dialog_history = []

        # Track current question number for field estimation
        question_count = [0]  # Use list to allow mutation in nested function

        # Callback for interviewer to ask questions
        async def callback_ask_question(question: str) -> str:
            """
            Callback for InteractiveInterviewer to ask questions

            Args:
                question: Question from interviewer

            Returns:
                Answer from user simulator
            """
            # Skip if question is None (hardcoded question already asked)
            if question is None:
                # This is a hardcoded question, just wait for answer from queue
                # For simulation, return a mock answer
                return "Mock answer for hardcoded question"

            # Log question
            logger.info(f"\n[INTERVIEWER] {question}")
            dialog_history.append({
                "role": "interviewer",
                "text": question,
                "timestamp": datetime.now().isoformat()
            })

            # Estimate field name from question count (simple heuristic)
            # We don't have direct access to current_reference_point from outside
            # So we'll use a generic approach or extract from question content
            question_count[0] += 1

            # Try to infer field from question content
            field_name = "general_info"
            if "сут" in question.lower() or "цел" in question.lower():
                field_name = "project_essence"
            elif "проблем" in question.lower():
                field_name = "problem_description"
            elif "аудитор" in question.lower() or "целев" in question.lower():
                field_name = "target_audience"
            elif "бюджет" in question.lower():
                field_name = "budget"
            elif "результат" in question.lower():
                field_name = "expected_results"

            # Generate answer using SyntheticUserSimulator
            answer = await user_simulator.answer_question(question, field_name)

            # Log answer
            logger.info(f"[USER ({quality_level})] {answer[:200]}...")
            dialog_history.append({
                "role": "user",
                "text": answer,
                "timestamp": datetime.now().isoformat(),
                "field_name": field_name
            })

            return answer

        # Prepare user_data for interviewer
        user_data = {
            'telegram_id': self.test_user_id,
            'username': f'iter42_user_{interview_num}',
            'grant_fund': 'ФПГ',  # Federal Grant Fund
            'region': context['region'],
            'organization': context['organization']
        }

        # Conduct interview
        try:
            interview_result = await interviewer.conduct_interview(
                user_data=user_data,
                callback_ask_question=callback_ask_question
            )

            # Extract results
            anketa = interview_result.get('anketa', {})
            audit_score = interview_result.get('audit_score', 0)
            questions_asked = interview_result.get('questions_asked', 0)
            processing_time = interview_result.get('processing_time', 0)

            logger.info("=" * 80)
            logger.info(f"INTERVIEW #{interview_num} COMPLETED")
            logger.info(f"Questions asked: {questions_asked}")
            logger.info(f"Audit score: {audit_score}/100")
            logger.info(f"Processing time: {processing_time:.2f}s")
            logger.info(f"Dialog history length: {len(dialog_history)} messages")
            logger.info("=" * 80)

            # Save dialog_history to database
            session_id = anketa.get('session_id')
            if session_id:
                self.db.update_session_dialog_history(session_id, dialog_history)
                logger.info(f"[SUCCESS] Dialog history saved to session {session_id}")

            return {
                'interview_num': interview_num,
                'quality_level': quality_level,
                'context': context,
                'anketa_id': anketa.get('anketa_id'),
                'session_id': session_id,
                'audit_score': audit_score,
                'questions_asked': questions_asked,
                'processing_time': processing_time,
                'dialog_history_length': len(dialog_history),
                'dialog_history': dialog_history  # Full history
            }

        except Exception as e:
            logger.error(f"[ERROR] Interview #{interview_num} failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                'interview_num': interview_num,
                'quality_level': quality_level,
                'context': context,
                'error': str(e),
                'status': 'failed'
            }

    async def run_batch(
        self,
        quality_level: str,
        count: int,
        start_num: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Run a batch of interviews with the same quality level

        Args:
            quality_level: 'low' | 'medium' | 'high'
            count: Number of interviews
            start_num: Starting interview number

        Returns:
            List of interview results
        """
        logger.info("=" * 80)
        logger.info(f"BATCH: {quality_level.upper()} quality ({count} interviews)")
        logger.info("=" * 80)

        results = []
        for i in range(count):
            interview_num = start_num + i + 1
            result = await self.conduct_single_dialog(quality_level, interview_num)
            results.append(result)

            # Add delay between interviews to avoid rate limiting
            if i < count - 1:  # No delay after last interview
                delay = 10  # 10 seconds between interviews
                logger.info(f"Waiting {delay}s before next interview to avoid rate limits...")
                await asyncio.sleep(delay)

        return results

    async def run_all_10_interviews(self):
        """
        Run all 10 interviews: 3 low + 5 medium + 2 high
        """
        logger.info("\n" + "=" * 80)
        logger.info("STARTING 10 INTERVIEW CAMPAIGN")
        logger.info("=" * 80)

        # Batch 1: 3 low quality
        logger.info("\n[PHASE 1/3] LOW QUALITY (3 interviews)")
        self.results['low'] = await self.run_batch('low', count=3, start_num=0)

        # Batch 2: 5 medium quality
        logger.info("\n[PHASE 2/3] MEDIUM QUALITY (5 interviews)")
        self.results['medium'] = await self.run_batch('medium', count=5, start_num=3)

        # Batch 3: 2 high quality
        logger.info("\n[PHASE 3/3] HIGH QUALITY (2 interviews)")
        self.results['high'] = await self.run_batch('high', count=2, start_num=8)

        # Final statistics
        self._print_final_statistics()

        # Save results to JSON
        self._save_results_to_json()

    def _print_final_statistics(self):
        """Print final statistics for all interviews"""
        logger.info("\n" + "=" * 80)
        logger.info("FINAL STATISTICS - ITERATION 42")
        logger.info("=" * 80)

        all_results = (
            self.results['low'] +
            self.results['medium'] +
            self.results['high']
        )

        successful = [r for r in all_results if 'error' not in r]
        failed = [r for r in all_results if 'error' in r]

        logger.info(f"\nTotal interviews: {len(all_results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")

        if successful:
            avg_score = sum(r['audit_score'] for r in successful) / len(successful)
            avg_questions = sum(r['questions_asked'] for r in successful) / len(successful)
            avg_time = sum(r['processing_time'] for r in successful) / len(successful)
            avg_dialog_length = sum(r['dialog_history_length'] for r in successful) / len(successful)

            logger.info(f"\nAverage audit score: {avg_score:.2f}/100")
            logger.info(f"Average questions asked: {avg_questions:.1f}")
            logger.info(f"Average processing time: {avg_time:.2f}s")
            logger.info(f"Average dialog history length: {avg_dialog_length:.1f} messages")

        # Quality breakdown
        logger.info("\n--- BY QUALITY LEVEL ---")
        for quality in ['low', 'medium', 'high']:
            results = self.results[quality]
            successful_quality = [r for r in results if 'error' not in r]
            if successful_quality:
                avg_score_quality = sum(r['audit_score'] for r in successful_quality) / len(successful_quality)
                logger.info(f"{quality.upper()}: {len(successful_quality)} successful, avg score: {avg_score_quality:.2f}/100")

        logger.info("=" * 80)

    def _save_results_to_json(self):
        """Save all results to JSON file for analysis"""
        output_file = f"iteration_42_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        results_data = {
            'iteration': 42,
            'test_user_id': self.test_user_id,
            'start_time': self.test_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'results': {
                'low': self.results['low'],
                'medium': self.results['medium'],
                'high': self.results['high']
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n[SUCCESS] Results saved to: {output_file}")


async def main():
    """Main entry point"""
    test = Iteration42RealDialogTest()

    try:
        await test.run_all_10_interviews()
        logger.info("\n[SUCCESS] Iteration 42 test completed!")

    except Exception as e:
        logger.error(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
