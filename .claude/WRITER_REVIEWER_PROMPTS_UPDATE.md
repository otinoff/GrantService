# Обновление Промптов Writer V2 и Reviewer

**Дата**: 2025-10-09
**Основа**: Анализ 3 реальных успешных заявок на Президентские гранты

---

## 📌 Summary of Changes

### Critical Priority (Must Implement):
1. ✅ **Раздел "Проблема"** - расширить с 1-2 абзацев до 2-4 страниц
2. ✅ **Все статистические данные** из research_results использовать
3. ✅ **Формат цитирования** - изменить на официальный стиль
4. ✅ **Календарный план** - добавить генерацию таблицы

### High Priority (Should Implement):
5. ✅ **Официальный стиль** - третье лицо, бюрократический язык
6. ✅ **Количественные результаты** - только точные цифры
7. ✅ **Качественные результаты** - с методами измерения

---

## 🔄 WRITER V2 - STAGE 1 (Planning) UPDATES

### Current Planning Prompt (Lines 222-265):

```python
planning_prompt = f"""Ты эксперт по написанию грантовых заявок. Твоя задача - спланировать структуру заявки.

ПРОЕКТ:
Название: {user_answers.get('project_name', 'Проект')}
Описание: {user_answers.get('description', 'Описание проекта')}

РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ (27 запросов):
Блок 1 - Проблема: {block1_summary[:500]}...
Блок 2 - География: {block2_summary[:500]}...
Блок 3 - Цели и задачи: {block3_summary[:500]}...

Всего источников: {metadata.get('sources_count', 0)}
Всего цитат: {metadata.get('quotes_count', 0)}

ТРЕБОВАНИЯ К ЗАЯВКЕ:
- Минимум 15,000 символов
- Минимум 10 прямых цитат с источниками
- Минимум 2 сравнительные таблицы
- Использование всех 3 блоков исследования
- Обязательное включение:
  * Официальной статистики (Росстат, министерства)
  * Ссылок на нацпроекты и госпрограммы
  * 3 успешных кейса
  * Сравнение региона с РФ и лидером

ЗАДАЧА:
Создай план структуры грантовой заявки (5-7 разделов) с указанием:
1. Название раздела
2. Ключевые элементы (что включить)
3. Какие данные из исследования использовать
4. Где вставить цитаты и таблицы

Ответ дай в формате JSON:
{
  "sections": [
    {
      "name": "Название раздела",
      "key_elements": ["элемент1", "элемент2"],
      "research_blocks": ["block1", "block2"],
      "citations_count": 2,
      "tables_count": 1
    }
  ],
  "total_citations": 10,
  "total_tables": 2,
  "estimated_length": 15000
}
"""
```

### ✅ UPDATED Planning Prompt:

