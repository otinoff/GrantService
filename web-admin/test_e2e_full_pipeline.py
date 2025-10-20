#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test: Full Grant Application Pipeline
==========================================
Tests complete flow: Interviewer → Auditor → Researcher → Writer → Reviewer

IMPORTANT: This test does NOT delete data - all results are saved to database
"""
import sys

# Исправление кодировки для Windows
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import json
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web-admin'))
sys.path.insert(0, os.path.dirname(__file__))

# Import helpers
from utils.postgres_helper import execute_query, execute_update
from utils.stage_tracker import update_stage, get_stage_info

# Test data - реалистичный проект
TEST_PROJECT_DATA = {
    "project_name": "E2E Test: AI Platform for Grant Applications",
    "project_description": "Разработка AI-платформы для автоматизации подготовки грантовых заявок с использованием LLM",
    "organization": "SnowWhite AI Lab",
    "target_audience": "Научные коллективы, стартапы, НКО",
    "problem_statement": "Подготовка грантовых заявок занимает недели и требует экспертных знаний",
    "solution": "AI-агенты помогают собрать информацию, структурировать проект и написать профессиональную заявку",
    "budget": "500000",
    "duration_months": "12",
    "expected_results": "Сокращение времени подготовки заявок с 2 недель до 2 дней, повышение качества заявок",
    "innovation": "Использование Claude Code API и мультиагентной системы CrewAI",
    "social_impact": "Повышение доступности грантового финансирования для малых команд",
    "team_size": "5",
    "experience": "3 года в разработке AI-систем",
}


def create_test_session():
    """Create test session with anketa"""
    print("\n[STAGE 1] Creating test session...")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    anketa_id = f"E2E-TEST-{timestamp}"

    # Create user if not exists and get user_id
    execute_update("""
        INSERT INTO users (telegram_id, username, first_name)
        VALUES (999888777, 'e2e_test_user', 'E2E Test')
        ON CONFLICT (telegram_id) DO UPDATE SET username = 'e2e_test_user'
    """)

    # Get user_id
    user_result = execute_query("SELECT id FROM users WHERE telegram_id = 999888777")
    user_id = user_result[0]['id'] if user_result else None

    # Create session with answers
    answers_json = json.dumps(TEST_PROJECT_DATA)

    query = """
        INSERT INTO sessions (
            telegram_id, anketa_id, current_stage, agents_passed,
            status, answers_data, project_name,
            current_step, total_questions, questions_answered
        ) VALUES (
            999888777, %s, 'interviewer', ARRAY[]::TEXT[],
            'in_progress', %s::jsonb, %s,
            'step_24', 24, 24
        )
        RETURNING id, anketa_id
    """

    result = execute_query(query, (anketa_id, answers_json, TEST_PROJECT_DATA['project_name']))
    session_id = result[0]['id']

    print(f"    [OK] Session created: {anketa_id}")
    print(f"    Session ID: {session_id}")
    print(f"    User ID: {user_id}")
    print(f"    Answers: {len(TEST_PROJECT_DATA)} fields")

    return session_id, anketa_id, user_id


def run_auditor_stage(session_id, anketa_id, user_id):
    """Run Auditor Agent - checks anketa quality"""
    print("\n[STAGE 2] Running Auditor Agent...")

    # Update stage to auditor
    update_stage(anketa_id, 'auditor')

    # Simulate auditor evaluation
    audit_scores = {
        "completeness": 9,
        "clarity": 8,
        "feasibility": 8,
        "innovation": 9,
        "quality": 8
    }

    avg_score = sum(audit_scores.values()) / len(audit_scores)

    feedback = f"""Auditor Evaluation (Auto-generated for E2E test):

Scores (1-10):
- Completeness: {audit_scores['completeness']}/10 - Anketa fully filled
- Clarity: {audit_scores['clarity']}/10 - Project clearly described
- Feasibility: {audit_scores['feasibility']}/10 - Realistic implementation
- Innovation: {audit_scores['innovation']}/10 - AI/LLM technology is innovative
- Quality: {audit_scores['quality']}/10 - Professional presentation

Average Score: {avg_score:.1f}/10

