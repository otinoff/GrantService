#!/usr/bin/env python3
"""
E2E Test: Complete Grant Application Workflow

Iteration 66: E2E Test Suite
Tests PRODUCTION code path: Interview → Audit → Research → Write → Review

Architecture:
- Uses modular test components (tests/e2e/modules/)
- Each step validates against success criteria from past iterations
- Saves artifacts for manual inspection
- Tests production database writes

Based on successful iterations:
- Iteration 63: InteractiveInterviewer (anketa generation)
- Iteration 54: AuditorAgent (audit with unwrap)
- Iteration 60: ResearcherAgent (WebSearch)
- Iteration 65: WriterAgent ('application' key fix)
- Iteration 58: ReviewerAgent (review structure)

Usage:
    python -m pytest tests/e2e/test_grant_workflow.py -v -s

Or run directly:
    python tests/e2e/test_grant_workflow.py
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import production database
from data.database.models import GrantServiceDatabase

# Import test modules
from tests.e2e.modules import (
    InterviewerTestModule,
    AuditorTestModule,
    ResearcherTestModule,
    WriterTestModule,
    ReviewerTestModule
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2EGrantWorkflowTest:
    """
    Complete E2E test of grant application workflow

    Tests full production pipeline in 5 steps:
    1. Interview → Generate anketa (14+ questions)
    2. Audit → Validate anketa completeness (score > 0)
    3. Research → WebSearch for grant data (3+ sources)
    4. Write → Generate grant application (15000+ chars)
    5. Review → Critique grant quality (score > 0)
    """

    def __init__(self):
        """Initialize test with production database"""
        self.db = GrantServiceDatabase()
        self.logger = logging.getLogger(__name__)

        # Initialize test modules
        self.interviewer = InterviewerTestModule(self.db)
        self.auditor = AuditorTestModule(self.db)
        self.researcher = ResearcherTestModule(self.db)
        self.writer = WriterTestModule(self.db)
        self.reviewer = ReviewerTestModule(self.db)

        # Setup artifacts directory
        self.artifacts_dir = self._setup_artifacts_dir()

    def _setup_artifacts_dir(self) -> Path:
        """Create artifacts directory for this test run"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        artifacts_dir = Path(__file__).parent.parent.parent / 'iterations' / 'Iteration_66_E2E_Test_Suite' / 'artifacts' / f'run_{timestamp}'
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Artifacts directory: {artifacts_dir}")
        return artifacts_dir

    async def run_workflow(self) -> dict:
        """
        Run complete E2E workflow

        Returns:
            Dict with results from all 5 steps

        Raises:
            AssertionError: If any step fails validation
        """
        self.logger.info("="*80)
        self.logger.info("E2E GRANT WORKFLOW TEST - STARTING")
        self.logger.info("="*80)

        results = {}

        try:
            # STEP 1: Generate Anketa (Interview)
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 1/5: INTERVIEW (Generate Anketa)")
            self.logger.info("="*80)

            anketa_data = await self.interviewer.run_automated_interview(
                telegram_id=999999001,
                username="e2e_test_user",
                llm_provider="gigachat"
            )

            results['anketa'] = anketa_data

            # Export anketa
            anketa_file = self.artifacts_dir / 'step1_anketa.txt'
            self.interviewer.export_to_file(anketa_data, anketa_file)

            self.logger.info(f"✅ STEP 1 COMPLETE: {anketa_data['questions_count']} questions, {anketa_data['total_chars']} chars")

            # STEP 2: Audit Anketa
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 2/5: AUDIT (Validate Anketa)")
            self.logger.info("="*80)

            audit_data = await self.auditor.test_auditor(
                anketa_data=anketa_data,
                llm_provider="gigachat"
            )

            results['audit'] = audit_data

            # Export audit
            audit_file = self.artifacts_dir / 'step2_audit.txt'
            self.auditor.export_to_file(audit_data, audit_file)

            self.logger.info(f"✅ STEP 2 COMPLETE: Score {audit_data['average_score']}/10, status={audit_data['approval_status']}")

            # STEP 3: Research
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 3/5: RESEARCH (WebSearch)")
            self.logger.info("="*80)

            research_data = await self.researcher.test_researcher(
                anketa_data=anketa_data,
                llm_provider="claude_code"  # WebSearch enabled
            )

            results['research'] = research_data

            # Export research
            research_file = self.artifacts_dir / 'step3_research.txt'
            self.researcher.export_to_file(research_data, research_file)

            self.logger.info(f"✅ STEP 3 COMPLETE: {research_data['sources_count']} sources found")

            # STEP 4: Write Grant
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 4/5: WRITER (Generate Grant)")
            self.logger.info("="*80)

            grant_data = await self.writer.test_writer(
                anketa_data=anketa_data,
                research_data=research_data,
                llm_provider="gigachat"
            )

            results['grant'] = grant_data

            # Export grant
            grant_file = self.artifacts_dir / 'step4_grant.txt'
            self.writer.export_to_file(grant_data, grant_file)

            self.logger.info(f"✅ STEP 4 COMPLETE: {grant_data['grant_length']} characters")

            # STEP 5: Review Grant
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 5/5: REVIEWER (Critique Grant)")
            self.logger.info("="*80)

            review_data = await self.reviewer.test_reviewer(
                grant_data=grant_data,
                llm_provider="gigachat"
            )

            results['review'] = review_data

            # Export review
            review_file = self.artifacts_dir / 'step5_review.txt'
            self.reviewer.export_to_file(review_data, review_file)

            self.logger.info(f"✅ STEP 5 COMPLETE: Score {review_data['review_score']}")

            # Save summary
            self._save_summary(results)

            self.logger.info("\n" + "="*80)
            self.logger.info("E2E WORKFLOW COMPLETE - ALL STEPS PASSED")
            self.logger.info("="*80)

            return results

        except Exception as e:
            self.logger.error(f"\n❌ WORKFLOW FAILED: {e}")
            self._save_error_summary(results, e)
            raise

    def _save_summary(self, results: dict):
        """Save test summary to file"""
        summary_file = self.artifacts_dir / 'SUMMARY.txt'

        lines = []
        lines.append("="*80)
        lines.append("E2E GRANT WORKFLOW TEST - SUMMARY")
        lines.append("="*80)
        lines.append(f"\nTest Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Artifacts: {self.artifacts_dir}")

        lines.append("\n" + "="*80)
        lines.append("RESULTS")
        lines.append("="*80)

        if 'anketa' in results:
            lines.append(f"\n✅ STEP 1 - INTERVIEW:")
            lines.append(f"   Anketa ID: {results['anketa']['anketa_id']}")
            lines.append(f"   Questions: {results['anketa']['questions_count']}")
            lines.append(f"   Total Chars: {results['anketa']['total_chars']}")

        if 'audit' in results:
            lines.append(f"\n✅ STEP 2 - AUDIT:")
            lines.append(f"   Audit ID: {results['audit']['audit_id']}")
            lines.append(f"   Average Score: {results['audit']['average_score']}/10")
            lines.append(f"   Approval Status: {results['audit']['approval_status']}")

        if 'research' in results:
            lines.append(f"\n✅ STEP 3 - RESEARCH:")
            lines.append(f"   Research ID: {results['research']['research_id']}")
            lines.append(f"   Sources: {results['research']['sources_count']}")

        if 'grant' in results:
            lines.append(f"\n✅ STEP 4 - WRITER:")
            lines.append(f"   Grant ID: {results['grant']['grant_id']}")
            lines.append(f"   Length: {results['grant']['grant_length']} chars")

        if 'review' in results:
            lines.append(f"\n✅ STEP 5 - REVIEWER:")
            lines.append(f"   Review ID: {results['review']['review_id']}")
            lines.append(f"   Score: {results['review']['review_score']}")
            lines.append(f"   Strengths: {len(results['review']['strengths'])}")
            lines.append(f"   Weaknesses: {len(results['review']['weaknesses'])}")
            lines.append(f"   Recommendations: {len(results['review']['recommendations'])}")

        lines.append("\n" + "="*80)
        lines.append("TEST STATUS: PASSED ✅")
        lines.append("="*80)

        summary_file.write_text('\n'.join(lines), encoding='utf-8')
        self.logger.info(f"Summary saved: {summary_file}")

    def _save_error_summary(self, results: dict, error: Exception):
        """Save error summary"""
        error_file = self.artifacts_dir / 'ERROR.txt'

        lines = []
        lines.append("="*80)
        lines.append("E2E WORKFLOW TEST - FAILED")
        lines.append("="*80)
        lines.append(f"\nError: {error}")
        lines.append(f"\nCompleted Steps: {list(results.keys())}")

        error_file.write_text('\n'.join(lines), encoding='utf-8')


async def main():
    """Run E2E test"""
    test = E2EGrantWorkflowTest()
    results = await test.run_workflow()
    return results


if __name__ == '__main__':
    asyncio.run(main())