```python
planning_prompt = f"""Ты эксперт по написанию заявок на Президентские гранты РФ. Твоя задача - спланировать структуру заявки согласно официальной форме ФПГ.

КОНТЕКСТ ПРОЕКТА:
Название: {user_answers.get('project_name', 'Проект')}
Описание: {user_answers.get('description', 'Описание проекта')}
Проблема: {user_answers.get('problem', '')}
Решение: {user_answers.get('solution', '')}
Бюджет: {user_answers.get('budget', '1,000,000')} рублей
Срок реализации: {user_answers.get('timeline', '12')} месяцев
Целевая группа: {user_answers.get('target_group', '')}
География: {user_answers.get('geography', '')}

РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ (27 запросов):
Блок 1 - Проблема: {block1_summary[:800]}...
Блок 2 - География: {block2_summary[:800]}...
Блок 3 - Цели и задачи: {block3_summary[:800]}...

Статистика:
- Всего источников: {metadata.get('sources_count', 0)}
- Всего цитат и данных: {metadata.get('quotes_count', 0)}
- Ключевые факты о проблеме: {len(research_results.get('block1_problem', {}).get('key_facts', []))}
- Федеральные программы найдены: {len(research_results.get('block1_problem', {}).get('programs', []))}
- Успешные кейсы найдены: {len(research_results.get('block1_problem', {}).get('success_cases', []))}

СТРУКТУРА ЗАЯВКИ НА ПРЕЗИДЕНТСКИЙ ГРАНТ:
Заявка должна следовать официальной форме ФПГ (Фонд Президентских Грантов) и включать:

ОБЯЗАТЕЛЬНЫЕ РАЗДЕЛЫ:

1. **КРАТКОЕ ОПИСАНИЕ ПРОЕКТА** (0.5-1 страница)
   - Суть проекта в 2-3 абзацах
   - Целевая группа
   - География
   - Ключевые мероприятия

2. **ОБОСНОВАНИЕ СОЦИАЛЬНОЙ ЗНАЧИМОСТИ** / **ОПИСАНИЕ ПРОБЛЕМЫ** (2-4 страницы) ⚠️ САМЫЙ ВАЖНЫЙ РАЗДЕЛ
   Должен содержать:
   - Официальную статистику с точными цифрами (Росстат, министерства, ВОЗ, ВЦИОМ)
   - Прямые ссылки на источники в формате "(ссылка: https://...)"
   - Упоминание федеральных/национальных проектов с целевыми показателями
   - Региональный контекст (специфика местности, демография)
   - Статистику по целевой группе
   - Исследования и опросы
   - Реальные кейсы и примеры
   - Использовать ВСЕ key_facts из block1_problem
   - Включить dynamics_table с динамикой показателей
   - Включить comparison_table с сравнением региона

3. **ЦЕЛЬ ПРОЕКТА** (1 абзац)
   - Конкретная, измеримая цель (SMART)
   - С указанием точных цифр из user_answers

4. **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ**
   - **Целевые группы**: список из user_answers
   - **Количественные результаты**: bullet list с ТОЧНЫМИ цифрами (из user_answers)
   - **Качественные результаты**: с указанием способов измерения (опросы, отзывы, фиксация персоналом)

5. **ЗАДАЧИ ПРОЕКТА** (3-5 пунктов)
   - Конкретные, действенные задачи
   - Соответствуют мероприятиям календарного плана

6. **ПАРТНЕРЫ ПРОЕКТА**
   - Использовать programs из block1_problem как основу для партнеров
   - Типы поддержки: Информационная, Организационная, Материальная, Консультационная

7. **ИНФОРМАЦИОННОЕ СОПРОВОЖДЕНИЕ**
   - Конкретные площадки (соцсети, СМИ, сайты партнеров)
   - Количество публикаций

8. **ДАЛЬНЕЙШЕЕ РАЗВИТИЕ ПРОЕКТА**
   - Планы после гранта

9. **КАЛЕНДАРНЫЙ ПЛАН** ⚠️ ОБЯЗАТЕЛЬНАЯ ТАБЛИЦА
   - 4-8 строк (по числу задач)
   - Каждая строка: Задача | Мероприятие | Даты | Результат

ТРЕБОВАНИЯ К ОБЪЕМУ И КАЧЕСТВУ:
- Общий объем: 20-30 страниц (с учетом всех разделов)
- Раздел "Проблема": 2-4 страницы (самый большой)
- Официальная статистика: минимум 5-10 источников
- Конкретные цифры в разделе "Проблема": минимум 10-15 числовых данных
- Прямые цитаты: минимум 10
- Таблицы сравнения: минимум 2
- Стиль: официальный, бюрократический, третье лицо

ЗАДАЧА:
Создай детальный план структуры заявки, включая:
1. Краткое описание (что писать)
2. Обоснование проблемы (ДЕТАЛЬНЫЙ ПЛАН на 2-4 страницы)
3. Цель проекта (формулировка)
4. Результаты (количественные + качественные с методами измерения)
5. Задачи (3-5 пунктов)
6. Партнеры (из programs)
7. Информационное сопровождение
8. Дальнейшее развитие
9. КАЛЕНДАРНЫЙ ПЛАН (таблица 4-8 строк)

Особое внимание к разделу "Описание проблемы" - распиши подробно:
- Какие key_facts использовать (ВСЕ из block1_problem)
- Какие programs упомянуть с целевыми показателями
- Какие success_cases включить
- Где разместить dynamics_table
- Где разместить comparison_table
- Как структурировать 2-4 страницы текста

Ответ дай в формате JSON:
{{
  "section_1_brief": {{
    "content_plan": "Что включить в краткое описание",
    "length_chars": 2000
  }},
  "section_2_problem": {{
    "subsections": [
      {{
        "title": "Федеральный контекст",
        "content_plan": "Нацпроекты, федеральные программы, целевые показатели",
        "key_facts_indices": [0, 1, 2],
        "programs_indices": [0, 1],
        "citations_count": 3
      }},
      {{
        "title": "Региональная специфика",
        "content_plan": "Статистика региона, comparison_table",
        "key_facts_indices": [3, 4, 5],
        "tables": ["comparison_table"],
        "citations_count": 2
      }},
      {{
        "title": "Целевая группа",
        "content_plan": "Демография, проблемы, потребности",
        "key_facts_indices": [6, 7, 8],
        "citations_count": 2
      }},
      {{
        "title": "Динамика проблемы",
        "content_plan": "Динамика показателей, тренды",
        "key_facts_indices": [9, 10, 11],
        "tables": ["dynamics_table"],
        "citations_count": 3
      }},
      {{
        "title": "Успешный опыт",
        "content_plan": "Success cases как доказательства",
        "success_cases_indices": [0, 1, 2],
        "citations_count": 0
      }}
    ],
    "total_length_chars": 8000,
    "total_citations": 10,
    "total_tables": 2
  }},
  "section_3_goal": {{
    "goal_text": "Формулировка цели с точными цифрами"
  }},
  "section_4_results": {{
    "quantitative": [
      "Результат 1 с точной цифрой",
      "Результат 2 с точной цифрой"
    ],
    "qualitative": [
      {{
        "result": "Качественный результат",
        "measurement": "Способ измерения (опрос, отзывы, фиксация)"
      }}
    ]
  }},
  "section_5_tasks": [
    "Задача 1",
    "Задача 2",
    "Задача 3"
  ],
  "section_6_partners": [
    {{
      "name": "Название партнера из programs",
      "support_types": ["Информационная", "Организационная"]
    }}
  ],
  "section_7_info_support": "План информационного сопровождения",
  "section_8_future": "Дальнейшее развитие",
  "section_9_calendar": {{
    "rows": [
      {{
        "task_number": 1,
        "task_from_section_5": "Задача 1",
        "event_description": "Подробное описание мероприятия",
        "start_date": "01.03.2025",
        "end_date": "31.03.2025",
        "expected_result": "Конкретный результат с цифрами"
      }}
    ]
  }},
  "total_estimated_chars": 25000,
  "style_notes": "Официальный, третье лицо, бюрократический"
}}
"""
```

