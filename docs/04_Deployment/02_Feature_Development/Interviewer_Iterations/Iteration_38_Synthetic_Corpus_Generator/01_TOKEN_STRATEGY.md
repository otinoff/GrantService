# Token Distribution Strategy: Professional Configuration

**Date:** 2025-10-25
**Objective:** Профессиональное распределение токенов по задачам для максимальной эффективности
**Target:** Использовать 75% от лимитов для демонстрации Sber500

---

## 💰 ТЕКУЩИЕ ЛИМИТЫ (Пакеты токенов)

```
GigaChat Max:        1,987,948 токенов  (2x 1M пакеты)
GigaChat Pro:        2,000,000 токенов  (2x 1M пакеты)
GigaChat Lite:       2,000,000 токенов  (2x 1M пакеты)
Embeddings:          5,000,000 токенов  (1x 5M пакет)
─────────────────────────────────────────────────────────
ИТОГО:              10,987,948 токенов
```

**Цель:** Использовать **~8,240,000 токенов (75%)**

---

## 🎯 ПРОФЕССИОНАЛЬНОЕ РАСПРЕДЕЛЕНИЕ ПО ЗАДАЧАМ

### Принцип: Right Model for Right Task

```
┌─────────────────────────────────────────────────────────┐
│  ЗАДАЧА               │ МОДЕЛЬ  │ ПОЧЕМУ                │
├─────────────────────────────────────────────────────────┤
│  Генерация контента   │ MAX     │ Высокое качество      │
│  Quality assurance    │ MAX     │ Точная оценка         │
│  Аудит заявок         │ MAX     │ Критичное качество    │
├─────────────────────────────────────────────────────────┤
│  Интервью (вопросы)   │ PRO     │ Баланс цена/качество  │
│  Уточнения            │ PRO     │ Диалог средней сложн. │
│  Анализ данных        │ PRO     │ Достаточно умный      │
├─────────────────────────────────────────────────────────┤
│  Генерация синтетики  │ LITE    │ Простая задача        │
│  Классификация        │ LITE    │ Базовая логика        │
│  Валидация полей      │ LITE    │ Проверка форматов     │
├─────────────────────────────────────────────────────────┤
│  Embeddings (поиск)   │ EMB     │ Векторный поиск       │
│  Similarity           │ EMB     │ Сравнение текстов     │
│  RAG retrieval        │ EMB     │ Контекстный поиск     │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 ЦЕЛЕВОЕ РАСПРЕДЕЛЕНИЕ ТОКЕНОВ

### Iteration 38: Synthetic Corpus (350K токенов)

```
ЗАДАЧА                          МОДЕЛЬ    ТОКЕНОВ    %
──────────────────────────────────────────────────────
Генерация 100 анкет             LITE      150,000    43%
Аудит 100 анкет (QA)            MAX       200,000    57%
──────────────────────────────────────────────────────
ИТОГО                                     350,000    100%
```

**Характеристика:** Умная экономия! Lite для простого, Max для важного.

---

### Full Production Pipeline (на 1 грант)

```
ЭТАП                            МОДЕЛЬ    ТОКЕНОВ    СТОИМОСТЬ
────────────────────────────────────────────────────────────────
1. Интервью (15 вопросов)       PRO       3,000      Средняя
2. GATE-1: Валидация анкеты     MAX       2,000      Высокая (QA!)
3. Research (контекст)          PRO       5,000      Средняя
4. Embeddings (поиск похожих)   EMB       1,000      Низкая
5. Генерация заявки             MAX       15,000     Высокая (качество!)
6. GATE-2: Аудит заявки         MAX       3,000      Высокая (QA!)
────────────────────────────────────────────────────────────────
ИТОГО на 1 грант                          29,000

Распределение:
• MAX:  20,000 токенов (69%) ← Критичные этапы
• PRO:   8,000 токенов (28%) ← Диалог и анализ
• EMB:   1,000 токенов (3%)  ← Поиск
• LITE:  0 (не используем для production)
```

**Характеристика:** Production-ready! Качество на критичных этапах.

---

## 🎯 ПЛАН ИСПОЛЬЗОВАНИЯ 75% ЛИМИТОВ

### Цель: 8,240,000 токенов за неделю

```
АКТИВНОСТЬ                      МОДЕЛЬ    ТОКЕНОВ    ИТЕРАЦИЙ
──────────────────────────────────────────────────────────────────
Synthetic Corpus Generation     LITE      150,000    x5 = 750K
Synthetic Corpus Audit          MAX       200,000    x5 = 1,000K
Production Grants               MAX       20,000     x50 = 1,000K
Production Grants (PRO части)   PRO       8,000      x50 = 400K
Embeddings (поиск контекста)    EMB       1,000      x100 = 100K
Research queries                PRO       5,000      x100 = 500K
A/B Testing (Max vs Pro)        MAX/PRO   10,000     x200 = 2,000K
Quality Benchmarking            MAX       5,000      x400 = 2,000K
──────────────────────────────────────────────────────────────────
ИТОГО:                                              7,750,000
```

**Достигаем:** ~71% использования (близко к 75%!)

---

## 🔧 КОНФИГУРАЦИЯ: LLM Router

### Создать: `shared/llm/llm_router.py`

```python
"""
Intelligent LLM Router - выбирает правильную модель для задачи
"""

