# 🤖 Политика выбора LLM провайдера для GrantService

**Дата:** 2025-10-22
**Статус:** КРИТИЧЕСКАЯ ВАЖНОСТЬ
**Версия:** 1.0

---

## ⚠️ ВАЖНО: Claude Code - ЕДИНСТВЕННЫЙ основной LLM

### ❌ НЕПРАВИЛЬНО (что было раньше):
```
Основной LLM: GigaChat
Fallback: Claude Code
```

### ✅ ПРАВИЛЬНО (как должно быть):
```
Основной LLM: Claude Code
Fallback: НЕТ (нет автоматического fallback)
GigaChat: Только мануальный выбор пользователя
```

---

## 📋 Политика использования LLM

### 1. Claude Code - Основной и единственный провайдер

**Для всех агентов по умолчанию:**
- ✅ InterviewerAgent → `claude_code`
- ✅ ResearcherAgent → `claude_code`
- ✅ WriterAgent → `claude_code`
- ✅ ReviewerAgent → `claude_code`
- ✅ AuditorAgent → `claude_code`

**Код:**
```python
# ✅ ПРАВИЛЬНО
agent = InteractiveInterviewerAgent(
    db=db,
    llm_provider="claude_code"  # Основной и единственный!
)

# ❌ НЕПРАВИЛЬНО
agent = InteractiveInterviewerAgent(
    db=db,
    llm_provider="gigachat"  # НЕТ! Только Claude Code!
)
```

### 2. GigaChat - Только мануальный выбор

**GigaChat используется ТОЛЬКО если:**
- Пользователь ЯВНО выбрал GigaChat в настройках
- Разработчик ВРУЧНУЮ указал `llm_provider="gigachat"`

**НЕ используется:**
- ❌ Автоматический fallback при недоступности Claude Code
- ❌ По умолчанию
- ❌ В примерах кода

### 3. Поведение при недоступности Claude Code

**Если Claude Code недоступен:**
```
1. Логируем ошибку
2. Показываем пользователю сообщение:
   "⚠️ LLM временно недоступен. Попробуйте позже."
3. НЕ переключаемся на GigaChat автоматически
4. Возвращаем ошибку
```

**Код error handling:**
```python
try:
    response = await self.llm_client.generate_async(
        prompt=prompt,
        provider="claude_code"
    )
except Exception as e:
    logger.error(f"❌ Claude Code unavailable: {e}")

    # НЕ делаем fallback на GigaChat!
    # Вместо этого возвращаем ошибку пользователю
    return {
        'status': 'error',
        'message': 'LLM temporarily unavailable. Please try again later.',
        'error': str(e)
    }
```

---

## 📝 Конфигурация по умолчанию

### shared/llm/config.py

```python
# LLM PROVIDER POLICY
# ВАЖНО: Claude Code - основной и единственный провайдер!
# GigaChat - только мануальный выбор

DEFAULT_LLM_PROVIDER = "claude_code"  # НЕ gigachat!

AGENT_CONFIGS = {
    "interviewer": {
        "provider": "claude_code",  # ✅ ОСНОВНОЙ
        "model": "claude-sonnet-4.5",
        "temperature": 0.6,
        "max_tokens": 2000
    },
    "auditor": {
        "provider": "claude_code",  # ✅ ОСНОВНОЙ
        "model": "claude-sonnet-4.5",
        "temperature": 0.3,
        "max_tokens": 2500
    },
    "researcher": {
        "provider": "claude_code",  # ✅ ОСНОВНОЙ (для LLM)
        "websearch_provider": "perplexity",  # Для WebSearch
        "model": "claude-sonnet-4.5",
        "temperature": 0.6,
        "max_tokens": 16000
    },
    "writer": {
        "provider": "claude_code",  # ✅ ОСНОВНОЙ (НЕ gigachat!)
        "model": "claude-sonnet-4.5",
        "temperature": 0.7,
        "max_tokens": 16000
    },
    "reviewer": {
        "provider": "claude_code",  # ✅ ОСНОВНОЙ
        "model": "claude-sonnet-4.5",
        "temperature": 0.5,
        "max_tokens": 8000
    }
}

# GigaChat - только для мануального выбора
GIGACHAT_CONFIG = {
    "provider": "gigachat",
    "model": "GigaChat-Pro",
    "temperature": 0.6,
    "max_tokens": 8000,
    "note": "Используется только при явном выборе пользователя"
}
```

---

## 🧪 Тестирование

### Проверка конфигурации:

