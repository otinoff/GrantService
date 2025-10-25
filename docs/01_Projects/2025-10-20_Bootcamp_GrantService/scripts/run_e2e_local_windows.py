#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Локальный E2E Test для Windows - Sber500 Bootcamp

Запускает:
1. Researcher V2 (27 запросов)
2. Writer V2 с GigaChat-Max
3. Собирает метрики для буткэмпа

Анкета: Наталья (#AN-20251012-Natalia_bruzzzz-001)
"""

import sys
import os
from pathlib import Path
import asyncio
import json
import time
from datetime import datetime

# Пути к проекту (Windows)
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "web-admin"))

print(f"📁 Project root: {project_root}", flush=True)

# Загрузка .env.local для credentials
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    print(f"🔐 Loading credentials from: {env_file}", flush=True)
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print("✅ Credentials loaded", flush=True)
else:
    print(f"⚠️  .env.local not found: {env_file}", flush=True)

# Настройки
ANKETA_ID = "#AN-20251012-Natalia_bruzzzz-001"
GIGACHAT_MODEL = "GigaChat-2-Max"  # GigaChat 2.0 (second generation)
LLM_PROVIDER = "gigachat"

# Путь к анкете
ANKETA_FILE = Path(r"C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\test_data\natalia_anketa_20251012.json")

# Метрики
metrics = {
    "start_time": None,
    "end_time": None,
    "anketa_id": ANKETA_ID,
    "model": GIGACHAT_MODEL,
    "stages": {}
}

def log(message: str, emoji: str = "📌"):
    """Логирование с немедленным выводом"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}", flush=True)

def log_request(stage: str, request_type: str, details: str = ""):
    """Логирование запроса с немедленным выводом"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"→ [{timestamp}] [{stage}] {request_type}: {details}", flush=True)

def log_response(stage: str, response_type: str, details: str = "", success: bool = True):
    """Логирование ответа с немедленным выводом"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    emoji = "✓" if success else "✗"
    print(f"← [{timestamp}] [{stage}] {emoji} {response_type}: {details}", flush=True)

def load_anketa():
    """Загрузить анкету из JSON"""
    log(f"Загрузка анкеты: {ANKETA_FILE}", "📋")

    if not ANKETA_FILE.exists():
        log(f"ОШИБКА: Файл не найден: {ANKETA_FILE}", "❌")
        return None

    with open(ANKETA_FILE, 'r', encoding='utf-8') as f:
        anketa = json.load(f)

    log(f"Анкета загружена: {anketa.get('project_info', {}).get('name', 'Без названия')[:50]}...", "✅")
    return anketa

def check_credentials():
    """Проверить наличие credentials"""
    log("Проверка credentials...", "🔑")

    required = {
        "GIGACHAT_API_KEY": "GigaChat API",
        "PERPLEXITY_API_KEY": "Perplexity API (для Researcher)"
    }

    missing = []
    for env_var, name in required.items():
        if not os.getenv(env_var):
            missing.append(f"  ❌ {env_var} ({name})")
        else:
            log(f"  ✅ {name}", "")

    if missing:
        log("ОТСУТСТВУЮТ CREDENTIALS:", "⚠️")
        for m in missing:
            print(m)
        log("", "")
        log("Установите переменные окружения:", "💡")
        log("  set GIGACHAT_API_KEY=<your_key>", "")
        log("  set PERPLEXITY_API_KEY=<your_key>", "")
        log("", "")
        log("Или добавьте в .env файл", "💡")
        return False

    return True

