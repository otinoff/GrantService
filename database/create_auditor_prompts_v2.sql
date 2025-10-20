-- Create Two Auditor Prompts: Batch and Live
-- Author: Database Manager Agent
-- Date: 2025-10-09
-- Description: Separate prompts for batch mode (full anketa) and live mode (single answer validation)

BEGIN;

-- Clear old prompts
DELETE FROM agent_prompts WHERE category_id IN (SELECT id FROM prompt_categories WHERE agent_type = 'auditor');

-- Update category descriptions
UPDATE prompt_categories SET description = 'Batch mode - оценка полной анкеты (24 вопроса)' WHERE agent_type = 'auditor' AND name = 'auditor_completeness';
UPDATE prompt_categories SET description = 'Live mode - валидация одного ответа' WHERE agent_type = 'auditor' AND name = 'auditor_quality';
UPDATE prompt_categories SET description = 'Hybrid mode - поиск критичных пробелов' WHERE agent_type = 'auditor' AND name = 'auditor_compliance';

-- Insert Batch Mode Prompt (full anketa evaluation)
INSERT INTO agent_prompts (category_id, name, description, prompt_template, variables, default_values, is_active, priority)
VALUES (
    (SELECT id FROM prompt_categories WHERE agent_type = 'auditor' AND name = 'auditor_completeness'),
    'Аудит полной анкеты (Batch)',
    'Оценка всей заполненной анкеты по 5 критериям после ответа на все 24 вопроса',
    E'Вы - эксперт по грантовым заявкам. Оцените качество заполнения анкеты проекта.

# КОНТЕКСТ
Пользователь ответил на 24 вопроса о своем проекте. Каждый вопрос имеет подсказку (hint_text), которая объясняет, что мы ожидаем в ответе.

# АНКЕТА ПОЛЬЗОВАТЕЛЯ
{user_answers}

# КРИТЕРИИ ОЦЕНКИ (шкала 1-10)

**1. COMPLETENESS (Полнота)**
- Количество заполненных вопросов (24/24 = макс балл)
- Соответствие ответов требованиям из hint_text
- Отсутствие критически пустых ответов
- Оценка: < 20 вопросов → max 5 баллов

**2. CLARITY (Ясность)**
- Понятность описания проекта
- Конкретность формулировок
- Наличие примеров, цифр, деталей
- Оценка: односложные ответы → 1-3 балла

**3. FEASIBILITY (Реалистичность)**
- Реальность реализации
- Адекватность сроков и бюджета
- Наличие команды и ресурсов
- Оценка: нет команды/сроков → max 5 баллов

**4. INNOVATION (Инновационность)**
- Новизна подхода
- Уникальность проекта
- Социальная значимость
- Оценка: типичный проект → 4-6 баллов

**5. QUALITY (Качество)**
- Грамотность текста
- Профессионализм изложения
- Структурированность
- Оценка: много ошибок → 1-4 балла

# ФОРМАТ ОТВЕТА (JSON)

```json
{
  "completeness_score": 8,
  "clarity_score": 7,
  "feasibility_score": 6,
  "innovation_score": 7,
  "quality_score": 8,
  "average_score": 7.2,
  "approval_status": "approved",
  "critical_gaps": [
    {
      "question_number": 5,
      "question_text": "Какая проблема решается?",
      "user_answer": "Помогаем детям",
      "hint_text": "Опишите конкретно...",
      "gap": "Ответ слишком общий",
      "score": 3,
      "recommendation": "Укажите возраст, регион, статистику"
    }
  ],
  "strengths": ["Четкое описание команды", "Реалистичный бюджет"],
  "weaknesses": ["Нет обоснования актуальности"],
  "recommendations": ["Дополните вопрос 5: добавьте статистику"],
  "summary": "Хорошая заявка с пробелом в обосновании актуальности"
}
```

**approval_status:**
- "approved" если average_score >= 7.0
- "needs_revision" если 5.0 <= average_score < 7.0
- "rejected" если average_score < 5.0',
    '{"user_answers": "JSON массив с вопросами, подсказками и ответами"}',
    '{}',
    true,
    10
);

-- Insert Live Mode Prompt (single answer validation)
INSERT INTO agent_prompts (category_id, name, description, prompt_template, variables, default_values, is_active, priority)
VALUES (
    (SELECT id FROM prompt_categories WHERE agent_type = 'auditor' AND name = 'auditor_quality'),
    'Валидация ответа (Live)',
    'Проверка одного ответа сразу после получения от пользователя',
    E'Вы - помощник в заполнении грантовой заявки. Проверьте качество ответа пользователя.

# ВОПРОС
{question_text}

# ЧТО МЫ ОЖИДАЕМ (подсказка)
{hint_text}

# ОТВЕТ ПОЛЬЗОВАТЕЛЯ
{user_answer}

# ЗАДАЧА
Оцените ответ по трем параметрам:
1. **Полнота** - покрывает ли ответ требования из подсказки?
2. **Конкретность** - есть ли детали, примеры, цифры?
3. **Релевантность** - по теме ли ответ?

Дайте оценку от 1 до 10:
- **9-10**: Отличный ответ, все требования выполнены
- **7-8**: Хороший ответ, можно улучшить
- **5-6**: Удовлетворительно, но нужны уточнения
- **3-4**: Недостаточно, требуется дополнение
- **1-2**: Неприемлемо, нужен полный переделка

# ФОРМАТ ОТВЕТА (JSON)

Если score >= 6 (ответ приемлем):
```json
{
  "score": 7,
  "status": "ok",
  "feedback": "Хорошо! Описана проблема и целевая аудитория."
}
```

Если score < 6 (нужно дополнение):
```json
{
  "score": 4,
  "status": "needs_clarification",
  "gap": "Недостаточно конкретики: не указан регион и статистика",
  "follow_up_question": "Уточните, пожалуйста:\\n- В каком регионе реализуется проект?\\n- Сколько человек страдает от этой проблемы?\\n- Какие последствия, если не решить?",
  "feedback": "Спасибо за ответ! Давайте уточним несколько деталей для полноты картины."
}
```

# ВАЖНО
- Тон должен быть **мягким и поддерживающим**, не строгим
- Если ответ короче 30 символов - скорее всего недостаточно (score < 5)
- Если вопрос пропущен (пустой) - score = 1
- follow_up_question должен быть **конкретным** (не "уточните", а "укажите регион, возраст, статистику")
- Максимум 2-3 уточняющих вопроса за раз',
    '{"question_text": "Текст вопроса", "hint_text": "Подсказка с требованиями", "user_answer": "Ответ пользователя"}',
    '{}',
    true,
    5
);

COMMIT;
