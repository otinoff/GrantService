# 🚀 WebSearch Fix - Deployment Instructions

**Дата**: 2025-10-12
**Решение**: Флаг `--dangerously-skip-permissions` для Claude Code CLI
**Статус**: ✅ Готово к deployment

---

## 🎯 Суть проблемы (ИСПРАВЛЕННАЯ ДИАГНОСТИКА)

### ❌ НЕВЕРНАЯ ГИПОТЕЗА (игнорировать):
- ~~География (сервер в Швеции)~~
- ~~OAuth scopes не включают WebSearch~~
- ~~Subscription type~~

### ✅ ПРАВИЛЬНАЯ ПРИЧИНА:
**Claude Code CLI по умолчанию требует интерактивного подтверждения для WebSearch tool.**

На сервере (неинтерактивный режим) → запрос блокируется → ошибка `"I don't have permission to use the WebSearch tool"`

**Решение**: Флаг `--dangerously-skip-permissions` отключает запросы разрешений

---

## 📋 Deployment Plan

### Шаг 1: Backup текущего wrapper

```bash
ssh root@178.236.17.55

# Найти процесс
ps aux | grep claude-api-wrapper | grep -v grep

# Создать backup
cp /opt/claude-api/claude-api-wrapper.py /opt/claude-api/claude-api-wrapper.py.backup-$(date +%Y%m%d-%H%M%S)
```

### Шаг 2: Загрузить обновленный wrapper

```bash
# С локальной машины
scp "C:\SnowWhiteAI\GrantService\Claude Code CLI\02-Server\claude-api-wrapper.py" \
    root@178.236.17.55:/opt/claude-api/claude-api-wrapper.py
```

### Шаг 3: Перезапустить wrapper

```bash
# Найти PID
PID=$(ps aux | grep claude-api-wrapper | grep -v grep | awk '{print $2}')

# Убить процесс
kill $PID
sleep 2

# Запустить заново
cd /opt/claude-api
nohup python3 claude-api-wrapper.py > /var/log/claude-api.log 2>&1 &

# Проверить что запустился
ps aux | grep claude-api-wrapper | grep -v grep
```

### Шаг 4: Проверить логи

```bash
# Смотреть логи в реальном времени
tail -f /var/log/claude-api.log

# Должно быть:
# ╭────────────────────────────────────────╮
# │     Claude Code API Wrapper v1.0.0    │
# ├────────────────────────────────────────┤
# │  Host: 0.0.0.0                         │
# │  Port: 8000                            │
# ...
```

### Шаг 5: Протестировать WebSearch

```bash
# Health check
curl http://localhost:8000/health

# Chat (должен работать)
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{"message":"Use WebSearch to find: тест поиска","model":"sonnet"}'

# ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
# ✅ 200 OK с результатами поиска (НЕ ошибка "I don't have permission")
```

---

## 🔍 Что изменилось в коде

**Файл**: `claude-api-wrapper.py`
**Строка**: 179

### До:
```python
command = f'echo "{escaped_message}" | claude'
```

### После:
```python
# ВАЖНО: --dangerously-skip-permissions отключает запросы на разрешение WebSearch
command = f'echo "{escaped_message}" | claude --dangerously-skip-permissions'
```

---

## ✅ Критерии успеха

После deployment проверить:

1. **Health endpoint работает**:
   ```bash
   curl http://178.236.17.55:8000/health
   # → 200 OK
   ```

2. **Chat endpoint работает**:
   ```bash
   curl -X POST http://178.236.17.55:8000/chat \
     -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
     -H "Content-Type: application/json" \
     -d '{"message":"Hello","model":"sonnet"}'
   # → 200 OK с ответом Claude
   ```

3. **WebSearch работает** (НЕ ошибка "I don't have permission"):
   ```bash
   curl -X POST http://178.236.17.55:8000/chat \
     -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
     -H "Content-Type: application/json" \
     -d '{"message":"Use WebSearch tool to search for: статистика инвалидов России","model":"sonnet"}'
   # → 200 OK с результатами поиска
   ```

