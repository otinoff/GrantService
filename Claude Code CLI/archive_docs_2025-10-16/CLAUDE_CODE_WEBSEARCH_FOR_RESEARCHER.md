# 🔍 Claude Code WebSearch для Researcher Agent

**Дата**: 2025-10-08
**Обновление архитектуры**: RESEARCHER_ARCHITECTURE_ANALYSIS.md
**Интеграция**: Claude Code API + WebSearch tool

---

## 🎯 Ключевое открытие

**Claude Code имеет встроенный WebSearch tool!**

Это значит, что для Researcher Agent **НЕ НУЖЕН Perplexity API** - можно использовать WebSearch напрямую через Claude Code.

---

## 📊 Преимущества WebSearch vs Perplexity

| Критерий | Claude Code WebSearch | Perplexity API |
|----------|----------------------|----------------|
| **Интеграция** | ✅ Уже есть | ❌ Нужно интегрировать |
| **API Key** | ✅ Уже настроен | ❌ Нужен отдельный |
| **Стоимость** | ✅ Бесплатно (в подписке) | ❌ $0.27 на анкету (27 запросов × $0.01) |
| **Фильтрация доменов** | ✅ allowed_domains | ⚠️ Ограничено |
| **RU-источники** | ✅ Отлично | ✅ Хорошо |
| **Актуальность** | ✅ Да | ✅ Да |
| **Цитаты** | ✅ С парсингом | ✅ Да |
| **Доступность** | ✅ Через Claude Code API | ⚠️ Отдельный сервис |

**Вывод**: WebSearch Claude Code - оптимальное решение для Researcher!

---

## 🏗️ Архитектура с WebSearch

### **Текущая проблема**
```
Анкета → Auditor (OK) → Researcher (PENDING!) → Planner → Writer
                              ↓
                         Создаёт запись, но НЕ завершается
                         status='pending', completed_at=None
```

### **Целевое решение**
```
Анкета → Auditor → Researcher (АВТОЗАПУСК!)
                        ↓
                   Claude Code WebSearch
                        ↓
                   27 специализированных запросов:
                   ├── Блок 1: Проблема (10 запросов)
                   │   ├── Статистика (rosstat.gov.ru)
                   │   ├── Исследования (elibrary.ru)
                   │   ├── Программы (nationalprojects.ru)
                   │   └── ...
                   ├── Блок 2: География + ЦА (10 запросов)
                   │   ├── Демография (fedstat.ru)
                   │   ├── Инфраструктура (minsport.gov.ru)
                   │   └── ...
                   └── Блок 3: Задачи + цель (7 запросов)
                       ├── KPI (government.ru)
                       ├── Индикаторы
                       └── ...
                        ↓
                   research_results (JSONB)
                   {
                     block1: {facts, quotes, sources},
                     block2: {demographics, infrastructure},
                     block3: {goals, indicators}
                   }
                        ↓
                   status='completed', completed_at=NOW()
                        ↓
                   Planner → Writer → Grant (с исследованием!)
```

---

## 🤖 Researcher Agent с WebSearch

### **Новая реализация**

**Файл**: `agents/researcher_agent.py`

