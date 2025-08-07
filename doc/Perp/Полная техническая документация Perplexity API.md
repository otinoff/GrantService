<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Полная техническая документация Perplexity API

## 1. Эндпоинты и параметры запросов/ответов

### Основные эндпоинты

#### POST `/chat/completions`

**Описание:** Синхронный чат с поиском в реальном времени[^1][^2]
**URL:** `https://api.perplexity.ai/chat/completions`

**Основные параметры запроса:**

- `model` (обязательный) - Имя модели для использования
- `messages` (обязательный) - Массив сообщений беседы
- `search_mode` - Режим поиска: `web` (по умолчанию) или `academic`
- `reasoning_effort` - Уровень вычислительных усилий: `low`, `medium` (по умолчанию), `high` (только для sonar-deep-research)
- `max_tokens` - Максимальное количество токенов в ответе
- `temperature` - Уровень случайности (0-2, по умолчанию 0.2)
- `top_p` - Порог nucleus sampling (по умолчанию 0.9)
- `search_domain_filter` - Массив доменов для фильтрации (до 10 доменов)
- `return_images` - Включать ли изображения в результаты поиска (по умолчанию false)
- `return_related_questions` - Возвращать ли связанные вопросы (по умолчанию false)
- `search_recency_filter` - Фильтр по времени ('week', 'day')
- `search_after_date_filter` - Фильтр контента после даты (формат %m/%d/%Y)
- `search_before_date_filter` - Фильтр контента до даты (формат %m/%d/%Y)
- `last_updated_after_filter` - Фильтр по дате последнего обновления после
- `last_updated_before_filter` - Фильтр по дате последнего обновления до
- `top_k` - Количество токенов для top-k фильтрации (по умолчанию 0)
- `stream` - Потоковая передача ответа (по умолчанию false)
- `presence_penalty` - Штраф за присутствие (0-2, по умолчанию 0)
- `frequency_penalty` - Штраф за частоту (0-2, по умолчанию 0)
- `response_format` - Формат структурированного вывода
- `web_search_options` - Конфигурация веб-поиска[^1][^2]

**Структура ответа:**

```json
{
  "id": "string",
  "model": "string", 
  "created": 123,
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 123,
    "total_tokens": 123,
    "search_context_size": "string",
    "citation_tokens": 123,
    "num_search_queries": 123,
    "reasoning_tokens": 123
  },
  "object": "chat.completion",
  "choices": [
    {
      "index": 123,
      "finish_reason": "stop",
      "message": {
        "content": "string",
        "role": "assistant"
      }
    }
  ],
  "search_results": [
    {
      "title": "string",
      "url": "string", 
      "date": "2023-12-25"
    }
  ]
}
```


#### POST `/async/chat/completions`

**Описание:** Создание асинхронного запроса завершения чата[^3]
**URL:** `https://api.perplexity.ai/async/chat/completions`

Принимает те же параметры, что и синхронная версия, но обернутые в объект `request`.

#### GET `/async/chat/completions`

**Описание:** Получение списка асинхронных запросов[^4]
**URL:** `https://api.perplexity.ai/async/chat/completions`

**Параметры запроса:**

- `limit` - Максимальное количество запросов (по умолчанию 20)
- `next_token` - Токен для следующей страницы результатов


#### GET `/async/chat/completions/{request_id}`

**Описание:** Получение результата конкретного асинхронного запроса[^5]
**URL:** `https://api.perplexity.ai/async/chat/completions/{request_id}`

## 2. Полный список моделей с возможностями и лимитами

### Поисковые модели (Search)[^6]

| Модель | Контекст | Цена вход/выход | Описание | Применение |
| :-- | :-- | :-- | :-- | :-- |
| `sonar` | 128K | \$1/\$1 за 1M токенов | Легкая, экономичная поисковая модель | Быстрые факты, новости, простые Q\&A |
| `sonar-pro` | 128K | \$3/\$15 за 1M токенов | Продвинутый поиск с глубоким пониманием | Сложные запросы, анализ конкурентов |