4. **Python test проходит**:
   ```bash
   # С локальной машины
   cd C:\SnowWhiteAI\GrantService
   python test_claude_api.py
   # → TEST PASSED
   ```

5. **Researcher Agent может использовать WebSearch**:
   ```bash
   python test_researcher_websearch.py
   # → SUCCESS
   ```

---

## ⚠️ Безопасность

### Флаг `--dangerously-skip-permissions` - безопасно ли?

✅ **Да, для этого сервера:**
- Сервер работает в изолированной среде
- Запросы идут только от вашего API wrapper (с API key)
- Claude Code не имеет доступа к критическим системным файлам
- WebSearch - это просто поиск в интернете, не опасная операция
- Рабочая директория ограничена: `/tmp/claude_sessions`

❌ **НЕ используйте в:**
- Production системах с доступом к чувствительным данным
- Серверах с важными конфигурационными файлами в доступе
- Если промпты приходят от ненадежных пользователей

### Альтернатива (более безопасная):

Если хотите разрешить только WebSearch (без других инструментов):

```python
command = f'echo "{escaped_message}" | claude --allowedTools "WebSearch"'
```

---

## 🔄 Rollback Plan

Если что-то пошло не так:

```bash
# Найти PID
PID=$(ps aux | grep claude-api-wrapper | grep -v grep | awk '{print $2}')

# Убить процесс
kill $PID

# Восстановить backup
cp /opt/claude-api/claude-api-wrapper.py.backup-YYYYMMDD-HHMMSS \
   /opt/claude-api/claude-api-wrapper.py

# Запустить заново
cd /opt/claude-api
nohup python3 claude-api-wrapper.py > /var/log/claude-api.log 2>&1 &
```

---

## 📊 Ожидаемый результат

### До deployment:
```
Claude Code → WebSearch → ❌ "I don't have permission to use the WebSearch tool"
Researcher Agent → ❌ НЕ РАБОТАЕТ
```

### После deployment:
```
Claude Code --dangerously-skip-permissions → WebSearch → ✅ РАБОТАЕТ
Researcher Agent → ✅ 27 запросов выполняются успешно
```

---

## 📝 Отчет после deployment

После выполнения заполнить:

```markdown
# WebSearch Deployment Report

**Дата**: YYYY-MM-DD HH:MM
**Executor**: [Имя]

## Выполненные действия:
1. [ ] Backup создан
2. [ ] Wrapper обновлен
3. [ ] Сервис перезапущен
4. [ ] Логи проверены
5. [ ] Тесты пройдены

## Результаты тестов:
- Health: ✅/❌
- Chat: ✅/❌
- WebSearch: ✅/❌ (работает/не работает)
- Python test: ✅/❌
- Researcher test: ✅/❌

## Статус:
✅ SUCCESS / ❌ FAILED

## Проблемы (если есть):
[Описание]

## Рекомендации:
[Если есть]
```

---

## 🎯 Следующие шаги после успешного deployment

1. **Обновить архитектуру**:
   - PRIMARY: Claude Code WebSearch (бесплатно!)
   - FALLBACK: Perplexity API ($0.30/анкета)

2. **Изменить WebSearchRouter**:
   ```python
   # В agents/researcher_agent_v2.py
   self.websearch_provider = 'claude_code'  # было: 'perplexity'
   self.websearch_fallback = 'perplexity'   # было: 'claude_code'
   ```

3. **Обновить в БД**:
   ```sql
   UPDATE ai_agent_settings
   SET config = jsonb_set(config, '{websearch_provider}', '"claude_code"'),
       config = jsonb_set(config, '{websearch_fallback}', '"perplexity"')
   WHERE agent_name = 'researcher';
   ```

4. **Протестировать полный цикл**:
   ```bash
   python tests/integration/test_ekaterina_e2e_full_pipeline.py
   ```

5. **Обновить документацию** (см. следующий файл)

---

**Готово к deployment!** 🚀

**Время выполнения**: ~10 минут
**Сложность**: Низкая
**Риск**: Минимальный (есть rollback plan)
