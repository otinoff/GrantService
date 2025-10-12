# План на следующую сессию - 2025-10-12

## 🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА: Claude Code API сервер

### Текущая ситуация
- Сервер 178.236.17.55:8000 работает (/health ✅, /models ✅)
- НО: /chat endpoint возвращает **500 Internal Server Error**
- **Причина**: OAuth токен истёк в `/root/.claude/.credentials.json` на сервере
- **Попытки исправить**:
  - ✅ Добавили ANTHROPIC_API_KEY в .env
  - ✅ Добавили ANTHROPIC_API_KEY в systemd service
  - ✅ Перезапустили сервис
  - ❌ Скопировали токен с локальной машины - но он тоже истёк!
  - ❌ Claude CLI на сервере: "OAuth token has expired"

---

## ✅ РЕШЕНИЕ: Использовать GigaChat для Writer Agent

### Шаг 1: Переключить Writer Agent на GigaChat (2 мин)

**Файл**: `C:\SnowWhiteAI\GrantService\shared\llm\config.py`

**Текущее** (НЕ РАБОТАЕТ):
```python
"writer": {
    "provider": "claude",  # ❌ Claude Code API не работает
    "model": "sonnet",
    "temperature": 0.7,
    "max_tokens": 16000
},
```

**Нужно изменить на** (РАБОТАЕТ):
```python
"writer": {
    "provider": "gigachat",  # ✅ GigaChat работает
    "model": "GigaChat",
    "temperature": 0.7,
    "max_tokens": 8000  # GigaChat лимит
},
```

### Шаг 2: Запустить тест
```bash
python test_writer_real_code.py
```

---

## 🎯 ЦЕЛЬ

Сгенерировать грантовую заявку через основной код:
1. ✅ Writer Agent работает
2. ✅ Использует Research (27 запросов)
3. ✅ Генерирует 9 разделов ФПГ
4. ✅ Создаёт MD файл
5. ✅ Создаёт PDF
6. ✅ Отправляет в Telegram
7. ✅ Правильная номенклатура: #AN-YYYYMMDD-username-NNN

**Время**: ~20 минут
**Приоритет**: 🔴 КРИТИЧЕСКИЙ
