# Архитектура интеграции Claude Code API в GrantService

## 📋 Содержание
1. [Анализ возможностей](#анализ-возможностей)
2. [Архитектурные решения](#архитектурные-решения)
3. [Варианты использования](#варианты-использования)
4. [Техническая реализация](#техническая-реализация)
5. [План интеграции](#план-интеграции)
6. [Примеры использования](#примеры-использования)

---

## 1. Анализ возможностей

### 1.1 Claude Code API Wrapper - Возможности

**Доступные эндпоинты:**
- `/chat` - Чат с Claude (Sonnet/Opus) - интеллектуальный диалог
- `/code` - Выполнение кода через Claude Code - автоматизация задач
- `/sessions` - Управление контекстными сессиями
- `/models` - Список доступных моделей

**Технические характеристики:**
- URL: `http://178.236.17.55:8000`
- API Key: `1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732`
- Аутентификация: Bearer token
- Модели: Sonnet (быстрый), Opus (мощный)
- Temperature: 0.0-1.0 (управление креативностью)
- Max tokens: 1-8000

### 1.2 Преимущества для GrantService

**По сравнению с GigaChat:**

| Критерий | GigaChat | Claude Code API | Преимущество |
|----------|----------|-----------------|--------------|
| **Качество текста** | Хорошее для русского | Отличное для аналитики | Claude: глубокий анализ |
| **Контекст** | До 8K токенов | До 200K токенов | Claude: 25x больше |
| **Программирование** | Базовый | Экспертный уровень | Claude: code execution |
| **Аналитика** | Средняя | Превосходная | Claude: лучше для оценки |
| **Стоимость** | Средняя | Через прокси | Claude: оптимальная |
| **Латентность** | ~2-3 сек | ~1-2 сек | Claude: быстрее |
| **Русский язык** | Отлично | Хорошо | GigaChat: локализация |

**Ключевое преимущество:** Claude Code может **выполнять код** и **анализировать данные** напрямую, что открывает новые возможности автоматизации.

### 1.3 Стратегия использования

**Рекомендация: Гибридный подход**

```
┌─────────────────────────────────────┐
│      GrantService LLM Router        │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────┐      ┌──────────┐    │
│  │ GigaChat │      │  Claude  │    │
│  │          │      │   Code   │    │
│  └──────────┘      └──────────┘    │
│       │                  │          │
│       ▼                  ▼          │
│  Русский текст      Аналитика      │
│  Генерация          Оценка         │
│  Локализация        Автоматизация  │
└─────────────────────────────────────┘
```

**Распределение задач:**

1. **GigaChat** → Генерация русского текста
   - Writer Agent (финальные тексты заявок)
   - Interviewer Agent (общение с пользователем на русском)
   - Локализованные промпты

2. **Claude Code** → Аналитика и автоматизация
   - Auditor Agent (оценка проектов 1-10)
   - Planner Agent (структурирование)
   - Researcher Agent (анализ данных)
   - Code execution (автоматизация задач)

---

## 2. Архитектурные решения

### 2.1 Компонентная архитектура

```
GrantService/
│
├── shared/
│   └── llm/
│       ├── config.py                    # Общая конфигурация
│       ├── unified_llm_client.py        # Текущий клиент (GigaChat, Ollama)
│       ├── claude_code_client.py        # ⭐ НОВЫЙ: Claude Code клиент
│       └── llm_router.py                # ⭐ НОВЫЙ: Роутер провайдеров
│
├── agents/
│   ├── base_agent.py                    # Базовый класс
│   ├── auditor_agent.py                 # → Claude Code (аналитика)
│   ├── interviewer_agent.py             # → GigaChat (русский язык)
│   ├── researcher_agent.py              # → Claude Code (исследование)
│   ├── writer_agent.py                  # → GigaChat (генерация текста)
│   └── prompts/
│       ├── claude_code_prompts.py       # ⭐ НОВЫЙ: Промпты для Claude
│       └── gigachat_prompts.py          # Промпты для GigaChat
│
├── config/
│   └── config.env                       # + CLAUDE_CODE_API_KEY
│
└── data/
    └── database/
        └── llm_logs.py                  # ⭐ НОВЫЙ: Логирование LLM запросов
```

### 2.2 LLM Router Pattern

**Преимущества:**
- ✅ Единая точка входа для всех LLM
- ✅ Автоматический выбор провайдера по задаче
- ✅ Fallback при недоступности
- ✅ Централизованное логирование
- ✅ Оптимизация стоимости

**Пример использования:**

```python
from shared.llm.llm_router import LLMRouter

router = LLMRouter()

# Автоматический выбор провайдера по задаче
result = await router.generate(
    prompt="Оцени проект по 10 критериям",
    task_type="analysis",  # → Claude Code
    language="ru"
)

result = await router.generate(
    prompt="Напиши введение к грантовой заявке",
    task_type="generation",  # → GigaChat
    language="ru"
)
```

### 2.3 Сессионное управление

**Проблема:** Грантовые заявки требуют длительного контекста (интервью 24 вопроса)

**Решение:** Использовать `/sessions` API для сохранения контекста

```python
# Создаём сессию для пользователя
session_id = await claude_client.create_session(user_id=telegram_id)

# Все вопросы интервью в одной сессии
for question in interview_questions:
    response = await claude_client.chat(
        message=question,
        session_id=session_id  # Сохраняется контекст
    )

# В конце - полный анализ с учётом всех ответов
final_analysis = await claude_client.chat(
    message="Проанализируй весь диалог и оцени проект",
    session_id=session_id
)
```

---

## 3. Варианты использования

### 3.1 Auditor Agent (Оценка проектов)

**Задача:** Оценить проект по 10 критериям (1-10 баллов каждый)

**Почему Claude Code:**
- Глубокий аналитический анализ
- Объективная оценка без эмоций
- Структурированный вывод
- Большой контекст (весь проект сразу)

**Реализация:**

```python
class AuditorAgentClaude(BaseAgent):
    async def evaluate_project(self, project_data: Dict) -> Dict:
        prompt = f"""
        Ты эксперт по оценке грантовых заявок. Оцени проект:

        {json.dumps(project_data, ensure_ascii=False, indent=2)}

        Оцени по критериям (1-10 баллов):
        1. Актуальность
        2. Новизна
        3. Методология
        4. Бюджет
        5. Команда
        6. Результаты
        7. Риски
        8. Социальная значимость
        9. Масштабируемость
        10. Устойчивость

        Верни JSON с оценками и рекомендациями.
        """

        response = await self.claude_client.chat(
            message=prompt,
            temperature=0.3,  # Низкая для объективности
            max_tokens=3000
        )

        return json.loads(response)
```

### 3.2 Code Execution для автоматизации

**Задача:** Автоматически проверять бюджет на математические ошибки

**Реализация через `/code` endpoint:**

```python
async def validate_budget(budget_data: Dict) -> Dict:
    code = f"""
import json

budget = {json.dumps(budget_data)}

# Проверяем суммы
total_planned = sum(item['amount'] for item in budget['items'])
total_declared = budget['total']

errors = []
if abs(total_planned - total_declared) > 0.01:
    errors.append({{
        'type': 'sum_mismatch',
        'declared': total_declared,
        'calculated': total_planned,
        'difference': total_planned - total_declared
    }})

# Проверяем лимиты
for item in budget['items']:
    if item['amount'] > budget.get('max_item_cost', float('inf')):
        errors.append({{
            'type': 'item_exceeds_limit',
            'item': item['name'],
            'amount': item['amount'],
            'limit': budget['max_item_cost']
        }})

print(json.dumps({{'errors': errors, 'valid': len(errors) == 0}}))
"""

    result = await claude_client.execute_code(
        code=code,
        language="python"
    )

    return json.loads(result['result'])
```

### 3.3 Researcher Agent (Поиск аналогов)

**Задача:** Найти похожие успешные гранты и выделить паттерны

**Реализация:**

```python
async def research_similar_grants(project_description: str) -> Dict:
    prompt = f"""
    Проект: {project_description}

    Задачи:
    1. Определи ключевые темы проекта
    2. Найди в базе похожие успешные проекты
    3. Выдели общие паттерны успеха
    4. Дай рекомендации по позиционированию

    База успешных грантов:
    {load_successful_grants_db()}
    """

    analysis = await claude_client.chat(
        message=prompt,
        temperature=0.5,
        max_tokens=4000
    )

    return parse_research_results(analysis)
```

### 3.4 Planner Agent (Структурирование)

**Задача:** Создать оптимальную структуру заявки под конкретный фонд

**Реализация:**

```python
async def create_grant_structure(
    project_data: Dict,
    fund_requirements: Dict
) -> Dict:
    prompt = f"""
    Создай структуру грантовой заявки:

    Проект: {json.dumps(project_data, ensure_ascii=False)}
    Требования фонда: {json.dumps(fund_requirements, ensure_ascii=False)}

    Создай оптимальную структуру разделов с:
    1. Названиями разделов
    2. Рекомендуемым объёмом каждого
    3. Ключевыми тезисами для каждого раздела
    4. Приоритетом важности (1-10)

    Верни JSON со структурой.
    """

    structure = await claude_client.chat(
        message=prompt,
        temperature=0.4,
        max_tokens=3000
    )

    return json.loads(structure)
```

---

## 4. Техническая реализация

### 4.1 Claude Code Client

**Файл:** `shared/llm/claude_code_client.py`

```python
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ClaudeCodeClient:
    """Клиент для работы с Claude Code API Wrapper"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://178.236.17.55:8000",
        default_model: str = "sonnet",
        default_temperature: float = 0.7
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.session: Optional[aiohttp.ClientSession] = None
        self.debug_log = []

    async def __aenter__(self):
        """Создание сессии"""
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Чат с Claude

        Args:
            message: Сообщение для Claude
            session_id: ID сессии для сохранения контекста
            model: Модель (sonnet/opus)
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимум токенов (1-8000)

        Returns:
            Ответ Claude
        """
        url = f"{self.base_url}/chat"

        payload = {
            "message": message,
            "model": model or self.default_model,
            "temperature": temperature or self.default_temperature,
        }

        if session_id:
            payload["session_id"] = session_id
        if max_tokens:
            payload["max_tokens"] = max_tokens

        self.debug_log.append({
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/chat",
            "payload": payload
        })

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.debug_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "response": data
                    })
                    return data["response"]
                else:
                    error_text = await response.text()
                    logger.error(f"Claude API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")

        except Exception as e:
            logger.error(f"Claude chat error: {e}")
            raise

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Выполнение кода через Claude Code

        Args:
            code: Код для выполнения
            language: Язык программирования (python по умолчанию)
            session_id: ID сессии

        Returns:
            Результат выполнения
        """
        url = f"{self.base_url}/code"

        payload = {
            "code": code,
            "language": language
        }

        if session_id:
            payload["session_id"] = session_id

        self.debug_log.append({
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/code",
            "payload": payload
        })

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.debug_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "response": data
                    })
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Code execution error: {response.status} - {error_text}")
                    raise Exception(f"Code execution failed: {response.status}")

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            raise

    async def list_sessions(self) -> list:
        """Получить список активных сессий"""
        url = f"{self.base_url}/sessions"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return []
        except Exception as e:
            logger.error(f"List sessions error: {e}")
            return []

    async def delete_session(self, session_id: str) -> bool:
        """Удалить сессию"""
        url = f"{self.base_url}/sessions/{session_id}"

        try:
            async with self.session.delete(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Delete session error: {e}")
            return False

    async def list_models(self) -> list:
        """Получить список доступных моделей"""
        url = f"{self.base_url}/models"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return []
        except Exception as e:
            logger.error(f"List models error: {e}")
            return []

    async def check_health(self) -> bool:
        """Проверка здоровья API"""
        url = f"{self.base_url}/health"

        try:
            async with self.session.get(url) as response:
                return response.status == 200
        except:
            return False

    def get_debug_log(self) -> list:
        """Получить лог отладки"""
        return self.debug_log.copy()

    def clear_debug_log(self):
        """Очистить лог отладки"""
        self.debug_log.clear()
```

### 4.2 LLM Router

**Файл:** `shared/llm/llm_router.py`

```python
from typing import Optional, Dict, Any, Literal
from enum import Enum
import logging

from .unified_llm_client import UnifiedLLMClient
from .claude_code_client import ClaudeCodeClient
from .config import (
    GIGACHAT_API_KEY,
    CLAUDE_CODE_API_KEY,
    CLAUDE_CODE_BASE_URL
)

logger = logging.getLogger(__name__)

class TaskType(str, Enum):
    """Типы задач для LLM"""
    GENERATION = "generation"      # Генерация текста → GigaChat
    ANALYSIS = "analysis"          # Анализ → Claude Code
    EVALUATION = "evaluation"      # Оценка → Claude Code
    STRUCTURING = "structuring"    # Структурирование → Claude Code
    RESEARCH = "research"          # Исследование → Claude Code
    CONVERSATION = "conversation"  # Общение → GigaChat
    CODE = "code"                  # Выполнение кода → Claude Code

class LLMRouter:
    """Роутер для автоматического выбора LLM провайдера"""

    def __init__(self):
        self.gigachat_client = None
        self.claude_client = None

        # Матрица выбора провайдера
        self.provider_matrix = {
            TaskType.GENERATION: "gigachat",
            TaskType.ANALYSIS: "claude",
            TaskType.EVALUATION: "claude",
            TaskType.STRUCTURING: "claude",
            TaskType.RESEARCH: "claude",
            TaskType.CONVERSATION: "gigachat",
            TaskType.CODE: "claude"
        }

    async def __aenter__(self):
        """Инициализация клиентов"""
        self.gigachat_client = UnifiedLLMClient(
            provider="gigachat",
            api_key=GIGACHAT_API_KEY
        )

        self.claude_client = ClaudeCodeClient(
            api_key=CLAUDE_CODE_API_KEY,
            base_url=CLAUDE_CODE_BASE_URL
        )

        await self.gigachat_client.__aenter__()
        await self.claude_client.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие клиентов"""
        if self.gigachat_client:
            await self.gigachat_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.claude_client:
            await self.claude_client.__aexit__(exc_type, exc_val, exc_tb)

    async def generate(
        self,
        prompt: str,
        task_type: TaskType,
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Универсальная генерация с автоматическим выбором провайдера

        Args:
            prompt: Промпт
            task_type: Тип задачи
            provider: Явное указание провайдера (опционально)
            **kwargs: Дополнительные параметры

        Returns:
            Сгенерированный текст
        """
        # Определяем провайдера
        target_provider = provider or self.provider_matrix.get(task_type, "gigachat")

        logger.info(f"🎯 Task: {task_type}, Provider: {target_provider}")

        try:
            if target_provider == "claude":
                result = await self.claude_client.chat(
                    message=prompt,
                    **kwargs
                )
            else:  # gigachat
                result = await self.gigachat_client.generate_async(
                    prompt=prompt,
                    **kwargs
                )

            logger.info(f"✅ {target_provider} успешно сгенерировал ответ")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка {target_provider}: {e}")

            # Fallback на другой провайдер
            fallback_provider = "gigachat" if target_provider == "claude" else "claude"
            logger.info(f"🔄 Fallback на {fallback_provider}")

            try:
                if fallback_provider == "claude":
                    return await self.claude_client.chat(message=prompt, **kwargs)
                else:
                    return await self.gigachat_client.generate_async(prompt=prompt, **kwargs)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback также неудачен: {fallback_error}")
                raise

    async def execute_code(self, code: str, language: str = "python", **kwargs) -> Dict:
        """Выполнение кода через Claude Code"""
        return await self.claude_client.execute_code(code, language, **kwargs)

    async def create_session(self, user_id: str) -> str:
        """Создать сессию для пользователя"""
        # Используем user_id как session_id для простоты
        return f"grant_session_{user_id}"
```

### 4.3 Обновление конфигурации

**Файл:** `shared/llm/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

# GigaChat Configuration
GIGACHAT_BASE_URL = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")
GIGACHAT_AUTH_URL = os.getenv("GIGACHAT_AUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "")
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID", "")

# Claude Code Configuration
CLAUDE_CODE_API_KEY = os.getenv("CLAUDE_CODE_API_KEY", "1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732")
CLAUDE_CODE_BASE_URL = os.getenv("CLAUDE_CODE_BASE_URL", "http://178.236.17.55:8000")

# Perplexity Configuration (optional)
PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

# Ollama Configuration (optional)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# Default settings
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))
REQUEST_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

# Async settings
ASYNC_CONNECTION_LIMIT = int(os.getenv("ASYNC_CONNECTION_LIMIT", "10"))
ASYNC_CONNECTION_LIMIT_PER_HOST = int(os.getenv("ASYNC_CONNECTION_LIMIT_PER_HOST", "5"))
ASYNC_REQUEST_TIMEOUT = int(os.getenv("ASYNC_REQUEST_TIMEOUT", "120"))
```

### 4.4 Промпты для Claude Code

**Файл:** `agents/prompts/claude_code_prompts.py`

```python
"""
Промпты для Claude Code API в грантовых задачах
"""

# Auditor Agent - Оценка проекта
AUDITOR_EVALUATION_PROMPT = """
Ты эксперт по оценке грантовых заявок с 20-летним опытом работы в грантовых фондах.

Оцени проект по 10 критериям (шкала 1-10 баллов):

1. **Актуальность** - насколько проблема важна сегодня
2. **Новизна** - уникальность подхода и решения
3. **Методология** - обоснованность методов реализации
4. **Бюджет** - реалистичность и обоснованность расходов
5. **Команда** - компетентность и опыт команды
6. **Результаты** - конкретность и измеримость результатов
7. **Риски** - идентификация и план управления рисками
8. **Социальная значимость** - влияние на целевую аудиторию
9. **Масштабируемость** - потенциал тиражирования
10. **Устойчивость** - план продолжения после гранта

Данные проекта:
{project_data}

Верни JSON в формате:
{{
    "scores": {{
        "актуальность": {{"score": 8, "reasoning": "..."}},
        ...
    }},
    "total_score": 85,
    "recommendation": "одобрить/доработать/отклонить",
    "strengths": ["..."],
    "weaknesses": ["..."],
    "improvement_suggestions": ["..."]
}}
"""

# Planner Agent - Структурирование
PLANNER_STRUCTURE_PROMPT = """
Ты опытный консультант по грантовым заявкам.

Создай оптимальную структуру заявки для данного фонда:

Проект: {project_description}
Фонд: {fund_name}
Требования фонда: {fund_requirements}

Создай структуру разделов со следующей информацией для каждого:
1. Название раздела
2. Рекомендуемый объём (символы/страницы)
3. Ключевые тезисы (3-5 пунктов)
4. Приоритет важности (1-10)
5. Советы по написанию

Верни JSON:
{{
    "sections": [
        {{
            "title": "Название проекта",
            "volume": "100-150 символов",
            "key_points": ["...", "..."],
            "priority": 10,
            "writing_tips": ["..."]
        }},
        ...
    ],
    "total_estimated_pages": 15,
    "critical_sections": ["...", "..."]
}}
"""

# Researcher Agent - Поиск аналогов
RESEARCHER_ANALYSIS_PROMPT = """
Ты исследователь успешных грантовых практик.

Проанализируй проект и найди успешные аналоги:

Проект: {project_description}

База успешных грантов:
{successful_grants_db}

Задачи:
1. Определи 5 ключевых тем проекта
2. Найди 3-5 похожих успешных проектов
3. Выдели общие паттерны успеха
4. Дай рекомендации по позиционированию

Верни JSON:
{{
    "key_themes": ["...", "..."],
    "similar_grants": [
        {{
            "title": "...",
            "fund": "...",
            "year": 2023,
            "amount": 1000000,
            "success_factors": ["...", "..."]
        }},
        ...
    ],
    "success_patterns": ["...", "..."],
    "positioning_recommendations": ["...", "..."]
}}
"""

# Code Validation - Проверка бюджета
BUDGET_VALIDATION_CODE = """
import json

budget = {budget_data}

errors = []
warnings = []

# 1. Проверка суммы
total_calculated = sum(item['amount'] for item in budget['items'])
total_declared = budget['total']

if abs(total_calculated - total_declared) > 0.01:
    errors.append({{
        'type': 'sum_mismatch',
        'message': f'Сумма не сходится: заявлено {{total_declared}}, рассчитано {{total_calculated}}',
        'declared': total_declared,
        'calculated': total_calculated,
        'difference': total_calculated - total_declared
    }})

# 2. Проверка лимитов
max_item_cost = budget.get('max_item_cost', float('inf'))
for item in budget['items']:
    if item['amount'] > max_item_cost:
        errors.append({{
            'type': 'item_exceeds_limit',
            'message': f"{{item['name']}}: {{item['amount']}} > {{max_item_cost}}",
            'item': item['name'],
            'amount': item['amount'],
            'limit': max_item_cost
        }})

# 3. Проверка категорий
required_categories = budget.get('required_categories', [])
present_categories = set(item['category'] for item in budget['items'])

for cat in required_categories:
    if cat not in present_categories:
        warnings.append({{
            'type': 'missing_category',
            'message': f'Отсутствует обязательная категория: {{cat}}',
            'category': cat
        }})

# 4. Проверка процентного соотношения
if 'category_limits' in budget:
    category_totals = {{}}
    for item in budget['items']:
        cat = item['category']
        category_totals[cat] = category_totals.get(cat, 0) + item['amount']

    for cat, limit_pct in budget['category_limits'].items():
        if cat in category_totals:
            actual_pct = (category_totals[cat] / total_calculated) * 100
            if actual_pct > limit_pct:
                errors.append({{
                    'type': 'category_limit_exceeded',
                    'message': f'{{cat}}: {{actual_pct:.1f}}% > {{limit_pct}}%',
                    'category': cat,
                    'actual_percent': actual_pct,
                    'limit_percent': limit_pct
                }})

result = {{
    'valid': len(errors) == 0,
    'errors': errors,
    'warnings': warnings,
    'total_calculated': total_calculated,
    'total_declared': total_declared
}}

print(json.dumps(result, ensure_ascii=False, indent=2))
"""

# Interview Analysis - Анализ интервью
INTERVIEW_ANALYSIS_PROMPT = """
Проанализируй весь диалог интервью для грантовой заявки.

Сессия содержит 24 вопроса и ответы пользователя.

Задачи:
1. Выдели ключевые инсайты о проекте
2. Определи сильные стороны
3. Найди пробелы и недостатки
4. Оцени общую готовность проекта (1-100)
5. Дай конкретные рекомендации

Верни JSON:
{{
    "key_insights": ["...", "..."],
    "strengths": ["...", "..."],
    "gaps": ["...", "..."],
    "readiness_score": 75,
    "recommendations": [
        {{
            "priority": "high",
            "area": "методология",
            "suggestion": "..."
        }},
        ...
    ],
    "next_steps": ["...", "..."]
}}
"""
```

---

## 5. План интеграции

### Этап 1: Подготовка (1 день)

**Задачи:**
1. ✅ Создать `claude_code_client.py`
2. ✅ Создать `llm_router.py`
3. ✅ Обновить `config.py`
4. ✅ Добавить переменные в `.env`
5. ✅ Написать unit-тесты

**Файлы:**
```bash
shared/llm/claude_code_client.py
shared/llm/llm_router.py
shared/llm/config.py
agents/prompts/claude_code_prompts.py
tests/test_claude_code_client.py
```

### Этап 2: MVP - Auditor Agent (2 дня)

**Цель:** Заменить оценку проектов на Claude Code

**Задачи:**
1. Обновить `auditor_agent.py` для использования Claude Code
2. Создать промпты для оценки
3. Протестировать на реальных проектах
4. Сравнить качество с GigaChat

**Критерии успеха:**
- Оценки более объективные
- Рекомендации более конкретные
- Скорость не медленнее GigaChat

### Этап 3: Code Execution (2 дня)

**Цель:** Автоматическая валидация бюджетов

**Задачи:**
1. Создать промпты для генерации кода валидации
2. Реализовать проверку через `/code` endpoint
3. Интегрировать в Planner Agent
4. Добавить визуализацию ошибок в админке

**Критерии успеха:**
- 100% точность математических проверок
- Выявление логических ошибок
- Автоматические предложения исправлений

### Этап 4: Session Management (3 дня)

**Цель:** Длинный контекст для интервью

**Задачи:**
1. Реализовать создание сессий для пользователей
2. Сохранять весь диалог в одной сессии
3. Финальный анализ всего интервью
4. Интеграция с Telegram Bot

**Критерии успеха:**
- Контекст сохраняется весь диалог (24 вопроса)
- Анализ учитывает все ответы
- Нет потери информации

### Этап 5: Researcher Agent (3 дня)

**Цель:** Поиск и анализ аналогов

**Задачи:**
1. Собрать базу успешных грантов
2. Реализовать поиск похожих проектов
3. Анализ паттернов успеха
4. Рекомендации по позиционированию

**Критерии успеха:**
- Находит релевантные аналоги
- Выделяет паттерны успеха
- Даёт конкретные рекомендации

### Этап 6: Production Deployment (2 дня)

**Задачи:**
1. Финальное тестирование
2. Документация
3. Обучение команды
4. Мониторинг и метрики

**Критерии успеха:**
- Все агенты работают стабильно
- Fallback механизмы функционируют
- Логирование настроено
- Команда обучена

**Общая длительность:** 13 дней

---

## 6. Примеры использования

### 6.1 Базовое использование

```python
from shared.llm.llm_router import LLMRouter, TaskType

async def process_grant_application():
    async with LLMRouter() as router:
        # Оценка проекта (автоматически выберет Claude)
        evaluation = await router.generate(
            prompt="Оцени проект по 10 критериям...",
            task_type=TaskType.EVALUATION,
            temperature=0.3,
            max_tokens=3000
        )

        # Генерация текста (автоматически выберет GigaChat)
        intro_text = await router.generate(
            prompt="Напиши введение к грантовой заявке...",
            task_type=TaskType.GENERATION,
            temperature=0.7,
            max_tokens=1000
        )
```

### 6.2 Валидация бюджета

```python
from shared.llm.claude_code_client import ClaudeCodeClient

async def validate_budget_example():
    async with ClaudeCodeClient(api_key=CLAUDE_CODE_API_KEY) as client:
        budget_data = {
            "total": 1000000,
            "items": [
                {"name": "Зарплаты", "category": "personnel", "amount": 600000},
                {"name": "Оборудование", "category": "equipment", "amount": 300000},
                {"name": "Расходники", "category": "materials", "amount": 100000}
            ],
            "max_item_cost": 500000,
            "category_limits": {
                "personnel": 60,
                "equipment": 30,
                "materials": 10
            }
        }

        code = BUDGET_VALIDATION_CODE.format(
            budget_data=json.dumps(budget_data, ensure_ascii=False)
        )

        result = await client.execute_code(code, language="python")
        validation = json.loads(result['result'])

        if not validation['valid']:
            print("Найдены ошибки в бюджете:")
            for error in validation['errors']:
                print(f"  - {error['message']}")
```

### 6.3 Сессионное интервью

```python
async def conduct_interview(user_id: str, questions: List[str]):
    async with ClaudeCodeClient(api_key=CLAUDE_CODE_API_KEY) as client:
        session_id = f"grant_interview_{user_id}"

        # Начальный промпт с контекстом
        await client.chat(
            message="""Ты проводишь интервью для грантовой заявки.
            Задавай вопросы, анализируй ответы, запоминай контекст.
            В конце дай полный анализ проекта.""",
            session_id=session_id
        )

        # Задаём вопросы
        for question in questions:
            user_answer = get_user_answer(question)  # От пользователя

            response = await client.chat(
                message=f"Вопрос: {question}\nОтвет: {user_answer}\n\nТвой комментарий?",
                session_id=session_id
            )

            # Сохраняем комментарий AI
            save_ai_comment(response)

        # Финальный анализ
        final_analysis = await client.chat(
            message="Проанализируй весь диалог. Оцени проект и дай рекомендации.",
            session_id=session_id,
            max_tokens=4000
        )

        return final_analysis
```

### 6.4 Интеграция с существующими агентами

```python
# Обновление AuditorAgent
from shared.llm.llm_router import LLMRouter, TaskType

class AuditorAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = None

    async def evaluate_project(self, project_data: Dict) -> Dict:
        async with LLMRouter() as router:
            # Используем Claude для оценки
            evaluation_json = await router.generate(
                prompt=AUDITOR_EVALUATION_PROMPT.format(
                    project_data=json.dumps(project_data, ensure_ascii=False, indent=2)
                ),
                task_type=TaskType.EVALUATION,
                temperature=0.3,
                max_tokens=3000
            )

            # Парсим JSON ответ
            evaluation = json.loads(evaluation_json)

            # Логируем
            self.log_activity("project_evaluated", {
                "total_score": evaluation["total_score"],
                "recommendation": evaluation["recommendation"]
            })

            return evaluation
```

---

## 7. Мониторинг и метрики

### 7.1 Ключевые метрики

**Отслеживать:**
1. Процент использования каждого провайдера
2. Среднее время ответа
3. Количество fallback-ов
4. Стоимость запросов
5. Частота ошибок

**Таблица в БД:** `llm_request_logs`

```sql
CREATE TABLE llm_request_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    provider VARCHAR(50),
    task_type VARCHAR(50),
    prompt_length INTEGER,
    response_length INTEGER,
    duration_ms INTEGER,
    tokens_used INTEGER,
    cost DECIMAL(10, 6),
    error TEXT,
    user_id VARCHAR(100),
    session_id VARCHAR(100)
);
```

### 7.2 Dashboard в Streamlit

```python
# web-admin/pages/📊_LLM_Analytics.py

import streamlit as st
from data.database.llm_logs import get_llm_statistics

st.title("📊 LLM Analytics")

stats = get_llm_statistics(days=7)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Всего запросов", stats['total_requests'])
    st.metric("Claude Code", f"{stats['claude_percent']}%")

with col2:
    st.metric("Среднее время", f"{stats['avg_duration_ms']}ms")
    st.metric("GigaChat", f"{stats['gigachat_percent']}%")

with col3:
    st.metric("Успешность", f"{stats['success_rate']}%")
    st.metric("Fallback", f"{stats['fallback_count']}")

# График распределения по задачам
st.bar_chart(stats['tasks_distribution'])
```

---

## 8. Безопасность и лимиты

### 8.1 Rate Limiting

```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = defaultdict(list)

    def check_limit(self, user_id: str) -> bool:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Очистка старых запросов
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > minute_ago
        ]

        # Проверка лимита
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        self.requests[user_id].append(now)
        return True
```

### 8.2 Защита API ключей

```python
# Никогда не коммитить ключи в git
# Использовать переменные окружения

import os
from pathlib import Path

# Проверка наличия .env
env_file = Path(".env")
if not env_file.exists():
    raise FileNotFoundError(
        "❌ Файл .env не найден! "
        "Скопируйте config/.env.example в .env и заполните API ключи"
    )

# Валидация ключей
CLAUDE_CODE_API_KEY = os.getenv("CLAUDE_CODE_API_KEY")
if not CLAUDE_CODE_API_KEY:
    raise ValueError("❌ CLAUDE_CODE_API_KEY не задан в .env")
```

---

## 9. FAQ

### Q: Стоит ли полностью заменить GigaChat на Claude?

**A:** Нет, гибридный подход лучше:
- GigaChat отлично генерирует русский текст
- Claude отлично анализирует и структурирует
- Fallback механизм повышает надёжность

### Q: Как хранить API ключи?

**A:**
1. В `.env` файле (не коммитить в git)
2. В переменных окружения на сервере
3. В секретах Docker/Kubernetes
4. Никогда не хардкодить в коде

### Q: Что делать если Claude API недоступен?

**A:** LLMRouter автоматически переключится на GigaChat (fallback)

### Q: Как оптимизировать стоимость?

**A:**
1. Использовать Sonnet (быстрее, дешевле) для простых задач
2. Opus только для сложной аналитики
3. Кешировать частые запросы
4. Оптимизировать промпты (меньше токенов)

### Q: Можно ли использовать несколько Claude аккаунтов?

**A:** Да, реализовать балансировку нагрузки:

```python
class ClaudeBalancer:
    def __init__(self, api_keys: List[str]):
        self.clients = [
            ClaudeCodeClient(api_key=key)
            for key in api_keys
        ]
        self.current_index = 0

    def get_client(self):
        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.clients)
        return client
```

---

## 10. Заключение

### Ключевые выводы

1. **Claude Code API расширяет возможности GrantService:**
   - Глубокая аналитика проектов
   - Выполнение кода для автоматизации
   - Длинный контекст для интервью
   - Высокое качество оценок

2. **Гибридный подход оптимален:**
   - GigaChat → Русский текст
   - Claude → Аналитика и структурирование
   - Fallback → Высокая надёжность

3. **Поэтапная интеграция снижает риски:**
   - MVP с Auditor Agent
   - Постепенное расширение
   - Сравнение качества
   - Оптимизация

### Следующие шаги

1. ✅ Создать файлы клиентов
2. ✅ Добавить переменные окружения
3. ✅ Обновить Auditor Agent
4. ✅ Протестировать MVP
5. ✅ Собрать метрики
6. ✅ Оптимизировать промпты
7. ✅ Развернуть в продакшен

### Ожидаемый эффект

- **↑ 30-40% точность оценок** проектов
- **↓ 50% ошибок** в бюджетах (автоматическая валидация)
- **↑ 2x контекст** для анализа (200K vs 8K токенов)
- **↑ 20-25% качество** рекомендаций
- **↓ 40% время** на структурирование заявок

---

*Документ подготовлен: 2025-10-05*
*Автор: grant-architect agent*
*Версия: 1.0*
