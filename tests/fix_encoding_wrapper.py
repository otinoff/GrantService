#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix encoding wrapper in agent files - make it safe for multiple imports
"""
import sys
import os
import io
from pathlib import Path

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def fix_encoding_wrapper(file_path: Path) -> bool:
    """
    Заменяет небезопасный encoding wrapper на безопасный
    """
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Старый небезопасный вариант
    old_wrapper = """# Fix UTF-8 encoding for Windows console
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')"""

    # Новый безопасный вариант
    new_wrapper = """# Fix UTF-8 encoding for Windows console (only if not already done)
import io
if sys.platform == 'win32' and not hasattr(sys.stdout, '_wrapped_for_utf8'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        sys.stdout._wrapped_for_utf8 = True
    except (ValueError, AttributeError):
        pass  # Already wrapped or no buffer"""

    if old_wrapper in content:
        content = content.replace(old_wrapper, new_wrapper)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {file_path.name} - encoding wrapper исправлен")
        return True
    else:
        print(f"ℹ️  {file_path.name} - не требует исправления")
        return True


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    agents_dir = project_root / 'agents'

    agent_files = [
        agents_dir / 'base_agent.py',
        agents_dir / 'auditor_agent.py',
        agents_dir / 'interactive_interviewer_agent.py',
        agents_dir / 'presidential_grants_researcher.py',
        agents_dir / 'writer_agent_v2.py',
        agents_dir / 'reviewer_agent.py',
    ]

    print("=" * 70)
    print("🔧 Исправление encoding wrapper в файлах агентов")
    print("=" * 70)

    for agent_file in agent_files:
        fix_encoding_wrapper(agent_file)

    print("=" * 70)
    print("✅ Готово!")
    print("=" * 70)