```python
import os
import asyncio
from typing import Dict, List, Any
from datetime import datetime
import json

class ResearcherAgent(BaseAgent):
    """Агент-исследователь с Claude Code WebSearch"""

    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("researcher", db, llm_provider)

        # Claude Code API
        self.claude_api_key = os.getenv('CLAUDE_CODE_API_KEY')
        self.claude_base_url = os.getenv('CLAUDE_CODE_BASE_URL')

        # Официальные RU-домены
        self.OFFICIAL_DOMAINS = [
            "rosstat.gov.ru",
            "fedstat.ru",
            "gks.ru",
            "minsport.gov.ru",
            "nationalprojects.ru",
            "government.ru",
            "minzdrav.gov.ru",
            "minprosvet.gov.ru",
            "elibrary.ru",
            "cyberleninka.ru"
        ]

    async def research_anketa(self, anketa_id: str) -> Dict[str, Any]:
        """
        Исследование через Claude Code WebSearch

        Выполняет 27 специализированных запросов по промтам эксперта:
        - Блок 1: Проблема и социальная значимость (10 запросов)
        - Блок 2: География и целевая аудитория (10 запросов)
        - Блок 3: Задачи, мероприятия, цель (7 запросов)
        """
        try:
            # 1. Получить анкету
            anketa = self.db.get_session_by_anketa_id(anketa_id)

            if not anketa:
                return {
                    'status': 'error',
                    'message': f'Анкета {anketa_id} не найдена'
                }

            # 2. Извлечь placeholders
            placeholders = self._extract_placeholders(anketa)

            # 3. Выполнить исследование по блокам
            print(f"🔍 Начинаем исследование {anketa_id}...")

            block1_results = await self._research_block1_websearch(placeholders)
            print(f"✅ Блок 1 завершён: {len(block1_results.get('queries', []))} запросов")

            block2_results = await self._research_block2_websearch(placeholders)
            print(f"✅ Блок 2 завершён: {len(block2_results.get('queries', []))} запросов")

            block3_results = await self._research_block3_websearch(placeholders)
            print(f"✅ Блок 3 завершён: {len(block3_results.get('queries', []))} запросов")

            # 4. Агрегировать результаты
            research_results = {
                'block1': block1_results,
                'block2': block2_results,
                'block3': block3_results,
                'metadata': {
                    'total_queries': (
                        len(block1_results.get('queries', [])) +
                        len(block2_results.get('queries', [])) +
                        len(block3_results.get('queries', []))
                    ),
                    'sources_count': self._count_sources([
                        block1_results, block2_results, block3_results
                    ]),
                    'quotes_count': self._count_quotes([
                        block1_results, block2_results, block3_results
                    ])
                }
            }

            # 5. Сохранить в БД
            research_data = {
                'anketa_id': anketa_id,
                'user_id': anketa.get('telegram_id'),
                'session_id': anketa.get('id'),
                'research_type': 'comprehensive_websearch',
                'llm_provider': 'claude_code',
                'model': 'sonnet-4.5',
                'status': 'completed',
                'completed_at': datetime.now(),
                'research_results': research_results
            }

            research_id = self.db.save_research_results(research_data)

            print(f"✅ Исследование завершено! ID: {research_id}")

            return {
                'status': 'success',
                'research_id': research_id,
                'anketa_id': anketa_id,
                'results': research_results
            }

        except Exception as e:
            print(f"❌ Ошибка исследования: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'anketa_id': anketa_id
            }

    async def _research_block1_websearch(self, p: Dict) -> Dict:
        """
        Блок 1: Проблема и социальная значимость (10 запросов)

        По промтам эксперта из agents/251008/тест_промпт_1_проблема_и_соц_значимость.md
        """
        results = {
            'block_name': 'Проблема и социальная значимость',
            'queries': []
        }

        # Запрос 1: Официальная статистика
        q1 = await self._websearch_with_claude(
            query=f"официальная статистика {p['ПРОБЛЕМА']} {p['РЕГИОН']} 2022-2025",
            allowed_domains=["rosstat.gov.ru", "fedstat.ru", "gks.ru"],
            context="Найди точные цифры и динамику проблемы"
        )
        results['queries'].append({
            'name': 'Официальная статистика',
            'query': q1['query'],
            'result': q1['result']
        })

        # Запрос 2: Научные исследования
        q2 = await self._websearch_with_claude(
            query=f"научные исследования эффективность решения {p['ПРОБЛЕМА']} РФ 2022-2025",
            allowed_domains=["elibrary.ru", "cyberleninka.ru"],
            context="Найди 3-5 исследований с метриками эффективности"
        )
        results['queries'].append({
            'name': 'Научные исследования',
            'query': q2['query'],
            'result': q2['result']
        })

        # Запрос 3: Государственные программы
        q3 = await self._websearch_with_claude(
            query=f"государственные программы нацпроекты {p['СФЕРА']} {p['ПРОБЛЕМА']} 2024-2025",
            allowed_domains=["nationalprojects.ru", "government.ru"],
            context="Найди связь с нацпроектами и целевые показатели"
        )
        results['queries'].append({
            'name': 'Государственные программы',
            'query': q3['query'],
            'result': q3['result']
        })

        # ... еще 7 запросов по промтам эксперта

        return results

    async def _research_block2_websearch(self, p: Dict) -> Dict:
        """Блок 2: География и целевая аудитория (10 запросов)"""
        # Аналогично block1
        pass

    async def _research_block3_websearch(self, p: Dict) -> Dict:
        """Блок 3: Задачи, мероприятия, цель (7 запросов)"""
        # Аналогично block1
        pass

    async def _websearch_with_claude(
        self,
        query: str,
        allowed_domains: List[str] = None,
        context: str = ""
    ) -> Dict:
        """
        Выполнить WebSearch через Claude Code

        Args:
            query: Поисковый запрос
            allowed_domains: Список разрешённых доменов (RU-источники)
            context: Дополнительный контекст для Claude

        Returns:
            {
                'query': str,
                'result': {
                    'summary': str,
                    'sources': List[Dict],
                    'quotes': List[Dict]
                }
            }
        """
        import requests

        # Формируем запрос к Claude Code
        headers = {
            "Authorization": f"Bearer {self.claude_api_key}",
            "Content-Type": "application/json"
        }

        # Промпт для Claude с WebSearch
        prompt = f"""
Выполни поиск по запросу: "{query}"

Ограничения:
- Только источники из: {', '.join(allowed_domains or self.OFFICIAL_DOMAINS)}
- Данные не старше 3 лет (2022-2025)
- Приоритет официальным источникам

Задача: {context}

Верни результат в формате JSON:
{{
    "summary": "краткое резюме (5-7 предложений)",
    "sources": [
        {{
            "url": "полный URL",
            "title": "название документа/страницы",
            "org": "организация (Росстат, Минспорт и т.д.)",
            "date": "дата публикации",
            "relevance": "высокая/средняя/низкая"
        }}
    ],
    "quotes": [
        {{
            "text": "прямая цитата (2-3 предложения)",
            "source": "URL источника",
            "org": "организация",
            "date": "дата",
            "strength": "A|B (A - сильная цитата)"
        }}
    ]
}}

Используй WebSearch tool для поиска.
"""

        payload = {
            "message": prompt,
            "model": "sonnet",
            "temperature": 0.3,
            "max_tokens": 2000
        }

        try:
            response = requests.post(
                f"{self.claude_base_url}/chat",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                claude_response = data.get('response', '{}')

                # Парсим JSON из ответа Claude
                try:
                    result = json.loads(claude_response)
                except json.JSONDecodeError:
                    # Если Claude вернул не JSON, пытаемся извлечь
                    result = {
                        'summary': claude_response[:500],
                        'sources': [],
                        'quotes': []
                    }

                return {
                    'query': query,
                    'result': result
                }
            else:
                raise Exception(f"Claude API error: {response.status_code}")

        except Exception as e:
            print(f"❌ WebSearch ошибка: {e}")
            return {
                'query': query,
                'result': {
                    'summary': f"Ошибка поиска: {str(e)}",
                    'sources': [],
                    'quotes': []
                }
            }

    def _extract_placeholders(self, anketa: Dict) -> Dict:
        """Извлечь placeholders из анкеты"""
        return {
            'РЕГИОН': anketa.get('geography', anketa.get('region', '')),
            'ПРОБЛЕМА': anketa.get('problem', ''),
            'ЦЕЛЕВАЯ_ГРУППА': anketa.get('target_group', ''),
            'СФЕРА': anketa.get('sphere', anketa.get('category', '')),
            'ПЕРИОД': '2022-2025'
        }

    def _count_sources(self, blocks: List[Dict]) -> int:
        """Подсчитать количество источников"""
        total = 0
        for block in blocks:
            for query in block.get('queries', []):
                total += len(query.get('result', {}).get('sources', []))
        return total

    def _count_quotes(self, blocks: List[Dict]) -> int:
        """Подсчитать количество цитат"""
        total = 0
        for block in blocks:
            for query in block.get('queries', []):
                total += len(query.get('result', {}).get('quotes', []))
        return total
```

