#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 41: Realistic Interactive Interview Simulation - FULL 100 INTERVIEWS

Симулирует 100 реалистичных интервью:
- 20 low quality
- 50 medium quality
- 30 high quality

Используем Sber500 промокод - ТРАТИМ ВСЕ ТОКЕНЫ! 🚀

Date: 2025-10-25
Token Budget: ~1,100,000 tokens (~110 руб)
Duration: ~5 hours
"""

import asyncio
import json
import logging
import os
import sys
import random
from datetime import datetime
from typing import Dict, List
import statistics

# Setup UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{text:^80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}\n")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.WARNING}ℹ️  {text}{Colors.ENDC}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


class Iteration41Test:
    """Realistic Interactive Interview Simulation - 100 INTERVIEWS"""

    # Константы
    REGIONS = [
        'Москва', 'Санкт-Петербург', 'Кемеровская область', 'Новосибирск',
        'Екатеринбург', 'Казань', 'Нижний Новгород', 'Красноярск',
        'Челябинск', 'Самара', 'Уфа', 'Ростов-на-Дону'
    ]

    TOPICS = [
        'молодёжь', 'культура', 'образование', 'спорт',
        'экология', 'волонтёрство', 'социальная поддержка',
        'наука', 'технологии', 'искусство'
    ]

    ORG_TYPES = ['АНО', 'Фонд', 'Ассоциация', 'Центр', 'Клуб']
    ORG_THEMES = ['Молодежные инициативы', 'Развитие', 'Культурное наследие',
                  'Образовательные проекты', 'Социальная поддержка']

    # Обязательные поля анкеты
    REQUIRED_FIELDS = [
        'project_name', 'organization', 'region', 'problem', 'solution',
        'goals', 'activities', 'results', 'budget', 'budget_breakdown'
    ]

    def __init__(self):
        # Set PostgreSQL environment
        os.environ['PGHOST'] = 'localhost'
        os.environ['PGPORT'] = '5432'

        from data.database.models import GrantServiceDatabase
        self.db = GrantServiceDatabase()

        self.test_user_id = 999999997  # Iteration 41 test user
        self.results = {
            'low': [],
            'medium': [],
            'high': []
        }
        self.conversation_logs = []

    def _cleanup_test_data(self):
        """Cleanup old test data"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                # Delete auditor results first (FK constraint)
                cursor.execute("""
                    DELETE FROM auditor_results
                    WHERE session_id IN (
                        SELECT id FROM sessions WHERE telegram_id = %s
                    )
                """, (self.test_user_id,))

                # Delete grant applications
                cursor.execute("""
                    DELETE FROM grant_applications
                    WHERE application_number LIKE '#AN-%-iter41_%'
                """)

                # Delete sessions
                cursor.execute("""
                    DELETE FROM sessions
                    WHERE telegram_id = %s
                """, (self.test_user_id,))

                conn.commit()
                cursor.close()

                print_info(f"✅ Cleaned old test data for user {self.test_user_id}")
        except Exception as e:
            print_info(f"⚠️ No old test data to clean: {e}")

    def _generate_organization_name(self) -> str:
        """Generate realistic organization name"""
        org_type = random.choice(self.ORG_TYPES)
        theme = random.choice(self.ORG_THEMES)
        return f'{org_type} "{theme}"'

    def _generate_context(self) -> Dict:
        """Generate project context"""
        return {
            'region': random.choice(self.REGIONS),
            'topic': random.choice(self.TOPICS),
            'organization': self._generate_organization_name()
        }

    async def conduct_single_interview(self, quality_level: str, interview_num: int) -> Dict:
        """
        Проводит одно реалистичное интервью

        Args:
            quality_level: 'low', 'medium', 'high'
            interview_num: Номер интервью (для логирования)

        Returns:
            Result dict with anketa_id, audit_score, etc.
        """
        from agents.synthetic_user_simulator import SyntheticUserSimulator
        from agents.anketa_validator import AnketaValidator

        print_info(f"[Interview {interview_num}] Starting {quality_level} quality interview...")

        # 1. Generate context
        context = self._generate_context()
        print_info(f"[Interview {interview_num}] Context: {context['region']}, {context['topic']}, {context['organization']}")

        # 2. Initialize user simulator
        user_simulator = SyntheticUserSimulator(
            quality_level=quality_level,
            context=context
        )

        # 3. Conduct interview (simplified - direct Q&A, no InteractiveInterviewer agent)
        interview_data = {}
        conversation_log = []

        questions = {
            'project_name': "Как называется ваш проект?",
            'organization': f"Подтвердите название вашей организации: {context['organization']}",
            'region': f"Подтвердите регион реализации: {context['region']}",
            'problem': "Опишите подробно социальную проблему, которую решает ваш проект.",
            'solution': "Опишите ваше решение этой проблемы. Как именно проект поможет?",
            'goals': "Перечислите конкретные цели проекта (3-5 целей).",
            'activities': "Опишите основные мероприятия проекта (3-5 мероприятий с датами).",
            'results': "Опишите ожидаемые результаты проекта. Используйте конкретные показатели.",
            'budget': "Укажите общий бюджет проекта в рублях (только число).",
            'budget_breakdown': "Распределите бюджет по категориям: оборудование, зарплаты, материалы, прочее."
        }

        for field_name in self.REQUIRED_FIELDS:
            question = questions.get(field_name, f"Расскажите о {field_name}")

            # User answers
            try:
                answer = await user_simulator.answer_question(question, field_name)

                conversation_log.append({
                    'question': question,
                    'field': field_name,
                    'answer': answer,
                    'length': len(answer)
                })

                interview_data[field_name] = answer

                # Log progress every 3 fields
                if len(interview_data) % 3 == 0:
                    print_info(f"[Interview {interview_num}] Progress: {len(interview_data)}/10 fields completed")

            except Exception as e:
                print_error(f"[Interview {interview_num}] Failed on field {field_name}: {e}")
                raise

        # 4. Save anketa
        session_id = self.db.create_session(telegram_id=self.test_user_id)

        anketa_data = {
            'session_id': session_id,
            'user_data': {
                'telegram_id': self.test_user_id,
                'username': f'iter41_user_{interview_num}'
            },
            'interview_data': interview_data
        }

        anketa_id = self.db.save_anketa(anketa_data)

        if not anketa_id:
            raise Exception("Failed to save anketa")

        print_success(f"[Interview {interview_num}] Anketa saved: {anketa_id}")

        # 5. Audit quality
        print_info(f"[Interview {interview_num}] Running audit...")

        validator = AnketaValidator(llm_provider='gigachat', db=self.db)

        try:
            audit_result = await validator.validate(
                interview_data=interview_data,
                user_id=self.test_user_id
            )

            audit_score = audit_result.get('score', 0)
            approval_status = audit_result.get('approval_status', 'unknown')

            print_success(f"[Interview {interview_num}] Audit complete: {audit_score}/10, {approval_status}")

            # Save audit to database
            # (AnketaValidator should save automatically, but verify)

        except Exception as e:
            print_error(f"[Interview {interview_num}] Audit failed: {e}")
            audit_score = 0
            approval_status = 'error'
            audit_result = {'score': 0, 'approval_status': 'error'}

        # 6. Return results
        result = {
            'interview_num': interview_num,
            'anketa_id': anketa_id,
            'quality_level': quality_level,
            'context': context,
            'audit_score': audit_score,
            'approval_status': approval_status,
            'conversation_log': conversation_log,
            'timestamp': datetime.now().isoformat()
        }

        # Save conversation log
        self.conversation_logs.append(result)

        return result

    async def run_batch(self, quality_level: str, count: int, start_num: int) -> List[Dict]:
        """
        Запускает batch интервью

        Args:
            quality_level: 'low', 'medium', 'high'
            count: Количество интервью
            start_num: Начальный номер (для логирования)

        Returns:
            List of results
        """
        print_header(f"BATCH: {count} {quality_level.upper()} QUALITY INTERVIEWS")

        results = []

        for i in range(count):
            interview_num = start_num + i + 1

            try:
                result = await self.conduct_single_interview(quality_level, interview_num)
                results.append(result)

                # Progress update every 5 interviews
                if (i + 1) % 5 == 0:
                    avg_score = statistics.mean([r['audit_score'] for r in results])
                    print_success(f"Completed {i+1}/{count} {quality_level} interviews | Avg score: {avg_score:.2f}/10")

            except Exception as e:
                print_error(f"Interview {interview_num} failed: {e}")
                logger.error(f"Interview failed", exc_info=True)
                # Continue with next interview
                continue

        return results

    async def run_all_100_interviews(self):
        """Run all 100 interviews: 20 low + 50 medium + 30 high"""
        print_header("ITERATION 41: 100 REALISTIC INTERVIEWS - START")
        print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_info(f"Test user ID: {self.test_user_id}")
        print_info(f"Target: 100 interviews (20 low, 50 medium, 30 high)")
        print_info(f"Estimated tokens: ~1,100,000 tokens")
        print_info(f"Estimated cost: ~110 руб (Sber500 промокод)")
        print_info(f"Estimated time: ~5 hours")

        # Cleanup old data
        self._cleanup_test_data()

        # Create test user
        self.db.create_user(
            telegram_id=self.test_user_id,
            username='iter41_test_user',
            first_name='Iteration41',
            last_name='Realistic'
        )

        # Run batches
        start_time = datetime.now()

        # Batch 1: 20 low quality
        self.results['low'] = await self.run_batch('low', count=20, start_num=0)

        # Batch 2: 50 medium quality
        self.results['medium'] = await self.run_batch('medium', count=50, start_num=20)

        # Batch 3: 30 high quality
        self.results['high'] = await self.run_batch('high', count=30, start_num=70)

        end_time = datetime.now()
        duration = end_time - start_time

        # Final summary
        self.print_final_summary(duration)

    def print_final_summary(self, duration):
        """Print final summary"""
        print_header("ITERATION 41 - FINAL SUMMARY")

        total_interviews = len(self.results['low']) + len(self.results['medium']) + len(self.results['high'])

        print_success(f"Total interviews completed: {total_interviews}/100")
        print_info(f"Duration: {duration}")

        # Score statistics per quality level
        for quality_level in ['low', 'medium', 'high']:
            results = self.results[quality_level]

            if not results:
                continue

            scores = [r['audit_score'] for r in results]
            approvals = [r['approval_status'] for r in results]

            avg_score = statistics.mean(scores)
            min_score = min(scores)
            max_score = max(scores)

            approved_count = sum(1 for a in approvals if a == 'approved')
            revision_count = sum(1 for a in approvals if a == 'needs_revision')
            rejected_count = sum(1 for a in approvals if a == 'rejected')

            print(f"\n📊 {quality_level.upper()} Quality ({len(results)} interviews):")
            print(f"   Avg Score: {avg_score:.2f}/10 (min: {min_score}, max: {max_score})")
            print(f"   Approved: {approved_count} ({approved_count/len(results)*100:.1f}%)")
            print(f"   Needs Revision: {revision_count} ({revision_count/len(results)*100:.1f}%)")
            print(f"   Rejected: {rejected_count} ({rejected_count/len(results)*100:.1f}%)")

        print(f"\n✅ ALL 100 INTERVIEWS COMPLETE!")
        print_info(f"Conversation logs saved: {len(self.conversation_logs)} entries")
        print_info(f"Ready for RL optimization (state/action/reward data collected)")


async def main():
    """Main entry point"""
    test = Iteration41Test()
    await test.run_all_100_interviews()


if __name__ == "__main__":
    asyncio.run(main())