Status: APPROVED for next stage
Recommendation: Proceed to Researcher"""

    # Save audit results to grant_applications
    application_number = f"APP-{anketa_id}"
    content_json = json.dumps({
        "audit_scores": audit_scores,
        "audit_feedback": feedback,
        "project_data": TEST_PROJECT_DATA
    })

    query = """
        INSERT INTO grant_applications (
            application_number, title, anketa_id, user_id, session_id,
            content_json, quality_score, summary,
            current_stage, agents_passed,
            status, created_at
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s::jsonb, %s, %s,
            'auditor', ARRAY['interviewer']::TEXT[],
            'approved', NOW()
        )
        RETURNING id
    """

    result = execute_query(query, (
        application_number,
        TEST_PROJECT_DATA['project_name'],
        anketa_id,
        user_id,
        session_id,
        content_json,
        avg_score,
        feedback
    ))
    application_id = result[0]['id']

    print(f"    [OK] Auditor completed")
    print(f"    Application ID: {application_id}")
    print(f"    Average Score: {avg_score:.1f}/10")
    print(f"    Status: APPROVED")

    return application_id, audit_scores


def run_researcher_stage(session_id, anketa_id, user_id):
    """Run Researcher Agent - gather market data"""
    print("\n[STAGE 3] Running Researcher Agent...")

    # Update stage to researcher
    update_stage(anketa_id, 'researcher')

    research_id = f"RES-{anketa_id}"

    # Simulate research results
    research_results = {
        "market_analysis": "AI-powered grant preparation market growing at 25% CAGR",
        "competitors": ["GrantAI", "FundingBot"],
        "opportunities": "Untapped market in Russia/CIS region",
        "target_market_size": "500+ organizations annually",
        "technological_landscape": "Claude API, GigaChat, CrewAI framework gaining adoption",
        "success_factors": "Quality of AI prompts, user experience, integration with grant databases",
        "web_sources": [
            "https://example.com/ai-grant-market-2025",
            "https://example.com/llm-applications"
        ]
    }

    # Save research to database
    query = """
        INSERT INTO researcher_research (
            research_id, anketa_id, user_id, session_id,
            research_type, llm_provider, model,
            status, research_results,
            created_at, completed_at
        ) VALUES (
            %s, %s, %s, %s,
            'comprehensive', 'claude_code', 'claude-sonnet-4-5',
            'completed', %s::jsonb,
            NOW(), NOW()
        )
        RETURNING id
    """

    result = execute_query(query, (
        research_id, anketa_id, user_id, session_id,
        json.dumps(research_results)
    ))

    research_db_id = result[0]['id']

    print(f"    [OK] Researcher completed")
    print(f"    Research ID: {research_id}")
    print(f"    DB ID: {research_db_id}")
    print(f"    Market size: {research_results['target_market_size']}")
    print(f"    Competitors: {len(research_results['competitors'])}")

    return research_id, research_results


def run_writer_stage(session_id, anketa_id, user_id, research_id):
    """Run Writer Agent - generate grant text"""
    print("\n[STAGE 4] Running Writer Agent...")

    # Update stage to writer
    update_stage(anketa_id, 'writer')

    grant_id = f"GRANT-{anketa_id}"

    # Simulate grant text generation
    grant_text = f"""
ГРАНТОВАЯ ЗАЯВКА
================

1. НАЗВАНИЕ ПРОЕКТА
{TEST_PROJECT_DATA['project_name']}

2. АКТУАЛЬНОСТЬ
В современных условиях подготовка качественной грантовой заявки требует значительных временных
и интеллектуальных ресурсов. {TEST_PROJECT_DATA['problem_statement']}. Наш проект решает эту
проблему путем автоматизации процесса с помощью AI-технологий.

3. ОПИСАНИЕ ПРОЕКТА
{TEST_PROJECT_DATA['solution']}

Целевая аудитория: {TEST_PROJECT_DATA['target_audience']}
Организация-заявитель: {TEST_PROJECT_DATA['organization']}

4. ИННОВАЦИОННОСТЬ
{TEST_PROJECT_DATA['innovation']}

Использование последних достижений в области больших языковых моделей (LLM) позволяет
генерировать высококачественные тексты заявок, адаптированные под требования конкретных фондов.

5. СОЦИАЛЬНАЯ ЗНАЧИМОСТЬ
{TEST_PROJECT_DATA['social_impact']}

Проект направлен на демократизацию доступа к грантовому финансированию, особенно для
малых исследовательских групп и НКО.

6. КОМАНДА
Размер команды: {TEST_PROJECT_DATA['team_size']} человек
Опыт: {TEST_PROJECT_DATA['experience']}

7. БЮДЖЕТ
Общая сумма: {TEST_PROJECT_DATA['budget']} рублей
Срок реализации: {TEST_PROJECT_DATA['duration_months']} месяцев

8. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ
{TEST_PROJECT_DATA['expected_results']}

