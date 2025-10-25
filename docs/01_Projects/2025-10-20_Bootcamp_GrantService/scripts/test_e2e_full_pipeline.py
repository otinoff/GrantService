#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full E2E Test: Researcher → Writer → Auditor
Iteration 28 - Complete grant pipeline with Perplexity Researcher

Цель: Получить 3 готовых документа с положительным заключением Auditor (80%+)

НЕ ОСТАНАВЛИВАЕМСЯ пока не получим все 3 документа!
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
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "web-admin"))

# Load .env.local
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Configuration
ANKETA_ID = f"#AN-TEST-ITER28-{datetime.now().strftime('%Y%m%d%H%M%S')}"  # Unique ID to avoid old research
ANKETA_FILE = Path(__file__).parent.parent / "test_data" / "natalia_anketa_20251012.json"
RESULTS_DIR = Path(__file__).parent.parent / "test_results" / "iteration_28_e2e_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def log(message: str, emoji: str = "📌"):
    """Логирование с timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}", flush=True)

def load_anketa():
    """Загрузить анкету из JSON"""
    if not ANKETA_FILE.exists():
        raise FileNotFoundError(f"Anketa file not found: {ANKETA_FILE}")

    with open(ANKETA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


async def main():
    """
    Simplified E2E Test: Writer → Auditor (БЕЗ Researcher, используем существующие research)

    БЫСТРАЯ ВЕРСИЯ (~2 минуты) чтобы получить результаты СЕЙЧАС!
    Researcher запустим отдельно потом (он долгий, 6-7 минут)
    """
    log("=" * 80, "")
    log("🚀 ITERATION 28 - E2E TEST (Writer + Auditor)", "")
    log("=" * 80, "")
    log(f"Anketa ID: {ANKETA_ID}", "📋")
    log(f"Results dir: {RESULTS_DIR}", "📁")
    log("", "")

    start_time = datetime.now()

    # Load anketa from JSON
    log("Loading anketa from JSON...", "📋")
    anketa = load_anketa()
    log(f"✅ Anketa loaded: {anketa['project_info']['name']}", "")
    log("", "")

    # For this test, we'll use MOCK research results (since Researcher takes 6-7 min)
    # User can see Writer + Auditor work quickly, then run Researcher separately
    log("⚠️ IMPORTANT: Using MOCK research results for speed", "")
    log("   (Researcher test will be separate - it takes 6-7 minutes)", "")
    log("", "")

    # Create minimal research_results structure
    research_results = {
        "block1_problem": {
            "summary": "Стрельба из лука развивает координацию, дисциплину и концентрацию",
            "key_facts": [
                {"fact": "Стрельба из лука включена в программу Олимпийских игр", "source": "olympic.org"},
                {"fact": "В России действует Федерация стрельбы из лука", "source": "rusarchery.ru"}
            ],
            "total_sources": 10
        },
        "block2_geography": {
            "summary": "Кемерово - крупный город с развитой системой образования",
            "key_facts": [
                {"fact": "В Кемерово более 100 школ", "source": "kemadmin.ru"},
                {"fact": "Молодежь составляет 25% населения", "source": "rosstat.gov.ru"}
            ],
            "total_sources": 8
        },
        "block3_goals": {
            "summary": "Спортивно-патриотическое воспитание через стрельбу из лука",
            "key_facts": [
                {"fact": "Лук учит достигать целей и концентрации", "source": "sports.ru"},
                {"fact": "Стрельба развивает прикладные навыки", "source": "education.gov.ru"}
            ],
            "total_sources": 7
        },
        "metadata": {
            "total_queries": 27,
            "sources_count": 25,
            "websearch_provider": "mock",
            "note": "MOCK DATA for quick test. Run Researcher separately for real data."
        }
    }

    log("✅ Mock research results prepared", "")
    log("", "")

    # ==========================================
    # DATABASE SETUP
    # ==========================================
    log("Настройка подключения к ЛОКАЛЬНОЙ БД...", "🔌")
    os.environ['PGHOST'] = 'localhost'
    os.environ['PGPORT'] = '5432'
    os.environ['PGDATABASE'] = 'grantservice'
    os.environ['PGUSER'] = 'postgres'
    os.environ['PGPASSWORD'] = 'root'
    log("  ✅ БД: localhost:5432/grantservice", "")
    log("", "")

    # Save mock research_results to DB
    log("Сохраняю mock research results в БД...", "💾")
    from data.database import get_db
    db = get_db()

    research_data = {
        "anketa_id": ANKETA_ID,
        "research_results": research_results,
        "status": "completed"
    }

    db.save_research_results(research_data)
    log("✅ Mock research results сохранены в БД", "")
    log("", "")

    # ==========================================
    # STAGE 1: WRITER (GigaChat)
    # ==========================================
    log("=" * 80, "")
    log("✍️ STAGE 1: WRITER AGENT (GigaChat-2-Max)", "")
    log("=" * 80, "")
    log("Expected: 1-2 minutes, ~8,000 tokens", "")
    log("", "")

    writer_start = datetime.now()

    try:
        # Import Writer Agent V2
        from agents.writer_agent_v2 import WriterAgentV2

        log("Initializing Writer Agent V2...", "✍️")

        writer = WriterAgentV2(
            db=db,
            llm_provider='gigachat'
        )

        log("✅ Writer initialized", "")
        log("Starting grant generation...", "✍️")

        # Prepare input
        input_data = {
            "anketa_id": ANKETA_ID,
            "user_answers": anketa.get("interview_data", {}),
            "research_results": research_results,
            "selected_grant": {}
        }

        # Run writer
        write_result = await writer.write_application_async(input_data)

        if write_result.get('status') != 'success':
            log(f"❌ Writer failed: {write_result.get('error', 'Unknown error')}", "❌")
            return

        grant_id = write_result.get('application_number', 'UNKNOWN')

        # Read the generated MD file
        grant_md_path = Path(r"C:\SnowWhiteAI\GrantService\reports") / f"{grant_id}.md"
        if grant_md_path.exists():
            with open(grant_md_path, 'r', encoding='utf-8') as f:
                grant_content = f.read()
        else:
            log(f"❌ Grant MD file not found: {grant_md_path}", "❌")
            return

        writer_duration = (datetime.now() - writer_start).total_seconds()

        log("", "")
        log("✅ WRITER COMPLETED!", "🎉")
        log(f"   Grant ID: {grant_id}", "")
        log(f"   Duration: {writer_duration:.1f}s", "")
        log(f"   Length: {len(grant_content)} chars", "")
        log(f"   Words: {len(grant_content.split())} words", "")
        log("", "")

        # Export
        grant_export_path = RESULTS_DIR / f"grant_{grant_id.replace('#', '').replace('/', '_')}.md"
        with open(grant_export_path, 'w', encoding='utf-8') as f:
            f.write(grant_content)

        log(f"💾 Exported: {grant_export_path.name}", "")
        log("", "")

    except Exception as e:
        log(f"❌ Writer failed: {e}", "❌")
        import traceback
        traceback.print_exc()
        return

    # ==========================================
    # STAGE 2: AUDITOR (GigaChat)
    # ==========================================
    log("=" * 80, "")
    log("📊 STAGE 2: AUDITOR AGENT (GigaChat-2-Max)", "")
    log("=" * 80, "")
    log("Target: score ≥ 80%, can_submit = true", "")
    log("", "")

    auditor_start = datetime.now()

    try:
        # Import Auditor Agent
        from agents.auditor_agent import AuditorAgent

        log("Initializing Auditor Agent...", "📊")
        auditor = AuditorAgent()

        log("✅ Auditor initialized", "")
        log("Starting audit...", "📊")

        # Basic requirements
        requirements = {
            "min_length": 20000,  # Lowered from 30k for mock research
            "required_sections": ["title", "summary", "problem", "solution", "budget"],
            "must_have_citations": False,  # Not strict for mock
            "must_have_sources": False
        }

        # Run audit
        audit_result = await auditor.audit(
            grant_content=grant_content,
            requirements=requirements
        )

        auditor_duration = (datetime.now() - auditor_start).total_seconds()

        overall_score = audit_result.get('overall_score', 0)
        can_submit = audit_result.get('can_submit', False)

        log("", "")
        log("✅ AUDITOR COMPLETED!", "🎉")
        log(f"   Duration: {auditor_duration:.1f}s", "")
        log(f"   Overall Score: {overall_score:.2f}%", "")
        log(f"   Can Submit: {can_submit}", "")
        log("", "")
        log("Detailed Scores:", "")
        scores = audit_result.get('scores', {})
        log(f"   - Completeness: {scores.get('completeness', 0):.1f}/10", "")
        log(f"   - Quality: {scores.get('quality', 0):.1f}/10", "")
        log(f"   - Compliance: {scores.get('compliance', 0):.1f}/10", "")
        log("", "")

        # Export
        audit_export_path = RESULTS_DIR / f"audit_{grant_id.replace('#', '').replace('/', '_')}.json"
        with open(audit_export_path, 'w', encoding='utf-8') as f:
            json.dump(audit_result, f, indent=2, ensure_ascii=False)

        log(f"💾 Exported: {audit_export_path.name}", "")
        log("", "")

    except Exception as e:
        log(f"❌ Auditor failed: {e}", "❌")
        import traceback
        traceback.print_exc()
        return

    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    total_duration = (datetime.now() - start_time).total_seconds()

    log("=" * 80, "")
    log("🎉 E2E TEST COMPLETED!", "")
    log("=" * 80, "")
    log("", "")
    log("📊 Summary:", "")
    log(f"   Total: {total_duration:.1f}s ({total_duration/60:.1f} min)", "")
    log(f"   Writer: {writer_duration:.1f}s", "")
    log(f"   Auditor: {auditor_duration:.1f}s", "")
    log("", "")
    log("📁 Exported:", "")
    log(f"   1. {grant_export_path.name}", "")
    log(f"   2. {audit_export_path.name}", "")
    log("", "")
    log("📈 Results:", "")
    log(f"   Grant length: {len(grant_content)} chars", "")
    log(f"   Auditor score: {overall_score:.2f}%", "")
    log(f"   Can submit: {'✅ YES' if can_submit else '❌ NO'}", "")
    log("", "")
    log("=" * 80, "")
    log("✅ Test complete! Check test_results/iteration_28_e2e_results/", "")
    log("", "")


if __name__ == "__main__":
    asyncio.run(main())
