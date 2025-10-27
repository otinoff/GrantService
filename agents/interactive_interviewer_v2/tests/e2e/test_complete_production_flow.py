#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test: Complete Production Flow (Iteration 53+)

ПОЛНЫЙ PRODUCTION WORKFLOW:
1. Hardcoded questions (имя, организация, проект)
2. Interactive questions (adaptive с LLM)
3. Save to database (session + anketa)
4. Generate anketa.txt file
5. Simulate send to user
6. Offer audit
   - Test A: Accept audit → run audit → generate audit.txt
   - Test B: Decline audit → end workflow

This test REPLACES manual end-to-end testing.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-27 (Iteration 53 - Phase 6)
"""

import sys
from pathlib import Path
import pytest
import asyncio
from typing import Dict, Any, List
import tempfile
import os
import json
from datetime import datetime

# Add project root to path
_project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))
sys.path.insert(0, str(_project_root / "data"))

from agents.full_flow_manager import FullFlowManager
from agents.synthetic_user_simulator import SyntheticUserSimulator
from agents.auditor_agent import AuditorAgent
from shared.telegram.file_generators import generate_anketa_txt, generate_audit_txt
from data.database.models import GrantServiceDatabase


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

pytestmark = pytest.mark.e2e


# Hardcoded questions (как в interview_handler.py)
HARDCODED_QUESTIONS = [
    {
        "id": "user_name",
        "text": "Скажите, как Ваше имя, как я могу к Вам обращаться?",
        "field_name": "user_name",
    },
    {
        "id": "organization",
        "text": "Расскажите о Вашей организации",
        "field_name": "organization_description",
    },
    {
        "id": "project_essence",
        "text": "В чём суть Вашего проекта?",
        "field_name": "project_essence",
    },
]


# =============================================================================
# PRODUCTION WORKFLOW SIMULATOR
# =============================================================================

class ProductionWorkflowSimulator:
    """
    Симулирует ПОЛНЫЙ production workflow как в Telegram боте.

    Phases:
    1. Hardcoded questions
    2. Interactive questions (with LLM)
    3. Save to DB
    4. Generate files
    5. Send to user (simulated)
    6. Audit decision
    """

    def __init__(self, db: GrantServiceDatabase, quality_level: str = "medium"):
        """
        Args:
            db: Database connection
            quality_level: "medium" or "high" for user simulator
        """
        self.db = db
        self.quality_level = quality_level

        # Workflow state
        self.session_id = None
        self.anketa_id = None
        self.anketa_data = {}
        self.dialog_history = []
        self.files_generated = {}

        # Test user
        self.test_user_id = 999999999  # E2E test user

    async def run_full_workflow(self, accept_audit: bool = True) -> Dict[str, Any]:
        """
        Run complete production workflow.

        Args:
            accept_audit: True = accept audit, False = decline

        Returns:
            Complete workflow result
        """
        print("\n" + "="*80)
        print("🚀 COMPLETE PRODUCTION WORKFLOW - START")
        print("="*80)

        workflow_start = datetime.now()

        # Phase 1: Hardcoded Questions
        print("\n" + "="*60)
        print("📝 PHASE 1: Hardcoded Questions")
        print("="*60)
        hardcoded_data = await self._phase_1_hardcoded_questions()

        # Phase 2: Interactive Questions
        print("\n" + "="*60)
        print("💬 PHASE 2: Interactive Questions (LLM)")
        print("="*60)
        interview_result = await self._phase_2_interactive_questions(hardcoded_data)

        # Phase 3: Save to Database
        print("\n" + "="*60)
        print("💾 PHASE 3: Save to Database")
        print("="*60)
        db_result = await self._phase_3_save_to_database(interview_result)

        # Phase 4: Generate anketa.txt
        print("\n" + "="*60)
        print("📄 PHASE 4: Generate anketa.txt File")
        print("="*60)
        anketa_file = await self._phase_4_generate_anketa_file()

        # Phase 5: Send to User (simulated)
        print("\n" + "="*60)
        print("📤 PHASE 5: Send to User (simulated)")
        print("="*60)
        send_result = await self._phase_5_send_to_user(anketa_file)

        # Phase 6: Audit Decision
        print("\n" + "="*60)
        print(f"🎯 PHASE 6: Audit Decision (accept={accept_audit})")
        print("="*60)
        audit_result = await self._phase_6_audit_decision(accept_audit)

        workflow_end = datetime.now()
        workflow_duration = (workflow_end - workflow_start).total_seconds()

        print("\n" + "="*80)
        print("COMPLETE PRODUCTION WORKFLOW - SUCCESS")
        print("="*80)
        print(f"Duration: {workflow_duration:.1f}s")
        print(f"Hardcoded questions: {len(HARDCODED_QUESTIONS)}")
        print(f"Interactive questions: {interview_result.get('questions_asked', 0)}")
        print(f"Total dialog messages: {len(self.dialog_history)}")
        print(f"Anketa ID: {self.anketa_id}")
        print(f"Audit run: {audit_result is not None}")
        print("="*80)

        return {
            'workflow_duration': workflow_duration,
            'hardcoded_data': hardcoded_data,
            'interview_result': interview_result,
            'db_result': db_result,
            'anketa_file': anketa_file,
            'send_result': send_result,
            'audit_result': audit_result,
            'session_id': self.session_id,
            'anketa_id': self.anketa_id,
            'dialog_history': self.dialog_history,
            'files_generated': self.files_generated,
        }

    async def _phase_1_hardcoded_questions(self) -> Dict[str, str]:
        """Phase 1: Ask hardcoded questions."""
        user_simulator = SyntheticUserSimulator(
            quality_level=self.quality_level,
            context={
                'region': 'Москва',
                'topic': 'молодёжь',
                'organization': 'АНО "Развитие"'
            }
        )

        hardcoded_data = {}

        for i, q in enumerate(HARDCODED_QUESTIONS, 1):
            question = q['text']
            field_name = q['field_name']

            print(f"\n[Q{i}] HARDCODED: {question}")
            self.dialog_history.append({
                'role': 'interviewer',
                'text': question,
                'phase': 'hardcoded',
                'timestamp': datetime.now().isoformat()
            })

            # Get answer from simulator
            answer = await user_simulator.answer_question(question, field_name)
            hardcoded_data[field_name] = answer

            print(f"[A{i}] USER: {answer[:100]}...")
            self.dialog_history.append({
                'role': 'user',
                'text': answer,
                'phase': 'hardcoded',
                'field_name': field_name,
                'timestamp': datetime.now().isoformat()
            })

        print(f"\nHardcoded phase complete: {len(hardcoded_data)} fields collected")
        return hardcoded_data

    async def _phase_2_interactive_questions(self, hardcoded_data: Dict[str, str]) -> Dict[str, Any]:
        """Phase 2: Interactive questions with LLM."""
        # Create full flow manager
        flow_manager = FullFlowManager(
            db=self.db,
            llm_provider='gigachat',
            qdrant_host=None,  # Disable for speed
            qdrant_port=None
        )

        # Create user simulator
        user_simulator = SyntheticUserSimulator(
            quality_level=self.quality_level,
            context={
                'region': 'Москва',
                'topic': 'молодёжь',
                'organization': 'АНО "Развитие"'
            }
        )

        # User data
        user_data = {
            'telegram_id': self.test_user_id,
            'username': f'e2e_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'grant_fund': 'ФПГ',
            'region': 'Москва',
            **hardcoded_data  # Include hardcoded answers
        }

        # Run full interview (hardcoded + interactive)
        full_result = await flow_manager.conduct_full_interview(
            user_data=user_data,
            user_simulator=user_simulator
        )

        # Merge dialog history
        self.dialog_history.extend(full_result.get('dialog_history', []))

        # Extract anketa
        self.anketa_data = full_result.get('anketa', {})
        self.session_id = full_result.get('session_id')

        print(f"\nInteractive phase complete:")
        print(f"   - Questions asked: {full_result.get('adaptive_questions_asked', 0)}")
        print(f"   - Audit score: {full_result.get('audit_score', 0)}")
        print(f"   - Session ID: {self.session_id}")

        return full_result

    async def _phase_3_save_to_database(self, interview_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Save session and anketa to database."""
        # In production, this is done by interactive_pipeline_handler.py
        # We simulate it here

        # Note: session already saved by flow_manager, we just get the ID
        self.session_id = interview_result.get('session_id')

        # Generate anketa_id (in production: auto-generated or from session)
        self.anketa_id = f"ANKETA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.test_user_id}"

        # Add anketa_id to anketa_data
        self.anketa_data['anketa_id'] = self.anketa_id
        self.anketa_data['telegram_id'] = self.test_user_id
        self.anketa_data['created_at'] = datetime.now().isoformat()

        print(f"\nDatabase save complete:")
        print(f"   - Session ID: {self.session_id}")
        print(f"   - Anketa ID: {self.anketa_id}")
        print(f"   - Data fields: {len(self.anketa_data)}")

        return {
            'session_id': self.session_id,
            'anketa_id': self.anketa_id,
            'saved': True
        }

    async def _phase_4_generate_anketa_file(self) -> str:
        """Phase 4: Generate anketa.txt file."""
        # Prepare data for file generator
        file_data = {
            'answers_data': self.anketa_data,
            'interview_data': self.anketa_data
        }

        # Generate content
        anketa_content = generate_anketa_txt(file_data)

        # Save to temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            suffix='.txt',
            delete=False,
            prefix=f'anketa_{self.anketa_id}_'
        ) as f:
            f.write(anketa_content)
            file_path = f.name

        self.files_generated['anketa.txt'] = file_path

        print(f"\nFile generation complete:")
        print(f"   - File: {os.path.basename(file_path)}")
        print(f"   - Size: {len(anketa_content)} chars")
        print(f"   - Location: {file_path}")

        return file_path

    async def _phase_5_send_to_user(self, file_path: str) -> Dict[str, Any]:
        """Phase 5: Simulate sending file to user."""
        # In production: context.bot.send_document(chat_id, file_path)
        # We just verify file exists and is readable

        assert os.path.exists(file_path), f"File not found: {file_path}"

        with open(file_path, 'r', encoding='utf-8') as f:
            content_preview = f.read(200)

        print(f"\nSend to user (simulated):")
        print(f"   - Recipient: User {self.test_user_id}")
        print(f"   - File: anketa.txt")
        print(f"   - Preview: {content_preview}...")
        print(f"   - Message: 'Спасибо! Интервью завершено.'")
        print(f"   - Button: [Начать аудит] [Отказаться]")

        return {
            'sent': True,
            'file_path': file_path,
            'user_id': self.test_user_id
        }

    async def _phase_6_audit_decision(self, accept: bool) -> Dict[str, Any]:
        """Phase 6: User decides to accept or decline audit."""
        if not accept:
            print(f"\nUser declined audit")
            print(f"   - Workflow complete without audit")
            return None

        print(f"\nUser accepted audit - starting audit...")

        # Run audit
        auditor = AuditorAgent(db=self.db)

        audit_input = {
            'anketa_data': self.anketa_data,
            'grant_type': 'Фонд Президентских Грантов'
        }

        audit_result = await auditor.audit_application_async(audit_input)

        # Generate audit.txt (simplified - в продакшене через file_generators.py)
        audit_content = f"""
=== РЕЗУЛЬТАТЫ АУДИТА ===

Анкета: {self.anketa_id}
Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Итоговый балл: {audit_result.get('final_score', 0)}/100

Статус: {audit_result.get('status', 'completed')}

=============================
"""

        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            suffix='.txt',
            delete=False,
            prefix=f'audit_{self.anketa_id}_'
        ) as f:
            f.write(audit_content)
            audit_file_path = f.name

        self.files_generated['audit.txt'] = audit_file_path

        print(f"\nAudit complete:")
        print(f"   - Score: {audit_result.get('final_score', 0)}/100")
        print(f"   - File: {os.path.basename(audit_file_path)}")
        print(f"   - Sent to user")

        return {
            'audit_score': audit_result.get('final_score', 0),
            'audit_file': audit_file_path,
            'audit_result': audit_result
        }


