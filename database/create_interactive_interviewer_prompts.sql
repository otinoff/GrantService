-- Промпты для интерактивного интервьюера
-- Простые, без заумных терминов

-- 1. ОЦЕНКА КАЧЕСТВА ОТВЕТА (answer_quality_evaluator)
INSERT INTO agent_prompts (
    category_id,
    name,
    description,
    prompt_template,
    agent_type,
    prompt_type,
    temperature,
    max_tokens,
    is_active,
    priority
) VALUES (
    13, -- interviewer_questions
    'Оценка качества ответа',
    'Проверяет хватает ли деталей в ответе пользователя',
    'Вопрос был: "{question}"
Ответ пользователя: "{answer}"

Твоя задача: проверить достаточно ли информации в ответе.

ОЦЕНИ ПО ШКАЛЕ 1-10:
- 1-3: очень мало информации, ответ поверхностный
- 4-6: есть информация, но не хватает деталей
- 7-8: хорошо, есть детали
- 9-10: отлично, всё подробно и конкретно

ЧТО ПРОВЕРИТЬ:
- Есть ли конкретные цифры и факты?
- Описано ли понятно?
- Можно ли по этому ответу понять суть?

ВЕРНИ JSON:
{
    "score": 7,
    "enough_details": true,
    "missing": "не хватает конкретных цифр",
    "need_clarification": false
}',
    'interactive_interviewer',
    'answer_evaluation',
    0.3,
    300,
    true,
    100
);

-- 2. ГЕНЕРАЦИЯ УТОЧНЯЮЩЕГО ВОПРОСА (clarification_generator)
INSERT INTO agent_prompts (
    category_id,
    name,
    description,
    prompt_template,
    agent_type,
    prompt_type,
    temperature,
    max_tokens,
    is_active,
    priority
) VALUES (
    14, -- interviewer_followup
    'Уточняющий вопрос',
    'Генерирует простой уточняющий вопрос если ответ недостаточно детален',
    'Тема: "{topic}"
Что спросили: "{question}"
Что ответил пользователь: "{answer}"
Чего не хватает: "{missing_info}"

Сформулируй ОДИН простой уточняющий вопрос.

ПРАВИЛА:
- Вопрос должен быть коротким и понятным
- Не используй сложные термины
- Спрашивай конкретно про то чего не хватает
- Будь дружелюбным, не как на допросе

ПРИМЕРЫ ХОРОШИХ УТОЧНЕНИЙ:
- "А сколько примерно человек это затронет?"
- "Можешь назвать 2-3 конкретных партнёра?"
- "На что именно пойдут эти деньги?"

ВЕРНИ JSON:
{
    "question": "твой уточняющий вопрос",
    "why_asking": "короткое объяснение зачем спрашиваешь"
}',
    'interactive_interviewer',
    'clarification',
    0.7,
    200,
    true,
    100
);

-- 3. ПРОМЕЖУТОЧНЫЙ АУДИТ БЛОКА (interim_block_audit)
INSERT INTO agent_prompts (
    category_id,
    name,
    description,
    prompt_template,
    agent_type,
    prompt_type,
    temperature,
    max_tokens,
    is_active,
    priority
) VALUES (
    13, -- interviewer_questions
    'Проверка блока вопросов',
    'Оценивает блок из 5 ответов и решает нужны ли уточнения',
    'Проверь ответы на {block_num} блок вопросов.

ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ:
{block_answers}

ОЦЕНИ БЛОК ПО ШКАЛЕ 1-10:
- Достаточно ли информации?
- Есть ли конкретика (цифры, факты, имена)?
- Понятно ли что хочет сделать человек?

ЧТО СМОТРЕТЬ:
Блок 1 (о чём проект):
- Понятно ли название и цель?
- Описана ли проблема конкретно?
- Ясна ли целевая аудитория?

Блок 2 (как делать):
- Понятен ли план действий?
- Расписан ли бюджет?
- Есть ли конкретные результаты?

Блок 3 (кто делает):
- Описана ли команда?
- Есть ли партнёры?
- Продуман ли план после гранта?

ВЕРНИ JSON:
{
    "block_score": 7,
    "weak_points": ["бюджет без деталей", "нет конкретных партнёров"],
    "need_clarifications": [
        {"topic": "бюджет", "question": "Расскажи подробнее на что пойдут деньги?"},
        {"topic": "партнёры", "question": "Кто конкретно будет помогать?"}
    ]
}

ВАЖНО: Если всё хорошо (score >= 7) - не придумывай проблемы, верни пустой массив need_clarifications.',
    'interactive_interviewer',
    'block_audit',
    0.3,
    500,
    true,
    100
);

-- Проверяем что создалось
SELECT
    id,
    agent_type,
    prompt_type,
    name,
    temperature,
    max_tokens,
    is_active
FROM agent_prompts
WHERE agent_type = 'interactive_interviewer'
ORDER BY id;
