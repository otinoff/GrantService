# Changelog
**Version**: 1.0.1 | **Last Modified**: 2025-09-30

All notable changes to GrantService project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2025-09-30

### Added
- **Concrete production data** for Telegram bot:
  - Bot username: @Grafana_SnowWhite_bot (ID: 8057176426)
  - Admin group: "Грантсервис" (ID: -4930683040)
- **Testing infrastructure** for admin notifications:
  - test_admin_notifications_unit.py - модульные тесты (13/13 пройдено)
  - test_notification_demo.py - демонстрация работы
  - test_notification_readiness.py - проверка готовности (92.3%)
  - send_real_notification.py - отправка реальных уведомлений

### Changed
- **AdminNotifier improvements** (telegram-bot v2.1.4):
  - Добавлен импорт `from telegram.constants import ParseMode`
  - Улучшена обработка None значений в данных заявки
  - Расширено логирование для отладки

### Fixed
- **Message formatting** в уведомлениях администраторам
- **Error handling** при отправке уведомлений в группу
- **None value processing** в данных заявок

### Testing
- **Production readiness**: 92.3% готовности к продакшну
- **Successful notification**: Message ID 313 отправлено в admin группу
- **Full test coverage**: 13/13 модульных тестов пройдено

### Documentation
- **DEPLOYMENT.md v1.0.2**: Добавлены конкретные данные бота и тестовые команды
- **COMPONENTS.md v1.0.2**: Обновлена документация AdminNotifier с примерами v2.1.4
- **API_REFERENCE.md v1.0.1**: Добавлен endpoint для admin notifications
- **README.md v1.0.2**: Обновлена навигационная таблица

## [1.0.1] - 2025-09-29

### Added
- **AdminNotifier class** in `telegram-bot/utils/admin_notifications.py`
  - Автоматические уведомления администраторам о новых заявках
  - Отправка в группу администраторов (ID: -4930683040)
  - Форматированные сообщения с данными заявки и пользователя
  - Обработка ошибок отправки уведомлений
- Grant document sending mechanism with detailed logging
- Cross-platform database path compatibility

### Changed
- **Database integration**: Обновлен метод `save_grant_application()` с интеграцией уведомлений
- Removed question type display from telegram bot files
- Enhanced database file exclusion in .gitignore
- Updated GitHub Actions workflow for database protection

### Documentation
- **COMPONENTS.md v1.0.1**: Добавлена документация AdminNotifier класса
- **DATABASE.md v1.0.1**: Обновлено описание бизнес-логики save_grant_application
- **DEPLOYMENT.md v1.0.1**: Добавлена конфигурация ADMIN_GROUP_ID для уведомлений
- **README.md v1.0.1**: Обновлена навигационная таблица
- **CHANGELOG.md v1.0.0**: Создан файл истории изменений

### Fixed
- Streamlit compatibility issues in web-admin panel
- Cross-platform database paths for Windows/Linux
- GitHub Actions database protection

### Removed
- Authorization from admin panel main page for easier access
- Database files from Git tracking

## [1.0.0] - 2025-01-29

### Added
- Initial documentation structure
- Core system architecture documentation
- Database schema documentation
- API reference documentation
- AI agents configuration documentation
- Deployment guide
- Components overview

### Documentation
- Created modular documentation structure
- Established version control for documentation files
- Set up cross-referencing between documentation sections

---

**Documentation Management Rules:**
- Each documentation file has independent versioning
- Updates are tracked in this changelog
- README.md maintains overview and navigation
- All changes must update corresponding documentation files