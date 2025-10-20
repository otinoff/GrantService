#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Agent Settings UI Integration
======================================
Quick verification script for Phase 3 completion

Author: Grant Architect Agent
Date: 2025-10-06
"""

import sys
from pathlib import Path


def verify_file_changes():
    """Verify that all required changes are in the file"""
    print("=" * 70)
    print("Verification: Agent Settings UI Integration (Phase 3)")
    print("=" * 70)

    page_file = Path(__file__).parent / 'web-admin' / 'pages' / '🤖_Агенты.py'

    if not page_file.exists():
        print(f"❌ File not found: {page_file}")
        return False

    content = page_file.read_text(encoding='utf-8')

    checks = [
        # Imports
        ("Import execute_update", "from utils.postgres_helper import execute_query, execute_update"),
        ("Import agent_settings", "from utils.agent_settings import"),
        ("AGENT_SETTINGS_AVAILABLE flag", "AGENT_SETTINGS_AVAILABLE = True"),

        # New functions
        ("render_interviewer_settings function", "def render_interviewer_settings():"),
        ("render_writer_settings function", "def render_writer_settings():"),
        ("render_generic_agent_settings function", "def render_generic_agent_settings(agent_name: str, display_name: str):"),

        # Integration calls
        ("Interviewer settings call", "render_interviewer_settings()"),
        ("Auditor settings call", "render_generic_agent_settings('auditor', 'Auditor Agent')"),
        ("Planner settings call", "render_generic_agent_settings('planner', 'Planner Agent')"),
        ("Researcher settings call", "render_generic_agent_settings('researcher', 'Researcher Agent')"),
        ("Writer settings call", "render_writer_settings()"),

        # UI elements
        ("Interviewer mode radio", "structured', 'ai_powered"),
        ("Writer provider radio", "gigachat', 'claude_code"),
        ("Temperature slider", "st.slider"),
        ("Save button", "💾 Сохранить"),
    ]

    passed = 0
    failed = 0

    print("\nChecking file content:")
    print("-" * 70)

    for check_name, check_string in checks:
        if check_string in content:
            print(f"[OK] {check_name}")
            passed += 1
        else:
            print(f"[FAIL] {check_name}")
            failed += 1

    print("-" * 70)
    print(f"\nResults: {passed} passed, {failed} failed")

    # Count lines
    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")

    return failed == 0


def verify_module_imports():
    """Verify that modules can be imported"""
    print("\n" + "=" * 70)
    print("Verifying module imports")
    print("=" * 70)

    # Add path
    web_admin_path = str(Path(__file__).parent / 'web-admin')
    if web_admin_path not in sys.path:
        sys.path.insert(0, web_admin_path)

    checks = []

    try:
        from utils.agent_settings import get_agent_settings, save_agent_settings
        print("[OK] utils.agent_settings imported successfully")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] Failed to import utils.agent_settings: {e}")
        checks.append(False)

    try:
        from utils.postgres_helper import execute_query, execute_update
        print("[OK] utils.postgres_helper imported successfully")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] Failed to import utils.postgres_helper: {e}")
        checks.append(False)

    return all(checks)


def main():
    """Run all verifications"""
    results = []

    # File changes
    results.append(verify_file_changes())

    # Module imports
    results.append(verify_module_imports())

    # Final summary
    print("\n" + "=" * 70)
    if all(results):
        print("[SUCCESS] ALL VERIFICATIONS PASSED!")
        print("=" * 70)
        print("\nPhase 3 - UI Integration COMPLETE")
        print("\nNext steps:")
        print("1. Start Streamlit: streamlit run web-admin/app_main.py")
        print("2. Navigate to: 🤖 Агенты page")
        print("3. Check each tab (Interviewer, Auditor, Planner, Researcher, Writer)")
        print("4. Verify settings section appears at bottom of each tab")
        print("5. Test changing settings and clicking Save")
        print("6. Verify changes persist after page refresh")
        print("\nManual testing checklist:")
        print("[ ] Interviewer tab shows mode selection (structured/ai_powered)")
        print("[ ] Writer tab shows provider + temperature slider")
        print("[ ] Auditor tab shows generic settings")
        print("[ ] Planner tab shows generic settings")
        print("[ ] Researcher tab shows generic settings (in Statistics sub-tab)")
        print("[ ] All Save buttons work")
        print("[ ] Settings persist after refresh")
    else:
        print("[FAIL] SOME VERIFICATIONS FAILED")
        print("=" * 70)
        print("\nPlease review the errors above and fix issues.")

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
