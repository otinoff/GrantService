#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест экспорта грантовой заявки session 9 в MD, PDF, DOCX
Использует универсальный модуль shared/grant_exporter.py
"""
import sys
import os

# Добавляем пути
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from shared.grant_exporter import export_grant_from_json_file

print("=" * 70)
print("ТЕСТ ЭКСПОРТА ГРАНТОВОЙ ЗАЯВКИ SESSION 9")
print("=" * 70)
print()

# Пути к файлам
json_path = "grant_export_session_9/03_grant_draft/grant_result.json"
output_dir = "grant_export_session_9/03_grant_draft/"

print(f"[*] JSON файл: {json_path}")
print(f"[*] Выходная директория: {output_dir}")
print()

try:
    # Экспорт во все форматы
    print("[*] Запускаем экспорт во все форматы...")
    print()

    files = export_grant_from_json_file(
        json_path=json_path,
        output_dir=output_dir,
        base_filename="grant_session_9"
    )

    # Результаты
    print("=" * 70)
    print("РЕЗУЛЬТАТЫ ЭКСПОРТА")
    print("=" * 70)
    print()

    for format_name, file_path in files.items():
        if file_path:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            print(f"[OK] {format_name.upper():10s}: {file_path}")
            print(f"     Размер: {file_size:,} байт")
        else:
            print(f"[FAIL] {format_name.upper():10s}: ОШИБКА")
        print()

    success_count = sum(1 for v in files.values() if v is not None)
    print(f"[*] Успешно экспортировано: {success_count}/3 форматов")
    print()

    if success_count == 3:
        print("[SUCCESS] ВСЕ ФОРМАТЫ ЭКСПОРТИРОВАНЫ УСПЕШНО!")
    elif success_count > 0:
        print("[WARNING] Частичный успех - проверьте логи")
    else:
        print("[FAIL] ЭКСПОРТ НЕ УДАЛСЯ")

    print("=" * 70)

except Exception as e:
    print(f"[ERROR] КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
