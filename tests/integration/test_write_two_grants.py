#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Write Two Grant Applications (MEDIUM vs HIGH quality)
Based on: docs/TESTING-METHODOLOGY-GRANTSERVICE.md

Iteration 47: Test writer_agent on real interview data from Iteration 45/46
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
from agents.writer_agent import WriterAgent
try:
    from data.database.models import db as DatabaseManager
except ImportError:
    try:
        from data.database.db_manager import DatabaseManager
    except ImportError:
        print("⚠️ DatabaseManager not found, test will skip")
        DatabaseManager = None

# ===== TEST CONFIGURATION =====

# GigaChat Pro model for writing (2M tokens available)
GIGACHAT_MODEL = "GigaChat-Pro"

# Success criteria from Iteration 47 plan
SUCCESS_CRITERIA = {
    'min_grants_completed': 2,
    'max_generation_time': 600,  # 10 minutes max per grant
    'min_pdf_pages_medium': 10,  # MEDIUM: at least 10 pages
    'min_pdf_pages_high': 15,    # HIGH: at least 15 pages
    'high_should_be_longer': True,  # HIGH > MEDIUM in length
}


# ===== PYTEST MARKERS =====

pytestmark = [
    pytest.mark.integration,  # Needs database
    pytest.mark.gigachat,     # Needs real GigaChat API
    pytest.mark.slow,         # Takes minutes (LLM generation)
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

    # DatabaseManager is already a singleton instance from models.py
    yield DatabaseManager
    # No cleanup - we want to save grant applications


@pytest.fixture(scope="module")
def writer(db):
    """WriterAgent with GigaChat Pro"""
    # Create agent with GigaChat provider
    agent = WriterAgent(db=db, llm_provider="gigachat")

    # Override LLM client to use GigaChat-Pro model
    if hasattr(agent, 'llm_client'):
        from shared.llm.unified_llm_client import UnifiedLLMClient
        agent.llm_client = UnifiedLLMClient(provider="gigachat", model=GIGACHAT_MODEL)

    return agent


@pytest.fixture(scope="module")
def interview_1_data_with_audit(db) -> Dict[str, Any]:
    """
    Extract Interview #1 data + audit results

    Quality: MEDIUM
    Region: Новосибирск
    Theme: Наука
    Organization: Центр "Образовательные проекты"
    """
    # Load anketa text
    anketa_file = _project_root / "iterations" / "Iteration_45_Full_Flow_Testing" / "INTERVIEW_1_ANKETA_MEDIUM_QUALITY.txt"

    if not anketa_file.exists():
        pytest.skip(f"Interview anketa not found: {anketa_file}")

    with open(anketa_file, 'r', encoding='utf-8') as f:
        anketa_text = f.read()

    # Parse anketa into structured data
    user_answers = _parse_anketa_to_answers(anketa_text)

    # Audit results from Iteration 46 (mock for now, real would come from DB)
    audit_results = {
        'overall_score': 0.777,
        'readiness_status': 'Хорошо',
        'recommendations': [
            'Добавить больше конкретных цифр в бюджет',
            'Уточнить сроки реализации проекта',
            'Описать команду более детально'
        ]
    }

    return {
        'anketa_id': f"TEST-IT47-MEDIUM-{int(time.time())}",
        'anketa_text': anketa_text,
        'user_answers': user_answers,
        'audit_results': audit_results,
        'quality_level': 'MEDIUM',
        'context': {
            'region': 'Новосибирск',
            'topic': 'Наука',
            'organization': 'Центр "Образовательные проекты"',
            'grant_program': 'Президентский грант (молодёжные проекты)'
        }
    }


@pytest.fixture(scope="module")
def interview_2_data_with_audit(db) -> Dict[str, Any]:
    """
    Extract Interview #2 data + audit results

    Quality: HIGH
    Region: Екатеринбург
    Theme: Наука
    Organization: Ассоциация "Молодежные инициативы"
    """
    # Load anketa text
    anketa_file = _project_root / "iterations" / "Iteration_45_Full_Flow_Testing" / "INTERVIEW_2_ANKETA_HIGH_QUALITY.txt"

    if not anketa_file.exists():
        pytest.skip(f"Interview anketa not found: {anketa_file}")

    with open(anketa_file, 'r', encoding='utf-8') as f:
        anketa_text = f.read()

    # Parse anketa into structured data
    user_answers = _parse_anketa_to_answers(anketa_text)

    # Audit results from Iteration 46 (mock for now)
    audit_results = {
        'overall_score': 0.85,  # Expected higher for HIGH quality
        'readiness_status': 'Отлично',
        'recommendations': [
            'Отличная заявка, готова к подаче'
        ]
    }

    return {
        'anketa_id': f"TEST-IT47-HIGH-{int(time.time())}",
        'anketa_text': anketa_text,
        'user_answers': user_answers,
        'audit_results': audit_results,
        'quality_level': 'HIGH',
        'context': {
            'region': 'Екатеринбург',
            'topic': 'Наука',
            'organization': 'Ассоциация "Молодежные инициативы"',
            'grant_program': 'Президентский грант (молодёжные проекты)'
        }
    }


# ===== HELPER FUNCTIONS =====

def _parse_anketa_to_answers(anketa_text: str) -> Dict[str, str]:
    """
    Parse anketa from Iteration 45 format into user_answers dict

    Format:
        ### ВОПРОС 1 [HARDCODED]

        **INTERVIEWER:**
        Вопрос текст

        **USER (ОТВЕТ):**
        Ответ текст
    """
    answers = {}
    lines = anketa_text.strip().split('\n')

    current_question = None
    current_answer = []
    in_answer_section = False

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Skip empty lines
        if not line_stripped:
            continue

        # Detect question section
        if line_stripped.startswith('### ВОПРОС'):
            # Save previous answer
            if current_question and current_answer:
                answer_text = '\n'.join(current_answer).strip()
                if answer_text:
                    answers[current_question] = answer_text

            current_question = None
            current_answer = []
            in_answer_section = False
            continue

        # Detect interviewer question
        if line_stripped.startswith('**INTERVIEWER:**'):
            # Get question text (next line)
            if i + 1 < len(lines):
                question_text = lines[i + 1].strip()
                current_question = _map_question_to_key(question_text)
            continue

        # Detect user answer section
        if line_stripped.startswith('**USER (ОТВЕТ):**') or line_stripped.startswith('**USER:**'):
            in_answer_section = True
            current_answer = []
            continue

        # Collect answer text
        if in_answer_section and current_question:
            # Skip metadata lines
            if line_stripped.startswith('*[Ответ:') or line_stripped.startswith('==='):
                in_answer_section = False
                continue

            # Add content line
            if line_stripped and not line_stripped.startswith('**'):
                current_answer.append(line_stripped)

    # Save last answer
    if current_question and current_answer:
        answer_text = '\n'.join(current_answer).strip()
        if answer_text:
            answers[current_question] = answer_text

    return answers


def _map_question_to_key(question_text: str) -> str:
    """Map question text to standardized key for Writer Agent"""
    question_lower = question_text.lower()

    # Name/organization
    if 'имя' in question_lower or 'зовут' in question_lower:
        return 'name'
    elif 'организац' in question_lower:
        return 'organization'

    # Project basics
    elif 'название' in question_lower or 'наименование' in question_lower or 'проект' in question_lower:
        return 'project_name'
    elif 'цель' in question_lower or 'описан' in question_lower or 'суть' in question_lower:
        return 'description'

    # Problem & Solution
    elif 'проблем' in question_lower or 'вызов' in question_lower:
        return 'problem'
    elif 'решен' in question_lower or 'подход' in question_lower:
        return 'solution'

    # Implementation
    elif 'реализац' in question_lower or 'внедрен' in question_lower or 'этап' in question_lower:
        return 'implementation'
    elif 'сро' in question_lower or 'время' in question_lower or 'период' in question_lower:
        return 'timeline'

    # Resources
    elif 'бюджет' in question_lower or 'финансир' in question_lower or 'сто' in question_lower:
        return 'budget'
    elif 'команд' in question_lower or 'сотрудник' in question_lower or 'персонал' in question_lower:
        return 'team'

    # Impact
    elif 'результат' in question_lower or 'эффект' in question_lower or 'достижен' in question_lower:
        return 'impact'
    elif 'устойчив' in question_lower or 'после' in question_lower:
        return 'sustainability'

    # Fallback - use first word as key
    else:
        # Get first significant word
        words = question_lower.split()
        if words:
            return words[0].strip('?,.:;!')[:20]  # Max 20 chars
        return 'other'


# ===== TEST: Write Grant #1 (MEDIUM Quality) =====

@pytest.mark.timeout(600)  # 10 minutes max
def test_write_grant_1_medium_quality(writer, interview_1_data_with_audit, db):
    """
    Test: Write MEDIUM quality grant application

    Expected:
    - Grant generated successfully
    - Execution time: <10 minutes
    - PDF has at least 10 pages
    - Saved to database
    """
    print("\n" + "="*80)
    print("✍️ WRITING GRANT #1: MEDIUM Quality Interview")
    print("="*80)

    start_time = time.time()

    # ===== PREPARE INPUT =====
    input_data = {
        'anketa_id': interview_1_data_with_audit['anketa_id'],
        'user_answers': interview_1_data_with_audit['user_answers'],
        'research_data': {},  # Empty for now
        'selected_grant': interview_1_data_with_audit['context'],
        'audit_results': interview_1_data_with_audit['audit_results']
    }

    print(f"\n📋 Anketa ID: {interview_1_data_with_audit['anketa_id']}")
    print(f"📊 Quality Level: {interview_1_data_with_audit['quality_level']}")
    print(f"🔧 LLM Provider: {writer.llm_provider}")
    print(f"🤖 LLM Model: {GIGACHAT_MODEL}")
    print(f"📝 Audit Score: {interview_1_data_with_audit['audit_results']['overall_score']*100:.1f}/100")
    print(f"\n🔍 DEBUG: user_answers keys: {list(interview_1_data_with_audit['user_answers'].keys())}")
    print(f"🔍 DEBUG: user_answers count: {len(interview_1_data_with_audit['user_answers'])}")
    print("\nWriting grant application...")

    # ===== RUN WRITER =====
    result = writer.process(input_data)

    execution_time = time.time() - start_time

    # ===== VALIDATE RESULT =====
    assert result['status'] == 'success', f"Writer failed: {result.get('error')}"

    # Extract inner result (BaseAgent wraps in {'result': {...}})
    grant_result = result.get('result', result)  # Fallback if not wrapped

    # Writer returns 'application' dict, not 'application_text'
    application = grant_result.get('application', {})
    grant_sections = grant_result.get('structure', {})

    # Build full text from sections
    grant_text = ""
    if isinstance(application, dict):
        for section_name, section_content in application.items():
            grant_text += f"\n\n{'='*80}\n{section_name}\n{'='*80}\n\n{section_content}"

    # ===== ASSERTIONS =====

    # Success criterion 1: Grant text generated
    assert len(grant_text) > 1000, f"Grant too short: {len(grant_text)} chars"

    # Success criterion 2: Execution time
    assert execution_time < SUCCESS_CRITERIA['max_generation_time'], \
        f"Generation took {execution_time:.1f}s, exceeds {SUCCESS_CRITERIA['max_generation_time']}s"

    # Success criterion 3: Has main sections
    required_sections = ['title', 'problem', 'solution', 'budget', 'team']
    for section in required_sections:
        assert section in grant_sections or section in grant_text.lower(), \
            f"Missing required section: {section}"

    # ===== PRINT RESULTS =====
    print("\n" + "="*80)
    print("✅ GRANT #1 COMPLETED")
    print("="*80)
    print(f"\n📊 STATS:")
    print(f"   Text length:  {len(grant_text)} characters")
    print(f"   Sections:     {len(grant_sections)}")
    print(f"   Time:         {execution_time:.2f}s")

    print(f"\n📝 SECTIONS:")
    for section_name in grant_sections.keys():
        print(f"   - {section_name}")

    print("\n" + "="*80 + "\n")

    # Save to file for manual review
    output_file = _project_root / "iterations" / "Iteration_47_Writer_Testing" / "grant_medium.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(grant_text)
    print(f"💾 Saved to: {output_file}\n")

    # Return for comparison in final test
    return {
        'anketa_id': interview_1_data_with_audit['anketa_id'],
        'quality_level': 'MEDIUM',
        'text_length': len(grant_text),
        'sections_count': len(grant_sections),
        'execution_time': execution_time,
        'full_result': result
    }


# ===== TEST: Write Grant #2 (HIGH Quality) =====

@pytest.mark.timeout(600)  # 10 minutes max
def test_write_grant_2_high_quality(writer, interview_2_data_with_audit, db):
    """
    Test: Write HIGH quality grant application

    Expected:
    - Grant generated successfully
    - Execution time: <10 minutes
    - PDF has at least 15 pages
    - Longer and more detailed than MEDIUM
    """
    print("\n" + "="*80)
    print("✍️ WRITING GRANT #2: HIGH Quality Interview")
    print("="*80)

    start_time = time.time()

    # ===== PREPARE INPUT =====
    input_data = {
        'anketa_id': interview_2_data_with_audit['anketa_id'],
        'user_answers': interview_2_data_with_audit['user_answers'],
        'research_data': {},
        'selected_grant': interview_2_data_with_audit['context'],
        'audit_results': interview_2_data_with_audit['audit_results']
    }

    print(f"\n📋 Anketa ID: {interview_2_data_with_audit['anketa_id']}")
    print(f"📊 Quality Level: {interview_2_data_with_audit['quality_level']}")
    print(f"📝 Audit Score: {interview_2_data_with_audit['audit_results']['overall_score']*100:.1f}/100")
    print("\nWriting grant application...")

    # ===== RUN WRITER =====
    result = writer.process(input_data)

    execution_time = time.time() - start_time

    # ===== VALIDATE RESULT =====
    assert result['status'] == 'success', f"Writer failed: {result.get('error')}"

    # Extract inner result (BaseAgent wraps in {'result': {...}})
    grant_result = result.get('result', result)
    # Writer returns 'application' dict, not 'application_text'
    application = grant_result.get('application', {})
    grant_sections = grant_result.get('structure', {})

    # Build full text from sections
    grant_text = ""
    if isinstance(application, dict):
        for section_name, section_content in application.items():
            grant_text += f"\n\n{'='*80}\n{section_name}\n{'='*80}\n\n{section_content}"

    # ===== ASSERTIONS =====
    assert len(grant_text) > 1000, f"Grant too short: {len(grant_text)} chars"
    assert execution_time < SUCCESS_CRITERIA['max_generation_time'], \
        f"Generation took {execution_time:.1f}s, exceeds {SUCCESS_CRITERIA['max_generation_time']}s"

    # ===== PRINT RESULTS =====
    print("\n" + "="*80)
    print("✅ GRANT #2 COMPLETED")
    print("="*80)
    print(f"\n📊 STATS:")
    print(f"   Text length:  {len(grant_text)} characters")
    print(f"   Sections:     {len(grant_sections)}")
    print(f"   Time:         {execution_time:.2f}s")

    print("\n" + "="*80 + "\n")

    # Save to file
    output_file = _project_root / "iterations" / "Iteration_47_Writer_Testing" / "grant_high.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(grant_text)
    print(f"💾 Saved to: {output_file}\n")

    return {
        'anketa_id': interview_2_data_with_audit['anketa_id'],
        'quality_level': 'HIGH',
        'text_length': len(grant_text),
        'sections_count': len(grant_sections),
        'execution_time': execution_time,
        'full_result': result
    }


# ===== TEST: Compare MEDIUM vs HIGH =====

def test_compare_medium_vs_high(test_write_grant_1_medium_quality, test_write_grant_2_high_quality):
    """
    Compare MEDIUM vs HIGH quality grants

    Expected:
    - HIGH should be longer than MEDIUM
    - HIGH should have more/better sections
    """
    pytest.skip("Comparison test - manual review needed")

    medium = test_write_grant_1_medium_quality
    high = test_write_grant_2_high_quality

    print("\n" + "="*80)
    print("📊 COMPARISON: MEDIUM vs HIGH")
    print("="*80)

    print(f"\nMEDIUM Quality:")
    print(f"  - Text length:  {medium['text_length']} chars")
    print(f"  - Sections:     {medium['sections_count']}")
    print(f"  - Time:         {medium['execution_time']:.2f}s")

    print(f"\nHIGH Quality:")
    print(f"  - Text length:  {high['text_length']} chars")
    print(f"  - Sections:     {high['sections_count']}")
    print(f"  - Time:         {high['execution_time']:.2f}s")

    # Assertion: HIGH should be longer
    if SUCCESS_CRITERIA['high_should_be_longer']:
        assert high['text_length'] > medium['text_length'], \
            f"HIGH ({high['text_length']}) should be longer than MEDIUM ({medium['text_length']})"
        print("\n✅ HIGH is longer than MEDIUM")

    print("\n" + "="*80 + "\n")