---

## ✍️ WRITER V2 - STAGE 2 (Writing) UPDATES

### Current Writing Prompt (Lines 356-450):

```python
writing_prompt = f"""Ты профессиональный грант-райтер. Напиши полную заявку на грант.

ПРОЕКТ:
Название: {user_answers.get('project_name', 'Проект')}
Описание: {user_answers.get('description', '')}
Проблема: {user_answers.get('problem', '')}
Решение: {user_answers.get('solution', '')}
Бюджет: {user_answers.get('budget', '1,000,000')} рублей
Срок: {user_answers.get('timeline', '12')} месяцев

ПЛАН СТРУКТУРЫ:
{json.dumps(plan, ensure_ascii=False, indent=2)}

ЦИТАТЫ ДЛЯ ИСПОЛЬЗОВАНИЯ (минимум 10):
{citations_text}

ТАБЛИЦЫ ДЛЯ ВКЛЮЧЕНИЯ (минимум 2):
{tables_text}

БЛОК 1 - ПРОБЛЕМА:
{block1.get('summary', '')[:1000]}

Ключевые факты:
{json.dumps(block1.get('key_facts', [])[:5], ensure_ascii=False, indent=2)}

...
```

### ✅ UPDATED Writing Prompt:

```python
writing_prompt = f"""Ты профессиональный грант-райтер с 15-летним опытом написания заявок на Президентские гранты РФ.

Твоя задача - написать полную заявку на грант, строго следуя официальной форме ФПГ (Фонд Президентских Грантов).

СТИЛЬ НАПИСАНИЯ (КРИТИЧНО ВАЖНО):
- ✅ Официальный, деловой, бюрократический стиль
- ✅ Третье лицо ВСЕГДА ("проект направлен на...", "планируется...", "будет проведено...")
- ✅ НЕТ первого лица ("мы", "наш", "наша команда")
- ✅ Длинные, сложные предложения с вводными конструкциями
- ✅ Безэмоциональный тон (только факты, цифры, ссылки)
- ✅ Использование аббревиатур (ВОЗ, ВЦИОМ, МинЗдрав, Росстат, ЕГРЮЛ и т.д.)
- ✅ Академический/научный подход

ФОРМАТ ЦИТИРОВАНИЯ (СТРОГО ОБЯЗАТЕЛЬНО):
Все статистические данные и факты оформляй так:
"По данным [организация] [факт с точными цифрами]. [Вывод или рекомендация] (ссылка: https://полная-ссылка-на-источник)."

Примеры правильного цитирования:
- "По данным всемирной организации здравоохранения актуален вопрос снижения уровня физического воспитания молодежи, Россия находится по данному показателю на 98 месте (ссылка: https://tass.ru/obschestvo/7176407)."
- "Согласно исследованию фонда "Общественное мнение" 11% опрошенных школьников воспринимают физкультуру, как "тяжёлую обязанность"."
- "По плану федерального проекта «Спорт – норма жизни» (в рамках нацпроекта «Демография») доля детей и молодежи (возраст 3—29 лет), систематически занимающихся физкультурой и спортом, должна составить 86% к 2024 году."

ДАННЫЕ ПРОЕКТА:
Название: {user_answers.get('project_name', 'Проект')}
Описание: {user_answers.get('description', '')}
Проблема: {user_answers.get('problem', '')}
Решение: {user_answers.get('solution', '')}
Целевая группа: {user_answers.get('target_group', '')}
География: {user_answers.get('geography', '')}
Бюджет: {user_answers.get('budget', '1,000,000')} рублей
Срок реализации: {user_answers.get('timeline', '12')} месяцев

ПЛАН СТРУКТУРЫ (из Stage 1):
{json.dumps(plan, ensure_ascii=False, indent=2)}

ЦИТАТЫ И ИСТОЧНИКИ (минимум 10 использовать):
{citations_text}

ТАБЛИЦЫ (минимум 2 включить):
{tables_text}

БЛОК 1 - ПРОБЛЕМА (Использовать ВСЕ данные):
Резюме: {block1.get('summary', '')}

Ключевые факты (ИСПОЛЬЗОВАТЬ ВСЕ):
{json.dumps(block1.get('key_facts', []), ensure_ascii=False, indent=2)}

Динамика показателей:
{json.dumps(block1.get('dynamics_table', {}), ensure_ascii=False, indent=2)}

Федеральные программы и нацпроекты:
{json.dumps(block1.get('programs', []), ensure_ascii=False, indent=2)}

Успешные кейсы:
{json.dumps(block1.get('success_cases', []), ensure_ascii=False, indent=2)}

БЛОК 2 - ГЕОГРАФИЯ:
Резюме: {block2.get('summary', '')}

Ключевые факты о регионе:
{json.dumps(block2.get('key_facts', []), ensure_ascii=False, indent=2)}

Сравнительная таблица (регион vs РФ vs лидер):
{json.dumps(block2.get('comparison_table', {}), ensure_ascii=False, indent=2)}

Целевая аудитория:
{json.dumps(block2.get('target_audience', {}), ensure_ascii=False, indent=2)}

БЛОК 3 - ЦЕЛИ И ЗАДАЧИ:
Резюме: {block3.get('summary', '')}

Основные задачи:
{json.dumps(block3.get('key_tasks', []), ensure_ascii=False, indent=2)}

Варианты целей (с SMART-проверкой):
{json.dumps(block3.get('main_goal_variants', []), ensure_ascii=False, indent=2)}

ЗАДАНИЕ:
Напиши полную заявку на грант, включающую ВСЕ разделы согласно плану:

1. КРАТКОЕ ОПИСАНИЕ ПРОЕКТА (0.5-1 страница, ~2000 символов)
   - Суть проекта (2-3 абзаца, третье лицо)
   - Целевая группа и география
   - Ключевые мероприятия

2. ОБОСНОВАНИЕ СОЦИАЛЬНОЙ ЗНАЧИМОСТИ / ОПИСАНИЕ ПРОБЛЕМЫ (2-4 страницы, ~8000 символов) ⚠️ САМЫЙ ВАЖНЫЙ РАЗДЕЛ

   СТРУКТУРА РАЗДЕЛА ПРОБЛЕМЫ:

   Подраздел 1: Федеральный контекст (1 страница)
   - Используй ВСЕ relevant key_facts из block1
   - Включи ВСЕ programs с упоминанием целевых показателей
   - Формат: "По данным [программа] к [год] планируется достичь [показатель]"
   - Минимум 3 цитаты с прямыми ссылками

   Подраздел 2: Региональная специфика (0.5-1 страница)
   - Используй key_facts из block2
   - ОБЯЗАТЕЛЬНО включи comparison_table
   - Формат таблицы: "Сравнение показателей:\n| Показатель | Регион | РФ | Лидер |\n..."
   - Минимум 2 цитаты о регионе

   Подраздел 3: Целевая группа (0.5 страницы)
   - Демография из target_audience
   - Специфические проблемы целевой группы
   - Минимум 2 цитаты

   Подраздел 4: Динамика проблемы (0.5 страницы)
   - ОБЯЗАТЕЛЬНО включи dynamics_table
   - Формат таблицы: "Динамика показателя:\n| Год | Значение | Изменение |\n..."
   - Тренды и прогнозы
   - Минимум 2-3 цитаты

   Подраздел 5: Успешный опыт решения (0.5 страницы)
   - Включи ВСЕ success_cases
   - Формат: Название кейса, место, результаты
   - Без прямых цитат (это примеры)

   ⚠️ КРИТИЧНО: Раздел "Проблема" должен быть 8000+ символов с 10+ цитатами и 2 таблицами

3. ЦЕЛЬ ПРОЕКТА (1 абзац, ~500 символов)
   - Используй вариант цели из block3.main_goal_variants с высоким SMART-score
   - Добавь точные цифры из user_answers (количество благополучателей, мероприятий)
   - Формат: "[Действие] через [методы] в [география], охватив [количество] [целевая группа] за [срок]"

4. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ (1 страница, ~2500 символов)

   4.1 Целевые группы:
   Bullet list из user_answers.target_group

   4.2 Количественные результаты:
   - Только ТОЧНЫЕ цифры из user_answers
   - Формат: "• Количество [что]: [число]"
   - Минимум 5 пунктов
   - Примеры:
     * Количество благополучателей: [точная цифра]
     * Количество проведенных мероприятий: [точная цифра]
     * Количество публикаций в СМИ: [точная цифра]

   4.3 Качественные результаты и способы их измерения:
   - НЕ просто "улучшится" или "повысится"
   - ОБЯЗАТЕЛЬНО указать метод измерения
   - Формат: "[Результат]. Способ измерения: [конкретный метод]"
   - Примеры методов измерения:
     * "Входной и выходной опрос участников проекта"
     * "Отзывы родителей в социальных сетях и на сайте"
     * "Фиксирует тренерский состав, команда проекта"
     * "Онлайн-опрос персонала до и после реализации проекта"
     * "Мониторинг публикаций в СМИ"
   - Минимум 3 качественных результата с методами измерения

5. ЗАДАЧИ ПРОЕКТА (0.5 страницы, ~1000 символов)
   - Используй key_tasks из block3
   - 3-5 конкретных, действенных задач
   - Формат: bullet list, начинается с глагола в инфинитиве
   - Каждая задача соответствует разделу календарного плана

6. ПАРТНЕРЫ ПРОЕКТА (0.5 страницы, ~1000 символов)
   - Извлеки организации из block1.programs как потенциальных партнеров
   - Для каждого партнера укажи:
     * Название организации (официальное)
     * Типы поддержки: Информационная, Организационная, Материальная, Консультационная
   - Формат: "[Название]. Тип поддержки: [типы]."
   - Упомяни, что письма поддержки прилагаются (если применимо)

7. ИНФОРМАЦИОННОЕ СОПРОВОЖДЕНИЕ (0.3 страницы, ~800 символов)
   - Конкретные площадки: соцсети (ВКонтакте, Telegram), сайт организации, сайты партнеров
   - Количество публикаций: точные цифры
   - Формат видео-контента (если применимо)
   - Охват аудитории (если известен)

8. ДАЛЬНЕЙШЕЕ РАЗВИТИЕ ПРОЕКТА (0.3 страницы, ~800 символов)
   - Планы масштабирования (другие территории, целевые группы)
   - Источники финансирования после гранта
   - Самоокупаемость (если применимо)

9. КАЛЕНДАРНЫЙ ПЛАН (таблица, ~2000 символов)
   - Формат Markdown таблицы:

   | № | Решаемая задача | Мероприятие | Дата начала | Дата окончания | Ожидаемые результаты |
   |---|----------------|-------------|-------------|----------------|---------------------|
   | 1 | [Задача из п.5] | [Подробное описание мероприятия с местом проведения] | [дд.мм.гггг] | [дд.мм.гггг] | [Конкретный результат с точными цифрами] |

   - 4-8 строк (по числу задач из раздела 5)
   - Каждая задача = отдельная строка
   - Распределить timeline из user_answers по задачам
   - В результатах использовать количественные показатели

ТРЕБОВАНИЯ К ФИНАЛЬНОМУ ТЕКСТУ:
✅ Общий объем: 25,000+ символов (20-30 страниц)
✅ Раздел "Проблема": 8,000+ символов (2-4 страницы)
✅ Официальный стиль, третье лицо, длинные предложения
✅ Минимум 10 прямых цитат в формате "По данным... (ссылка: https://...)"
✅ 2 таблицы обязательно (comparison_table и dynamics_table)
✅ Все цифры точные (из user_answers)
✅ Качественные результаты с методами измерения
✅ Календарный план в формате таблицы
✅ Аббревиатуры (ВОЗ, ВЦИОМ, МинЗдрав, РосСтат и т.д.)

Верни результат в формате JSON:
{{
  "section_1_brief": "Текст раздела 1...",
  "section_2_problem": "Текст раздела 2 (2-4 страницы)...",
  "section_3_goal": "Текст раздела 3...",
  "section_4_results": "Текст раздела 4...",
  "section_5_tasks": "Текст раздела 5...",
  "section_6_partners": "Текст раздела 6...",
  "section_7_info": "Текст раздела 7...",
  "section_8_future": "Текст раздела 8...",
  "section_9_calendar": "Текст календарного плана (таблица Markdown)...",
  "metadata": {{
    "total_chars": 25000,
    "citations_used": 12,
    "tables_included": 2,
    "style_check": "official_third_person"
  }}
}}
"""
```

