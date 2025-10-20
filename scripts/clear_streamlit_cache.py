#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clear Streamlit cache and restart
"""

import shutil
from pathlib import Path

# Streamlit cache locations
cache_paths = [
    Path.home() / ".streamlit" / "cache",
    Path(__file__).parent / "web-admin" / ".streamlit" / "cache",
    Path(__file__).parent / ".streamlit" / "cache",
]

print("="*70)
print("CLEARING STREAMLIT CACHE")
print("="*70)

for cache_path in cache_paths:
    if cache_path.exists():
        print(f"\nRemoving: {cache_path}")
        try:
            shutil.rmtree(cache_path)
            print("  [OK] Removed")
        except Exception as e:
            print(f"  [ERROR] {e}")
    else:
        print(f"\nSkipping (not found): {cache_path}")

print("\n" + "="*70)
print("[SUCCESS] Cache cleared!")
print("="*70)
print("\nNext steps:")
print("1. Restart Streamlit:")
print("   - Stop current process (Ctrl+C)")
print("   - Run: python launcher.py")
print("")
print("2. Open browser: http://localhost:8501")
print("")
print("3. Go to 'Grants' page")
print("")
print("4. You should now see 22 grants (from PostgreSQL)")
print("="*70)
