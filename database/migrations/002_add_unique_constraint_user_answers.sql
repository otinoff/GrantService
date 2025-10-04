-- Миграция: Добавление UNIQUE constraint на user_answers
-- Дата: 2025-10-04
-- Цель: Предотвратить дубликаты ответов на один вопрос в одной сессии

-- Проверяем наличие дубликатов перед добавлением constraint
DO $$
BEGIN
    -- Проверка на дубликаты
    IF EXISTS (
        SELECT session_id, question_id, COUNT(*)
        FROM user_answers
        GROUP BY session_id, question_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Найдены дубликаты! Сначала удалите дублирующиеся записи.';
    END IF;
END $$;

-- Добавляем UNIQUE constraint
ALTER TABLE user_answers
ADD CONSTRAINT unique_session_question
UNIQUE (session_id, question_id);

-- Добавляем комментарий
COMMENT ON CONSTRAINT unique_session_question ON user_answers IS
'Предотвращает дубликаты ответов: один пользователь может ответить на вопрос только один раз в рамках сессии';
