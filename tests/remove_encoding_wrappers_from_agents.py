#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove encoding wrappers from agent files
Encoding wrapper should be set only once at the entry point (tests, main scripts)
"""
import sys
import os
import io
from pathlib import Path

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def remove_encoding_wrapper(file_path: Path) -> bool:
    """
    Удаляет encoding wrapper из файла агента
    """
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Ищем и удаляем блок encoding wrapper
    new_lines = []
    skip_next = 0
    removed = False

    for i, line in enumerate(lines):
        if skip_next > 0:
            skip_next -= 1
            continue

        # Проверяем начало блока encoding wrapper
        if ('# Fix UTF-8 encoding for Windows console' in line or
            '# Fix Windows console encoding' in line):
            # Пропускаем весь блок (обычно 5-8 строк)
            j = i + 1
            while j < len(lines) and j < i + 10:
                next_line = lines[j]
                if (next_line.strip().startswith('import ') or
                    next_line.strip().startswith('from ') or
                    next_line.strip() == '' or
                    'sys.stdout' in next_line or
                    'sys.stderr' in next_line or
                    'io.TextIOWrapper' in next_line or
                    'pass  # Already wrapped' in next_line or
                    'except' in next_line or
                    'try:' in next_line or
                    '_wrapped_for_utf8' in next_line):
                    j += 1
                else:
                    break

            skip_next = j - i - 1
            removed = True
            print(f"  Удален блок encoding wrapper (строки {i+1}-{j})")
            continue

        new_lines.append(line)

    if removed:
        # Сохраняем файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✅ {file_path.name} - encoding wrapper удален")
        return True
    else:
        print(f"ℹ️  {file_path.name} - не содержит encoding wrapper")
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
    print("🔧 Удаление encoding wrappers из файлов агентов")
    print("   (Encoding wrapper должен быть только в entry points)")
    print("=" * 70)

    for agent_file in agent_files:
        remove_encoding_wrapper(agent_file)

    print("=" * 70)
    print("✅ Готово!")
    print("=" * 70)