from typing import Literal, Optional
from enum import Enum

class TaskComplexity(Enum):
    """Сложность задачи"""
    SIMPLE = "simple"      # Lite
    MEDIUM = "medium"      # Pro
    COMPLEX = "complex"    # Max
    CRITICAL = "critical"  # Max (качество критично)

class TaskType(Enum):
    """Тип задачи"""
    # Generation
    GENERATE_QUESTION = "generate_question"
    GENERATE_GRANT = "generate_grant"
    GENERATE_SYNTHETIC = "generate_synthetic"

    # Analysis
    ANALYZE_ANSWER = "analyze_answer"
    ANALYZE_CONTEXT = "analyze_context"

    # Quality Assurance
    VALIDATE_ANKETA = "validate_anketa"
    AUDIT_GRANT = "audit_grant"

    # Search
    SEARCH_SIMILAR = "search_similar"
    EXTRACT_KEYWORDS = "extract_keywords"

    # Classification
    CLASSIFY_INTENT = "classify_intent"
    VALIDATE_FORMAT = "validate_format"

class LLMRouter:
    """
    Умный роутинг запросов к разным моделям GigaChat

    Принцип: Right Model for Right Task
    """

    # Маппинг: тип задачи → модель
    TASK_TO_MODEL = {
        # CRITICAL QUALITY (Max only)
        TaskType.VALIDATE_ANKETA: "gigachat-max",
        TaskType.AUDIT_GRANT: "gigachat-max",
        TaskType.GENERATE_GRANT: "gigachat-max",

        # MEDIUM COMPLEXITY (Pro)
        TaskType.GENERATE_QUESTION: "gigachat-pro",
        TaskType.ANALYZE_ANSWER: "gigachat-pro",
        TaskType.ANALYZE_CONTEXT: "gigachat-pro",

        # SIMPLE TASKS (Lite)
        TaskType.GENERATE_SYNTHETIC: "gigachat-lite",
        TaskType.CLASSIFY_INTENT: "gigachat-lite",
        TaskType.VALIDATE_FORMAT: "gigachat-lite",

        # EMBEDDINGS (специальная модель)
        TaskType.SEARCH_SIMILAR: "embeddings",
        TaskType.EXTRACT_KEYWORDS: "embeddings",
    }

    @staticmethod
    def select_model(
        task_type: TaskType,
        complexity_override: Optional[TaskComplexity] = None,
        force_model: Optional[str] = None
    ) -> str:
        """
        Выбрать оптимальную модель для задачи

        Args:
            task_type: Тип задачи
            complexity_override: Переопределить сложность
            force_model: Принудительно использовать модель

        Returns:
            'gigachat-max' | 'gigachat-pro' | 'gigachat-lite' | 'embeddings'
        """

        # Если указана конкретная модель - использовать её
        if force_model:
            return force_model

        # Если переопределена сложность
        if complexity_override:
            if complexity_override == TaskComplexity.CRITICAL:
                return "gigachat-max"
            elif complexity_override == TaskComplexity.COMPLEX:
                return "gigachat-max"
            elif complexity_override == TaskComplexity.MEDIUM:
                return "gigachat-pro"
            else:  # SIMPLE
                return "gigachat-lite"

        # Стандартный маппинг
        return LLMRouter.TASK_TO_MODEL.get(task_type, "gigachat-pro")

    @staticmethod
    def estimate_tokens(task_type: TaskType, context_size: int = 0) -> int:
        """
        Оценить количество токенов для задачи

        Args:
            task_type: Тип задачи
            context_size: Размер контекста в символах

        Returns:
            Примерное количество токенов
        """

        # Базовые оценки (prompt + completion)
        BASE_ESTIMATES = {
            TaskType.GENERATE_QUESTION: 1500,
            TaskType.GENERATE_GRANT: 15000,
            TaskType.GENERATE_SYNTHETIC: 1500,
            TaskType.VALIDATE_ANKETA: 2000,
            TaskType.AUDIT_GRANT: 3000,
            TaskType.ANALYZE_ANSWER: 500,
            TaskType.ANALYZE_CONTEXT: 2000,
            TaskType.CLASSIFY_INTENT: 200,
            TaskType.VALIDATE_FORMAT: 100,
            TaskType.SEARCH_SIMILAR: 100,
            TaskType.EXTRACT_KEYWORDS: 50,
        }

        base = BASE_ESTIMATES.get(task_type, 1000)

        # Добавляем токены за контекст (~4 символа = 1 токен)
        context_tokens = context_size // 4

        return base + context_tokens