### Модели рассуждений (Reasoning)[^6]

| Модель | Контекст | Цена вход/выход | Описание | Применение |
| :-- | :-- | :-- | :-- | :-- |
| `sonar-reasoning` | 128K | \$1/\$5 за 1M токенов | Быстрые рассуждения с поиском | Логические задачи, математика |
| `sonar-reasoning-pro` | 128K | \$2/\$8 за 1M токенов | Улучшенные рассуждения (DeepSeek-R1 с CoT) | Сложные проблемы, стратегическое планирование |

### Исследовательские модели (Research)[^6]

| Модель | Контекст | Стоимость | Описание | Применение |
| :-- | :-- | :-- | :-- | :-- |
| `sonar-deep-research` | 128K | Вход: \$2/1M<br>Выход: \$8/1M<br>Цитаты: \$2/1M<br>Поиск: \$5/1K запросов<br>Рассуждения: \$3/1M | Экспертные исследования с исчерпывающим поиском | Академические исследования, маркетинговый анализ |

### Дополнительные расходы[^7]

**Плата за запрос (Request fees)** применяется к моделям Sonar, Sonar Pro, Sonar Reasoning, Sonar Reasoning Pro:

- Высокий контекст поиска: \$12 за 1K запросов
- Средний контекст поиска: \$8 за 1K запросов
- Низкий контекст поиска: \$5 за 1K запросов


## 3. Rate Limits для всех тарифов (Tier 0-5)[^8]

### Прогрессия тарифов

| Тариф | Общие потраченные кредиты | Статус |
| :-- | :-- | :-- |
| **Tier 0** | \$0 | Новые аккаунты, ограниченный доступ |
| **Tier 1** | \$50+ | Легкое использование, базовые лимиты |
| **Tier 2** | \$250+ | Регулярное использование |
| **Tier 3** | \$500+ | Интенсивное использование |
| **Tier 4** | \$1,000+ | Продакшн использование |
| **Tier 5** | \$5,000+ | Корпоративное использование |

### Rate Limits по моделям (запросов в минуту)[^8]

| Модель/Эндпоинт | RPM |
| :-- | :-- |
| `sonar-deep-research` | 5 |
| `sonar-reasoning-pro` | 50 |
| `sonar-reasoning` | 50 |
| `sonar-pro` | 50 |
| `sonar` | 50 |
| POST `/async/chat/completions` | 5 |
| GET `/async/chat/completions` | 3000 |
| GET `/async/chat/completions/{request_id}` | 6000 |

**Важно:** Тарифы основаны на совокупных покупках кредитов за всё время, не на текущем балансе. Повышение тарифа происходит автоматически и является постоянным.

## 4. Structured Outputs с примерами JSON схем[^9]

### Поддерживаемые типы структурированного вывода

1. **JSON Schema** - для всех моделей
2. **Regex** - только для модели `sonar`

### Примеры JSON Schema

#### Финансовый анализ

```json
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "schema": {
        "type": "object",
        "properties": {
          "company": {"type": "string"},
          "quarter": {"type": "string"},
          "revenue": {"type": "number"},
          "net_income": {"type": "number"},
          "eps": {"type": "number"},
          "revenue_growth_yoy": {"type": "number"},
          "key_highlights": {
            "type": "array",
            "items": {"type": "string"}
          }
        },
        "required": ["company", "quarter", "revenue", "net_income", "eps"]
      }
    }
  }
}
```


#### Извлечение контактной информации с Regex

```json
{
  "response_format": {
    "type": "regex",
    "regex": {
      "regex": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    }
  }
}
```


### Особенности реализации Perplexity

**Упрощенное определение схемы:**

- Автоматическое именование схем
- Автоматическая валидация
- Упрощенный синтаксис (не требуется поле `name` или `strict`)

**Ограничения:**

- Рекурсивные JSON схемы не поддерживаются
- Неограниченные объекты (`dict[str, Any]`) не поддерживаются

