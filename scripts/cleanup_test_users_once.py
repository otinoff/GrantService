#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-time cleanup of test users to reset E2E test data"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-admin"))

from utils.postgres_helper import execute_update

def main():
    print("=" * 60)
    print("ONE-TIME CLEANUP: Deleting test users to reset E2E tests")
    print("=" * 60)

    test_telegram_ids = [999999999, 999888777]

    for test_id in test_telegram_ids:
        print(f"\nDeleting test user {test_id}...")

        # Delete in correct order (FK constraints)
        print("  - Deleting grants...")
        execute_update("DELETE FROM grants WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)", (test_id,))

        print("  - Deleting researcher_research...")
        execute_update("DELETE FROM researcher_research WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)", (test_id,))

        print("  - Deleting planner_structures...")
        execute_update("DELETE FROM planner_structures WHERE session_id IN (SELECT id FROM sessions WHERE telegram_id = %s)", (test_id,))

        print("  - Deleting auditor_results...")
        execute_update("DELETE FROM auditor_results WHERE session_id IN (SELECT id FROM sessions WHERE telegram_id = %s)", (test_id,))

        print("  - Deleting user_answers...")
        execute_update("DELETE FROM user_answers WHERE session_id IN (SELECT id FROM sessions WHERE telegram_id = %s)", (test_id,))

        print("  - Deleting sessions...")
        execute_update("DELETE FROM sessions WHERE telegram_id = %s", (test_id,))

        print("  - Deleting user...")
        execute_update("DELETE FROM users WHERE telegram_id = %s", (test_id,))

        print(f"  ✓ User {test_id} deleted")

    print("\n" + "=" * 60)
    print("Cleanup complete! Now run E2E tests:")
    print("pytest tests/integration/test_end_to_end_grant_flow.py -v")
    print("=" * 60)

if __name__ == "__main__":
    main()
