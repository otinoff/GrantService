"""
Remote Executor for Test Engineer Agent

Запускает агента на production сервере через SSH,
но сохраняет результаты локально с tracking токенов.
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class RemoteExecutor:
    """Execute Test Engineer Agent on production via SSH"""

    def __init__(
        self,
        ssh_host: str = "5.35.88.251",
        ssh_user: str = "root",
        ssh_key: str = r"C:\Users\Андрей\.ssh\id_rsa",
        remote_path: str = "/var/GrantService",
        local_artifacts_dir: str = None
    ):
        """
        Initialize remote executor

        Args:
            ssh_host: Production server IP
            ssh_user: SSH user
            ssh_key: Path to SSH private key
            remote_path: Path to GrantService on production
            local_artifacts_dir: Where to save artifacts locally
        """
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_key = ssh_key
        self.remote_path = remote_path

        # Local artifacts directory
        if local_artifacts_dir is None:
            local_artifacts_dir = Path(__file__).parent.parent / "test_artifacts"

        self.local_artifacts_dir = Path(local_artifacts_dir)
        self.local_artifacts_dir.mkdir(parents=True, exist_ok=True)

        print(f"[Local] Artifacts: {self.local_artifacts_dir}")
        print(f"[Remote] Server: {ssh_user}@{ssh_host}:{remote_path}")

    def execute_remote_test(
        self,
        use_mock_websearch: bool = True,
        track_tokens: bool = True
    ) -> Dict:
        """
        Execute E2E test on production, save results locally

        Args:
            use_mock_websearch: Use mock WebSearch
            track_tokens: Track token usage

        Returns:
            Test results with token tracking
        """
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("\n" + "="*80)
        print("[RUN] REMOTE EXECUTION - Test Engineer Agent")
        print("="*80)
        print(f"Test ID: {test_id}")
        print(f"Mode: {'Mock WebSearch' if use_mock_websearch else 'Real WebSearch'}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # Build SSH command
        websearch_flag = "--mock-websearch" if use_mock_websearch else "--real-websearch"

        ssh_cmd = [
            "ssh",
            "-i", self.ssh_key,
            "-o", "StrictHostKeyChecking=no",
            f"{self.ssh_user}@{self.ssh_host}",
            f"cd {self.remote_path} && "
            f"export PGHOST=localhost && "
            f"export PGPORT=5434 && "
            f"export PGDATABASE=grantservice && "
            f"export PGUSER=grantservice && "
            f"export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' && "
            f"python3 tester/agent.py {websearch_flag} --output-json"
        ]

        # Execute remote test
        print("\n[WAIT] Executing test on production...")
        start_time = time.time()

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 min timeout
            )

            duration = time.time() - start_time

            # Parse output
            output = result.stdout
            error_output = result.stderr

            # Try to extract JSON result
            test_results = self._parse_output(output)

            if test_results:
                print(f"[OK] Test completed in {duration:.1f}s")
            else:
                print(f"[WARN] Test finished but no JSON output found")
                test_results = {
                    "test_id": test_id,
                    "status": "partial",
                    "error": "No JSON output"
                }

            # Add metadata
            test_results["execution"] = {
                "mode": "remote",
                "duration_sec": duration,
                "ssh_host": self.ssh_host,
                "timestamp": datetime.now().isoformat()
            }

            # Track tokens if enabled
            if track_tokens:
                token_info = self._get_token_info()
                test_results["tokens"] = token_info

            # Save results locally
            self._save_results_locally(test_id, test_results, output, error_output)

            return test_results

        except subprocess.TimeoutExpired:
            print("[FAIL] Test timed out after 10 minutes")
            return {
                "test_id": test_id,
                "status": "timeout",
                "error": "Execution timeout (10 min)"
            }

        except Exception as e:
            print(f"[FAIL] Execution failed: {e}")
            return {
                "test_id": test_id,
                "status": "error",
                "error": str(e)
            }

    def _parse_output(self, output: str) -> Optional[Dict]:
        """Extract JSON result from output"""
        try:
            # Try to find JSON block
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                return json.loads(json_str)

            # Try to parse as direct JSON
            lines = output.split("\n")
            for line in lines:
                if line.strip().startswith("{"):
                    try:
                        return json.loads(line.strip())
                    except:
                        continue

            return None

        except Exception as e:
            print(f"[WARN] Failed to parse output: {e}")
            return None

    def _get_token_info(self) -> Dict:
        """
        Get token usage info from production DB

        Returns token info with spent/remaining balance
        """
        # Query production DB for token balance
        ssh_cmd = [
            "ssh",
            "-i", self.ssh_key,
            "-o", "StrictHostKeyChecking=no",
            f"{self.ssh_user}@{self.ssh_host}",
            f"cd {self.remote_path} && "
            f"PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' "
            f"psql -h localhost -p 5434 -U grantservice -d grantservice -t -c "
            f"\"SELECT SUM(tokens_used) as total FROM llm_call_logs WHERE created_at > NOW() - INTERVAL '1 day';\""
        ]

        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                tokens_today = int(result.stdout.strip()) if result.stdout.strip() else 0
            else:
                tokens_today = 0

            # Estimate remaining (assuming 100k daily limit)
            daily_limit = 100000
            remaining = max(0, daily_limit - tokens_today)

            return {
                "spent_today": tokens_today,
                "remaining_today": remaining,
                "daily_limit": daily_limit,
                "utilization_pct": round(tokens_today / daily_limit * 100, 1)
            }

        except Exception as e:
            print(f"[WARN] Token tracking failed: {e}")
            return {
                "spent_today": None,
                "remaining_today": None,
                "error": str(e)
            }

    def _save_results_locally(
        self,
        test_id: str,
        results: Dict,
        stdout: str,
        stderr: str
    ):
        """Save all test artifacts locally"""

        # Create test directory
        test_dir = self.local_artifacts_dir / f"test_{test_id}"
        test_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON results
        results_file = test_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, indent=2, fp=f, ensure_ascii=False)

        # Save stdout
        stdout_file = test_dir / "stdout.log"
        with open(stdout_file, "w", encoding="utf-8") as f:
            f.write(stdout)

        # Save stderr
        stderr_file = test_dir / "stderr.log"
        with open(stderr_file, "w", encoding="utf-8") as f:
            f.write(stderr)

        # Create summary file with token info
        summary_file = test_dir / "SUMMARY.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# Test Run: {test_id}\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write(f"## Execution\n\n")
            f.write(f"- **Mode:** Remote (SSH to {self.ssh_host})\n")
            f.write(f"- **Duration:** {results.get('execution', {}).get('duration_sec', 0):.1f}s\n")
            f.write(f"- **Status:** {results.get('status', 'unknown')}\n\n")

            # Token info
            if "tokens" in results:
                tokens = results["tokens"]
                f.write(f"## Token Usage\n\n")
                f.write(f"- **Spent Today:** {tokens.get('spent_today', 'N/A'):,} tokens\n")
                f.write(f"- **Remaining Today:** {tokens.get('remaining_today', 'N/A'):,} tokens\n")
                f.write(f"- **Daily Limit:** {tokens.get('daily_limit', 'N/A'):,} tokens\n")
                f.write(f"- **Utilization:** {tokens.get('utilization_pct', 'N/A')}%\n\n")

            # Steps summary
            if "steps" in results:
                f.write(f"## Steps\n\n")
                for step_name, step_data in results["steps"].items():
                    status = step_data.get("status", "unknown")
                    duration = step_data.get("duration_sec", 0)
                    f.write(f"- **{step_name}:** {status} ({duration:.1f}s)\n")

        print(f"\n[DIR] Results saved to: {test_dir}")
        print(f"   - results.json")
        print(f"   - SUMMARY.md (with token tracking)")
        print(f"   - stdout.log")
        print(f"   - stderr.log")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Remote Test Executor")
    parser.add_argument(
        "--real-websearch",
        action="store_true",
        help="Use real WebSearch (default: mock)"
    )
    parser.add_argument(
        "--no-token-tracking",
        action="store_true",
        help="Disable token tracking"
    )

    args = parser.parse_args()

    # Execute remote test
    executor = RemoteExecutor()
    results = executor.execute_remote_test(
        use_mock_websearch=not args.real_websearch,
        track_tokens=not args.no_token_tracking
    )

    # Print summary
    print("\n" + "="*80)
    if results.get("status") == "success":
        print("[OK] TEST PASSED")
    else:
        print("[FAIL] TEST FAILED")
    print("="*80)

    if "tokens" in results:
        tokens = results["tokens"]
        print(f"\n[TOKENS] Token Usage:")
        print(f"   Spent today: {tokens.get('spent_today', 'N/A'):,}")
        print(f"   Remaining: {tokens.get('remaining_today', 'N/A'):,}")
        print(f"   Utilization: {tokens.get('utilization_pct', 'N/A')}%")


if __name__ == "__main__":
    main()