**Для reasoning-моделей:** Ответ включает секцию рассуждений, за которой следует структурированный вывод. Требуется ручная обработка для извлечения JSON.

## 5. Параметры поиска

### Основные параметры поиска

| Параметр | Описание | Формат | Пример |
| :-- | :-- | :-- | :-- |
| `search_mode` | Режим поиска | `web` \| `academic` | `"academic"` |
| `search_domain_filter` | Фильтр доменов (до 10) | Массив строк | `["wikipedia.org", "-example.com"]` |
| `search_recency_filter` | Фильтр по времени | Строка | `"week"`, `"day"` |
| `search_after_date_filter` | Контент после даты | %m/%d/%Y | `"3/1/2025"` |
| `search_before_date_filter` | Контент до даты | %m/%d/%Y | `"3/1/2025"` |
| `last_updated_after_filter` | Обновлено после | %m/%d/%Y | `"3/1/2025"` |
| `last_updated_before_filter` | Обновлено до | %m/%d/%Y | `"3/1/2025"` |
| `return_images` | Включать изображения | Boolean | `true` |
| `return_related_questions` | Связанные вопросы | Boolean | `true` |

### Конфигурация веб-поиска

```json
{
  "web_search_options": {
    "search_context_size": "high" // "low", "medium", "high"
  }
}
```


### Фильтрация доменов

- **Разрешение:** `["wikipedia.org", "docs.python.org"]`
- **Запрет:** `["-spam.com", "-unreliable.net"]`
- **Смешанное:** `["wikipedia.org", "-spam.com"]`


## 6. Коды ошибок и их обработка

### Основные коды ошибок

| Код | Описание | Причина | Решение |
| :-- | :-- | :-- | :-- |
| **400** | Bad Request | Неверные параметры запроса | Проверить синтаксис JSON и обязательные поля |
| **401** | Unauthorized | Неверный API ключ | Проверить заголовок Authorization |
| **404** | Not Found | Ресурс не найден | Проверить URL эндпоинта или request_id |
| **429** | Too Many Requests | Превышен лимит запросов | Реализовать exponential backoff |
| **500** | Internal Server Error | Ошибка сервера | Повторить запрос позже |

### Статусы асинхронных запросов[^3][^5]

- `CREATED` - Запрос создан
- `IN_PROGRESS` - Обрабатывается
- `COMPLETED` - Завершен успешно
- `FAILED` - Завершен с ошибкой


### Рекомендации по обработке ошибок

1. Реализовать retry логику с exponential backoff для 429 ошибок
2. Мониторить текущий тариф для предотвращения превышения лимитов
3. Валидировать параметры перед отправкой запроса
4. Логировать ошибки для анализа паттернов

## 7. Методы аутентификации[^1][^2]

### Bearer Token аутентификация

**Заголовок:** `Authorization: Bearer YOUR_API_KEY`

**Пример:**

```bash
curl -H "Authorization: Bearer pplx-your-api-key-here" \
     -H "Content-Type: application/json" \
     https://api.perplexity.ai/chat/completions
```

**Получение API ключа:**

1. Зарегистрироваться на https://docs.perplexity.ai/
2. Перейти в настройки API
3. Создать новый API ключ
4. Скопировать и безопасно сохранить ключ

**Безопасность:**

- Никогда не передавайте API ключ в URL параметрах
- Храните ключи в переменных окружения
- Регулярно ротируйте ключи
- Не коммитьте ключи в git репозитории


## 8. Примеры кода на Python для всех основных функций

### Базовая настройка

```python
import requests
import json
import os
from typing import Dict, List, Optional

class PerplexityAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
```


### 1. Синхронный чат-запрос