---

## 🎯 REVIEWER UPDATES

### Current Reviewer Criteria:

1. **Evidence Base (40%)**: Citations, tables, sources
2. **Structure (30%)**: Sections, length, metadata
3. **Matching (20%)**: SMART goals, KPI, alignment
4. **Economics (10%)**: Budget details

### ✅ UPDATED Reviewer Criteria:

#### 1. Evidence Base (40%) - Add Checks:

```python
# New checks to add in _evaluate_evidence_base_async()

problem_section_checks = {
    "section_8_length": len(grant_content.get('section_2_problem', '')) >= 8000,  # 2-4 pages
    "official_statistics": count_sources(grant_content.get('section_2_problem', '')) >= 5,
    "concrete_numbers": count_numbers(grant_content.get('section_2_problem', '')) >= 10,
    "direct_links": count_links_with_format(grant_content.get('section_2_problem', ''), r'\(ссылка: https://') >= 5,
    "federal_programs": contains_keywords(grant_content.get('section_2_problem', ''),
                                          ['нацпроект', 'федеральная программа', 'федеральный проект']),
    "regional_context": contains_keywords(grant_content.get('section_2_problem', ''),
                                         ['область', 'регион', 'территория', 'муниципальн']),
    "comparison_table_included": 'comparison_table' in grant_content.get('section_2_problem', '') or
                                'Сравнение показателей' in grant_content.get('section_2_problem', ''),
    "dynamics_table_included": 'dynamics_table' in grant_content.get('section_2_problem', '') or
                              'Динамика показател' in grant_content.get('section_2_problem', ''),
}

# Evidence score calculation update:
evidence_score = (
    (problem_section_checks['section_8_length'] * 2) +  # Critical: 2 points
    (problem_section_checks['official_statistics'] * 2) +  # Critical: 2 points
    (problem_section_checks['concrete_numbers'] * 1) +
    (problem_section_checks['direct_links'] * 1) +
    (problem_section_checks['federal_programs'] * 1) +
    (problem_section_checks['regional_context'] * 1) +
    (problem_section_checks['comparison_table_included'] * 1) +
    (problem_section_checks['dynamics_table_included'] * 1)
) / 10 * 10  # Convert to 0-10 scale
```

