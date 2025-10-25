-- Fix block_audit prompt in LOCAL DB with proper JSON escaping
-- Use 4 curly braces {{{{ }}}} for JSON examples

UPDATE agent_prompts
SET prompt_template = 'Проверь ответы на {block_num} блок вопросов.

ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ:
{block_answers}

ОЦЕНИ БЛОК ПО ШКАЛЕ 1-10:
- Достаточно ли информации?
- Есть ли конкретика (цифры, факты, имена)?
- Понятно ли что хочет сделать человек?

ВАЖНО:
1. Верни ТОЛЬКО JSON, без дополнительного текста до и после
2. Не пиши объяснений, только JSON

ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
{{{{
    "block_score": 7,
    "weak_points": ["пример"],
    "need_clarifications": [
        {{{{ "topic": "тема", "question": "вопрос?" }}}}
    ]
}}}}'
WHERE name = 'block_audit'
  AND category_id IN (SELECT id FROM prompt_categories WHERE name='interactive_block_audit');
