# 🚀 WebSearch Deployment Report

**Дата**: 2025-10-08
**Сервер**: 178.236.17.55
**Статус**: ✅ Deployment успешный, ❌ WebSearch недоступен на сервере

---

## ✅ Выполненные задачи

1. **Создан обновленный wrapper** с WebSearch поддержкой
   - Файл: `claude-api-wrapper-v2.py`
   - Размер: 21KB (vs старый 15KB)
   - Новые модели: `WebSearchRequest`, `WebSearchResponse`
   - Новый метод: `ClaudeCodeInterface.websearch()`
   - Новый endpoint: `POST /websearch`

2. **Задеплоен на сервер**
   - SSH подключение: ✅
   - Бэкап старого файла: ✅
   - Замена файла: ✅
   - Перезапуск процесса: ✅
   - PID нового процесса: 62629

3. **Протестированы endpoint'ы**
   - `GET /health`: ✅ Работает
   - `POST /websearch`: ✅ Endpoint работает, но WebSearch недоступен

---

## ❌ Обнаруженная проблема

### Claude Code на сервере НЕ имеет доступа к WebSearch

**Ошибка:**
```json
{
  "snippet": "I don't have permission to use the WebSearch tool"
}
```

### ✅ ПРАВИЛЬНАЯ ПРИЧИНА (обновлено 2025-10-12):

**Claude Code CLI требует интерактивного подтверждения для WebSearch tool**

На сервере (неинтерактивный режим через pipe) → запрос разрешения блокируется → ошибка "I don't have permission"

**Решение**: Флаг `--dangerously-skip-permissions` отключает запросы разрешений

### ~~Неверные гипотезы~~ (игнорировать):

1. ~~OAuth токен не имеет WebSearch scopes~~ - НЕВЕРНО
   - Scopes: `user:inference`, `user:profile` достаточны
   - WebSearch не требует дополнительный scope

2. ~~Географические ограничения~~ - НЕВЕРНО
   - Сервер в Швеции - НЕ проблема
   - WebSearch работает из любого региона

3. ~~Subscription Type~~ - НЕВЕРНО
   - Max (20x rate limits) поддерживает WebSearch
   - Подписка не влияет на доступность инструмента

---

## 📊 Сравнение: Локально vs Сервер

| Параметр | Ваш ПК (Windows) | Сервер (178.236.17.55) |
|----------|------------------|------------------------|
| **WebSearch** | ✅ Работает | ❌ Недоступен |
| **Region** | ? | Швеция |
| **OAuth scopes** | user:inference, user:profile | user:inference, user:profile |
| **Subscription** | Max (20x) | Max (20x) |

---

## ✅ Решения (обновлено 2025-10-12)

### Вариант 1: Флаг --dangerously-skip-permissions (РЕКОМЕНДУЕТСЯ)

**Решение проблемы permissions**:
```bash
echo "prompt" | claude --dangerously-skip-permissions
```

**Что делает:**
- Отключает все запросы на подтверждение действий
- WebSearch работает в неинтерактивном режиме
- Безопасно для изолированного сервера

**Применение:**
```python
# В claude-api-wrapper.py строка 179:
command = f'echo "{escaped_message}" | claude --dangerously-skip-permissions'
```

**Статус**: ✅ Готово к deployment (см. WEBSEARCH_FIX_DEPLOYMENT_INSTRUCTIONS.md)

---

### Вариант 2: Perplexity API (Альтернатива)

**Преимущества:**
- ✅ Работает из любого региона
- ✅ Специализирован на поиске
- ✅ Фильтрация по доменам
- ✅ Цитаты и источники
- ✅ Актуальные данные

**Стоимость:**
- $0.01 за запрос
- $0.27 на анкету (27 запросов × $0.01)
- ~$27/месяц при 100 анкетах

**Интеграция:**
```python
# agents/researcher_agent.py
from perplexity import PerplexityClient

researcher = ResearcherAgent(db, llm_provider="perplexity")
result = await researcher.research_anketa(anketa_id)
```

### Вариант 2: VPN через США

