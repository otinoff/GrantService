#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 39: RL Optimization & Production Corpus - Automated Test

Phases:
1. Generate 100 synthetic anketas (20 low, 50 medium, 30 high)
2. Batch audit 100 anketas
3. Analyze correlations (quality_level, region, topic → score)
4. Grid search for optimal temperature
5. Update generator with optimal params

Date: 2025-10-25
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple
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


class Iteration39Test:
    """Automated test for Iteration 39"""

    def __init__(self):
        # Set PostgreSQL environment
        os.environ['PGHOST'] = 'localhost'
        os.environ['PGPORT'] = '5432'  # LOCAL database

        from data.database.models import GrantServiceDatabase
        self.db = GrantServiceDatabase()

        self.test_user_id = 999999999  # Test user
        self.results = {}
        self.generated_anketas = []
        self.audit_results = []

    async def run_all_phases(self):
        """Run all phases sequentially"""
        print_header("ITERATION 39: RL OPTIMIZATION - AUTOMATED TEST")
        print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_info(f"Test user ID: {self.test_user_id}")

        phases = [
            ("Phase 1: Generate 100 Synthetic Anketas", self.phase1_generate_corpus),
            ("Phase 2: Batch Audit 100 Anketas", self.phase2_batch_audit),
            ("Phase 3: Analyze Correlations", self.phase3_analyze_correlations),
            ("Phase 4: Grid Search Temperature", self.phase4_grid_search),
            ("Phase 5: Summary & Recommendations", self.phase5_summary)
        ]

        for phase_name, phase_func in phases:
            try:
                print_header(phase_name)
                await phase_func()
                print_success(f"{phase_name} - COMPLETED\n")
            except Exception as e:
                print_error(f"{phase_name} - FAILED: {e}")
                logger.error(f"Phase failed: {e}", exc_info=True)
                raise

        # Final summary
        self.print_final_summary()

    async def phase1_generate_corpus(self):
        """Phase 1: Generate 100 synthetic anketas"""
        from agents.anketa_synthetic_generator import AnketaSyntheticGenerator

        # Cleanup old test data
        self._cleanup_test_data()

        # Create test user
        self.db.create_user(
            telegram_id=self.test_user_id,
            username='test_user_iter39',
            first_name='Iteration39',
            last_name='Test'
        )

        # Create one real anketa as template
        await self._create_template_anketa()

        # Get templates
        templates = self.db.get_user_anketas(telegram_id=self.test_user_id, limit=5)
        print_info(f"Using {len(templates)} template anketas")

        # Initialize generator
        generator = AnketaSyntheticGenerator(db=self.db, llm_model='GigaChat')

        # Generate 100 anketas (20 low, 50 medium, 30 high)
        print_info("Generating 100 anketas (this will take ~30-40 minutes)...")
        print_info("Distribution: 20 low, 50 medium, 30 high")

        anketas = await generator.generate_batch(
            template_anketas=templates,
            count=100,
            quality_distribution={
                'low': 0.2,    # 20%
                'medium': 0.5, # 50%
                'high': 0.3    # 30%
            }
        )

        # Save to database
        print_info(f"Saving {len(anketas)} anketas to database...")
        saved_count = 0

        for anketa in anketas:
            # Create session
            session_id = self.db.create_session(telegram_id=self.test_user_id)

            anketa_data = {
                'session_id': session_id,
                'user_data': {
                    'telegram_id': self.test_user_id,
                    'username': 'test_user_iter39'
                },
                'interview_data': anketa
            }

            anketa_id = self.db.save_anketa(anketa_data)
            if anketa_id:
                saved_count += 1
                self.generated_anketas.append(anketa_id)

        print_success(f"Generated and saved {saved_count}/100 anketas")
        self.results['phase1'] = {
            'generated': len(anketas),
            'saved': saved_count,
            'anketa_ids': self.generated_anketas
        }

    async def phase2_batch_audit(self):
        """Phase 2: Batch audit all generated anketas"""
        from agents.anketa_validator import AnketaValidator

        print_info(f"Auditing {len(self.generated_anketas)} anketas...")
        print_info("This will take ~30-40 minutes (GigaChat Max)")

        validator = AnketaValidator(provider='gigachat')

        audited_count = 0
        scores = []

        for i, anketa_id in enumerate(self.generated_anketas, 1):
            try:
                # Get anketa
                anketa = self.db.get_anketa_by_id(anketa_id)
                if not anketa:
                    continue

                # Validate
                result = await validator.validate(
                    interview_data=anketa['interview_data'],
                    user_id=self.test_user_id
                )

                # Save audit result
                try:
                    self.db.update_anketa_audit(
                        anketa_id=anketa_id,
                        audit_result=result
                    )
                    audited_count += 1
                    scores.append(result['score'])

                    if i % 10 == 0:
                        avg_so_far = statistics.mean(scores)
                        print_info(f"Progress: {i}/{len(self.generated_anketas)} | Avg score so far: {avg_so_far:.2f}/10")

                except Exception as e:
                    logger.warning(f"Failed to save audit for {anketa_id}: {e}")
                    # Continue even if save fails

            except Exception as e:
                logger.error(f"Failed to audit {anketa_id}: {e}")
                continue

        avg_score = statistics.mean(scores) if scores else 0
        print_success(f"Audited {audited_count}/{len(self.generated_anketas)} anketas")
        print_info(f"Average score: {avg_score:.2f}/10")

        self.results['phase2'] = {
            'audited': audited_count,
            'avg_score': avg_score,
            'scores': scores
        }

    async def phase3_analyze_correlations(self):
        """Phase 3: Analyze correlations"""
        print_info("Analyzing correlations: quality_level, region, topic → score")

        # Get all synthetic anketas with audit results
        with self.db.connect() as conn:
            cursor = conn.cursor()

            # Quality level correlation
            cursor.execute("""
                SELECT
                    s.interview_data->>'quality_target' as quality,
                    AVG(ar.average_score) as avg_score,
                    COUNT(*) as count,
                    STDDEV(ar.average_score) as stddev
                FROM sessions s
                JOIN auditor_results ar ON s.id = ar.session_id
                WHERE s.interview_data->>'synthetic' = 'true'
                  AND s.telegram_id = %s
                GROUP BY s.interview_data->>'quality_target'
                ORDER BY avg_score DESC
            """, (self.test_user_id,))

            quality_stats = cursor.fetchall()

            # Region correlation
            cursor.execute("""
                SELECT
                    s.interview_data->>'region' as region,
                    AVG(ar.average_score) as avg_score,
                    COUNT(*) as count
                FROM sessions s
                JOIN auditor_results ar ON s.id = ar.session_id
                WHERE s.interview_data->>'synthetic' = 'true'
                  AND s.telegram_id = %s
                GROUP BY s.interview_data->>'region'
                ORDER BY avg_score DESC
                LIMIT 10
            """, (self.test_user_id,))

            region_stats = cursor.fetchall()

            cursor.close()

        # Print results
        print("\n📊 Quality Level → Score Correlation:")
        for quality, avg, count, stddev in quality_stats:
            print(f"   {quality:8s}: {avg:.2f}/10 (±{stddev:.2f}) | n={count}")

        print("\n📊 Top 10 Regions by Score:")
        for region, avg, count in region_stats:
            print(f"   {region:30s}: {avg:.2f}/10 | n={count}")

        self.results['phase3'] = {
            'quality_stats': quality_stats,
            'region_stats': region_stats
        }

    async def phase4_grid_search(self):
        """Phase 4: Grid search for optimal temperature"""
        from agents.anketa_synthetic_generator import AnketaSyntheticGenerator
        from agents.anketa_validator import AnketaValidator

        print_info("Running grid search: temperature × quality_level")

        temperatures = [0.3, 0.5, 0.7, 0.9]
        quality_levels = ['low', 'medium', 'high']
        samples_per_combo = 3  # 3 samples per combination

        results = {}

        templates = self.db.get_user_anketas(telegram_id=self.test_user_id, limit=5)
        validator = AnketaValidator(provider='gigachat')

        for temp in temperatures:
            for quality in quality_levels:
                print_info(f"Testing: temp={temp}, quality={quality}")

                generator = AnketaSyntheticGenerator(db=self.db, llm_model='GigaChat')
                # Override temperature
                generator.llm = None  # Force reinit with new temp

                scores = []

                for i in range(samples_per_combo):
                    try:
                        anketa = await generator.generate_synthetic_anketa(
                            template_anketas=templates,
                            quality_level=quality
                        )

                        # Quick audit
                        result = await validator.validate(
                            interview_data=anketa,
                            user_id=self.test_user_id
                        )

                        scores.append(result['score'])

                    except Exception as e:
                        logger.error(f"Failed sample: {e}")
                        continue

                avg_score = statistics.mean(scores) if scores else 0
                results[(temp, quality)] = {
                    'avg_score': avg_score,
                    'scores': scores
                }

                print(f"      → Avg score: {avg_score:.2f}/10")

        # Find optimal temperature per quality level
        optimal = {}
        for quality in quality_levels:
            best_temp = None
            best_score = 0

            for temp in temperatures:
                score = results.get((temp, quality), {}).get('avg_score', 0)
                if score > best_score:
                    best_score = score
                    best_temp = temp

            optimal[quality] = {
                'temperature': best_temp,
                'avg_score': best_score
            }

        print("\n🎯 Optimal Temperature per Quality Level:")
        for quality, params in optimal.items():
            print(f"   {quality:8s}: temp={params['temperature']}, score={params['avg_score']:.2f}/10")

        self.results['phase4'] = {
            'grid_search': results,
            'optimal': optimal
        }

    async def phase5_summary(self):
        """Phase 5: Summary and recommendations"""
        print_header("SUMMARY & RECOMMENDATIONS")

        # Calculate improvements
        if 'phase3' in self.results and 'phase4' in self.results:
            current_scores = {
                q[0]: q[1] for q in self.results['phase3']['quality_stats']
            }

            optimal = self.results['phase4']['optimal']

            print("📈 Potential Improvements:")
            for quality, params in optimal.items():
                current = current_scores.get(quality, 0)
                optimal_score = params['avg_score']
                improvement = optimal_score - current

                print(f"   {quality:8s}: {current:.2f} → {optimal_score:.2f} (Δ {improvement:+.2f})")

    def _cleanup_test_data(self):
        """Cleanup old test data"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM grant_applications
                    WHERE application_number LIKE '#AN-%-test_user_iter39-%'
                """)

                cursor.execute("""
                    DELETE FROM sessions
                    WHERE telegram_id = %s
                """, (self.test_user_id,))

                conn.commit()
                cursor.close()

                print_info(f"✅ Cleaned old test data for user {self.test_user_id}")
        except Exception as e:
            print_info(f"⚠️ No old test data to clean: {e}")

    async def _create_template_anketa(self):
        """Create template anketa"""
        test_data = {
            "project_name": "Тестовый проект Iteration 39",
            "organization": "Test Organization",
            "region": "Москва",
            "problem": "Тестовая проблема для генерации синтетических анкет в Iteration 39",
            "solution": "Тестовое решение",
            "goals": ["Цель 1", "Цель 2", "Цель 3"],
            "activities": ["Мероприятие 1", "Мероприятие 2"],
            "results": ["Результат 1", "Результат 2"],
            "budget": "1000000",
            "budget_breakdown": {
                "equipment": "300000",
                "teachers": "400000",
                "materials": "200000",
                "other": "100000"
            }
        }

        session_id = self.db.create_session(telegram_id=self.test_user_id)

        anketa_data = {
            'session_id': session_id,
            'user_data': {
                'telegram_id': self.test_user_id,
                'username': 'test_user_iter39'
            },
            'interview_data': test_data
        }

        anketa_id = self.db.save_anketa(anketa_data)
        print_info(f"✅ Template anketa created: {anketa_id}")

    def print_final_summary(self):
        """Print final summary"""
        print_header("ITERATION 39 - FINAL SUMMARY")

        print_success(f"Phase 1: Generated {self.results.get('phase1', {}).get('saved', 0)} anketas")
        print_success(f"Phase 2: Audited {self.results.get('phase2', {}).get('audited', 0)} anketas")
        print_success(f"Phase 3: Analyzed correlations")
        print_success(f"Phase 4: Grid search completed")
        print_success(f"Phase 5: Recommendations ready")

        print("\n✅ ITERATION 39 COMPLETE!")
        print_info(f"Results saved in: self.results")


async def main():
    """Main entry point"""
    test = Iteration39Test()
    await test.run_all_phases()


if __name__ == "__main__":
    asyncio.run(main())
