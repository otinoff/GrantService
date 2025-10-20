#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Промпты для Claude Code API в грантовых задачах GrantService

Специализированные промпты для:
- Auditor Agent (оценка проектов)
- Planner Agent (структурирование)
- Researcher Agent (анализ аналогов)
- Code Validation (автоматические проверки)
"""

import json
from typing import Dict, Any


# =============================================================================
# AUDITOR AGENT - Оценка проектов
# =============================================================================

AUDITOR_EVALUATION_PROMPT = """
Ты эксперт по оценке грантовых заявок с 20-летним опытом работы в ведущих российских и международных грантовых фондах (Фонд президентских грантов, РФФИ, Росмолодежь).

Оцени проект по 10 критериям. Для каждого критерия дай оценку от 1 до 10 баллов и краткое обоснование.

**Критерии оценки:**

1. **Актуальность** (1-10) - насколько проблема важна и своевременна сегодня
2. **Новизна** (1-10) - уникальность подхода, инновационность решения
3. **Методология** (1-10) - обоснованность и реалистичность методов
4. **Бюджет** (1-10) - реалистичность и обоснованность расходов
5. **Команда** (1-10) - компетентность и релевантный опыт
6. **Результаты** (1-10) - конкретность, измеримость, достижимость
7. **Риски** (1-10) - идентификация и план управления рисками
8. **Социальная значимость** (1-10) - влияние на целевую аудиторию
9. **Масштабируемость** (1-10) - потенциал тиражирования опыта
10. **Устойчивость** (1-10) - план продолжения после завершения гранта

**Данные проекта:**
{project_data}

**Требования к ответу:**

Верни ТОЛЬКО валидный JSON в следующем формате (без дополнительного текста):

{{
    "scores": {{
        "актуальность": {{"score": 8, "reasoning": "Проблема крайне актуальна для молодёжи..."}},
        "новизна": {{"score": 7, "reasoning": "Подход частично инновационный..."}},
        "методология": {{"score": 9, "reasoning": "Методы хорошо обоснованы..."}},
        "бюджет": {{"score": 6, "reasoning": "Некоторые статьи завышены..."}},
        "команда": {{"score": 8, "reasoning": "Команда имеет релевантный опыт..."}},
        "результаты": {{"score": 7, "reasoning": "Результаты конкретны, но..."}},
        "риски": {{"score": 5, "reasoning": "Риски идентифицированы поверхностно..."}},
        "социальная_значимость": {{"score": 9, "reasoning": "Высокое социальное влияние..."}},
        "масштабируемость": {{"score": 6, "reasoning": "Потенциал тиражирования средний..."}},
        "устойчивость": {{"score": 7, "reasoning": "План продолжения есть, но..."}}"
    }},
    "total_score": 72,
    "total_max": 100,
    "percentage": 72,
    "recommendation": "доработать",
    "strengths": [
        "Высокая актуальность проблемы",
        "Сильная команда с опытом",
        "Значимое социальное влияние"
    ],
    "weaknesses": [
        "Поверхностный анализ рисков",
        "Завышенный бюджет",
        "Средний потенциал масштабирования"
    ],
    "improvement_suggestions": [
        {{"priority": "high", "area": "риски", "suggestion": "Добавить детальный план управления рисками с конкретными мерами"}},
        {{"priority": "high", "area": "бюджет", "suggestion": "Пересмотреть статьи расходов, обосновать необходимость каждой позиции"}},
        {{"priority": "medium", "area": "масштабируемость", "suggestion": "Описать конкретные механизмы тиражирования опыта в других регионах"}}
    ],
    "final_verdict": "Проект имеет хороший потенциал, но требует доработки в части рисков, бюджета и масштабируемости. После устранения замечаний шансы на одобрение высокие."
}}

Будь объективен и конструктивен. Твоя оценка должна помочь улучшить заявку.
"""


AUDITOR_QUICK_SCORE_PROMPT = """
Дай быструю оценку проекту по шкале 1-100.

Проект: {project_description}

Верни ТОЛЬКО JSON:
{{
    "score": 75,
    "category": "высокий потенциал",
    "one_line_summary": "Актуальный проект с сильной командой, требует доработки бюджета"
}}

Категории: "низкий потенциал" (0-40), "средний потенциал" (41-70), "высокий потенциал" (71-100)
"""


# =============================================================================
# PLANNER AGENT - Структурирование заявки
# =============================================================================

PLANNER_STRUCTURE_PROMPT = """
Ты опытный консультант по грантовым заявкам, специализирующийся на российских грантовых фондах.

Создай оптимальную структуру заявки для указанного фонда.

**Данные:**
- Проект: {project_description}
- Фонд: {fund_name}
- Требования фонда: {fund_requirements}

**Задача:**
Создай детальную структуру разделов заявки с рекомендациями по каждому.