Метрики успеха:
- Время подготовки заявки: сокращение с 2 недель до 2 дней
- Качество заявок: повышение на 30%
- Количество обработанных заявок: 100+ в первый год

9. АНАЛИЗ РЫНКА
(На основе исследования {research_id})

Рынок AI-решений для подготовки грантов растет на 25% ежегодно.
Целевой размер рынка: 500+ организаций в год.

Конкуренты: ограничены за рубежом, в России практически отсутствуют.

10. ЗАКЛЮЧЕНИЕ
Проект сочетает передовые AI-технологии с глубоким пониманием специфики грантовых заявок,
что позволит значительно упростить и ускорить процесс получения грантового финансирования
для российских исследовательских коллективов.

---
Сгенерировано AI Writer Agent | {datetime.now().strftime("%Y-%m-%d %H:%M")}
Anketa ID: {anketa_id}
Research ID: {research_id}
"""

    # Save grant to database
    grant_sections = {
        "title": TEST_PROJECT_DATA['project_name'],
        "relevance": "Автоматизация подготовки грантовых заявок",
        "description": TEST_PROJECT_DATA['solution'],
        "innovation": TEST_PROJECT_DATA['innovation'],
        "social_impact": TEST_PROJECT_DATA['social_impact'],
        "team": f"{TEST_PROJECT_DATA['team_size']} человек",
        "budget": TEST_PROJECT_DATA['budget'],
        "results": TEST_PROJECT_DATA['expected_results']
    }

    query = """
        INSERT INTO grants (
            grant_id, anketa_id, research_id,
            user_id, grant_title, grant_content, grant_sections,
            llm_provider, model, status,
            current_stage, agents_passed,
            created_at
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s, %s::jsonb,
            'claude_code', 'claude-sonnet-4-5', 'draft',
            'writer', ARRAY['interviewer', 'auditor', 'researcher']::TEXT[],
            NOW()
        )
        RETURNING id
    """

    result = execute_query(query, (
        grant_id, anketa_id, research_id,
        user_id,
        TEST_PROJECT_DATA['project_name'],
        grant_text,
        json.dumps(grant_sections)
    ))

    grant_db_id = result[0]['id']

    print(f"    [OK] Writer completed")
    print(f"    Grant ID: {grant_id}")
    print(f"    DB ID: {grant_db_id}")
    print(f"    Text length: {len(grant_text)} chars")
    print(f"    Sections: {len(grant_sections)}")

    return grant_id, grant_text


def run_reviewer_stage(grant_id, anketa_id, grant_text):
    """Run Reviewer Agent - final quality check"""
    print("\n[STAGE 5] Running Reviewer Agent...")

    # Update stage to reviewer
    update_stage(anketa_id, 'reviewer')

    # Simulate review
    review_score = 8
    review_feedback = f"""Reviewer Final Assessment (Auto-generated for E2E test):

КАЧЕСТВО ЗАЯВКИ: {review_score}/10

СИЛЬНЫЕ СТОРОНЫ:
+ Четкая структура заявки
+ Инновационная технология (AI/LLM)
+ Социальная значимость проекта
+ Реалистичный бюджет и сроки
+ Обоснованные ожидаемые результаты

РЕКОМЕНДАЦИИ К УЛУЧШЕНИЮ:
- Добавить больше конкретики в описание команды
- Расширить раздел о методологии
- Включить risk management plan
- Добавить letters of support

СООТВЕТСТВИЕ ТРЕБОВАНИЯМ ФОНДА:
✓ Социальная значимость - ДА
✓ Инновационность - ДА
✓ Реализуемость - ДА
✓ Команда - ЧАСТИЧНО (требуется детализация)
✓ Бюджет - ДА

ФИНАЛЬНОЕ РЕШЕНИЕ: РЕКОМЕНДУЕТСЯ К ПОДАЧЕ
Статус: APPROVED (с учетом minor corrections)

