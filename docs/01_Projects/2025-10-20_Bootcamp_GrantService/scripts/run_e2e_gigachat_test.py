#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test для Sber500 Bootcamp с GigaChat-Max

Запускает полный цикл:
1. Researcher Agent (WebSearch через Perplexity)
2. Writer Agent (генерация заявки через GigaChat-Max)
3. Собирает метрики для буткэмпа

Анкета: Наталья (#AN-20251012-Natalia_bruzzzz-001)
Проект: Стрельба из лука - спортивно-патриотическое воспитание
"""

import sys
import os
from pathlib import Path
import asyncio
import json
import time
from datetime import datetime

# Пути к проекту
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "web-admin"))

# Импорты
from agents.researcher_agent_v2 import ResearcherAgentV2
from agents.writer_agent_v2 import WriterAgentV2
from shared.database.db_utils import DatabaseManager

# Настройки для буткэмпа
ANKETA_ID = "#AN-20251012-Natalia_bruzzzz-001"
GIGACHAT_MODEL = "GigaChat-Max"  # 🔥 ИСПОЛЬЗУЕМ MAX для пакетных токенов!
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
    """Логирование с эмодзи"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}")

async def run_researcher(db, anketa_id: str):
    """
    Запустить Researcher Agent

    NOTE: Researcher использует WebSearch (Perplexity), не использует GigaChat-Max
    """
    log("Запуск Researcher Agent (WebSearch через Perplexity)", "🔍")
    start = time.time()

    try:
        # Создаем агента (websearch через Perplexity)
        researcher = ResearcherAgentV2(
            db=db,
            llm_provider="claude_code",  # Для генерации промптов (не используется в поиске)
            websearch_provider="perplexity"
        )

        # Запускаем исследование
        log(f"Исследуем анкету: {anketa_id}", "📊")
        result = await researcher.run_research(anketa_id)

        elapsed = time.time() - start

        # Сохраняем метрики
        metrics["stages"]["researcher"] = {
            "status": "success" if result else "failed",
            "duration_seconds": round(elapsed, 2),
            "queries_count": 27,  # 27 экспертных запросов
            "provider": "Perplexity API"
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
    """
    Запустить Writer Agent с GigaChat-Max

    🔥 ЭТО ГЛАВНАЯ ТОЧКА ИСПОЛЬЗОВАНИЯ GIGACHAT-MAX ТОКЕНОВ!
    """
    log(f"Запуск Writer Agent с {GIGACHAT_MODEL}", "✍️")
    start = time.time()

    try:
        # Создаем агента с GigaChat-Max
        writer = WriterAgentV2(
            db=db,
            llm_provider=LLM_PROVIDER
        )

        # ВАЖНО: Нужно установить модель в UnifiedLLMClient
        if hasattr(writer, 'llm_client') and writer.llm_client:
            writer.llm_client.model = GIGACHAT_MODEL
            log(f"Модель установлена: {GIGACHAT_MODEL}", "🎯")

        # Запускаем генерацию заявки
        log(f"Генерируем грантовую заявку для: {anketa_id}", "📝")
        result = await writer.write_grant_application(anketa_id)

        elapsed = time.time() - start

        # Оценка использованных токенов (примерно)
        if result and 'application_text' in result:
            text_length = len(result['application_text'])
            estimated_tokens = text_length * 1.3  # ~1.3 токена на символ для русского
        else:
            estimated_tokens = 0

        # Сохраняем метрики
        metrics["stages"]["writer"] = {
            "status": "success" if result else "failed",
            "duration_seconds": round(elapsed, 2),
            "estimated_tokens": int(estimated_tokens),
            "provider": LLM_PROVIDER,
            "model": GIGACHAT_MODEL,
            "application_length": text_length if result else 0
        }

        log(f"Writer завершен за {elapsed:.1f}s", "✅")
        log(f"Оценка токенов: ~{int(estimated_tokens):,}", "💰")
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
    """Главная функция E2E теста"""
    log("="*80, "")
    log("E2E TEST для Sber500 Bootcamp", "🚀")
    log("="*80, "")

    metrics["start_time"] = datetime.now().isoformat()

    # Подключение к БД
    log("Подключение к PostgreSQL...", "🔌")
    try:
        db = DatabaseManager()
        log("PostgreSQL подключен", "✅")
    except Exception as e:
        log(f"ОШИБКА подключения к БД: {e}", "❌")
        return

    # Информация об анкете
    log(f"Анкета: {ANKETA_ID}", "📋")
    log(f"Проект: Стрельба из лука - спортивно-патриотическое воспитание", "🎯")
    log(f"Модель: {GIGACHAT_MODEL} (пакетные токены!)", "🔥")
    log("")

    # ЭТАП 1: Research (WebSearch)
    log("--- ЭТАП 1: ИССЛЕДОВАНИЕ ---", "🔍")
    research_result = await run_researcher(db, ANKETA_ID)

    if not research_result:
        log("Исследование не выполнено, прерываем", "❌")
        return

    log("")

    # ЭТАП 2: Write (GigaChat-Max)
    log("--- ЭТАП 2: НАПИСАНИЕ ЗАЯВКИ ---", "✍️")
    write_result = await run_writer(db, ANKETA_ID)

    if not write_result:
        log("Заявка не сгенерирована", "❌")

    log("")

    # Финализация метрик
    metrics["end_time"] = datetime.now().isoformat()
    metrics["total_duration_seconds"] = sum(
        stage.get("duration_seconds", 0)
        for stage in metrics["stages"].values()
    )

    # Сохраняем метрики для буткэмпа
    output_dir = Path(__file__).parent.parent / "test_results"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = output_dir / f"e2e_metrics_{timestamp}.json"

    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    log("="*80, "")
    log("ОТЧЕТ ДЛЯ БУТКЭМПА", "📊")
    log("="*80, "")
    log(f"Модель: {GIGACHAT_MODEL}", "🎯")
    log(f"Анкета: {ANKETA_ID}", "📋")

    if "researcher" in metrics["stages"]:
        r = metrics["stages"]["researcher"]
        log(f"Researcher: {r['status']} ({r['duration_seconds']}s)", "🔍")

    if "writer" in metrics["stages"]:
        w = metrics["stages"]["writer"]
        log(f"Writer: {w['status']} ({w['duration_seconds']}s)", "✍️")
        if 'estimated_tokens' in w:
            log(f"Токены GigaChat-Max: ~{w['estimated_tokens']:,}", "💰")

    log(f"Общее время: {metrics['total_duration_seconds']:.1f}s", "⏱️")
    log(f"Метрики сохранены: {metrics_file}", "💾")
    log("="*80, "")

    log("E2E Test завершен!", "✅")

if __name__ == "__main__":
    asyncio.run(main())
