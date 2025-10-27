"""
Integration tests for GrantService agents WITH mocked LLM calls.

These tests verify:
- Agent methods can be called successfully
- Agents handle inputs/outputs correctly
- Database integration works
- LLM responses are mocked (no actual API calls)

Run with: pytest tests/integration/test_agents_with_mocks.py -v
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# ============================================================
# TEST 1: Auditor Agent - Audit Anketa (Mocked LLM)
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_auditor_audit_anketa_mocked(test_db, test_anketa):
    """
    Test AuditorAgent.audit_application_async with mocked GigaChat.
    This verifies the agent's processing logic without actual LLM calls.
    """
    try:
        from agents.auditor_agent import AuditorAgent

        # Mock UnifiedLLMClient instead of GigaChatAPI
        with patch('agents.auditor_agent.UnifiedLLMClient') as mock_llm_class:
            # Create mock LLM instance
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm

            # Mock the generate_response method
            mock_llm.generate_response.return_value = """
            {
                "score": 8.5,
                "strengths": ["Четкая цель", "Обоснованный бюджет", "Опытная команда"],
                "weaknesses": ["Недостаточно метрик"],
                "recommendations": ["Добавить KPI", "Детализировать методологию"]
            }
            """

            # Create auditor
            auditor = AuditorAgent(db=test_db, llm_provider="gigachat")

            # Call audit method
            result = await auditor.audit_application_async(test_anketa)

            # Verify result structure
            assert result is not None, "Audit result is None"
            assert isinstance(result, dict), "Audit result is not a dict"

            # Verify LLM was called
            assert mock_llm.generate_response.called, "LLM generate_response not called"

            print(f"✅ AuditorAgent.audit_application_async works with mocked LLM!")
            print(f"   Result keys: {list(result.keys())}")

    except ImportError as e:
        pytest.skip(f"AuditorAgent not available: {e}")
    except AttributeError as e:
        pytest.fail(f"AuditorAgent missing expected method: {e}")


# ============================================================
# TEST 2: ProductionWriter - Generate Grant (Mocked LLM)
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_writer_generate_grant_mocked(test_anketa, sample_audit_result):
    """
    Test ProductionWriter.write with mocked GigaChat.
    This verifies grant generation without actual LLM calls.
    """
    try:
        from agents.production_writer import ProductionWriter

        # Mock UnifiedLLMClient
        with patch('agents.production_writer.UnifiedLLMClient') as mock_llm_class:
            # Create mock LLM instance
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm

            # Mock the generate_response method
            mock_llm.generate_response.return_value = """
# Грантовая заявка: Тестовый инновационный проект

## 1. Актуальность
Проект решает важную проблему...

## 2. Цели и задачи
Основная цель: Разработка инновационного решения...

