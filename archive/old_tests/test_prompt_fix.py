#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест исправленного промпта block_audit
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "web-admin"))

from utils.prompt_manager import DatabasePromptManager
from data.database.models import GrantServiceDatabase

def test_prompt():
    """Тест промпта с правильным экранированием"""
    print("="*80)
    print("ТЕСТ: Исправленный промпт block_audit")
    print("="*80)

    db = GrantServiceDatabase()
    pm = DatabasePromptManager(db)

    try:
        # Загружаем промпт
        prompt = pm.get_prompt(
            'interactive_interviewer',
            'block_audit',
            variables={
                'block_num': '1',
                'block_answers': 'Q1: Название проекта?\nA1: Инклюзивная кофейня\n\nQ2: Цель?\nA2: Создать рабочие места для людей с инвалидностью'
            }
        )

        if not prompt:
            print("❌ Промпт не загружен")
            return False

        print("\n✅ Промпт загружен успешно!")
        print(f"\nДлина: {len(prompt)} символов")

        # Проверяем что JSON пример остался в нужном виде
        if '{{' in prompt and '}}' in prompt:
            print("✅ JSON пример правильно экранирован (содержит {{...}})")
        else:
            print("⚠️ JSON пример может быть неправильно экранирован")

        # Проверяем что переменные подставлены
        if '{block_num}' not in prompt and 'блок 1' in prompt.lower():
            print("✅ Переменная block_num подставлена корректно")
        else:
            print("❌ Переменная block_num не подставлена")

        if '{block_answers}' not in prompt and 'Инклюзивная кофейня' in prompt:
            print("✅ Переменная block_answers подставлена корректно")
        else:
            print("❌ Переменная block_answers не подставлена")

        print("\n" + "="*80)
        print("ПРЕВЬЮ ПРОМПТА:")
        print("="*80)
        print(prompt[:500])
        print("...\n")

        return True

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_prompt()
    sys.exit(0 if success else 1)
