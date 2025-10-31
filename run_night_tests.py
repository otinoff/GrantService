#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Night Tests CLI Launcher

Command-line interface for running autonomous night testing.

Usage:
    python run_night_tests.py --cycles 100 --parallel 5
    python run_night_tests.py --cycles 10 --mock-websearch --dry-run
    python run_night_tests.py --resume night_tests/2025-10-31

Created: 2025-10-31
Iteration: 69 - Autonomous Night Testing
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tester.night_orchestrator import NightTestOrchestrator, NightTestConfig
from tester.morning_report_generator import MorningReportGenerator


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Night Test Orchestrator - Autonomous E2E Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 100 cycles with 5 parallel jobs
  python run_night_tests.py --cycles 100 --parallel 5

  # Quick test with 10 cycles, mock WebSearch
  python run_night_tests.py --cycles 10 --mock-websearch

  # Dry run (check setup)
  python run_night_tests.py --cycles 3 --dry-run

  # Resume from checkpoint
  python run_night_tests.py --resume night_tests/2025-10-31

  # Generate report only
  python run_night_tests.py --report-only night_tests/2025-10-31
        """
    )

    parser.add_argument(
        '--cycles',
        type=int,
        default=100,
        help='Number of test cycles to run (default: 100)'
    )

    parser.add_argument(
        '--parallel',
        type=int,
        default=5,
        help='Number of parallel jobs (default: 5)'
    )

    parser.add_argument(
        '--mock-websearch',
        action='store_true',
        help='Use mock WebSearch (saves tokens)'
    )

    parser.add_argument(
        '--no-expert',
        action='store_true',
        help='Disable Expert Agent evaluation'
    )

    parser.add_argument(
        '--artifacts-dir',
        type=str,
        default='night_tests',
        help='Artifacts directory (default: night_tests)'
    )

    parser.add_argument(
        '--max-hours',
        type=int,
        default=8,
        help='Maximum duration in hours (default: 8)'
    )

    parser.add_argument(
        '--checkpoint-interval',
        type=int,
        default=10,
        help='Checkpoint interval (default: 10 cycles)'
    )

    parser.add_argument(
        '--resume',
        type=str,
        metavar='DIR',
        help='Resume from checkpoint in specified directory'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - test setup without full execution'
    )

    parser.add_argument(
        '--report-only',
        type=str,
        metavar='DIR',
        help='Generate report only from existing artifacts'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose logging (DEBUG level)'
    )

    return parser.parse_args()


async def run_tests(config: NightTestConfig, resume: bool = False):
    """
    Run night tests

    Args:
        config: Test configuration
        resume: Resume from checkpoint
    """
    print("\n" + "="*80)
    print("NIGHT TEST ORCHESTRATOR")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Cycles: {config.num_cycles}")
    print(f"Parallel jobs: {config.parallel_jobs}")
    print(f"Mock WebSearch: {config.mock_websearch}")
    print(f"Expert Agent: {config.enable_expert}")
    print(f"Artifacts: {config.artifacts_dir}")
    print(f"Max duration: {config.max_duration_hours}h")
    print("="*80)

    # Initialize orchestrator
    orchestrator = NightTestOrchestrator(config)

    # Run tests
    try:
        summary = await orchestrator.run(resume=resume)

        # Print summary
        print("\n" + "="*80)
        print("TEST RUN COMPLETED")
        print("="*80)
        print(f"Total cycles: {summary['total_cycles']}")
        print(f"Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Duration: {summary['duration_hours']:.2f}h")
        print(f"Avg cycle duration: {summary['avg_cycle_duration']:.1f}s")

        if summary['expert_scores_count'] > 0:
            print(f"Avg expert score: {summary['avg_expert_score']:.2f}/10")

        print(f"\nArtifacts: {summary['artifacts_dir']}")
        print("="*80)

        # Generate morning report
        print("\nGenerating morning report...")
        generator = MorningReportGenerator(Path(summary['artifacts_dir']))
        report = generator.generate_report()

        print(f"✅ Morning report: {summary['artifacts_dir']}/MORNING_REPORT.md")

        return summary

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Progress saved to checkpoint. Resume with: --resume")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_report_only(artifacts_dir: str):
    """
    Generate report from existing artifacts

    Args:
        artifacts_dir: Artifacts directory
    """
    print(f"\nGenerating report from: {artifacts_dir}")

    try:
        generator = MorningReportGenerator(Path(artifacts_dir))
        report = generator.generate_report()

        print(f"✅ Report generated: {artifacts_dir}/MORNING_REPORT.md")
        print("\nPreview:")
        print("-"*80)
        print(report[:500])
        print("...")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    args = parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Report only mode
    if args.report_only:
        generate_report_only(args.report_only)
        return

    # Dry run mode
    if args.dry_run:
        print("\n🧪 DRY RUN MODE")
        args.cycles = min(args.cycles, 3)
        print(f"Running {args.cycles} cycles for testing\n")

    # Create config
    config = NightTestConfig(
        num_cycles=args.cycles,
        parallel_jobs=args.parallel,
        mock_websearch=args.mock_websearch,
        enable_expert=not args.no_expert,
        artifacts_dir=args.artifacts_dir,
        max_duration_hours=args.max_hours,
        checkpoint_interval=args.checkpoint_interval
    )

    # Resume mode
    resume = False
    if args.resume:
        config.artifacts_dir = args.resume
        resume = True
        print(f"\n📂 Resuming from: {args.resume}\n")

    # Run tests
    asyncio.run(run_tests(config, resume=resume))


if __name__ == "__main__":
    main()
