-- Iteration 35: Switch to GigaChat for Sber500 Bootcamp
-- Переключить пользователя на GigaChat для исправления Claude API errors

-- 1. Проверить текущий provider
SELECT telegram_id, username, preferred_llm_provider
FROM users
WHERE telegram_id = 5032079932;

-- 2. Переключить на GigaChat
UPDATE users
SET preferred_llm_provider = 'gigachat'
WHERE telegram_id = 5032079932;

-- 3. Проверить что изменилось
SELECT telegram_id, username, preferred_llm_provider
FROM users
WHERE telegram_id = 5032079932;

-- Примечание: Это также начнет накапливать статистику токенов для Sber500 Bootcamp!