#### 2. Structure (30%) - Add Checks:

```python
# New checks to add in _evaluate_structure_async()

fpg_form_checks = {
    "section_1_brief": 'section_1_brief' in grant_content and len(grant_content.get('section_1_brief', '')) >= 1500,
    "section_2_problem": 'section_2_problem' in grant_content and len(grant_content.get('section_2_problem', '')) >= 7000,
    "section_3_goal": 'section_3_goal' in grant_content and len(grant_content.get('section_3_goal', '')) >= 300,
    "section_4_results": 'section_4_results' in grant_content and 'Количественные результаты' in grant_content.get('section_4_results', ''),
    "section_5_tasks": 'section_5_tasks' in grant_content and len(grant_content.get('section_5_tasks', '').split('•')) >= 3,
    "section_6_partners": 'section_6_partners' in grant_content,
    "section_7_info": 'section_7_info' in grant_content,
    "section_8_future": 'section_8_future' in grant_content,
    "section_9_calendar": 'section_9_calendar' in grant_content and '|' in grant_content.get('section_9_calendar', ''),  # Markdown table

    "quantitative_exact_numbers": all([
        char.isdigit() for part in grant_content.get('section_4_results', '').split('Количественные')[1].split('Качественные')[0].split()
        if any(c.isdigit() for c in part)
    ]) if 'Количественные' in grant_content.get('section_4_results', '') else False,

    "qualitative_with_measurement": (
        'измерения' in grant_content.get('section_4_results', '').lower() or
        'опрос' in grant_content.get('section_4_results', '').lower() or
        'фиксирует' in grant_content.get('section_4_results', '').lower() or
        'отзывы' in grant_content.get('section_4_results', '').lower()
    ),

    "calendar_table_present": '|' in grant_content.get('section_9_calendar', ''),
    "calendar_rows_count": len([line for line in grant_content.get('section_9_calendar', '').split('\n') if line.startswith('|') and not line.startswith('|---|')]) >= 4,
}

# Structure score calculation:
structure_score = sum([
    fpg_form_checks['section_1_brief'] * 0.5,
    fpg_form_checks['section_2_problem'] * 2,  # Most important
    fpg_form_checks['section_3_goal'] * 0.5,
    fpg_form_checks['section_4_results'] * 1,
    fpg_form_checks['section_5_tasks'] * 0.5,
    fpg_form_checks['section_6_partners'] * 0.5,
    fpg_form_checks['section_7_info'] * 0.5,
    fpg_form_checks['section_8_future'] * 0.5,
    fpg_form_checks['section_9_calendar'] * 1.5,  # Important
    fpg_form_checks['quantitative_exact_numbers'] * 1,
    fpg_form_checks['qualitative_with_measurement'] * 1,
    fpg_form_checks['calendar_table_present'] * 0.5,
    fpg_form_checks['calendar_rows_count'] * 0.5,
]) / 10 * 10  # Convert to 0-10 scale
```