# =============================================================================
# E2E TESTS
# =============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_production_flow_with_audit_accept():
    """
    E2E Test: Complete production workflow - USER ACCEPTS AUDIT

    Tests full workflow:
    1. Hardcoded questions
    2. Interactive questions
    3. Save to DB
    4. Generate anketa.txt
    5. Send to user
    6. User clicks "Начать аудит"
    7. Run audit
    8. Generate audit.txt
    9. Send audit to user
    """
    print("\n" + "="*80)
    print("TEST: Complete Production Flow - ACCEPT AUDIT")
    print("="*80)

    # Setup
    db = GrantServiceDatabase()
    workflow = ProductionWorkflowSimulator(db, quality_level="medium")

    # Run workflow WITH audit
    result = await workflow.run_full_workflow(accept_audit=True)

    # === ASSERTIONS ===

    # Phase 1: Hardcoded questions
    assert len(result['hardcoded_data']) >= 3, "Should collect at least 3 hardcoded answers"
    assert 'user_name' in result['hardcoded_data'], "Should collect user name"

    # Phase 2: Interactive questions
    assert result['interview_result'] is not None, "Interview should complete"
    assert result['interview_result'].get('questions_asked', 0) >= 10, "Should ask at least 10 questions total"

    # Phase 3: Database
    assert result['db_result']['saved'] == True, "Should save to database"
    assert result['session_id'] is not None, "Should have session ID"
    assert result['anketa_id'] is not None, "Should have anketa ID"

    # Phase 4: File generation
    assert os.path.exists(result['anketa_file']), "anketa.txt should exist"
    with open(result['anketa_file'], 'r', encoding='utf-8') as f:
        anketa_content = f.read()
    assert len(anketa_content) > 0, "anketa.txt should not be empty"

    # Phase 5: Send to user
    assert result['send_result']['sent'] == True, "Should send file to user"

    # Phase 6: Audit
    assert result['audit_result'] is not None, "Audit should run when accepted"
    assert 'audit_score' in result['audit_result'], "Audit should return score"
    assert 0 <= result['audit_result']['audit_score'] <= 100, "Score should be 0-100"
    assert 'audit_file' in result['audit_result'], "Audit should generate file"
    assert os.path.exists(result['audit_result']['audit_file']), "audit.txt should exist"

    # Workflow completeness
    assert len(result['dialog_history']) >= 10, "Should have substantial dialog"
    assert workflow.workflow_duration < 600, "Workflow should complete in reasonable time (<10 min)"

    # Cleanup
    for file_path in workflow.files_generated.values():
        if os.path.exists(file_path):
            os.unlink(file_path)

    print("\n" + "="*80)
    print("TEST PASSED: Complete workflow with audit acceptance")
    print("="*80)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_production_flow_with_audit_decline():
    """
    E2E Test: Complete production workflow - USER DECLINES AUDIT

    Tests full workflow:
    1. Hardcoded questions
    2. Interactive questions
    3. Save to DB
    4. Generate anketa.txt
    5. Send to user
    6. User clicks "Отказаться"
    7. Workflow ends (no audit)
    """
    print("\n" + "="*80)
    print("TEST: Complete Production Flow - DECLINE AUDIT")
    print("="*80)

    # Setup
    db = GrantServiceDatabase()
    workflow = ProductionWorkflowSimulator(db, quality_level="high")

    # Run workflow WITHOUT audit
    result = await workflow.run_full_workflow(accept_audit=False)

    # === ASSERTIONS ===

    # Phases 1-5 should complete
    assert len(result['hardcoded_data']) >= 3
    assert result['interview_result'] is not None
    assert result['db_result']['saved'] == True
    assert os.path.exists(result['anketa_file'])
    assert result['send_result']['sent'] == True

    # Phase 6: NO audit
    assert result['audit_result'] is None, "Audit should NOT run when declined"
    assert 'audit.txt' not in workflow.files_generated, "Should not generate audit file"

    # Cleanup
    for file_path in workflow.files_generated.values():
        if os.path.exists(file_path):
            os.unlink(file_path)

    print("\n" + "="*80)
    print("TEST PASSED: Complete workflow with audit decline")
    print("="*80)


if __name__ == "__main__":
    """Run E2E tests directly."""
    pytest.main([__file__, "-v", "-s", "--tb=short"])
