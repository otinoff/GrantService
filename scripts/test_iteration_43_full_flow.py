#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 43: Full Production Flow Test

Tests COMPLETE production flow as users experience it:
- Phase 1: Hardcoded questions (interview_handler.py)
- Phase 2: Adaptive questions (InteractiveInterviewerAgentV2)

Scale: 2 anketas (1 medium + 1 high quality)

This is the FIRST TIME we test the FULL FLOW end-to-end.
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
from agents.full_flow_manager import FullFlowManager
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


class Iteration43FullFlowTest:
    """
    Test runner for 2 full-flow interviews

    Distribution: 1 medium + 1 high quality
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
        'Центр "Образовательные проекты"',
        'Клуб "Культурное наследие"'
    ]

    def __init__(self):
        """Initialize test environment"""
        self.db = GrantServiceDatabase()
        self.test_user_id = 999999997  # Iteration 43 test user
        self.results = []
        self.test_start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("ITERATION 43: FULL PRODUCTION FLOW TEST")
        logger.info("=" * 80)
        logger.info(f"Test User ID: {self.test_user_id}")
        logger.info(f"Target: 2 full-flow interviews (1 medium + 1 high)")
        logger.info("Flow: Hardcoded questions + Adaptive questions (V2)")
        logger.info("=" * 80)

    def _generate_context(self) -> Dict[str, str]:
        """Generate random context for interview"""
        return {
            'region': random.choice(self.REGIONS),
            'topic': random.choice(self.TOPICS),
            'organization': random.choice(self.ORGANIZATIONS)
        }

    async def conduct_single_full_flow_interview(
        self,
        quality_level: str,
        interview_num: int
    ) -> Dict[str, Any]:
        """
        Conduct one FULL FLOW interview (hardcoded + adaptive)

        Args:
            quality_level: 'medium' | 'high'
            interview_num: Interview number (1-2)

        Returns:
            Full flow result with all phases
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

        # Create full flow manager
        flow_manager = FullFlowManager(
            db=self.db,
            llm_provider='gigachat',
            qdrant_host='5.35.88.251',
            qdrant_port=6333
        )

        # Prepare user_data
        user_data = {
            'telegram_id': self.test_user_id,
            'username': f'iter43_fullflow_{interview_num}',
            'grant_fund': 'ФПГ',
            'region': context['region'],
            'organization': context['organization']
        }

        # Conduct FULL FLOW interview
        try:
            full_flow_result = await flow_manager.conduct_full_interview(
                user_data=user_data,
                user_simulator=user_simulator
            )

            logger.info("=" * 80)
            logger.info(f"INTERVIEW #{interview_num} COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"Hardcoded questions: {full_flow_result['hardcoded_questions_asked']}")
            logger.info(f"Adaptive questions: {full_flow_result['adaptive_questions_asked']}")
            logger.info(f"Total questions: {full_flow_result['total_questions_asked']}")
            logger.info(f"Dialog messages: {len(full_flow_result['dialog_history'])}")
            logger.info(f"Audit score: {full_flow_result['audit_score']}/100")
            logger.info(f"Processing time: {full_flow_result['processing_time']:.2f}s")
            logger.info("=" * 80)

            # Display sample dialog
            self._display_sample_dialog(full_flow_result['dialog_history'], interview_num)

            return {
                'interview_num': interview_num,
                'quality_level': quality_level,
                'context': context,
                'anketa_id': full_flow_result['anketa'].get('anketa_id'),
                'session_id': full_flow_result['session_id'],
                'audit_score': full_flow_result['audit_score'],
                'hardcoded_questions_asked': full_flow_result['hardcoded_questions_asked'],
                'adaptive_questions_asked': full_flow_result['adaptive_questions_asked'],
                'total_questions_asked': full_flow_result['total_questions_asked'],
                'dialog_history_length': len(full_flow_result['dialog_history']),
                'processing_time': full_flow_result['processing_time'],
                'status': 'success'
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

    def _display_sample_dialog(self, dialog_history: List[Dict[str, Any]], interview_num: int):
        """
        Display sample of dialog for inspection

        Args:
            dialog_history: Full dialog history
            interview_num: Interview number
        """
        logger.info("\n" + "=" * 80)
        logger.info(f"DIALOG SAMPLE - INTERVIEW #{interview_num}")
        logger.info("=" * 80)

        # Show first 6 messages (3 Q&A pairs)
        sample_count = min(6, len(dialog_history))

        for i, message in enumerate(dialog_history[:sample_count], 1):
            role = message.get('role', 'unknown')
            text = message.get('text', '')
            phase = message.get('phase', 'N/A')

            if role == 'interviewer':
                logger.info(f"\n[Q{(i+1)//2}] [{phase.upper()}] INTERVIEWER:")
                logger.info(f"    {text}")
            elif role == 'user':
                logger.info(f"\n[A{i//2}] [{phase.upper()}] USER:")
                if len(text) > 300:
                    logger.info(f"    {text[:300]}...")
                    logger.info(f"    [... {len(text)} chars total]")
                else:
                    logger.info(f"    {text}")

        if len(dialog_history) > sample_count:
            logger.info(f"\n... ({len(dialog_history) - sample_count} more messages)")

        logger.info("\n" + "=" * 80)

    async def run_2_interviews(self):
        """
        Run 2 full-flow interviews: 1 medium + 1 high
        """
        logger.info("\n" + "=" * 80)
        logger.info("STARTING 2-INTERVIEW CAMPAIGN (FULL FLOW)")
        logger.info("=" * 80)

        # Interview 1: Medium quality
        logger.info("\n[INTERVIEW 1/2] MEDIUM QUALITY")
        result1 = await self.conduct_single_full_flow_interview('medium', 1)
        self.results.append(result1)

        # Add delay to avoid rate limits
        if result1['status'] == 'success':
            logger.info("\n[DELAY] Waiting 30 seconds before next interview...")
            await asyncio.sleep(30)

        # Interview 2: High quality
        logger.info("\n[INTERVIEW 2/2] HIGH QUALITY")
        result2 = await self.conduct_single_full_flow_interview('high', 2)
        self.results.append(result2)

        # Final statistics
        self._print_final_statistics()

        # Save results to JSON
        self._save_results_to_json()

    def _print_final_statistics(self):
        """Print final statistics for all interviews"""
        logger.info("\n" + "=" * 80)
        logger.info("FINAL STATISTICS - ITERATION 43")
        logger.info("=" * 80)

        successful = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] == 'failed']

        logger.info(f"\nTotal interviews: {len(self.results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")

        if successful:
            avg_score = sum(r['audit_score'] for r in successful) / len(successful)
            avg_hardcoded = sum(r['hardcoded_questions_asked'] for r in successful) / len(successful)
            avg_adaptive = sum(r['adaptive_questions_asked'] for r in successful) / len(successful)
            avg_total = sum(r['total_questions_asked'] for r in successful) / len(successful)
            avg_time = sum(r['processing_time'] for r in successful) / len(successful)
            avg_dialog_length = sum(r['dialog_history_length'] for r in successful) / len(successful)

            logger.info(f"\nAverage audit score: {avg_score:.2f}/100")
            logger.info(f"Average hardcoded questions: {avg_hardcoded:.1f}")
            logger.info(f"Average adaptive questions: {avg_adaptive:.1f}")
            logger.info(f"Average total questions: {avg_total:.1f}")
            logger.info(f"Average processing time: {avg_time:.2f}s")
            logger.info(f"Average dialog history length: {avg_dialog_length:.1f} messages")

        # Quality breakdown
        logger.info("\n--- BY QUALITY LEVEL ---")
        for quality in ['medium', 'high']:
            quality_results = [r for r in successful if r['quality_level'] == quality]
            if quality_results:
                avg_score_quality = sum(r['audit_score'] for r in quality_results) / len(quality_results)
                logger.info(f"{quality.upper()}: {len(quality_results)} successful, avg score: {avg_score_quality:.2f}/100")

        logger.info("=" * 80)

    def _save_results_to_json(self):
        """Save all results to JSON file for analysis"""
        output_file = f"iteration_43_full_flow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        results_data = {
            'iteration': 43,
            'test_type': 'full_flow',
            'test_user_id': self.test_user_id,
            'start_time': self.test_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'results': self.results,
            'summary': {
                'total_interviews': len(self.results),
                'successful': len([r for r in self.results if r['status'] == 'success']),
                'failed': len([r for r in self.results if r['status'] == 'failed'])
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n[SUCCESS] Results saved to: {output_file}")


async def main():
    """Main entry point"""
    test = Iteration43FullFlowTest()

    try:
        await test.run_2_interviews()
        logger.info("\n[SUCCESS] Iteration 43 Full Flow Test completed!")

    except Exception as e:
        logger.error(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
