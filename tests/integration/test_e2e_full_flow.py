#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: End-to-End Full Flow (Iteration 50)
Based on: Iteration 46 (Audit) + Iteration 47 (Writer)

ПОЛНЫЙ ЦИКЛ:
1. Anketas (из Iteration 45) → копируем в Iteration 50 папку
2. AuditorAgent → AUDIT_1_MEDIUM.txt + AUDIT_2_HIGH.txt
3. WriterAgent → GRANT_1_MEDIUM.txt + GRANT_2_HIGH.txt

Результат: 6 файлов в iterations/Iteration_50_E2E_Full_Flow/
"""
import sys
from pathlib import Path

# Project root setup
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

import pytest
import time
import shutil
import json
from typing import Dict, Any

# ===== IMPORTS =====
from agents.auditor_agent import AuditorAgent
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

ITERATION_45_PATH = _project_root / "iterations" / "Iteration_45_Full_Flow_Testing"
ITERATION_50_PATH = _project_root / "iterations" / "Iteration_50_E2E_Full_Flow"

# Анкеты из Iteration 45
ANKETA_FILES = {
    'medium': "INTERVIEW_1_ANKETA_MEDIUM_QUALITY.txt",
    'high': "INTERVIEW_2_ANKETA_HIGH_QUALITY.txt"
}

# Success Criteria
SUCCESS_CRITERIA = {
    'total_files': 6,  # 2 anketas + 2 audits + 2 grants
    'max_phase_time': 600,  # 10 minutes per phase
}


# ===== PYTEST MARKERS =====

pytestmark = [
    pytest.mark.integration,  # Needs database
    pytest.mark.gigachat,     # Needs real GigaChat API
    pytest.mark.slow,         # Takes time (~20-30 minutes)
    pytest.mark.e2e,          # End-to-end full system test
]


# ===== FIXTURES =====

@pytest.fixture(scope="module")
def db():
    """Real PostgreSQL database connection"""
    if DatabaseManager is None:
        pytest.skip("DatabaseManager not available")
    yield DatabaseManager


@pytest.fixture(scope="module")
def output_dir():
    """Create output directory for Iteration 50"""
    ITERATION_50_PATH.mkdir(parents=True, exist_ok=True)
    return ITERATION_50_PATH


@pytest.fixture(scope="module")
def auditor(db):
    """AuditorAgent with GigaChat"""
    return AuditorAgent(db=db, llm_provider="gigachat")


@pytest.fixture(scope="module")
def writer(db):
    """WriterAgent with GigaChat Pro"""
    from shared.llm.unified_llm_client import UnifiedLLMClient
    agent = WriterAgent(db=db, llm_provider="gigachat")

    # Override to use GigaChat-Pro
    agent.llm_client = UnifiedLLMClient(provider="gigachat", model="GigaChat-Pro")

    return agent


# ===== HELPER FUNCTIONS =====

def _parse_anketa_to_answers(anketa_text: str) -> Dict[str, str]:
    """
    Parse anketa from Iteration 45 format into user_answers dict

    (Copied from test_write_two_grants.py - proven logic)
    """
    answers = {}
    lines = anketa_text.strip().split('\n')

    current_question = None
    current_answer = []
    in_answer_section = False

    for i, line in enumerate(lines):
        line_stripped = line.strip()

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
            if line_stripped.startswith('*[Ответ:') or line_stripped.startswith('==='):
                in_answer_section = False
                continue

            if line_stripped and not line_stripped.startswith('**'):
                current_answer.append(line_stripped)

    # Save last answer
    if current_question and current_answer:
        answer_text = '\n'.join(current_answer).strip()
        if answer_text:
            answers[current_question] = answer_text

    return answers


def _map_question_to_key(question_text: str) -> str:
    """Map question text to standardized key (from test_write_two_grants.py)"""
    question_lower = question_text.lower()

    if 'имя' in question_lower or 'зовут' in question_lower:
        return 'name'
    elif 'организац' in question_lower:
        return 'organization'
    elif 'название' in question_lower or 'проект' in question_lower:
        return 'project_name'
    elif 'цель' in question_lower or 'описан' in question_lower:
        return 'description'
    elif 'проблем' in question_lower:
        return 'problem'
    elif 'решен' in question_lower:
        return 'solution'
    elif 'реализац' in question_lower or 'внедрен' in question_lower:
        return 'implementation'
    elif 'сро' in question_lower or 'время' in question_lower:
        return 'timeline'
    elif 'бюджет' in question_lower or 'финансир' in question_lower:
        return 'budget'
    elif 'команд' in question_lower or 'сотрудник' in question_lower:
        return 'team'
    elif 'результат' in question_lower or 'эффект' in question_lower:
        return 'impact'
    elif 'устойчив' in question_lower:
        return 'sustainability'
    else:
        words = question_lower.split()
        if words:
            return words[0].strip('?,.:;!')[:20]
        return 'other'


# ===== PHASE 0: COPY ANKETAS =====

def test_phase_0_copy_anketas(output_dir):
    """
    Phase 0: Copy anketas from Iteration 45 to Iteration 50

    Creates:
    - ANKETA_1_MEDIUM.txt
    - ANKETA_2_HIGH.txt
    """
    print("\n" + "="*80)
    print("PHASE 0: Копируем анкеты из Iteration 45")
    print("="*80)

    # Copy MEDIUM anketa
    src_medium = ITERATION_45_PATH / ANKETA_FILES['medium']
    dst_medium = output_dir / "ANKETA_1_MEDIUM.txt"

    assert src_medium.exists(), f"Source MEDIUM anketa not found: {src_medium}"
    shutil.copy2(src_medium, dst_medium)
    print(f"✅ Copied: {dst_medium.name}")

    # Copy HIGH anketa
    src_high = ITERATION_45_PATH / ANKETA_FILES['high']
    dst_high = output_dir / "ANKETA_2_HIGH.txt"

    assert src_high.exists(), f"Source HIGH anketa not found: {src_high}"
    shutil.copy2(src_high, dst_high)
    print(f"✅ Copied: {dst_high.name}")

    # Verify
    assert dst_medium.exists()
    assert dst_high.exists()

    print(f"\n✅ Phase 0 COMPLETED: 2 anketas copied")
    print("="*80 + "\n")


# ===== PHASE 1: AUDIT =====

@pytest.mark.timeout(600)  # 10 minutes max
def test_phase_1_audit_two_anketas(auditor, output_dir):
    """
    Phase 1: Run AuditorAgent on 2 anketas

    Creates:
    - AUDIT_1_MEDIUM.txt
    - AUDIT_2_HIGH.txt
    """
    print("\n" + "="*80)
    print("PHASE 1: Запускаем AuditorAgent")
    print("="*80)

    start_time = time.time()

    # AUDIT #1 (MEDIUM)
    print("\n📋 Auditing Interview #1 (MEDIUM quality)...")

    anketa_medium_file = output_dir / "ANKETA_1_MEDIUM.txt"
    with open(anketa_medium_file, 'r', encoding='utf-8') as f:
        anketa_medium_text = f.read()

    user_answers_medium = _parse_anketa_to_answers(anketa_medium_text)

    # Run auditor (from test_audit_two_anketas.py logic)
    audit_result_medium = auditor.process({
        'user_answers': user_answers_medium
    })

    # Save audit to file
    audit_medium_file = output_dir / "AUDIT_1_MEDIUM.txt"
    with open(audit_medium_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("АУДИТ ГРАНТОВОЙ ЗАЯВКИ #1 (MEDIUM QUALITY)\n")
        f.write("="*80 + "\n\n")
        f.write(f"Итоговая оценка: {audit_result_medium.get('final_score', 'N/A')}/100\n")
        f.write(f"Статус готовности: {audit_result_medium.get('readiness_status', 'N/A')}\n\n")

        # Criteria scores
        criteria_scores = audit_result_medium.get('criteria_scores', {})
        f.write("Оценки по критериям:\n")
        for criterion, score in criteria_scores.items():
            f.write(f"  - {criterion}: {score}/10\n")

        f.write("\nРекомендации:\n")
        recommendations = audit_result_medium.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            f.write(f"  {i}. {rec}\n")

    print(f"✅ AUDIT_1_MEDIUM.txt created")

    # AUDIT #2 (HIGH)
    print("\n📋 Auditing Interview #2 (HIGH quality)...")

    anketa_high_file = output_dir / "ANKETA_2_HIGH.txt"
    with open(anketa_high_file, 'r', encoding='utf-8') as f:
        anketa_high_text = f.read()

    user_answers_high = _parse_anketa_to_answers(anketa_high_text)

    audit_result_high = auditor.process({
        'user_answers': user_answers_high
    })

    # Save audit to file
    audit_high_file = output_dir / "AUDIT_2_HIGH.txt"
    with open(audit_high_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("АУДИТ ГРАНТОВОЙ ЗАЯВКИ #2 (HIGH QUALITY)\n")
        f.write("="*80 + "\n\n")
        f.write(f"Итоговая оценка: {audit_result_high.get('final_score', 'N/A')}/100\n")
        f.write(f"Статус готовности: {audit_result_high.get('readiness_status', 'N/A')}\n\n")

        criteria_scores = audit_result_high.get('criteria_scores', {})
        f.write("Оценки по критериям:\n")
        for criterion, score in criteria_scores.items():
            f.write(f"  - {criterion}: {score}/10\n")

        f.write("\nРекомендации:\n")
        recommendations = audit_result_high.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            f.write(f"  {i}. {rec}\n")

    print(f"✅ AUDIT_2_HIGH.txt created")

    phase_time = time.time() - start_time

    print(f"\n✅ Phase 1 COMPLETED: 2 audits done in {phase_time:.1f}s")
    print("="*80 + "\n")

    assert audit_medium_file.exists()
    assert audit_high_file.exists()


# ===== PHASE 2: WRITE GRANTS =====

@pytest.mark.timeout(1200)  # 20 minutes max (2 grants × 10 min each)
def test_phase_2_write_two_grants(writer, output_dir):
    """
    Phase 2: Run WriterAgent on 2 anketas

    Creates:
    - GRANT_1_MEDIUM.txt
    - GRANT_2_HIGH.txt
    """
    print("\n" + "="*80)
    print("PHASE 2: Запускаем WriterAgent")
    print("="*80)

    start_time = time.time()

    # GRANT #1 (MEDIUM)
    print("\n✍️ Writing Grant #1 (MEDIUM quality)...")

    anketa_medium_file = output_dir / "ANKETA_1_MEDIUM.txt"
    with open(anketa_medium_file, 'r', encoding='utf-8') as f:
        anketa_medium_text = f.read()

    user_answers_medium = _parse_anketa_to_answers(anketa_medium_text)

    # Run writer (from test_write_two_grants.py logic)
    grant_result_medium = writer.process({
        'anketa_id': "IT50-MEDIUM",
        'user_answers': user_answers_medium,
        'research_data': {},
        'selected_grant': {'grant_program': 'Президентский грант'},
        'audit_results': {}
    })

    # Extract application_number from result
    application_number_medium = grant_result_medium.get('application_number')
    print(f"📋 Grant application created: {application_number_medium}")

    # Extract application content from result (NOT from database)
    application_medium = grant_result_medium.get('application', {})

    # Format grant text
    grant_text_medium = ""
    for section_name, section_content in application_medium.items():
        grant_text_medium += f"\n\n{'='*80}\n{section_name}\n{'='*80}\n\n{section_content}"

    # Save to file
    grant_medium_file = output_dir / "GRANT_1_MEDIUM.txt"
    with open(grant_medium_file, 'w', encoding='utf-8') as f:
        f.write(grant_text_medium)

    print(f"✅ GRANT_1_MEDIUM.txt created ({len(grant_text_medium)} chars)")

    # GRANT #2 (HIGH)
    print("\n✍️ Writing Grant #2 (HIGH quality)...")

    anketa_high_file = output_dir / "ANKETA_2_HIGH.txt"
    with open(anketa_high_file, 'r', encoding='utf-8') as f:
        anketa_high_text = f.read()

    user_answers_high = _parse_anketa_to_answers(anketa_high_text)

    grant_result_high = writer.process({
        'anketa_id': "IT50-HIGH",
        'user_answers': user_answers_high,
        'research_data': {},
        'selected_grant': {'grant_program': 'Президентский грант'},
        'audit_results': {}
    })

    # Extract application_number from result
    application_number_high = grant_result_high.get('application_number')
    print(f"📋 Grant application created: {application_number_high}")

    # Extract application content from result (NOT from database)
    application_high = grant_result_high.get('application', {})

    # Format grant text
    grant_text_high = ""
    for section_name, section_content in application_high.items():
        grant_text_high += f"\n\n{'='*80}\n{section_name}\n{'='*80}\n\n{section_content}"

    # Save to file
    grant_high_file = output_dir / "GRANT_2_HIGH.txt"
    with open(grant_high_file, 'w', encoding='utf-8') as f:
        f.write(grant_text_high)

    print(f"✅ GRANT_2_HIGH.txt created ({len(grant_text_high)} chars)")

    phase_time = time.time() - start_time

    print(f"\n✅ Phase 2 COMPLETED: 2 grants written in {phase_time:.1f}s")
    print("="*80 + "\n")

    assert grant_medium_file.exists()
    assert grant_high_file.exists()
    assert len(grant_text_medium) > 1000
    assert len(grant_text_high) > 1000


# ===== FINAL VALIDATION =====

def test_final_validation(output_dir):
    """
    Final: Verify all 6 files exist
    """
    print("\n" + "="*80)
    print("FINAL VALIDATION: Checking 6 files")
    print("="*80)

    expected_files = [
        "ANKETA_1_MEDIUM.txt",
        "ANKETA_2_HIGH.txt",
        "AUDIT_1_MEDIUM.txt",
        "AUDIT_2_HIGH.txt",
        "GRANT_1_MEDIUM.txt",
        "GRANT_2_HIGH.txt"
    ]

    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"Missing file: {filename}"
        size = file_path.stat().st_size
        print(f"✅ {filename} ({size:,} bytes)")

    print(f"\n✅ ALL 6 FILES CREATED")
    print(f"📁 Location: {output_dir}")
    print("="*80 + "\n")


# ===== MAIN =====

if __name__ == "__main__":
    """Run E2E test directly"""
    pytest.main([__file__, "-xvs", "--tb=short"])
