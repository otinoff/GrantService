#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load Researcher Agent prompts to database"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-admin"))

from utils.prompt_manager import save_prompt

def main():
    print("=" * 70)
    print("Loading Researcher Agent Prompts")
    print("=" * 70)

    # 1. Web Search Prompt (Claude Code default)
    web_search_prompt = """Проведи веб-поиск по теме проекта и собери актуальную информацию:

{project_description}

Найди и проанализируй:
1. **Похожие проекты и стартапы** в этой области
2. **Статистику рынка** - размер, тренды, прогнозы роста
3. **Целевую аудиторию** и ее потребности
4. **Актуальные новости** за последние 3 месяца
5. **Грантовые программы** подходящие для этого проекта

Дай структурированный отчет с конкретными фактами, цифрами и ссылками на источники.
Формат ответа:
```
## Похожие проекты
[список с описанием]

## Статистика рынка
[данные с источниками]

## Целевая аудитория
[анализ]

## Актуальные новости
[последние события]

## Грантовые программы
[подходящие гранты]

## Источники
[список ссылок]
```
"""

    result1 = save_prompt(
        agent_name='researcher',
        prompt_type='web_search',
        prompt_text=web_search_prompt,
        prompt_key='researcher_web_search_claude',
        description='Веб-поиск через Claude Code WebSearch tool для сбора актуальной информации о проекте',
        variables={'project_description': 'string'},
        llm_provider='claude_code',
        model='claude-3.5-sonnet',
        temperature=0.3,
        max_tokens=4000,
        is_default=True,
        updated_by='system'
    )

    if result1:
        print(f"✅ Loaded: researcher_web_search_claude (ID: {result1})")
    else:
        print("❌ Failed to load web_search prompt")

    # 2. Market Analysis Prompt (GigaChat)
    market_analysis_prompt = """Проведи анализ рынка для проекта на основе найденных данных:

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
```
"""

    result2 = save_prompt(
        agent_name='researcher',
        prompt_type='market_analysis',
        prompt_text=market_analysis_prompt,
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

    if result2:
        print(f"✅ Loaded: researcher_market_analysis (ID: {result2})")
    else:
        print("❌ Failed to load market_analysis prompt")

    # 3. Grant Search Prompt (Claude Code)
    grant_search_prompt = """Найди актуальные грантовые программы для проекта:

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
```
"""

    result3 = save_prompt(
        agent_name='researcher',
        prompt_type='grant_search',
        prompt_text=grant_search_prompt,
        prompt_key='researcher_grant_search_claude',
        description='Поиск подходящих грантовых программ через Claude Code',
        variables={
            'project_description': 'string',
            'project_area': 'string',
            'budget_range': 'string'
        },
        llm_provider='claude_code',
        model='claude-3.5-sonnet',
        temperature=0.2,
        max_tokens=3500,
        is_default=True,
        updated_by='system'
    )

    if result3:
        print(f"✅ Loaded: researcher_grant_search_claude (ID: {result3})")
    else:
        print("❌ Failed to load grant_search prompt")

    print("\n" + "=" * 70)
    print("Researcher prompts loaded successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()