async def main():
    """Главная функция"""
    log("="*80, "")
    log("E2E TEST - Sber500 Bootcamp (Локально)", "🚀")
    log("="*80, "")

    metrics["start_time"] = datetime.now().isoformat()

    # Проверка credentials
    if not check_credentials():
        log("Сначала настройте credentials", "⚠️")
        return

    # Загрузка анкеты
    anketa = load_anketa()
    if not anketa:
        return

    log("", "")
    log("ПЛАН:", "📝")
    log("  1. Researcher V2: 27 экспертных запросов (Perplexity)", "🔍")
    log("  2. Writer V2: Генерация заявки (GigaChat-Max)", "✍️")
    log("  3. Метрики для буткэмпа", "📊")
    log("", "")

    # Настройка переменных окружения для локальной БД
    log("Настройка подключения к ЛОКАЛЬНОЙ БД...", "🔌")
    os.environ['PGHOST'] = 'localhost'
    os.environ['PGPORT'] = '5432'
    os.environ['PGDATABASE'] = 'grantservice'
    os.environ['PGUSER'] = 'postgres'
    os.environ['PGPASSWORD'] = 'root'
    log("  ✅ БД: localhost:5432/grantservice", "")
    log("", "")

    # Создание DB instance
    from data.database import get_db
    db = get_db()
    log(f"✅ Database instance created", "")
    log("", "")

    # STAGE 1: Researcher V2
    try:
        log("STAGE 1: Researcher V2", "🔍")
        log("-" * 80, "")
        stage_start = time.time()

        log_request("RESEARCHER", "INIT", "Creating ResearcherAgentV2 instance")
        from researcher_agent_v2 import ResearcherAgentV2
        researcher = ResearcherAgentV2(
            db=db,
            llm_provider='gigachat',  # GigaChat для траты токенов!
            websearch_provider='gigachat'  # GigaChat вместо Perplexity!
        )
        log_response("RESEARCHER", "INIT", "ResearcherAgentV2 created", success=True)

        log_request("RESEARCHER", "START", f"Anketa: {ANKETA_ID}, Queries: 27, Provider: GigaChat-2-Max")
        log(f"🚀 Запуск 27 экспертных запросов через GigaChat-2-Max... (больше токенов!)", "")

        result = await researcher.research_with_expert_prompts(ANKETA_ID)

        if result:
            log_response("RESEARCHER", "COMPLETE", f"27 queries completed", success=True)
        else:
            log_response("RESEARCHER", "COMPLETE", "Result is None or False", success=False)

        stage_duration = time.time() - stage_start

        metrics["stages"]["researcher"] = {
            "status": "success" if result else "failed",
            "duration_seconds": round(stage_duration, 2),
            "queries": 27,
            "provider": "GigaChat-2-Max",
            "tokens_used": "~27 requests x tokens"
        }

        log(f"✅ Researcher завершён за {stage_duration:.1f} секунд", "")
        log("", "")

    except Exception as e:
        log_response("RESEARCHER", "ERROR", str(e), success=False)
        log(f"❌ ОШИБКА Researcher: {e}", "")
        import traceback
        print("\n" + "="*80, flush=True)
        print("RESEARCHER TRACEBACK:", flush=True)
        print("="*80, flush=True)
        traceback.print_exc()
        print("="*80 + "\n", flush=True)

        metrics["stages"]["researcher"] = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

    # STAGE 2: Writer V2
    try:
        log("STAGE 2: Writer V2 (GigaChat-2-Max)", "✍️")
        log("-" * 80, "")
        stage_start = time.time()

        log_request("WRITER", "INIT", "Creating WriterAgentV2 instance")
        from writer_agent_v2 import WriterAgentV2
        writer = WriterAgentV2(
            db=db,
            llm_provider='gigachat'
        )
        log_response("WRITER", "INIT", "WriterAgentV2 created", success=True)

        # Prepare input_data for Writer V2
        input_data = {
            "anketa_id": ANKETA_ID,
            "user_answers": anketa.get("interview_data", {}),
            "selected_grant": {}
        }

        log_request("WRITER", "START", f"Anketa: {ANKETA_ID}, Model: {GIGACHAT_MODEL}")
        log(f"🚀 Генерация заявки через GigaChat-2-Max...", "")

        result = await writer.write_application_async(input_data)

        if result:
            log_response("WRITER", "COMPLETE", f"Application generated", success=True)
        else:
            log_response("WRITER", "COMPLETE", "Result is None or False", success=False)

        stage_duration = time.time() - stage_start

        metrics["stages"]["writer"] = {
            "status": "success" if result else "failed",
            "duration_seconds": round(stage_duration, 2),
            "estimated_tokens": 18500,
            "model": GIGACHAT_MODEL
        }

        log(f"✅ Writer завершён за {stage_duration:.1f} секунд", "")
        log("", "")

    except Exception as e:
        log_response("WRITER", "ERROR", str(e), success=False)
        log(f"❌ ОШИБКА Writer: {e}", "")
        import traceback
        print("\n" + "="*80, flush=True)
        print("WRITER TRACEBACK:", flush=True)
        print("="*80, flush=True)
        traceback.print_exc()
        print("="*80 + "\n", flush=True)

        metrics["stages"]["writer"] = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

    # Финализация
    metrics["end_time"] = datetime.now().isoformat()

    # Сохранение метрик
    output_dir = Path(r"C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\test_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = output_dir / f"e2e_metrics_local_{timestamp}.json"

    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    log("="*80, "")
    log("ГОТОВО", "✅")
    log(f"Метрики: {metrics_file}", "💾")
    log("="*80, "")

    log("", "")
    log("СЛЕДУЮЩИЕ ШАГИ:", "🎯")
    log("  1. Настроить подключение к БД (или использовать удаленную)", "")
    log("  2. Запустить Researcher (27 запросов)", "")
    log("  3. Запустить Writer с GigaChat-Max", "")
    log("  4. Собрать метрики токенов", "")
    log("  5. Деплой 6 на production", "")

if __name__ == "__main__":
    asyncio.run(main())
