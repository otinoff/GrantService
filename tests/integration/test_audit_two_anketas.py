#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Audit Two Anketas (MEDIUM vs HIGH quality)
Based on: docs/TESTING-METHODOLOGY-GRANTSERVICE.md

Iteration 46: Test auditor_agent on real interview data from Iteration 45
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
from agents.auditor_agent import AuditorAgent
# DatabaseManager находится в data/database/models.py, не db_manager.py
try:
    from data.database.models import db as DatabaseManager
except ImportError:
    # Fallback на старый путь
    try:
        from data.database.db_manager import DatabaseManager
    except ImportError:
        print("⚠️ DatabaseManager not found, test will skip")
        DatabaseManager = None

# ===== TEST CONFIGURATION =====

# GigaChat Pro model for audit (2M tokens available)
GIGACHAT_MODEL = "GigaChat-Pro"

# Success criteria from Iteration 46 plan
SUCCESS_CRITERIA = {
    'min_audits_completed': 2,
    'expected_medium_score_range': (40, 70),  # MEDIUM quality: 4-7/10
    'expected_high_score_range': (70, 90),    # HIGH quality: 7-9/10
    'high_should_exceed_medium': True,        # HIGH > MEDIUM
    'max_execution_time': 120,                # 2 minutes max per audit
}


# ===== PYTEST MARKERS =====
pytestmark = [
    pytest.mark.integration,  # Needs database
    pytest.mark.gigachat,     # Needs real GigaChat API
    pytest.mark.slow,         # Takes minutes
]


# ===== FIXTURES =====

@pytest.fixture(scope="module")
def db():
    """Real PostgreSQL database connection"""
    if DatabaseManager is None:
        pytest.skip("DatabaseManager not available")

    # DatabaseManager is already a singleton instance from models.py
    yield DatabaseManager
    # No cleanup - we want to save audit results


@pytest.fixture(scope="module")
def auditor(db):
    """AuditorAgent with GigaChat Pro"""
    return AuditorAgent(db=db, llm_provider="gigachat")


@pytest.fixture(scope="module")
def interview_1_data(db) -> Dict[str, Any]:
    """
    Extract Interview #1 data from Iteration 45

    Quality: MEDIUM
    Region: Новосибирск
    Theme: Наука
    Organization: Центр "Образовательные проекты"
    """
    # Load from text file (we created readable Q&A format in Iteration 45)
    anketa_file = _project_root / "iterations" / "Iteration_45_Full_Flow_Testing" / "INTERVIEW_1_ANKETA_MEDIUM_QUALITY.txt"

    if not anketa_file.exists():
        pytest.skip(f"Interview anketa not found: {anketa_file}")

    with open(anketa_file, 'r', encoding='utf-8') as f:
        anketa_text = f.read()

    return {
        'anketa_id': f"TEST-IT46-MEDIUM-{int(time.time())}",
        'anketa_text': anketa_text,
        'quality_level': 'MEDIUM',
        'context': {
            'region': 'Новосибирск',
            'topic': 'Наука',
            'organization': 'Центр "Образовательные проекты"'
        }
    }


@pytest.fixture(scope="module")
def interview_2_data(db) -> Dict[str, Any]:
    """
    Extract Interview #2 data from Iteration 45

    Quality: HIGH
    Region: Екатеринбург
    Theme: Наука
    Organization: Ассоциация "Молодежные инициативы"
    """
    # Load from text file
    anketa_file = _project_root / "iterations" / "Iteration_45_Full_Flow_Testing" / "INTERVIEW_2_ANKETA_HIGH_QUALITY.txt"

    if not anketa_file.exists():
        pytest.skip(f"Interview anketa not found: {anketa_file}")

    with open(anketa_file, 'r', encoding='utf-8') as f:
        anketa_text = f.read()

    return {
        'anketa_id': f"TEST-IT46-HIGH-{int(time.time())}",
        'anketa_text': anketa_text,
        'quality_level': 'HIGH',
        'context': {
            'region': 'Екатеринбург',
            'topic': 'Наука',
            'organization': 'Ассоциация "Молодежные инициативы"'
        }
    }


# ===== TEST: Audit Interview #1 (MEDIUM Quality) =====

