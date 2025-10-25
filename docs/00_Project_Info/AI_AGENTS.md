# AI Agents Configuration
**Version**: 1.1.0 | **Last Modified**: 2025-10-03

## Table of Contents
- [Overview](#overview)
- [Project Orchestrator](#project-orchestrator)
- [GigaChat Integration](#gigachat-integration)
- [Grant Application Agents](#grant-application-agents)
- [Development Agents](#development-agents)
- [Agent Artifacts Structure](#agent-artifacts-structure)
- [Garbage Collection Rules](#garbage-collection-rules)
- [Prompt Management](#prompt-management)
- [Performance Metrics](#performance-metrics)

## Overview

GrantService использует систему AI агентов для автоматизации различных процессов:
- **Project Orchestrator** - главный координатор всех агентов
- **Grant Agents** - для работы с грантовыми заявками
- **Development Agents** - для разработки и поддержки системы
- **Support Agents** - для помощи пользователям

### Agent Architecture
```
┌─────────────────────────────────────┐
│      Project Orchestrator           │
│    (Координация и управление)       │
├──────────┬──────────┬──────────────┤
│          │          │              │
▼          ▼          ▼              ▼
Grant    Development  Quality    Support
Agents     Agents    & Ops      Agents
│          │          │              │
└──────────┴──────────┴──────────────┘
               │
               ▼
        ┌──────────────┐
        │   GigaChat   │
        │   API v2.0   │
        └──────────────┘
```

## Project Orchestrator

### Overview
**Version**: 1.0.0 | **Created**: 2025-10-03
**Purpose**: Главный оркестратор проекта, ответственный за координацию команды специализированных агентов и управление архитектурой проекта.

### Responsibilities
1. **Координация агентов**
   - Анализ задач и определение необходимых агентов
   - Делегирование подзадач специализированным агентам
   - Интеграция результатов работы всех агентов
   - Разрешение конфликтов между решениями агентов

2. **Управление артефактами и Garbage Collection**
   - Применение правил GC согласно `gc-rules.yaml`
   - Контроль размещения артефактов в правильных папках
   - Очистка устаревших отчётов и временных файлов
   - Поддержание чистоты структуры проекта

3. **Архитектурный надзор**
   - Соблюдение архитектурных принципов проекта
   - Предотвращение дублирования кода и функционала
   - Контроль качества интеграций между модулями
   - Поддержка актуальности основной документации

### Delegation Workflow
```yaml
# Feature development template
primary: grant-architect / streamlit-admin-developer / telegram-bot-developer
supporting:
  - database-manager (if schema changes needed)
  - ai-integration-specialist (if AI features needed)
review:
  - test-engineer (mandatory)
  - documentation-keeper (update docs)
```
```

#### Evaluation Criteria
```python
EVALUATION_CRITERIA = {
    "innovation": {
        "weight": 0.25,
        "description": "Инновационность и уникальность проекта"
    },
    "social_impact": {
        "weight": 0.30,
        "description": "Социальная значимость и влияние"
    },
    "feasibility": {
        "weight": 0.20,
        "description": "Реализуемость и реалистичность"
    },
    "sustainability": {
        "weight": 0.15,
        "description": "Устойчивость и долгосрочность"
    },
    "team": {
        "weight": 0.10,
        "description": "Команда и компетенции"
    }
}
```

#### Audit Report Template
```python
AUDIT_TEMPLATE = """
# Аудит проекта: {project_name}

## Общая оценка: {score}/10

### Сильные стороны:
{strengths}

### Области для улучшения:
{improvements}

### Рекомендации:
{recommendations}

### Соответствие грантовым требованиям:
{grant_compliance}
"""
```

### 3. Planner Agent
**Version**: 1.0.5
**Model**: GigaChat-Pro
**Purpose**: Структурирование заявки и создание плана

#### Configuration
```python
PLANNER_CONFIG = {
    "model": "GigaChat-Pro",
    "temperature": 0.4,
    "max_tokens": 2000,
    "system_prompt_version": "1.0.5"
}
```

#### Plan Structure
```python
GRANT_STRUCTURE = {
    "sections": [
        {
            "id": "summary",
            "title": "Краткое описание проекта",
            "max_words": 500,
            "required": True
        },
        {
            "id": "problem",
            "title": "Проблема и актуальность",
            "max_words": 800,
            "required": True
        },
        {
            "id": "solution",
            "title": "Предлагаемое решение",
            "max_words": 1000,
            "required": True
        },
        {
            "id": "goals",
            "title": "Цели и задачи",
            "max_words": 600,
            "required": True
        },
        {
            "id": "audience",
            "title": "Целевая аудитория",
            "max_words": 400,
            "required": True
        },
        {
            "id": "plan",
            "title": "План реализации",
            "max_words": 1200,
            "required": True
        },
        {
            "id": "budget",
            "title": "Бюджет проекта",
            "max_words": 800,
            "required": True
        },
        {
            "id": "results",
            "title": "Ожидаемые результаты",
            "max_words": 600,
            "required": True
        }
    ]
}
```

### 4. Writer Agent
**Version**: 1.3.0
**Model**: GigaChat-Max
**Purpose**: Написание текстов грантовой заявки

#### Configuration
```python
WRITER_CONFIG = {
    "model": "GigaChat-Max",
    "temperature": 0.7,
    "max_tokens": 3000,
    "system_prompt_version": "1.3.0",
    "style": "professional",
    "tone": "confident"
}
```

#### Writing Guidelines
```python
WRITING_RULES = """
1. Используй профессиональный, но доступный язык
2. Избегай сложных терминов без необходимости
3. Приводи конкретные факты и цифры
4. Структурируй текст с подзаголовками
5. Используй активный залог
6. Делай акцент на результатах и влиянии
7. Соблюдай лимиты по количеству слов
8. Проверяй соответствие требованиям гранта
"""
```

## Development Agents

### 1. AI Integration Specialist
**Version**: 1.0.0
**Purpose**: Интеграция AI технологий в проект

#### Responsibilities
- Интеграция LLM моделей
- Оптимизация промптов
- Мониторинг производительности AI
- A/B тестирование промптов

### 2. Telegram Bot Developer
**Version**: 1.0.0
**Purpose**: Разработка и поддержка Telegram бота

#### Responsibilities
- Разработка новых команд
- Интеграция с AI агентами
- Оптимизация пользовательского опыта
- Обработка ошибок и исключений

### 3. Test Engineer
**Version**: 1.0.0
**Purpose**: Тестирование и контроль качества

#### Responsibilities
- Автоматизированное тестирование
- Интеграционные тесты
- Нагрузочное тестирование
- Мониторинг качества

### 4. Documentation Keeper
**Version**: 1.0.0
**Purpose**: Поддержка актуальной документации

#### Responsibilities
- Обновление документации
- Версионирование документов
- Создание примеров использования
- Поддержка changelog

## Prompt Management

### Prompt Versioning
```python
class PromptManager:
    def __init__(self):
        self.prompts = {}

    def register_prompt(self, agent_type, version, prompt_text):
        """Register new prompt version"""
        key = f"{agent_type}_{version}"
        self.prompts[key] = {
            "text": prompt_text,
            "created_at": datetime.now(),
            "usage_count": 0,
            "success_rate": 0.0
        }

    def get_prompt(self, agent_type, version=None):
        """Get prompt by agent type and version"""
        if version is None:
            version = self.get_latest_version(agent_type)
        return self.prompts.get(f"{agent_type}_{version}")

    def update_metrics(self, agent_type, version, success):
        """Update prompt performance metrics"""
        key = f"{agent_type}_{version}"
        if key in self.prompts:
            self.prompts[key]["usage_count"] += 1
            # Update success rate calculation
```

### Prompt Testing
```python
def test_prompt(prompt_text, test_cases):
    """Test prompt with various inputs"""
    results = []

    for test_case in test_cases:
        response = gigachat_client.generate(
            prompt=prompt_text.format(**test_case["input"]),
            temperature=0.3
        )

        score = evaluate_response(
            response,
            test_case["expected_output"]
        )

        results.append({
            "test_case": test_case["name"],
            "score": score,
            "response": response
        })

    return {
        "average_score": sum(r["score"] for r in results) / len(results),
        "results": results
    }
```

### A/B Testing
```python
class ABTestManager:
    def __init__(self):
        self.tests = {}

    def create_test(self, agent_type, prompt_a, prompt_b):
        """Create A/B test for prompts"""
        test_id = f"{agent_type}_{datetime.now().timestamp()}"
        self.tests[test_id] = {
            "prompt_a": prompt_a,
            "prompt_b": prompt_b,
            "results_a": [],
            "results_b": [],
            "start_time": datetime.now()
        }
        return test_id

    def select_variant(self, test_id):
        """Select variant for test"""
        import random
        return "a" if random.random() < 0.5 else "b"

    def record_result(self, test_id, variant, success):
        """Record test result"""
        if variant == "a":
            self.tests[test_id]["results_a"].append(success)
        else:
            self.tests[test_id]["results_b"].append(success)

    def analyze_results(self, test_id):
        """Analyze A/B test results"""
        test = self.tests[test_id]
        success_rate_a = sum(test["results_a"]) / len(test["results_a"])
        success_rate_b = sum(test["results_b"]) / len(test["results_b"])

        return {
            "variant_a": success_rate_a,
            "variant_b": success_rate_b,
            "winner": "a" if success_rate_a > success_rate_b else "b",
            "confidence": calculate_confidence(test["results_a"], test["results_b"])
        }
```

## Performance Metrics

### Agent Metrics
```python
AGENT_METRICS = {
    "response_time": {
        "unit": "seconds",
        "threshold": 5.0,
        "alert_on": "exceed"
    },
    "token_usage": {
        "unit": "tokens",
        "threshold": 3000,
        "alert_on": "exceed"
    },
    "success_rate": {
        "unit": "percentage",
        "threshold": 0.85,
        "alert_on": "below"
    },
    "user_satisfaction": {
        "unit": "score",
        "threshold": 4.0,
        "alert_on": "below"
    }
}
```

### Monitoring Dashboard
```python
class AgentMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)

    def record_metric(self, agent_type, metric_name, value):
        """Record agent metric"""
        self.metrics[f"{agent_type}_{metric_name}"].append({
            "value": value,
            "timestamp": datetime.now()
        })

    def get_statistics(self, agent_type, metric_name, period="1h"):
        """Get metric statistics for period"""
        key = f"{agent_type}_{metric_name}"
        data = self.filter_by_period(self.metrics[key], period)

        return {
            "average": np.mean([d["value"] for d in data]),
            "median": np.median([d["value"] for d in data]),
            "min": min([d["value"] for d in data]),
            "max": max([d["value"] for d in data]),
            "count": len(data)
        }

    def check_alerts(self):
        """Check if any metrics exceed thresholds"""
        alerts = []
        for metric_key, values in self.metrics.items():
            agent_type, metric_name = metric_key.rsplit("_", 1)

            if metric_name in AGENT_METRICS:
                threshold = AGENT_METRICS[metric_name]["threshold"]
                alert_on = AGENT_METRICS[metric_name]["alert_on"]
                recent_value = values[-1]["value"] if values else 0

                if alert_on == "exceed" and recent_value > threshold:
                    alerts.append({
                        "agent": agent_type,
                        "metric": metric_name,
                        "value": recent_value,
                        "threshold": threshold
                    })
                elif alert_on == "below" and recent_value < threshold:
                    alerts.append({
                        "agent": agent_type,
                        "metric": metric_name,
                        "value": recent_value,
                        "threshold": threshold
                    })

        return alerts
```

### Cost Tracking
```python
GIGACHAT_PRICING = {
    "GigaChat": 0.001,      # per 1000 tokens
    "GigaChat-Pro": 0.002,  # per 1000 tokens
    "GigaChat-Max": 0.005   # per 1000 tokens
}

class CostTracker:
    def __init__(self):
        self.usage = defaultdict(int)

    def track_usage(self, model, tokens):
        """Track token usage"""
        self.usage[model] += tokens

    def calculate_cost(self):
        """Calculate total cost"""
        total_cost = 0
        for model, tokens in self.usage.items():
            cost_per_token = GIGACHAT_PRICING.get(model, 0)
            total_cost += (tokens / 1000) * cost_per_token
        return total_cost

    def get_report(self):
        """Generate cost report"""
        return {
            "usage_by_model": dict(self.usage),
            "total_tokens": sum(self.usage.values()),
            "total_cost": self.calculate_cost(),
            "average_cost_per_request": self.calculate_cost() / len(self.usage)
        }
```

## Agent Configuration Files

### agents_config.yaml
```yaml
agents:
  interviewer:
    version: "1.2.0"
    model: "GigaChat-Pro"
    temperature: 0.6
    max_tokens: 1500
    enabled: true

  auditor:
    version: "1.1.0"
    model: "GigaChat-Pro"
    temperature: 0.3
    max_tokens: 2500
    enabled: true

  planner:
    version: "1.0.5"
    model: "GigaChat-Pro"
    temperature: 0.4
    max_tokens: 2000
    enabled: true

  writer:
    version: "1.3.0"
    model: "GigaChat-Max"
    temperature: 0.7
    max_tokens: 3000
    enabled: true

monitoring:
  enabled: true
  alert_email: "admin@grantservice.ru"
  check_interval: 300  # seconds

cost_tracking:
  enabled: true
  budget_limit: 1000  # USD per month
  alert_threshold: 0.8  # 80% of budget
```

## Best Practices

### Prompt Engineering
1. **Clarity**: Четкие и однозначные инструкции
2. **Context**: Предоставляйте достаточный контекст
3. **Examples**: Используйте примеры для сложных задач
4. **Constraints**: Задавайте ограничения (длина, формат)
5. **Iteration**: Тестируйте и улучшайте промпты

### Error Handling
```python
def safe_agent_call(agent, *args, **kwargs):
    """Safe wrapper for agent calls"""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            return agent.process(*args, **kwargs)
        except RateLimitError as e:
            time.sleep(retry_delay * (2 ** attempt))
        except TokenLimitError as e:
            # Reduce max_tokens and retry
            kwargs["max_tokens"] = kwargs.get("max_tokens", 2000) * 0.8
        except Exception as e:
            logger.error(f"Agent error: {e}")
            if attempt == max_retries - 1:
                return {"error": str(e), "status": "failed"}

    return {"error": "Max retries exceeded", "status": "failed"}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-29 | Initial AI agents documentation |

---

*This document is maintained by documentation-keeper agent*