```python
def test_llm_provider_is_claude_code():
    """Тест: все агенты используют Claude Code по умолчанию"""

    from shared.llm.config import AGENT_CONFIGS

    for agent_name, config in AGENT_CONFIGS.items():
        assert config['provider'] == 'claude_code', \
            f"Agent {agent_name} должен использовать claude_code, а не {config['provider']}"

    print("✅ Все агенты используют Claude Code")

def test_no_automatic_gigachat_fallback():
    """Тест: нет автоматического fallback на GigaChat"""

    # Проверяем что при ошибке Claude Code не переключаемся на GigaChat
    agent = InteractiveInterviewerAgent(db=db, llm_provider="claude_code")

    # Симулируем ошибку Claude Code
    with patch('llm.UnifiedLLMClient.generate_async', side_effect=Exception("Claude unavailable")):
        result = await agent.conduct_interview()

        # Должна быть ошибка, а НЕ успех через fallback на GigaChat
        assert result['status'] == 'error', \
            "При недоступности Claude Code должна быть ошибка, а не fallback на GigaChat"

    print("✅ Нет автоматического fallback на GigaChat")
```

---

## 📊 Примеры правильного использования

### Адаптивный интервьюер:

```python
# ✅ ПРАВИЛЬНО
interviewer = AdaptiveInterviewerWithQuestionBank(
    llm_client=UnifiedLLMClient(provider="claude_code"),
    llm_provider="claude_code"
)

# ❌ НЕПРАВИЛЬНО
interviewer = AdaptiveInterviewerWithQuestionBank(
    llm_client=UnifiedLLMClient(provider="gigachat"),  # НЕТ!
    llm_provider="gigachat"  # НЕТ!
)
```

### Telegram Bot handlers:

```python
# ✅ ПРАВИЛЬНО
async def start_interview(update: Update, context: CallbackContext):
    agent = InteractiveInterviewerAgent(
        db=db,
        llm_provider="claude_code"  # ✅ Claude Code!
    )

    result = await agent.conduct_interview_with_audit(user_data)
    # ...

# ❌ НЕПРАВИЛЬНО
async def start_interview(update: Update, context: CallbackContext):
    agent = InteractiveInterviewerAgent(
        db=db,
        llm_provider="gigachat"  # ❌ НЕТ! Только Claude Code!
    )
```

### Дорожные карты и документация:

```markdown
<!-- ✅ ПРАВИЛЬНО -->
## LLM Provider
- **Основной:** Claude Code (claude-sonnet-4.5)
- **Мануальный выбор:** GigaChat (только если пользователь выбрал)

<!-- ❌ НЕПРАВИЛЬНО -->
## LLM Provider
- **Основной:** GigaChat  <!-- НЕТ! -->
- **Fallback:** Claude Code  <!-- НЕТ! -->
```

---

## 🔍 Почему Claude Code, а не GigaChat?

### Технические причины:

1. **API доступность** - Claude Code API более стабилен
2. **Качество ответов** - лучше понимает контекст и генерирует адаптивные вопросы
3. **Token limits** - Claude Code: 16k tokens, GigaChat: 8k tokens
4. **Скорость** - Claude Code быстрее отвечает
5. **Поддержка JSON** - Claude Code лучше генерирует валидный JSON

### Бизнес причины:

1. **Основная интеграция** - Claude Code - наш основной провайдер
2. **Стоимость** - уже оплачена подписка Claude Code
3. **Поддержка** - есть техническая поддержка от Anthropic

---

## ✅ Чеклист проверки кода

Перед коммитом проверь:

- [ ] Все `llm_provider` параметры по умолчанию = `"claude_code"`
- [ ] Нет автоматического fallback на GigaChat
- [ ] В документации упоминается Claude Code как основной
- [ ] В примерах кода используется `"claude_code"`
- [ ] Error handling возвращает ошибку, а не переключается на GigaChat
- [ ] Конфиг файлы (config.py) имеют `provider: "claude_code"`

---

**ИТОГО:**
```
Claude Code = ОСНОВНОЙ и ЕДИНСТВЕННЫЙ
GigaChat = МАНУАЛЬНЫЙ ВЫБОР
Fallback = НЕТ (ошибка вместо fallback)
```

---

**Создано:** 2025-10-22
**Автор:** Project Orchestrator
**Статус:** ✅ КРИТИЧЕСКАЯ ПОЛИТИКА - ОБЯЗАТЕЛЬНА К ИСПОЛНЕНИЮ
