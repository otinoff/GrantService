#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенный E2E Test для Sber500 Bootcamp с GigaChat-Max
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

# PYTHONPATH уже установлен в wrapper скрипте
from data.database.models import GrantServiceDatabase
from agents.researcher_agent_v2 import ResearcherAgentV2
from agents.writer_agent_v2 import WriterAgentV2

# Настройки
ANKETA_ID = "#AN-20251012-Natalia_bruzzzz-001"
GIGACHAT_MODEL = "GigaChat-Max"
LLM_PROVIDER = "gigachat"

# Метрики
metrics = {
    "start_time": None,
    "end_time": None,
    "anketa_id": ANKETA_ID,
    "model": GIGACHAT_MODEL,
    "stages": {}
}

def log(message: str, emoji: str = "📌"):
    """Логирование"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}")

async def run_researcher(db, anketa_id: str):
    """Запустить Researcher Agent"""
    log("Запуск Researcher Agent", "🔍")
    start = time.time()

    try:
        researcher = ResearcherAgentV2(
            db=db,
            llm_provider="claude_code",
            websearch_provider="perplexity"
        )

        result = await researcher.run_research(anketa_id)
        elapsed = time.time() - start

        metrics["stages"]["researcher"] = {
            "status": "success" if result else "failed",
            "duration_seconds": round(elapsed, 2),
            "queries": 27
        }

        log(f"Researcher завершен за {elapsed:.1f}s", "✅")
        return result

    except Exception as e:
        elapsed = time.time() - start
        log(f"ОШИБКА Researcher: {e}", "❌")
        metrics["stages"]["researcher"] = {
            "status": "error",
            "duration_seconds": round(elapsed, 2),
            "error": str(e)
        }
        return None

async def run_writer(db, anketa_id: str):
    """Запустить Writer Agent с GigaChat-Max"""
    log(f"Запуск Writer Agent с {GIGACHAT_MODEL}", "✍️")
    start = time.time()

    try:
        writer = WriterAgentV2(db=db, llm_provider=LLM_PROVIDER)

        # Установить модель
        if hasattr(writer, 'llm_client') and writer.llm_client:
            writer.llm_client.model = GIGACHAT_MODEL
            log(f"Модель: {GIGACHAT_MODEL}", "🎯")

        result = await writer.write_grant_application(anketa_id)
        elapsed = time.time() - start

        if result and 'application_text' in result:
            text_length = len(result['application_text'])
            estimated_tokens = int(text_length * 1.3)
        else:
            text_length = 0
            estimated_tokens = 0

        metrics["stages"]["writer"] = {
            "status": "success" if result else "failed",
            "duration_seconds": round(elapsed, 2),
            "estimated_tokens": estimated_tokens,
            "model": GIGACHAT_MODEL
        }

        log(f"Writer завершен за {elapsed:.1f}s", "✅")
        log(f"Токены: ~{estimated_tokens:,}", "💰")
        return result

    except Exception as e:
        elapsed = time.time() - start
        log(f"ОШИБКА Writer: {e}", "❌")
        metrics["stages"]["writer"] = {
            "status": "error",
            "duration_seconds": round(elapsed, 2),
            "error": str(e)
        }
        return None

async def main():
    log("="*80, "")
    log("E2E TEST - Sber500 Bootcamp", "🚀")
    log("="*80, "")

    metrics["start_time"] = datetime.now().isoformat()

    # БД
    log("Подключение к БД...", "🔌")
    try:
        db = GrantServiceDatabase()
        log("БД подключена", "✅")
    except Exception as e:
        log(f"ОШИБКА БД: {e}", "❌")
        return

    log(f"Анкета: {ANKETA_ID}", "📋")
    log(f"Модель: {GIGACHAT_MODEL}", "🔥")
    log("")

    # Research
    log("--- RESEARCH ---", "🔍")
    research_result = await run_researcher(db, ANKETA_ID)
    if not research_result:
        log("Research failed", "❌")
        return
    log("")

    # Write
    log("--- WRITE ---", "✍️")
    write_result = await run_writer(db, ANKETA_ID)
    log("")

    # Metrics
    metrics["end_time"] = datetime.now().isoformat()
    metrics["total_duration"] = sum(
        s.get("duration_seconds", 0) for s in metrics["stages"].values()
    )

    # Save
    output_dir = Path("/var/GrantService/test_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = output_dir / f"e2e_metrics_{timestamp}.json"

    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    log("="*80, "")
    log("ОТЧЕТ", "📊")
    log("="*80, "")
    log(f"Модель: {GIGACHAT_MODEL}", "🎯")

    if "researcher" in metrics["stages"]:
        r = metrics["stages"]["researcher"]
        log(f"Researcher: {r['status']} ({r['duration_seconds']}s)", "🔍")

    if "writer" in metrics["stages"]:
        w = metrics["stages"]["writer"]
        log(f"Writer: {w['status']} ({w['duration_seconds']}s)", "✍️")
        if 'estimated_tokens' in w:
            log(f"Токены: ~{w['estimated_tokens']:,}", "💰")

    log(f"Время: {metrics['total_duration']:.1f}s", "⏱️")
    log(f"Метрики: {metrics_file}", "💾")
    log("="*80, "")

if __name__ == "__main__":
    asyncio.run(main())