```python
def chat_completion(self, model: str, messages: List[Dict], **kwargs) -> Dict:
    """Синхронный запрос завершения чата"""
    payload = {
        "model": model,
        "messages": messages,
        **kwargs
    }
    
    response = requests.post(
        f"{self.base_url}/chat/completions",
        headers=self.headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

# Пример использования
api = PerplexityAPI(os.getenv("PERPLEXITY_API_KEY"))

result = api.chat_completion(
    model="sonar-pro",
    messages=[
        {"role": "user", "content": "Последние новости об искусственном интеллекте"}
    ],
    search_mode="web",
    return_images=True
)

print(result["choices"][^0]["message"]["content"])
```


### 2. Поиск с фильтрацией доменов

```python
def search_with_domain_filter(self, query: str, domains: List[str], model: str = "sonar") -> Dict:
    """Поиск с фильтрацией по доменам"""
    return self.chat_completion(
        model=model,
        messages=[{"role": "user", "content": query}],
        search_domain_filter=domains,
        web_search_options={"search_context_size": "high"}
    )

# Пример: поиск только по Википедии и научным источникам
result = api.search_with_domain_filter(
    query="Квантовые вычисления",
    domains=["wikipedia.org", "arxiv.org", "nature.com"]
)
```


### 3. Структурированный вывод с JSON Schema

```python
def structured_completion(self, model: str, messages: List[Dict], schema: Dict) -> Dict:
    """Запрос со структурированным выводом"""
    return self.chat_completion(
        model=model,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {"schema": schema}
        }
    )

# Пример: анализ компании
company_schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "market_cap": {"type": "number"},
        "sector": {"type": "string"},
        "key_metrics": {
            "type": "object",
            "properties": {
                "revenue": {"type": "number"},
                "profit_margin": {"type": "number"}
            }
        }
    },
    "required": ["company_name", "market_cap", "sector"]
}

result = api.structured_completion(
    model="sonar-pro",
    messages=[{"role": "user", "content": "Анализ Apple Inc"}],
    schema=company_schema
)
```


### 4. Асинхронные запросы

```python
def create_async_completion(self, model: str, messages: List[Dict], **kwargs) -> str:
    """Создание асинхронного запроса"""
    payload = {
        "request": {
            "model": model,
            "messages": messages,
            **kwargs
        }
    }
    
    response = requests.post(
        f"{self.base_url}/async/chat/completions",
        headers=self.headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["id"]
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

def get_async_result(self, request_id: str) -> Dict:
    """Получение результата асинхронного запроса"""
    response = requests.get(
        f"{self.base_url}/async/chat/completions/{request_id}",
        headers=self.headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

def wait_for_async_completion(self, request_id: str, max_wait: int = 300) -> Dict:
    """Ожидание завершения асинхронного запроса"""
    import time
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        result = self.get_async_result(request_id)
        
        if result["status"] == "COMPLETED":
            return result["response"]
        elif result["status"] == "FAILED":
            raise Exception(f"Async request failed: {result.get('error_message')}")
        
        time.sleep(5)  # Ждем 5 секунд перед следующей проверкой
    
    raise TimeoutError("Async request timed out")

# Пример использования
request_id = api.create_async_completion(
    model="sonar-deep-research",
    messages=[{"role": "user", "content": "Подробный анализ рынка электромобилей"}],
    reasoning_effort="high"
)

result = api.wait_for_async_completion(request_id)
print(result["choices"][^0]["message"]["content"])
```


### 5. Работа с изображениями

```python
def analyze_image_with_context(self, image_url: str, query: str, model: str = "sonar-pro") -> Dict:
    """Анализ изображения с веб-контекстом"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]
    
    return self.chat_completion(
        model=model,
        messages=messages,
        return_images=True
    )

# Пример
result = api.analyze_image_with_context(
    image_url="https://example.com/chart.png",
    query="Проанализируй этот график и найди дополнительную информацию в интернете"
)
```


### 6. Обработка ошибок и retry логика

```python
import time
import random

def robust_completion(self, model: str, messages: List[Dict], max_retries: int = 3, **kwargs) -> Dict:
    """Запрос с retry логикой и обработкой ошибок"""
    for attempt in range(max_retries):
        try:
            return self.chat_completion(model, messages, **kwargs)
        
        except Exception as e:
            if "429" in str(e):  # Rate limit exceeded
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit exceeded. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                raise e
            else:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(1)
    
    raise Exception("Max retries exceeded")
```