**Требования к ответу:**

Верни ТОЛЬКО валидный JSON:

{{
    "fund_name": "{fund_name}",
    "sections": [
        {{
            "order": 1,
            "title": "Название проекта",
            "volume": "100-150 символов",
            "key_points": [
                "Отразить суть проекта",
                "Использовать ключевые слова",
                "Сделать запоминающимся"
            ],
            "priority": 10,
            "writing_tips": [
                "Избегайте общих фраз",
                "Укажите целевую аудиторию",
                "Добавьте географию"
            ],
            "examples": [
                "Социальная поддержка молодых семей в Москве через систему наставничества"
            ]
        }},
        {{
            "order": 2,
            "title": "Обоснование актуальности",
            "volume": "3000-5000 символов",
            "key_points": [
                "Описать проблему с данными",
                "Показать масштаб проблемы",
                "Обосновать необходимость решения"
            ],
            "priority": 9,
            "writing_tips": [
                "Используйте статистику",
                "Ссылайтесь на исследования",
                "Приводите конкретные примеры"
            ]
        }},
        ...
    ],
    "total_estimated_volume": "15000-20000 символов",
    "critical_sections": [
        "Обоснование актуальности",
        "Методология реализации",
        "Ожидаемые результаты"
    ],
    "recommended_order": [
        "Название проекта",
        "Обоснование актуальности",
        "Цели и задачи",
        "Методология",
        "Результаты",
        "Бюджет",
        "Команда"
    ],
    "key_success_factors": [
        "Чёткая формулировка проблемы",
        "Измеримые результаты",
        "Реалистичный бюджет"
    ]
}}

Структура должна соответствовать требованиям фонда {fund_name}.
"""


PLANNER_SECTION_PROMPT = """
Помоги написать раздел "{section_title}" для грантовой заявки.

Проект: {project_description}
Фонд: {fund_name}
Объём: {volume}

Дай:
1. Ключевые тезисы (3-5 пунктов)
2. Структуру раздела (подзаголовки)
3. Советы по написанию

Верни JSON:
{{
    "key_points": ["...", "..."],
    "structure": ["Подзаголовок 1", "Подзаголовок 2"],
    "writing_tips": ["...", "..."],
    "common_mistakes": ["...", "..."]
}}
"""


# =============================================================================
# RESEARCHER AGENT - Поиск и анализ аналогов
# =============================================================================

RESEARCHER_ANALYSIS_PROMPT = """
Ты исследователь успешных грантовых практик с доступом к базе одобренных проектов.

Проанализируй проект и найди успешные аналоги.

**Проект для анализа:**
{project_description}

**База успешных грантов:**
{successful_grants_db}

**Задачи:**
1. Определи 5 ключевых тем проекта
2. Найди 3-5 похожих успешных проектов из базы
3. Выдели общие паттерны успеха
4. Дай рекомендации по позиционированию

**Требования к ответу:**

Верни ТОЛЬКО валидный JSON:

{{
    "key_themes": [
        "социальная поддержка",
        "молодёжь",
        "наставничество",
        "профориентация",
        "адаптация"
    ],
    "similar_grants": [
        {{
            "title": "Наставники будущего",
            "fund": "Фонд президентских грантов",
            "year": 2023,
            "amount": 1500000,
            "similarity_score": 85,
            "success_factors": [
                "Чёткая целевая аудитория",
                "Измеримые результаты",
                "Партнёрство с вузами"
            ],
            "key_differences": [
                "Фокус на студентах, а не на выпускниках"
            ]
        }},
        ...
    ],
    "success_patterns": [
        "Все успешные проекты имели партнёрства с государственными структурами",
        "Измеримые KPI были ключевым фактором",
        "Долгосрочная устойчивость проекта чётко описана"
    ],
    "positioning_recommendations": [
        "Подчеркнуть уникальность подхода к наставничеству",
        "Добавить больше количественных показателей эффективности",
        "Расширить географию реализации для повышения масштабируемости"
    ],
    "competitive_advantages": [
        "Инновационная методика наставничества",
        "Опыт команды в работе с молодёжью",
        "Партнёрство с 10+ организациями"
    ],
    "risks_from_analysis": [
        "Высокая конкуренция в теме молодёжной поддержки",
        "Необходимость отличаться от 15+ похожих проектов"
    ]
}}
"""


RESEARCHER_FUND_ANALYSIS_PROMPT = """
Проанализируй грантовый фонд и дай рекомендации.

Фонд: {fund_name}
Проект: {project_description}

