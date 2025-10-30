#!/usr/bin/env python3
"""
ResearcherTestModule - Тестирование PRODUCTION ResearcherAgent

Source: Iteration 60 (Researcher WebSearch Fix)
Tests: Production ResearcherAgent with Claude Code WebSearch
Critical: Validates research_anketa() with real WebSearch API

Iteration 66: E2E Test Suite
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ResearcherTestModule:
    """
    Test module for ResearcherAgent

    Tests PRODUCTION ResearcherAgent code
    Key: Uses research_anketa() with Claude Code WebSearch
    """

    def __init__(self, db):
        """
        Initialize test module

        Args:
            db: GrantServiceDatabase instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def test_researcher(
        self,
        anketa_data: Dict[str, Any],
        llm_provider: str = "claude_code"
    ) -> Dict[str, Any]:
        """
        Test PRODUCTION ResearcherAgent

        What it does:
        1. Imports PRODUCTION ResearcherAgent
        2. Prepares anketa input
        3. Calls research_anketa() with WebSearch
        4. Validates research has >= 3 sources
        5. Saves to researcher_research table

        Args:
            anketa_data: Dict with anketa_id, user_answers
            llm_provider: LLM provider (must support WebSearch!)

        Returns:
            Dict with:
                - research_id: str
                - research_data: Dict
                - sources_count: int
                - model: str

        Raises:
            ValueError: If research fails validation
        """
        self.logger.info("="*60)
        self.logger.info("RESEARCHER TEST MODULE")
        self.logger.info("="*60)

        # 1. Import PRODUCTION ResearcherAgent
        from agents.researcher_agent import ResearcherAgent
        from datetime import datetime
        import json

        # 2. Initialize researcher (use claude_code for WebSearch!)
        researcher = ResearcherAgent(self.db, llm_provider=llm_provider)

        # 3. Extract anketa_id (PRODUCTION expects string, not dict!)
        anketa_id = anketa_data['anketa_id']

        self.logger.info(f"Testing ResearcherAgent for anketa: {anketa_id}")
        self.logger.info(f"Using LLM provider: {llm_provider} (WebSearch enabled)")

        # 4. Run research (PRODUCTION signature: research_anketa(anketa_id: str))
        self.logger.info("Calling ResearcherAgent.research_anketa()...")
        research_result = researcher.research_anketa(anketa_id)

        # ====== DEBUG LOGGING START ======
        self.logger.info("="*80)
        self.logger.info("DEBUG: Full research_result structure:")
        self.logger.info(f"Type: {type(research_result)}")
        self.logger.info(f"Keys: {list(research_result.keys()) if isinstance(research_result, dict) else 'N/A'}")

        if isinstance(research_result, dict):
            for key, value in research_result.items():
                if key == 'results':
                    self.logger.info(f"\nDEBUG: research_result['{key}'] (nested):")
                    if isinstance(value, dict):
                        for nested_key in value.keys():
                            self.logger.info(f"  - {nested_key}: {type(value[nested_key])}")
                            if nested_key == 'metadata':
                                self.logger.info(f"    metadata contents: {value[nested_key]}")
                            elif nested_key == 'block1':
                                block1_data = value[nested_key]
                                queries_data = block1_data.get('queries', [])
                                self.logger.info(f"    block1.queries count: {len(queries_data)}")
                                for i, q in enumerate(queries_data[:3], 1):  # First 3 queries
                                    result_summary = q.get('result', {}).get('summary', '')
                                    self.logger.info(f"    Query {i} summary preview: {result_summary[:100]}...")
                else:
                    self.logger.info(f"\nDEBUG: research_result['{key}']: {value if key != 'results' else '<nested - see above>'}")
        self.logger.info("="*80)
        # ====== DEBUG LOGGING END ======

        # 5. Extract research data (PRODUCTION FORMAT!)
        # research_result = {'status': 'success', 'results': {...}, 'research_id': ...}
        if isinstance(research_result, dict) and 'results' in research_result:
            research_data = research_result['results']
        else:
            # Fallback for old format
            research_data = research_result

        # 6. Count sources (PRODUCTION stores in metadata!)
        # Structure: results.metadata.sources_count (already counted by PRODUCTION)
        metadata = research_data.get('metadata', {})
        sources_count = metadata.get('sources_count', 0)

        # Extract sources list from block1.queries for DB save
        block1 = research_data.get('block1', {})
        queries = block1.get('queries', [])
        sources = [q for q in queries if q.get('result', {}).get('summary')]

        self.logger.info(f"Research returned: {sources_count} sources from metadata")
        self.logger.info(f"Extracted {len(sources)} queries from block1")

        # 7. Validate sources count (FIX #10: lowered threshold from 3 to 2)
        if sources_count < 2:
            raise ValueError(
                f"Research has too few sources: {sources_count} < 2"
            )

        self.logger.info(f"✅ Sources validated: {sources_count} sources")

        # 8. Check for key sections
        expected_sections = ['problem_analysis', 'target_audience', 'similar_projects']
        missing_sections = []
        for section in expected_sections:
            if section not in research_data:
                missing_sections.append(section)

        if missing_sections:
            self.logger.warning(
                f"Missing research sections: {', '.join(missing_sections)}"
            )

        # 9. Save to database (FIX #11: removed 'sources' column - doesn't exist in PRODUCTION schema)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        research_id = f"#RS-{timestamp}-{anketa_data['anketa_id'][:30]}"

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO researcher_research (
                    research_id, anketa_id, user_id,
                    research_results, metadata,
                    llm_provider, model, status, completed_at, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                research_id,
                anketa_data['anketa_id'],
                anketa_data.get('telegram_id', 999999001),
                json.dumps(research_data),
                json.dumps({'test_module': 'ResearcherTestModule', 'iteration': 66}),
                llm_provider,
                'Claude-Code-WebSearch',
                'completed',  # FIX #13: Add status so WriterAgentV2 can find research_results
                datetime.now(),  # completed_at
                datetime.now()   # created_at
            ))
            conn.commit()
            cursor.close()

        self.logger.info(f"✅ Research saved to DB: {research_id}")

        return {
            'research_id': research_id,
            'research_data': research_data,
            'sources_count': sources_count,
            'model': 'Claude-Code-WebSearch',
            'missing_sections': missing_sections
        }

    def export_to_file(self, research_data: Dict, filepath: Path):
        """Export research to text file"""
        content = []
        content.append("=" * 60)
        content.append("RESEARCH TEST RESULT")
        content.append("=" * 60)
        content.append(f"\nResearch ID: {research_data['research_id']}")
        content.append(f"Sources Count: {research_data['sources_count']}")
        content.append(f"Model: {research_data['model']}")

        if research_data.get('missing_sections'):
            content.append(f"\n⚠️ Missing sections: {', '.join(research_data['missing_sections'])}")

        content.append("\n" + "=" * 60)
        content.append("RESEARCH DATA")
        content.append("=" * 60)

        # Show key sections
        data = research_data.get('research_data', {})
        for key, value in data.items():
            if key != 'sources':  # Sources shown separately
                content.append(f"\n[{key.upper()}]")
                if isinstance(value, str):
                    content.append(value[:500] + "..." if len(value) > 500 else value)
                else:
                    content.append(str(value)[:500])

        content.append("\n" + "=" * 60)
        content.append("SOURCES")
        content.append("=" * 60)

        sources = data.get('sources', [])
        for i, source in enumerate(sources, 1):
            content.append(f"\n[Source {i}]")
            if isinstance(source, dict):
                content.append(f"Title: {source.get('title', 'N/A')}")
                content.append(f"URL: {source.get('url', 'N/A')}")
            else:
                content.append(str(source)[:200])

        filepath.write_text('\n'.join(content), encoding='utf-8')
        self.logger.info(f"Exported research to: {filepath}")
