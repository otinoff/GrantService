#!/usr/bin/env python3
"""
Local Test Runner - запускает агента на production, сохраняет результаты локально

Usage:
    python run_test_local.py              # Mock WebSearch
    python run_test_local.py --real       # Real WebSearch
    python run_test_local.py --no-tokens  # Без tracking токенов
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tester.remote_executor import RemoteExecutor


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Local Test Runner - production code, local artifacts"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real WebSearch (default: mock)"
    )
    parser.add_argument(
        "--no-tokens",
        action="store_true",
        help="Disable token tracking"
    )

    args = parser.parse_args()

    print("="*80)
    print("TEST ENGINEER AGENT - Local → Production Execution")
    print("="*80)
    print()
    print("📍 Mode:")
    print("   - Code: Production (SSH to 5.35.88.251)")
    print("   - Artifacts: Local (test_artifacts/)")
    print("   - Tracking: Tokens + Duration + Steps")
    print()

    # Execute
    executor = RemoteExecutor()
    results = executor.execute_remote_test(
        use_mock_websearch=not args.real,
        track_tokens=not args.no_tokens
    )

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    # Status
    status = results.get("status", "unknown")
    if status == "success" or not results.get("errors"):
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")

    # Steps
    if "steps" in results:
        print(f"\n🔧 Steps:")
        for step_name, step_data in results["steps"].items():
            status_emoji = "✅" if step_data.get("status") == "success" else "❌"
            duration = step_data.get("duration_sec", 0)
            print(f"   {status_emoji} {step_name}: {duration:.1f}s")

    # Tokens
    if "tokens" in results:
        tokens = results["tokens"]
        print(f"\n💰 Token Usage:")
        print(f"   Spent today: {tokens.get('spent_today', 'N/A'):,} tokens")
        print(f"   Remaining: {tokens.get('remaining_today', 'N/A'):,} tokens")
        print(f"   Utilization: {tokens.get('utilization_pct', 'N/A')}%")

    # Artifacts
    print(f"\n📁 Artifacts saved to:")
    test_id = results.get("test_id", "unknown")
    artifacts_dir = project_root / "test_artifacts" / f"test_{test_id}"
    print(f"   {artifacts_dir}")
    print(f"   - results.json")
    print(f"   - SUMMARY.md (открой для деталей!)")
    print(f"   - stdout.log")
    print(f"   - stderr.log")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
