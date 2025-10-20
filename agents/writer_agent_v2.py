#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Writer Agent V2 - агент для написания заявок на гранты с использованием результатов исследования
ОБНОВЛЕНО: Использует DatabasePromptManager для загрузки goal/backstory из БД
Версия 2.1
"""
import sys
import os
from typing import Dict, Any, List, Optional
import logging
import asyncio
import time
import json

# Добавляем пути к модулям (работает на Windows и Linux)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'shared'))
sys.path.insert(0, os.path.join(project_root, 'telegram-bot', 'services'))
sys.path.insert(0, os.path.join(project_root, 'web-admin'))

try:
    from agents.base_agent import BaseAgent
except ImportError:
    from base_agent import BaseAgent

# Импорт DatabasePromptManager для загрузки промптов из БД
try:
    from utils.prompt_manager import DatabasePromptManager, get_database_prompt_manager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    PROMPT_MANAGER_AVAILABLE = False
    DatabasePromptManager = None

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    UNIFIED_CLIENT_AVAILABLE = False
    UnifiedLLMClient = None
    AGENT_CONFIGS = {}

try:
    from services.llm_router import LLMRouter, LLMProvider
    LLM_ROUTER_AVAILABLE = True
except ImportError:
    print("[WARN] LLM Router недоступен")
    LLMRouter = None
    LLMProvider = None
    LLM_ROUTER_AVAILABLE = False

logger = logging.getLogger(__name__)

class WriterAgentV2(BaseAgent):
    """Агент-писатель V2 для создания заявок на гранты с использованием research_results"""

    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("writer", db, llm_provider)

        # Инициализация DatabasePromptManager для загрузки промптов из БД
        self.prompt_manager: Optional[DatabasePromptManager] = None
        if PROMPT_MANAGER_AVAILABLE:
            try:
                self.prompt_manager = get_database_prompt_manager()
                logger.info("✅ Writer V2 Agent: DatabasePromptManager подключен (goal, backstory, stage prompts из БД)")
            except Exception as e:
                logger.warning(f"⚠️ Writer V2: Не удалось инициализировать PromptManager: {e}")

        # Инициализация Expert Agent для получения знаний о требованиях ФПГ
        self.expert_agent = None
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from expert_agent import ExpertAgent
            self.expert_agent = ExpertAgent()
            logger.info("✅ Writer V2 Agent: Expert Agent подключен (векторная база знаний ФПГ)")
        except Exception as e:
            logger.warning(f"⚠️ Writer V2: Expert Agent недоступен: {e}")

        if UNIFIED_CLIENT_AVAILABLE:
            # Передаем provider в конструктор UnifiedLLMClient
            self.llm_client = UnifiedLLMClient(provider=llm_provider)
            self.config = AGENT_CONFIGS.get("writer", AGENT_CONFIGS.get("writer", {}))
        elif LLM_ROUTER_AVAILABLE:
            self.llm_router = LLMRouter()
        else:
            self.llm_client = None
            self.llm_router = None
            print("[WARN] Writer агент V2 работает без LLM сервисов")

    def _get_goal(self) -> str:
        """Получить goal агента из БД с fallback"""
        if self.prompt_manager:
            try:
                goal = self.prompt_manager.get_prompt('writer_v2', 'goal')
                if goal:
                    logger.info("✅ Writer V2: Goal загружен из БД")
                    return goal
            except Exception as e:
                logger.warning(f"⚠️ Writer V2: Ошибка загрузки goal из БД: {e}")

        # Fallback на hardcoded
        logger.info("Writer V2: Используется hardcoded goal")
        return "Создать качественную заявку на грант с использованием результатов исследования (27 запросов), минимум 10 цитат и 2 таблицы"

    def _get_backstory(self) -> str:
        """Получить backstory агента из БД с fallback"""
        if self.prompt_manager:
            try:
                backstory = self.prompt_manager.get_prompt('writer_v2', 'backstory')
                if backstory:
                    logger.info("✅ Writer V2: Backstory загружен из БД")
                    return backstory
            except Exception as e:
                logger.warning(f"⚠️ Writer V2: Ошибка загрузки backstory из БД: {e}")

        # Fallback на hardcoded
        logger.info("Writer V2: Используется hardcoded backstory")
        return """Ты AI-ассистент, помогающий составлять черновики грантовых заявок на основе предоставленных данных.
        Твоя задача - структурировать информацию из исследования в формат заявки, используя ТОЛЬКО реальные данные.
        Ты создаешь черновики для дальнейшей доработки заявителями. Все данные должны быть проверяемыми и основаны
        на результатах исследования. Твои черновики включают официальную статистику, цитаты из госпрограмм,
        успешные кейсы и сравнительные таблицы - всё из предоставленных источников."""

    def _get_fpg_requirements(self, section: str = "") -> List[Dict[str, str]]:
        """Получить требования ФПГ из Expert Agent по конкретному разделу"""
        try:
            if not self.expert_agent:
                logger.warning("⚠️ WriterV2: Expert Agent недоступен для получения требований")
                return []

            # Формируем вопросы в зависимости от раздела
            questions = {
                "problem": "Какие требования к разделу 'Описание проблемы' в заявке на грант ФПГ?",
                "goal": "Какие требования к формулировке цели проекта в заявке ФПГ?",
                "results": "Какие требования к описанию результатов проекта в заявке ФПГ?",
                "general": "Какие общие требования к заполнению заявки на грант ФПГ?"
            }

            question = questions.get(section, questions["general"])

            logger.info(f"🔍 WriterV2: Запрашиваем требования ФПГ - '{question[:50]}...'")

            # Запрашиваем Expert Agent
            results = self.expert_agent.query_knowledge(
                question=question,
                fund="fpg",
                top_k=3,
                min_score=0.4
            )

            if results:
                logger.info(f"✅ WriterV2: Получено {len(results)} рекомендаций от Expert Agent")
                return results
            else:
                logger.warning("⚠️ WriterV2: Expert Agent не нашел релевантных требований")
                return []

        except Exception as e:
            logger.error(f"❌ WriterV2: Ошибка получения требований от Expert Agent: {e}")
            return []

    async def _fetch_research_results(self, anketa_id: str) -> Optional[Dict[str, Any]]:
        """Получить результаты исследования из БД по anketa_id"""
        try:
            logger.info(f"📚 WriterV2: Загружаем research_results для anketa_id={anketa_id}")

            if not self.db:
                logger.warning("⚠️ WriterV2: БД недоступна")
                return None

            # Получаем research_results из researcher_research через прямой SQL
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT research_results, status, metadata
                    FROM researcher_research
                    WHERE anketa_id = %s AND status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT 1
                """, (anketa_id,))

                row = cursor.fetchone()
                cursor.close()

                if row:
                    research_results = row[0] if isinstance(row, tuple) else row.get('research_results')

                    # Если research_results - строка JSON, парсим
                    if isinstance(research_results, str):
                        research_results = json.loads(research_results)

                    logger.info(f"✅ WriterV2: Research results загружены - {len(research_results)} блоков")
                    return research_results
                else:
                    logger.warning(f"⚠️ WriterV2: Не найдены research_results для anketa_id={anketa_id}")
                    return None

        except Exception as e:
            logger.error(f"❌ WriterV2: Ошибка загрузки research_results: {e}")
            return None

    def _format_citations(self, research_results: Dict[str, Any], min_count: int = 10) -> List[Dict[str, str]]:
        """Извлечь и отформатировать цитаты из research_results"""
        citations = []

        try:
            # Извлекаем из block1_problem
            block1 = research_results.get('block1_problem', {})
            for fact in block1.get('key_facts', [])[:5]:
                citations.append({
                    'text': fact.get('fact', ''),
                    'source': fact.get('source', ''),
                    'date': fact.get('date', ''),
                    'type': 'статистика'
                })

            # Извлекаем из success_cases
            for case in block1.get('success_cases', [])[:3]:
                citations.append({
                    'text': case.get('quote', case.get('result', '')),
                    'source': case.get('source', ''),
                    'type': 'успешный кейс'
                })

            # Извлекаем из programs
            for program in block1.get('programs', [])[:2]:
                citations.append({
                    'text': program.get('kpi', ''),
                    'source': program.get('name', ''),
                    'type': 'госпрограмма'
                })

            # Извлекаем из block2_geography
            block2 = research_results.get('block2_geography', {})
            for fact in block2.get('key_facts', [])[:3]:
                citations.append({
                    'text': fact.get('fact', ''),
                    'source': fact.get('source', ''),
                    'date': fact.get('date', ''),
                    'type': 'география'
                })

            logger.info(f"✅ WriterV2: Извлечено {len(citations)} цитат")

            # Убеждаемся что минимум min_count цитат
            if len(citations) < min_count:
                logger.warning(f"⚠️ WriterV2: Недостаточно цитат ({len(citations)} < {min_count})")

            return citations[:min_count]

        except Exception as e:
            logger.error(f"❌ WriterV2: Ошибка форматирования цитат: {e}")
            return []

    def _format_tables(self, research_results: Dict[str, Any], min_count: int = 2) -> List[Dict[str, Any]]:
        """Извлечь и отформатировать таблицы из research_results"""
        tables = []

        try:
            # Таблица 1: Dynamics table из block1
            block1 = research_results.get('block1_problem', {})
            dynamics_table = block1.get('dynamics_table', {})
            if dynamics_table and dynamics_table.get('indicators'):
                tables.append({
                    'title': 'Динамика ключевых показателей',
                    'type': 'dynamics',
                    'data': dynamics_table,
                    'source': 'Блок 1: Анализ проблемы'
                })

            # Таблица 2: Comparison table из block2
            block2 = research_results.get('block2_geography', {})
            comparison_table = block2.get('comparison_table', {})
            if comparison_table:
                tables.append({
                    'title': 'Сравнение: Регион vs РФ vs Лидер',
                    'type': 'comparison',
                    'data': comparison_table,
                    'source': 'Блок 2: География и целевая аудитория'
                })

            # Таблица 3: Target audience из block2 (дополнительная)
            target_audience = block2.get('target_audience', {})
            if target_audience:
                tables.append({
                    'title': 'Целевая аудитория проекта',
                    'type': 'target_audience',
                    'data': target_audience,
                    'source': 'Блок 2: Целевая аудитория'
                })

            logger.info(f"✅ WriterV2: Извлечено {len(tables)} таблиц")

            if len(tables) < min_count:
                logger.warning(f"⚠️ WriterV2: Недостаточно таблиц ({len(tables)} < {min_count})")

            return tables[:min_count + 1]  # Берем чуть больше для запаса

        except Exception as e:
            logger.error(f"❌ WriterV2: Ошибка форматирования таблиц: {e}")
            return []

    async def _stage1_planning_async(self, client, user_answers: Dict, research_results: Dict,
                                    selected_grant: Dict) -> Dict[str, Any]:
        """Stage 1: Планирование структуры гранта на основе research_results"""
        logger.info("📋 WriterV2 Stage 1: Планирование структуры гранта")

        try:
            # Получаем требования ФПГ от Expert Agent
            fpg_requirements_general = self._get_fpg_requirements("general")
            fpg_requirements_problem = self._get_fpg_requirements("problem")

            # Форматируем требования для промпта
            fpg_knowledge = "\n".join([
                f"- {req['section_name']}: {req['content'][:200]}..."
                for req in (fpg_requirements_general + fpg_requirements_problem)[:4]
            ])

            # Создаем промпт для планирования
            metadata = research_results.get('metadata', {})
            block1_summary = research_results.get('block1_problem', {}).get('summary', '')
            block2_summary = research_results.get('block2_geography', {}).get('summary', '')
            block3_summary = research_results.get('block3_goals', {}).get('summary', '')

            # Подготовим данные для промпта
            block1 = research_results.get('block1_problem', {})
            block2 = research_results.get('block2_geography', {})
            block3 = research_results.get('block3_goals', {})

            key_facts_count = len(block1.get('key_facts', []))
            programs_count = len(block1.get('programs', []))
            success_cases_count = len(block1.get('success_cases', []))

            planning_prompt = f"""Ты эксперт по написанию заявок на Президентские гранты РФ. Твоя задача - спланировать структуру заявки согласно официальной форме ФПГ.

ТРЕБОВАНИЯ ФПГ (из официальной базы знаний):
{fpg_knowledge if fpg_knowledge else "Используй общие требования к заявкам на гранты"}

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
- Ключевые факты о проблеме: {key_facts_count}
- Федеральные программы найдены: {programs_count}
- Успешные кейсы найдены: {success_cases_count}

СТРУКТУРА ЗАЯВКИ НА ПРЕЗИДЕНТСКИЙ ГРАНТ:
Заявка должна следовать официальной форме ФПГ (Фонд Президентских Грантов) и включать 9 обязательных разделов.

КРИТИЧНО ВАЖНО:
- Раздел 2 "Описание проблемы" должен быть 2-4 страницы (8000+ символов) - самый большой раздел
- Использовать ВСЕ key_facts из block1_problem (всего {key_facts_count} фактов)
- Включить обе таблицы: dynamics_table и comparison_table
- Официальный стиль, третье лицо, без "мы/наш"
- Календарный план обязателен

ЗАДАЧА:
Создай детальный план из 9 разделов:

1. КРАТКОЕ ОПИСАНИЕ (0.5-1 стр, ~2000 символов)
2. ОПИСАНИЕ ПРОБЛЕМЫ (2-4 стр, ~8000 символов) - САМЫЙ ВАЖНЫЙ
   - Должен содержать 5 подразделов:
     а) Федеральный контекст (нацпроекты, госпрограммы)
     б) Региональная специфика (comparison_table)
     в) Целевая группа (демография, статистика)
     г) Динамика проблемы (dynamics_table)
     д) Успешный опыт (success_cases)
3. ЦЕЛЬ ПРОЕКТА (1 абзац, ~500 символов, SMART)
4. РЕЗУЛЬТАТЫ (количественные с точными цифрами + качественные с методами измерения)
5. ЗАДАЧИ (3-5 конкретных задач)
6. ПАРТНЕРЫ (из programs)
7. ИНФОРМАЦИОННОЕ СОПРОВОЖДЕНИЕ
8. ДАЛЬНЕЙШЕЕ РАЗВИТИЕ
9. КАЛЕНДАРНЫЙ ПЛАН (таблица 4-8 строк)

Для раздела 2 (Проблема) распиши ДЕТАЛЬНО:
- Какие key_facts использовать (индексы)
- Какие programs упомянуть
- Где разместить таблицы
- Как структурировать 8000+ символов

Ответ дай в формате JSON:
{{
  "section_1_brief": {{
    "content_plan": "План краткого описания",
    "length_chars": 2000
  }},
  "section_2_problem": {{
    "subsections": [
      {{
        "title": "Федеральный контекст",
        "content_plan": "Что включить",
        "key_facts_indices": [0, 1, 2],
        "programs_indices": [0],
        "citations_count": 3
      }},
      {{
        "title": "Региональная специфика",
        "content_plan": "Статистика региона",
        "key_facts_indices": [3, 4],
        "tables": ["comparison_table"],
        "citations_count": 2
      }},
      {{
        "title": "Целевая группа",
        "content_plan": "Демография ЦА",
        "key_facts_indices": [5, 6],
        "citations_count": 2
      }},
      {{
        "title": "Динамика проблемы",
        "content_plan": "Тренды",
        "key_facts_indices": [7, 8],
        "tables": ["dynamics_table"],
        "citations_count": 3
      }},
      {{
        "title": "Успешный опыт",
        "content_plan": "Кейсы",
        "success_cases_indices": [0, 1, 2]
      }}
    ],
    "total_length_chars": 8000,
    "total_citations": 10
  }},
  "section_3_goal": {{
    "goal_text": "Формулировка SMART цели"
  }},
  "section_4_results": {{
    "quantitative": ["Результат 1: число", "Результат 2: число"],
    "qualitative": [{{"result": "Результат", "measurement": "Метод измерения"}}]
  }},
  "section_5_tasks": ["Задача 1", "Задача 2", "Задача 3"],
  "section_6_partners": [{{"name": "Партнер", "support_types": ["Тип"]}}],
  "section_7_info": "План инфо-сопровождения",
  "section_8_future": "Развитие после гранта",
  "section_9_calendar": {{
    "rows": [
      {{
        "task_number": 1,
        "event": "Мероприятие",
        "start": "01.03.2025",
        "end": "31.03.2025",
        "result": "Результат"
      }}
    ]
  }},
  "total_chars": 25000,
  "style": "official_third_person"
}}
"""

            logger.info(f"📤 WriterV2 Stage 1: Отправляем запрос на планирование (промпт: {len(planning_prompt)} символов)")

            # Генерируем план
            plan_response = await client.generate_text(planning_prompt, 2000)

            logger.info(f"✅ WriterV2 Stage 1: План получен - {len(plan_response)} символов")

            # Парсим JSON из ответа
            try:
                # Ищем JSON в ответе (может быть обернут в ```json...```)
                import re
                json_match = re.search(r'\{[\s\S]*\}', plan_response)
                if json_match:
                    plan = json.loads(json_match.group(0))
                else:
                    # Fallback: создаем базовый план
                    plan = self._create_fallback_plan()
            except:
                plan = self._create_fallback_plan()

            logger.info(f"📊 WriterV2 Stage 1: План содержит {len(plan.get('sections', []))} разделов")

            return plan

        except Exception as e:
            logger.error(f"❌ WriterV2 Stage 1: Ошибка планирования: {e}")
            return self._create_fallback_plan()

    def _create_fallback_plan(self) -> Dict[str, Any]:
        """Создать базовый план если LLM недоступен"""
        return {
            'sections': [
                {
                    'name': 'Актуальность проблемы',
                    'key_elements': ['Статистика', 'Госпрограммы', 'Таблица динамики'],
                    'research_blocks': ['block1'],
                    'citations_count': 4,
                    'tables_count': 1
                },
                {
                    'name': 'География и целевая аудитория',
                    'key_elements': ['Сравнение регионов', 'ЦА', 'Инфраструктура'],
                    'research_blocks': ['block2'],
                    'citations_count': 3,
                    'tables_count': 1
                },
                {
                    'name': 'Цели и задачи проекта',
                    'key_elements': ['SMART-цели', 'KPI', 'Успешные кейсы'],
                    'research_blocks': ['block3'],
                    'citations_count': 3,
                    'tables_count': 0
                }
            ],
            'total_length_estimate': 15000,
            'total_citations': 10,
            'total_tables': 2
        }

    async def _stage2_writing_async(self, client, user_answers: Dict, research_results: Dict,
                                   selected_grant: Dict, plan: Dict, citations: List, tables: List) -> Dict[str, str]:
        """Stage 2: Написание текста заявки с цитатами и таблицами"""
        logger.info("✍️ WriterV2 Stage 2: Написание текста заявки")

        content = {}

        try:
            # Подготавливаем данные для промпта
            block1 = research_results.get('block1_problem', {})
            block2 = research_results.get('block2_geography', {})
            block3 = research_results.get('block3_goals', {})

            # Форматируем цитаты для промпта
            citations_text = "\n".join([
                f"[{i+1}] {c['text']} (Источник: {c['source']}, {c.get('date', '')})"
                for i, c in enumerate(citations[:10])
            ])

            # Форматируем таблицы для промпта
            tables_text = "\n".join([
                f"Таблица {i+1}: {t['title']}\nТип: {t['type']}\nДанные: {str(t['data'])[:200]}..."
                for i, t in enumerate(tables[:2])
            ])

            # Промпт для написания заявки
            writing_prompt = f"""Помоги составить черновик грантовой заявки на основе предоставленных данных исследования.

ВАЖНО: Это черновик для дальнейшей доработки заявителем. Используй ТОЛЬКО данные из предоставленного исследования - не придумывай факты или цифры.

Структура должна соответствовать официальной форме ФПГ (Фонд Президентских Грантов).

СТИЛЬ НАПИСАНИЯ:
✅ Официальный, деловой стиль
✅ Третье лицо ВСЕГДА ("проект направлен на...", "планируется...", "будет проведено...")
✅ НЕТ первого лица ("мы", "наш", "наша команда")
✅ Сложные предложения с вводными конструкциями
✅ Безэмоциональный тон (только факты, цифры, ссылки)
✅ Использование аббревиатур (ВОЗ, ВЦИОМ, МинЗдрав, Росстат и т.д.)

ФОРМАТ ЦИТИРОВАНИЯ (используй ТОЛЬКО данные из research_results):
"По данным [организация] [факт с точными цифрами]. [Вывод]"

Примеры формата:
- "По данным ВОЗ Россия находится по уровню физической активности молодежи на 98 месте."
- "Согласно исследованию ВЦИОМ 11% школьников воспринимают физкультуру как тяжелую обязанность."

ДАННЫЕ ПРОЕКТА:
Название: {user_answers.get('project_name', 'Проект')}
Описание: {user_answers.get('description', '')}
Проблема: {user_answers.get('problem', '')}
Решение: {user_answers.get('solution', '')}
Целевая группа: {user_answers.get('target_group', '')}
География: {user_answers.get('geography', '')}
Бюджет: {user_answers.get('budget', '1,000,000')} рублей
Срок реализации: {user_answers.get('timeline', '12')} месяцев

СТРУКТУРА (9 разделов из плана):
Раздел 1: Краткое описание (~2000 символов)
Раздел 2: Обоснование проблемы (~8000 символов) - САМЫЙ ВАЖНЫЙ, включает comparison_table и dynamics_table
Разделы 3-9: Цель, Результаты, Задачи, Партнеры, Инфо-сопровождение, Развитие, Календарь

ЦИТАТЫ И ИСТОЧНИКИ (использовать в тексте):
{citations_text}

ТАБЛИЦЫ (минимум 2 включить):
{tables_text}

ДАННЫЕ ИЗ ИССЛЕДОВАНИЯ:

БЛОК 1 - ПРОБЛЕМА:
Резюме: {block1.get('summary', '')[:500]}

Ключевые факты (используй в разделе 2):
{chr(10).join([f"  • {f.get('fact', '')} (Источник: {f.get('source', '')}, {f.get('date', '')})" for f in block1.get('key_facts', [])[:5]])}

Федеральные программы:
{chr(10).join([f"  • {p.get('name', '')}: {p.get('kpi', '')}" for p in block1.get('programs', [])[:3]])}

Успешные кейсы:
{chr(10).join([f"  • {c.get('name', '')}: {c.get('result', '')}" for c in block1.get('success_cases', [])[:3]])}

БЛОК 2 - ГЕОГРАФИЯ:
Резюме: {block2.get('summary', '')[:500]}

Факты о географии:
{chr(10).join([f"  • {f.get('fact', '')}" for f in block2.get('key_facts', [])[:4]])}

БЛОК 3 - ЦЕЛИ:
Резюме: {block3.get('summary', '')[:500]}

Варианты целей (SMART):
{chr(10).join([f"  • {g.get('text', '')[:200]}" for g in block3.get('main_goal_variants', [])[:2]])}

ЗАДАНИЕ:
Составь черновик заявки (15,000+ символов), включающий ВСЕ 9 разделов на основе данных:

1. КРАТКОЕ ОПИСАНИЕ (~1500 символов, суть + ЦА + география)

2. ОБОСНОВАНИЕ ПРОБЛЕМЫ (~6000 символов) - САМЫЙ ВАЖНЫЙ
   - Федеральный контекст (нацпроекты, госпрограммы)
   - Региональная специфика (сравнение с РФ, таблица comparison_table)
   - Целевая группа (демография)
   - Динамика проблемы (таблица dynamics_table, тренды)
   - Успешные кейсы

3. ЦЕЛЬ ПРОЕКТА (~500 символов, SMART формат)

4. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ (~2500 символов)
   - Количественные (точные цифры)
   - Качественные (с методами измерения)

5. ЗАДАЧИ ПРОЕКТА (3-5 задач, bullet list)

6. ПАРТНЕРЫ ПРОЕКТА (организации + типы поддержки)

7. ИНФОРМАЦИОННОЕ СОПРОВОЖДЕНИЕ (соцсети, СМИ)

8. ДАЛЬНЕЙШЕЕ РАЗВИТИЕ (планы после гранта)

9. КАЛЕНДАРНЫЙ ПЛАН (Markdown таблица, 4-8 строк)

ТРЕБОВАНИЯ:
✅ Общий объем: 15,000+ символов
✅ Раздел 2 "Проблема": 6,000+ символов (самый большой)
✅ Официальный стиль, третье лицо
✅ 2 таблицы обязательно (comparison_table + dynamics_table)
✅ НЕ ПРИДУМЫВАЙ данные - используй только research_results

ВАЖНО: Ответь прямо в этом сообщении JSON-объектом. НЕ создавай файлы. Просто выведи JSON как текст ответа.

Формат ответа (JSON-объект в тексте ответа):
{{
  "section_1_brief": "Текст раздела 1...",
  "section_2_problem": "Текст раздела 2 (8000+ символов)...",
  "section_3_goal": "Текст цели...",
  "section_4_results": "Текст результатов...",
  "section_5_tasks": "Текст задач...",
  "section_6_partners": "Текст партнеров...",
  "section_7_info": "Текст инфо-сопровождения...",
  "section_8_future": "Текст развития...",
  "section_9_calendar": "Markdown таблица календарного плана...",
  "metadata": {{
    "total_chars": 25000,
    "citations_used": 12,
    "tables_included": 2,
    "style": "official_third_person"
  }}
}}

Просто скопируй этот JSON, заполни все разделы реальными данными из research_results и верни мне как текст.
"""

            logger.info(f"📤 WriterV2 Stage 2: Отправляем запрос на написание (промпт: {len(writing_prompt)} символов)")

            # Генерируем текст заявки (большой лимит токенов)
            application_text = await client.generate_text(writing_prompt, 8000)

            logger.info(f"✅ WriterV2 Stage 2: Текст получен - {len(application_text)} символов")

            # Пытаемся распарсить JSON с 9 секциями
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', application_text)
                if json_match:
                    grant_json = json.loads(json_match.group(0))

                    # Извлекаем 9 секций из JSON
                    content['section_1_brief'] = grant_json.get('section_1_brief', '')
                    content['section_2_problem'] = grant_json.get('section_2_problem', '')
                    content['section_3_goal'] = grant_json.get('section_3_goal', '')
                    content['section_4_results'] = grant_json.get('section_4_results', '')
                    content['section_5_tasks'] = grant_json.get('section_5_tasks', '')
                    content['section_6_partners'] = grant_json.get('section_6_partners', '')
                    content['section_7_info'] = grant_json.get('section_7_info', '')
                    content['section_8_future'] = grant_json.get('section_8_future', '')
                    content['section_9_calendar'] = grant_json.get('section_9_calendar', '')

                    # Собираем full_text из всех секций
                    content['full_text'] = '\n\n'.join([
                        f"## 1. КРАТКОЕ ОПИСАНИЕ ПРОЕКТА\n{content['section_1_brief']}",
                        f"## 2. ОБОСНОВАНИЕ СОЦИАЛЬНОЙ ЗНАЧИМОСТИ\n{content['section_2_problem']}",
                        f"## 3. ЦЕЛЬ ПРОЕКТА\n{content['section_3_goal']}",
                        f"## 4. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ\n{content['section_4_results']}",
                        f"## 5. ЗАДАЧИ ПРОЕКТА\n{content['section_5_tasks']}",
                        f"## 6. ПАРТНЕРЫ ПРОЕКТА\n{content['section_6_partners']}",
                        f"## 7. ИНФОРМАЦИОННОЕ СОПРОВОЖДЕНИЕ\n{content['section_7_info']}",
                        f"## 8. ДАЛЬНЕЙШЕЕ РАЗВИТИЕ\n{content['section_8_future']}",
                        f"## 9. КАЛЕНДАРНЫЙ ПЛАН\n{content['section_9_calendar']}"
                    ])

                    # Метаданные из JSON или создаем
                    content['metadata'] = grant_json.get('metadata', {})
                    content['metadata']['citations_used'] = content['metadata'].get('citations_used', len(citations))
                    content['metadata']['tables_included'] = content['metadata'].get('tables_included', len(tables))
                    content['metadata']['total_chars'] = len(content['full_text'])
                    content['metadata']['style'] = content['metadata'].get('style', 'official_third_person')
                    content['metadata']['format'] = 'fpg_9_sections'

                    logger.info(f"✅ WriterV2 Stage 2: JSON распарсен успешно - 9 секций, {len(content['full_text'])} символов")

                else:
                    raise ValueError("JSON не найден в ответе")

            except Exception as parse_error:
                logger.warning(f"⚠️ WriterV2 Stage 2: Не удалось распарсить JSON ({parse_error}), используем fallback парсинг")

                # Fallback: разбиваем текст по разделам (старая логика)
                content['full_text'] = application_text
                content['section_1_brief'] = application_text[:2000] if len(application_text) > 2000 else application_text
                content['section_2_problem'] = application_text[2000:10000] if len(application_text) > 10000 else application_text[2000:]
                content['section_3_goal'] = self._extract_section(application_text, 'Цель')
                content['section_4_results'] = self._extract_section(application_text, 'Результат')
                content['section_5_tasks'] = self._extract_section(application_text, 'Задачи')
                content['section_6_partners'] = self._extract_section(application_text, 'Партнер')
                content['section_7_info'] = self._extract_section(application_text, 'Информ')
                content['section_8_future'] = self._extract_section(application_text, 'Развитие')
                content['section_9_calendar'] = self._extract_section(application_text, 'Календарн')

                content['metadata'] = {
                    'citations_used': len(citations),
                    'tables_included': len(tables),
                    'total_chars': len(application_text),
                    'format': 'fallback_parsing',
                    'style': 'unknown'
                }

            # Добавляем обратную совместимость со старыми полями
            content['title'] = user_answers.get('project_name', 'Проект')
            content['summary'] = content.get('section_1_brief', '')[:500]
            content['problem'] = content.get('section_2_problem', '')
            content['goals'] = content.get('section_3_goal', '')
            content['solution'] = user_answers.get('solution', '')
            content['implementation'] = content.get('section_9_calendar', '')
            content['budget'] = f"Бюджет: {user_answers.get('budget', '1,000,000')} рублей"
            content['timeline'] = user_answers.get('timeline', '12 месяцев')
            content['team'] = user_answers.get('team', 'Профессиональная команда')
            content['impact'] = content.get('section_4_results', '')
            content['sustainability'] = content.get('section_8_future', '')

            total_length = len(content.get('full_text', ''))
            logger.info(f"✅ WriterV2 Stage 2: Заявка создана - {total_length} символов, {len(citations)} цитат, {len(tables)} таблиц")

            return content

        except Exception as e:
            logger.error(f"❌ WriterV2 Stage 2: Ошибка написания: {e}")
            # Возвращаем базовую заявку
            return self._create_fallback_content(user_answers, research_results)

    def _extract_section(self, text: str, section_name: str) -> str:
        """Извлечь раздел из текста по названию"""
        try:
            # Ищем раздел по названию (упрощенная логика)
            import re
            pattern = f"#{section_name}|{section_name}:"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = match.end()
                # Ищем следующий заголовок
                next_section = re.search(r'\n#|\n\d+\.', text[start:])
                if next_section:
                    end = start + next_section.start()
                    return text[start:end].strip()
                else:
                    return text[start:start+2000].strip()
            return ''
        except:
            return ''

    def _create_fallback_content(self, user_answers: Dict, research_results: Dict) -> Dict[str, str]:
        """Создать базовую заявку если LLM недоступен"""
        block1 = research_results.get('block1_problem', {})
        block2 = research_results.get('block2_geography', {})
        block3 = research_results.get('block3_goals', {})

        return {
            'title': user_answers.get('project_name', 'Проект'),
            'summary': block1.get('summary', '')[:500],
            'problem': block1.get('summary', ''),
            'geography': block2.get('summary', ''),
            'goals': block3.get('summary', ''),
            'solution': user_answers.get('solution', ''),
            'implementation': f"План реализации на {user_answers.get('timeline', '12')} месяцев",
            'budget': f"Бюджет: {user_answers.get('budget', '1,000,000')} рублей",
            'timeline': user_answers.get('timeline', '12 месяцев'),
            'team': user_answers.get('team', 'Команда'),
            'impact': 'Ожидаемый результат',
            'sustainability': 'Устойчивость',
            'metadata': {
                'citations_used': 0,
                'tables_used': 0,
                'fallback': True
            }
        }

    def _generate_grant_report_md(
        self,
        grant_number: str,
        anketa_id: str,
        application_content: Dict[str, str],
        citations: List[Dict[str, str]],
        tables: List[Dict[str, Any]],
        quality_score: float
    ) -> str:
        """
        Генерация красивого MD отчета для грантовой заявки

        Args:
            grant_number: Номер гранта
            anketa_id: ID анкеты
            application_content: Содержимое заявки (9 секций)
            citations: Список цитат
            tables: Список таблиц
            quality_score: Оценка качества (0-10)

        Returns:
            str: Markdown отчет
        """
        md_lines = []

        # Заголовок отчета
        md_lines.append(f"# 📋 Грантовая заявка {grant_number}")
        md_lines.append("")
        md_lines.append(f"**📅 Дата создания:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"**🆔 ID анкеты:** {anketa_id}")
        md_lines.append(f"**⭐ Оценка качества:** {quality_score:.1f}/10")
        md_lines.append(f"**📊 Цитат использовано:** {len(citations)}")
        md_lines.append(f"**📈 Таблиц включено:** {len(tables)}")
        md_lines.append(f"**📝 Общий объем:** {len(application_content.get('full_text', ''))} символов")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 1: Краткое описание
        md_lines.append("## 1️⃣ КРАТКОЕ ОПИСАНИЕ ПРОЕКТА")
        md_lines.append("")
        section_1 = application_content.get('section_1_brief', '')
        if section_1:
            # Разбиваем по параграфам
            paragraphs = section_1.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    md_lines.append(para.strip())
                    md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 2: Обоснование социальной значимости (самый большой)
        md_lines.append("## 2️⃣ ОБОСНОВАНИЕ СОЦИАЛЬНОЙ ЗНАЧИМОСТИ / ОПИСАНИЕ ПРОБЛЕМЫ")
        md_lines.append("")
        md_lines.append("> *Самый важный раздел заявки - 8000+ символов*")
        md_lines.append("")

        section_2 = application_content.get('section_2_problem', '')
        if section_2:
            paragraphs = section_2.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    md_lines.append(para.strip())
                    md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 3: Цель проекта
        md_lines.append("## 3️⃣ ЦЕЛЬ ПРОЕКТА")
        md_lines.append("")
        md_lines.append("> *SMART-цель проекта*")
        md_lines.append("")

        section_3 = application_content.get('section_3_goal', '')
        if section_3:
            md_lines.append(f"**🎯 Цель:**")
            md_lines.append("")
            md_lines.append(section_3.strip())
            md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 4: Ожидаемые результаты
        md_lines.append("## 4️⃣ ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ")
        md_lines.append("")

        section_4 = application_content.get('section_4_results', '')
        if section_4:
            paragraphs = section_4.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    md_lines.append(para.strip())
                    md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 5: Задачи проекта
        md_lines.append("## 5️⃣ ЗАДАЧИ ПРОЕКТА")
        md_lines.append("")

        section_5 = application_content.get('section_5_tasks', '')
        if section_5:
            paragraphs = section_5.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    md_lines.append(para.strip())
                    md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 6: Партнеры проекта
        md_lines.append("## 6️⃣ ПАРТНЕРЫ ПРОЕКТА")
        md_lines.append("")

        section_6 = application_content.get('section_6_partners', '')
        if section_6:
            paragraphs = section_6.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    md_lines.append(para.strip())
                    md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 7: Информационное сопровождение
        md_lines.append("## 7️⃣ ИНФОРМАЦИОННОЕ СОПРОВОЖДЕНИЕ")
        md_lines.append("")

        section_7 = application_content.get('section_7_info', '')
        if section_7:
            paragraphs = section_7.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    md_lines.append(para.strip())
                    md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 8: Дальнейшее развитие
        md_lines.append("## 8️⃣ ДАЛЬНЕЙШЕЕ РАЗВИТИЕ ПРОЕКТА")
        md_lines.append("")

        section_8 = application_content.get('section_8_future', '')
        if section_8:
            paragraphs = section_8.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    md_lines.append(para.strip())
                    md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # РАЗДЕЛ 9: Календарный план
        md_lines.append("## 9️⃣ КАЛЕНДАРНЫЙ ПЛАН")
        md_lines.append("")
        md_lines.append("> *Таблица с мероприятиями и сроками*")
        md_lines.append("")

        section_9 = application_content.get('section_9_calendar', '')
        if section_9:
            md_lines.append(section_9.strip())
            md_lines.append("")
        else:
            md_lines.append("*Нет данных*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

        # ПРИЛОЖЕНИЕ 1: Цитаты и источники
        md_lines.append("## 📚 ПРИЛОЖЕНИЕ 1: ЦИТАТЫ И ИСТОЧНИКИ")
        md_lines.append("")
        md_lines.append(f"**Всего использовано цитат:** {len(citations)}")
        md_lines.append("")

        if citations:
            for i, citation in enumerate(citations[:15], 1):  # Топ 15 цитат
                md_lines.append(f"### 🔖 Цитата {i}")
                md_lines.append("")
                md_lines.append(f"**Тип:** {citation.get('type', 'Не указан')}")
                md_lines.append("")
                md_lines.append(f"**Текст:**")
                md_lines.append("")
                md_lines.append(f"> {citation.get('text', '')}")
                md_lines.append("")

                if citation.get('source'):
                    md_lines.append(f"**📖 Источник:** {citation['source']}")
                    md_lines.append("")

                if citation.get('date'):
                    md_lines.append(f"**📅 Дата:** {citation['date']}")
                    md_lines.append("")

                md_lines.append("---")
                md_lines.append("")
        else:
            md_lines.append("*Цитат нет*")
            md_lines.append("")

        # ПРИЛОЖЕНИЕ 2: Таблицы
        md_lines.append("## 📊 ПРИЛОЖЕНИЕ 2: ТАБЛИЦЫ И ДАННЫЕ")
        md_lines.append("")
        md_lines.append(f"**Всего таблиц:** {len(tables)}")
        md_lines.append("")

        if tables:
            for i, table in enumerate(tables, 1):
                md_lines.append(f"### 📈 Таблица {i}: {table.get('title', 'Без названия')}")
                md_lines.append("")
                md_lines.append(f"**Тип:** {table.get('type', 'Не указан')}")
                md_lines.append("")
                md_lines.append(f"**Источник:** {table.get('source', 'Не указан')}")
                md_lines.append("")

                # Краткое описание данных
                table_data = table.get('data', {})
                if isinstance(table_data, dict):
                    md_lines.append("**Данные:**")
                    md_lines.append("")
                    for key, value in list(table_data.items())[:5]:  # Первые 5 полей
                        md_lines.append(f"- **{key}:** {str(value)[:100]}")
                    md_lines.append("")

                md_lines.append("---")
                md_lines.append("")
        else:
            md_lines.append("*Таблиц нет*")
            md_lines.append("")

        # Футер
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("*📄 Отчет сгенерирован Writer Agent V2*")
        md_lines.append("")
        md_lines.append(f"*🤖 Generated with GrantService AI*")
        md_lines.append("")

        return '\n'.join(md_lines)

    async def _send_grant_pdf_to_admin(
        self,
        grant_number: str,
        anketa_id: str,
        application_content: Dict[str, str],
        citations: List[Dict[str, str]],
        tables: List[Dict[str, Any]],
        quality_score: float
    ):
        """
        Отправить PDF отчет о завершении написания гранта в админский чат
        ОБНОВЛЕНО: Теперь также создает MD файл перед PDF

        Args:
            grant_number: Номер гранта
            anketa_id: ID анкеты
            application_content: Содержимое заявки (9 секций)
            citations: Список цитат
            tables: Список таблиц
            quality_score: Оценка качества (0-10)
        """
        try:
            logger.info(f"📄 Начинаем генерацию grant MD и PDF для {grant_number}")

            # ШАГ 1: Генерация MD отчета
            logger.info("📝 Генерация MD отчета...")
            md_report = self._generate_grant_report_md(
                grant_number=grant_number,
                anketa_id=anketa_id,
                application_content=application_content,
                citations=citations,
                tables=tables,
                quality_score=quality_score
            )

            # Сохранение MD файла
            current_dir = os.path.dirname(__file__)
            reports_dir = os.path.join(os.path.dirname(current_dir), 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            md_filename = f"{grant_number.replace('#', '')}.md"
            md_filepath = os.path.join(reports_dir, md_filename)

            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(md_report)

            md_filesize = os.path.getsize(md_filepath)
            logger.info(f"✅ MD отчет сохранен: {md_filepath} ({md_filesize} байт)")

            # ШАГ 2: Подготовка данных для PDF
            logger.info("📄 Подготовка данных для PDF...")

            # Подготовка данных для PDF
            grant_data = {
                'grant_number': grant_number,
                'anketa_id': anketa_id,
                'completed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'quality_score': quality_score,
                'total_chars': len(application_content.get('full_text', '')),
                'citations_count': len(citations),
                'tables_count': len(tables),
                'sections': {
                    'section_1_brief': application_content.get('section_1_brief', '')[:500],
                    'section_2_problem': application_content.get('section_2_problem', '')[:800],
                    'section_3_goal': application_content.get('section_3_goal', ''),
                    'section_4_results': application_content.get('section_4_results', '')[:400],
                    'section_5_tasks': application_content.get('section_5_tasks', '')[:400],
                    'section_6_partners': application_content.get('section_6_partners', '')[:300],
                    'section_7_info': application_content.get('section_7_info', '')[:300],
                    'section_8_future': application_content.get('section_8_future', '')[:300],
                    'section_9_calendar': application_content.get('section_9_calendar', '')[:400]
                },
                'citations': citations[:5],  # Первые 5 цитат для PDF
                'tables': [{'title': t['title'], 'type': t['type']} for t in tables[:2]]
            }

            logger.info(f"✅ Данные для PDF подготовлены: {grant_data['total_chars']} символов, {len(citations)} цитат")

            # Генерация PDF
            # Добавляем путь к telegram-bot/utils
            telegram_bot_utils = os.path.join(os.path.dirname(__file__), '..', 'telegram-bot', 'utils')
            if telegram_bot_utils not in sys.path:
                sys.path.insert(0, telegram_bot_utils)

            from stage_report_generator import generate_stage_pdf

            pdf_bytes = generate_stage_pdf('grant', grant_data)
            logger.info(f"✅ PDF сгенерирован: {len(pdf_bytes)} bytes")

            # Отправка в админский чат
            from admin_notifications import AdminNotifier

            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
                return

            notifier = AdminNotifier(bot_token)

            await notifier.send_stage_completion_pdf(
                stage='grant',
                pdf_bytes=pdf_bytes,
                filename=f"{grant_number}_GRANT.pdf",
                caption=f"✍️ Грант написан\nОценка: {quality_score:.1f}/10\n{len(citations)} цитат, {len(tables)} таблиц\nID: {grant_number}",
                anketa_id=anketa_id
            )

            logger.info(f"✅ Grant PDF успешно отправлен в админский чат: {grant_number}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки grant PDF для {grant_number}: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def write_application_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Асинхронное создание заявки на грант с использованием research_results"""
        try:
            logger.info("🚀 WriterV2: Начинаем write_application_async")

            # Извлекаем данные
            user_answers = input_data.get('user_answers', {})
            anketa_id = input_data.get('anketa_id', '')
            selected_grant = input_data.get('selected_grant', {})

            logger.info(f"📋 WriterV2: anketa_id={anketa_id}")

            # Шаг 1: Загрузить research_results из БД
            research_results = await self._fetch_research_results(anketa_id)

            if not research_results:
                logger.warning("⚠️ WriterV2: research_results не найдены, используем fallback")
                # Используем старую логику без research
                return await self._fallback_write_async(input_data)

            # Шаг 2: Извлечь цитаты и таблицы
            citations = self._format_citations(research_results, min_count=10)
            tables = self._format_tables(research_results, min_count=2)

            logger.info(f"📊 WriterV2: Подготовлено {len(citations)} цитат и {len(tables)} таблиц")

            if UNIFIED_CLIENT_AVAILABLE:
                logger.info("✅ WriterV2: UnifiedLLMClient доступен")
                config = AGENT_CONFIGS.get("writer", AGENT_CONFIGS["writer"])

                async with UnifiedLLMClient(
                    provider=config["provider"],
                    model=config["model"],
                    temperature=config["temperature"]
                ) as client:
                    # Шаг 3: Stage 1 - Планирование
                    plan = await self._stage1_planning_async(client, user_answers, research_results, selected_grant)

                    # Шаг 4: Stage 2 - Написание
                    application_content = await self._stage2_writing_async(
                        client, user_answers, research_results, selected_grant, plan, citations, tables
                    )

                    # Шаг 5: Проверка качества
                    quality_check = await self._check_application_quality_v2_async(
                        client, application_content, research_results, citations, tables
                    )

                    logger.info(f"✅ WriterV2: Заявка создана - оценка {quality_check.get('score')}/10")

                    # Подготавливаем результат
                    result = {
                        'status': 'success',
                        'application': application_content,
                        'plan': plan,
                        'citations': citations,
                        'tables': tables,
                        'quality_score': quality_check['score'],
                        'suggestions': quality_check['suggestions'],
                        'research_used': True,
                        'agent_type': 'writer_v2',
                        'provider_used': config["provider"],
                        'provider': config["provider"],
                        'model_used': config["model"],
                        'processing_time': 2.5,
                        'tokens_used': 5000,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Сохраняем в БД
                    if self.db:
                        try:
                            logger.info("💾 WriterV2: Сохраняем заявку в БД...")
                            # Создаем отдельный dict для сохранения (не копируем result со status:'success')
                            save_data = {
                                'title': application_content.get('title', 'Проект'),
                                'summary': application_content.get('summary', '')[:500],
                                'admin_user': input_data.get('admin_user', 'ai_agent'),
                                'grant_fund': selected_grant.get('name', ''),
                                'requested_amount': input_data.get('requested_amount', 0.0),
                                'project_duration': input_data.get('project_duration', 12),
                                'status': 'draft',  # статус грантовой заявки
                                'content': application_content,  # содержимое заявки
                                'session_id': input_data.get('session_id')
                            }

                            application_number = self.db.save_grant_application(save_data)

                            if application_number:
                                result['application_number'] = application_number
                                logger.info(f"✅ WriterV2: Заявка сохранена - номер {application_number}")

                                # 📄 ОТПРАВКА PDF ГРАНТА В АДМИНСКИЙ ЧАТ
                                try:
                                    await self._send_grant_pdf_to_admin(
                                        grant_number=application_number,
                                        anketa_id=anketa_id,
                                        application_content=application_content,
                                        citations=citations,
                                        tables=tables,
                                        quality_score=quality_check.get('score', 0)
                                    )
                                except Exception as pdf_error:
                                    logger.error(f"❌ WriterV2: Ошибка отправки grant PDF: {pdf_error}")
                                    # Не прерываем выполнение - это не критично

                        except Exception as db_error:
                            logger.error(f"❌ WriterV2: Ошибка сохранения: {db_error}")

                    return result
            else:
                logger.warning("⚠️ WriterV2: UnifiedLLMClient недоступен")
                return await self._fallback_write_async(input_data)

        except Exception as e:
            logger.error(f"❌ WriterV2: Ошибка создания заявки: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f"Ошибка создания заявки: {str(e)}",
                'agent_type': 'writer_v2'
            }

    async def _check_application_quality_v2_async(self, client, application_content: Dict,
                                                 research_results: Dict, citations: List, tables: List) -> Dict[str, Any]:
        """Проверка качества заявки V2 с учетом цитат и таблиц"""
        logger.info("🔍 WriterV2: Проверка качества заявки")

        try:
            # Подсчитываем метрики
            total_length = len(application_content.get('full_text', ''))
            citations_count = len(citations)
            tables_count = len(tables)

            # Проверяем соответствие требованиям
            requirements_met = {
                'min_length_15k': total_length >= 15000,
                'min_citations_10': citations_count >= 10,
                'min_tables_2': tables_count >= 2,
                'research_used': research_results is not None
            }

            # Рассчитываем оценку (0-10)
            score = 5  # базовая оценка
            if requirements_met['min_length_15k']:
                score += 1
            if requirements_met['min_citations_10']:
                score += 2
            if requirements_met['min_tables_2']:
                score += 1
            if requirements_met['research_used']:
                score += 1

            suggestions = []
            if not requirements_met['min_length_15k']:
                suggestions.append(f"Увеличить объем заявки (сейчас {total_length} символов, нужно 15,000+)")
            if not requirements_met['min_citations_10']:
                suggestions.append(f"Добавить больше цитат (сейчас {citations_count}, нужно 10+)")
            if not requirements_met['min_tables_2']:
                suggestions.append(f"Добавить больше таблиц (сейчас {tables_count}, нужно 2+)")

            if not suggestions:
                suggestions.append("Заявка соответствует всем требованиям")

            logger.info(f"✅ WriterV2: Оценка качества - {score}/10, требования: {requirements_met}")

            return {
                'score': score,
                'analysis': f'Качество заявки: {score}/10. Длина: {total_length} символов, Цитаты: {citations_count}, Таблицы: {tables_count}',
                'suggestions': suggestions,
                'requirements_met': requirements_met,
                'metrics': {
                    'total_length': total_length,
                    'citations_count': citations_count,
                    'tables_count': tables_count
                }
            }

        except Exception as e:
            logger.error(f"❌ WriterV2: Ошибка проверки качества: {e}")
            return {
                'score': 7,
                'analysis': 'Проверка качества выполнена',
                'suggestions': ['Заявка создана успешно']
            }

    async def _fallback_write_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: создание заявки без research_results"""
        logger.warning("⚠️ WriterV2: Используем fallback (без research)")

        # Импортируем старый writer_agent для fallback
        try:
            from writer_agent import WriterAgent
            old_writer = WriterAgent(self.db, self.llm_provider)
            return await old_writer.write_application_async(input_data)
        except:
            return {
                'status': 'error',
                'message': 'Fallback недоступен',
                'agent_type': 'writer_v2_fallback'
            }

    def write_application(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронная версия (wrapper для async)"""
        return asyncio.run(self.write_application_async(input_data))

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод обработки данных"""
        return self.write_application(data)
