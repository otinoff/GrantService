#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест AUDITOR для существующей заявки
"""
import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add paths
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))

# Configuration
GRANT_ID = "GA-20251023-52B86815"
GRANT_MD_PATH = Path(r"C:\SnowWhiteAI\GrantService\reports") / f"{GRANT_ID}.md"
RESULTS_DIR = Path(__file__).parent.parent / "test_results" / "iteration_28_e2e_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def log(message: str, emoji: str = "📌"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}", flush=True)

async def main():
    log("=" * 80, "")
    log("📊 QUICK TEST: AUDITOR ONLY", "")
    log("=" * 80, "")
    log(f"Grant ID: {GRANT_ID}", "")
    log(f"Grant MD: {GRANT_MD_PATH.name}", "")
    log("", "")

    start_time = datetime.now()

    # Read grant content
    log("Читаю заявку из MD файла...", "📄")
    if not GRANT_MD_PATH.exists():
        log(f"❌ Файл не найден: {GRANT_MD_PATH}", "")
        return

    with open(GRANT_MD_PATH, 'r', encoding='utf-8') as f:
        grant_content = f.read()

    log(f"✅ Заявка загружена: {len(grant_content)} символов", "")
    log("", "")

    # Run Auditor
    log("=" * 80, "")
    log("📊 ЗАПУСКАЕМ AUDITOR AGENT", "")
    log("=" * 80, "")

    auditor_start = datetime.now()

    try:
        from agents.auditor_agent import AuditorAgent
        from data.database import get_db

        # Setup DB
        os.environ['PGHOST'] = 'localhost'
        os.environ['PGPORT'] = '5432'
        os.environ['PGDATABASE'] = 'grantservice'
        os.environ['PGUSER'] = 'postgres'
        os.environ['PGPASSWORD'] = 'root'

        db = get_db()

        log("Инициализация Auditor Agent...", "📊")
        auditor = AuditorAgent(db=db, llm_provider='gigachat')
        log("✅ Auditor инициализирован", "")
        log("Запуск аудита...", "📊")
        log("", "")

        # Prepare input_data for auditor
        input_data = {
            "anketa_id": GRANT_ID,
            "application": grant_content,
            "user_answers": {},
            "research_data": {},
            "selected_grant": {}
        }

        audit_result = await auditor.audit_application_async(input_data)

        auditor_duration = (datetime.now() - auditor_start).total_seconds()

        # Extract result from BaseAgent wrapper
        result = audit_result.get('result', audit_result)

        overall_score = result.get('overall_score', 0)
        can_submit = result.get('can_submit', False)
        completeness_score = result.get('completeness_score', 0)
        quality_score = result.get('quality_score', 0)
        compliance_score = result.get('compliance_score', 0)

        log("", "")
        log("✅ AUDITOR COMPLETED!", "🎉")
        log(f"   Duration: {auditor_duration:.1f}s", "")
        log(f"   Overall Score: {overall_score*100:.2f}%", "")
        log(f"   Can Submit: {can_submit}", "")
        log("", "")
        log("Detailed Scores:", "")
        log(f"   - Completeness: {completeness_score:.1f}/10", "")
        log(f"   - Quality: {quality_score:.1f}/10", "")
        log(f"   - Compliance: {compliance_score:.1f}/10", "")
        log("", "")

        # Export
        audit_export_path = RESULTS_DIR / f"audit_{GRANT_ID}.json"
        with open(audit_export_path, 'w', encoding='utf-8') as f:
            json.dump(audit_result, f, indent=2, ensure_ascii=False)

        log(f"💾 Exported: {audit_export_path.name}", "")

        # Copy grant to results
        grant_export_path = RESULTS_DIR / f"grant_{GRANT_ID}.md"
        with open(grant_export_path, 'w', encoding='utf-8') as f:
            f.write(grant_content)

        log(f"💾 Exported: {grant_export_path.name}", "")
        log("", "")

        # Summary
        total_duration = (datetime.now() - start_time).total_seconds()

        log("=" * 80, "")
        log("🎉 AUDITOR TEST COMPLETED!", "")
        log("=" * 80, "")
        log("", "")
        log(f"Total: {total_duration:.1f}s", "")
        log("", "")
        log("📁 Exported:", "")
        log(f"   1. {grant_export_path.name}", "")
        log(f"   2. {audit_export_path.name}", "")
        log("", "")
        log("📈 Results:", "")
        log(f"   Grant length: {len(grant_content)} chars", "")
        log(f"   Auditor score: {overall_score*100:.2f}%", "")
        log(f"   Can submit: {'✅ YES' if can_submit else '❌ NO'}", "")
        log("", "")
        log("=" * 80, "")

    except Exception as e:
        log(f"❌ Auditor failed: {e}", "❌")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