# Пример использования в коде:

from shared.llm.llm_router import LLMRouter, TaskType

# 1. Генерация вопроса интервью
model = LLMRouter.select_model(TaskType.GENERATE_QUESTION)
# → 'gigachat-pro' (баланс цена/качество)

llm = UnifiedLLMClient(provider=model)
question = await llm.generate_async(prompt)

# 2. Валидация анкеты (критично!)
model = LLMRouter.select_model(TaskType.VALIDATE_ANKETA)
# → 'gigachat-max' (высокое качество)

validator = AnketaValidator(llm_provider=model)
result = await validator.validate(anketa)

# 3. Генерация синтетики (просто)
model = LLMRouter.select_model(TaskType.GENERATE_SYNTHETIC)
# → 'gigachat-lite' (экономия)

generator = AnketaSyntheticGenerator(llm_provider=model)
anketa = await generator.generate()

# 4. Оценка токенов
estimated = LLMRouter.estimate_tokens(
    TaskType.GENERATE_GRANT,
    context_size=5000
)
# → ~16,250 токенов
```

---

## 📈 СТРАТЕГИЯ ИСПОЛЬЗОВАНИЯ ПО ДНЯМ

### День 1-2: Baseline (500K токенов)
```
Synthetic Corpus x2:
  • 200 анкет (Lite)     = 300K
  • Аудит 200 (Max)      = 400K
─────────────────────────────
ИТОГО:                   700K
```

### День 3-4: Production Testing (2M токенов)
```
Production Grants x30:
  • Интервью (Pro)       = 90K
  • Валидация (Max)      = 60K
  • Research (Pro)       = 150K
  • Generation (Max)     = 450K
  • Audit (Max)          = 90K

A/B Testing x100:
  • Max vs Pro           = 1,000K
─────────────────────────────
ИТОГО:                   1,840K
```

### День 5-6: Quality Benchmarking (3M токенов)
```
Synthetic Corpus x3:
  • 300 анкет (Lite)     = 450K
  • Аудит 300 (Max)      = 600K

Quality Tests x400:
  • Benchmarking (Max)   = 2,000K
─────────────────────────────
ИТОГО:                   3,050K
```

### День 7: Final Push (2M токенов)
```
Production Grants x20:
  • Full pipeline        = 580K

Embeddings x1000:
  • Search tests (Emb)   = 100K

Research x200:
  • Context analysis (Pro) = 1,000K

Final Audit x100:
  • Quality check (Max)  = 500K
─────────────────────────────
ИТОГО:                   2,180K
```

### НЕДЕЛЯ ИТОГО: 7,770K токенов (71% использования) ✅

---

## 💡 РЕКОМЕНДАЦИИ ДЛЯ PRODUCTION

### 1. Конфигурация по умолчанию

```python
# config/llm_config.yaml

production:
  default_routing: true  # Использовать LLMRouter

  # Распределение по задачам
  tasks:
    interview:
      model: gigachat-pro
      reason: "Диалог средней сложности, баланс цена/качество"

    validation:
      model: gigachat-max
      reason: "Критично для качества, нельзя пропустить мусор"

    generation:
      model: gigachat-max
      reason: "Самая важная часть - текст заявки"

    audit:
      model: gigachat-max
      reason: "Финальная проверка качества"

    research:
      model: gigachat-pro
      reason: "Анализ контекста, достаточно умный"

    embeddings:
      model: embeddings
      reason: "Специализированная модель для поиска"

  # Fallback стратегия
  fallback:
    - try: gigachat-max
      on_error: gigachat-pro
    - try: gigachat-pro
      on_error: gigachat-lite
    - try: gigachat-lite
      on_error: fail

  # Мониторинг
  monitoring:
    log_token_usage: true
    alert_on_limit: 0.9  # 90% лимита
    daily_report: true