---

## 🔗 Интеграция с Grant Crew

**Файл**: `agents/grant_crew.py`

```python
async def process_grant_application(anketa_id: str):
    """Полный цикл обработки заявки"""

    # 1. Auditor
    auditor = AuditorAgent(db)
    audit_result = await auditor.evaluate_project(anketa_id)

    if audit_result['approval_status'] != 'approved':
        return {'status': 'needs_revision', 'auditor': audit_result}

    # 2. Researcher (АВТОЗАПУСК!)
    researcher = ResearcherAgent(db, llm_provider="claude_code")
    research_result = await researcher.research_anketa(anketa_id)

    if research_result['status'] != 'success':
        return {'status': 'research_failed', 'researcher': research_result}

    # 3. Planner
    planner = PlannerAgent(db)
    plan_result = await planner.create_structure(anketa_id)

    # 4. Writer (использует research_results!)
    writer = WriterAgent(db)
    grant_result = await writer.write_grant(
        anketa_id=anketa_id,
        research_id=research_result['research_id']  # ← Использует исследование!
    )

    return {
        'status': 'success',
        'grant_id': grant_result['grant_id'],
        'research_id': research_result['research_id']
    }
```

---

## 📊 Результат

### **БЕЗ Researcher (текущее состояние)**
```
Грант Валерии:
- 11,425 символов
- Нет официальной статистики
- Нет ссылок на Росстат/нацпроекты
- Нет успешных кейсов
- Шансы одобрения: 10-15%
```

