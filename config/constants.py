"""
Константы конфигурации для ГрантСервис бота
"""

# Администраторы бота (Telegram ID)
ADMIN_USERS = [
    5032079932,  # theperipherals (Андрей) - главный админ
]

# Разрешенные пользователи (если список пуст - доступ разрешен всем)
# Добавьте Telegram ID пользователей, которым разрешен доступ
ALLOWED_USERS = []  # Пустой список = доступ для всех

# Настройки безопасности
ENABLE_AUTHORIZATION = False  # True - включить проверку доступа, False - доступ для всех
ENABLE_ADMIN_CHECK = False    # True - проверять права админа, False - все админы

# Роли по умолчанию для новых пользователей
DEFAULT_USER_ROLE = 'user'  # user, editor, admin

# Время жизни токенов (в часах)
TOKEN_LIFETIME_HOURS = 24

# URL админ-панели для разных окружений
ADMIN_BASE_URLS = {
    'development': 'http://localhost:8501',
    'production': 'https://admin.grantservice.onff.ru'
}

# Текущее окружение
ENVIRONMENT = 'development'  # development или production

# Настройки логирования
LOG_LEVEL = 'INFO'
ENABLE_EMOJI_IN_LOGS = True

# Настройки n8n webhook
N8N_WEBHOOK_TIMEOUT = 30  # секунды

# Лимиты
MAX_MESSAGE_LENGTH = 4096  # максимальная длина сообщения Telegram
MAX_QUESTIONS = 50  # максимальное количество вопросов в анкете