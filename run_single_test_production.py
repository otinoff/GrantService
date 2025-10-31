#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Single Night Test on Production

Запускает ОДИН полный цикл на production сервере через SSH
и проверяет артефакты на каждом этапе.

Usage:
    python run_single_test_production.py
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import json

# Production SSH config
SSH_HOST = "5.35.88.251"
SSH_USER = "root"
SSH_KEY = r"C:\Users\Андрей\.ssh\id_rsa"
REMOTE_PATH = "/var/GrantService"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_step(step_num: int, total: int, name: str):
    """Print step header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}STEP {step_num}/{total}: {name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {message}{RESET}")


def run_ssh_command(command: str, show_output: bool = True) -> tuple[int, str, str]:
    """
    Run command on production via SSH

    Returns:
        (exit_code, stdout, stderr)
    """
    ssh_cmd = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        f"{SSH_USER}@{SSH_HOST}",
        command
    ]

    result = subprocess.run(
        ssh_cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if show_output and result.stdout:
        print(result.stdout)

    if show_output and result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode, result.stdout, result.stderr


def check_artifact(artifact_path: str, min_size: int = 100) -> bool:
    """
    Check if artifact exists and is valid

    Args:
        artifact_path: Path to artifact on production
        min_size: Minimum file size in bytes

    Returns:
        True if artifact is valid
    """
    # Check if file exists and get size
    cmd = f"cd {REMOTE_PATH} && [ -f {artifact_path} ] && wc -c < {artifact_path} || echo 0"
    exit_code, stdout, stderr = run_ssh_command(cmd, show_output=False)

    try:
        file_size = int(stdout.strip())
        if file_size >= min_size:
            print_success(f"Artifact valid: {artifact_path} ({file_size} bytes)")
            return True
        else:
            print_error(f"Artifact too small: {artifact_path} ({file_size} bytes < {min_size})")
            return False
    except ValueError:
        print_error(f"Artifact not found: {artifact_path}")
        return False


def read_artifact(artifact_path: str, max_lines: int = 20) -> str:
    """
    Read artifact content from production

    Args:
        artifact_path: Path to artifact on production
        max_lines: Max lines to read

    Returns:
        Artifact content preview
    """
    cmd = f"cd {REMOTE_PATH} && head -n {max_lines} {artifact_path}"
    exit_code, stdout, stderr = run_ssh_command(cmd, show_output=False)
    return stdout


def main():
    """Main execution"""

    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}SINGLE NIGHT TEST - PRODUCTION{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"SSH Host: {SSH_HOST}")
    print(f"Remote Path: {REMOTE_PATH}")
    print(f"Test: 1 cycle with mock WebSearch")
    print(f"{BLUE}{'='*80}{RESET}\n")

    start_time = time.time()

    # Step 1: Check production connection
    print_step(1, 7, "Check Production Connection")
    cmd = "hostname && uptime"
    exit_code, stdout, stderr = run_ssh_command(cmd)
    if exit_code != 0:
        print_error("Failed to connect to production")
        return 1
    print_success("Connected to production")

    # Step 2: Check PostgreSQL
    print_step(2, 7, "Check PostgreSQL")
    cmd = f"cd {REMOTE_PATH} && PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql -h localhost -p 5434 -U grantservice -d grantservice -c 'SELECT 1' -t"
    exit_code, stdout, stderr = run_ssh_command(cmd, show_output=False)
    if exit_code != 0:
        print_error("PostgreSQL not available")
        return 1
    print_success("PostgreSQL connected")

    # Step 3: Check Qdrant
    print_step(3, 7, "Check Qdrant")
    cmd = "curl -s localhost:6333/collections/test_engineer_kb | head -n 5"
    exit_code, stdout, stderr = run_ssh_command(cmd, show_output=False)
    if exit_code != 0 or "test_engineer_kb" not in stdout:
        print_warning("Qdrant collection 'test_engineer_kb' not found (RAG disabled)")
    else:
        print_success("Qdrant connected")

    # Step 4: Run night test (1 cycle)
    print_step(4, 7, "Run Night Test (1 cycle)")
    print("This will take ~4-5 minutes...\n")

    cmd = f"cd {REMOTE_PATH} && python3 run_night_tests.py --cycles 1 --mock-websearch 2>&1"
    exit_code, stdout, stderr = run_ssh_command(cmd)

    if exit_code != 0:
        print_error("Night test failed")
        print("\nStdout:")
        print(stdout)
        print("\nStderr:")
        print(stderr)
        return 1

    print_success("Night test completed")

    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")

    # Step 5: Verify artifacts structure
    print_step(5, 7, "Verify Artifacts Structure")

    artifacts_dir = f"night_tests/{today}"
    cmd = f"cd {REMOTE_PATH} && ls -lh {artifacts_dir}/cycle_001/"
    exit_code, stdout, stderr = run_ssh_command(cmd)

    if exit_code != 0:
        print_error(f"Artifacts directory not found: {artifacts_dir}/cycle_001/")
        return 1

    print_success("Artifacts directory exists")

    # Step 6: Validate each artifact
    print_step(6, 7, "Validate Artifacts")

    artifacts = [
        ("anketa.txt", 500, "User questionnaire"),
        ("research.txt", 200, "Research findings"),
        ("grant.txt", 1000, "Grant application"),
        ("audit.txt", 200, "Audit report"),
        ("review.txt", 200, "Review report"),
        ("expert_evaluation.json", 50, "Expert evaluation")
    ]

    all_valid = True

    for filename, min_size, description in artifacts:
        artifact_path = f"{artifacts_dir}/cycle_001/{filename}"
        print(f"\nChecking: {description} ({filename})")

        if check_artifact(artifact_path, min_size):
            # Show preview
            content = read_artifact(artifact_path, max_lines=5)
            print(f"{YELLOW}Preview:{RESET}")
            for line in content.split('\n')[:5]:
                print(f"  {line}")
        else:
            all_valid = False

    # Step 7: Show summary
    print_step(7, 7, "Test Summary")

    # Read expert evaluation
    eval_path = f"{artifacts_dir}/cycle_001/expert_evaluation.json"
    cmd = f"cd {REMOTE_PATH} && cat {eval_path}"
    exit_code, stdout, stderr = run_ssh_command(cmd, show_output=False)

    if exit_code == 0:
        try:
            evaluation = json.loads(stdout)
            print(f"\nExpert Evaluation:")
            print(f"  Score: {evaluation.get('score', 'N/A')}/10")
            print(f"  Strengths: {', '.join(evaluation.get('strengths', []))}")
            print(f"  Weaknesses: {', '.join(evaluation.get('weaknesses', []))}")
            print(f"  Compliance:")
            compliance = evaluation.get('compliance', {})
            for key, value in compliance.items():
                status = "✓" if value else "✗"
                print(f"    {status} {key}: {value}")
        except json.JSONDecodeError:
            print_warning("Failed to parse expert evaluation JSON")

    # Read morning report
    report_path = f"{artifacts_dir}/MORNING_REPORT.md"
    cmd = f"cd {REMOTE_PATH} && cat {report_path}"
    exit_code, stdout, stderr = run_ssh_command(cmd, show_output=False)

    if exit_code == 0:
        print(f"\nMorning Report Preview:")
        print("─" * 80)
        for line in stdout.split('\n')[:30]:
            print(line)
        print("─" * 80)

    # Final status
    duration = time.time() - start_time

    print(f"\n{BLUE}{'='*80}{RESET}")
    if all_valid:
        print_success(f"TEST PASSED - All artifacts valid")
    else:
        print_error(f"TEST FAILED - Some artifacts invalid")

    print(f"\nDuration: {duration:.1f}s")
    print(f"Artifacts: {SSH_HOST}:{REMOTE_PATH}/{artifacts_dir}/cycle_001/")
    print(f"{BLUE}{'='*80}{RESET}\n")

    return 0 if all_valid else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
