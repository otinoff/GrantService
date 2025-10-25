#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 29 - FULL E2E TEST with Perplexity Researcher
Цель: Researcher (Perplexity) → Writer (GigaChat) → Auditor (GigaChat)
НЕ ОСТАНАВЛИВАЕМСЯ пока не получим ВСЕ 3 документа!
"""
import sys
import os
import asyncio
import json
import time
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
ANKETA_ID = f"#AN-ITER29-{datetime.now().strftime('%Y%m%d%H%M%S')}"  # Unique ID
ANKETA_FILE = Path(__file__).parent.parent / "test_data" / "natalia_anketa_20251012.json"
RESULTS_DIR = Path(__file__).parent.parent / "test_results" / "iteration_29_e2e_results"
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
    FULL E2E TEST: Researcher (Perplexity) → Writer (GigaChat) → Auditor (GigaChat)
    """
    log("=" * 80, "")
    log("🚀 ITERATION 29 - FULL E2E TEST (Perplexity + GigaChat)", "")
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

    # Setup database
    log("Настройка подключения к ЛОКАЛЬНОЙ БД...", "🔌")
    os.environ['PGHOST'] = 'localhost'
    os.environ['PGPORT'] = '5432'
    os.environ['PGDATABASE'] = 'grantservice'
    os.environ['PGUSER'] = 'postgres'
    os.environ['PGPASSWORD'] = 'root'
    log("  ✅ БД: localhost:5432/grantservice", "")
    log("", "")

    # ====================================================================================
    # STAGE 1: RESEARCHER AGENT (Perplexity) - 6-7 minutes
    # ====================================================================================
    log("=" * 80, "")
    log("🔍 STAGE 1: RESEARCHER AGENT (Perplexity)", "")
    log("=" * 80, "")
    log("Expected: 6-7 minutes, 27 queries, ~20,000 tokens", "")
    log("", "")

    researcher_start = datetime.now()

    try:
        from agents.researcher_agent_v2 import ResearcherAgentV2
        from data.database import get_db

        log("Initializing Researcher Agent V2 with Perplexity...", "🔍")
        db = get_db()

        # Save anketa to DB first
        log("Saving anketa to DB...", "💾")
        session_data = {
            "anketa_id": ANKETA_ID,
            "user_id": "test_user",
            "project_name": anketa['project_info']['name'],
            "answers_data": json.dumps(anketa.get("interview_data", {})),
            "status": "completed"
        }
        db.create_session(session_data)
        log("✅ Anketa saved to DB", "")

        # IMPORTANT: Force Perplexity!
        researcher = ResearcherAgentV2(
            db=db,
            llm_provider='claude_code',
            websearch_provider='perplexity',
            websearch_fallback='claude_code'
        )
        log("✅ Researcher initialized (Perplexity provider)", "")
        log("", "")

        log("Starting research (27 queries про стрельбу из лука)...", "🔍")
        log("⏳ This will take 6-7 minutes...", "")
        log("", "")

        # Run researcher
        research_result = await researcher.research_with_expert_prompts(ANKETA_ID)

        if research_result.get('status') != 'success':
            log(f"❌ Researcher failed: {research_result.get('error', 'Unknown error')}", "❌")
            return

        research_id = research_result.get('research_id', 'UNKNOWN')
        research_data = research_result.get('research_results', {})

        researcher_duration = (datetime.now() - researcher_start).total_seconds()

        log("", "")
        log("✅ RESEARCHER COMPLETED!", "🎉")
        log(f"   Research ID: {research_id}", "")
        log(f"   Duration: {researcher_duration:.1f}s ({researcher_duration/60:.1f} min)", "")
        log(f"   Queries: {research_data.get('metadata', {}).get('total_queries', 0)}", "")
        log(f"   Sources: {research_data.get('metadata', {}).get('sources_count', 0)}", "")
        log("", "")

        # Export research results
        research_export_path = RESULTS_DIR / f"research_results_{research_id.replace('#', '').replace('/', '_')}.json"
        with open(research_export_path, 'w', encoding='utf-8') as f:
            json.dump(research_data, f, indent=2, ensure_ascii=False)

        log(f"💾 Exported: {research_export_path.name}", "")
        log("", "")

    except Exception as e:
        log(f"❌ Researcher failed: {e}", "❌")
        import traceback
        traceback.print_exc()
        return

    # ====================================================================================
    # STAGE 2: WRITER V2 AGENT (GigaChat) - 1-2 minutes
    # ====================================================================================
    log("=" * 80, "")
    log("✍️ STAGE 2: WRITER AGENT (GigaChat-2-Max)", "")
    log("=" * 80, "")
    log("Expected: 1-2 minutes, ~8,000 tokens", "")
    log("", "")

    writer_start = datetime.now()

    try:
        from agents.writer_agent_v2 import WriterAgentV2

        log("Initializing Writer Agent V2...", "✍️")

        writer = WriterAgentV2(
            db=db,
            llm_provider='gigachat'
        )

        log("✅ Writer initialized", "")
        log("Starting grant generation...", "✍️")
        log("", "")

        # Prepare input
        writer_input = {
            "anketa_id": ANKETA_ID,
            "user_answers": anketa.get("interview_data", {}),
            "research_results": research_data,
            "selected_grant": {}
        }

        # Run writer
        write_result = await writer.write_application_async(writer_input)

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

    # ====================================================================================
    # DELAY TO AVOID GIGACHAT RATE LIMIT
    # ====================================================================================
    log("=" * 80, "")
    log("⏳ DELAY: Waiting 10 seconds to avoid GigaChat rate limit...", "")
    log("=" * 80, "")
    await asyncio.sleep(10)
    log("✅ Delay complete", "")
    log("", "")

    # ====================================================================================
    # STAGE 3: AUDITOR AGENT (GigaChat) - 30 seconds
    # ====================================================================================
    log("=" * 80, "")
    log("📊 STAGE 3: AUDITOR AGENT (GigaChat-2-Max)", "")
    log("=" * 80, "")
    log("Target: score ≥ 80%, can_submit = true", "")
    log("", "")

    auditor_start = datetime.now()

    try:
        from agents.auditor_agent import AuditorAgent

        log("Initializing Auditor Agent...", "📊")
        auditor = AuditorAgent(db=db, llm_provider='gigachat')
        log("✅ Auditor initialized", "")
        log("Starting audit...", "📊")
        log("", "")

        # Prepare input
        auditor_input = {
            "anketa_id": ANKETA_ID,
            "application": grant_content,
            "user_answers": anketa.get("interview_data", {}),
            "research_data": research_data,
            "selected_grant": {}
        }

        # Run audit
        audit_result = await auditor.audit_application_async(auditor_input)

        auditor_duration = (datetime.now() - auditor_start).total_seconds()

        overall_score = audit_result.get('overall_score', 0)
        can_submit = audit_result.get('can_submit', False)

        log("", "")
        log("✅ AUDITOR COMPLETED!", "🎉")
        log(f"   Duration: {auditor_duration:.1f}s", "")
        log(f"   Overall Score: {overall_score * 100:.2f}%", "")
        log(f"   Can Submit: {can_submit}", "")
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
        # Continue anyway to show summary

    # ====================================================================================
    # FINAL SUMMARY
    # ====================================================================================
    total_duration = (datetime.now() - start_time).total_seconds()

    log("=" * 80, "")
    log("🎉 FULL E2E TEST COMPLETED!", "")
    log("=" * 80, "")
    log("", "")
    log("📊 Summary:", "")
    log(f"   Total: {total_duration:.1f}s ({total_duration/60:.1f} min)", "")
    log(f"   Researcher: {researcher_duration:.1f}s ({researcher_duration/60:.1f} min)", "")
    log(f"   Writer: {writer_duration:.1f}s", "")
    log(f"   Auditor: {auditor_duration:.1f}s", "")
    log("", "")
    log("📁 Exported:", "")
    log(f"   1. {research_export_path.name}", "")
    log(f"   2. {grant_export_path.name}", "")
    log(f"   3. {audit_export_path.name}", "")
    log("", "")
    log("📈 Results:", "")
    log(f"   Research queries: {research_data.get('metadata', {}).get('total_queries', 0)}", "")
    log(f"   Grant length: {len(grant_content)} chars", "")
    log(f"   Auditor score: {overall_score * 100:.2f}%", "")
    log(f"   Can submit: {'✅ YES' if can_submit else '❌ NO'}", "")
    log("", "")
    log("=" * 80, "")
    log("✅ Test complete! Check test_results/iteration_29_e2e_results/", "")
    log("", "")


if __name__ == "__main__":
    asyncio.run(main())