#### 3. Style Check (NEW sub-criterion under Structure):

```python
# New function to add in reviewer_agent.py

def _evaluate_style(self, grant_content: Dict) -> Dict[str, Any]:
    """Проверка стиля написания (официальный, третье лицо)"""

    full_text = ' '.join([
        grant_content.get('section_1_brief', ''),
        grant_content.get('section_2_problem', ''),
        grant_content.get('section_3_goal', ''),
        grant_content.get('section_4_results', ''),
        grant_content.get('section_5_tasks', ''),
    ])

    style_checks = {
        "official_tone": True,  # Would need NLP analysis
        "third_person": not any(word in full_text.lower() for word in ['мы ', ' мы', 'наш', 'наша', 'наше', 'нами']),
        "citation_format": full_text.count('(ссылка: https://') >= 5,
        "uses_abbreviations": any(abbr in full_text for abbr in ['ВОЗ', 'ВЦИОМ', 'МинЗдрав', 'РосСтат', 'ЕГРЮЛ', 'ГПХ']),
        "long_sentences": True,  # Would need sentence length analysis
        "no_exclamations": '!' not in full_text[:5000],  # Check first 5000 chars
        "data_driven": full_text.count('По данным') + full_text.count('Согласно') >= 5,
    }

    style_score = (
        (style_checks['third_person'] * 3) +  # Critical
        (style_checks['citation_format'] * 2) +  # Critical
        (style_checks['uses_abbreviations'] * 1) +
        (style_checks['no_exclamations'] * 1) +
        (style_checks['data_driven'] * 3)  # Critical
    ) / 10 * 10

    return {
        "score": style_score,
        "checks": style_checks,
        "comments": f"Стиль: {'Официальный ✅' if style_score >= 7 else 'Требует доработки ❌'}"
    }
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Writer V2 Updates (Priority 1 - Critical)
- [ ] Update Stage 1 planning prompt (lines 222-265)
- [ ] Update Stage 2 writing prompt (lines 356-450)
- [ ] Add calendar plan generation in Stage 1
- [ ] Expand problem section to use ALL key_facts
- [ ] Change citation format to official style
- [ ] Switch to third-person style

### Phase 2: Writer V2 Updates (Priority 2 - High)
- [ ] Add qualitative results with measurement methods
- [ ] Extract exact quantitative numbers from user_answers
- [ ] Add partner section from programs
- [ ] Add all 9 sections to output JSON

### Phase 3: Reviewer Updates
- [ ] Add problem section checks (8000+ chars, 10+ numbers, 5+ links)
- [ ] Add FPG form checks (9 required sections)
- [ ] Add style checker (third person, citation format)
- [ ] Update evidence_base scoring formula
- [ ] Update structure scoring formula

### Phase 4: Testing
- [ ] Run E2E tests on 5 test cases
- [ ] Compare with reference grants
- [ ] Measure approval_probability changes
- [ ] Collect feedback

### Phase 5: Iteration
- [ ] Review test results
- [ ] Adjust prompts based on feedback
- [ ] Re-run tests
- [ ] Finalize prompts

---

## 📊 EXPECTED IMPROVEMENTS

### Current Performance:
- Average readiness_score: 7.72/10
- Average approval_probability: 48.8%
- Problem section: 1-2 абзаца
- Style: Нейтральный, журналистский
- Structure: Свободная форма

### Expected Performance After Updates:
- Average readiness_score: 8.5-9.0/10 (+0.8-1.3)
- Average approval_probability: 52-58% (+3-9%)
- Problem section: 2-4 страницы с полной статистикой
- Style: Официальный, бюрократический, третье лицо
- Structure: Строгое следование форме ФПГ (9 разделов + календарный план)

---

**Конец документа**
**Дата**: 2025-10-09
**Статус**: Ready for Implementation
**Приоритет**: Critical (Phase 1), High (Phases 2-3)
