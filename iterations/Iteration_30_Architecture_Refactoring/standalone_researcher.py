#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StandaloneResearcher - Researcher Agent wrapper для standalone testing

ЦЕЛЬ: Отделить Researcher от Telegram Bot и database dependency

АРХИТЕКТУРА (Iteration 30):
- Принимает project_data (Dict) вместо anketa_id
- Использует WebSearchRouter для Perplexity API
- Генерирует 27 экспертных запросов
- Возвращает research_results (Dict)
- БЕЗ сохранения в БД (опционально)

Автор: Claude Code (Iteration 30)
Дата: 2025-10-24
Версия: 1.0
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import asyncio
import time
from datetime import datetime
import json

# Добавляем пути
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "agents"))

from shared.llm.websearch_router import WebSearchRouter
from agents.prompt_loader import ResearcherPromptLoader

logger = logging.getLogger(__name__)


class StandaloneResearcher:
    """
    Standalone Researcher - работает БЕЗ БД и Telegram Bot

    Использует:
    - ResearcherPromptLoader для генерации запросов
    - WebSearchRouter для Perplexity API
    - Возвращает structured research_results Dict

    Example:
        researcher = StandaloneResearcher(websearch_provider='perplexity')

        project_data = {
            "project_name": "Стрельба из лука",
            "problem": "Обучение детей...",
            "target_audience": "дети 7-17 лет",
            "geography": "Кемерово",
            "goals": ["Развитие спорта", "Патриотизм"]
        }

        research_results = await researcher.research(project_data)
    """

    def __init__(
        self,
        websearch_provider: str = 'perplexity',
        websearch_fallback: str = 'claude_code',
        db=None  # Optional для сохранения результатов
    ):
        """
        Args:
            websearch_provider: Провайдер для WebSearch (default: perplexity)
            websearch_fallback: Fallback провайдер (default: claude_code)
            db: Database instance (опционально, для сохранения результатов)
        """
        self.websearch_provider = websearch_provider
        self.websearch_fallback = websearch_fallback
        self.db = db

        # Инициализируем PromptLoader для генерации запросов
        self.prompt_loader = ResearcherPromptLoader()

        logger.info(f"[StandaloneResearcher] Initialized with {websearch_provider}")

    def _convert_project_data_to_anketa(self, project_data: Dict) -> Dict:
        """
        Конвертировать project_data в формат anketa для PromptLoader

        Args:
            project_data: {
                "project_name": "...",
                "problem": "...",
                "target_audience": "...",
                "geography": "...",
                "goals": [...]
            }

        Returns:
            anketa: Dict в формате для extract_placeholders()
        """
        # Создаём структуру анкеты из project_data
        anketa = {
            "interview_data": {
                "project_essence": project_data.get("project_name", ""),
                "problem_and_significance": project_data.get("problem", ""),
                "target_group": project_data.get("target_audience", ""),
                "geography": project_data.get("geography", ""),
                "main_goal": ", ".join(project_data.get("goals", [])) if isinstance(project_data.get("goals"), list) else project_data.get("goals", "")
            }
        }

        return anketa

    def _generate_queries(self, project_data: Dict) -> Dict[str, List[str]]:
        """
        Генерировать 27 экспертных запросов из project_data

        Args:
            project_data: Данные проекта

        Returns:
            {
                'block1': [...],  # 10 запросов про проблему
                'block2': [...],  # 10 запросов про географию
                'block3': [...]   # 7 запросов про цели
            }
        """
        logger.info(f"🔍 Генерируем запросы для: {project_data.get('project_name', 'Unknown')}")

        # Конвертируем в формат anketa
        anketa = self._convert_project_data_to_anketa(project_data)

        # Извлекаем placeholders через PromptLoader
        placeholders = self.prompt_loader.extract_placeholders(anketa)

        logger.info(f"📋 Placeholders:")
        logger.info(f"   - ПРОБЛЕМА: {placeholders['ПРОБЛЕМА'][:50]}...")
        logger.info(f"   - РЕГИОН: {placeholders['РЕГИОН']}")
        logger.info(f"   - СФЕРА: {placeholders['СФЕРА']}")

        # Загружаем шаблоны запросов (уже заполненные placeholders!)
        all_queries = {
            'block1': self.prompt_loader.get_block1_queries(placeholders),
            'block2': self.prompt_loader.get_block2_queries(placeholders),
            'block3': self.prompt_loader.get_block3_queries(placeholders)
        }

        logger.info(f"✅ Запросы подготовлены:")
        logger.info(f"   - Блок 1: {len(all_queries['block1'])} запросов")
        logger.info(f"   - Блок 2: {len(all_queries['block2'])} запросов")
        logger.info(f"   - Блок 3: {len(all_queries['block3'])} запросов")

        return all_queries

    async def _execute_websearch(
        self,
        queries: List[str],
        websearch_router: WebSearchRouter,
        allowed_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Выполнить WebSearch запросы через Perplexity (batch)

        Args:
            queries: Список запросов
            websearch_router: WebSearchRouter instance
            allowed_domains: Разрешённые домены (опционально)

        Returns:
            List[Dict]: Результаты поиска
        """
        try:
            logger.info(f"   Executing {len(queries)} queries via batch_websearch...")

            # Выполняем batch WebSearch
            batch_results = await websearch_router.batch_websearch(
                queries=queries,
                allowed_domains=allowed_domains,
                max_results=5
            )

            # Конвертируем в expected format
            results = []
            for i, query in enumerate(queries):
                if i < len(batch_results):
                    result = batch_results[i]
                    results.append({
                        'query': query,
                        'result': result,
                        'status': 'success' if result else 'failed'
                    })
                else:
                    results.append({
                        'query': query,
                        'error': 'No result returned',
                        'status': 'failed'
                    })

            return results

        except Exception as e:
            logger.warning(f"   ⚠️ Batch search error: {e}")
            # Return all as failed
            return [{
                'query': q,
                'error': str(e),
                'status': 'failed'
            } for q in queries]

    def _structure_results(
        self,
        block1_results: List[Dict],
        block2_results: List[Dict],
        block3_results: List[Dict],
        project_data: Dict
    ) -> Dict[str, Any]:
        """
        Структурировать результаты в финальный формат

        Args:
            block1_results: Результаты блока 1 (проблема)
            block2_results: Результаты блока 2 (география)
            block3_results: Результаты блока 3 (цели)
            project_data: Исходные данные проекта

        Returns:
            research_results: Structured dict
        """
        def extract_key_facts(results: List[Dict]) -> List[str]:
            """Извлечь ключевые факты из результатов"""
            facts = []
            for r in results:
                if r.get('status') == 'success' and r.get('result'):
                    # Берём первые 200 символов каждого результата
                    text = r['result'][:200] if isinstance(r['result'], str) else str(r['result'])[:200]
                    facts.append(text)
            return facts

        research_results = {
            "block1_problem": {
                "summary": f"Исследование проблемы: {project_data.get('problem', '')[:100]}...",
                "key_facts": extract_key_facts(block1_results),
                "total_sources": len([r for r in block1_results if r.get('status') == 'success']),
                "queries_executed": len(block1_results)
            },
            "block2_geography": {
                "summary": f"Анализ географии: {project_data.get('geography', '')}",
                "key_facts": extract_key_facts(block2_results),
                "total_sources": len([r for r in block2_results if r.get('status') == 'success']),
                "queries_executed": len(block2_results)
            },
            "block3_goals": {
                "summary": f"Исследование целей проекта",
                "key_facts": extract_key_facts(block3_results),
                "total_sources": len([r for r in block3_results if r.get('status') == 'success']),
                "queries_executed": len(block3_results)
            },
            "metadata": {
                "total_queries": len(block1_results) + len(block2_results) + len(block3_results),
                "websearch_provider": self.websearch_provider,
                "timestamp": datetime.now().isoformat(),
                "project_name": project_data.get("project_name", "Unknown")
            }
        }

        return research_results

    async def research(self, project_data: Dict) -> Dict[str, Any]:
        """
        Выполнить полное исследование БЕЗ БД зависимостей

        Args:
            project_data: {
                "project_name": "Стрельба из лука",
                "problem": "Обучение детей...",
                "target_audience": "дети 7-17 лет",
                "geography": "Кемерово",
                "goals": ["Развитие спорта", "Патриотизм"]
            }

        Returns:
            research_results: {
                "block1_problem": {...},
                "block2_geography": {...},
                "block3_goals": {...},
                "metadata": {
                    "total_queries": 27,
                    "websearch_provider": "perplexity"
                }
            }
        """
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("🔍 STANDALONE RESEARCHER - STARTING")
        logger.info("=" * 80)
        logger.info(f"Project: {project_data.get('project_name', 'Unknown')}")
        logger.info(f"Provider: {self.websearch_provider}")
        logger.info("")

        try:
            # 1. Генерировать 27 запросов
            all_queries = self._generate_queries(project_data)

            # 2. Выполнить запросы через WebSearchRouter
            async with WebSearchRouter(self.db) as websearch_router:

                # Проверить здоровье API
                healthy = await websearch_router.check_health()
                if not healthy:
                    logger.warning(f"⚠️ WebSearch provider {self.websearch_provider} not responding")

                # БЛОК 1: Проблема (10 запросов)
                logger.info("🔍 БЛОК 1: Проблема и социальная значимость (10 запросов)")
                block1_results = await self._execute_websearch(
                    queries=all_queries['block1'],
                    websearch_router=websearch_router,
                    allowed_domains=[
                        'rosstat.gov.ru',
                        'fedstat.ru',
                        'government.ru',
                        'nationalprojects.ru'
                    ]
                )
                logger.info(f"✅ Блок 1 завершён: {len(block1_results)} запросов")

                # БЛОК 2: География (10 запросов)
                logger.info("🌍 БЛОК 2: География и целевая аудитория (10 запросов)")
                block2_results = await self._execute_websearch(
                    queries=all_queries['block2'],
                    websearch_router=websearch_router
                )
                logger.info(f"✅ Блок 2 завершён: {len(block2_results)} запросов")

                # БЛОК 3: Цели (7 запросов)
                logger.info("🎯 БЛОК 3: Цели и задачи проекта (7 запросов)")
                block3_results = await self._execute_websearch(
                    queries=all_queries['block3'],
                    websearch_router=websearch_router
                )
                logger.info(f"✅ Блок 3 завершён: {len(block3_results)} запросов")

            # 3. Структурировать результаты
            research_results = self._structure_results(
                block1_results=block1_results,
                block2_results=block2_results,
                block3_results=block3_results,
                project_data=project_data
            )

            duration = time.time() - start_time

            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ STANDALONE RESEARCHER - COMPLETED")
            logger.info("=" * 80)
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Total queries: {research_results['metadata']['total_queries']}")
            logger.info(f"Block 1 sources: {research_results['block1_problem']['total_sources']}")
            logger.info(f"Block 2 sources: {research_results['block2_geography']['total_sources']}")
            logger.info(f"Block 3 sources: {research_results['block3_goals']['total_sources']}")
            logger.info("")

            return research_results

        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    """
    Quick test of StandaloneResearcher
    """
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test project data
    test_project_data = {
        "project_name": "Стрельба из лука - спортивно-патриотическое воспитание",
        "problem": "Уроки физкультуры не могут в полной мере привлечь детей к спорту",
        "target_audience": "Дети и молодёжь 10-21 лет",
        "geography": "г. Кемерово",
        "goals": ["Спортивно-патриотическое воспитание", "Пропаганда ЗОЖ", "Обучение стрельбе"]
    }

    async def main():
        researcher = StandaloneResearcher(websearch_provider='perplexity')
        research_results = await researcher.research(test_project_data)

        print("\n📊 RESEARCH RESULTS:")
        print(json.dumps(research_results, indent=2, ensure_ascii=False))

    asyncio.run(main())
