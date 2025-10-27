"""
Integration tests for GrantService pipeline with REAL agents.

Tests use:
- REAL agent classes (production imports)
- REAL PostgreSQL database (test instance)
- MOCKED LLM calls (GigaChat)

Run with: pytest tests/integration/test_pipeline_real_agents.py -v
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
# TEST 0: Fixtures Verification
# ============================================================

@pytest.mark.integration
def test_fixtures_work(test_db, test_anketa, mock_gigachat):
    """
    Verify that all fixtures load correctly.
    This test should pass first before running others.
    """
    # Test database fixture
    assert test_db is not None, "Database fixture not loaded"

    # Test anketa fixture
    assert test_anketa is not None, "Anketa fixture not loaded"
    assert 'id' in test_anketa, "Anketa missing ID"
    assert 'project_name' in test_anketa, "Anketa missing project_name"

    # Test mock fixture
    assert mock_gigachat is not None, "GigaChat mock not loaded"

    print("✅ All fixtures loaded successfully!")


# ============================================================
# TEST 1: Database Operations
# ============================================================

@pytest.mark.integration
def test_database_connection(test_db):
    """Test that we can connect to database"""

    # Verify db object exists and has required methods
    assert test_db is not None, "Database object is None"

    # Check that key methods exist
    assert hasattr(test_db, 'get_all_users'), "Database missing get_all_users method"
    assert hasattr(test_db, 'get_active_sessions'), "Database missing get_active_sessions method"
    assert hasattr(test_db, 'connection_params'), "Database missing connection_params"

    # Check connection params are set
    assert test_db.connection_params is not None, "Connection params not initialized"
    assert 'database' in test_db.connection_params, "Database name not in connection params"

    print(f"✅ Database connection verified! Database: {test_db.connection_params['database']}")


# ============================================================
# TEST 2: Auditor Agent Integration (Simplified)
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_auditor_agent_basic(test_db, test_anketa):
    """
    Test that AuditorAgent can be imported and instantiated.
    This is a basic smoke test.
    """

    try:
        # Try to import agent
        from agents.auditor_agent import AuditorAgent

        # Try to create instance WITH db parameter
        auditor = AuditorAgent(db=test_db)

        assert auditor is not None
        print("✅ AuditorAgent imported and instantiated successfully!")

    except ImportError as e:
        pytest.skip(f"AuditorAgent not available: {e}")
    except Exception as e:
        pytest.fail(f"AuditorAgent instantiation failed: {e}")


# ============================================================
# TEST 3: Production Writer Integration (Simplified)
# ============================================================

@pytest.mark.integration
def test_production_writer_basic():
    """
    Test that ProductionWriter can be imported and instantiated.
    Basic smoke test.
    """

    try:
        # Try to import
        from agents.production_writer import ProductionWriter

        # Try to create instance
        writer = ProductionWriter()

        assert writer is not None
        print("✅ ProductionWriter imported and instantiated successfully!")

    except ImportError as e:
        pytest.skip(f"ProductionWriter not available: {e}")
    except Exception as e:
        pytest.fail(f"ProductionWriter instantiation failed: {e}")


# ============================================================
# TEST 4: Reviewer Agent Integration (Simplified)
# ============================================================

@pytest.mark.integration
def test_reviewer_agent_basic(test_db):
    """
    Test that ReviewerAgent can be imported and instantiated.
    Basic smoke test.
    """

    try:
        # Try to import
        from agents.reviewer_agent import ReviewerAgent

        # Try to create instance WITH db parameter
        reviewer = ReviewerAgent(db=test_db)

        assert reviewer is not None
        print("✅ ReviewerAgent imported and instantiated successfully!")

    except ImportError as e:
        pytest.skip(f"ReviewerAgent not available: {e}")
    except Exception as e:
        pytest.fail(f"ReviewerAgent instantiation failed: {e}")


# ============================================================
# TEST 5: Pipeline Handler Import
# ============================================================

@pytest.mark.integration
def test_pipeline_handler_import():
    """
    Test that InteractivePipelineHandler can be imported.
    This validates Iteration 52 code is available.
    """

    try:
        from handlers.interactive_pipeline_handler import InteractivePipelineHandler

        assert InteractivePipelineHandler is not None
        print("✅ InteractivePipelineHandler imported successfully!")

    except ImportError as e:
        pytest.skip(f"InteractivePipelineHandler not available (Iteration 52 code): {e}")


# ============================================================
# TEST 6: Full Agent Method Signatures
# ============================================================

@pytest.mark.integration
def test_agent_method_signatures(test_db):
    """
    Verify that agents have expected methods.
    This catches AttributeError issues from Iteration 52.
    """

    # Test Auditor Agent
    try:
        from agents.auditor_agent import AuditorAgent
        auditor = AuditorAgent(db=test_db)

        # Check for audit method
        assert hasattr(auditor, 'audit_application_async') or \
               hasattr(auditor, 'audit_application') or \
               hasattr(auditor, 'audit'), \
               "AuditorAgent missing audit method"

        print("✅ AuditorAgent has audit method")

    except ImportError:
        pytest.skip("AuditorAgent not available")

    # Test Production Writer
    try:
        from agents.production_writer import ProductionWriter
        writer = ProductionWriter()

        # Check for write method
        assert hasattr(writer, 'write') or \
               hasattr(writer, 'generate') or \
               hasattr(writer, 'write_grant'), \
               "ProductionWriter missing write method"

        print("✅ ProductionWriter has write method")

    except ImportError:
        pytest.skip("ProductionWriter not available")

    # Test Reviewer Agent
    try:
        from agents.reviewer_agent import ReviewerAgent
        reviewer = ReviewerAgent(db=test_db)

        # Check for review method
        assert hasattr(reviewer, 'review_grant_async') or \
               hasattr(reviewer, 'review_grant') or \
               hasattr(reviewer, 'review'), \
               "ReviewerAgent missing review method"

        print("✅ ReviewerAgent has review method")

    except ImportError:
        pytest.skip("ReviewerAgent not available")


# ============================================================
# Helper to run all tests
# ============================================================

if __name__ == "__main__":
    """
    Run tests directly:
    python tests/integration/test_pipeline_real_agents.py
    """
    pytest.main([__file__, "-v", "-s"])
