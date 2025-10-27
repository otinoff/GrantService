#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test: Full Interview Workflow

This test REPLACES manual testing by:
1. Conducting complete interview (all questions)
2. Verifying anketa.txt file generation
3. Proceeding to audit stage
4. Verifying audit results

Based on Iteration 53 manual testing workflow.
"""

import sys
from pathlib import Path
import pytest
import asyncio
from typing import Dict, Any, List
import tempfile
import os

# Add project root to path
_project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))
sys.path.insert(0, str(_project_root / "data"))

from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2
from shared.telegram.file_generators import generate_anketa_txt
from agents.auditor_agent import AuditorAgent


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

pytestmark = pytest.mark.asyncio
pytest.mark.e2e = pytest.mark.e2e


# =============================================================================
# MOCK CALLBACK FOR AUTO-ANSWERING
# =============================================================================

class InterviewAutoResponder:
    """Automatically responds to interview questions with realistic answers."""

    def __init__(self):
        self.questions_asked: List[str] = []
        self.answers_given: List[str] = []

        # Predefined answers for common question patterns
        self.answer_patterns = {
            'название': 'AI Grant Assistant - Интеллектуальная система для грантов',
            'описание': 'Система использует AI для автоматизации подготовки грантовых заявок',
            'аудитория': 'Молодые учёные и исследователи до 35 лет',
            'бюджет': '1 500 000 рублей',
            'срок': '12 месяцев',
            'результат': 'Рабочий прототип с веб-интерфейсом',
            'команда': '5 человек: 2 разработчика, 1 дизайнер, 1 менеджер, 1 тестировщик',
            'опыт': 'Да, получали грант РФФИ в 2023 году',
            'эффект': 'Упрощение доступа к грантовому финансированию для 1000+ учёных',
            'готовность': 'Уже есть MVP, нужны средства на полноценную разработку',
            'грант': 'Фонд Президентских Грантов',
            'социальный': 'Повышение доступности грантов для молодых учёных',
            'инновации': 'Используем GPT-4 для генерации текстов и анализа требований',
            'партнёры': 'Сотрудничаем с НИУ ВШЭ и МГУ',
            'риски': 'Основной риск - изменение требований фонда, план миtigации готов'
        }

    async def ask_question(self, question: str) -> str:
        """Auto-answer question based on keywords."""
        self.questions_asked.append(question)

        # Find matching answer based on question keywords
        question_lower = question.lower()
        answer = "Подробный ответ на вопрос"  # Default

        for keyword, response in self.answer_patterns.items():
            if keyword in question_lower:
                answer = response
                break

        # If still default, generate contextual answer
        if answer == "Подробный ответ на вопрос":
            answer = f"Ответ на вопрос '{question[:30]}...': Детальная информация по проекту"

        self.answers_given.append(answer)
        return answer


# =============================================================================
# E2E TEST: FULL WORKFLOW
# =============================================================================

@pytest.mark.e2e
async def test_full_interview_and_audit_workflow(test_db, test_user_data):
    """
    E2E Test: Complete interview → anketa.txt → audit

    Replaces manual testing from Iteration 53:
    - User starts interview
    - Answers all questions
    - Receives anketa.txt file
    - Clicks "Начать аудит" button
    - Receives audit.txt file with score
    """

    # PHASE 1: Initialize Agent
    print("\n" + "="*60)
    print("PHASE 1: Initialize Interactive Interviewer Agent V2")
    print("="*60)

    agent = InteractiveInterviewerAgentV2(
        db=test_db,
        llm_provider="gigachat",
        qdrant_host=None,  # Disable for speed
        qdrant_port=None
    )

    assert agent is not None, "Agent should initialize successfully"
    assert agent.db is not None, "Database should be connected"
    print("Agent initialized successfully")


    # PHASE 2: Conduct Interview
    print("\n" + "="*60)
    print("PHASE 2: Conduct Complete Interview")
    print("="*60)

    responder = InterviewAutoResponder()

    # Run interview with auto-responder
    result = await agent.conduct_interview(
        user_data=test_user_data,
        callback_ask_question=responder.ask_question
    )

    # Verify interview completion
    assert result is not None, "Interview should return result"
    assert 'anketa' in result, "Result should contain anketa"
    assert isinstance(result['anketa'], dict), "Anketa should be dict"

    questions_count = len(responder.questions_asked)
    print(f"Interview completed: {questions_count} questions asked")

    # Verify minimum questions asked (from Iteration 53: min 10)
    assert questions_count >= 10, f"Should ask at least 10 questions, got {questions_count}"
    print(f"Minimum questions requirement met: {questions_count} >= 10")

    # Verify answers collected
    answers_count = len(responder.answers_given)
    assert answers_count == questions_count, "Should have answer for each question"
    print(f"All questions answered: {answers_count} answers collected")

    # Log some questions for verification
    print("\nSample questions asked:")
    for i, q in enumerate(responder.questions_asked[:3], 1):
        print(f"  {i}. {q}")
    print(f"  ... (total {questions_count} questions)\n")


    # PHASE 3: Generate anketa.txt File
    print("="*60)
    print("PHASE 3: Generate anketa.txt File")
    print("="*60)

    anketa_data = result['anketa']

    # Prepare data for file generation (matching file_generators.py format)
    file_data = {
        'answers_data': anketa_data if isinstance(anketa_data, dict) else {},
        'interview_data': anketa_data if isinstance(anketa_data, dict) else {}
    }

    # Generate file content
    anketa_txt_content = generate_anketa_txt(file_data)

    assert anketa_txt_content is not None, "Should generate anketa.txt content"
    assert len(anketa_txt_content) > 0, "anketa.txt should not be empty"
    print(f"anketa.txt generated: {len(anketa_txt_content)} characters")

    # Verify content has expected sections
    assert "АНКЕТА" in anketa_txt_content or "AI Grant Assistant" in anketa_txt_content, \
        "File should contain project information"
    print("anketa.txt contains valid project data")

    # Save to temp file for verification
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write(anketa_txt_content)
        temp_anketa_path = f.name

    assert os.path.exists(temp_anketa_path), "Temporary anketa.txt file should exist"
    print(f"anketa.txt saved to: {temp_anketa_path}")
    print(f"   Preview (first 200 chars):\n   {anketa_txt_content[:200]}...\n")


    # PHASE 4: Run Audit (simulating button click)
    print("="*60)
    print("PHASE 4: Run Audit (Simulate Button Click)")
    print("="*60)

    # Initialize auditor
    auditor = AuditorAgent(db=test_db)
    assert auditor is not None, "Auditor should initialize"
    print("Auditor agent initialized")

    # Prepare audit input
    audit_input = {
        'anketa_data': anketa_data,
        'grant_type': anketa_data.get('grant_type', 'Фонд Президентских Грантов')
    }

    # Run audit
    print("Running audit... (this may take time with real LLM)")
    audit_result = await auditor.audit_application_async(audit_input)

    assert audit_result is not None, "Audit should return result"
    assert 'result' in audit_result, "Audit should contain result"
    assert 'overall_score' in audit_result['result'], "Audit should contain overall_score"

    # Convert overall_score (0.0-1.0) to percentage (0-100)
    score = audit_result['result']['overall_score'] * 100
    print(f"Audit completed: score = {score:.1f}/100")

    # Verify audit score is valid
    assert 0 <= score <= 100, f"Score should be 0-100, got {score}"
    print(f"Audit score is valid: {score:.1f}/100")


    # PHASE 5: Verify Complete Workflow
    print("\n" + "="*60)
    print("PHASE 5: Verify Complete Workflow")
    print("="*60)

    # Verify all data is present
    workflow_checks = {
        'Interview completed': questions_count >= 10,
        'Anketa generated': len(anketa_txt_content) > 0,
        'Audit completed': score >= 0,
        'All phases successful': True
    }

    for check, status in workflow_checks.items():
        symbol = "[PASS]" if status else "[FAIL]"
        print(f"{symbol} {check}")

    assert all(workflow_checks.values()), "All workflow phases should succeed"


    # PHASE 6: Cleanup
    print("\n" + "="*60)
    print("PHASE 6: Cleanup")
    print("="*60)

    # Remove temp file
    if os.path.exists(temp_anketa_path):
        os.unlink(temp_anketa_path)
        print(f"Cleaned up temp file: {temp_anketa_path}")


    # FINAL SUMMARY
    print("\n" + "="*60)
    print("E2E TEST PASSED - Full Workflow Verified")
    print("="*60)
    print(f"""
