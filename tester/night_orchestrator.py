#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Night Test Orchestrator - Autonomous testing controller

Runs N E2E test cycles (default 100) autonomously.
- Generates synthetic user profiles
- Executes full E2E pipeline
- Saves artifacts for each cycle
- Integrates Expert Agent evaluation
- Handles errors with retry logic
- Checkpoint/resume capability

Created: 2025-10-31
Iteration: 69 - Autonomous Night Testing
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import traceback
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class NightTestConfig:
    """Configuration for night testing"""
    num_cycles: int = 100
    parallel_jobs: int = 5
    mock_websearch: bool = False
    enable_expert: bool = True
    artifacts_dir: str = "night_tests"
    max_duration_hours: int = 8
    checkpoint_interval: int = 10
    retry_attempts: int = 3
    timeout_per_cycle: int = 600  # 10 minutes


@dataclass
class CycleResult:
    """Result of a single test cycle"""
    cycle_id: int
    success: bool
    duration: float
    anketa_id: Optional[int] = None
    grant_id: Optional[str] = None
    expert_score: Optional[float] = None
    error: Optional[str] = None
    token_usage: Optional[int] = None
    artifacts_saved: bool = False


class NightTestOrchestrator:
    """
    Orchestrates autonomous night testing

    Features:
    - Runs N E2E cycles sequentially or parallel
    - Generates synthetic user profiles
    - Saves artifacts for each cycle
    - Expert Agent evaluation
    - Checkpoint/resume capability
    - Error handling and retries
    - Token tracking
    """

    def __init__(self, config: NightTestConfig):
        """
        Initialize orchestrator

        Args:
            config: NightTestConfig instance
        """
        self.config = config
        self.results: List[CycleResult] = []
        self.start_time = None
        self.checkpoint_file = None

        # Setup artifacts directory
        self.artifacts_dir = Path(config.artifacts_dir) / datetime.now().strftime("%Y-%m-%d")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_file = self.artifacts_dir / "checkpoint.json"
        self.log_file = self.artifacts_dir / "orchestrator.log"

        # Setup logging
        self._setup_logging()

        logger.info("="*80)
        logger.info("NIGHT TEST ORCHESTRATOR INITIALIZED")
        logger.info("="*80)
        logger.info(f"Cycles: {config.num_cycles}")
        logger.info(f"Parallel jobs: {config.parallel_jobs}")
        logger.info(f"Mock WebSearch: {config.mock_websearch}")
        logger.info(f"Expert Agent: {config.enable_expert}")
        logger.info(f"Artifacts: {self.artifacts_dir}")
        logger.info(f"Checkpoint interval: {config.checkpoint_interval}")
        logger.info("="*80)

    def _setup_logging(self):
        """Setup file and console logging"""
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )

        # Add handlers to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)

    async def run(self, resume: bool = False) -> Dict:
        """
        Run night testing

        Args:
            resume: Resume from checkpoint

        Returns:
            Summary dictionary
        """
        self.start_time = time.time()

        # Load checkpoint if resuming
        start_cycle = 1
        if resume and self.checkpoint_file.exists():
            start_cycle = self._load_checkpoint()
            logger.info(f"Resuming from cycle {start_cycle}")

        logger.info("\n" + "="*80)
        logger.info("STARTING NIGHT TEST RUN")
        logger.info("="*80)

        # Import components
        from tester.synthetic_user_generator import SyntheticUserGenerator
        from tester.expert_agent import ExpertAgent
        from data.database.models import GrantServiceDatabase

        # Initialize components
        user_generator = SyntheticUserGenerator()
        expert_agent = None
        if self.config.enable_expert:
            expert_agent = ExpertAgent(use_rag=True)

        # Optional: Database for token tracking (не критично для тестов)
        db = None
        try:
            db = GrantServiceDatabase()
            logger.info("[Database] Connected for token tracking")
        except Exception as e:
            logger.warning(f"[Database] Not available: {e}. Running without DB.")

        # Generate all profiles upfront
        logger.info(f"Generating {self.config.num_cycles} user profiles...")
        profiles = user_generator.generate_profiles(count=self.config.num_cycles)

        # Run cycles
        for cycle_num in range(start_cycle, self.config.num_cycles + 1):
            # Check timeout
            if self._check_timeout():
                logger.warning("Maximum duration reached. Stopping.")
                break

            profile = profiles[cycle_num - 1]

            logger.info("\n" + "-"*80)
            logger.info(f"CYCLE {cycle_num}/{self.config.num_cycles}: {profile.name}")
            logger.info("-"*80)

            # Run cycle with retry
            result = await self._run_cycle_with_retry(
                cycle_num=cycle_num,
                profile=profile,
                db=db,
                expert_agent=expert_agent
            )

            self.results.append(result)

            # Log result
            if result.success:
                logger.info(f"✅ Cycle {cycle_num} SUCCESS - Score: {result.expert_score}/10, Duration: {result.duration:.1f}s")
            else:
                logger.error(f"❌ Cycle {cycle_num} FAILED - Error: {result.error}")

            # Checkpoint
            if cycle_num % self.config.checkpoint_interval == 0:
                self._save_checkpoint(cycle_num)
                self._print_progress()

        # Generate summary
        summary = self._generate_summary()

        logger.info("\n" + "="*80)
        logger.info("NIGHT TEST RUN COMPLETED")
        logger.info("="*80)
        logger.info(f"Total cycles: {len(self.results)}")
        logger.info(f"Success: {summary['successful']}/{summary['total_cycles']}")
        logger.info(f"Duration: {summary['duration_hours']:.2f}h")
        logger.info("="*80)

        return summary

    async def _run_cycle_with_retry(
        self,
        cycle_num: int,
        profile,
        db,
        expert_agent
    ) -> CycleResult:
        """
        Run a single cycle with retry logic

        Args:
            cycle_num: Cycle number
            profile: UserProfile instance
            db: Database instance
            expert_agent: ExpertAgent instance

        Returns:
            CycleResult
        """
        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                if attempt > 1:
                    logger.info(f"Retry attempt {attempt}/{self.config.retry_attempts}")

                result = await self._run_single_cycle(
                    cycle_num=cycle_num,
                    profile=profile,
                    db=db,
                    expert_agent=expert_agent
                )

                return result

            except asyncio.TimeoutError:
                error_msg = f"Timeout after {self.config.timeout_per_cycle}s"
                logger.error(f"Attempt {attempt} failed: {error_msg}")
                if attempt == self.config.retry_attempts:
                    return CycleResult(
                        cycle_id=cycle_num,
                        success=False,
                        duration=self.config.timeout_per_cycle,
                        error=error_msg
                    )

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Attempt {attempt} failed: {error_msg}")
                logger.debug(traceback.format_exc())

                if attempt == self.config.retry_attempts:
                    return CycleResult(
                        cycle_id=cycle_num,
                        success=False,
                        duration=0,
                        error=error_msg
                    )

                # Wait before retry
                await asyncio.sleep(5)

    async def _run_single_cycle(
        self,
        cycle_num: int,
        profile,
        db,
        expert_agent
    ) -> CycleResult:
        """
        Run a single E2E test cycle

        Steps:
        1. Interview (synthetic user)
        2. Auditor
        3. Researcher
        4. Writer
        5. Reviewer
        6. Expert Agent (evaluation)
        7. Save artifacts

        Returns:
            CycleResult
        """
        cycle_start = time.time()

        # Create cycle directory
        cycle_dir = self.artifacts_dir / f"cycle_{cycle_num:03d}"
        cycle_dir.mkdir(parents=True, exist_ok=True)

        # Import E2E modules
        from tests.e2e.modules.interviewer_module import InterviewerTestModule
        from tests.e2e.modules.auditor_module import AuditorTestModule
        from tests.e2e.modules.researcher_module import ResearcherTestModule
        from tests.e2e.modules.writer_module import WriterTestModule
        from tests.e2e.modules.reviewer_module import ReviewerTestModule

        # Initialize modules
        interviewer = InterviewerTestModule(db)
        auditor = AuditorTestModule(db)
        researcher = ResearcherTestModule(db)
        writer = WriterTestModule(db)
        reviewer = ReviewerTestModule(db)

        # Generate unique telegram_id
        telegram_id = 999999000 + cycle_num

        # Step 1: Interview
        logger.info(f"[Cycle {cycle_num}] Step 1/6: Interview")
        anketa_data = await interviewer.run_automated_interview(
            telegram_id=telegram_id,
            username=f"test_cycle_{cycle_num}",
            llm_provider="gigachat"
        )

        # Save anketa
        self._save_artifact(cycle_dir / "anketa.txt", anketa_data.get('full_text', ''))
        self._save_artifact(cycle_dir / "anketa.json", anketa_data)

        # Step 2: Auditor
        logger.info(f"[Cycle {cycle_num}] Step 2/6: Auditor")
        audit_data = await auditor.test_auditor(anketa_data)
        self._save_artifact(cycle_dir / "audit.txt", audit_data.get('audit_text', ''))
        self._save_artifact(cycle_dir / "audit.json", audit_data)

        # Step 3: Researcher
        logger.info(f"[Cycle {cycle_num}] Step 3/6: Researcher")
        research_data = await researcher.test_researcher(
            anketa_data,
            use_mock=self.config.mock_websearch
        )
        self._save_artifact(cycle_dir / "research.txt", research_data.get('research_text', ''))
        self._save_artifact(cycle_dir / "research.json", research_data)

        # Step 4: Writer
        logger.info(f"[Cycle {cycle_num}] Step 4/6: Writer")
        writer_data = await writer.test_writer(anketa_data, research_data)
        self._save_artifact(cycle_dir / "grant.txt", writer_data.get('grant_text', ''))
        self._save_artifact(cycle_dir / "grant.json", writer_data)

        # Step 5: Reviewer
        logger.info(f"[Cycle {cycle_num}] Step 5/6: Reviewer")
        review_data = await reviewer.test_reviewer(writer_data)
        self._save_artifact(cycle_dir / "review.txt", review_data.get('review_text', ''))
        self._save_artifact(cycle_dir / "review.json", review_data)

        # Step 6: Expert Agent
        expert_score = None
        if expert_agent:
            logger.info(f"[Cycle {cycle_num}] Step 6/6: Expert Agent")
            evaluation = expert_agent.evaluate_grant(
                grant_text=writer_data.get('grant_text', ''),
                profile=profile.to_dict(),
                research_text=research_data.get('research_text', ''),
                audit_text=audit_data.get('audit_text', '')
            )
            expert_score = evaluation['score']

            self._save_artifact(cycle_dir / "expert_evaluation.json", evaluation)

            logger.info(f"[Cycle {cycle_num}] Expert Score: {expert_score}/10")

        # Calculate duration
        duration = time.time() - cycle_start

        # Create result
        result = CycleResult(
            cycle_id=cycle_num,
            success=True,
            duration=duration,
            anketa_id=anketa_data.get('anketa_id'),
            grant_id=writer_data.get('grant_id'),
            expert_score=expert_score,
            artifacts_saved=True
        )

        return result

    def _save_artifact(self, path: Path, content):
        """Save artifact to file"""
        try:
            if isinstance(content, (dict, list)):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(str(content))

        except Exception as e:
            logger.error(f"Failed to save artifact {path}: {e}")

    def _check_timeout(self) -> bool:
        """Check if max duration exceeded"""
        elapsed = time.time() - self.start_time
        max_seconds = self.config.max_duration_hours * 3600
        return elapsed > max_seconds

    def _save_checkpoint(self, cycle_num: int):
        """Save checkpoint"""
        checkpoint = {
            "last_completed_cycle": cycle_num,
            "timestamp": datetime.now().isoformat(),
            "results_count": len(self.results)
        }

        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)

            logger.info(f"Checkpoint saved: cycle {cycle_num}")

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> int:
        """Load checkpoint and return next cycle number"""
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)

            last_cycle = checkpoint.get('last_completed_cycle', 0)
            return last_cycle + 1

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return 1

    def _print_progress(self):
        """Print progress summary"""
        if not self.results:
            return

        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        avg_duration = sum(r.duration for r in self.results) / len(self.results)

        logger.info("\n" + "="*80)
        logger.info("PROGRESS UPDATE")
        logger.info("="*80)
        logger.info(f"Completed: {len(self.results)}/{self.config.num_cycles}")
        logger.info(f"Success: {successful} ({100*successful/len(self.results):.1f}%)")
        logger.info(f"Failed: {failed}")
        logger.info(f"Avg duration: {avg_duration:.1f}s")
        logger.info("="*80)

    def _generate_summary(self) -> Dict:
        """Generate test run summary"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful

        duration = time.time() - self.start_time

        # Expert scores
        expert_scores = [r.expert_score for r in self.results if r.expert_score is not None]
        avg_score = sum(expert_scores) / len(expert_scores) if expert_scores else 0

        summary = {
            "total_cycles": total,
            "successful": successful,
            "failed": failed,
            "success_rate": 100 * successful / total if total > 0 else 0,
            "duration_seconds": duration,
            "duration_hours": duration / 3600,
            "avg_cycle_duration": sum(r.duration for r in self.results) / total if total > 0 else 0,
            "avg_expert_score": avg_score,
            "expert_scores_count": len(expert_scores),
            "artifacts_dir": str(self.artifacts_dir)
        }

        return summary


if __name__ == "__main__":
    # Test orchestrator
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Test config
    config = NightTestConfig(
        num_cycles=3,  # Test with 3 cycles
        parallel_jobs=1,
        mock_websearch=True,
        enable_expert=True,
        checkpoint_interval=1
    )

    orchestrator = NightTestOrchestrator(config)

    # Run
    try:
        summary = asyncio.run(orchestrator.run())

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        for key, value in summary.items():
            print(f"{key}: {value}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
