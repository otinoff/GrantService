#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch testing for all Streamlit admin pages
Can do compile-only check or full headless testing
"""

import sys
import os
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Final 6 pages structure
FINAL_PAGES = [
    "web-admin/pages/🎯_Dashboard.py",
    "web-admin/pages/👥_Пользователи.py",
    "web-admin/pages/🤖_Агенты.py",
    "web-admin/pages/📄_Гранты.py",
    "web-admin/pages/📊_Аналитика.py",
    "web-admin/pages/⚙️_Настройки.py",
]


def compile_check(page_path: str) -> bool:
    """
    Check if Python file compiles without errors

    Args:
        page_path: Path to .py file

    Returns:
        bool: True if compiles, False otherwise
    """
    page_file = Path(page_path)
    if not page_file.exists():
        print(f"  ⚠️  File not found: {page_path}")
        return False

    try:
        result = subprocess.run(
            ["python", "-m", "py_compile", str(page_file)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"  ✅ {page_file.name}")
            return True
        else:
            print(f"  ❌ {page_file.name}")
            print(f"     Error: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  ❌ {page_file.name} (timeout)")
        return False
    except Exception as e:
        print(f"  ❌ {page_file.name} ({str(e)[:100]})")
        return False


async def headless_test(page_path: str, port: int) -> bool:
    """
    Run headless browser test on a page

    Args:
        page_path: Path to .py file
        port: Port number for Streamlit

    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        # Import test function
        from test_page_headless import test_streamlit_page

        success = await test_streamlit_page(page_path, port)
        return success

    except ImportError as e:
        print(f"  ❌ Cannot import test_page_headless: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False


def main():
    """Main test runner"""

    compile_only = "--compile-only" in sys.argv
    test_mode = "COMPILATION CHECK" if compile_only else "FULL HEADLESS TEST"

    print("\n" + "="*70)
    print(f"🧪 TESTING ALL ADMIN PAGES - {test_mode}")
    print("="*70)

    # Find pages to test
    pages_to_test = []
    for page_path in FINAL_PAGES:
        full_path = project_root / page_path
        if full_path.exists():
            pages_to_test.append(str(full_path))
        else:
            print(f"\n⚠️  Page not found (skipping): {page_path}")

    if not pages_to_test:
        print("\n❌ No pages found to test!")
        sys.exit(1)

    print(f"\nTesting {len(pages_to_test)} page(s)...\n")

    # Results tracking
    results = []
    start_time = datetime.now()

    if compile_only:
        # COMPILE CHECK ONLY
        print("="*70)
        print("COMPILATION CHECK")
        print("="*70 + "\n")

        for page_path in pages_to_test:
            success = compile_check(page_path)
            results.append(success)

    else:
        # FULL HEADLESS TESTING
        print("="*70)
        print("HEADLESS BROWSER TESTING")
        print("="*70)
        print("This will take ~2 minutes per page...\n")

        async def run_all_tests():
            port = 8560
            for page_path in pages_to_test:
                page_name = Path(page_path).name
                print(f"\n📄 Testing: {page_name}")

                # First compile check
                if not compile_check(page_path):
                    results.append(False)
                    print(f"  ⏭️  Skipping headless test (compilation failed)")
                    continue

                # Then headless test
                success = await headless_test(page_path, port)
                results.append(success)
                port += 1  # Use different port for each page

        asyncio.run(run_all_tests())

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(results)
    failed = len(results) - passed
    pass_rate = (passed / len(results) * 100) if results else 0

    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print(f"📊 Pass Rate: {pass_rate:.1f}%")
    print(f"⏱️  Duration: {duration:.1f}s")

    if failed > 0:
        print("\n❌ SOME TESTS FAILED")
        print("\nFailed pages:")
        for i, page_path in enumerate(pages_to_test):
            if not results[i]:
                print(f"  - {Path(page_path).name}")

        print("\nCheck errors above and fix issues.")
        print("="*70 + "\n")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED!")
        print("="*70 + "\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