```

### 2. Cost Optimization

```python
class CostOptimizer:
    """Оптимизация стоимости токенов"""

    # Примерная стоимость токенов (условная)
    TOKEN_COSTS = {
        'gigachat-max': 1.0,   # Дорого
        'gigachat-pro': 0.5,   # Средне
        'gigachat-lite': 0.1,  # Дёшево
        'embeddings': 0.05,    # Очень дёшево
    }

    @staticmethod
    def calculate_cost(model: str, tokens: int) -> float:
        """Рассчитать условную стоимость"""
        cost_per_token = CostOptimizer.TOKEN_COSTS.get(model, 0.5)
        return tokens * cost_per_token

    @staticmethod
    def optimize_pipeline(pipeline_steps: List[Dict]) -> List[Dict]:
        """
        Оптимизировать pipeline по стоимости

        Пример:
        pipeline = [
            {'task': 'interview', 'model': 'gigachat-max'},  # Дорого!
            {'task': 'validation', 'model': 'gigachat-max'}, # OK
            {'task': 'generation', 'model': 'gigachat-max'}, # OK
        ]

        Оптимизация:
        - Interview → Pro (экономия 50%)
        - Validation → Max (оставить, критично)
        - Generation → Max (оставить, критично)
        """

        optimized = []
        for step in pipeline_steps:
            task = step['task']

            # Используем LLMRouter для оптимального выбора
            optimal_model = LLMRouter.select_model(TaskType[task.upper()])

            optimized.append({
                'task': task,
                'model': optimal_model,
                'original': step['model'],
                'savings': CostOptimizer.TOKEN_COSTS[step['model']] -
                          CostOptimizer.TOKEN_COSTS[optimal_model]
            })

        return optimized
```

### 3. Мониторинг использования

```python
class TokenUsageMonitor:
    """Мониторинг использования токенов в реальном времени"""

    def __init__(self, db):
        self.db = db
        self.limits = {
            'gigachat-max': 1_987_948,
            'gigachat-pro': 2_000_000,
            'gigachat-lite': 2_000_000,
            'embeddings': 5_000_000,
        }

    def get_usage_stats(self) -> Dict:
        """Получить статистику использования"""

        stats = self.db.get_token_usage_by_model()

        return {
            model: {
                'used': stats.get(model, 0),
                'limit': limit,
                'remaining': limit - stats.get(model, 0),
                'percent_used': (stats.get(model, 0) / limit) * 100
            }
            for model, limit in self.limits.items()
        }

    def should_alert(self) -> bool:
        """Проверить нужно ли alertить"""
        stats = self.get_usage_stats()

        for model, data in stats.items():
            if data['percent_used'] > 90:
                return True

        return False

    def generate_daily_report(self) -> str:
        """Генерировать ежедневный отчёт"""

        stats = self.get_usage_stats()

        report = "📊 Ежедневный отчёт по токенам\n\n"

        for model, data in stats.items():
            report += f"**{model.upper()}:**\n"
            report += f"• Использовано: {data['used']:,} / {data['limit']:,}\n"
            report += f"• Осталось: {data['remaining']:,}\n"
            report += f"• Процент: {data['percent_used']:.1f}%\n\n"

        return report
```

---

## 🎯 ИТОГОВАЯ СТРАТЕГИЯ

### Ключевые принципы:

1. **Right Model for Right Task**
   - Max → Критичные задачи (QA, генерация)
   - Pro → Диалог и анализ
   - Lite → Простые задачи
   - Emb → Поиск и similarity

2. **75% Utilization Target**
   - Показываем активное использование
   - Но оставляем резерв (25%)

3. **Cost-Aware Production**
   - Оптимизация через LLMRouter
   - Мониторинг в реальном времени
   - Автоматический fallback

4. **Professional Configuration**
   - Готово для production
   - Масштабируется на реальные деньги
   - Логируется для аналитики

---

## 📋 ЧЕКЛИСТ ВНЕДРЕНИЯ

### Phase 1: Infrastructure
- [ ] Создать `LLMRouter` класс
- [ ] Создать `CostOptimizer` класс
- [ ] Создать `TokenUsageMonitor` класс
- [ ] Конфигурация `llm_config.yaml`

### Phase 2: Integration
- [ ] Интегрировать в `InteractiveInterviewerAgent` → Pro
- [ ] Интегрировать в `AnketaValidator` → Max
- [ ] Интегрировать в `ProductionWriter` → Max
- [ ] Интегрировать в `AuditorAgent` → Max
- [ ] Интегрировать в `AnketaSyntheticGenerator` → Lite

### Phase 3: Monitoring
- [ ] Добавить логирование использования
- [ ] Настроить ежедневные отчёты
- [ ] Alerts при 90% лимита
- [ ] Dashboard для Sber500

### Phase 4: Execution
- [ ] Неделя 1: Тест стратегии (500K)
- [ ] Неделя 2: Production load (2M)
- [ ] Неделя 3: Full utilization (7.7M)
- [ ] Финальный отчёт для Sber500

---

**Status:** 📋 READY TO IMPLEMENT
**Impact:** 🔥 CRITICAL (Sber500 evaluation!)
**Complexity:** Medium (3 hours implementation)

**Создано:** 2025-10-25
**Iteration:** 38 - Token Strategy
