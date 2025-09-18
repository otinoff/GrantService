#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования функции получения вопросов из базы данных
"""

import sys
import os

# Добавляем путь к модулю БД
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_interview_questions

def test_get_questions():
    """Тестирует функцию получения вопросов"""
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ФУНКЦИИ get_interview_questions()")
    print("=" * 60)
    
    try:
        # Получаем вопросы
        questions = get_interview_questions()
        
        print(f"Найдено активных вопросов: {len(questions)}")
        print("-" * 60)
        
        # Проверяем каждый вопрос
        for i, question in enumerate(questions, 1):
            q_num = question.get('question_number', 'N/A')
            q_text = question.get('question_text', 'N/A')
            hint_text = question.get('hint_text', '')
            field_name = question.get('field_name', 'N/A')
            question_type = question.get('question_type', 'N/A')
            
            print(f"\n{i}. Вопрос {q_num}:")
            print(f"   Текст: {q_text[:60]}{'...' if len(q_text) > 60 else ''}")
            print(f"   Поле: {field_name}")
            print(f"   Тип: {question_type}")
            
            if hint_text and hint_text.strip():
                hint_preview = hint_text[:80] + "..." if len(hint_text) > 80 else hint_text
                print(f"   Подсказка: {hint_preview}")
                print(f"   [OK] Подсказка присутствует")
            else:
                print(f"   Подсказка: [НЕТ]")
                print(f"   [ERROR] Подсказка отсутствует!")
        
        # Статистика
        questions_with_hints = sum(1 for q in questions if q.get('hint_text') and q['hint_text'].strip())
        questions_without_hints = len(questions) - questions_with_hints
        
        print("\n" + "=" * 60)
        print("СТАТИСТИКА:")
        print("-" * 60)
        print(f"Всего активных вопросов: {len(questions)}")
        print(f"Вопросов с подсказками: {questions_with_hints}")
        print(f"Вопросов БЕЗ подсказок: {questions_without_hints}")
        
        if questions_without_hints == 0:
            print("\n✅ ВСЕ АКТИВНЫЕ ВОПРОСЫ ИМЕЮТ ПОДСКАЗКИ!")
        else:
            print(f"\n❌ НАЙДЕНО {questions_without_hints} ВОПРОСОВ БЕЗ ПОДСКАЗОК!")
            
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_questions()