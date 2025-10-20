#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix imports in agent files for cross-platform compatibility
Заменяет Linux-специфичные пути на кроссплатформенные
"""
import sys
import os
import io
from pathlib import Path

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def fix_agent_imports(agent_file_path: Path) -> bool:
    """
    Исправляет импорты в файле агента

    Заменяет:
    sys.path.append('/var/GrantService/shared')

    На:
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "shared"))
    sys.path.insert(0, str(project_root / "telegram-bot" / "services"))
    sys.path.insert(0, str(project_root / "web-admin"))
    sys.path.insert(0, str(project_root / "data" / "database"))
    """

    if not agent_file_path.exists():
        print(f"❌ Файл не найден: {agent_file_path}")
        return False

    # Читаем содержимое
    with open(agent_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем, нужно ли исправление
    if '/var/GrantService/' not in content:
        print(f"✅ {agent_file_path.name} - пути уже кроссплатформенные")
        return True

    # Заменяем Linux-пути на кроссплатформенные
    old_imports = [
        "sys.path.append('/var/GrantService/shared')",
        "sys.path.append('/var/GrantService/telegram-bot/services')",
        "sys.path.append('/var/GrantService/web-admin')",
        "sys.path.append('/var/GrantService/agents')",
        "sys.path.append('/var/GrantService/data')",
        "sys.path.append('/var/GrantService/telegram-bot/utils')",
    ]

    new_imports = """# Cross-platform path setup
from pathlib import Path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "telegram-bot" / "services"))
sys.path.insert(0, str(_project_root / "web-admin"))
sys.path.insert(0, str(_project_root / "web-admin" / "utils"))
sys.path.insert(0, str(_project_root / "data" / "database"))
sys.path.insert(0, str(_project_root / "agents"))
"""

    # Удаляем старые импорты
    for old_import in old_imports:
        content = content.replace(old_import + '\n', '')
        content = content.replace(old_import, '')

    # Добавляем новые импорты после импорта sys и os
    if 'import sys' in content and '_project_root' not in content:
        # Находим позицию после import os
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import os') or line.startswith('from typing'):
                insert_pos = i + 1
                break

        # Вставляем новые импорты
        lines.insert(insert_pos, '\n' + new_imports)
        content = '\n'.join(lines)

    # Также добавим фикс для кодировки Windows в начало файла
    if 'sys.platform == \'win32\'' not in content and '# -*- coding: utf-8 -*-' in content:
        encoding_fix = """
# Fix UTF-8 encoding for Windows console
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
        # Вставляем после импортов
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from typing'):
                lines.insert(i + 1, encoding_fix)
                break
        content = '\n'.join(lines)

    # Сохраняем исправленный файл
    with open(agent_file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {agent_file_path.name} - импорты исправлены")
    return True


if __name__ == '__main__':
    # Список файлов для исправления
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
    print("🔧 Исправление импортов в файлах агентов")
    print("=" * 70)

    success_count = 0
    for agent_file in agent_files:
        if fix_agent_imports(agent_file):
            success_count += 1

    print("=" * 70)
    print(f"✅ Исправлено файлов: {success_count}/{len(agent_files)}")
    print("=" * 70)
