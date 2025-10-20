# Базовые правила использования Claude Code в GrantService

**Дата создания:** 2025-10-12
**Статус:** ОБЯЗАТЕЛЬНО К ИСПОЛНЕНИЮ

---

## 🎯 ГЛАВНОЕ НАМЕРЕНИЕ

**Claude Code Sonnet 4.5 ДОЛЖЕН работать на сервере GrantService**

### Почему это важно:

1. **Claude Sonnet 4.5** - одна из лучших AI моделей в мире (если не лучшая)
2. **WebSearch встроен** - уникальная возможность для качественных исследований
3. **Подписка $200/месяц** - уже оплачена и должна использоваться
4. **Качество текстов** - превосходит альтернативы (Perplexity, GigaChat)
5. **GrantService** - премиум продукт, требует премиум инструментов

---

## 🚫 ЧТО ЭТО НЕ ЗНАЧИТ

**НЕ удаленный доступ по SSH!**

Мы НЕ говорим про:
- Подключение к серверу через SSH с локального ПК
- Использование VS Code Remote SSH
- Работу через терминал с Windows на Linux

---

## ✅ ЧТО ЭТО ЗНАЧИТ

**Локальная работа Claude Code НА СЕРВЕРЕ**

Сервер GrantService (178.236.17.55):
```
[Telegram Bot] → [Writer Agent V2] → [Claude Sonnet 4.5 API] → [Генерация грантов]
                          ↓
              Всё работает ЛОКАЛЬНО на сервере
              НЕТ SSH подключений
              НЕТ wrapper через :8000
```

---

## 📋 ТРЕБОВАНИЯ К РЕШЕНИЮ

### 1. Использовать Anthropic SDK напрямую

**НЕ через wrapper!** Wrapper - это костыль с проблемами.

**ПРАВИЛЬНО:**
```python
import anthropic

client = anthropic.Anthropic()  # Использует ~/.claude/.credentials.json
# ИЛИ
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
```

### 2. Локальная работа на сервере

Все компоненты на одном сервере:
- ✅ PostgreSQL база (localhost)
- ✅ Telegram Bot (localhost)
- ✅ Writer Agent (localhost)
- ✅ Claude API вызовы (локально, не через HTTP wrapper)

### 3. OAuth credentials или API Key

**Приоритет 1:** OAuth (Claude Max subscription $200/мес)
- Файл: `/root/.claude/.credentials.json`
- Включает: accessToken, refreshToken, expiresAt
- Автообновление через refreshToken

**Приоритет 2:** API Key (fallback)
- Env variable: `ANTHROPIC_API_KEY`
- Для стабильности если OAuth глючит

### 4. Качество текстов = приоритет #1

Writer Agent ДОЛЖЕН использовать лучшую модель:
- ✅ Claude Opus 4 - для сложных разделов (Актуальность, Новизна)
- ✅ Claude Sonnet 4.5 - для быстрых разделов
- ❌ НЕ Perplexity (только временно, пока настраиваем)
- ❌ НЕ GigaChat (только для Interviewer на русском языке)

---

## 🔧 ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ

### Файл: `shared/llm/unified_llm_client.py`

**УЖЕ ПОДДЕРЖИВАЕТ прямой вызов Claude!**

```python
# Строки 54-59, 311-366
async def _generate_claude_code(self, prompt: str, ...):
    # ИСПОЛЬЗУЕТ Anthropic SDK напрямую
    # НЕ использует wrapper через :8000
```

### Файл: `shared/llm/config.py`

**ЦЕЛЕВАЯ конфигурация:**

