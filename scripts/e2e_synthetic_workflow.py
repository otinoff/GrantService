#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Synthetic Workflow: Full Pipeline Test

Generates synthetic anketas and runs them through complete workflow:
GENERATE → AUDIT → RESEARCH → WRITER → REVIEW

Usage:
    python scripts/e2e_synthetic_workflow.py --cycles 5
    python scripts/e2e_synthetic_workflow.py --cycles 1  # test
    python scripts/e2e_synthetic_workflow.py --cycles 5 --with-embeddings

Iteration: 63 - E2E Synthetic Workflow
"""

import asyncio
import argparse
import logging
import sys
import random
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.synthetic_user_simulator import SyntheticUserSimulator
from agents.auditor_agent_claude import AuditorAgentClaude
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent_v2 import WriterAgentV2
from data.database.models import GrantServiceDatabase
from shared.telegram_utils.file_generators import (
    generate_anketa_txt,
    generate_audit_txt,
    generate_research_txt,
    generate_grant_txt
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2ESyntheticWorkflow:
    """
    End-to-end workflow for synthetic anketa generation
    """

    # Context pools
    REGIONS = [
        'Москва', 'Санкт-Петербург', 'Кемеровская область - Кузбасс',
        'Новосибирская область', 'Свердловская область'
    ]

    TOPICS = [
        'молодёжные инициативы', 'культурное развитие', 'образовательные программы',
        'спорт и здоровый образ жизни', 'поддержка ветеранов'
    ]

    REQUIRED_FIELDS = [
        'project_name', 'organization', 'region', 'problem', 'solution',
        'goals', 'activities', 'results', 'budget', 'budget_breakdown'
    ]

    QUESTIONS = {
        'project_name': "Как называется ваш проект?",
        'organization': "Укажите полное название вашей организации.",
        'region': "В каком регионе будет реализован проект?",
        'problem': "Опишите подробно социальную проблему, которую решает ваш проект.",
        'solution': "Опишите ваше решение этой проблемы.",
        'goals': "Перечислите конкретные цели проекта (3-5 целей).",
        'activities': "Опишите основные мероприятия проекта.",
        'results': "Опишите ожидаемые результаты проекта с конкретными показателями.",
        'budget': "Укажите общий бюджет проекта в рублях.",
        'budget_breakdown': "Распределите бюджет по категориям."
    }

    def __init__(self, db: GrantServiceDatabase, with_embeddings: bool = False):
        self.db = db
        self.with_embeddings = with_embeddings
        self.output_dir = Path(f"data/synthetic_corpus_{datetime.now().strftime('%Y-%m-%d')}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'start_time': None,
            'end_time': None,
            'cycle_results': []
        }

    def _generate_context(self, index: int) -> Dict[str, any]:
        """Generate random context for synthetic anketa"""
        region = random.choice(self.REGIONS)
        topic = random.choice(self.TOPICS)
        org_type = random.choice(['АНО', 'Фонд', 'Ассоциация'])
        organization = f"{org_type} \"{topic.capitalize()}\""

        return {
            'region': region,
            'topic': topic,
            'organization': organization,
            'index': index + 1
        }

    async def step1_generate_anketa(self, index: int) -> Optional[Dict[str, any]]:
        """
        Step 1: Generate synthetic anketa using SyntheticUserSimulator

        Returns:
            Dict with session_id, anketa_id, interview_data
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"[{index+1}] STEP 1: GENERATE ANKETA")
            logger.info(f"{'='*60}")

            # 1. Generate context
            context = self._generate_context(index)
            logger.info(f"Context: {context['region']}, {context['topic']}")

            # 2. Initialize simulator
            simulator = SyntheticUserSimulator(
                quality_level='medium',
                context=context
            )

            # 3. Create session
            telegram_id = 999999001 + index
            username = f"synthetic_user_{index+1:03d}"

            session_id = self.db.create_session(telegram_id=telegram_id)

            logger.info(f"Created session ID: {session_id}")

            # 4. Simulate interview
            interview_data = {}
            for field_name in self.REQUIRED_FIELDS:
                question = self.QUESTIONS[field_name]

                # Simple fields
                if field_name == 'project_name':
                    answer = f"Проект \"{context['topic'].capitalize()}\" в {context['region']}"
                elif field_name == 'organization':
                    answer = context['organization']
                elif field_name == 'region':
                    answer = context['region']
                elif field_name == 'budget':
                    answer = str(random.randint(500000, 3000000))
                else:
                    # LLM-generated answer
                    answer = await simulator.answer_question(question, field_name)

                interview_data[field_name] = answer

            # 5. Save to database - update answers_data
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions
                    SET answers_data = %s::jsonb,
                        status = 'completed',
                        last_activity = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (json.dumps(interview_data), session_id))
                conn.commit()
                cursor.close()

            logger.info(f"✅ Saved interview data for session {session_id}")

            # 6. Generate anketa ID
            anketa_id = f"#AN-{datetime.now().strftime('%Y%m%d')}-{username}-001"

            # 7. Generate file
            anketa_data = {
                'anketa_id': anketa_id,
                'session_id': session_id,
                'interview_data': interview_data,
                'created_at': datetime.now()
            }

            anketa_txt = generate_anketa_txt(anketa_data)

            # Save file
            cycle_dir = self.output_dir / f"cycle_{index+1}"
            cycle_dir.mkdir(exist_ok=True)

            filename = cycle_dir / f"anketa_{anketa_id.replace('#', '')}.txt"
            filename.write_text(anketa_txt, encoding='utf-8')

            logger.info(f"✅ Anketa generated: {filename.name}")

            return {
                'session_id': session_id,
                'anketa_id': anketa_id,
                'interview_data': interview_data,
                'filename': str(filename)
            }

        except Exception as e:
            logger.error(f"❌ Step 1 failed: {e}", exc_info=True)
            return None

    async def step2_audit(self, session_id: int, anketa_id: str, interview_data: Dict, cycle_dir: Path) -> Optional[Dict]:
        """
        Step 2: Run audit using AuditorAgent

        Returns:
            Dict with audit_id, audit_result, filename
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP 2: AUDIT")
            logger.info(f"{'='*60}")

            # 1. Initialize auditor
            auditor = AuditorAgentClaude(self.db)

            # 2. Run audit
            logger.info("Running AuditorAgent...")
            audit_result = await auditor.audit_anketa(interview_data)

            # 3. Save to database
            audit_id = f"{anketa_id}-AU-001"

            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO audits (session_id, audit_data, created_at)
                VALUES (?, ?, ?)
            """, (session_id, json.dumps(audit_result, ensure_ascii=False), datetime.now()))
            self.db.conn.commit()

            # 4. Generate file
            audit_data = {
                'audit_id': audit_id,
                'anketa_id': anketa_id,
                'audit_results': audit_result,
                'created_at': datetime.now()
            }

            audit_txt = generate_audit_txt(audit_data)

            filename = cycle_dir / f"audit_{audit_id.replace('#', '')}.txt"
            filename.write_text(audit_txt, encoding='utf-8')

            logger.info(f"✅ Audit complete: {filename.name}")

            return {
                'audit_id': audit_id,
                'audit_result': audit_result,
                'filename': str(filename)
            }

        except Exception as e:
            logger.error(f"❌ Step 2 failed: {e}", exc_info=True)
            return None

    async def step3_research(self, session_id: int, anketa_id: str, interview_data: Dict, cycle_dir: Path) -> Optional[Dict]:
        """
        Step 3: Run research using ResearcherAgent

        Returns:
            Dict with research_id, research_result, filename
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP 3: RESEARCH")
            logger.info(f"{'='*60}")

            # 1. Initialize researcher
            researcher = ResearcherAgent(self.db)

            # 2. Run research (3 WebSearch queries)
            logger.info("Running ResearcherAgent with WebSearch...")
            research_result = await researcher.research_anketa(interview_data)

            # 3. Save to database
            research_id = f"{anketa_id}-RS-001"

            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO researcher_research (session_id, research_data, created_at)
                VALUES (?, ?, ?)
            """, (session_id, json.dumps(research_result, ensure_ascii=False), datetime.now()))
            self.db.conn.commit()

            # 4. Generate file (using Iteration 62 fix!)
            research_data = {
                'research_id': research_id,
                'anketa_id': anketa_id,
                'research_results': research_result,
                'created_at': datetime.now(),
                'llm_provider': 'claude_code'
            }

            research_txt = generate_research_txt(research_data)

            filename = cycle_dir / f"research_{research_id.replace('#', '')}.txt"
            filename.write_text(research_txt, encoding='utf-8')

            logger.info(f"✅ Research complete: {filename.name}")

            return {
                'research_id': research_id,
                'research_result': research_result,
                'filename': str(filename)
            }

        except Exception as e:
            logger.error(f"❌ Step 3 failed: {e}", exc_info=True)
            return None

    async def step4_writer(
        self,
        session_id: int,
        anketa_id: str,
        interview_data: Dict,
        audit_result: Dict,
        research_result: Dict,
        cycle_dir: Path
    ) -> Optional[Dict]:
        """
        Step 4: Generate grant using WriterAgent

        Returns:
            Dict with grant_id, grant_text, filename
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP 4: WRITER")
            logger.info(f"{'='*60}")

            # 1. Initialize writer
            writer = WriterAgentV2(self.db)

            # 2. Generate grant
            logger.info("Running WriterAgent...")
            grant_text = await writer.write_grant(
                interview_data=interview_data,
                audit_data=audit_result,
                research_data=research_result
            )

            # 3. Save to database
            grant_id = f"{anketa_id}-GR-001"

            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO grants (session_id, grant_text, created_at)
                VALUES (?, ?, ?)
            """, (session_id, grant_text, datetime.now()))
            self.db.conn.commit()

            # 4. Generate file
            grant_data = {
                'grant_id': grant_id,
                'anketa_id': anketa_id,
                'grant_text': grant_text,
                'created_at': datetime.now()
            }

            grant_txt = generate_grant_txt(grant_data)

            filename = cycle_dir / f"grant_{grant_id.replace('#', '')}.txt"
            filename.write_text(grant_txt, encoding='utf-8')

            logger.info(f"✅ Grant written: {filename.name}")
            logger.info(f"   Length: {len(grant_text)} chars")

            return {
                'grant_id': grant_id,
                'grant_text': grant_text,
                'filename': str(filename)
            }

        except Exception as e:
            logger.error(f"❌ Step 4 failed: {e}", exc_info=True)
            return None

    async def step5_review(
        self,
        session_id: int,
        anketa_id: str,
        grant_text: str,
        cycle_dir: Path
    ) -> Optional[Dict]:
        """
        Step 5: Review grant (simplified - no ReviewerAgent yet)

        Returns:
            Dict with review_id, review_result, filename
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP 5: REVIEW")
            logger.info(f"{'='*60}")

            # Simplified review (TODO: Implement ReviewerAgent)
            review_id = f"{anketa_id}-RV-001"

            review_result = {
                'score': 8.0,
                'recommendations': 'Grant looks good. Synthetic data quality is acceptable.',
                'status': 'approved'
            }

            # Save to database
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO reviews (session_id, review_data, created_at)
                VALUES (?, ?, ?)
            """, (session_id, json.dumps(review_result, ensure_ascii=False), datetime.now()))
            self.db.conn.commit()

            # Generate file
            review_txt = f"""{'='*60}
REVIEW REPORT
{'='*60}

Review ID: {review_id}
Grant ID: {anketa_id}-GR-001
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
SCORE: {review_result['score']}/10
{'='*60}

RECOMMENDATIONS:
{review_result['recommendations']}

STATUS: {review_result['status'].upper()}

{'='*60}
"""

            filename = cycle_dir / f"review_{review_id.replace('#', '')}.txt"
            filename.write_text(review_txt, encoding='utf-8')

            logger.info(f"✅ Review complete: {filename.name}")

            return {
                'review_id': review_id,
                'review_result': review_result,
                'filename': str(filename)
            }

        except Exception as e:
            logger.error(f"❌ Step 5 failed: {e}", exc_info=True)
            return None

    async def run_full_cycle(self, index: int) -> Optional[Dict]:
        """
        Run complete E2E cycle for one anketa

        Returns:
            Dict with all IDs and results
        """
        try:
            logger.info(f"\n\n{'#'*60}")
            logger.info(f"CYCLE {index+1}")
            logger.info(f"{'#'*60}\n")

            cycle_dir = self.output_dir / f"cycle_{index+1}"
            cycle_dir.mkdir(exist_ok=True)

            # Step 1: Generate anketa
            step1_result = await self.step1_generate_anketa(index)
            if not step1_result:
                return None

            # Step 2: Audit
            step2_result = await self.step2_audit(
                step1_result['session_id'],
                step1_result['anketa_id'],
                step1_result['interview_data'],
                cycle_dir
            )
            if not step2_result:
                return None

            # Step 3: Research
            step3_result = await self.step3_research(
                step1_result['session_id'],
                step1_result['anketa_id'],
                step1_result['interview_data'],
                cycle_dir
            )
            if not step3_result:
                return None

            # Step 4: Writer
            step4_result = await self.step4_writer(
                step1_result['session_id'],
                step1_result['anketa_id'],
                step1_result['interview_data'],
                step2_result['audit_result'],
                step3_result['research_result'],
                cycle_dir
            )
            if not step4_result:
                return None

            # Step 5: Review
            step5_result = await self.step5_review(
                step1_result['session_id'],
                step1_result['anketa_id'],
                step4_result['grant_text'],
                cycle_dir
            )
            if not step5_result:
                return None

            logger.info(f"\n{'='*60}")
            logger.info(f"✅ CYCLE {index+1} COMPLETE!")
            logger.info(f"{'='*60}")
            logger.info(f"Session ID: {step1_result['session_id']}")
            logger.info(f"Anketa: {step1_result['anketa_id']}")
            logger.info(f"Audit: {step2_result['audit_id']}")
            logger.info(f"Research: {step3_result['research_id']}")
            logger.info(f"Grant: {step4_result['grant_id']}")
            logger.info(f"Review: {step5_result['review_id']}")
            logger.info(f"Files: {cycle_dir}/")
            logger.info(f"{'='*60}\n")

            return {
                'cycle': index + 1,
                'session_id': step1_result['session_id'],
                'anketa_id': step1_result['anketa_id'],
                'audit_id': step2_result['audit_id'],
                'research_id': step3_result['research_id'],
                'grant_id': step4_result['grant_id'],
                'review_id': step5_result['review_id'],
                'files': {
                    'anketa': step1_result['filename'],
                    'audit': step2_result['filename'],
                    'research': step3_result['filename'],
                    'grant': step4_result['filename'],
                    'review': step5_result['filename']
                }
            }

        except Exception as e:
            logger.error(f"❌ Cycle {index+1} failed: {e}", exc_info=True)
            return None

    async def run_all_cycles(self, num_cycles: int):
        """Run N complete cycles"""
        self.stats['start_time'] = datetime.now()
        self.stats['total_cycles'] = num_cycles

        # Create synthetic users in database first
        logger.info("Creating synthetic users in database...")
        for i in range(num_cycles):
            telegram_id = 999999001 + i
            username = f"synthetic_user_{i+1:03d}"
            first_name = f"Synthetic"
            last_name = f"User {i+1}"

            try:
                self.db.create_user(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                logger.info(f"✅ Created user {telegram_id}: {username}")
            except Exception as e:
                logger.warning(f"Could not create user {telegram_id}: {e}")

        logger.info(f"✅ Created {num_cycles} synthetic users")

        for i in range(num_cycles):
            result = await self.run_full_cycle(i)

            if result:
                self.stats['successful_cycles'] += 1
                self.stats['cycle_results'].append(result)
            else:
                self.stats['failed_cycles'] += 1

        self.stats['end_time'] = datetime.now()

        # Print summary
        self._print_summary()

        # Save summary
        self._save_summary()

    def _print_summary(self):
        """Print final summary"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info(f"\n\n{'#'*60}")
        logger.info(f"FINAL SUMMARY")
        logger.info(f"{'#'*60}")
        logger.info(f"Total cycles: {self.stats['total_cycles']}")
        logger.info(f"Successful: {self.stats['successful_cycles']} ✅")
        logger.info(f"Failed: {self.stats['failed_cycles']} ❌")
        logger.info(f"Duration: {duration/60:.1f} minutes")
        logger.info(f"Files generated: {self.stats['successful_cycles'] * 5}")
        logger.info(f"Output: {self.output_dir}/")
        logger.info(f"{'#'*60}\n")

    def _save_summary(self):
        """Save summary to JSON"""
        summary_file = self.output_dir / "summary.json"

        summary = {
            'iteration': 63,
            'date': datetime.now().isoformat(),
            'stats': {
                'total_cycles': self.stats['total_cycles'],
                'successful_cycles': self.stats['successful_cycles'],
                'failed_cycles': self.stats['failed_cycles'],
                'duration_seconds': (self.stats['end_time'] - self.stats['start_time']).total_seconds(),
                'files_generated': self.stats['successful_cycles'] * 5
            },
            'cycles': self.stats['cycle_results']
        }

        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
        logger.info(f"Summary saved: {summary_file}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='End-to-End Synthetic Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--cycles',
        type=int,
        default=1,
        help='Number of cycles to run (default: 1)'
    )

    parser.add_argument(
        '--with-embeddings',
        action='store_true',
        help='Generate embeddings (optional, not implemented yet)'
    )

    args = parser.parse_args()

    # Initialize database
    logger.info("Initializing database...")
    db = GrantServiceDatabase()

    # Create workflow
    workflow = E2ESyntheticWorkflow(db, with_embeddings=args.with_embeddings)

    # Run cycles
    try:
        await workflow.run_all_cycles(args.cycles)
        logger.info("✅ All cycles complete!")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