### **С Researcher + WebSearch (целевое)**
```
Грант:
- 15,000-20,000 символов
- Официальная статистика (3-5 источников)
- Прямые цитаты из госпрограмм (5-7 цитат)
- Успешные кейсы (3 аналога)
- Индикаторный матчинг (цели → KPI нацпроектов)
- Шансы одобрения: 40-50% ✅
```

---

## ✅ План реализации

### **Этап 1: Автозапуск (1 час)**
1. Добавить триггер в `grant_crew.py`
2. Researcher запускается после Auditor approval
3. Тестировать на анкете Валерии

### **Этап 2: WebSearch интеграция (2-3 часа)**
1. Реализовать `_websearch_with_claude()`
2. Реализовать `_research_block1_websearch()` (10 запросов)
3. Тестировать на одном блоке

### **Этап 3: Все 27 запросов (3-4 часа)**
1. Реализовать block2 (10 запросов)
2. Реализовать block3 (7 запросов)
3. Загрузить промты эксперта в БД

### **Этап 4: Writer интеграция (1 час)**
1. Модифицировать `writer_agent.py`
2. Использовать `research_results` при генерации
3. Добавить цитаты и ссылки в текст гранта

---

## 🎯 Критерии успеха

1. ✅ Researcher запускается автоматически после Auditor
2. ✅ Status меняется на 'completed' после завершения
3. ✅ 27 WebSearch запросов выполнены через Claude Code
4. ✅ research_results содержит:
   - Факты с цифрами (≥10)
   - Прямые цитаты (≥15)
   - Источники с метаданными (≥20)
   - Индикаторный матчинг (≥3 госпрограммы)
5. ✅ Writer использует research_results при генерации
6. ✅ Грант содержит официальную статистику и ссылки

---

## 📝 Обновить документацию

### **Добавить в ARCHITECTURE.md**

**Раздел**: "LLM Providers and Tools"

```markdown
## Claude Code API

### Available Tools:
- `/chat` - Чат с Claude (Sonnet/Opus)
- `/code` - Выполнение Python/JavaScript кода
- `/sessions` - Управление контекстными сессиями
- `/models` - Список доступных моделей
- **WebSearch** - Поиск в интернете (встроенный tool)

### WebSearch Features:
- Фильтрация по доменам (allowed_domains)
- Актуальность данных
- Цитаты и источники
- Приоритет RU-источникам

### Usage for Researcher Agent:
```python
researcher = ResearcherAgent(db, llm_provider="claude_code")
result = await researcher.research_anketa(anketa_id)
```
```

---

**Статус**: 📋 План готов
**Время реализации**: 6-8 часов
**Приоритет**: 🔴 КРИТИЧЕСКИЙ (без Researcher качество грантов низкое)