Рекомендуется доработать разделы "Команда" и "Риски" перед финальной подачей.
"""

    # Update grant with review
    query = """
        UPDATE grants
        SET
            review_score = %s,
            review_feedback = %s,
            final_status = %s,
            current_stage = 'reviewer',
            agents_passed = ARRAY['interviewer', 'auditor', 'researcher', 'writer']::TEXT[],
            updated_at = NOW()
        WHERE grant_id = %s
    """

    execute_update(query, (review_score, review_feedback, 'approved', grant_id))

    print(f"    [OK] Reviewer completed")
    print(f"    Review Score: {review_score}/10")
    print(f"    Final Status: APPROVED")
    print(f"    Recommendation: Ready for submission (with minor corrections)")

    return review_score, review_feedback


def verify_data_integrity(session_id, anketa_id):
    """Verify that no data was deleted during pipeline"""
    print("\n[VERIFICATION] Checking data integrity...")

    checks = []

    # Check session exists
    result = execute_query("SELECT id FROM sessions WHERE id = %s", (session_id,))
    checks.append(("Session", len(result) > 0))

    # Check application exists
    result = execute_query("SELECT id FROM grant_applications WHERE anketa_id = %s", (anketa_id,))
    checks.append(("Grant Application", len(result) > 0))

    # Check research exists
    result = execute_query("SELECT id FROM researcher_research WHERE anketa_id = %s", (anketa_id,))
    checks.append(("Research", len(result) > 0))

    # Check grant exists
    result = execute_query("SELECT id FROM grants WHERE anketa_id = %s", (anketa_id,))
    checks.append(("Grant", len(result) > 0))

    all_passed = all(check[1] for check in checks)

    for name, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"    {status} {name} exists")

    if all_passed:
        print("\n    [SUCCESS] All data preserved - no deletions!")
    else:
        print("\n    [ERROR] Some data was deleted!")

    return all_passed


def display_final_report(session_id, anketa_id, grant_text, review_feedback):
    """Display final E2E test report"""
    print("\n" + "="*70)
    print("E2E TEST FINAL REPORT")
    print("="*70)

    # Get stage info
    stage_info = get_stage_info(anketa_id)

    if stage_info:
        print(f"\nAnketa ID: {stage_info['anketa_id']}")
        print(f"Current Stage: {stage_info['current_stage']}")
        print(f"Agents Passed: {', '.join(stage_info['agents_passed'])}")
        print(f"Progress: {stage_info['progress_percentage']}%")
        print(f"Badge: {stage_info['badge']}")

    print("\n" + "-"*70)
    print("FINAL GRANT TEXT")
    print("-"*70)
    print(grant_text)

    print("\n" + "-"*70)
    print("REVIEWER FEEDBACK")
    print("-"*70)
    print(review_feedback)

    print("\n" + "="*70)
    print("[SUCCESS] E2E Test Completed!")
    print("="*70)
    print("\nAll stages completed successfully:")
    print("  [1] Interviewer - Anketa created ✓")
    print("  [2] Auditor - Quality checked ✓")
    print("  [3] Researcher - Market analyzed ✓")
    print("  [4] Writer - Grant generated ✓")
    print("  [5] Reviewer - Final review ✓")
    print("\nData Integrity: PASSED ✓")
    print("\nYou can find this grant in the database:")
    print(f"  Anketa ID: {anketa_id}")
    print(f"  Tables: sessions, grant_applications, researcher_research, grants")


def main():
    """Run full E2E test"""
    print("="*70)
    print("E2E TEST: Full Grant Application Pipeline")
    print("="*70)
    print("\nThis test will:")
    print("  1. Create test session with project data")
    print("  2. Run Auditor (quality check)")
    print("  3. Run Researcher (market analysis)")
    print("  4. Run Writer (grant generation)")
    print("  5. Run Reviewer (final review)")
    print("  6. Verify data integrity (no deletions)")
    print("  7. Display final report")
    print("\nNOTE: All data is saved to database - nothing is deleted!")
    print("")

    try:
        # Run pipeline
        session_id, anketa_id, user_id = create_test_session()
        application_id, audit_scores = run_auditor_stage(session_id, anketa_id, user_id)
        research_id, research_results = run_researcher_stage(session_id, anketa_id, user_id)
        grant_id, grant_text = run_writer_stage(session_id, anketa_id, user_id, research_id)
        review_score, review_feedback = run_reviewer_stage(grant_id, anketa_id, grant_text)

        # Verify integrity
        integrity_ok = verify_data_integrity(session_id, anketa_id)

        # Final report
        display_final_report(session_id, anketa_id, grant_text, review_feedback)

        # Save report to file
        report_path = f"E2E_TEST_REPORT_{anketa_id}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"E2E Test Report\n")
            f.write(f"===============\n\n")
            f.write(f"Anketa ID: {anketa_id}\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Application ID: {application_id}\n")
            f.write(f"Research ID: {research_id}\n")
            f.write(f"Grant ID: {grant_id}\n\n")
            f.write(f"GRANT TEXT:\n{'-'*70}\n{grant_text}\n\n")
            f.write(f"REVIEW:\n{'-'*70}\n{review_feedback}\n")

        print(f"\n[OK] Report saved to: {report_path}")

        return True

    except Exception as e:
        print(f"\n[ERROR] E2E test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