@pytest.mark.timeout(120)  # 2 minutes max
def test_audit_interview_1_medium_quality(auditor, interview_1_data, db):
    """
    Test: Audit MEDIUM quality interview from Iteration 45

    Expected:
    - Score: 40-70/100 (4-7/10)
    - Execution time: <120s
    - Status: "Requires improvement" or "Satisfactory"
    - Recommendations: 3-7 items
    """
    print("\n" + "="*80)
    print("🔍 AUDIT #1: MEDIUM Quality Interview")
    print("="*80)

    start_time = time.time()

    # ===== PREPARE INPUT =====
    # Convert anketa text to application format
    application = _anketa_text_to_application(interview_1_data['anketa_text'])

    input_data = {
        'anketa_id': interview_1_data['anketa_id'],
        'application': application,
        'user_answers': {},  # Empty for test
        'research_data': {},  # Empty for test
        'selected_grant': {
            'name': 'Тестовый грант (Наука)',
            'requirements': 'Развитие научно-исследовательского потенциала молодёжи',
            'amount': '500000'
        }
    }

    # ===== RUN AUDIT =====
    print(f"\n📋 Anketa ID: {interview_1_data['anketa_id']}")
    print(f"📊 Quality Level: {interview_1_data['quality_level']}")
    print(f"🔧 LLM Provider: {auditor.llm_provider}")
    print(f"🤖 LLM Model: {GIGACHAT_MODEL}")
    print("\nRunning audit...")

    # Synchronous call (uses asyncio.run internally)
    result = auditor.process(input_data)

    execution_time = time.time() - start_time

    # ===== VALIDATE RESULT =====
    assert result['status'] == 'success', f"Audit failed: {result.get('error')}"

    # Extract inner result (BaseAgent wraps in {'result': {...}})
    audit_result = result['result']

    overall_score = audit_result['overall_score']
    overall_score_100 = overall_score * 100  # Convert 0-1 to 0-100

    completeness_score = audit_result.get('completeness_score', 0)
    quality_score = audit_result.get('quality_score', 0)
    compliance_score = audit_result.get('compliance_score', 0)

    readiness_status = audit_result.get('readiness_status', 'Unknown')
    recommendations = audit_result.get('recommendations', [])

    # ===== ASSERTIONS =====

    # Success criterion 1: Score in expected range
    min_score, max_score = SUCCESS_CRITERIA['expected_medium_score_range']
    assert min_score <= overall_score_100 <= max_score, \
        f"MEDIUM quality score {overall_score_100:.1f} outside expected range [{min_score}, {max_score}]"

    # Success criterion 2: Execution time
    assert execution_time < SUCCESS_CRITERIA['max_execution_time'], \
        f"Audit took {execution_time:.1f}s, exceeds {SUCCESS_CRITERIA['max_execution_time']}s"

    # Success criterion 3: Recommendations provided
    assert len(recommendations) >= 3, \
        f"Expected at least 3 recommendations, got {len(recommendations)}"

    # Success criterion 4: Status matches score
    if overall_score_100 < 60:
        assert readiness_status in ["Требует доработки", "Не готово"], \
            f"Low score {overall_score_100:.1f} should have negative status, got {readiness_status}"

    # ===== PRINT RESULTS =====
    print("\n" + "="*80)
    print("✅ AUDIT #1 COMPLETED")
    print("="*80)
    print(f"\n📊 SCORES:")
    print(f"   Overall:      {overall_score_100:.1f}/100 (raw: {overall_score:.3f})")
    print(f"   Completeness: {completeness_score:.1f}/10")
    print(f"   Quality:      {quality_score:.1f}/10")
    print(f"   Compliance:   {compliance_score:.1f}/10")

    print(f"\n📋 STATUS: {readiness_status}")
    print(f"⏱️  TIME: {execution_time:.2f}s")

    print(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")

    print("\n" + "="*80 + "\n")

    # Return for comparison in final test
    return {
        'anketa_id': interview_1_data['anketa_id'],
        'quality_level': 'MEDIUM',
        'overall_score': overall_score_100,
        'completeness_score': completeness_score,
        'quality_score': quality_score,
        'execution_time': execution_time,
        'readiness_status': readiness_status,
        'recommendations_count': len(recommendations),
        'full_result': result
    }


# ===== TEST: Audit Interview #2 (HIGH Quality) =====

@pytest.mark.timeout(120)  # 2 minutes max
def test_audit_interview_2_high_quality(auditor, interview_2_data, db):
    """
    Test: Audit HIGH quality interview from Iteration 45

    Expected:
    - Score: 70-90/100 (7-9/10)
    - Execution time: <120s
    - Status: "Good" or "Excellent"
    - Recommendations: 1-4 items (fewer than MEDIUM)
    """
    print("\n" + "="*80)
    print("🔍 AUDIT #2: HIGH Quality Interview")
    print("="*80)

    start_time = time.time()

    # ===== PREPARE INPUT =====
    application = _anketa_text_to_application(interview_2_data['anketa_text'])

    input_data = {
        'anketa_id': interview_2_data['anketa_id'],
        'application': application,
        'user_answers': {},
        'research_data': {},
        'selected_grant': {
            'name': 'Тестовый грант (Наука)',
            'requirements': 'Развитие научно-исследовательского потенциала молодёжи',
            'amount': '1000000'
        }
    }

    # ===== RUN AUDIT =====
    print(f"\n📋 Anketa ID: {interview_2_data['anketa_id']}")
    print(f"📊 Quality Level: {interview_2_data['quality_level']}")
    print(f"🔧 LLM Provider: {auditor.llm_provider}")
    print(f"🤖 LLM Model: {GIGACHAT_MODEL}")
    print("\nRunning audit...")

    result = auditor.process(input_data)

    execution_time = time.time() - start_time

    # ===== VALIDATE RESULT =====
    assert result['status'] == 'success', f"Audit failed: {result.get('error')}"

    # Extract inner result (BaseAgent wraps in {'result': {...}})
    audit_result = result['result']

    overall_score = audit_result['overall_score']
    overall_score_100 = overall_score * 100

    completeness_score = audit_result.get('completeness_score', 0)
    quality_score = audit_result.get('quality_score', 0)
    compliance_score = audit_result.get('compliance_score', 0)

    readiness_status = audit_result.get('readiness_status', 'Unknown')
    recommendations = audit_result.get('recommendations', [])

    # ===== ASSERTIONS =====

    # Success criterion 1: Score in expected range
    min_score, max_score = SUCCESS_CRITERIA['expected_high_score_range']
    assert min_score <= overall_score_100 <= max_score, \
        f"HIGH quality score {overall_score_100:.1f} outside expected range [{min_score}, {max_score}]"

    # Success criterion 2: Execution time
    assert execution_time < SUCCESS_CRITERIA['max_execution_time'], \
        f"Audit took {execution_time:.1f}s, exceeds {SUCCESS_CRITERIA['max_execution_time']}s"

    # Success criterion 3: Status matches high quality
    assert readiness_status in ["Хорошо", "Отлично", "Удовлетворительно"], \
        f"High score {overall_score_100:.1f} should have positive status, got {readiness_status}"

    # ===== PRINT RESULTS =====
    print("\n" + "="*80)
    print("✅ AUDIT #2 COMPLETED")
    print("="*80)
    print(f"\n📊 SCORES:")
    print(f"   Overall:      {overall_score_100:.1f}/100 (raw: {overall_score:.3f})")
    print(f"   Completeness: {completeness_score:.1f}/10")
    print(f"   Quality:      {quality_score:.1f}/10")
    print(f"   Compliance:   {compliance_score:.1f}/10")

    print(f"\n📋 STATUS: {readiness_status}")
    print(f"⏱️  TIME: {execution_time:.2f}s")

    print(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")

    print("\n" + "="*80 + "\n")

    return {
        'anketa_id': interview_2_data['anketa_id'],
        'quality_level': 'HIGH',
        'overall_score': overall_score_100,
        'completeness_score': completeness_score,
        'quality_score': quality_score,
        'execution_time': execution_time,
        'readiness_status': readiness_status,
        'recommendations_count': len(recommendations),
        'full_result': result
    }


# ===== TEST: Compare MEDIUM vs HIGH =====

def test_compare_medium_vs_high(auditor, interview_1_data, interview_2_data, db):
    """
    Test: Compare audit results for MEDIUM vs HIGH quality

    Expected:
    - HIGH score > MEDIUM score (by at least 20 points)
    - HIGH has fewer recommendations
    - HIGH has better status
    """
    print("\n" + "="*80)
    print("📊 COMPARISON: MEDIUM vs HIGH Quality")
    print("="*80)

    # Run both audits
    print("\n🔄 Running MEDIUM quality audit...")
    result_medium = test_audit_interview_1_medium_quality(auditor, interview_1_data, db)

    print("\n🔄 Running HIGH quality audit...")
    result_high = test_audit_interview_2_high_quality(auditor, interview_2_data, db)

    # ===== COMPARE SCORES =====
    score_diff = result_high['overall_score'] - result_medium['overall_score']

    print("\n" + "="*80)
    print("📊 COMPARISON RESULTS")
    print("="*80)

    print(f"\n🎯 OVERALL SCORES:")
    print(f"   MEDIUM: {result_medium['overall_score']:.1f}/100")
    print(f"   HIGH:   {result_high['overall_score']:.1f}/100")
    print(f"   DIFF:   +{score_diff:.1f} points")

    print(f"\n⏱️  EXECUTION TIME:")
    print(f"   MEDIUM: {result_medium['execution_time']:.2f}s")
    print(f"   HIGH:   {result_high['execution_time']:.2f}s")

    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   MEDIUM: {result_medium['recommendations_count']} items")
    print(f"   HIGH:   {result_high['recommendations_count']} items")

    print(f"\n📋 STATUS:")
    print(f"   MEDIUM: {result_medium['readiness_status']}")
    print(f"   HIGH:   {result_high['readiness_status']}")

    # ===== ASSERTIONS =====

    # Success criterion: HIGH > MEDIUM
    if SUCCESS_CRITERIA['high_should_exceed_medium']:
        assert result_high['overall_score'] > result_medium['overall_score'], \
            f"HIGH ({result_high['overall_score']:.1f}) should exceed MEDIUM ({result_medium['overall_score']:.1f})"

        # Minimum 20-point difference expected
        assert score_diff >= 20, \
            f"Expected HIGH to exceed MEDIUM by at least 20 points, got {score_diff:.1f}"

    print("\n✅ COMPARISON PASSED!")
    print("="*80 + "\n")

    # Save comparison to file
    _save_comparison_report(result_medium, result_high, score_diff)


# ===== HELPER FUNCTIONS =====

def _anketa_text_to_application(anketa_text: str) -> Dict[str, str]:
    """
    Convert anketa text (Q&A format) to application format

    Args:
        anketa_text: Full text of the interview anketa

    Returns:
        Dict with application sections
    """
    # Simple parsing - just use the full text
    # auditor_agent will parse it automatically
    return {
        'title': 'Проект по развитию научного потенциала молодёжи',
        'summary': anketa_text[:500],
        'problem': anketa_text,
        'solution': anketa_text,
        'implementation': anketa_text,
        'budget': _extract_section(anketa_text, 'бюджет', 'budget') or anketa_text[:1000],
        'timeline': _extract_section(anketa_text, 'сроки', 'timeline') or anketa_text[:1000],
        'team': _extract_section(anketa_text, 'команда', 'team') or anketa_text[:1000],
        'impact': anketa_text,
        'sustainability': anketa_text[:1000]
    }


def _extract_section(text: str, keyword: str, section_name: str) -> str:
    """Extract section by keyword (simple heuristic)"""
    lines = text.split('\n')
    in_section = False
    section_lines = []

    for line in lines:
        if keyword.lower() in line.lower():
            in_section = True
            continue

        if in_section:
            if line.strip() and not line.strip().startswith('#'):
                section_lines.append(line)
            elif len(section_lines) > 3:
                break

    return '\n'.join(section_lines[:20])  # Max 20 lines per section


def _save_comparison_report(medium_result: Dict, high_result: Dict, score_diff: float):
    """Save comparison report to file"""
    report_path = _project_root / "iterations" / "Iteration_46_Audit_Testing" / "AUDIT_COMPARISON.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'medium_quality': medium_result,
        'high_quality': high_result,
        'score_difference': score_diff,
        'success_criteria': SUCCESS_CRITERIA,
        'verdict': 'PASSED' if score_diff >= 20 else 'FAILED'
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Comparison report saved: {report_path}")


# ===== MAIN (for standalone execution) =====

if __name__ == '__main__':
    """
    Standalone execution (outside pytest)

    Usage:
        python tests/integration/test_audit_two_anketas.py
    """
    print("\n" + "="*80)
    print("🧪 INTEGRATION TEST: Audit Two Anketas (Iteration 46)")
    print("="*80)
    print(f"\nBased on: docs/TESTING-METHODOLOGY-GRANTSERVICE.md")
    print(f"Data from: Iteration 45 Full Flow Testing")
    print(f"LLM Model: {GIGACHAT_MODEL} (GigaChat Pro)")
    print("\n" + "="*80)

    # Run with pytest
    pytest.main([__file__, '-v', '--tb=short'])
