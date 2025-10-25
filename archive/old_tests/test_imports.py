#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test imports for Iteration 37 changes"""

import sys
sys.path.insert(0, 'C:/SnowWhiteAI/GrantService')
sys.path.insert(0, 'C:/SnowWhiteAI/GrantService/shared')

print("Testing imports...")

# Test AnketaValidator import
try:
    from agents.anketa_validator import AnketaValidator
    print('[OK] AnketaValidator import success')
except Exception as e:
    print(f'[FAIL] AnketaValidator import failed: {e}')
    sys.exit(1)

# Test handler imports
try:
    from telegram_bot.handlers.anketa_management_handler import AnketaManagementHandler
    print('[OK] AnketaManagementHandler import success')
except Exception as e:
    print(f'[FAIL] AnketaManagementHandler import failed: {e}')
    sys.exit(1)

try:
    from telegram_bot.handlers.grant_handler import GrantHandler
    print('[OK] GrantHandler import success')
except Exception as e:
    print(f'[FAIL] GrantHandler import failed: {e}')
    sys.exit(1)

print("\n[SUCCESS] All imports OK!")
print("\nReady for local bot testing.")
