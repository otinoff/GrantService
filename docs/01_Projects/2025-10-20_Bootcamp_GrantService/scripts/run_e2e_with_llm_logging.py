#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test с ДЕТАЛЬНЫМ логированием LLM взаимодействий
Показывает первые 500 символов всех запросов/ответов
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

# Добавляем путь к llm_logger
sys.path.insert(0, str(Path(__file__).parent))

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

# Import LLM Logger
from llm_logger import get_llm_logger

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

# Monkey-patch UnifiedLLMClient для логирования
def patch_unified_llm_client():
    """Патчим UnifiedLLMClient чтобы логировать все запросы"""
    from llm.unified_llm_client import UnifiedLLMClient

    original_generate_gigachat = UnifiedLLMClient._generate_gigachat

    async def logged_generate_gigachat(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """Обёртка с логированием"""
        llm_logger = get_llm_logger()

        llm_logger.log_request(
            agent="writer",
            stage="gigachat_call",
            prompt=prompt,
            model=self.model,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens
        )

        try:
            response = await original_generate_gigachat(self, prompt, temperature, max_tokens)

            llm_logger.log_response(
                agent="writer",
                stage="gigachat_call",
                response=response,
                success=True
            )

            return response
        except Exception as e:
            llm_logger.log_error(
                agent="writer",
                stage="gigachat_call",
                error=str(e)
            )
            raise

    UnifiedLLMClient._generate_gigachat = logged_generate_gigachat
    log("✅ UnifiedLLMClient patched для логирования", "🔧")

async def main():
    """Главная функция"""
    log("="*80, "")
    log("E2E TEST - С ДЕТАЛЬНЫМ LLM ЛОГИРОВАНИЕМ", "🚀")
    log("="*80, "")

    # Инициализация LLM Logger
    llm_logger = get_llm_logger()

    # Патчим UnifiedLLMClient
    patch_unified_llm_client()

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
    log("ЗАПУСКАЕМ ТОЛЬКО WRITER (для проверки LLM)", "✍️")
    log("", "")

    # WRITER V2
    try:
        log("STAGE: Writer V2 (GigaChat-2-Max)", "✍️")
        log("-" * 80, "")

        from writer_agent_v2 import WriterAgentV2
        writer = WriterAgentV2(
            db=db,
            llm_provider='gigachat'
        )

        input_data = {
            "anketa_id": ANKETA_ID,
            "user_answers": anketa.get("interview_data", {}),
            "selected_grant": {}
        }

        log(f"🚀 Генерация заявки через GigaChat-2-Max...", "")
        log(f"   User answers length: {len(str(input_data['user_answers']))} chars", "")
        log("", "")

        result = await writer.write_application_async(input_data)

        if result:
            log(f"✅ Writer завершён", "")
            log(f"   Application length: {len(str(result.get('application', '')))} chars", "")
        else:
            log(f"❌ Writer вернул None", "")

    except Exception as e:
        log(f"❌ ОШИБКА Writer: {e}", "")
        import traceback
        traceback.print_exc()

    # SUMMARY
    log("", "")
    log("="*80, "")
    log("LLM LOGGING SUMMARY", "📊")
    log("="*80, "")

    summary = llm_logger.get_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    log("", "")
    log(f"📄 Лог файл: {llm_logger.log_file}", "")
    log("="*80, "")

if __name__ == "__main__":
    asyncio.run(main())