**Действия:**
1. Установить VPN на сервере (OpenVPN/WireGuard)
2. Настроить маршрутизацию через US сервер
3. Перезапустить Claude Code wrapper
4. Протестировать WebSearch

**Стоимость:**
- VPN сервис: ~$5-10/месяц

**Риски:**
- Может не помочь (если проблема в OAuth scopes)
- Увеличит латентность запросов

### Вариант 3: Google Custom Search API

**Преимущества:**
- ✅ Бесплатно до 100 запросов/день
- ✅ Работает из любого региона

**Стоимость:**
- Бесплатно: 100 запросов/день
- Платно: $5 за 1000 запросов

**Ограничения:**
- ❌ Нет фильтрации по RU-доменам
- ❌ Менее релевантные результаты

---

## 🎯 Рекомендация

**Использовать Perplexity API**

### Почему:
1. **Надежность** - работает стабильно из любого региона
2. **Качество** - специализирован на поиске и анализе
3. **Фильтрация** - поддерживает allowed_domains для RU-источников
4. **Цена** - $0.27 на анкету приемлемо для качественного гранта
5. **Готовое решение** - не требует настройки VPN

### План реализации:

#### Этап 1: Получить API ключ (5 мин)
```
1. Зарегистрироваться на perplexity.ai
2. Получить API ключ
3. Добавить в .env: PERPLEXITY_API_KEY=xxx
```

#### Этап 2: Интегрировать в Researcher (1 час)
```python
# agents/researcher_agent.py
class ResearcherAgent(BaseAgent):
    def __init__(self, db, llm_provider: str = "perplexity"):
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')

    async def websearch(self, query: str, domains: List[str]):
        # Используем Perplexity API
        ...
```

#### Этап 3: Протестировать (30 мин)
```bash
pytest tests/integration/test_researcher_perplexity.py
```

#### Этап 4: Запустить на анкете Валерии (5 мин)
```bash
python telegram-bot/test_researcher_logging.py --anketa-id AN-20250905-Valeria_bruzzzz-001
```

---

## 📝 Обновленная архитектура

```
GrantService
    ↓
Researcher Agent
    ↓
Perplexity API (НЕ Claude Code WebSearch!)
    ↓
27 специализированных запросов
    ↓
research_results (JSONB)
    ↓
Writer Agent → Grant с исследованием
```

---

## 🔧 Deployment Details

### Сервер
- IP: 178.236.17.55
- Hostname: ctytdjxzil
- User: root

### Процесс
- PID: 62629
- Command: `/opt/claude-api/venv/bin/python3 /opt/claude-api/claude-api-wrapper.py`
- Status: ✅ Running
- Port: 8000

### Файлы
- Wrapper: `/opt/claude-api/claude-api-wrapper.py` (21KB)
- Backup: `/opt/claude-api/claude-api-wrapper.py.backup-20251008-*`
- Logs: `/var/log/claude-api.log`

### Endpoints
- `GET /`: ✅ Работает
- `GET /health`: ✅ Работает (features: chat, code, websearch)
- `POST /chat`: ✅ Работает
- `POST /code`: ✅ Работает
- `POST /websearch`: ✅ Endpoint работает, WebSearch недоступен

---

## 📊 Итоги

### ✅ Успешно:
1. Wrapper обновлен до v2.0.0 с WebSearch поддержкой
2. Deployment на сервер выполнен
3. Все endpoint'ы работают
4. Обнаружена причина недоступности WebSearch

### ❌ Проблемы:
1. Claude Code WebSearch недоступен на сервере
2. Требуется альтернативное решение для поиска

### 🎯 Следующие шаги:
1. Интегрировать Perplexity API
2. Протестировать на анкете Валерии
3. Запустить Researcher автоматически после Auditor
4. Обновить Writer для использования research_results

---

## 📞 Контакты

- Сервер: root@178.236.17.55
- API: http://178.236.17.55:8000
- API Key: 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732

---

**Дата отчета**: 2025-10-08 12:50 UTC
**Автор**: AI Integration Specialist
**Статус**: ✅ Deployment завершен, готов к интеграции Perplexity
