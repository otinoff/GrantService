#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from utils.postgres_helper import execute_query
import json

print("="*70)
print("CHECKING REAL ANKETAS IN DATABASE")
print("="*70)

# Get all sessions with anketa_id and answers
query = """
    SELECT
        id as session_id,
        telegram_id,
        anketa_id,
        project_name,
        status,
        current_stage,
        agents_passed,
        questions_answered,
        total_questions,
        answers_data,
        interview_data,
        started_at
    FROM sessions
    WHERE anketa_id IS NOT NULL
    ORDER BY started_at DESC
"""

results = execute_query(query)

print(f"\n[*] Found {len(results)} sessions with anketa_id\n")

real_anketas = []

for idx, row in enumerate(results, 1):
    session_id = row['session_id']
    anketa_id = row['anketa_id']
    project_name = row['project_name']
    status = row['status']
    current_stage = row['current_stage'] or 'interviewer'
    agents_passed = row['agents_passed'] or []
    answers_data = row['answers_data']
    interview_data = row['interview_data']

    # Determine if it's a real anketa (not test)
    is_test = 'TEST' in anketa_id.upper() or 'E2E' in anketa_id.upper()

    # Count answered questions
    answered_count = 0
    if answers_data:
        answered_count = len(answers_data) if isinstance(answers_data, dict) else 0
    elif interview_data:
        answered_count = len(interview_data) if isinstance(interview_data, dict) else 0

    marker = "[TEST]" if is_test else "[REAL]"

    print(f"{idx}. {marker} {anketa_id}")
    print(f"   Session: {session_id} | Stage: {current_stage} | Status: {status}")
    print(f"   Project: {project_name or 'N/A'}")
    print(f"   Answers: {answered_count} | Passed: {', '.join(agents_passed) if agents_passed else 'none'}")
    print(f"   Started: {row['started_at']}")

    if not is_test and answered_count > 0:
        real_anketas.append({
            'session_id': session_id,
            'anketa_id': anketa_id,
            'project_name': project_name,
            'answers_count': answered_count,
            'current_stage': current_stage,
            'agents_passed': agents_passed,
            'answers_data': answers_data,
            'interview_data': interview_data
        })

    print()

print("="*70)
print(f"SUMMARY: {len(real_anketas)} REAL ANKETAS READY FOR E2E PROCESSING")
print("="*70)

if real_anketas:
    print("\nREAL ANKETAS LIST:")
    for idx, anketa in enumerate(real_anketas, 1):
        print(f"  {idx}. {anketa['anketa_id']} - {anketa['project_name']} ({anketa['answers_count']} answers)")

print(f"\nTotal: {len(results)} sessions, {len(real_anketas)} real anketas, {len(results) - len(real_anketas)} test anketas")