Верни JSON с анализом:
{{
    "fund_priorities": ["тема 1", "тема 2"],
    "typical_budget_range": {{"min": 500000, "max": 2000000}},
    "success_rate": "15-20%",
    "key_criteria": ["...", "..."],
    "recommendations": ["...", "..."]
}}
"""


# =============================================================================
# CODE VALIDATION - Автоматические проверки
# =============================================================================

def generate_budget_validation_code(budget_data: Dict[str, Any]) -> str:
    """
    Генерирует Python код для валидации бюджета

    Args:
        budget_data: Данные бюджета для проверки

    Returns:
        Python код для выполнения через /code endpoint
    """
    return f"""
import json

# Данные бюджета
budget = {json.dumps(budget_data, ensure_ascii=False, indent=2)}

errors = []
warnings = []

# 1. Проверка суммы
total_calculated = sum(item['amount'] for item in budget['items'])
total_declared = budget.get('total', 0)

if abs(total_calculated - total_declared) > 0.01:
    errors.append({{
        'type': 'sum_mismatch',
        'severity': 'critical',
        'message': f'Сумма не сходится: заявлено {{total_declared:,.0f}}, рассчитано {{total_calculated:,.0f}}',
        'declared': total_declared,
        'calculated': total_calculated,
        'difference': total_calculated - total_declared
    }})

# 2. Проверка лимитов на отдельные статьи
max_item_cost = budget.get('max_item_cost', float('inf'))
for item in budget['items']:
    if item['amount'] > max_item_cost:
        errors.append({{
            'type': 'item_exceeds_limit',
            'severity': 'high',
            'message': f"{{item['name']}}: {{item['amount']:,.0f}} руб > лимит {{max_item_cost:,.0f}} руб",
            'item': item['name'],
            'amount': item['amount'],
            'limit': max_item_cost
        }})

# 3. Проверка обязательных категорий
required_categories = budget.get('required_categories', [])
present_categories = set(item.get('category', 'прочее') for item in budget['items'])

for cat in required_categories:
    if cat not in present_categories:
        warnings.append({{
            'type': 'missing_category',
            'severity': 'medium',
            'message': f'Отсутствует обязательная категория: {{cat}}',
            'category': cat
        }})

# 4. Проверка процентного соотношения категорий
if 'category_limits' in budget:
    category_totals = {{}}
    for item in budget['items']:
        cat = item.get('category', 'прочее')
        category_totals[cat] = category_totals.get(cat, 0) + item['amount']

    for cat, limit_pct in budget['category_limits'].items():
        if cat in category_totals:
            actual_pct = (category_totals[cat] / total_calculated) * 100 if total_calculated > 0 else 0
            if actual_pct > limit_pct:
                errors.append({{
                    'type': 'category_limit_exceeded',
                    'severity': 'high',
                    'message': f'{{cat}}: {{actual_pct:.1f}}% > лимит {{limit_pct}}%',
                    'category': cat,
                    'actual_percent': round(actual_pct, 2),
                    'limit_percent': limit_pct,
                    'amount': category_totals[cat]
                }})

# 5. Проверка минимальных сумм
min_total = budget.get('min_total', 0)
if total_calculated < min_total:
    warnings.append({{
        'type': 'below_minimum',
        'severity': 'medium',
        'message': f'Бюджет {{total_calculated:,.0f}} руб ниже минимума {{min_total:,.0f}} руб',
        'total': total_calculated,
        'minimum': min_total
    }})

# 6. Проверка на пустые/нулевые статьи
for item in budget['items']:
    if item['amount'] <= 0:
        warnings.append({{
            'type': 'zero_amount',
            'severity': 'low',
            'message': f"Статья '{{item['name']}}' имеет нулевую или отрицательную сумму",
            'item': item['name'],
            'amount': item['amount']
        }})

# Формирование результата
result = {{
    'valid': len(errors) == 0,
    'errors': errors,
    'warnings': warnings,
    'total_calculated': total_calculated,
    'total_declared': total_declared,
    'summary': {{
        'critical_errors': len([e for e in errors if e['severity'] == 'critical']),
        'high_errors': len([e for e in errors if e['severity'] == 'high']),
        'warnings': len(warnings)
    }}
}}

print(json.dumps(result, ensure_ascii=False, indent=2))
"""


BUDGET_VALIDATION_PROMPT = """
Проверь бюджет грантовой заявки на ошибки и несоответствия.

Бюджет: {budget_json}

Верни JSON с результатами проверки:
{{
    "valid": true/false,
    "errors": [...],
    "warnings": [...],
    "suggestions": [...]
}}
"""


# =============================================================================
# INTERVIEW ANALYSIS - Анализ интервью
# =============================================================================

INTERVIEW_ANALYSIS_PROMPT = """
Проанализируй полный диалог интервью для грантовой заявки.

Интервью содержит 24 вопроса о проекте и ответы заявителя.

**Полный текст интервью:**
{interview_transcript}

