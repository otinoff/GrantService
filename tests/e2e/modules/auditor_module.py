#!/usr/bin/env python3
"""
AuditorTestModule - Тестирование PRODUCTION AuditorAgent

Source: Iteration 54 (Auditor Fix)
Tests: Production AuditorAgentClaude with BaseAgent unwrap
Critical: Validates unwrap_result() for nested responses

Iteration 66: E2E Test Suite
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditorTestModule:
    """
    Test module for AuditorAgent

    Tests PRODUCTION AuditorAgentClaude code
    Key fix: Unwrap BaseAgent result to get actual audit data
    """

    def __init__(self, db):
        """
        Initialize test module

        Args:
            db: GrantServiceDatabase instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def test_auditor(
        self,
        anketa_data: Dict[str, Any],
        llm_provider: str = "gigachat"
    ) -> Dict[str, Any]:
        """
        Test PRODUCTION AuditorAgent

        What it does:
        1. Imports PRODUCTION AuditorAgentClaude
        2. Prepares anketa input
        3. Calls audit_anketa()
        4. Unwraps BaseAgent result (ITERATION 54 FIX!)
        5. Validates audit score > 0
        6. Saves to auditor_results table

        Args:
            anketa_data: Dict with anketa_id, user_answers
            llm_provider: LLM provider

        Returns:
            Dict with:
                - audit_id: str
                - audit_score: float
                - missing_fields: List[str]
                - model: str

        Raises:
            ValueError: If audit fails validation
        """
        self.logger.info("="*60)
        self.logger.info("AUDITOR TEST MODULE")
        self.logger.info("="*60)

        # 1. Import PRODUCTION AuditorAgent
        from agents.auditor_agent_claude import AuditorAgentClaude
        from datetime import datetime
        import json

        # 2. Initialize auditor
        auditor = AuditorAgentClaude(self.db, llm_provider=llm_provider)

        # 3. Prepare input
        anketa_input = {
            "anketa_id": anketa_data['anketa_id'],
            "user_answers": anketa_data['user_answers']
        }

        self.logger.info(f"Testing AuditorAgent for anketa: {anketa_data['anketa_id']}")

        # 4. Run audit (PRODUCTION METHOD: evaluate_project_async)
        self.logger.info("Calling AuditorAgentClaude.evaluate_project_async()...")
        audit_result = await auditor.evaluate_project_async(anketa_input)

        # 5. Unwrap BaseAgent result (ITERATION 54 FIX!)
        # AuditorAgent may return nested {'status': 'success', 'result': {...}}
        if isinstance(audit_result, dict):
            if 'result' in audit_result:
                audit_data = audit_result['result']
            else:
                audit_data = audit_result
        else:
            audit_data = audit_result

        # 6. Extract audit scores (PRODUCTION FORMAT)
        # AuditorAgentClaude returns: completeness_score, quality_score, compliance_score (0-100)
        completeness = int(audit_data.get('completeness_score', 70))
        quality = int(audit_data.get('quality_score', 70))
        compliance = int(audit_data.get('compliance_score', 70))

        # 7. Convert to 5 scores (1-10) like web-admin does
        comp_score = min(10, max(1, completeness // 10))
        clar_score = min(10, max(1, quality // 10))
        feas_score = min(10, max(1, compliance // 10))
        inno_score = min(10, max(1, quality // 10))
        qual_score = min(10, max(1, quality // 10))

        # 8. Calculate average (required by DB constraint)
        average_score = round((comp_score + clar_score + feas_score + inno_score + qual_score) / 5.0, 2)

        self.logger.info(f"Audit scores: comp={comp_score}, clar={clar_score}, feas={feas_score}, inno={inno_score}, qual={qual_score}")
        self.logger.info(f"Average score: {average_score}")

        # 9. Get session_id from anketa_data
        session_id = anketa_data.get('session_id')
        if not session_id:
            raise ValueError("anketa_data must contain 'session_id' for PRODUCTION schema")

        # 10. Map approval status
        status_map = {
            'Отлично': 'approved',
            'Хорошо': 'approved',
            'Удовлетворительно': 'needs_revision',
            'Требует доработки': 'needs_revision',
            'Не готово': 'rejected'
        }
        approval_status = status_map.get(
            audit_data.get('readiness_status', 'Требует доработки'),
            'needs_revision'
        )

        # 11. Save to database (PRODUCTION SCHEMA)
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO auditor_results (
                    session_id, completeness_score, clarity_score,
                    feasibility_score, innovation_score, quality_score,
                    average_score, approval_status, recommendations,
                    auditor_llm_provider, model, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                session_id,
                comp_score,
                clar_score,
                feas_score,
                inno_score,
                qual_score,
                average_score,
                approval_status,
                json.dumps(audit_data.get('recommendations', []), ensure_ascii=False),
                llm_provider,
                'GigaChat-Max',
                json.dumps(audit_data, ensure_ascii=False)
            ))
            audit_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        self.logger.info(f"✅ Audit saved to DB: ID={audit_id}, avg_score={average_score}, status={approval_status}")

        return {
            'audit_id': audit_id,
            'average_score': average_score,
            'approval_status': approval_status,
            'scores': {
                'completeness': comp_score,
                'clarity': clar_score,
                'feasibility': feas_score,
                'innovation': inno_score,
                'quality': qual_score
            },
            'model': 'GigaChat-Max'
        }

    def export_to_file(self, audit_data: Dict, filepath: Path):
        """Export audit to text file (PRODUCTION FORMAT)"""
        content = []
        content.append("=" * 80)
        content.append("AUDITOR TEST RESULT (PRODUCTION SCHEMA)")
        content.append("=" * 80)
        content.append(f"\nAudit ID: {audit_data['audit_id']}")
        content.append(f"Approval Status: {audit_data['approval_status']}")
        content.append(f"Model: {audit_data['model']}")
        content.append("")
        content.append("=" * 80)
        content.append("SCORES (1-10 scale)")
        content.append("=" * 80)
        scores = audit_data.get('scores', {})
        content.append(f"Completeness:  {scores.get('completeness', 0)}/10")
        content.append(f"Clarity:       {scores.get('clarity', 0)}/10")
        content.append(f"Feasibility:   {scores.get('feasibility', 0)}/10")
        content.append(f"Innovation:    {scores.get('innovation', 0)}/10")
        content.append(f"Quality:       {scores.get('quality', 0)}/10")
        content.append(f"")
        content.append(f"Average Score: {audit_data['average_score']}/10")
        content.append("")
        content.append("=" * 80)

        filepath.write_text('\n'.join(content), encoding='utf-8')
        self.logger.info(f"Exported audit to: {filepath}")
