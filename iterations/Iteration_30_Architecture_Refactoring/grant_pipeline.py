#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GrantPipeline - Orchestrator для полного грантового потока

ЦЕЛЬ: Координировать Researcher → Writer → Auditor БЕЗ БД зависимостей

АРХИТЕКТУРА (Iteration 30):
- Принимает project_data (JSON input)
- Координирует 3 агента последовательно
- Экспортирует результаты в 3 текстовых файла
- Rate limit handling между агентами
- Полная независимость от Telegram Bot

Workflow:
1. Researcher (6-7 min) → research_results.json
2. Writer (1-2 min) → grant_application.md
3. Auditor (30 sec) → audit_report.json

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
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Импортируем standalone агенты
from standalone_researcher import StandaloneResearcher
from standalone_writer import StandaloneWriter
from standalone_auditor import StandaloneAuditor

logger = logging.getLogger(__name__)


class GrantPipeline:
    """
    Orchestrator для полного грантового потока
    БЕЗ зависимости от Telegram Bot!

    Example:
        config = load_config("test_config.json")

        pipeline = GrantPipeline(config)

        project_data = {
            "project_name": "...",
            "problem": "...",
            "target_audience": "...",
            "geography": "...",
            "goals": [...]
        }

        results = await pipeline.run(
            project_data=project_data,
            export_dir=Path("test_results/iteration_30")
        )
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Конфигурация из test_config.json
        """
        self.config = config

        # Извлекаем настройки
        llm_config = config.get('llm', {})
        gigachat_config = llm_config.get('gigachat', {})
        rate_limit_config = gigachat_config.get('rate_limit', {})

        perplexity_config = llm_config.get('perplexity', {})

        # Инициализируем агенты
        logger.info("=" * 80)
        logger.info("🚀 GRANT PIPELINE - INITIALIZING")
        logger.info("=" * 80)

        self.researcher = StandaloneResearcher(
            websearch_provider=perplexity_config.get('provider', 'perplexity')
        )
        logger.info("✅ Researcher initialized (Perplexity)")

        self.writer = StandaloneWriter(
            llm_provider='gigachat',
            rate_limit_delay=rate_limit_config.get('delay_between_requests', 6)
        )
        logger.info("✅ Writer initialized (GigaChat)")

        self.auditor = StandaloneAuditor(
            llm_provider='gigachat',
            rate_limit_delay=rate_limit_config.get('delay_between_requests', 6),
            retry_attempts=rate_limit_config.get('retry_attempts', 3)
        )
        logger.info("✅ Auditor initialized (GigaChat)")

        self.rate_limit_delay = rate_limit_config.get('delay_between_requests', 6)

        logger.info("")

    def _log_stage(self, stage: str, message: str):
        """Вывод лога с форматированием"""
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"{stage}: {message}")
        logger.info("=" * 80)
        logger.info("")

    async def run(
        self,
        project_data: Dict[str, Any],
        export_dir: Path
    ) -> Dict[str, Any]:
        """
        Запускает полный цикл: Researcher → Writer → Auditor

        Args:
            project_data: {
                "project_name": "...",
                "problem": "...",
                "target_audience": "...",
                "geography": "...",
                "goals": [...]
            }
            export_dir: Директория для экспорта результатов

        Returns:
            {
                "researcher": {...},
                "writer": "...",
                "auditor": {...},
                "exported_files": [...],
                "duration": {...}
            }
        """
        pipeline_start = time.time()

        # Создаём директорию для экспорта
        export_dir.mkdir(parents=True, exist_ok=True)

        logger.info("")
        logger.info("=" * 80)
        logger.info("🚀 STARTING GRANT PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Project: {project_data.get('project_name', 'Unknown')}")
        logger.info(f"Export dir: {export_dir}")
        logger.info("")

        try:
            # ============================================================
            # STAGE 1: Researcher (6-7 min)
            # ============================================================
            self._log_stage("🔍 STAGE 1/3", "Researcher (Perplexity)")
            logger.info(f"Expected duration: 6-7 minutes")
            logger.info(f"Queries: 27 expert queries")
            logger.info("")

            stage1_start = time.time()
            research_results = await self.researcher.research(project_data)
            stage1_duration = time.time() - stage1_start

            # Export research results
            research_file = export_dir / "1_research_results.json"
            with open(research_file, 'w', encoding='utf-8') as f:
                json.dump(research_results, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Stage 1 completed in {stage1_duration:.1f}s")
            logger.info(f"✅ Exported: {research_file.name}")

            # ============================================================
            # STAGE 2: Writer (1-2 min)
            # ============================================================
            self._log_stage("✍️ STAGE 2/3", "Writer (GigaChat)")
            logger.info(f"Expected duration: 1-2 minutes")
            logger.info(f"Target: 30,000+ characters, 10+ citations")
            logger.info("")

            stage2_start = time.time()
            grant_content = await self.writer.write(project_data, research_results)
            stage2_duration = time.time() - stage2_start

            # Export grant application
            grant_file = export_dir / "2_grant_application.md"
            with open(grant_file, 'w', encoding='utf-8') as f:
                f.write(grant_content)

            logger.info(f"✅ Stage 2 completed in {stage2_duration:.1f}s")
            logger.info(f"✅ Exported: {grant_file.name} ({len(grant_content)} chars)")

            # ============================================================
            # DELAY to avoid rate limit
            # ============================================================
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"⏳ RATE LIMIT PROTECTION: Waiting {self.rate_limit_delay}s...")
            logger.info("=" * 80)
            await asyncio.sleep(self.rate_limit_delay)

            # ============================================================
            # STAGE 3: Auditor (30 sec)
            # ============================================================
            self._log_stage("📊 STAGE 3/3", "Auditor (GigaChat)")
            logger.info(f"Expected duration: 30-60 seconds")
            logger.info(f"Target score: ≥ 80%, can_submit = true")
            logger.info("")

            stage3_start = time.time()
            audit_result = await self.auditor.audit(grant_content)
            stage3_duration = time.time() - stage3_start

            # Export audit report
            audit_file = export_dir / "3_audit_report.json"
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Stage 3 completed in {stage3_duration:.1f}s")
            logger.info(f"✅ Exported: {audit_file.name}")

            # ============================================================
            # PIPELINE COMPLETED
            # ============================================================
            pipeline_duration = time.time() - pipeline_start

            logger.info("")
            logger.info("=" * 80)
            logger.info("🎉 PIPELINE COMPLETED!")
            logger.info("=" * 80)
            logger.info(f"Total duration: {pipeline_duration:.1f}s ({pipeline_duration/60:.1f} min)")
            logger.info("")
            logger.info("📊 RESULTS:")
            logger.info(f"   Auditor score: {audit_result.get('overall_score', 0) * 100:.1f}%")
            logger.info(f"   Can submit: {audit_result.get('can_submit', False)}")
            logger.info(f"   Grant length: {len(grant_content)} characters")
            logger.info(f"   Research sources: {research_results.get('metadata', {}).get('total_queries', 0)} queries")
            logger.info("")
            logger.info("📁 EXPORTED FILES:")
            logger.info(f"   1. {research_file.name}")
            logger.info(f"   2. {grant_file.name}")
            logger.info(f"   3. {audit_file.name}")
            logger.info("=" * 80)
            logger.info("")

            return {
                "researcher": research_results,
                "writer": grant_content,
                "auditor": audit_result,
                "exported_files": [research_file, grant_file, audit_file],
                "duration": {
                    "stage1_researcher": stage1_duration,
                    "stage2_writer": stage2_duration,
                    "stage3_auditor": stage3_duration,
                    "total": pipeline_duration
                }
            }

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    """
    Quick test of GrantPipeline
    """
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test config
    test_config = {
        "llm": {
            "gigachat": {
                "model": "GigaChat-2-Max",
                "rate_limit": {
                    "delay_between_requests": 6,
                    "retry_attempts": 3
                }
            },
            "perplexity": {
                "provider": "perplexity"
            }
        }
    }

    # Test project data
    test_project_data = {
        "project_name": "Стрельба из лука - спортивно-патриотическое воспитание",
        "problem": "Уроки физкультуры не могут в полной мере привлечь детей к спорту",
        "target_audience": "Дети и молодёжь 10-21 лет",
        "geography": "г. Кемерово",
        "goals": ["Спортивно-патриотическое воспитание", "Пропаганда ЗОЖ"]
    }

    async def main():
        pipeline = GrantPipeline(test_config)

        results = await pipeline.run(
            project_data=test_project_data,
            export_dir=Path("test_results/pipeline_test")
        )

        print("\n✅ PIPELINE TEST COMPLETED!")
        print(f"Exported files: {len(results['exported_files'])}")

    asyncio.run(main())
