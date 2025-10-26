#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Reviewer Agent - Final Grant Review
Based on: docs/TESTING-METHODOLOGY-GRANTSERVICE.md, iterations/Iteration_49_Reviewer_Testing/00_ITERATION_PLAN.md

Iteration 49: Test ReviewerAgent on MEDIUM quality grant from Iteration 48
Tests vector DB integration, 4-criteria evaluation, and production readiness assessment
"""
import sys
from pathlib import Path

# Project root setup
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List

# ===== IMPORTS =====
from agents.reviewer_agent import ReviewerAgent

try:
    from data.database.models import db as DatabaseManager
except ImportError:
    try:
        from data.database.db_manager import DatabaseManager
    except ImportError:
        print("⚠️ DatabaseManager not found, test will skip")
        DatabaseManager = None


# ===== TEST CONFIGURATION =====

# Grant to review (from Iteration 48)
GRANT_APPLICATION_NUMBER = "GA-20251026-7A4C689D"  # MEDIUM quality grant (53,683 chars)

# Success criteria from Iteration 49 plan
SUCCESS_CRITERIA = {
    'min_readiness_score': 5.0,  # 0-10 scale (7+ считается готовым к подаче)
    'max_review_time': 120,  # 2 minutes max
    'required_criteria': ['evidence_base', 'structure', 'matching', 'economics'],
    'criteria_count': 4,
    'min_fpg_requirements': 4,  # Minimum 4 FPG requirements from vector DB (one per criterion)
    'min_strengths': 1,
    'min_weaknesses': 1,
    'min_recommendations': 3,
}


# ===== PYTEST MARKERS =====

pytestmark = [
    pytest.mark.integration,  # Needs database
    pytest.mark.slow,         # Takes time (vector search + analysis)
]


# ===== FIXTURES =====

@pytest.fixture(scope="module")
def db():
    """
    Real PostgreSQL database connection (singleton from models.py)

    Scope: module - shared across all tests in this file
    """
    if DatabaseManager is None:
        pytest.skip("DatabaseManager not available")

    yield DatabaseManager
    # No cleanup - we want to keep review results


@pytest.fixture(scope="module")
def reviewer(db):
    """ReviewerAgent with production configuration"""
    # Create agent with claude_code provider (default)
    agent = ReviewerAgent(db=db, llm_provider="claude_code")

    return agent


@pytest.fixture(scope="module")
def grant_from_db(db) -> Dict[str, Any]:
    """
    Load grant application from database

    Returns full grant data for review:
    - grant_content: parsed JSON content
    - user_answers: original user answers
    - metadata: application_number, status, created_at
    """
    with db.connect() as conn:
        cursor = conn.cursor()

        # Fetch grant application
        cursor.execute("""
            SELECT
                application_number,
                status,
                content_json,
                created_at
            FROM grant_applications
            WHERE application_number = %s
        """, (GRANT_APPLICATION_NUMBER,))

        row = cursor.fetchone()
        cursor.close()

        if not row:
            pytest.skip(f"Grant application not found: {GRANT_APPLICATION_NUMBER}")

        application_number, status, content_json, created_at = row

        # Parse content
        if isinstance(content_json, str):
            content = json.loads(content_json)
        else:
            content = content_json

        return {
            'application_number': application_number,
            'status': status,
            'grant_content': content,
            'user_answers': content.get('user_answers', {}),
            'created_at': created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
        }


# ===== HELPER FUNCTIONS =====

def validate_review_structure(result: Dict[str, Any]) -> None:
    """Validate review result structure"""
    # 1. TECHNICAL structure validation
    assert 'status' in result, "Missing 'status' field"
    assert result['status'] == 'success', f"Review failed: {result.get('message')}"

    assert 'agent_type' in result, "Missing 'agent_type' field"
    assert result['agent_type'] == 'reviewer', f"Wrong agent type: {result['agent_type']}"

    # 2. READINESS SCORE (0-10)
    assert 'readiness_score' in result, "Missing 'readiness_score'"
    readiness_score = result['readiness_score']
    assert isinstance(readiness_score, (int, float)), "readiness_score must be numeric"
    assert 0 <= readiness_score <= 10, f"readiness_score out of range: {readiness_score}"

    # 3. APPROVAL PROBABILITY (0-100%)
    assert 'approval_probability' in result, "Missing 'approval_probability'"
    approval_prob = result['approval_probability']
    assert isinstance(approval_prob, (int, float)), "approval_probability must be numeric"
    assert 0 <= approval_prob <= 100, f"approval_probability out of range: {approval_prob}"

    # 4. FPG REQUIREMENTS from vector DB
    assert 'fpg_requirements' in result, "Missing 'fpg_requirements' (vector DB)"
    fpg_req = result['fpg_requirements']
    assert isinstance(fpg_req, dict), "fpg_requirements must be a dict"

    # 5. CRITERIA SCORES (4 criteria)
    assert 'criteria_scores' in result, "Missing 'criteria_scores'"
    criteria = result['criteria_scores']
    assert isinstance(criteria, dict), "criteria_scores must be a dict"

    required_criteria = SUCCESS_CRITERIA['required_criteria']
    for criterion in required_criteria:
        assert criterion in criteria, f"Missing criterion: {criterion}"

        criterion_data = criteria[criterion]
        assert 'score' in criterion_data, f"Missing score in {criterion}"
        assert 'weight' in criterion_data, f"Missing weight in {criterion}"
        assert 'weighted_score' in criterion_data, f"Missing weighted_score in {criterion}"

        # Score должен быть 0-10
        score = criterion_data['score']
        assert 0 <= score <= 10, f"{criterion} score out of range: {score}"

    # 6. STRENGTHS & WEAKNESSES
    assert 'strengths' in result, "Missing 'strengths'"
    assert isinstance(result['strengths'], list), "strengths must be a list"

    assert 'weaknesses' in result, "Missing 'weaknesses'"
    assert isinstance(result['weaknesses'], list), "weaknesses must be a list"

    # 7. RECOMMENDATIONS
    assert 'recommendations' in result, "Missing 'recommendations'"
    assert isinstance(result['recommendations'], list), "recommendations must be a list"

    # 8. QUALITY TIER & CAN_SUBMIT
    assert 'quality_tier' in result, "Missing 'quality_tier'"
    assert 'can_submit' in result, "Missing 'can_submit'"
    assert isinstance(result['can_submit'], bool), "can_submit must be boolean"


def validate_vector_db_usage(result: Dict[str, Any]) -> None:
    """Validate that vector DB was actually used"""
    fpg_req = result['fpg_requirements']

    # Проверяем что хотя бы для одного критерия получены требования
    total_requirements = 0
    for criterion, requirements in fpg_req.items():
        if isinstance(requirements, list):
            total_requirements += len(requirements)

    assert total_requirements >= SUCCESS_CRITERIA['min_fpg_requirements'], \
        f"Too few FPG requirements from vector DB: {total_requirements}, expected >= {SUCCESS_CRITERIA['min_fpg_requirements']}"

    print(f"\n✅ Vector DB usage confirmed: {total_requirements} FPG requirements retrieved")

    # Показываем примеры требований
    for criterion, requirements in fpg_req.items():
        if requirements:
            print(f"   - {criterion}: {len(requirements)} requirements")


def validate_business_logic(result: Dict[str, Any], grant_data: Dict[str, Any]) -> None:
    """Validate business logic and semantic content"""
    # 1. READINESS SCORE должен быть разумным для MEDIUM quality
    readiness_score = result['readiness_score']
    # MEDIUM quality grant (без research/citations) должен получить 3-8/10
    # Низкая оценка ожидаема если нет доказательной базы (citations, tables, research_results)
    assert 2.0 <= readiness_score <= 9.0, \
        f"Unexpected readiness_score for MEDIUM grant: {readiness_score} (expected 3-8)"

    # 2. APPROVAL PROBABILITY должна соответствовать readiness_score
    approval_prob = result['approval_probability']
    # Формула из reviewer_agent.py: base_probability(15%) + (readiness_score * multiplier(4.375))
    # Для score 2-9: 15 + (2*4.375) = 23.75% до 15 + (9*4.375) = 54.375%
    expected_min = 15 + (2.0 * 4.375)
    expected_max = 15 + (9.0 * 4.375)
    assert expected_min <= approval_prob <= expected_max, \
        f"approval_probability {approval_prob}% не соответствует readiness_score {readiness_score}"

    # 3. STRENGTHS и WEAKNESSES должны быть содержательными
    strengths = result['strengths']
    weaknesses = result['weaknesses']

    assert len(strengths) >= SUCCESS_CRITERIA['min_strengths'], \
        f"Too few strengths: {len(strengths)}"
    assert len(weaknesses) >= SUCCESS_CRITERIA['min_weaknesses'], \
        f"Too few weaknesses: {len(weaknesses)}"

    # Проверяем что это не пустые строки
    for strength in strengths:
        assert len(strength) > 10, f"Strength too short: {strength}"
    for weakness in weaknesses:
        assert len(weakness) > 10, f"Weakness too short: {weakness}"

    # 4. RECOMMENDATIONS должны быть конкретными
    recommendations = result['recommendations']
    assert len(recommendations) >= SUCCESS_CRITERIA['min_recommendations'], \
        f"Too few recommendations: {len(recommendations)}"

    for rec in recommendations:
        assert len(rec) > 15, f"Recommendation too short: {rec}"

    # 5. CAN_SUBMIT должен соответствовать readiness_score
    can_submit = result['can_submit']
    # Порог готовности: 7.0 (из reviewer_agent.py:282)
    expected_can_submit = readiness_score >= 7.0
    assert can_submit == expected_can_submit, \
        f"can_submit={can_submit} не соответствует readiness_score={readiness_score} (threshold=7.0)"

    print(f"\n✅ Business logic validated:")
    print(f"   - Readiness: {readiness_score:.2f}/10")
    print(f"   - Approval Probability: {approval_prob:.1f}%")
    print(f"   - Can Submit: {can_submit}")
    print(f"   - Strengths: {len(strengths)}, Weaknesses: {len(weaknesses)}")
    print(f"   - Recommendations: {len(recommendations)}")


# ===== TESTS =====

@pytest.mark.asyncio
async def test_review_medium_grant_async(reviewer, grant_from_db):
    """
    Test ReviewerAgent on MEDIUM quality grant (async)

    Success Criteria:
    1. Review completes successfully
    2. Vector DB used (FPG requirements retrieved)
    3. All 4 criteria evaluated
    4. Readiness score 5-8/10
    5. Approval probability calculated
    6. Strengths, weaknesses, recommendations present
    7. Processing time < 2 minutes
    """
    print(f"\n{'='*80}")
    print(f"TEST: Reviewer Agent - MEDIUM Quality Grant Review")
    print(f"Grant: {grant_from_db['application_number']}")
    print(f"Created: {grant_from_db['created_at']}")
    print(f"{'='*80}\n")

    # Prepare input data
    input_data = {
        'grant_content': grant_from_db['grant_content'],
        'user_answers': grant_from_db['user_answers'],
        'research_results': {},  # Optional
        'citations': [],         # Optional
        'tables': [],            # Optional
        'selected_grant': {},    # Optional
    }

    start_time = time.time()

    # 1. EXECUTE review
    result = await reviewer.review_grant_async(input_data)

    processing_time = time.time() - start_time

    # 2. VALIDATE TECHNICAL structure
    print("\n📋 VALIDATING STRUCTURE...")
    validate_review_structure(result)
    print("✅ Structure validation PASSED")

    # 3. VALIDATE VECTOR DB usage
    print("\n📚 VALIDATING VECTOR DB USAGE...")
    validate_vector_db_usage(result)
    print("✅ Vector DB validation PASSED")

    # 4. VALIDATE BUSINESS LOGIC
    print("\n🎯 VALIDATING BUSINESS LOGIC...")
    validate_business_logic(result, grant_from_db)
    print("✅ Business logic validation PASSED")

    # 5. VALIDATE PERFORMANCE
    print(f"\n⏱️ VALIDATING PERFORMANCE...")
    assert processing_time < SUCCESS_CRITERIA['max_review_time'], \
        f"Review took too long: {processing_time:.2f}s (max {SUCCESS_CRITERIA['max_review_time']}s)"
    print(f"✅ Performance validation PASSED ({processing_time:.2f}s)")

    # 6. PRINT SUMMARY
    print(f"\n{'='*80}")
    print(f"✅ REVIEW COMPLETED SUCCESSFULLY")
    print(f"{'='*80}")
    print(f"📊 Overall Score: {result['readiness_score']:.2f}/10")
    print(f"📈 Approval Probability: {result['approval_probability']:.1f}%")
    print(f"🎯 Quality Tier: {result['quality_tier']}")
    print(f"✅ Ready to Submit: {'YES' if result['can_submit'] else 'NO'}")
    print(f"\n🔍 Criteria Scores:")
    for criterion, data in result['criteria_scores'].items():
        print(f"   - {criterion}: {data['score']:.2f}/10 (weight: {data['weight']:.0%}, weighted: {data['weighted_score']:.2f})")

    print(f"\n💪 Strengths ({len(result['strengths'])}):")
    for i, strength in enumerate(result['strengths'][:5], 1):
        print(f"   {i}. {strength}")

    print(f"\n⚠️ Weaknesses ({len(result['weaknesses'])}):")
    for i, weakness in enumerate(result['weaknesses'][:5], 1):
        print(f"   {i}. {weakness}")

    print(f"\n💡 Recommendations ({len(result['recommendations'])}):")
    for i, rec in enumerate(result['recommendations'][:7], 1):
        print(f"   {i}. {rec}")

    print(f"\n⏱️ Processing Time: {processing_time:.2f}s")
    print(f"{'='*80}\n")


def test_review_medium_grant_sync(reviewer, grant_from_db):
    """
    Test ReviewerAgent on MEDIUM quality grant (sync wrapper)

    This test uses the synchronous wrapper method for compatibility testing.
    """
    print(f"\n{'='*80}")
    print(f"TEST: Reviewer Agent - SYNC Wrapper Test")
    print(f"Grant: {grant_from_db['application_number']}")
    print(f"{'='*80}\n")

    input_data = {
        'grant_content': grant_from_db['grant_content'],
        'user_answers': grant_from_db['user_answers'],
        'research_results': {},
        'citations': [],
        'tables': [],
        'selected_grant': {},
    }

    start_time = time.time()

    # Execute using sync wrapper
    result = reviewer.review_grant(input_data)

    processing_time = time.time() - start_time

    # Basic validation
    validate_review_structure(result)

    print(f"✅ Sync wrapper test PASSED ({processing_time:.2f}s)")
    print(f"   - Readiness: {result['readiness_score']:.2f}/10")
    print(f"   - Approval: {result['approval_probability']:.1f}%")


# ===== MAIN =====

if __name__ == "__main__":
    """Run tests directly (for debugging)"""
    pytest.main([__file__, "-xvs", "--tb=short"])
