#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Researcher Agent V2 - агент для проведения исследований через 27 экспертных запросов

АРХИТЕКТУРА (обновлено 2025-10-11, v2.3):
- Database-Driven: WebSearch провайдер читается из ai_agent_settings.config.websearch_provider
- WebSearchRouter: Автоматический выбор провайдера с fallback (Perplexity → Claude Code)
- НЕ хардкодим: Провайдеры настраиваются через UI, без изменения кода

Использует:
- DatabasePromptManager для загрузки 27 запросов из БД (3 блока: 10+10+7)
- WebSearchRouter для автоматического выбора WebSearch провайдера
  - Perplexity API (primary): ~$0.01/запрос, работает из РФ, 100% success rate
  - Claude Code WebSearch (fallback): географические ограничения
- researcher_research таблица для хранения результатов в JSONB

Ключевые изменения v2.3:
- Заменен PerplexityWebSearchClient на WebSearchRouter
- Провайдер читается из БД через get_agent_settings('researcher')
- Поддержка fallback через websearch_fallback config
- Metadata содержит реальный использованный провайдер

Автор: AI Integration Specialist
Дата: 2025-10-11
Версия: 2.3
"""

import sys
import os
from typing import Dict, Any, List, Optional
import logging
import asyncio
import time
from datetime import datetime
import json

# Добавляем пути к модулям
sys.path.append('/var/GrantService/shared')
sys.path.append('/var/GrantService/agents')
# Добавляем путь к web-admin (с дефисом)
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'web-admin'))

from agents.base_agent import BaseAgent
from agents.prompt_loader import ResearcherPromptLoader  # Оставляем для fallback
from shared.llm.websearch_router import WebSearchRouter

# Импортируем DatabasePromptManager
try:
    from utils.prompt_manager import DatabasePromptManager, get_database_prompt_manager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    print("[WARN] DatabasePromptManager недоступен, используется ResearcherPromptLoader")
    PROMPT_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResearcherAgentV2(BaseAgent):
    """
    Researcher Agent V2: 27 экспертных запросов для грантовых заявок

    Workflow:
    1. Загрузить анкету из БД
    2. Извлечь placeholders через PromptLoader
    3. Сгенерировать 27 запросов (блок 1: 10, блок 2: 10, блок 3: 7)
    4. Выполнить запросы через PerplexityWebSearchClient (Perplexity API)
    5. Агрегировать результаты в JSONB структуру
    6. Сохранить в researcher_research.research_results

    NOTE: Switched from Claude Code WebSearch to Perplexity API due to geographical restrictions
    """

    def __init__(self, db, llm_provider: str = "claude_code", websearch_provider: str = None, websearch_fallback: str = None):
        """
        Инициализация агента

        Args:
            db: Database instance
            llm_provider: Провайдер LLM (по умолчанию claude_code)
            websearch_provider: WebSearch провайдер (опционально, если None - читается из БД)
            websearch_fallback: WebSearch fallback (опционально, если None - читается из БД)
        """
        super().__init__("researcher_v2", db, llm_provider)

        # Если провайдеры переданы напрямую, используем их
        if websearch_provider:
            self.websearch_provider = websearch_provider
            self.websearch_fallback = websearch_fallback or 'perplexity'
            logger.info(f"[ResearcherAgentV2] WebSearch provider (from params): {self.websearch_provider}")
            logger.info(f"[ResearcherAgentV2] WebSearch fallback (from params): {self.websearch_fallback}")
        else:
            # Читаем настройки WebSearch из БД (НЕ захардкожены!)
            try:
                # Импорт из web-admin (директория с дефисом)
                import importlib.util
                utils_path = os.path.join(current_dir, 'web-admin', 'utils', 'agent_settings.py')
                spec = importlib.util.spec_from_file_location("agent_settings", utils_path)
                agent_settings_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_settings_module)
                get_agent_settings = agent_settings_module.get_agent_settings

                settings = get_agent_settings('researcher')
                config = settings.get('config', {})

                # WebSearch провайдер из настроек (НЕ хардкод!)
                self.websearch_provider = config.get('websearch_provider', 'perplexity')
                self.websearch_fallback = config.get('websearch_fallback', 'claude_code')

                logger.info(f"[ResearcherAgentV2] WebSearch provider from DB: {self.websearch_provider}")
                logger.info(f"[ResearcherAgentV2] WebSearch fallback from DB: {self.websearch_fallback}")

            except Exception as e:
                logger.warning(f"[ResearcherAgentV2] Failed to load WebSearch settings from DB: {e}")
                logger.info("[ResearcherAgentV2] Using defaults: websearch_provider=claude_code, NO fallback (Claude Code ONLY policy)")
                self.websearch_provider = 'claude_code'
                self.websearch_fallback = None  # NO fallback - Claude Code ONLY

        # Инициализируем DatabasePromptManager
        self.prompt_manager: Optional[DatabasePromptManager] = None
        if PROMPT_MANAGER_AVAILABLE:
            try:
                self.prompt_manager = get_database_prompt_manager()
                logger.info("[OK] Researcher V2: DatabasePromptManager connected (27 queries from DB)")
            except Exception as e:
                logger.warning(f"[WARN] Could not initialize PromptManager: {e}")

        logger.info(f"[OK] ResearcherAgentV2 initialized with WebSearchRouter (provider={self.websearch_provider})")

    def _get_goal(self) -> str:
        """Получить goal агента из БД с fallback"""
        if self.prompt_manager:
            try:
                goal = self.prompt_manager.get_prompt('researcher_v2', 'goal')
                if goal:
                    return goal
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки goal из БД: {e}")

        # Fallback на hardcoded
        return "Провести комплексное исследование через 27 экспертных WebSearch запросов для грантовой заявки"

    def _get_backstory(self) -> str:
        """Получить backstory агента из БД с fallback"""
        if self.prompt_manager:
            try:
                backstory = self.prompt_manager.get_prompt('researcher_v2', 'backstory')
                if backstory:
                    return backstory
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки backstory из БД: {e}")

        # Fallback на hardcoded
        return """Ты эксперт-исследователь с 15-летним опытом в грантовом консалтинге.
        Специализация: поиск официальной статистики, анализ госпрограмм, изучение успешных кейсов.
        Используешь только проверенные российские источники: Росстат, министерства, нацпроекты."""

    async def research_with_expert_prompts(self, anketa_id: str) -> Dict[str, Any]:
        """
        Выполнить 27 экспертных запросов для исследования грантовой заявки

        Args:
            anketa_id: ID анкеты пользователя

        Returns:
            {
                'research_id': 'RES-...',
                'status': 'completed',
                'research_results': {
                    'block1_problem': {...},
                    'block2_geography': {...},
                    'block3_goals': {...},
                    'metadata': {...}
                }
            }
        """
        start_time = time.time()

        try:
            logger.info(f"🔍 Запуск исследования для anketa_id={anketa_id}")

            # 1. Получить анкету из БД
            anketa = await self._get_anketa(anketa_id)
            if not anketa:
                raise ValueError(f"Anketa {anketa_id} not found")

            logger.info(f"✅ Анкета загружена: user_id={anketa.get('user_id', anketa.get('telegram_id'))}")

            # 2. Создать запись в researcher_research (status='pending')
            research_id = await self._create_research_record(anketa_id, anketa)
            logger.info(f"📝 Создана запись исследования: {research_id}")

            # 3. Обновить статус на 'processing'
            await self._update_research_status(research_id, 'processing')

            # 4. Извлечь placeholders
            # Используем ResearcherPromptLoader только для извлечения placeholders
            loader = ResearcherPromptLoader()
            placeholders = loader.extract_placeholders(anketa)

            logger.info(f"📋 Placeholders извлечены:")
            logger.info(f"   - ПРОБЛЕМА: {placeholders['ПРОБЛЕМА'][:50]}...")
            logger.info(f"   - РЕГИОН: {placeholders['РЕГИОН']}")
            logger.info(f"   - СФЕРА: {placeholders['СФЕРА']}")

            # 5. Загрузить 27 запросов из БД (DatabasePromptManager) или fallback на PromptLoader
            all_queries = await self._load_queries_from_db_or_fallback(placeholders)

            logger.info(f"✅ Запросы подготовлены:")
            logger.info(f"   - Блок 1: {len(all_queries['block1'])} запросов")
            logger.info(f"   - Блок 2: {len(all_queries['block2'])} запросов")
            logger.info(f"   - Блок 3: {len(all_queries['block3'])} запросов")

            # 6. Выполнить запросы через WebSearchRouter (читает настройки из БД!)
            async with WebSearchRouter(self.db) as websearch_router:

                # Проверить здоровье API
                healthy = await websearch_router.check_health()
                if not healthy:
                    logger.warning(f"[WARN] WebSearch provider {self.websearch_provider} not responding, attempting to continue...")

                # БЛОК 1: Проблема и социальная значимость (10 запросов)
                logger.info("🔍 БЛОК 1: Проблема и социальная значимость (10 запросов)")
                block1_results = await self._execute_block_queries(
                    block_name="block1_problem",
                    queries=all_queries['block1'],
                    websearch_client=websearch_router,  # Router вместо прямого клиента!
                    allowed_domains=[
                        'rosstat.gov.ru',
                        'fedstat.ru',
                        'government.ru',
                        'nationalprojects.ru',
                        f"{placeholders.get('ПРОФИЛЬНОЕ_МИНИСТЕРСТВО', 'minsport')}.gov.ru",
                        'edu.gov.ru',
                        'minzdrav.gov.ru'
                    ],
                    placeholders=placeholders
                )

                logger.info(f"✅ Блок 1 завершён: {block1_results['total_sources']} источников")

                # 💾 СОХРАНИТЬ ДАННЫЕ БЛОКА 1 СРАЗУ!
                await self._save_block_results(research_id, 'block1_problem', block1_results)

                # БЛОК 2: География и целевая аудитория (10 запросов)
                logger.info("🌍 БЛОК 2: География и целевая аудитория (10 запросов)")
                block2_results = await self._execute_block_queries(
                    block_name="block2_geography",
                    queries=all_queries['block2'],
                    websearch_client=websearch_router,  # Router вместо прямого клиента!
                    allowed_domains=[
                        'rosstat.gov.ru',
                        'fedstat.ru',
                        'government.gov.ru',
                        f"{placeholders['РЕГИОН'].lower().replace(' ', '')}.gov.ru",  # Региональный портал
                        'minjust.gov.ru',
                        'asi.ru'
                    ],
                    placeholders=placeholders
                )

                logger.info(f"✅ Блок 2 завершён: {block2_results['total_sources']} источников")

                # 💾 СОХРАНИТЬ ДАННЫЕ БЛОКА 2 СРАЗУ!
                await self._save_block_results(research_id, 'block2_geography', block2_results)

                # БЛОК 3: Задачи, мероприятия и главная цель (7 запросов)
                logger.info("🎯 БЛОК 3: Задачи, мероприятия и главная цель (7 запросов)")
                block3_results = await self._execute_block_queries(
                    block_name="block3_goals",
                    queries=all_queries['block3'],
                    websearch_client=websearch_router,  # Router вместо прямого клиента!
                    allowed_domains=[
                        'rosstat.gov.ru',
                        'government.ru',
                        'nationalprojects.ru',
                        'asi.ru'
                    ],
                    placeholders=placeholders
                )

                logger.info(f"✅ Блок 3 завершён: {block3_results['total_sources']} источников")

                # 💾 СОХРАНИТЬ ДАННЫЕ БЛОКА 3 СРАЗУ!
                await self._save_block_results(research_id, 'block3_goals', block3_results)

                # Получить статистику (если метод доступен)
                client_stats = {}
                if hasattr(websearch_router, 'get_statistics'):
                    try:
                        client_stats = await websearch_router.get_statistics()
                    except:
                        pass

            # 7. Агрегировать результаты
            processing_time = time.time() - start_time

            research_results = {
                'block1_problem': block1_results,
                'block2_geography': block2_results,
                'block3_goals': block3_results,
                'metadata': {
                    'total_queries': 27,
                    'sources_count': (
                        block1_results['total_sources'] +
                        block2_results['total_sources'] +
                        block3_results['total_sources']
                    ),
                    'blocks': {
                        'block1': {
                            'queries': len(all_queries['block1']),
                            'sources': block1_results['total_sources'],
                            'processing_time': block1_results['processing_time']
                        },
                        'block2': {
                            'queries': len(all_queries['block2']),
                            'sources': block2_results['total_sources'],
                            'processing_time': block2_results['processing_time']
                        },
                        'block3': {
                            'queries': len(all_queries['block3']),
                            'sources': block3_results['total_sources'],
                            'processing_time': block3_results['processing_time']
                        }
                    },
                    'total_processing_time': int(processing_time),
                    'websearch_provider': self.websearch_provider,  # Читается из БД!
                    'websearch_fallback': self.websearch_fallback,  # Fallback provider
                    'websearch_stats': client_stats
                }
            }

            # 8. Сохранить результаты в БД
            await self._update_research_results(
                research_id=research_id,
                status='completed',
                research_results=research_results,
                completed_at=datetime.now()
            )

            logger.info(f"✅ Исследование завершено!")
            logger.info(f"   - Research ID: {research_id}")
            logger.info(f"   - Всего запросов: 27")
            logger.info(f"   - Всего источников: {research_results['metadata']['sources_count']}")
            logger.info(f"   - Время обработки: {processing_time:.2f}s")

            # 📄 ОТПРАВКА PDF В АДМИНСКИЙ ЧАТ
            try:
                await self._send_research_pdf_to_admin(
                    research_id=research_id,
                    anketa_id=anketa_id,
                    research_results=research_results,
                    queries=all_queries
                )
            except Exception as e:
                logger.error(f"❌ Ошибка отправки PDF в админский чат: {e}")
                # Не падаем если отправка не удалась - это не критично

            return {
                'research_id': research_id,
                'status': 'completed',
                'research_results': research_results
            }

        except Exception as e:
            logger.error(f"❌ Ошибка исследования: {e}", exc_info=True)

            # Обновить статус на 'error'
            if 'research_id' in locals():
                await self._update_research_status(
                    research_id,
                    'error',
                    error_message=str(e)
                )

            return {
                'research_id': locals().get('research_id'),
                'status': 'error',
                'error': str(e)
            }

    async def _get_anketa(self, anketa_id: str) -> Optional[Dict]:
        """Получить анкету из БД"""
        try:
            # Попробовать разные методы получения анкеты
            anketa = self.db.get_session_by_anketa_id(anketa_id)

            if not anketa:
                # Попробовать через прямой SQL запрос
                with self.db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM sessions WHERE anketa_id = %s LIMIT 1", (anketa_id,))
                    row = cursor.fetchone()
                    if row:
                        anketa = self.db._dict_row(cursor, row)
                    cursor.close()

            return anketa

        except Exception as e:
            logger.error(f"Ошибка получения анкеты {anketa_id}: {e}")
            return None

    async def _load_queries_from_db_or_fallback(self, placeholders: Dict) -> Dict[str, List[str]]:
        """
        Загрузить 27 запросов из БД или использовать fallback на PromptLoader

        Args:
            placeholders: Словарь с переменными для подстановки

        Returns:
            {'block1': [...], 'block2': [...], 'block3': [...]}
        """
        # Попытка загрузить запросы из БД через DatabasePromptManager
        if self.prompt_manager:
            try:
                logger.info("📥 Загрузка запросов из БД...")

                # Получить шаблоны запросов для каждого блока
                block1_templates = self.prompt_manager.get_researcher_queries(1)
                block2_templates = self.prompt_manager.get_researcher_queries(2)
                block3_templates = self.prompt_manager.get_researcher_queries(3)

                logger.info(f"✅ Загружено из БД: {len(block1_templates)} + {len(block2_templates)} + {len(block3_templates)} = {len(block1_templates) + len(block2_templates) + len(block3_templates)} запросов")

                # Применить placeholders к шаблонам
                block1_queries = [template.format(**placeholders) for template in block1_templates]
                block2_queries = [template.format(**placeholders) for template in block2_templates]
                block3_queries = [template.format(**placeholders) for template in block3_templates]

                return {
                    'block1': block1_queries,
                    'block2': block2_queries,
                    'block3': block3_queries
                }

            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки запросов из БД: {e}")
                logger.info("Fallback на ResearcherPromptLoader...")

        # Fallback на PromptLoader (hardcoded queries)
        logger.info("📥 Использование ResearcherPromptLoader (fallback)...")
        loader = ResearcherPromptLoader()
        all_queries = loader.get_all_queries(placeholders)

        return all_queries

    async def _create_research_record(self, anketa_id: str, anketa: Dict) -> str:
        """Создать запись исследования в БД с правильной номенклатурой"""
        # ✅ ПРАВИЛЬНАЯ НОМЕНКЛАТУРА: anketa_id-RS-001
        # Генерируем research_id через метод БД (номенклатура: #AN-DATE-username-NNN-RS-NNN)
        # Примеры: #AN-20251008-ekaterina_maksimova-001-RS-001

        user_id = anketa.get('user_id', anketa.get('telegram_id', 0))
        session_id = anketa.get('id', anketa.get('session_id'))

        research_data = {
            # НЕ передаём research_id - db.save_research_results сам сгенерирует через generate_research_id()
            'anketa_id': anketa_id,
            'user_id': user_id,
            'session_id': session_id,
            'research_type': 'expert_websearch_27_queries',
            'llm_provider': self.websearch_provider,  # Читается из БД!
            'model': 'router',  # WebSearchRouter вместо конкретной модели
            'status': 'pending',
            'created_at': datetime.now(),
            'research_results': {}
        }

        # Сохранить через метод БД
        saved_id = self.db.save_research_results(research_data)

        # ВАЖНО: Возвращаем ID из БД, а не локальную переменную!
        return saved_id

    async def _update_research_status(
        self,
        research_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Обновить статус исследования"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE researcher_research
                    SET status = %s
                    WHERE research_id = %s
                    """,
                    (status, research_id)
                )
                conn.commit()
                cursor.close()

            logger.info(f"📝 Статус обновлён: {research_id} → {status}")

        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")

    async def _update_research_results(
        self,
        research_id: str,
        status: str,
        research_results: Dict,
        completed_at: datetime
    ):
        """Обновить результаты исследования"""
        try:
            # PostgreSQL: JSONB
            results_json = json.dumps(research_results, ensure_ascii=False)

            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE researcher_research
                    SET status = %s,
                        research_results = %s::jsonb,
                        completed_at = %s
                    WHERE research_id = %s
                    """,
                    (status, results_json, completed_at, research_id)
                )
                conn.commit()
                cursor.close()

            logger.info(f"💾 Результаты сохранены: {research_id}")

        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")

    async def _save_block_results(
        self,
        research_id: str,
        block_name: str,
        block_results: Dict
    ):
        """
        Сохранить результаты блока СРАЗУ после выполнения

        Инкрементальное сохранение - обновляет только один блок в JSONB
        Так даже если произойдет ошибка, данные предыдущих блоков сохранятся
        """
        try:
            # Прочитать текущие результаты
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT research_results
                    FROM researcher_research
                    WHERE research_id = %s
                    """,
                    (research_id,)
                )
                row = cursor.fetchone()

                if row and row[0]:
                    current_results = row[0]
                else:
                    current_results = {}

                # Добавить новый блок
                current_results[block_name] = block_results

                # Сохранить обратно
                results_json = json.dumps(current_results, ensure_ascii=False)
                cursor.execute(
                    """
                    UPDATE researcher_research
                    SET research_results = %s::jsonb
                    WHERE research_id = %s
                    """,
                    (results_json, research_id)
                )
                conn.commit()
                cursor.close()

            logger.info(f"💾 Блок {block_name} сохранен: {block_results['total_sources']} источников")

        except Exception as e:
            logger.error(f"Ошибка сохранения блока {block_name}: {e}")

    async def _execute_block_queries(
        self,
        block_name: str,
        queries: List[str],
        websearch_client: WebSearchRouter,  # Router вместо конкретного клиента!
        allowed_domains: List[str],
        placeholders: Dict
    ) -> Dict:
        """
        Выполнить запросы для одного блока

        Args:
            block_name: Название блока (block1_problem, block2_geography, block3_goals)
            queries: Список запросов
            websearch_client: WebSearchRouter для автоматического выбора провайдера
            allowed_domains: Разрешенные домены
            placeholders: Placeholders для постобработки

        Returns:
            {
                'summary': 'Резюме блока',
                'key_facts': [...],
                'sources': [...],
                'queries_used': [...],
                'total_sources': 15,
                'processing_time': 120
            }
        """
        start_time = time.time()

        logger.info(f"   Выполнение {len(queries)} запросов для блока {block_name}...")

        # Выполнить batch WebSearch
        batch_results = await websearch_client.batch_websearch(
            queries=queries,
            allowed_domains=allowed_domains,
            max_results=5,
            max_concurrent=3
        )

        # Извлечь результаты
        all_results = []
        all_sources = []

        # WebSearchRouter возвращает прямые результаты, не обернутые в {'result': ...}
        for result in batch_results:
            all_results.append(result)

            # Собрать источники
            if result.get('sources'):
                all_sources.extend(result['sources'])

        # Уникальные источники
        unique_sources = list(set(all_sources))

        # Агрегировать результаты блока
        block_results = await self._aggregate_block_results(
            block_name=block_name,
            query_results=all_results,
            queries_used=queries,
            placeholders=placeholders
        )

        block_results['sources'] = unique_sources
        block_results['total_sources'] = len(unique_sources)
        block_results['processing_time'] = int(time.time() - start_time)

        logger.info(f"   ✅ Блок завершён: {len(unique_sources)} источников за {block_results['processing_time']}s")

        return block_results

    async def _aggregate_block_results(
        self,
        block_name: str,
        query_results: List[Dict],
        queries_used: List[str],
        placeholders: Dict
    ) -> Dict:
        """
        Агрегировать результаты запросов в структуру блока

        TODO: Здесь можно добавить LLM вызов для структурирования данных
        Пока возвращаем базовую структуру
        """
        # Извлечь все результаты в один текст
        all_text = ""
        for result in query_results:
            for item in result.get('results', []):
                all_text += f"{item.get('title', '')} {item.get('snippet', '')} "

        # Подсчитать ключевые факты (простая эвристика)
        key_facts = []
        for result in query_results:
            for item in result.get('results', []):
                if item.get('snippet'):
                    key_facts.append({
                        'fact': item['snippet'][:200],
                        'source': item.get('source', 'unknown'),
                        'url': item.get('url', ''),
                        'title': item.get('title', '')
                    })

        return {
            'summary': all_text[:500] if all_text else 'Нет данных',
            'key_facts': key_facts[:10],  # Топ 10 фактов
            'queries_used': queries_used,
            'raw_results': query_results  # Для дальнейшей обработки
        }

    def _generate_research_report_md(
        self,
        research_id: str,
        anketa_id: str,
        research_results: Dict,
        queries: Dict[str, List[str]],
        user_info: Dict
    ) -> str:
        """
        Генерация MD отчета исследования

        Args:
            research_id: ID исследования
            anketa_id: ID анкеты
            research_results: Результаты исследования
            queries: Все 27 запросов (dict с block1, block2, block3)
            user_info: Информация о пользователе

        Returns:
            str: MD отчет
        """
        md_lines = []

        # Заголовок
        md_lines.append("# Отчёт исследования грантовой заявки")
        md_lines.append("")

        # Метаданные
        full_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or user_info.get('username', 'Unknown')
        md_lines.append("## Метаданные")
        md_lines.append("")
        md_lines.append(f"- **ID Анкеты**: {anketa_id}")
        md_lines.append(f"- **ID Исследования**: {research_id}")
        md_lines.append(f"- **Пользователь**: {full_name} (@{user_info.get('username', 'unknown')})")
        md_lines.append(f"- **Telegram ID**: {user_info.get('telegram_id', 'unknown')}")
        md_lines.append(f"- **Дата завершения**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"- **Всего запросов**: 27")
        md_lines.append(f"- **Всего источников**: {research_results['metadata']['sources_count']}")
        md_lines.append(f"- **Время обработки**: {research_results['metadata']['total_processing_time']}s")
        md_lines.append(f"- **WebSearch провайдер**: {research_results['metadata']['websearch_provider']}")
        md_lines.append("")

        # Блок 1: Проблема и социальная значимость (10 запросов)
        md_lines.append("## Блок 1: Проблема и социальная значимость")
        md_lines.append("")
        md_lines.append(f"**Запросов**: {len(queries['block1'])}")
        md_lines.append(f"**Источников**: {research_results['block1_problem']['total_sources']}")
        md_lines.append(f"**Время обработки**: {research_results['block1_problem']['processing_time']}s")
        md_lines.append("")

        block1_results = research_results.get('block1_problem', {})
        raw_results = block1_results.get('raw_results', [])

        for i, query in enumerate(queries['block1'], 1):
            md_lines.append(f"### 🔍 Запрос {i}")
            md_lines.append("")
            md_lines.append(f"**❓ Вопрос:**")
            md_lines.append("")
            md_lines.append(f"> {query}")
            md_lines.append("")

            query_result = raw_results[i-1] if i-1 < len(raw_results) else {}

            # Используем полный синтезированный ответ из 'content' (не snippet!)
            full_answer = query_result.get('content', '')

            if full_answer:
                md_lines.append(f"**💬 Ответ:**")
                md_lines.append("")
                # Разбиваем по параграфам для читаемости
                paragraphs = full_answer.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        md_lines.append(para.strip())
                        md_lines.append("")

                # Источники из 'results' (топ 5 для полноты)
                if query_result.get('results'):
                    sources = [r.get('url', '') for r in query_result['results'] if r.get('url')][:5]
                    if sources:
                        md_lines.append(f"**🔗 Источники ({len(sources)}):**")
                        md_lines.append("")
                        for idx, source in enumerate(sources, 1):
                            md_lines.append(f"{idx}. {source}")
                        md_lines.append("")
            else:
                md_lines.append("**💬 Ответ:** Нет данных")
                md_lines.append("")

            # Разделитель между запросами
            md_lines.append("---")
            md_lines.append("")

        # Блок 2: География и целевая аудитория (10 запросов)
        md_lines.append("## Блок 2: География и целевая аудитория")
        md_lines.append("")
        md_lines.append(f"**Запросов**: {len(queries['block2'])}")
        md_lines.append(f"**Источников**: {research_results['block2_geography']['total_sources']}")
        md_lines.append(f"**Время обработки**: {research_results['block2_geography']['processing_time']}s")
        md_lines.append("")

        block2_results = research_results.get('block2_geography', {})
        raw_results = block2_results.get('raw_results', [])

        for i, query in enumerate(queries['block2'], 1):
            md_lines.append(f"### 🔍 Запрос {i + 10}")
            md_lines.append("")
            md_lines.append(f"**❓ Вопрос:**")
            md_lines.append("")
            md_lines.append(f"> {query}")
            md_lines.append("")

            query_result = raw_results[i-1] if i-1 < len(raw_results) else {}

            # Используем полный синтезированный ответ из 'content' (не snippet!)
            full_answer = query_result.get('content', '')

            if full_answer:
                md_lines.append(f"**💬 Ответ:**")
                md_lines.append("")
                # Разбиваем по параграфам для читаемости
                paragraphs = full_answer.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        md_lines.append(para.strip())
                        md_lines.append("")

                # Источники из 'results' (топ 5 для полноты)
                if query_result.get('results'):
                    sources = [r.get('url', '') for r in query_result['results'] if r.get('url')][:5]
                    if sources:
                        md_lines.append(f"**🔗 Источники ({len(sources)}):**")
                        md_lines.append("")
                        for idx, source in enumerate(sources, 1):
                            md_lines.append(f"{idx}. {source}")
                        md_lines.append("")
            else:
                md_lines.append("**💬 Ответ:** Нет данных")
                md_lines.append("")

            # Разделитель между запросами
            md_lines.append("---")
            md_lines.append("")

        # Блок 3: Задачи, мероприятия и главная цель (7 запросов)
        md_lines.append("## Блок 3: Задачи, мероприятия и главная цель")
        md_lines.append("")
        md_lines.append(f"**Запросов**: {len(queries['block3'])}")
        md_lines.append(f"**Источников**: {research_results['block3_goals']['total_sources']}")
        md_lines.append(f"**Время обработки**: {research_results['block3_goals']['processing_time']}s")
        md_lines.append("")

        block3_results = research_results.get('block3_goals', {})
        raw_results = block3_results.get('raw_results', [])

        for i, query in enumerate(queries['block3'], 1):
            md_lines.append(f"### 🔍 Запрос {i + 20}")
            md_lines.append("")
            md_lines.append(f"**❓ Вопрос:**")
            md_lines.append("")
            md_lines.append(f"> {query}")
            md_lines.append("")

            query_result = raw_results[i-1] if i-1 < len(raw_results) else {}

            # Используем полный синтезированный ответ из 'content' (не snippet!)
            full_answer = query_result.get('content', '')

            if full_answer:
                md_lines.append(f"**💬 Ответ:**")
                md_lines.append("")
                # Разбиваем по параграфам для читаемости
                paragraphs = full_answer.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        md_lines.append(para.strip())
                        md_lines.append("")

                # Источники из 'results' (топ 5 для полноты)
                if query_result.get('results'):
                    sources = [r.get('url', '') for r in query_result['results'] if r.get('url')][:5]
                    if sources:
                        md_lines.append(f"**🔗 Источники ({len(sources)}):**")
                        md_lines.append("")
                        for idx, source in enumerate(sources, 1):
                            md_lines.append(f"{idx}. {source}")
                        md_lines.append("")
            else:
                md_lines.append("**💬 Ответ:** Нет данных")
                md_lines.append("")

            # Разделитель между запросами
            md_lines.append("---")
            md_lines.append("")

        # Итоговая информация
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("## Итоги исследования")
        md_lines.append("")
        md_lines.append(f"- **Всего запросов выполнено**: 27")
        md_lines.append(f"- **Всего уникальных источников**: {research_results['metadata']['sources_count']}")
        md_lines.append(f"- **Общее время обработки**: {research_results['metadata']['total_processing_time']}s")
        md_lines.append(f"- **Использован провайдер**: {research_results['metadata']['websearch_provider']}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append(f"*Отчёт сгенерирован автоматически*  ")
        md_lines.append(f"*Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  ")
        md_lines.append(f"*ID отчёта: {research_id}*")

        return "\n".join(md_lines)

    async def _send_research_pdf_to_admin(
        self,
        research_id: str,
        anketa_id: str,
        research_results: Dict,
        queries: Dict[str, List[str]]
    ):
        """
        Отправить PDF отчет о завершении исследования в админский чат

        Args:
            research_id: ID исследования
            anketa_id: ID анкеты
            research_results: Результаты исследования
            queries: Все 27 запросов (dict с block1, block2, block3)
        """
        try:
            logger.info(f"📄 Генерация отчетов (MD + PDF) для research_id={research_id}")

            # Получить информацию о пользователе из БД
            user_info = {'username': 'Unknown', 'first_name': '', 'last_name': '', 'telegram_id': 0}
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.telegram_id, u.username, u.first_name, u.last_name
                    FROM users u
                    JOIN sessions s ON s.telegram_id = u.telegram_id
                    WHERE s.anketa_id = %s
                    LIMIT 1
                """, (anketa_id,))
                user_row = cursor.fetchone()

                if user_row:
                    if isinstance(user_row, tuple):
                        user_info = {
                            'telegram_id': user_row[0],
                            'username': user_row[1] or 'unknown',
                            'first_name': (user_row[2] or '').strip(),
                            'last_name': (user_row[3] or '').strip()
                        }
                    elif hasattr(user_row, '_asdict'):
                        user_dict = user_row._asdict()
                        user_info = {
                            'telegram_id': user_dict.get('telegram_id', 0),
                            'username': user_dict.get('username', 'unknown'),
                            'first_name': (user_dict.get('first_name', '') or '').strip(),
                            'last_name': (user_dict.get('last_name', '') or '').strip()
                        }

                cursor.close()

            logger.info(f"✅ User info получена: {user_info['username']}")

            # 1. Генерация MD отчета
            md_report = self._generate_research_report_md(
                research_id=research_id,
                anketa_id=anketa_id,
                research_results=research_results,
                queries=queries,
                user_info=user_info
            )

            # Сохранить MD файл
            md_filename = f"{research_id.replace('#', '')}.md"
            md_filepath = os.path.join(current_dir, 'reports', md_filename)
            os.makedirs(os.path.dirname(md_filepath), exist_ok=True)

            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(md_report)

            logger.info(f"✅ MD отчет сохранен: {md_filepath}")

            # 2. Генерация PDF отчета

            # Подготовка данных для PDF
            # Преобразуем результаты в формат для PDF генератора
            queries_list = []
            query_id = 1

            # Блок 1
            for i, query in enumerate(queries['block1']):
                block1_results = research_results.get('block1_problem', {})
                raw_results = block1_results.get('raw_results', [])
                query_result = raw_results[i] if i < len(raw_results) else {}

                # Извлекаем ПОЛНЫЙ ответ из 'content' (не snippet!)
                answer = query_result.get('content', '') or "Нет данных"

                # Источники (топ 5 для полноты)
                sources = []
                if query_result.get('results'):
                    sources = [r.get('url', '') for r in query_result['results'] if r.get('url')][:5]

                queries_list.append({
                    'query_id': query_id,
                    'question': query,
                    'answer': answer,
                    'sources': sources
                })
                query_id += 1

            # Блок 2
            for i, query in enumerate(queries['block2']):
                block2_results = research_results.get('block2_geography', {})
                raw_results = block2_results.get('raw_results', [])
                query_result = raw_results[i] if i < len(raw_results) else {}

                # Извлекаем ПОЛНЫЙ ответ из 'content' (не snippet!)
                answer = query_result.get('content', '') or "Нет данных"

                # Источники (топ 5 для полноты)
                sources = []
                if query_result.get('results'):
                    sources = [r.get('url', '') for r in query_result['results'] if r.get('url')][:5]

                queries_list.append({
                    'query_id': query_id,
                    'question': query,
                    'answer': answer,
                    'sources': sources
                })
                query_id += 1

            # Блок 3
            for i, query in enumerate(queries['block3']):
                block3_results = research_results.get('block3_goals', {})
                raw_results = block3_results.get('raw_results', [])
                query_result = raw_results[i] if i < len(raw_results) else {}

                # Извлекаем ПОЛНЫЙ ответ из 'content' (не snippet!)
                answer = query_result.get('content', '') or "Нет данных"

                # Источники (топ 5 для полноты)
                sources = []
                if query_result.get('results'):
                    sources = [r.get('url', '') for r in query_result['results'] if r.get('url')][:5]

                queries_list.append({
                    'query_id': query_id,
                    'question': query,
                    'answer': answer,
                    'sources': sources
                })
                query_id += 1

            # Формируем данные для PDF
            research_data = {
                'anketa_id': anketa_id,
                'research_id': research_id,
                'queries': queries_list,
                'summary': f"Всего запросов: 27. Всего источников: {research_results['metadata']['sources_count']}",
                'key_findings': f"Время обработки: {research_results['metadata']['total_processing_time']}s. Провайдер: {research_results['metadata']['websearch_provider']}",
                'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Импортируем генератор PDF через importlib (надежнее)
            import importlib.util
            pdf_gen_path = os.path.join(current_dir, 'telegram-bot', 'utils', 'stage_report_generator.py')
            spec_pdf = importlib.util.spec_from_file_location("stage_report_generator", pdf_gen_path)
            pdf_gen_module = importlib.util.module_from_spec(spec_pdf)
            spec_pdf.loader.exec_module(pdf_gen_module)
            generate_stage_pdf = pdf_gen_module.generate_stage_pdf

            # Генерируем PDF
            pdf_bytes = generate_stage_pdf('research', research_data)
            logger.info(f"✅ PDF сгенерирован: {len(pdf_bytes)} байт")

            # 3. Отправка PDF в админский чат с унифицированной caption
            # Импортируем AdminNotifier через importlib
            admin_notif_path = os.path.join(current_dir, 'telegram-bot', 'utils', 'admin_notifications.py')
            spec_admin = importlib.util.spec_from_file_location("admin_notifications", admin_notif_path)
            admin_module = importlib.util.module_from_spec(spec_admin)
            spec_admin.loader.exec_module(admin_module)
            AdminNotifier = admin_module.AdminNotifier

            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.warning("⚠️ TELEGRAM_BOT_TOKEN не найден, PDF не отправлен")
                return

            # Унифицированный формат caption (как в Interview и Audit)
            full_name = f"{user_info['first_name']} {user_info['last_name']}".strip() or user_info['username']
            sources_count = research_results['metadata']['sources_count']
            provider = research_results['metadata']['websearch_provider']
            completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            caption = f"""📊 ИССЛЕДОВАНИЕ ЗАВЕРШЕНО

📋 Анкета: {anketa_id}
👤 Пользователь: {full_name} (@{user_info['username']})
🆔 Telegram ID: {user_info['telegram_id']}
📅 Дата: {completed_at}
🔍 Запросов: 27
🌐 Источников: {sources_count}
⚙️ Провайдер: {provider}

PDF документ с полным исследованием прикреплен

#research #completed"""

            notifier = AdminNotifier(bot_token)
            success = await notifier.send_stage_completion_pdf(
                stage='research',
                pdf_bytes=pdf_bytes,
                filename=f"{research_id.replace('#', '')}.pdf",  # FIXED: Nomenclature
                caption=caption,
                anketa_id=anketa_id
            )

            if success:
                logger.info(f"✅ PDF отправлен в админский чат: {research_id}")
            else:
                logger.warning(f"⚠️ Не удалось отправить PDF в админский чат")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки PDF: {e}", exc_info=True)
            # Не бросаем исключение - отправка PDF не критична для работы агента

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод обработки (синхронная обёртка)"""
        anketa_id = data.get('anketa_id')

        if not anketa_id:
            return {
                'status': 'error',
                'message': 'anketa_id не указан'
            }

        # Запустить асинхронный метод
        return asyncio.run(self.research_with_expert_prompts(anketa_id))


# Для обратной совместимости
ResearcherAgent = ResearcherAgentV2