```python
# Claude Code API настройки
CLAUDE_CODE_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')  # Fallback
CLAUDE_CODE_BASE_URL = ""  # НЕ НУЖЕН! Прямой SDK вызов
CLAUDE_CODE_DEFAULT_MODEL = "opus"  # Топовое качество

AGENT_CONFIGS = {
    "writer": {
        "provider": "claude",  # ← ЦЕЛЕВОЕ СОСТОЯНИЕ
        "model": "opus",       # ← Лучшее качество для грантов
        "temperature": 0.7,
        "max_tokens": 8000
    },
    "researcher": {
        "provider": "claude",  # ← Claude для исследований
        "model": "sonnet",     # ← С WebSearch
        "temperature": 0.3,
        "max_tokens": 1500
    },
    "auditor": {
        "provider": "claude",  # ← Claude для оценки
        "model": "sonnet",
        "temperature": 0.3,
        "max_tokens": 3000
    },
    "interviewer": {
        "provider": "gigachat",  # ← Только для русского языка
        "model": "GigaChat",
        "temperature": 0.5,
        "max_tokens": 1000
    }
}
```

---

## 🎯 ЦЕЛЕВОЕ СОСТОЯНИЕ

### Что должно быть:

1. ✅ **Writer Agent** использует Claude Opus через Anthropic SDK
2. ✅ **Researcher Agent** использует Claude Sonnet + WebSearch
3. ✅ **Auditor Agent** использует Claude Sonnet для оценки
4. ✅ **Всё работает локально** на сервере (без SSH, без wrapper)
5. ✅ **OAuth credentials** автоматически обновляются (refreshToken)
6. ✅ **Качество грантов** максимальное (Claude Opus)

### Что НЕ должно быть:

- ❌ Wrapper через :8000 (костыль с проблемами)
- ❌ SSH подключения для работы (только для администрирования)
- ❌ Perplexity для Writer (только временно)
- ❌ GigaChat для Writer (низкое качество текстов)
- ❌ Потеря OAuth токенов (должен автообновляться)

---

## 📊 СРАВНЕНИЕ МОДЕЛЕЙ

| Модель | Качество | Скорость | WebSearch | Стоимость | Использование |
|--------|----------|----------|-----------|-----------|---------------|
| **Claude Opus 4** | ⭐⭐⭐⭐⭐ | 400 tok/s | ❌ | $200/мес | Writer (сложные разделы) |
| **Claude Sonnet 4.5** | ⭐⭐⭐⭐⭐ | 800 tok/s | ✅ | $200/мес | Researcher, Auditor |
| **Perplexity Sonar** | ⭐⭐⭐⭐ | 1200 tok/s | ✅ | API credits | Временно (пока настраиваем) |
| **GigaChat** | ⭐⭐⭐ | 200 tok/s | ❌ | Бесплатно | Только Interviewer |

---

## 🚀 ПЛАН ДЕЙСТВИЙ

### Фаза 1: Проверка текущего состояния ✅ DONE
- [x] Обновили OAuth credentials на сервере
- [x] Проверили UnifiedLLMClient поддержку Claude
- [x] Убедились что Anthropic SDK установлен

### Фаза 2: Переключение на Claude (NEXT)
- [ ] Установить ANTHROPIC_API_KEY как fallback
- [ ] Изменить config.py для Writer Agent
- [ ] Протестировать генерацию текста через Claude
- [ ] Проверить качество грантов (сравнить с Perplexity)

### Фаза 3: Оптимизация
- [ ] Настроить автообновление OAuth через refreshToken
- [ ] Добавить мониторинг использования токенов
- [ ] Настроить smart routing (Opus для сложных, Sonnet для простых)

### Фаза 4: Production
- [ ] Все агенты используют Claude
- [ ] Качество грантов максимальное
- [ ] Стабильная работа 24/7
- [ ] Подписка $200/мес оправдывает себя

---

## 💰 ЭКОНОМИЧЕСКОЕ ОБОСНОВАНИЕ

**Подписка Claude Max: $200/месяц**

**Что включает:**
- Unlimited Claude Opus 4 (топовое качество)
- Unlimited Claude Sonnet 4.5 (быстро + качественно)
- 20x rate limits (против обычного API)
- WebSearch встроен
- Priority support

