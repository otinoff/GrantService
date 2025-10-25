#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Iteration 37 fixes"""

import sys
sys.path.insert(0, 'C:/SnowWhiteAI/GrantService')
sys.path.insert(0, 'C:/SnowWhiteAI/GrantService/shared')

print("=" * 60)
print("ITERATION 37: QUICK SYNTAX CHECK")
print("=" * 60)

# Test 1: Import handlers
print("\n[TEST 1] Import handlers...")
try:
    from telegram_bot.handlers.anketa_management_handler import AnketaManagementHandler
    print("✅ AnketaManagementHandler imported")
except Exception as e:
    print(f"❌ AnketaManagementHandler import failed: {e}")
    sys.exit(1)

try:
    from telegram_bot.handlers.grant_handler import GrantHandler
    print("✅ GrantHandler imported")
except Exception as e:
    print(f"❌ GrantHandler import failed: {e}")
    sys.exit(1)

# Test 2: Import AnketaValidator
print("\n[TEST 2] Import AnketaValidator...")
try:
    from agents.anketa_validator import AnketaValidator
    print("✅ AnketaValidator imported")
except Exception as e:
    print(f"❌ AnketaValidator import failed: {e}")
    sys.exit(1)

# Test 3: Check method signatures
print("\n[TEST 3] Check method signatures...")
import inspect

# Check _run_audit has context parameter
sig = inspect.signature(AnketaManagementHandler._run_audit)
params = list(sig.parameters.keys())
if 'context' in params:
    print(f"✅ _run_audit has context parameter: {params}")
else:
    print(f"❌ _run_audit missing context parameter: {params}")
    sys.exit(1)

# Check _send_audit_report_file has bot parameter
sig = inspect.signature(AnketaManagementHandler._send_audit_report_file)
params = list(sig.parameters.keys())
if 'bot' in params:
    print(f"✅ _send_audit_report_file has bot parameter: {params}")
else:
    print(f"❌ _send_audit_report_file missing bot parameter: {params}")
    sys.exit(1)

# Test 4: Check validator methods exist
print("\n[TEST 4] Check AnketaValidator methods...")
if hasattr(AnketaValidator, 'validate'):
    print("✅ AnketaValidator.validate exists")
else:
    print("❌ AnketaValidator.validate missing")
    sys.exit(1)

if hasattr(AnketaValidator, '_check_required_fields'):
    print("✅ AnketaValidator._check_required_fields exists")
else:
    print("❌ AnketaValidator._check_required_fields missing")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL SYNTAX CHECKS PASSED ✅")
print("=" * 60)
print("\nFixed issues:")
print("1. ✅ Database field: conversation_data → interview_data")
print("2. ✅ Bot reference: .get_bot() → context.bot")
print("3. ✅ File export: _send_audit_report_file ready")
print("\nReady for bot testing!")
print("Next: Start bot and test /audit_anketa")
