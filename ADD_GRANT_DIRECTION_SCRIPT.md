# Скрипт для добавления вопроса с выбором грантового направления

## Файл: `scripts/add_grant_direction_question.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления вопроса с выбором грантового направления
"""

import sys
import os
import json

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import db

def add_grant_direction_question():
    """Добавить вопрос с выбором грантового направления"""
    
    # Варианты ответов
    options = [
        {
            "value": "science_education",
            "text": "Поддержка проектов в области науки, образования, просвещения",
            "description": "включает стандартный и долгосрочный срок реализации"
        },
        {
            "value": "civil_society",
            "text": "Развитие институтов гражданского общества",
            "description": "включает стандартный и долгосрочный срок реализации"
        },
        {
            "value": "public_diplomacy",
            "text": "Развитие общественной дипломатии и поддержка соотечественников",
            "description": ""
        },
        {
            "value": "social_initiatives",
            "text": "Поддержка социально значимых инициатив и проектов",
            "description": ""
        },
        {
            "value": "culture_art",
            "text": "Развитие культуры и искусства",
            "description": ""
        },
        {
            "value": "charity_support",
            "text": "Поддержка проектов в сфере благотворительности и поддержки уязвимых групп",
            "description": ""
        },
        {
            "value": "environment",
            "text": "Поддержка проектов в области охраны окружающей среды и устойчивого развития",
            "description": ""
        },
        {
            "value": "youth_initiatives",
            "text": "Развитие молодежных инициатив и проектов",
            "description": ""
        },
        {
            "value": "sport_physical",
            "text": "Поддержка и развитие спорта и массового физкультурного движения",
            "description": ""
        },
        {
            "value": "innovation_tech",
            "text": "Поддержка инновационных и технологических проектов в общественной сфере",
            "description": ""
        },
        {
            "value": "regional_initiatives",
            "text": "Развитие региональных инициатив и проектов",
            "description": ""
        }
    ]
    
    # Конвертируем в JSON
    options_json = json.dumps(options, ensure_ascii=False)
    
    # Данные вопроса
    question_data = {
        'question_number': 25,  # Добавляем как 25-й вопрос
        'question_text': 'Выберите грантовое направление для вашего проекта',
        'field_name': 'grant_direction',
        'question_type': 'select',
        'options': options_json,
        'hint_text': '''При заполнении заявки нужно выбрать только одно грантовое направление, которому более всего соответствует тема проекта и основная часть мероприятий. 

Также в заявке нужно выбрать тематическое направление внутри выбранного грантового направления, что влияет на экспертизу проекта.

Источник: методические рекомендации Фонда президентских грантов 2025 года.''',
        'is_required': 1,
        'is_active': 1
    }
    
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже вопрос с таким номером или field_name
            cursor.execute("""
                SELECT id, question_number, question_text 
                FROM interview_questions 
                WHERE question_number = ? OR field_name = ?
            """, (question_data['question_number'], question_data['field_name']))
            
            existing = cursor.fetchone()
            if existing:
                print(f"⚠️  Вопрос уже существует: ID={existing[0]}, №{existing[1]}: {existing[2][:50]}...")
                
                # Спрашиваем, обновить ли существующий вопрос
                response = input("Хотите обновить существующий вопрос? (y/n): ")
                if response.lower() == 'y':
                    cursor.execute("""
                        UPDATE interview_questions 
                        SET question_text = ?,
                            question_type = ?,
                            options = ?,
                            hint_text = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        question_data['question_text'],
                        question_data['question_type'],
                        question_data['options'],
                        question_data['hint_text'],
                        existing[0]
                    ))
                    conn.commit()
                    print(f"✅ Вопрос №{existing[1]} обновлен!")
                else:
                    print("Операция отменена")
                    return
            else:
                # Сдвигаем номера существующих вопросов если нужно
                cursor.execute("""
                    UPDATE interview_questions 
                    SET question_number = question_number + 1
                    WHERE question_number >= ? AND is_active = 1
                """, (question_data['question_number'],))
                
                # Добавляем новый вопрос
                cursor.execute("""
                    INSERT INTO interview_questions (
                        question_number,
                        question_text,
                        field_name,
                        question_type,
                        options,
                        hint_text,
                        is_required,
                        is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    question_data['question_number'],
                    question_data['question_text'],
                    question_data['field_name'],
                    question_data['question_type'],
                    question_data['options'],
                    question_data['hint_text'],
                    question_data['is_required'],
                    question_data['is_active']
                ))
                
                conn.commit()
                print(f"✅ Вопрос №{question_data['question_number']} успешно добавлен!")
                print(f"   Тип: {question_data['question_type']}")
                print(f"   Вариантов ответа: {len(options)}")
                print(f"   Field name: {question_data['field_name']}")
            
            # Показываем общую статистику
            cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
            total_active = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE question_type = 'select' AND is_active = 1")
            total_select = cursor.fetchone()[0]
            
            print(f"\n📊 Статистика:")
            print(f"   Всего активных вопросов: {total_active}")
            print(f"   Вопросов с выбором: {total_select}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("Добавление вопроса с выбором грантового направления")
    print("=" * 60)
    add_grant_direction_question()
```

## Как использовать

1. **Создайте файл скрипта:**
   ```bash
   # Windows
   notepad GrantService\scripts\add_grant_direction_question.py
   
   # Linux
   nano /var/GrantService/scripts/add_grant_direction_question.py
   ```

2. **Скопируйте код из этого документа в файл**

3. **Запустите скрипт:**
   ```bash
   # Windows
   cd C:\SnowWhiteAI\GrantService
   python scripts\add_grant_direction_question.py
   
   # Linux
   cd /var/GrantService
   python3 scripts/add_grant_direction_question.py
   ```

4. **Проверьте результат:**
   - Скрипт покажет, добавлен ли вопрос
   - Выведет статистику по вопросам

## Альтернативный вариант - прямой SQL

Если предпочитаете работать напрямую с БД:

```sql
-- Проверка существующих вопросов
SELECT question_number, field_name, question_text, question_type 
FROM interview_questions 
WHERE question_number = 25 OR field_name = 'grant_direction';

-- Добавление нового вопроса
INSERT INTO interview_questions (
    question_number,
    question_text,
    field_name,
    question_type,
    options,
    hint_text,
    is_required,
    is_active,
    created_at,
    updated_at
) VALUES (
    25,
    'Выберите грантовое направление для вашего проекта',
    'grant_direction',
    'select',
    '[{"value":"science_education","text":"Поддержка проектов в области науки, образования, просвещения","description":"включает стандартный и долгосрочный срок реализации"},{"value":"civil_society","text":"Развитие институтов гражданского общества","description":"включает стандартный и долгосрочный срок реализации"},{"value":"public_diplomacy","text":"Развитие общественной дипломатии и поддержка соотечественников","description":""},{"value":"social_initiatives","text":"Поддержка социально значимых инициатив и проектов","description":""},{"value":"culture_art","text":"Развитие культуры и искусства","description":""},{"value":"charity_support","text":"Поддержка проектов в сфере благотворительности и поддержки уязвимых групп","description":""},{"value":"environment","text":"Поддержка проектов в области охраны окружающей среды и устойчивого развития","description":""},{"value":"youth_initiatives","text":"Развитие молодежных инициатив и проектов","description":""},{"value":"sport_physical","text":"Поддержка и развитие спорта и массового физкультурного движения","description":""},{"value":"innovation_tech","text":"Поддержка инновационных и технологических проектов в общественной сфере","description":""},{"value":"regional_initiatives","text":"Развитие региональных инициатив и проектов","description":""}]',
    'При заполнении заявки нужно выбрать только одно грантовое направление, которому более всего соответствует тема проекта и основная часть мероприятий. Также в заявке нужно выбрать тематическое направление внутри выбранного грантового направления. Источник: методические рекомендации Фонда президентских грантов 2025 года.',
    1,
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Проверка результата
SELECT COUNT(*) as total_questions FROM interview_questions WHERE is_active = 1;
SELECT COUNT(*) as select_questions FROM interview_questions WHERE question_type = 'select' AND is_active = 1;
```

## Результат

После выполнения скрипта:
1. В БД появится новый вопрос №25 с типом 'select'
2. Вопрос будет содержать 11 вариантов грантовых направлений
3. Бот сможет отображать этот вопрос с кнопками выбора (после обновления кода бота)