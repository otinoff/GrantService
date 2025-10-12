# Claude Code API добавлен в настройки ✅

**Дата**: 2025-10-08 12:02
**Страница**: `web-admin/pages/⚙️_Настройки.py`

---

## 📊 Что добавлено

### 1. Статус Claude Code API в разделе "Статус сервисов"

**4 сервиса теперь:**
- ✅ База данных (PostgreSQL)
- ✅ **Claude Code API** ← НОВОЕ
- 🔄 Telegram Bot
- 🔄 GigaChat API

**Проверка подключения:**
```python
response = requests.get(f"{claude_base_url}/health", timeout=3)
if response.status_code == 200:
    st.success("✅ Подключен")
    st.caption("Sonnet 4.5 (безлимит)")
```

**Индикация:**
- ✅ Зелёный = подключен
- ❌ Красный = ошибка/недоступен
- 🔄 Жёлтый = неизвестно

---

### 2. Секция "Claude Code API (Основная модель)"

**Информация отображается:**
- **API URL**: `http://178.236.17.55:8000`
- **API Key**: `1f79b062...27aa0732` (замаскированный)
- **Модель**: Claude Sonnet 4.5 (200k контекст)
- **Статус**: ✅ Активна / ❌ Недоступна
- **Лимиты**: Безлимитная (по подписке)

**Кнопки действий:**

1. **🔄 Проверить подключение**
   - GET /health
   - Результат: ✅/❌

2. **📊 Проверить модели**
   - GET /models (с Authorization header)
   - Показывает список: `Claude Sonnet 4.5 (sonnet), Claude Opus 4 (opus)`
   - Требует API ключ для авторизации

---

### 3. GigaChat переименован в Fallback

**Было:**
```
🔧 Настройки API
  ├── GigaChat API
  └── Telegram Bot
```

**Стало:**
```
🔧 Дополнительные API (Fallback)
  ├── GigaChat API (Fallback)
  │   └── ⚠️ Используется только если Claude Code недоступен
  └── Telegram Bot
```

---

## 🔑 Откуда берутся данные

### Переменные окружения (`.env`)
```bash
CLAUDE_CODE_API_KEY=1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732
CLAUDE_CODE_BASE_URL=http://178.236.17.55:8000
CLAUDE_CODE_DEFAULT_MODEL=sonnet
```

### Проверка в коде
```python
claude_api_key = os.getenv('CLAUDE_CODE_API_KEY', '1f79b062...')
claude_base_url = os.getenv('CLAUDE_CODE_BASE_URL', 'http://178.236.17.55:8000')
```

---

## 📈 Преимущества Claude Code

| Параметр | Claude Code | GigaChat |
|----------|-------------|----------|
| **Контекст** | 200k токенов | 8k токенов |
| **Лимиты** | ✅ Безлимитный (подписка) | ❌ Ограниченный |
| **Качество** | ⭐⭐⭐⭐⭐ Sonnet 4.5 | ⭐⭐⭐ GigaChat |
| **Скорость** | Быстро | Средне |
| **Стоимость** | Фиксированная подписка | По токенам |

**Вывод**: Claude Code - основная модель, GigaChat - fallback на случай недоступности

---

## 🎯 Как использовать

### В админ-панели

1. Откройте `Настройки → Система`
2. Проверьте статус **Claude Code API**
3. Убедитесь: ✅ Подключен
4. Нажмите **🔄 Проверить подключение** для теста
5. Нажмите **📊 Проверить модели** чтобы увидеть список

### В коде агентов

```python
import os

# Получить настройки
claude_api_key = os.getenv('CLAUDE_CODE_API_KEY')
claude_base_url = os.getenv('CLAUDE_CODE_BASE_URL')

# Использовать
from shared.llm.claude_code_client import ClaudeCodeClient

async with ClaudeCodeClient(api_key=claude_api_key, base_url=claude_base_url) as client:
    response = await client.chat("Оцени этот проект...")
```

---

## ✅ Тестирование

### Открыть страницу настроек
```bash
python launcher.py
# Откроется: http://localhost:8501
# Перейти: Настройки → Система
```

**Проверить:**
- ✅ Claude Code API показывает статус
- ✅ API URL отображается
- ✅ API Key замаскирован правильно
- ✅ Кнопки "Проверить подключение" и "Проверить модели" работают
- ✅ GigaChat помечен как Fallback

---

## 📝 Следующие шаги

1. **Добавить проверку Telegram Bot** - аналогично Claude Code
2. **Добавить проверку GigaChat** - GET /health
3. **Сохранение настроек в БД** - таблица `system_settings`
4. **История использования API** - логи запросов к Claude/GigaChat
5. **Статистика токенов** - сколько потрачено за день/месяц

---

**Статус**: ✅ Готово к использованию
**Файл**: `web-admin/pages/⚙️_Настройки.py:80-158`
