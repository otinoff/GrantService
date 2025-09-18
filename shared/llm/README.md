# UnifiedLLMClient для GrantService

## 📋 Описание

UnifiedLLMClient - это унифицированный клиент для работы с различными LLM провайдерами, скопированный из рабочего проекта `review_generator` и адаптированный для GrantService.

## 🚀 Возможности

- **Множественные провайдеры**: GigaChat, Perplexity, Ollama
- **Асинхронная работа**: Полная поддержка async/await
- **Retry логика**: Автоматические повторы при ошибках
- **Rate limiting**: Обработка ограничений API
- **Токен-менеджмент**: Автоматическое обновление токенов GigaChat
- **Очистка текста**: Удаление markdown разметки

## 🔧 Установка

### Зависимости

```bash
pip install aiohttp
```

### Структура файлов

```
GrantService/shared/llm/
├── __init__.py
├── config.py              # Конфигурация с рабочими API ключами
├── unified_llm_client.py  # Основной клиент
└── README.md              # Этот файл
```

## 📖 Использование

### Базовое использование

```python
import asyncio
from shared.llm.unified_llm_client import UnifiedLLMClient

async def main():
    # GigaChat
    async with UnifiedLLMClient(
        provider="gigachat",
        model="GigaChat",
        temperature=0.7
    ) as client:
        result = await client.generate_text("Привет!", max_tokens=100)
        print(result)
    
    # Perplexity
    async with UnifiedLLMClient(
        provider="perplexity",
        model="sonar",
        temperature=0.3
    ) as client:
        result = await client.generate_text("Что такое грант?", max_tokens=150)
        print(result)

asyncio.run(main())
```

### Использование в агентах

```python
from shared.llm.config import AGENT_CONFIGS
from shared.llm.unified_llm_client import UnifiedLLMClient

async def researcher_agent(prompt: str):
    config = AGENT_CONFIGS["researcher"]
    
    async with UnifiedLLMClient(
        provider=config["provider"],
        model=config["model"],
        temperature=config["temperature"]
    ) as client:
        return await client.generate_text(prompt, config["max_tokens"])

async def writer_agent(prompt: str):
    config = AGENT_CONFIGS["writer"]
    
    async with UnifiedLLMClient(
        provider=config["provider"],
        model=config["model"],
        temperature=config["temperature"]
    ) as client:
        return await client.generate_text(prompt, config["max_tokens"])
```

### Проверка подключения

```python
async def check_connections():
    providers = ["gigachat", "perplexity", "ollama"]
    
    for provider in providers:
        async with UnifiedLLMClient(provider=provider) as client:
            is_connected = await client.check_connection_async()
            print(f"{provider}: {'✅' if is_connected else '❌'}")
```

## ⚙️ Конфигурация

### API ключи (уже настроены)

```python
# GigaChat (рабочий ключ из review_generator)
GIGACHAT_API_KEY = "OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5Ojk4MmM0NjIyLTU3OWQtNDYxNi04YzVlLWIyMTY3YTZlNzI0NQ=="
GIGACHAT_CLIENT_ID = "967330d4-e5ab-4fca-a8e8-12a7d510d249"

# Perplexity
PERPLEXITY_API_KEY = "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"
```

### Конфигурации агентов

```python
AGENT_CONFIGS = {
    "researcher": {
        "provider": "perplexity",
        "model": "sonar",
        "temperature": 0.3,
        "max_tokens": 1500
    },
    "writer": {
        "provider": "gigachat", 
        "model": "GigaChat",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "auditor": {
        "provider": "gigachat",
        "model": "GigaChat", 
        "temperature": 0.5,
        "max_tokens": 2000
    }
}
```

## 🧪 Тестирование

Запустите тестовый скрипт:

```bash
cd /var/GrantService
python test_unified_llm.py
```

Тест проверит:
- ✅ Подключение к GigaChat
- ✅ Подключение к Perplexity  
- ✅ Подключение к Ollama (если доступен)
- ✅ Генерацию текста
- ✅ Анализ грантовой заявки

## 🔄 Интеграция с CrewAI

Обновленная конфигурация CrewAI (`telegram-bot/config/crewai_config.py`) автоматически использует UnifiedLLMClient:

```python
from shared.llm.unified_llm_client import UnifiedLLMClient

def create_agent_with_gigachat(role: str, goal: str, backstory: str, system_message: str = ""):
    """Создание агента с GigaChat через UnifiedLLMClient"""
    return create_agent_with_unified_llm(role, goal, backstory, system_message, "writer")
```

## 🚨 Обработка ошибок

### Rate Limits

Клиент автоматически обрабатывает rate limits с экспоненциальной задержкой:

```python
# При 429 ошибке автоматически:
# Попытка 1: ждет 1 секунду
# Попытка 2: ждет 2 секунды  
# Попытка 3: ждет 4 секунды
```

### Таймауты

Настроены разумные таймауты:
- **GigaChat**: 60 секунд
- **Perplexity**: 60 секунд
- **Ollama**: 30 секунд

### Fallback

При ошибках клиент возвращает сообщение об ошибке вместо падения:

```python
result = await client.generate_text(prompt)
# Если ошибка: result = "[ОШИБКА: описание ошибки]"
```

## 📊 Мониторинг

Логирование включено по умолчанию:

```
🔧 Инициализирован GIGACHAT клиент с моделью 'GigaChat'
🔐 Получаем токен авторизации для GigaChat...
✅ Токен GigaChat получен успешно
⚠️ Rate limit GigaChat. Попытка 1/3, ждём 1с...
```

## 🔧 Настройка для разработки

### Локальная разработка

```python
# Для локальной разработки можно использовать Ollama
async with UnifiedLLMClient(
    provider="ollama",
    model="qwen2.5:3b",
    base_url="http://localhost:11434"
) as client:
    result = await client.generate_text("Тест")
```

### Отладка

Включите подробное логирование:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## ✅ Готово к использованию

UnifiedLLMClient полностью готов к использованию в GrantService с:
- ✅ Рабочими API ключами
- ✅ Полной совместимостью с CrewAI
- ✅ Обработкой ошибок
- ✅ Асинхронной работой
- ✅ Тестами

**Просто импортируйте и используйте!**