**Если НЕ использовать Max, а платить за API:**
- Claude Opus API: ~$15 input / $75 output за 1M tokens
- 100 грантов по 25k tokens каждый = 2.5M tokens
- Output tokens: 2.5M * $75 = $187.50
- Input tokens: промпты ~1M * $15 = $15
- **Итого: ~$200 за 100 грантов**

**ВЫВОД:** Max subscription выгоден при >100 грантов/месяц.

---

## 🔒 БЕЗОПАСНОСТЬ

### OAuth Credentials

**Файл:** `/root/.claude/.credentials.json`

**Права доступа:**
```bash
chmod 600 /root/.claude/.credentials.json
chown root:root /root/.claude/.credentials.json
```

**Структура:**
```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1760293563957,
    "scopes": ["user:inference", "user:profile"],
    "subscriptionType": "max"
  }
}
```

**Автообновление:**
- refreshToken действителен ~90 дней
- accessToken обновляется автоматически через Anthropic SDK
- НЕ нужен wrapper для обновления

---

## 📝 ПРИНЦИПЫ РАЗРАБОТКИ

### 1. Качество > Скорость
Writer Agent должен генерировать ЛУЧШИЕ гранты, даже если это занимает больше времени.

### 2. Простота > Сложность
Прямой API вызов лучше чем wrapper через HTTP endpoint.

### 3. Стабильность > Фичи
Лучше один стабильный провайдер (Claude) чем 5 разных с проблемами.

### 4. Оправдание подписки
Если платим $200/мес за Claude Max - ДОЛЖНЫ его использовать максимально.

---

## ⚠️ ЗАПРЕТЫ

### НЕ ДЕЛАТЬ:

1. ❌ **НЕ создавать wrapper** через :8000 или другой порт
   - Причина: фундаментальные проблемы с аутентификацией
   - Альтернатива: прямой SDK вызов

2. ❌ **НЕ использовать Perplexity для Writer** в production
   - Причина: качество ниже, подписка не оправдывается
   - Исключение: только временно, пока настраиваем Claude

3. ❌ **НЕ использовать GigaChat для генерации грантов**
   - Причина: низкое качество текстов на английском
   - Исключение: только для Interviewer (русский язык)

4. ❌ **НЕ игнорировать истечение OAuth токена**
   - Причина: потеря доступа к Claude Max
   - Решение: мониторинг expiresAt + автообновление

---

## 🎓 ЗНАНИЯ ДЛЯ CLAUDE CODE ЭКСПЕРТА

### Документация (актуальная):

1. **Anthropic SDK:** https://github.com/anthropics/anthropic-sdk-python
2. **Claude API Docs:** https://docs.anthropic.com/
3. **OAuth Flow:** https://docs.anthropic.com/en/docs/claude-code/iam
4. **Known Issues:** https://github.com/anthropics/claude-code/issues

### Отзывы пользователей:

См. файл: `Отзывы об использовании Claude Code CLI на удаленн.md`

**Ключевые выводы:**
- Wrapper подход имеет фундаментальные ограничения
- Прямой API доступ - правильное решение
- OAuth токены могут теряться в SSH сессиях
- Anthropic SDK работает стабильнее чем wrapper

---

## 🔄 ОБНОВЛЕНИЕ ЭТОГО ДОКУМЕНТА

**Когда обновлять:**
- Изменение стратегии использования Claude
- Новые проблемы/решения
- Изменение подписки или цен
- Выход новых моделей (Claude Opus 4.5 и т.д.)

**Кто обновляет:**
- @claude-code-expert agent
- @grant-architect agent
- Разработчик вручную при важных изменениях

---

## ✅ КОНТРОЛЬНАЯ ТОЧКА

**Перед любым изменением спросить:**

1. Соответствует ли это главному намерению? (Claude должен работать)
2. Оправдывает ли это подписку $200/мес?
3. Улучшит ли это качество грантов?
4. Является ли решение стабильным и простым?

**Если хотя бы один ответ "НЕТ" - пересмотреть подход.**

---

**Версия:** 1.0
**Последнее обновление:** 2025-10-12
**Статус:** ACTIVE - обязательно к применению
