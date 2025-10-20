#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест web-admin/utils/agent_settings.py
Запускается из директории web-admin
"""

import sys
from pathlib import Path

# Add current dir and parent to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct import bypassing utils package __init__
import importlib.util
spec = importlib.util.spec_from_file_location("agent_settings", Path(__file__).parent / "utils" / "agent_settings.py")
agent_settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_settings)

get_agent_settings = agent_settings.get_agent_settings
save_agent_settings = agent_settings.save_agent_settings
get_interviewer_mode = agent_settings.get_interviewer_mode
get_agent_provider = agent_settings.get_agent_provider
is_claude_code_enabled = agent_settings.is_claude_code_enabled


def main():
    print("=" * 70)
    print("TEST: web-admin/utils/agent_settings.py")
    print("=" * 70)

    # Test 1
    print("\n[TEST 1] get_agent_settings('interviewer')")
    settings = get_agent_settings('interviewer')
    print(f"  Mode: {settings['mode']}")
    print(f"  Provider: {settings['provider']}")
    print(f"  Config: {settings['config']}")
    print("  ✓ PASSED")

    # Test 2
    print("\n[TEST 2] get_interviewer_mode()")
    mode = get_interviewer_mode()
    print(f"  Current mode: {mode}")
    print("  ✓ PASSED")

    # Test 3
    print("\n[TEST 3] get_agent_provider('writer')")
    provider = get_agent_provider('writer')
    print(f"  Writer provider: {provider}")
    print("  ✓ PASSED")

    # Test 4
    print("\n[TEST 4] is_claude_code_enabled('interviewer')")
    enabled = is_claude_code_enabled('interviewer')
    print(f"  Claude Code enabled: {enabled}")
    print("  ✓ PASSED")

    # Test 5
    print("\n[TEST 5] save_agent_settings() -> change and restore")
    original = get_agent_settings('interviewer')
    orig_mode = original['mode']
    print(f"  Original mode: {orig_mode}")

    # Change
    result = save_agent_settings('interviewer', mode='ai_powered')
    print(f"  Save ai_powered: {result}")

    # Verify
    updated = get_agent_settings('interviewer')
    print(f"  Updated mode: {updated['mode']}")
    assert updated['mode'] == 'ai_powered', "Mode should be ai_powered"

    # Restore
    save_agent_settings('interviewer', mode=orig_mode)
    restored = get_agent_settings('interviewer')
    print(f"  Restored mode: {restored['mode']}")
    assert restored['mode'] == orig_mode, "Mode should be restored"
    print("  ✓ PASSED")

    # Test 6
    print("\n[TEST 6] get_agent_settings('nonexistent') -> defaults")
    defaults = get_agent_settings('nonexistent_agent')
    print(f"  Default mode: {defaults['mode']}")
    print(f"  Default provider: {defaults['provider']}")
    assert defaults['mode'] == 'active'
    assert defaults['provider'] == 'gigachat'
    print("  ✓ PASSED")

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED (6/6)")
    print("=" * 70)
    print("\nФайл работает корректно!")
    print("Функции:")
    print("  - get_agent_settings()")
    print("  - save_agent_settings()")
    print("  - get_interviewer_mode()")
    print("  - get_agent_provider()")
    print("  - is_claude_code_enabled()")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
