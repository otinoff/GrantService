#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to refactor all pages to use minimal imports
Removes all sys.path manipulations and uses simple imports
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def get_minimal_import_block() -> str:
    """Get the minimal import block for pages"""
    return '''import streamlit as st
import sys
import os

# Simple imports without path manipulation
# The environment will be set up by the launcher
'''


def get_auth_check_block() -> str:
    """Get the simplified auth check block"""
    return '''# Authorization check
try:
    from utils.auth import is_user_authorized
    if not is_user_authorized():
        st.error("⛔ Не авторизован / Not authorized")
        st.info("Пожалуйста, используйте бота для получения токена / Please use the bot to get a token")
        st.stop()
except ImportError as e:
    st.error(f"❌ Ошибка импорта / Import error: {e}")
    st.info("Запустите через launcher.py / Run via launcher.py")
    st.stop()
'''


def refactor_file(filepath: Path) -> bool:
    """Refactor a single file to use minimal imports"""
    
    print(f"Processing: {filepath.name}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ Error reading: {e}")
        return False
    
    original_content = content
    lines = content.split('\n')
    
    # Find where the actual code starts (after imports and auth check)
    code_start = 0
    in_import_section = True
    auth_check_done = False
    
    for i, line in enumerate(lines):
        # Skip shebang and encoding
        if line.startswith('#!') or line.startswith('# -*-'):
            continue
        
        # Skip docstrings
        if line.strip().startswith('"""'):
            # Find end of docstring
            for j in range(i+1, len(lines)):
                if '"""' in lines[j]:
                    code_start = j + 1
                    break
            continue
        
        # Look for actual code that's not import or auth related
        if not line.startswith('import ') and \
           not line.startswith('from ') and \
           not 'sys.path' in line and \
           not 'is_user_authorized' in line and \
           not line.strip() == '' and \
           not line.strip().startswith('#'):
            
            # Check if we're past the auth check
            if 'st.set_page_config' in line or \
               'def ' in line or \
               'class ' in line or \
               (line.strip() and not line.strip().startswith('#')):
                code_start = i
                break
    
    if code_start == 0:
        print(f"  ⚠️  Could not find code start, skipping")
        return False
    
    # Extract the header (shebang, encoding, docstring)
    header_lines = []
    for i, line in enumerate(lines):
        if line.startswith('#!') or line.startswith('# -*-'):
            header_lines.append(line)
        elif line.strip().startswith('"""'):
            # Include docstring
            header_lines.append(line)
            for j in range(i+1, len(lines)):
                header_lines.append(lines[j])
                if '"""' in lines[j]:
                    break
            break
        else:
            break
    
    # Get the rest of the code (after imports and auth)
    rest_of_code = '\n'.join(lines[code_start:])
    
    # Build the new content
    new_content = '\n'.join(header_lines)
    if new_content:
        new_content += '\n\n'
    new_content += get_minimal_import_block()
    new_content += '\n'
    new_content += get_auth_check_block()
    new_content += '\n'
    new_content += rest_of_code
    
    # Save the refactored file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ Refactored successfully")
        return True
    except Exception as e:
        print(f"  ❌ Error writing: {e}")
        return False


def main():
    """Main function"""
    
    pages_dir = Path(__file__).parent / "web-admin" / "pages"
    
    if not pages_dir.exists():
        print(f"❌ Directory not found: {pages_dir}")
        return 1
    
    print(f"📁 Refactoring pages in: {pages_dir}\n")
    
    # List of files to process
    py_files = list(pages_dir.glob("*.py"))
    
    # Skip __init__.py
    py_files = [f for f in py_files if f.name != '__init__.py']
    
    print(f"Found {len(py_files)} Python files to refactor\n")
    
    success_count = 0
    error_count = 0
    
    for filepath in py_files:
        if refactor_file(filepath):
            success_count += 1
        else:
            error_count += 1
    
    print("\n" + "="*50)
    print(f"✅ Successfully refactored: {success_count} files")
    if error_count > 0:
        print(f"❌ Errors: {error_count} files")
    else:
        print("🎉 All files refactored successfully!")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())