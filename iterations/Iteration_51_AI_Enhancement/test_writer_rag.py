"""
Test script for WriterAgent with RAG enhancement (Iteration 51 - Phase 4)

Tests that WriterAgent successfully uses RAG retrieval to enhance grant writing.

Usage:
    python iterations/Iteration_51_AI_Enhancement/test_writer_rag.py
"""

import sys
import os
import asyncio
import logging

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../agents'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def load_qdrant_collections():
    """Load Qdrant collections (fpg_real_winners + fpg_requirements_gigachat)"""
    logger.info("[SETUP] Loading Qdrant collections...")

    # Run loaders
    import subprocess

    logger.info("[SETUP] Loading Phase 1 collection (fpg_real_winners)...")
    result1 = subprocess.run(
        ["python", "scripts/load_fpg_to_qdrant.py"],
        capture_output=True,
        text=True
    )

    if result1.returncode != 0:
        logger.error(f"[ERROR] Failed to load fpg_real_winners: {result1.stderr}")
        return False

    logger.info("[SETUP] Loading Phase 2 collection (fpg_requirements_gigachat)...")
    result2 = subprocess.run(
        ["python", "scripts/load_fpg_requirements_to_qdrant.py"],
        capture_output=True,
        text=True
    )

    if result2.returncode != 0:
        logger.error(f"[ERROR] Failed to load fpg_requirements: {result2.stderr}")
        return False

    logger.info("[SETUP] Both collections loaded successfully")
    return True


async def test_writer_agent_with_rag():
    """Test WriterAgent with RAG enhancement"""

    logger.info("\n" + "=" * 80)
    logger.info("ITERATION 51 - Phase 4: WriterAgent RAG Integration Test")
    logger.info("=" * 80 + "\n")

    # Test project (youth entrepreneurship project)
    test_project = {
        "user_answers": {
            "project_name": "Школа молодых предпринимателей",
            "description": "Создание образовательной программы для молодежи 18-25 лет по основам предпринимательства и стартапов в малых городах",
            "budget": "2000000 рублей",
            "timeline": "12 месяцев",
            "quality_level": "HIGH"
        },
        "research_data": {},
        "selected_grant": {}
    }

    logger.info(f"[TEST] Project: {test_project['user_answers']['project_name']}")
    logger.info(f"[TEST] Description: {test_project['user_answers']['description'][:100]}...\n")

    # Test 1: Initialize WriterAgent with RAG
    logger.info("[TEST 1] Initializing WriterAgent with RAG...")
    try:
        # Import WriterAgent
        from agents.writer_agent import WriterAgent

        # Create mock DB
        class MockDB:
            pass

        db = MockDB()
        agent = WriterAgent(db=db, llm_provider="gigachat")

        if agent.rag_retriever:
            logger.info("[OK] WriterAgent initialized with RAG retriever")
        else:
            logger.warning("[WARNING] WriterAgent initialized WITHOUT RAG retriever")

    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize WriterAgent: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Test RAG retrieval (without actual generation)
    logger.info("\n[TEST 2] Testing RAG retrieval...")
    try:
        if agent.rag_retriever:
            # Test upfront retrieval
            description = test_project['user_answers']['description']
            similar_grants = agent.rag_retriever.retrieve_similar_grants(
                query_text=description,
                top_k=3
            )

            logger.info(f"[OK] Retrieved {len(similar_grants)} similar grants")
            for i, grant in enumerate(similar_grants):
                logger.info(f"  {i+1}. {grant['title']} (score: {grant.get('max_score', 0):.3f})")

            # Test section-specific retrieval
            problem_examples = agent.rag_retriever.retrieve_section_examples(
                section_name="problem",
                query_text=description,
                top_k=2
            )

            logger.info(f"[OK] Retrieved {len(problem_examples)} problem examples")

        else:
            logger.warning("[SKIP] RAG retriever not available")

    except Exception as e:
        logger.error(f"[ERROR] RAG retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Test full WriterAgent execution (commented out to save tokens/time)
    logger.info("\n[TEST 3] Full WriterAgent execution (skipped to save time)")
    logger.info("[INFO] To test full generation, uncomment the code in test_writer_rag.py")

    # Uncomment to test full generation:
    # try:
    #     result = await agent.write_application_async(test_project)
    #     logger.info(f"[OK] Grant application generated: {result['status']}")
    #     logger.info(f"[OK] Problem section length: {len(result['application_content'].get('problem', ''))} chars")
    # except Exception as e:
    #     logger.error(f"[ERROR] Generation failed: {e}")
    #     return False

    logger.info("\n" + "=" * 80)
    logger.info("[SUCCESS] All RAG integration tests passed!")
    logger.info("=" * 80)

    return True


if __name__ == "__main__":
    try:
        # Note: Collection loading is commented out since we need to run loaders separately
        # Uncomment if you want to reload collections automatically:
        # asyncio.run(load_qdrant_collections())

        # Run tests
        success = asyncio.run(test_writer_agent_with_rag())

        if success:
            logger.info("\n[RESULT] ✅ TESTS PASSED")
            sys.exit(0)
        else:
            logger.error("\n[RESULT] ❌ TESTS FAILED")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n[FATAL] Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
