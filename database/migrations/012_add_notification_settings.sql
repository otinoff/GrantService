-- Migration 012: Add admin notification settings table
-- Created: 2025-10-12
-- Purpose: Add settings for controlling PDF notifications to admin chat

-- =====================================================
-- CREATE TABLE: admin_notification_settings
-- =====================================================

CREATE TABLE IF NOT EXISTS admin_notification_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system'
);

-- =====================================================
-- INSERT DEFAULT SETTINGS
-- =====================================================

-- Main toggle
INSERT INTO admin_notification_settings (setting_key, setting_value, description)
VALUES
    ('notifications_enabled', TRUE, 'Главный переключатель PDF уведомлений в админский чат')
ON CONFLICT (setting_key) DO NOTHING;

-- Stage-specific toggles
INSERT INTO admin_notification_settings (setting_key, setting_value, description)
VALUES
    ('notify_on_interview', TRUE, 'Отправлять PDF анкеты после завершения интервью'),
    ('notify_on_audit', TRUE, 'Отправлять PDF аудита после завершения оценки'),
    ('notify_on_research', TRUE, 'Отправлять PDF исследования после завершения 27 queries'),
    ('notify_on_grant', TRUE, 'Отправлять PDF гранта после написания заявки'),
    ('notify_on_review', TRUE, 'Отправлять PDF ревью после проверки ревьювером')
ON CONFLICT (setting_key) DO NOTHING;

-- =====================================================
-- CREATE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_notification_settings_key
ON admin_notification_settings(setting_key);

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE admin_notification_settings IS 'Настройки для PDF уведомлений в админский чат (-4930683040)';
COMMENT ON COLUMN admin_notification_settings.setting_key IS 'Ключ настройки (notifications_enabled, notify_on_interview, и т.д.)';
COMMENT ON COLUMN admin_notification_settings.setting_value IS 'Значение настройки (TRUE = включено, FALSE = выключено)';
COMMENT ON COLUMN admin_notification_settings.description IS 'Описание настройки для админки';

-- =====================================================
-- VERIFICATION
-- =====================================================

-- Проверка созданной таблицы
SELECT
    setting_key,
    setting_value,
    description
FROM admin_notification_settings
ORDER BY id;

-- Ожидаемый результат:
-- notifications_enabled | TRUE | Главный переключатель...
-- notify_on_interview   | TRUE | Отправлять PDF анкеты...
-- notify_on_audit       | TRUE | Отправлять PDF аудита...
-- notify_on_research    | TRUE | Отправлять PDF исследования...
-- notify_on_grant       | TRUE | Отправлять PDF гранта...
-- notify_on_review      | TRUE | Отправлять PDF ревью...

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Функция для получения значения настройки
CREATE OR REPLACE FUNCTION get_notification_setting(p_key VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_value BOOLEAN;
BEGIN
    SELECT setting_value INTO v_value
    FROM admin_notification_settings
    WHERE setting_key = p_key;

    -- Если настройка не найдена, возвращаем TRUE по умолчанию
    RETURN COALESCE(v_value, TRUE);
END;
$$ LANGUAGE plpgsql;

-- Функция для обновления настройки
CREATE OR REPLACE FUNCTION update_notification_setting(
    p_key VARCHAR,
    p_value BOOLEAN,
    p_updated_by VARCHAR DEFAULT 'admin'
)
RETURNS VOID AS $$
BEGIN
    UPDATE admin_notification_settings
    SET
        setting_value = p_value,
        updated_at = NOW(),
        updated_by = p_updated_by
    WHERE setting_key = p_key;

    -- Если настройка не найдена, создаем её
    IF NOT FOUND THEN
        INSERT INTO admin_notification_settings (setting_key, setting_value, updated_by)
        VALUES (p_key, p_value, p_updated_by);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- USAGE EXAMPLES
-- =====================================================

-- Получить значение настройки
-- SELECT get_notification_setting('notify_on_interview');

-- Обновить настройку
-- SELECT update_notification_setting('notify_on_interview', FALSE, 'admin@example.com');

-- Отключить все уведомления
-- SELECT update_notification_setting('notifications_enabled', FALSE, 'admin@example.com');

-- =====================================================
-- ROLLBACK (если нужен откат)
-- =====================================================

-- DROP TABLE IF EXISTS admin_notification_settings;
-- DROP FUNCTION IF EXISTS get_notification_setting(VARCHAR);
-- DROP FUNCTION IF EXISTS update_notification_setting(VARCHAR, BOOLEAN, VARCHAR);

-- =====================================================
-- END OF MIGRATION 012
-- =====================================================
