# 🤖 Claude Code Expert - Quick Reference

**Создан:** 2025-10-12
**Агент:** `claude-code-expert`
**Статус:** ✅ Активен

---

## 🎯 Когда использовать

Вызывайте `@claude-code-expert` когда нужна помощь с:

1. **Claude Code API проблемы**
   - 500 errors
   - OAuth/credentials issues
   - Rate limiting
   - Health check failures

2. **WebSearch интеграция**
   - Researcher Agent настройка
   - WebSearch не работает
   - Оптимизация queries

3. **Интеграция с Python**
   - ClaudeCodeClient usage
   - Error handling
   - Retry logic
   - Model selection

4. **Troubleshooting**
   - Диагностика проблем
   - Проверка логов
   - Обновление credentials

5. **Best Practices**
   - Temperature настройка
   - Token optimization
   - Monitoring & metrics

---

## 📝 Примеры использования

### 1. Диагностика проблемы

```
@claude-code-expert Claude API возвращает 500 error, помоги разобраться
```

**Агент проверит:**
- Health endpoint status
- Credentials expiration
- Server logs
- Process status

### 2. Оптимизация интеграции

```
@claude-code-expert Как правильно выбирать между Sonnet и Opus для Writer Agent?
```

**Агент предложит:**
- Рекомендации по выбору модели
- Temperature настройки
- Token optimization tips
- Примеры кода

### 3. WebSearch настройка

```
@claude-code-expert Researcher Agent не может использовать WebSearch, что делать?
```

**Агент проверит:**
- WebSearch client configuration
- API permissions
- Credentials
- Integration code

### 4. Monitoring setup

```
@claude-code-expert Хочу добавить мониторинг Claude API usage, как лучше?
```

**Агент предложит:**
- Метрики для отслеживания
- Logging setup
- Alerting thresholds
- Dashboard примеры

---

## 🔧 Быстрые команды

### Health Check
```bash
curl http://178.236.17.55:8000/health
```

### Тест API
```bash
python test_claude_api.py
```

### Проверка credentials
```bash
ssh root@178.236.17.55 "cat /root/.claude/.credentials.json"
```

### Логи
```bash
ssh root@178.236.17.55 "tail -50 /var/log/claude-api.log"
```

---

## 📚 Knowledge Base

Агент имеет доступ к:

- ✅ **README.md** - Центральная документация
- ✅ **CLAUDE-CODE-BEST-PRACTICES.md** - 34KB best practices
- ✅ **CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md** - 50KB architecture
- ✅ **WEBSEARCH_*.md** - WebSearch integration history
- ✅ **Troubleshooting guides** - Решённые проблемы

---

## 🎓 Специализация

### OAuth & Credentials
- ✅ Token lifecycle management
- ✅ Credentials refresh
- ✅ Multi-environment setup

### HTTP API Integration
- ✅ Endpoints: /health, /models, /chat, /code
- ✅ Authentication (Bearer token)
- ✅ Error handling
- ✅ Retry logic

### WebSearch
- ✅ Researcher Agent integration
- ✅ 27 specialized queries
- ✅ Results storage (PostgreSQL)

### Agent Integration
- ✅ Researcher (WebSearch)
- ✅ Writer (Opus 4)
- ✅ Auditor (Opus 4)

---

## ⚡ Pro Tips

1. **Всегда указывай контекст:**
   ```
   @claude-code-expert
   Проблема: Writer Agent timeout
   Код: agents/writer_agent_v2.py
   Ошибка: [вставить traceback]
   ```

2. **Агент знает историю проблем:**
   - 500 error fix (2025-10-08)
   - WebSearch integration
   - Rate limiting solutions

3. **Агент даёт готовые решения:**
   - Не только теория, но и working code
   - Ссылки на конкретные файлы
   - Проверенные на production

4. **Агент помогает с мониторингом:**
   - Metrics setup
   - Logging configuration
   - Alerting thresholds

---

## 🔗 Связанные файлы

- **Агент:** `.claude/agents/claude-code-expert.md`
- **Документация:** `Claude Code CLI/`
- **Клиенты:** `shared/llm/claude_code_*.py`
- **Тесты:** `test_claude_*.py`

---

## 📊 Статистика использования

После использования агента обновляй эту секцию:

- **Задач решено:** 0
- **Troubleshooting кейсов:** 0
- **Оптимизаций предложено:** 0
- **Документации создано:** 0

---

**Агент автоматически загружается при запуске Claude Code!** 🎉

Просто используй `@claude-code-expert` в любом чате.
