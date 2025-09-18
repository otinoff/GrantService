#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования отображения вопросов как в Telegram боте
"""

import sys
import os

# Добавляем путь к модулю БД
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_interview_questions

def test_question_display():
    """Тестирует отображение вопросов как в Telegram боте"""
    
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ ОТОБРАЖЕНИЯ ВОПРОСОВ (как в Telegram боте)")
    print("=" * 80)
    
    try:
        # Получаем вопросы
        questions = get_interview_questions()
        
        print(f"Найдено активных вопросов: {len(questions)}")
        print("\n" + "=" * 80)
        print("ТЕСТОВОЕ ОТОБРАЖЕНИЕ ВОПРОСОВ:")
        print("=" * 80)
        
        # Тестируем отображение для каждого вопроса (как в боте)
        for i, question in enumerate(questions, 1):
            question_number = question.get('question_number', i)
            question_text = question.get('question_text', '')
            hint_text = question.get('hint_text', '')
            question_type = question.get('question_type', '')
            
            print(f"\n*Вопрос {question_number} из {len(questions)}*")
            print(f"")
            print(f"{question_text}")
            print(f"")
            
            # Это то, что отображается в боте (строка 335 из main.py)
            if hint_text and hint_text.strip():
                hint_display = f"💡 *Подсказка:* {hint_text}"
                print(f"{hint_display}")
                print(f"")
                print(f"[OK] Подсказка будет отображаться в Telegram боте")
            else:
                print(f"[INFO] Подсказка отсутствует")
            
            if question_type:
                type_display = f"📝 *Тип ответа:* {question_type}"
                print(f"{type_display}")
            
            print("-" * 40)
        
        # Проверим конкретно вопрос 1
        print("\n" + "=" * 80)
        print("ПОДРОБНАЯ ПРОВЕРКА ВОПРОСА 1:")
        print("=" * 80)
        
        if questions:
            q1 = questions[0]
            print(f"question_number: {repr(q1.get('question_number'))}")
            print(f"question_text: {repr(q1.get('question_text'))}")
            print(f"hint_text: {repr(q1.get('hint_text'))}")
            print(f"hint_text is None: {q1.get('hint_text') is None}")
            print(f"hint_text == '': {q1.get('hint_text') == ''}")
            print(f"hint_text and hint_text.strip(): {bool(q1.get('hint_text') and q1.get('hint_text').strip())}")
            
            # Тест отображения
            hint_text = q1.get('hint_text', '')
            if hint_text and hint_text.strip():
                display_text = f"💡 *Подсказка:* {hint_text}"
                print(f"\n[ТЕСТ ОТОБРАЖЕНИЯ]: {display_text}")
            else:
                print(f"\n[ТЕСТ ОТОБРАЖЕНИЯ]: [Подсказка не будет отображаться]")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_question_display()