**Задачи:**
1. Выдели ключевые инсайты о проекте
2. Определи сильные стороны проекта
3. Найди пробелы и недостатки
4. Оцени общую готовность проекта к подаче заявки (0-100)
5. Дай конкретные рекомендации по приоритетам

**Требования к ответу:**

Верни ТОЛЬКО валидный JSON:

{{
    "key_insights": [
        "Проект направлен на социальную адаптацию молодёжи",
        "Планируется охватить 500+ человек за год",
        "Есть партнёрство с 3 вузами"
    ],
    "strengths": [
        "Чёткое понимание целевой аудитории",
        "Опыт команды в реализации похожих проектов",
        "Измеримые показатели эффективности"
    ],
    "gaps": [
        "Недостаточно проработан план управления рисками",
        "Не описана методика оценки результатов",
        "Отсутствует план устойчивости после гранта"
    ],
    "readiness_score": 75,
    "readiness_category": "хорошая готовность, требуется доработка",
    "missing_information": [
        "Детальный бюджет с обоснованием",
        "Конкретные сроки реализации",
        "План тиражирования опыта"
    ],
    "recommendations": [
        {{
            "priority": "high",
            "area": "риски",
            "suggestion": "Разработать детальную матрицу рисков с мерами реагирования",
            "impact": "Повысит оценку экспертов на 10-15%"
        }},
        {{
            "priority": "high",
            "area": "методология",
            "suggestion": "Описать конкретные инструменты оценки эффективности",
            "impact": "Сделает результаты более измеримыми"
        }},
        {{
            "priority": "medium",
            "area": "устойчивость",
            "suggestion": "Добавить план привлечения дополнительного финансирования",
            "impact": "Покажет долгосрочное видение"
        }}
    ],
    "next_steps": [
        "1. Разработать детальный бюджет с обоснованием каждой статьи",
        "2. Описать систему мониторинга и оценки результатов",
        "3. Создать план управления рисками",
        "4. Проработать стратегию устойчивости проекта"
    ],
    "estimated_grant_amount": "1000000-1500000 руб",
    "suitable_funds": [
        "Фонд президентских грантов (направление: поддержка молодёжи)",
        "Росмолодежь (конкурс молодёжных проектов)"
    ]
}}

Будь максимально конкретен и полезен.
"""


# =============================================================================
# GRANT TEXT IMPROVEMENT - Улучшение текстов
# =============================================================================

IMPROVE_TEXT_PROMPT = """
Улучши этот текст для грантовой заявки.

Тип раздела: {section_type}
Требования фонда: {fund_requirements}

Исходный текст:
{original_text}

Сделай текст:
- Более убедительным и профессиональным
- Конкретным (добавь цифры, факты)
- Структурированным
- Соответствующим требованиям фонда

Верни JSON:
{{
    "improved_text": "улучшенный текст...",
    "changes_made": ["добавлена статистика", "улучшена структура"],
    "remaining_issues": ["нужно больше конкретики в сроках"]
}}
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_project_data_for_evaluation(project: Dict[str, Any]) -> str:
    """
    Форматирует данные проекта для промпта оценки

    Args:
        project: Словарь с данными проекта

    Returns:
        Отформатированная строка для промпта
    """
    return json.dumps(project, ensure_ascii=False, indent=2)


def create_evaluation_prompt(project_data: Dict[str, Any]) -> str:
    """
    Создаёт промпт для оценки проекта

    Args:
        project_data: Данные проекта

    Returns:
        Готовый промпт
    """
    return AUDITOR_EVALUATION_PROMPT.format(
        project_data=format_project_data_for_evaluation(project_data)
    )


def create_structure_prompt(
    project_description: str,
    fund_name: str,
    fund_requirements: str
) -> str:
    """
    Создаёт промпт для структурирования заявки

    Args:
        project_description: Описание проекта
        fund_name: Название фонда
        fund_requirements: Требования фонда

    Returns:
        Готовый промпт
    """
    return PLANNER_STRUCTURE_PROMPT.format(
        project_description=project_description,
        fund_name=fund_name,
        fund_requirements=fund_requirements
    )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    # Auditor prompts
    'AUDITOR_EVALUATION_PROMPT',
    'AUDITOR_QUICK_SCORE_PROMPT',

    # Planner prompts
    'PLANNER_STRUCTURE_PROMPT',
    'PLANNER_SECTION_PROMPT',

    # Researcher prompts
    'RESEARCHER_ANALYSIS_PROMPT',
    'RESEARCHER_FUND_ANALYSIS_PROMPT',

    # Validation
    'generate_budget_validation_code',
    'BUDGET_VALIDATION_PROMPT',

    # Interview
    'INTERVIEW_ANALYSIS_PROMPT',

    # Text improvement
    'IMPROVE_TEXT_PROMPT',

    # Helpers
    'create_evaluation_prompt',
    'create_structure_prompt',
    'format_project_data_for_evaluation',
]
