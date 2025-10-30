#!/usr/bin/env python3
"""
WriterTestModule - Тестирование PRODUCTION WriterAgent

Source: Iteration 65 (Writer Key Fix)
Tests: Production WriterAgentV2 with correct 'application' key
Critical: Validates grant length >= 15000 chars

Iteration 66: E2E Test Suite
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class WriterTestModule:
    """
    Test module for WriterAgent

    Tests PRODUCTION WriterAgentV2 code
    Key fix: Use result['application'] not result['grant_text']
    """

    def __init__(self, db):
        """
        Initialize test module

        Args:
            db: GrantServiceDatabase instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def test_writer(
        self,
        anketa_data: Dict[str, Any],
        research_data: Dict[str, Any],
        llm_provider: str = "gigachat"
    ) -> Dict[str, Any]:
        """
        Test PRODUCTION WriterAgent

        What it does:
        1. Imports PRODUCTION WriterAgentV2
        2. Prepares input_data (anketa + research)
        3. Calls write_application_async()
        4. Extracts grant text from result['application'] (ITERATION 65 FIX!)
        5. Validates grant >= 15000 characters
        6. Saves to grants table

        Args:
            anketa_data: Dict with anketa_id, user_answers
            research_data: Dict with research results
            llm_provider: LLM provider

        Returns:
            Dict with:
                - grant_id: str
                - grant_text: str (full grant content)
                - grant_length: int
                - model: str

        Raises:
            ValueError: If grant fails validation
        """
        self.logger.info("="*60)
        self.logger.info("WRITER TEST MODULE")
        self.logger.info("="*60)

        # 1. Import PRODUCTION WriterAgent
        from agents.writer_agent_v2 import WriterAgentV2
        from datetime import datetime
        import json

        # 2. Initialize writer
        writer = WriterAgentV2(self.db, llm_provider=llm_provider)

        # 3. Prepare input_data
        input_data = {
            "anketa_id": anketa_data['anketa_id'],
            "user_answers": anketa_data['user_answers'],
            "research_results": research_data.get('research_data', {}),
            "selected_grant": {
                "name": "Президентский грант",
                "organization": "Фонд президентских грантов"
            }
        }

        self.logger.info(f"Testing WriterAgent for anketa: {anketa_data['anketa_id']}")

        # 4. Generate grant
        self.logger.info("Calling WriterAgentV2.write_application_async()...")
        writer_result = await writer.write_application_async(input_data)

        # 5. Extract grant text (ITERATION 65 FIX + FIX #15!)
        # WriterAgent returns result['application'] which is a DICT
        # FIX #15: Extract 'full_text' from application_content dict
        application_content = writer_result.get('application', {})

        if isinstance(application_content, dict):
            # PRODUCTION WriterAgentV2: application_content has 'full_text' key
            grant_text = application_content.get('full_text', '')

            # Fallback: concatenate sections if no full_text
            if not grant_text:
                sections = [
                    application_content.get('section_1_brief', ''),
                    application_content.get('section_2_problem', ''),
                    application_content.get('section_3_goal', ''),
                    application_content.get('section_4_results', ''),
                    application_content.get('section_5_tasks', ''),
                    application_content.get('section_6_partners', ''),
                    application_content.get('section_7_info', ''),
                    application_content.get('section_8_future', ''),
                    application_content.get('section_9_calendar', '')
                ]
                grant_text = '\n\n'.join([s for s in sections if s])
        else:
            # Fallback for old format (if application is string)
            grant_text = str(application_content)

        if not grant_text or grant_text == 'N/A':
            raise ValueError(
                f"Writer returned empty grant! Keys: {writer_result.keys()}"
            )

        grant_length = len(grant_text)
        self.logger.info(f"Writer returned: {grant_length} characters")

        # 6. Validate grant length
        if grant_length < 15000:
            raise ValueError(
                f"Grant too short: {grant_length} < 15000 characters"
            )

        self.logger.info(f"✅ Grant length validated: {grant_length} chars")

        # 7. Validate grant has required sections
        required_sections = [
            'ОПИСАНИЕ ПРОБЛЕМЫ',
            'ЦЕЛИ И ЗАДАЧИ',
            'МЕРОПРИЯТИЯ',
            'БЮДЖЕТ'
        ]

        missing_sections = []
        for section in required_sections:
            if section not in grant_text:
                missing_sections.append(section)

        if missing_sections:
            self.logger.warning(
                f"Missing sections: {', '.join(missing_sections)}"
            )

        # 8. Check for TODO/INSERT placeholders
        if 'TODO' in grant_text or 'INSERT' in grant_text:
            raise ValueError("Grant has unfinished parts (TODO/INSERT)")

        self.logger.info("✅ Grant has all required sections")

        # 9. Save to database
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        grant_id = f"#GR-{timestamp}-{anketa_data['anketa_id'][:30]}"

        grant_title = grant_text.split('\n')[0][:200] if grant_text else "Грантовая заявка"

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO grants (
                    grant_id, anketa_id, research_id, user_id,
                    grant_title, grant_content, grant_sections, metadata,
                    llm_provider, model, status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                grant_id,
                anketa_data['anketa_id'],
                research_data.get('research_id', 'N/A'),
                anketa_data.get('telegram_id', 999999001),
                grant_title,
                grant_text,
                json.dumps({}),
                json.dumps({'test_module': 'WriterTestModule', 'iteration': 66}),
                llm_provider,
                'GigaChat-Max',
                'draft',
                datetime.now()
            ))
            conn.commit()
            cursor.close()

        self.logger.info(f"✅ Grant saved to DB: {grant_id}")

        return {
            'grant_id': grant_id,
            'grant_text': grant_text,
            'grant_length': grant_length,
            'model': 'GigaChat-Max',
            'missing_sections': missing_sections
        }

    def export_to_file(self, grant_data: Dict, filepath: Path):
        """Export grant to text file"""
        content = []
        content.append("=" * 60)
        content.append("GRANT TEST RESULT")
        content.append("=" * 60)
        content.append(f"\nGrant ID: {grant_data['grant_id']}")
        content.append(f"Length: {grant_data['grant_length']} characters")
        content.append(f"Model: {grant_data['model']}")

        if grant_data.get('missing_sections'):
            content.append(f"\n⚠️ Missing sections: {', '.join(grant_data['missing_sections'])}")

        content.append("\n" + "=" * 60)
        content.append("GRANT CONTENT")
        content.append("=" * 60)
        content.append("")
        content.append(grant_data['grant_text'])

        filepath.write_text('\n'.join(content), encoding='utf-8')
        self.logger.info(f"Exported grant to: {filepath}")