Test Summary:
   - Questions Asked: {questions_count}
   - Answers Collected: {answers_count}
   - Anketa File Size: {len(anketa_txt_content)} chars
   - Audit Score: {score:.1f}/100
   - Status: PASSED

This test REPLACES manual testing from Iteration 53:
   Interview conducts all questions
   anketa.txt file generated successfully
   Audit runs and returns valid score
   No crashes or errors
    """)


# =============================================================================
# E2E TEST: Edge Cases
# =============================================================================

@pytest.mark.e2e
async def test_interview_with_short_answers(test_db, test_user_data):
    """Test that agent handles very short answers gracefully."""

    class ShortAnswerResponder:
        def __init__(self):
            self.questions_asked = []

        async def ask_question(self, question: str) -> str:
            self.questions_asked.append(question)
            return "да"  # Always short answer

    agent = InteractiveInterviewerAgentV2(
        db=test_db,
        llm_provider="gigachat",
        qdrant_host=None,
        qdrant_port=None
    )

    responder = ShortAnswerResponder()
    result = await agent.conduct_interview(
        user_data=test_user_data,
        callback_ask_question=responder.ask_question
    )

    assert result is not None
    assert len(responder.questions_asked) >= 10
    print(f"Short answer test passed: {len(responder.questions_asked)} questions")


@pytest.mark.e2e
async def test_interview_with_long_answers(test_db, test_user_data):
    """Test that agent handles very long answers gracefully."""

    class LongAnswerResponder:
        def __init__(self):
            self.questions_asked = []

        async def ask_question(self, question: str) -> str:
            self.questions_asked.append(question)
            # Very long answer
            return "Подробный ответ " * 100

    agent = InteractiveInterviewerAgentV2(
        db=test_db,
        llm_provider="gigachat",
        qdrant_host=None,
        qdrant_port=None
    )

    responder = LongAnswerResponder()
    result = await agent.conduct_interview(
        user_data=test_user_data,
        callback_ask_question=responder.ask_question
    )

    assert result is not None
    assert len(responder.questions_asked) >= 10
    print(f"Long answer test passed: {len(responder.questions_asked)} questions")


# =============================================================================
# E2E TEST: Performance
# =============================================================================

@pytest.mark.e2e
async def test_interview_performance(test_db, test_user_data):
    """Test that interview completes in reasonable time."""
    import time

    responder = InterviewAutoResponder()
    agent = InteractiveInterviewerAgentV2(
        db=test_db,
        llm_provider="gigachat",
        qdrant_host=None,
        qdrant_port=None
    )

    start_time = time.time()

    result = await agent.conduct_interview(
        user_data=test_user_data,
        callback_ask_question=responder.ask_question
    )

    duration = time.time() - start_time

    assert result is not None
    # Interview should complete in reasonable time (< 5 minutes without LLM)
    assert duration < 300, f"Interview too slow: {duration}s"

    print(f"Performance test passed: {duration:.1f}s for {len(responder.questions_asked)} questions")
    print(f"   Average: {duration/len(responder.questions_asked):.1f}s per question")


if __name__ == "__main__":
    """Run E2E tests directly."""
    pytest.main([__file__, "-v", "-s"])
