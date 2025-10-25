#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест ТОЛЬКО Writer с GigaChat-2-Max
Использует существующие research results из БД
"""
import sys
import os
from pathlib import Path
import asyncio
import json
import time
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Пути к проекту
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "web-admin"))

# Загрузка .env.local
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Настройки
ANKETA_ID = "#AN-20251012-Natalia_bruzzzz-001"
GIGACHAT_MODEL = "GigaChat-2-Max"

# Путь к анкете
ANKETA_FILE = Path(__file__).parent.parent / "test_data" / "natalia_anketa_20251012.json"

def log(message: str, emoji: str = "📌"):
    """Логирование"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}", flush=True)

def load_anketa():
    """Загрузить анкету"""
    log(f"Загрузка анкеты: {ANKETA_FILE}", "📋")
    with open(ANKETA_FILE, 'r', encoding='utf-8') as f:
        anketa = json.load(f)
    log(f"Анкета загружена: {anketa.get('project_info', {}).get('name', '')[:50]}...", "✅")
    return anketa

async def main():
    """Главная функция"""
    log("="*80, "")
    log("ТЕСТ WRITER ONLY - GigaChat-2-Max", "✍️")
    log("="*80, "")

    start_time = time.time()

    # Загрузка анкеты
    anketa = load_anketa()

    # Настройка локальной БД
    log("Настройка подключения к ЛОКАЛЬНОЙ БД...", "🔌")
    os.environ['PGHOST'] = 'localhost'
    os.environ['PGPORT'] = '5432'
    os.environ['PGDATABASE'] = 'grantservice'
    os.environ['PGUSER'] = 'postgres'
    os.environ['PGPASSWORD'] = 'root'
    log("  ✅ БД: localhost:5432/grantservice", "")

    # Создание DB instance
    from data.database import get_db
    db = get_db()
    log(f"✅ Database instance created", "")
    log("", "")

    # WRITER V2
    try:
        log("ЗАПУСКАЕМ WRITER V2 с GigaChat-2-Max", "✍️")
        log("-" * 80, "")

        from writer_agent_v2 import WriterAgentV2

        log("Инициализация Writer V2...", "")
        writer = WriterAgentV2(
            db=db,
            llm_provider='gigachat'  # Явно указываем GigaChat
        )
        log("✅ Writer V2 инициализирован", "")

        input_data = {
            "anketa_id": ANKETA_ID,
            "user_answers": anketa.get("interview_data", {}),
            "selected_grant": {}
        }

        log(f"User answers length: {len(str(input_data['user_answers']))} chars", "📊")
        log("", "")
        log("🚀 Запускаем генерацию через GigaChat-2-Max...", "")
        log("   (должны увидеть логи из Writer и расход токенов GigaChat)", "")
        log("", "")

        result = await writer.write_application_async(input_data)

        duration = time.time() - start_time

        if result:
            log(f"✅ Writer завершён за {duration:.1f} секунд", "")
            log(f"   Status: {result.get('status')}", "")
            log(f"   Provider used: {result.get('provider_used')}", "")
            log(f"   Model used: {result.get('model_used')}", "")
            log(f"   Application length: {len(str(result.get('application', '')))} chars", "")
            log(f"   Quality score: {result.get('quality_score')}/10", "")

            if result.get('application_number'):
                log(f"   Application number: {result.get('application_number')}", "")
        else:
            log(f"❌ Writer вернул None", "")

        log("", "")
        log("="*80, "")
        log("ПРОВЕРЬТЕ АДМИНКУ GIGACHAT!", "🎯")
        log("Должен быть расход токенов если GigaChat работает", "")
        log("="*80, "")

    except Exception as e:
        log(f"❌ ОШИБКА Writer: {e}", "")
        import traceback
        print("\n" + "="*80)
        print("TRACEBACK:")
        print("="*80)
        traceback.print_exc()
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