### 7. Полный пример интеграции

```python
#!/usr/bin/env python3
"""
Полный пример использования Perplexity API
"""

import os
import json
from typing import Dict, List, Optional
import requests

class PerplexityClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def research_topic(self, topic: str, depth: str = "medium") -> Dict:
        """Комплексное исследование темы"""
        return self.chat_completion(
            model="sonar-deep-research",
            messages=[
                {
                    "role": "system", 
                    "content": "Вы эксперт-исследователь. Предоставьте детальный анализ с источниками."
                },
                {"role": "user", "content": f"Проведи исследование по теме: {topic}"}
            ],
            reasoning_effort=depth,
            search_mode="web",
            return_related_questions=True,
            web_search_options={"search_context_size": "high"}
        )
    
    def academic_search(self, query: str) -> Dict:
        """Поиск по академическим источникам"""
        return self.chat_completion(
            model="sonar-pro",
            messages=[{"role": "user", "content": query}],
            search_mode="academic",
            search_domain_filter=["arxiv.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com"]
        )
    
    def get_latest_news(self, topic: str, days: int = 7) -> Dict:
        """Получение последних новостей"""
        return self.chat_completion(
            model="sonar",
            messages=[{"role": "user", "content": f"Последние новости: {topic}"}],
            search_recency_filter="week" if days <= 7 else "month",
            return_images=True
        )

def main():
    # Инициализация клиента
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("Установите переменную окружения PERPLEXITY_API_KEY")
    
    client = PerplexityClient(api_key)
    
    # Пример 1: Исследование темы
    print("=== Исследование темы ===")
    research = client.research_topic("Влияние ИИ на рынок труда")
    print(research["choices"][^0]["message"]["content"][:500] + "...")
    
    # Пример 2: Академический поиск
    print("\n=== Академический поиск ===")
    academic = client.academic_search("machine learning in healthcare")
    print(f"Найдено источников: {len(academic.get('search_results', []))}")
    
    # Пример 3: Последние новости
    print("\n=== Последние новости ===")
    news = client.get_latest_news("искусственный интеллект")
    print(f"Источники новостей: {len(news.get('search_results', []))}")

if __name__ == "__main__":
    main()
```


### Дополнительные утилиты

```python
def extract_sources(api_response: Dict) -> List[Dict]:
    """Извлечение источников из ответа API"""
    return api_response.get("search_results", [])

def format_response(api_response: Dict) -> str:
    """Форматирование ответа для вывода"""
    content = api_response["choices"][^0]["message"]["content"]
    sources = extract_sources(api_response)
    
    formatted = f"{content}\n\n--- Источники ---\n"
    for i, source in enumerate(sources, 1):
        formatted += f"{i}. {source['title']} - {source['url']}\n"
    
    return formatted

def save_response(api_response: Dict, filename: str):
    """Сохранение ответа в файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(api_response, f, ensure_ascii=False, indent=2)
```

Эта документация охватывает все аспекты работы с Perplexity API - от базовых запросов до сложных интеграций с обработкой ошибок и оптимизацией производительности[^1][^2][^3][^4][^5][^6][^7][^8][^9].

<div style="text-align: center">⁂</div>

[^1]: https://docs.perplexity.ai/api-reference/chat-completions-post

[^2]: https://docs.perplexity.ai/api-reference/async-chat-completions-post

[^3]: https://docs.perplexity.ai/getting-started/models

[^4]: https://docs.perplexity.ai/getting-started/models/models/sonar

[^5]: https://docs.perplexity.ai/guides/rate-limits-usage-tiers

[^6]: https://docs.perplexity.ai/getting-started/pricing

[^7]: https://docs.perplexity.ai/guides/structured-outputs

[^8]: https://docs.perplexity.ai/guides/prompt-guide

[^9]: https://docs.perplexity.ai/faq/faq

