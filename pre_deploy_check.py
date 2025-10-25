#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-Deployment Check Script

Запускает все критичные проверки перед деплоем:
1. Unit tests
2. Integration tests
3. Type checking (mypy)
4. Code style (optional)

Usage:
    python pre_deploy_check.py

Exit codes:
    0 - All checks passed, safe to deploy
    1 - Some checks failed, DO NOT deploy

Author: Claude Code
Created: 2025-10-22
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for output"""
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_failure(text: str):
    """Print failure message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """
    Run a command and return success status + output

    Args:
        cmd: Command to run as list
        description: Description for logging

    Returns:
        (success: bool, output: str)
    """
    print(f"{Colors.OKCYAN}Running: {description}...{Colors.ENDC}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        success = result.returncode == 0
        output = result.stdout + result.stderr

        return success, output

    except subprocess.TimeoutExpired:
        return False, "Command timed out after 5 minutes"
    except Exception as e:
        return False, f"Command failed: {str(e)}"


def check_unit_tests() -> bool:
    """Run unit tests"""
    print_header("UNIT TESTS")

    # Run pytest on tests folder (excluding integration)
    success, output = run_command(
        ["python", "-m", "pytest", "tests/",
         "--ignore=tests/integration/",
         "-v", "--tb=short", "-q"],
        "Unit tests"
    )

    if success:
        # Parse output for passed/failed
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line.lower():
                print_success(f"Unit tests: {line.strip()}")
                break
    else:
        print_failure("Unit tests failed!")
        print(output[-500:])  # Last 500 chars

    return success


def check_integration_tests() -> bool:
    """Run integration tests"""
    print_header("INTEGRATION TESTS")

    # Run pytest on integration tests
    success, output = run_command(
        ["python", "-m", "pytest",
         "tests/integration/test_hardcoded_rp_integration.py",
         "-v", "--tb=short"],
        "Integration tests (Iteration 26)"
    )

    if success:
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line.lower():
                print_success(f"Integration tests: {line.strip()}")
                break
    else:
        print_failure("Integration tests failed!")
        print(output[-500:])

    return success


def check_type_hints() -> bool:
    """Run mypy type checking"""
    print_header("TYPE CHECKING (mypy)")

    # Check if mypy.ini exists
    if not Path("mypy.ini").exists():
        print_warning("mypy.ini not found, skipping type checking")
        return True

    # Run mypy on critical files
    files_to_check = [
        "agents/interactive_interviewer_agent_v2.py",
        "telegram-bot/handlers/interactive_interview_handler.py"
    ]

    all_passed = True

    for file_path in files_to_check:
        if not Path(file_path).exists():
            print_warning(f"File not found: {file_path}")
            continue

        success, output = run_command(
            ["python", "-m", "mypy", file_path],
            f"Type check: {file_path}"
        )

        if success or "Success" in output:
            print_success(f"Type check passed: {file_path}")
        else:
            print_failure(f"Type errors in: {file_path}")
            # Print only error lines
            error_lines = [line for line in output.split('\n') if 'error:' in line.lower()]
            for line in error_lines[:5]:  # First 5 errors
                print(f"  {line}")
            all_passed = False

    return all_passed


def check_critical_files_exist() -> bool:
    """Check that critical files exist"""
    print_header("FILE EXISTENCE CHECK")

    critical_files = [
        "agents/interactive_interviewer_agent_v2.py",
        "telegram-bot/handlers/interactive_interview_handler.py",
        "telegram-bot/main.py",
        "agents/reference_points/reference_point.py",
        "agents/reference_points/reference_point_manager.py"
    ]

    all_exist = True

    for file_path in critical_files:
        if Path(file_path).exists():
            print_success(f"Found: {file_path}")
        else:
            print_failure(f"Missing: {file_path}")
            all_exist = False

    return all_exist


def check_iteration_26_code() -> bool:
    """Verify Iteration 26 code is present"""
    print_header("ITERATION 26 VERIFICATION")

    checks_passed = 0
    total_checks = 3

    # Check 1: Agent has hardcoded_rps check
    agent_file = "agents/interactive_interviewer_agent_v2.py"
    if Path(agent_file).exists():
        with open(agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "hardcoded_rps" in content and "ITERATION 26" in content:
                print_success("Agent has Iteration 26 code (hardcoded_rps)")
                checks_passed += 1
            else:
                print_failure("Agent missing Iteration 26 code!")

    # Check 2: Handler has callback with None support
    handler_file = "telegram-bot/handlers/interactive_interview_handler.py"
    if Path(handler_file).exists():
        with open(handler_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "question: str = None" in content or "question=None" in content:
                print_success("Handler callback supports None (Iteration 26 fix)")
                checks_passed += 1
            else:
                print_failure("Handler callback missing None support!")

    # Check 3: Main.py has hardcoded question #2
    main_file = "telegram-bot/main.py"
    if Path(main_file).exists():
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "hardcoded_rps" in content and "ITERATION 26" in content:
                print_success("Main.py has hardcoded question #2")
                checks_passed += 1
            else:
                print_failure("Main.py missing hardcoded question!")

    print(f"\nIteration 26 checks: {checks_passed}/{total_checks}")
    return checks_passed == total_checks


def main():
    """Run all pre-deployment checks"""
    start_time = time.time()

    print(f"\n{Colors.BOLD}╔{'═'*78}╗{Colors.ENDC}")
    print(f"{Colors.BOLD}║{' '*20}PRE-DEPLOYMENT CHECK SCRIPT{' '*29}║{Colors.ENDC}")
    print(f"{Colors.BOLD}║{' '*78}║{Colors.ENDC}")
    print(f"{Colors.BOLD}║  Running all critical checks before deployment...{' '*24}║{Colors.ENDC}")
    print(f"{Colors.BOLD}╚{'═'*78}╝{Colors.ENDC}\n")

    # Store results
    results = {}

    # Run all checks
    results['files'] = check_critical_files_exist()
    results['iteration_26'] = check_iteration_26_code()
    results['unit_tests'] = check_unit_tests()
    results['integration_tests'] = check_integration_tests()
    results['type_checking'] = check_type_hints()

    # Summary
    elapsed = time.time() - start_time

    print_header("SUMMARY")

    all_passed = all(results.values())

    print(f"Critical Files:      {'✅ PASS' if results['files'] else '❌ FAIL'}")
    print(f"Iteration 26 Code:   {'✅ PASS' if results['iteration_26'] else '❌ FAIL'}")
    print(f"Unit Tests:          {'✅ PASS' if results['unit_tests'] else '❌ FAIL'}")
    print(f"Integration Tests:   {'✅ PASS' if results['integration_tests'] else '❌ FAIL'}")
    print(f"Type Checking:       {'✅ PASS' if results['type_checking'] else '❌ FAIL'}")

    print(f"\nTime elapsed: {elapsed:.1f}s")

    print("\n" + "="*80)

    if all_passed:
        print_success("\n🎉 ALL CHECKS PASSED! Safe to deploy to production.")
        print_success("   Run: ./deploy_v2_to_production.sh")
        return 0
    else:
        print_failure("\n⛔ SOME CHECKS FAILED! DO NOT deploy to production.")
        print_failure("   Fix the issues above and run this script again.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
