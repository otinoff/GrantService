#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized Path Setup for GrantService Web Admin
==================================================
This module MUST be imported FIRST in all web-admin files before any other
project imports to ensure correct sys.path configuration.

Author: Streamlit Admin Developer Agent
Created: 2025-10-03
Version: 1.0.0

Usage:
    # In any web-admin file, import this FIRST (after standard library imports):
    import sys
    import os

    # IMPORT THIS FIRST!
    import setup_paths

    # Now you can safely import project modules:
    from utils.database import AdminDatabase
    from data.database import GrantServiceDatabase

Why this is needed:
    - Streamlit multipage apps run each page as separate process
    - Python import system requires paths to be set BEFORE first import
    - This centralizes path configuration in one place
    - Fixes "ModuleNotFoundError: No module named 'utils.database'" errors
"""

import sys
import os
from pathlib import Path


def setup_project_paths():
    """
    Configure sys.path with all required project directories.
    This function is idempotent - safe to call multiple times.

    Directories added:
        - web-admin/ (current directory)
        - GrantService/ (project root)
        - GrantService/data/ (database modules)
        - GrantService/telegram-bot/ (bot utilities)
        - GrantService/agents/ (AI agents)
        - GrantService/shared/ (shared libraries)
    """
    # Get current file location
    current_file = Path(__file__).resolve()
    web_admin_dir = current_file.parent  # web-admin/
    base_dir = web_admin_dir.parent      # GrantService/

    # Define all required paths
    required_paths = [
        web_admin_dir,                    # web-admin/
        base_dir,                         # GrantService/
        base_dir / 'data',                # GrantService/data/
        base_dir / 'telegram-bot',        # GrantService/telegram-bot/
        base_dir / 'agents',              # GrantService/agents/
        base_dir / 'shared',              # GrantService/shared/
    ]

    # Add paths to sys.path (only if not already present)
    paths_added = []
    for path in required_paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            paths_added.append(path_str)

    # Return info about what was added (useful for debugging)
    return {
        'status': 'success',
        'paths_added': paths_added,
        'total_paths_in_sys': len(sys.path),
        'web_admin_dir': str(web_admin_dir),
        'base_dir': str(base_dir)
    }


def verify_imports():
    """
    Verify that critical modules can be imported after path setup.
    Returns dict with import status for each module.
    """
    results = {}

    # Test utils.database
    try:
        from utils.database import AdminDatabase
        results['utils.database'] = 'OK'
    except ImportError as e:
        results['utils.database'] = f'FAILED: {e}'

    # Test data.database
    try:
        from data.database import GrantServiceDatabase
        results['data.database'] = 'OK'
    except ImportError as e:
        results['data.database'] = f'FAILED: {e}'

    # Test utils.ui_helpers
    try:
        from utils.ui_helpers import render_page_header
        results['utils.ui_helpers'] = 'OK'
    except ImportError as e:
        results['utils.ui_helpers'] = f'FAILED: {e}'

    return results


# Auto-setup on import
_setup_info = setup_project_paths()

# Debug mode: print setup info if GRANTSERVICE_DEBUG env var is set
if os.getenv('GRANTSERVICE_DEBUG') == '1':
    print("=" * 60)
    print("setup_paths.py - Path Configuration")
    print("=" * 60)
    print(f"Status: {_setup_info['status']}")
    print(f"Web Admin Dir: {_setup_info['web_admin_dir']}")
    print(f"Base Dir: {_setup_info['base_dir']}")
    print(f"Paths added: {len(_setup_info['paths_added'])}")
    for path in _setup_info['paths_added']:
        print(f"  + {path}")
    print("=" * 60)


# Export for external use if needed
__all__ = ['setup_project_paths', 'verify_imports']
