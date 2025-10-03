#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to update pages to use centralized database connection
"""

import os
import re
from pathlib import Path

# Files to update
files_to_update = [
    "pages/🤖_AI_Agents.py",
    "pages/🎯_Pipeline_Dashboard.py",
    "pages/📋_Управление_грантами.py"
]

def update_file(filepath):
    """Update a single file to use centralized db connection"""
    print(f"Updating {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already updated
    if 'from utils.database import get_db_connection' in content:
        print(f"  ✓ Already updated, skipping")
        return False

    # Pattern to find and remove the local get_db_connection function
    pattern = r'@st\.cache_resource\ndef get_db_connection\(\):[^\n]*\n[^\n]*\n[^\n]*\n[^\n]*\n'

    if re.search(pattern, content):
        # Remove the local function
        content = re.sub(pattern, '', content)
        print(f"  ✓ Removed local get_db_connection()")

        # Add import if not present
        if 'from utils.database import' not in content:
            # Find where to insert import (after other utils imports)
            insert_pattern = r'(from utils\.auth import[^\n]*\n)'
            if re.search(insert_pattern, content):
                content = re.sub(
                    insert_pattern,
                    r'\1from utils.database import get_db_connection\n',
                    content
                )
                print(f"  ✓ Added import from utils.database")
            else:
                # Insert after first import block
                insert_pattern = r'(import streamlit as st\n)'
                content = re.sub(
                    insert_pattern,
                    r'\1from utils.database import get_db_connection\n',
                    content
                )
                print(f"  ✓ Added import (fallback position)")

        # Save updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ File updated successfully")
        return True
    else:
        print(f"  ⚠ Pattern not found, skipping")
        return False

def main():
    """Main update function"""
    print("=" * 60)
    print("UPDATING PAGES TO USE CENTRALIZED DATABASE CONNECTION")
    print("=" * 60)

    base_dir = Path(__file__).parent
    updated_count = 0

    for file in files_to_update:
        filepath = base_dir / file
        if filepath.exists():
            if update_file(filepath):
                updated_count += 1
        else:
            print(f"⚠ File not found: {filepath}")

    print("=" * 60)
    print(f"COMPLETE: Updated {updated_count} files")
    print("=" * 60)

if __name__ == "__main__":
    main()