## 3. Методология
Будет использована Agile методология...
            """

            # Create writer
            writer = ProductionWriter()

            # Call write method
            result = await writer.write(
                anketa=test_anketa,
                audit_result=sample_audit_result,
                grant_fund='fpg'
            )

            # Verify result
            assert result is not None, "Write result is None"
            assert isinstance(result, (str, dict)), "Write result has unexpected type"

            # Verify LLM was called
            assert mock_llm.generate_response.called, "LLM generate_response not called"

            print(f"✅ ProductionWriter.write works with mocked LLM!")
            if isinstance(result, str):
                print(f"   Generated text length: {len(result)} chars")
            else:
                print(f"   Result keys: {list(result.keys())}")

    except ImportError as e:
        pytest.skip(f"ProductionWriter not available: {e}")
    except AttributeError as e:
        pytest.fail(f"ProductionWriter missing expected method: {e}")


# ============================================================
# TEST 3: ReviewerAgent - Review Grant (Mocked LLM)
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_reviewer_review_grant_mocked(test_db, sample_grant_content):
    """
    Test ReviewerAgent.review_grant_async with mocked GigaChat.
    This verifies review logic without actual LLM calls.
    """
    try:
        from agents.reviewer_agent import ReviewerAgent

        # Mock UnifiedLLMClient
        with patch('agents.reviewer_agent.UnifiedLLMClient') as mock_llm_class:
            # Create mock LLM instance
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm

            # Mock the generate_response method
            mock_llm.generate_response.return_value = """
            {
                "compliance_score": 9.0,
                "compliance_details": ["Соответствует требованиям ФПГ"],
                "improvements": ["Добавить больше количественных показателей"],
                "final_recommendation": "Рекомендуется к подаче"
            }
            """

            # Create reviewer
            reviewer = ReviewerAgent(db=test_db)

            # Call review method
            result = await reviewer.review_grant_async(
                grant_text=sample_grant_content,
                grant_fund='fpg'
            )

            # Verify result
            assert result is not None, "Review result is None"
            assert isinstance(result, dict), "Review result is not a dict"

            # Verify LLM was called
            assert mock_llm.generate_response.called, "LLM generate_response not called"

            print(f"✅ ReviewerAgent.review_grant_async works with mocked LLM!")
            print(f"   Result keys: {list(result.keys())}")

    except ImportError as e:
        pytest.skip(f"ReviewerAgent not available: {e}")
    except AttributeError as e:
        pytest.fail(f"ReviewerAgent missing expected method: {e}")


# ============================================================
# TEST 4: Full Pipeline Flow (Mocked LLM)
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_mocked(test_db, test_anketa):
    """
    Test full pipeline: Audit → Write → Review
    All LLM calls are mocked for fast, deterministic testing.
    """
    try:
        from agents.auditor_agent import AuditorAgent
        from agents.production_writer import ProductionWriter
        from agents.reviewer_agent import ReviewerAgent

        # Mock all UnifiedLLMClient calls
        with patch('agents.auditor_agent.UnifiedLLMClient') as mock_auditor_llm, \
             patch('agents.production_writer.UnifiedLLMClient') as mock_writer_llm, \
             patch('agents.reviewer_agent.UnifiedLLMClient') as mock_reviewer_llm:

            # Setup auditor mock
            mock_auditor = AsyncMock()
            mock_auditor_llm.return_value = mock_auditor
            mock_auditor.generate_response.return_value = """
            {"score": 8.5, "strengths": ["Good project"], "weaknesses": ["Needs more metrics"], "recommendations": ["Add KPIs"]}
            """

            # Setup writer mock
            mock_writer = AsyncMock()
            mock_writer_llm.return_value = mock_writer
            mock_writer.generate_response.return_value = "# Грантовая заявка\n\nПроект описание..."

            # Setup reviewer mock
            mock_reviewer = AsyncMock()
            mock_reviewer_llm.return_value = mock_reviewer
            mock_reviewer.generate_response.return_value = """
            {"compliance_score": 9.0, "improvements": ["Add metrics"], "final_recommendation": "Approve"}
            """

            # STAGE 1: Audit
            print("\n[1/3] Running Auditor...")
            auditor = AuditorAgent(db=test_db, llm_provider="gigachat")
            audit_result = await auditor.audit_application_async(test_anketa)
            assert audit_result is not None, "Audit failed"
            print("   ✅ Audit completed")

            # STAGE 2: Write
            print("\n[2/3] Running Writer...")
            writer = ProductionWriter()
            grant_text = await writer.write(
                anketa=test_anketa,
                audit_result=audit_result,
                grant_fund='fpg'
            )
            assert grant_text is not None, "Write failed"
            print("   ✅ Grant generated")

            # STAGE 3: Review
            print("\n[3/3] Running Reviewer...")
            reviewer = ReviewerAgent(db=test_db)
            review_result = await reviewer.review_grant_async(
                grant_text=grant_text if isinstance(grant_text, str) else grant_text.get('content', ''),
                grant_fund='fpg'
            )
            assert review_result is not None, "Review failed"
            print("   ✅ Review completed")

            print("\n✅ FULL PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"   Audit score: {audit_result.get('score', 'N/A')}")
            print(f"   Grant length: {len(str(grant_text))} chars")
            print(f"   Review score: {review_result.get('compliance_score', 'N/A')}")

    except ImportError as e:
        pytest.skip(f"Pipeline agents not available: {e}")
    except Exception as e:
        pytest.fail(f"Pipeline execution failed: {e}")


# ============================================================
# Helper to run all tests
# ============================================================

if __name__ == "__main__":
    """
    Run tests directly:
    python tests/integration/test_agents_with_mocks.py
    """
    pytest.main([__file__, "-v", "-s"])
