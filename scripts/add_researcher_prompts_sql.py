#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "web-admin"))

from utils.prompt_manager import save_prompt

# 2. Market Analysis Prompt
save_prompt(
    agent_name='researcher',
    prompt_type='market_analysis',
    prompt_text="""Проведи анализ рынка для проекта на основе найденных данных:

{research_data}

Проанализируй и структурируй:
1. **Размер рынка** - текущий объем и прогноз роста
2. **Ключевые тренды** - что происходит в отрасли
3. **Конкуренты** - кто уже работает в этой области
4. **Возможности** - где есть пространство для роста
5. **Риски** - потенциальные проблемы и вызовы

Формат ответа:
```
## Размер рынка
[объем, динамика, прогнозы]

## Ключевые тренды
[тренды с пояснениями]

## Конкурентный анализ
[основные игроки, их преимущества]

## Рыночные возможности
[ниши, потенциал]

## Риски
[угрозы и как их минимизировать]
```""",
    prompt_key='researcher_market_analysis',
    description='Анализ рынка на основе результатов веб-поиска',
    variables={'research_data': 'string'},
    llm_provider='gigachat',
    model='GigaChat-Pro',
    temperature=0.5,
    max_tokens=3000,
    is_default=True,
    updated_by='system'
)

# 3. Grant Search Prompt
save_prompt(
    agent_name='researcher',
    prompt_type='grant_search',
    prompt_text="""Найди актуальные грантовые программы для проекта:

{project_description}

**Область проекта:** {project_area}
**Бюджет:** {budget_range}

Используй веб-поиск и найди:
1. **Российские гранты** (президентские, молодежные, региональные)
2. **Международные программы** (если применимо)
3. **Корпоративные гранты** от компаний
4. **Требования** к заявкам для каждого гранта
5. **Сроки подачи** заявок

Для каждого гранта укажи:
- Название программы
- Организатор
- Максимальная сумма
- Основные требования
- Дедлайн
- Ссылка на официальный сайт

Формат ответа:
```
## Президентские гранты
[список с деталями]

## Молодежные программы
[список с деталями]

## Корпоративные гранты
[список с деталями]

## Рекомендации
[какие гранты наиболее подходят и почему]
```""",
    prompt_key='researcher_grant_search_claude',
    description='Поиск подходящих грантовых программ через Claude Code',
    variables={'project_description': 'string', 'project_area': 'string', 'budget_range': 'string'},
    llm_provider='claude_code',
    model='claude-3.5-sonnet',
    temperature=0.2,
    max_tokens=3500,
    is_default=True,
    updated_by='system'
)

print("Done")
