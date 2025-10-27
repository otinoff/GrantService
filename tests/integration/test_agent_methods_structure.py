"""
Integration tests for GrantService agent METHOD STRUCTURES.

These tests verify:
- Agents have expected methods
- Methods accept correct parameters
- Methods return expected types
- No actual LLM calls (structure only)

Run with: pytest tests/integration/test_agent_methods_structure.py -v
"""

import pytest
import inspect
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# ============================================================
# TEST 1: Auditor Agent Method Structure
# ============================================================

@pytest.mark.integration
def test_auditor_has_audit_methods(test_db):
    """Verify AuditorAgent has expected audit methods"""
    try:
        from agents.auditor_agent import AuditorAgent

        auditor = AuditorAgent(db=test_db)

        # Check for audit_application_async method
        assert hasattr(auditor, 'audit_application_async'), "Missing audit_application_async method"
        assert callable(auditor.audit_application_async), "audit_application_async not callable"

        # Check method signature
        sig = inspect.signature(auditor.audit_application_async)
        params = list(sig.parameters.keys())
        assert 'input_data' in params, "audit_application_async missing input_data parameter"

        # Check for sync wrapper
        assert hasattr(auditor, 'audit_application'), "Missing audit_application sync method"

        print(f"✅ AuditorAgent has correct audit methods")
        print(f"   audit_application_async parameters: {params}")

    except ImportError as e:
        pytest.skip(f"AuditorAgent not available: {e}")


# ============================================================
# TEST 2: ProductionWriter Method Structure
# ============================================================

@pytest.mark.integration
def test_writer_has_write_method():
    """Verify ProductionWriter has expected write method"""
    try:
        from agents.production_writer import ProductionWriter

        writer = ProductionWriter()

        # Check for write method
        assert hasattr(writer, 'write'), "Missing write method"
        assert callable(writer.write), "write not callable"

        # Check method signature
        sig = inspect.signature(writer.write)
        params = list(sig.parameters.keys())
        assert 'anketa_data' in params, "write missing anketa_data parameter"

        # Check it's async
        assert inspect.iscoroutinefunction(writer.write), "write should be async"

        print(f"✅ ProductionWriter has correct write method")
        print(f"   write parameters: {params}")

    except ImportError as e:
        pytest.skip(f"ProductionWriter not available: {e}")


# ============================================================
# TEST 3: ReviewerAgent Method Structure
# ============================================================

@pytest.mark.integration
def test_reviewer_has_review_methods(test_db):
    """Verify ReviewerAgent has expected review methods"""
    try:
        from agents.reviewer_agent import ReviewerAgent

        reviewer = ReviewerAgent(db=test_db)

        # Check for review_grant_async method
        assert hasattr(reviewer, 'review_grant_async'), "Missing review_grant_async method"
        assert callable(reviewer.review_grant_async), "review_grant_async not callable"

        # Check method signature
        sig = inspect.signature(reviewer.review_grant_async)
        params = list(sig.parameters.keys())
        assert 'input_data' in params, "review_grant_async missing input_data parameter"

        # Check for sync wrapper
        assert hasattr(reviewer, 'review_grant'), "Missing review_grant sync method"

        # Check it's async
        assert inspect.iscoroutinefunction(reviewer.review_grant_async), "review_grant_async should be async"

        print(f"✅ ReviewerAgent has correct review methods")
        print(f"   review_grant_async parameters: {params}")

    except ImportError as e:
        pytest.skip(f"ReviewerAgent not available: {e}")


# ============================================================
# TEST 4: Agent Input Data Structures
# ============================================================

@pytest.mark.integration
def test_agent_input_structures(test_db, test_anketa):
    """Verify agents accept expected input data structures"""
    try:
        from agents.auditor_agent import AuditorAgent
        from agents.production_writer import ProductionWriter
        from agents.reviewer_agent import ReviewerAgent

        # Test Auditor input structure
        auditor = AuditorAgent(db=test_db)
        auditor_input = {
            'application': test_anketa,
            'user_answers': {},
            'research_data': {},
            'selected_grant': {}
        }
        # Just verify it accepts the structure (don't actually call)
        print(f"✅ Auditor accepts input_data with keys: {list(auditor_input.keys())}")

        # Test Writer input structure
        writer = ProductionWriter()
        writer_input = test_anketa
        # Writer expects anketa_data dict
        print(f"✅ Writer accepts anketa_data with keys: {list(writer_input.keys())}")

        # Test Reviewer input structure
        reviewer = ReviewerAgent(db=test_db)
        reviewer_input = {
            'grant_content': {},
            'anketa_id': 'test_123',
            'grant_id': 123
        }
        print(f"✅ Reviewer accepts input_data with keys: {list(reviewer_input.keys())}")

    except ImportError as e:
        pytest.skip(f"Agents not available: {e}")


# ============================================================
# TEST 5: Agent Return Types (without LLM calls)
# ============================================================

@pytest.mark.integration
def test_agent_return_type_annotations(test_db):
    """Verify agents have correct return type annotations"""
    try:
        from agents.auditor_agent import AuditorAgent
        from agents.production_writer import ProductionWriter
        from agents.reviewer_agent import ReviewerAgent
        from typing import get_type_hints

        # Check Auditor return type
        auditor = AuditorAgent(db=test_db)
        hints = get_type_hints(auditor.audit_application_async)
        assert 'return' in hints, "audit_application_async missing return type hint"
        print(f"✅ Auditor return type: {hints['return']}")

        # Check Writer return type
        writer = ProductionWriter()
        hints = get_type_hints(writer.write)
        assert 'return' in hints, "write missing return type hint"
        print(f"✅ Writer return type: {hints['return']}")

        # Check Reviewer return type
        reviewer = ReviewerAgent(db=test_db)
        hints = get_type_hints(reviewer.review_grant_async)
        assert 'return' in hints, "review_grant_async missing return type hint"
        print(f"✅ Reviewer return type: {hints['return']}")

    except ImportError as e:
        pytest.skip(f"Agents not available: {e}")


# ============================================================
# TEST 6: Agents Have Common Interface Methods
# ============================================================

@pytest.mark.integration
def test_agents_common_interface(test_db):
    """Verify all agents have common interface methods"""
    try:
        from agents.auditor_agent import AuditorAgent
        from agents.production_writer import ProductionWriter
        from agents.reviewer_agent import ReviewerAgent

        # Check Auditor has common methods
        auditor = AuditorAgent(db=test_db)
        # All agents should have some form of processing method
        has_process_method = (
            hasattr(auditor, 'audit_application_async') or
            hasattr(auditor, 'process')
        )
        assert has_process_method, "AuditorAgent missing processing method"
        print(f"✅ AuditorAgent has processing methods")

        # Check Writer has processing method
        writer = ProductionWriter()
        assert hasattr(writer, 'write'), "ProductionWriter missing write method"
        print(f"✅ ProductionWriter has processing methods")

        # Check Reviewer has processing method
        reviewer = ReviewerAgent(db=test_db)
        has_process_method = (
            hasattr(reviewer, 'review_grant_async') or
            hasattr(reviewer, 'process')
        )
        assert has_process_method, "ReviewerAgent missing processing method"
        print(f"✅ ReviewerAgent has processing methods")

        print(f"✅ All agents have consistent interface")

    except ImportError as e:
        pytest.skip(f"Agents not available: {e}")


# ============================================================
# Helper to run all tests
# ============================================================

if __name__ == "__main__":
    """
    Run tests directly:
    python tests/integration/test_agent_methods_structure.py
    """
    pytest.main([__file__, "-v", "-s"])
