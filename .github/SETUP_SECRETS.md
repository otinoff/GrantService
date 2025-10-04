# GitHub Secrets Setup for CI/CD

## Required Secrets

Чтобы CI/CD работал корректно, нужно добавить следующие секреты в GitHub:

### 1. VPS Connection Secrets (уже настроены)

- ✅ `VPS_HOST` = `5.35.88.251`
- ✅ `VPS_USER` = `root`
- ✅ `VPS_SSH_KEY` = (приватный SSH ключ)
- ✅ `VPS_PORT` = `22` (опционально)

### 2. Telegram Bot Token (НОВОЕ - требуется настроить!)

- ⚠️ `TELEGRAM_BOT_TOKEN` - токен бота для уведомлений в группу

#### Как получить TELEGRAM_BOT_TOKEN:

1. **Использовать существующий бот** (@Grafana_SnowWhite_bot):
   - Токен должен быть в `config/.env` на сервере
   - Скопировать значение `TELEGRAM_BOT_TOKEN` из файла

2. **Или создать отдельный бот для CI/CD**:
   - Написать @BotFather в Telegram
   - Команда `/newbot`
   - Указать имя бота (например, "GrantService Deploy Bot")
   - Получить токен

#### Как добавить секрет в GitHub:

```bash
# Вариант 1: Через веб-интерфейс
1. Перейти в репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Нажать "New repository secret"
4. Name: TELEGRAM_BOT_TOKEN
5. Value: <вставить токен бота>
6. Нажать "Add secret"

# Вариант 2: Через GitHub CLI
gh secret set TELEGRAM_BOT_TOKEN --body "7686393933:AAG_example_token_here"
```

## Проверка настройки

После добавления секрета:

1. Перейти в **Actions** tab
2. Запустить workflow вручную: **Run workflow**
3. Проверить что уведомления приходят в группу -4930683040

## Группа для уведомлений

- **Chat ID**: `-4930683040`
- **Название**: "Грантсервис"
- **Тип уведомлений**:
  - 🚀 Deployment started
  - ✅ Deployment success
  - ❌ Deployment failed (с rollback)
  - ❌ Tests failed (деплой заблокирован)

## Безопасность

- ✅ Токен бота хранится в GitHub Secrets (зашифрован)
- ✅ Не отображается в логах
- ✅ Доступен только для GitHub Actions
- ✅ Может отправлять сообщения только в группу

## Troubleshooting

### Уведомления не приходят:

1. **Проверить что бот добавлен в группу**:
   ```bash
   # Отправить тестовое сообщение
   curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
     -d "chat_id=-4930683040" \
     -d "text=Test notification"
   ```

2. **Проверить что токен правильный**:
   ```bash
   # Проверить информацию о боте
   curl "https://api.telegram.org/bot<TOKEN>/getMe"
   ```

3. **Проверить права бота в группе**:
   - Бот должен быть участником группы
   - Бот должен иметь права на отправку сообщений

### Workflow падает на шаге с уведомлениями:

- Проверить что секрет `TELEGRAM_BOT_TOKEN` добавлен в GitHub
- Проверить что chat_id правильный: `-4930683040`
- Проверить логи workflow в GitHub Actions

---

**Дата создания**: 2025-10-04
**Последнее обновление**: Оптимизация CI/CD с тестами и уведомлениями
