#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для отладки получения вопросов в Telegram боте
"""

import sys
import os

# Добавляем путь к модулю БД
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_interview_questions

def debug_questions():
    """Отлаживает получение вопросов как в Telegram боте"""
    
    print("=" * 80)
    print("ОТЛАДКА ПОЛУЧЕНИЯ ВОПРОСОВ В TELEGRAM БОТЕ")
    print("=" * 80)
    
    try:
        # Получаем вопросы так же, как в боте (строка 89 в main.py)
        questions = get_interview_questions()
        
        print(f"Найдено активных вопросов: {len(questions)}")
        print("-" * 80)
        
        # Анализируем каждый вопрос
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
            
            # Проверяем наличие подсказки (как в строке 335 main.py)
            if hint_text and hint_text.strip():
                hint_preview = hint_text[:80] + "..." if len(hint_text) > 80 else hint_text
                print(f"   Подсказка: {hint_preview}")
                print(f"   [DEBUG] hint_text существует и не пустой")
            else:
                print(f"   Подсказка: [НЕТ]")
                print(f"   [DEBUG] hint_text отсутствует или пустой")
                print(f"   [DEBUG] hint_text = {repr(hint_text)}")
                print(f"   [DEBUG] hint_text and hint_text.strip() = {bool(hint_text and hint_text.strip())}")
            
            # Тест отображения как в боте (строка 335)
            hint_display = f"💡 *Подсказка:* {hint_text}" if hint_text and hint_text.strip() else ""
            if hint_display:
                print(f"   [ТЕСТ ОТОБРАЖЕНИЯ]: {hint_display[:60]}{'...' if len(hint_display) > 60 else ''}")
            else:
                print(f"   [ТЕСТ ОТОБРАЖЕНИЯ]: [Подсказка не будет отображаться]")
        
        # Статистика
        questions_with_hints = sum(1 for q in questions if q.get('hint_text') and q['hint_text'].strip())
        questions_without_hints = len(questions) - questions_with_hints
        
        print("\n" + "=" * 80)
        print("СТАТИСТИКА:")
        print("-" * 80)
        print(f"Всего активных вопросов: {len(questions)}")
        print(f"Вопросов с подсказками: {questions_with_hints}")
        print(f"Вопросов БЕЗ подсказок: {questions_without_hints}")
        
        if questions_without_hints == 0:
            print("\n✅ ВСЕ АКТИВНЫЕ ВОПРОСЫ ИМЕЮТ ПОДСКАЗКИ!")
            print("Если в Telegram боте подсказки не отображаются, проблема в другом месте.")
        else:
            print(f"\n❌ НАЙДЕНО {questions_without_hints} ВОПРОСОВ БЕЗ ПОДСКАЗОК!")
            print("Нужно обновить базу данных.")
            
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_questions()