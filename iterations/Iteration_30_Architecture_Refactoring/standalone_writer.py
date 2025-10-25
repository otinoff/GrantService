#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StandaloneWriter - Writer Agent wrapper для standalone testing

ЦЕЛЬ: Отделить Writer от database dependency

АРХИТЕКТУРА (Iteration 30):
- Принимает project_data + research_results явно (Dict)
- НЕ загружает из БД внутри
- Использует GigaChat-2-Max для генерации
- Возвращает grant_content (str)
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

# Добавляем пути
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "agents"))

from shared.llm.unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)


class StandaloneWriter:
    """
    Standalone Writer - работает с явными параметрами, БЕЗ БД зависимостей

    Использует:
    - GigaChat-2-Max для генерации
    - Research results (from Researcher)
    - Project data
    - Rate limit handling (6s delay)

    Example:
        writer = StandaloneWriter(
            llm_provider='gigachat',
            rate_limit_delay=6
        )

        grant_content = await writer.write(
            project_data=project_data,
            research_results=research_results
        )
    """

    def __init__(
        self,
        llm_provider: str = 'gigachat',
        rate_limit_delay: int = 6,
        db=None  # Optional для сохранения
    ):
        """
        Args:
            llm_provider: LLM провайдер (default: gigachat)
            rate_limit_delay: Задержка между запросами (секунды)
            db: Database instance (опционально)
        """
        self.llm_provider = llm_provider
        self.rate_limit_delay = rate_limit_delay
        self.db = db

        # Инициализируем LLM client
        self.llm_client = UnifiedLLMClient(provider=llm_provider)

        logger.info(f"[StandaloneWriter] Initialized with {llm_provider}")

    def _format_citations(self, research_results: Dict) -> List[str]:
        """
        Извлечь цитаты из research_results

        Args:
            research_results: Результаты от Researcher

        Returns:
            List[str]: Список цитат
        """
        citations = []

        for block_name in ['block1_problem', 'block2_geography', 'block3_goals']:
            block = research_results.get(block_name, {})
            facts = block.get('key_facts', [])

            for fact in facts[:5]:  # Берём первые 5 из каждого блока
                citations.append(fact)

        logger.info(f"📊 Extracted {len(citations)} citations from research")
        return citations

    def _build_context(
        self,
        project_data: Dict,
        research_results: Dict,
        citations: List[str]
    ) -> str:
        """
        Построить контекст для LLM

        Args:
            project_data: Данные проекта
            research_results: Результаты исследования
            citations: Цитаты из исследования

        Returns:
            str: Контекст для промпта
        """
        context = f"""
# ДАННЫЕ ПРОЕКТА

Название проекта: {project_data.get('project_name', '')}

Проблема: {project_data.get('problem', '')}

Целевая аудитория: {project_data.get('target_audience', '')}

География: {project_data.get('geography', '')}

Цели: {', '.join(project_data.get('goals', [])) if isinstance(project_data.get('goals'), list) else project_data.get('goals', '')}

# РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ

## Блок 1: Проблема
{research_results.get('block1_problem', {}).get('summary', '')}

Ключевые факты:
{chr(10).join(f'- {fact[:200]}...' for fact in research_results.get('block1_problem', {}).get('key_facts', [])[:3])}

## Блок 2: География
{research_results.get('block2_geography', {}).get('summary', '')}

Ключевые факты:
{chr(10).join(f'- {fact[:200]}...' for fact in research_results.get('block2_geography', {}).get('key_facts', [])[:3])}

## Блок 3: Цели
{research_results.get('block3_goals', {}).get('summary', '')}

Ключевые факты:
{chr(10).join(f'- {fact[:200]}...' for fact in research_results.get('block3_goals', {}).get('key_facts', [])[:3])}

# ДОСТУПНЫЕ ЦИТАТЫ

Используй эти цитаты в заявке (минимум 10 цитат):

{chr(10).join(f'{i+1}. {cit[:300]}...' for i, cit in enumerate(citations[:15]))}
"""
        return context

    def _build_prompt(
        self,
        project_data: Dict,
        research_results: Dict,
        citations: List[str]
    ) -> str:
        """
        Построить полный промпт для генерации заявки

        Args:
            project_data: Данные проекта
            research_results: Результаты исследования
            citations: Цитаты

        Returns:
            str: Полный промпт
        """
        context = self._build_context(project_data, research_results, citations)

        prompt = f"""
Ты эксперт по написанию грантовых заявок с опытом работы 15+ лет.

Твоя задача - создать качественную заявку на грант для Фонда президентских грантов (ФПГ).

ТРЕБОВАНИЯ:
1. Минимум 30,000 символов
2. Минимум 10 цитат из исследования (используй [Источник №X])
3. Минимум 2 таблицы с данными
4. Структура:
   - Краткое описание проекта (500 слов)
   - Описание проблемы (1500 слов + цитаты)
   - География проекта (800 слов)
   - Целевая аудитория (800 слов)
   - Цели и задачи (1000 слов)
   - Мероприятия проекта (1500 слов)
   - Ожидаемые результаты (1000 слов + таблицы)
   - Партнёры проекта (500 слов)
   - Устойчивость проекта (800 слов)

ВАЖНО:
- Используй ТОЛЬКО данные из исследования
- Все цитаты должны быть размечены [Источник №X]
- Цифры должны быть из официальных источников
- Пиши профессиональным языком
- Избегай общих фраз

{context}

НАЧИНАЙ ГЕНЕРАЦИЮ ЗАЯВКИ:
"""
        return prompt

    async def write(
        self,
        project_data: Dict,
        research_results: Dict
    ) -> str:
        """
        Написать грантовую заявку БЕЗ БД зависимостей

        Args:
            project_data: {
                "project_name": "...",
                "problem": "...",
                "target_audience": "...",
                "geography": "...",
                "goals": [...]
            }
            research_results: Результаты от Researcher {
                "block1_problem": {...},
                "block2_geography": {...},
                "block3_goals": {...}
            }

        Returns:
            grant_content: str (полный текст заявки)
        """
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("✍️ STANDALONE WRITER - STARTING")
        logger.info("=" * 80)
        logger.info(f"Project: {project_data.get('project_name', 'Unknown')}")
        logger.info(f"LLM Provider: {self.llm_provider}")
        logger.info(f"Rate limit delay: {self.rate_limit_delay}s")
        logger.info("")

        try:
            # 1. Извлечь цитаты из research_results
            citations = self._format_citations(research_results)

            logger.info(f"📊 Citations prepared: {len(citations)}")

            # 2. Построить промпт
            prompt = self._build_prompt(project_data, research_results, citations)

            logger.info(f"📝 Prompt built: {len(prompt)} characters")

            # 3. Генерировать через LLM
            logger.info("🤖 Generating grant application...")
            logger.info(f"   (This may take 1-2 minutes)")

            async with self.llm_client as client:
                grant_content = await client.generate_text(
                    prompt=prompt,
                    max_tokens=20000  # Большой лимит для 30k+ символов
                )

            duration = time.time() - start_time

            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ STANDALONE WRITER - COMPLETED")
            logger.info("=" * 80)
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Grant length: {len(grant_content)} characters")
            logger.info(f"Citations used: ~{grant_content.count('[Источник')}")
            logger.info("")

            return grant_content

        except Exception as e:
            logger.error(f"❌ Writer failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    """
    Quick test of StandaloneWriter
    """
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test data
    test_project_data = {
        "project_name": "Стрельба из лука - спортивно-патриотическое воспитание",
        "problem": "Уроки физкультуры не могут в полной мере привлечь детей к спорту",
        "target_audience": "Дети и молодёжь 10-21 лет",
        "geography": "г. Кемерово",
        "goals": ["Спортивно-патриотическое воспитание", "Пропаганда ЗОЖ"]
    }

    test_research_results = {
        "block1_problem": {
            "summary": "Проблема привлечения детей к спорту актуальна",
            "key_facts": [
                "Согласно Росстат, только 30% детей регулярно занимаются спортом",
                "Физкультура в школах не покрывает потребности в физической активности"
            ],
            "total_sources": 10
        },
        "block2_geography": {
            "summary": "Кемерово - промышленный город с населением 550 тыс.",
            "key_facts": [
                "В Кемерово 50+ школ и 10+ вузов",
                "Спортивная инфраструктура развита"
            ],
            "total_sources": 8
        },
        "block3_goals": {
            "summary": "Патриотическое воспитание через спорт",
            "key_facts": [
                "Стрельба из лука развивает дисциплину",
                "Прикладной навык для армейской службы"
            ],
            "total_sources": 7
        },
        "metadata": {
            "total_queries": 27,
            "websearch_provider": "perplexity"
        }
    }

    async def main():
        writer = StandaloneWriter(llm_provider='gigachat')

        grant_content = await writer.write(
            project_data=test_project_data,
            research_results=test_research_results
        )

        print("\n📄 GRANT APPLICATION:")
        print(grant_content[:1000])
        print(f"\n... (total {len(grant_content)} characters)")

    asyncio.run(main())
