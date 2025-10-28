#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Generators for Interactive Pipeline - Iteration 52

Generates human-readable text files for each pipeline stage:
- Anketa summary (after interview)
- Audit results (after audit)
- Grant application (after generation)
- Review feedback (after review)

Author: Claude Code
Created: 2025-10-26
Version: 1.0.0
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional


def generate_anketa_txt(anketa_data: Dict[str, Any]) -> str:
    """
    Generate readable anketa summary as text file

    Args:
        anketa_data: Dictionary with anketa fields from sessions table
            Required keys: project_name, answers_data, completed_at

    Returns:
        Formatted text content for anketa file

    Example:
        anketa = {
            'anketa_id': 'ANK123',
            'project_name': 'Школа юных предпринимателей',
            'answers_data': {...},
            'completed_at': '2025-10-26 14:30:00'
        }
        txt = generate_anketa_txt(anketa)
    """

    # Header
    lines = [
        "=" * 60,
        "ЗАПОЛНЕННАЯ АНКЕТА",
        "=" * 60,
        ""
    ]

    # Metadata
    anketa_id = anketa_data.get('anketa_id', 'Unknown')
    completed_at = anketa_data.get('completed_at', datetime.now())
    if isinstance(completed_at, str):
        completed_at_str = completed_at
    else:
        completed_at_str = completed_at.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"ID анкеты: {anketa_id}")
    lines.append(f"Дата заполнения: {completed_at_str}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Project name
    project_name = anketa_data.get('project_name', 'Не указано')
    lines.append(f"НАЗВАНИЕ ПРОЕКТА: {project_name}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Answers - try both answers_data and interview_data (Iteration 52 compatibility)
    answers_data = anketa_data.get('answers_data', {})
    if isinstance(answers_data, str):
        try:
            answers_data = json.loads(answers_data)
        except:
            answers_data = {}

    # ITERATION 53 FIX: If answers_data is empty/None/not-dict, try interview_data
    if not answers_data or not isinstance(answers_data, dict):
        answers_data = anketa_data.get('interview_data', {})
        if isinstance(answers_data, str):
            try:
                answers_data = json.loads(answers_data)
            except:
                answers_data = {}
        # If interview_data is also not a dict, use empty dict
        if not isinstance(answers_data, dict):
            answers_data = {}

    lines.append("ОТВЕТЫ НА ВОПРОСЫ:")
    lines.append("")

    # Common questions mapping
    question_labels = {
        'organization': 'Организация',
        'project_description': 'Описание проекта',
        'problem': 'Проблема',
        'problem_description': 'Описание проблемы',
        'solution': 'Решение',
        'target_audience': 'Целевая аудитория',
        'expected_results': 'Ожидаемые результаты',
        'budget': 'Бюджет',
        'budget_total': 'Общий бюджет',
        'budget_breakdown': 'Структура бюджета',
        'duration': 'Срок реализации',
        'team': 'Команда проекта',
        'team_description': 'Описание команды',
        'partners': 'Партнеры',
        'project_goal': 'Цель проекта',
        'methodology': 'Методология',
        'risks': 'Риски',
        'sustainability': 'Устойчивость',
    }

    # ITERATION 53 FIX: Check if answers_data is dict before calling .items()
    if isinstance(answers_data, dict):
        for key, value in answers_data.items():
            if value:
                label = question_labels.get(key, key.replace('_', ' ').capitalize())
                lines.append(f"{label}:")
                lines.append(f"  {value}")
                lines.append("")

    # Footer
    lines.append("")
    lines.append("=" * 60)
    # ITERATION 53 FIX: Check answers_data is dict before calling len()
    question_count = len(answers_data) if isinstance(answers_data, dict) else 0
    lines.append(f"Всего вопросов: {question_count}")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_audit_txt(audit_data: Dict[str, Any]) -> str:
    """
    Generate audit results as text file

    Args:
        audit_data: Dictionary with audit results from auditor_results table
            Required keys: average_score, approval_status, recommendations

    Returns:
        Formatted text content for audit file

    Example:
        audit = {
            'id': 123,
            'completeness_score': 8,
            'clarity_score': 7,
            'feasibility_score': 9,
            'innovation_score': 6,
            'quality_score': 8,
            'average_score': 7.6,
            'approval_status': 'approved',
            'recommendations': {...},
            'created_at': '2025-10-26 14:35:00'
        }
        txt = generate_audit_txt(audit)
    """

    # Header
    lines = [
        "=" * 60,
        "РЕЗУЛЬТАТЫ АУДИТА АНКЕТЫ",
        "=" * 60,
        ""
    ]

    # Metadata
    audit_id = audit_data.get('id', 'Unknown')
    created_at = audit_data.get('created_at', datetime.now())
    if isinstance(created_at, str):
        created_at_str = created_at
    else:
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"ID аудита: {audit_id}")
    lines.append(f"Дата аудита: {created_at_str}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Overall score
    average_score = audit_data.get('average_score', 0)
    approval_status = audit_data.get('approval_status', 'pending')

    status_labels = {
        'approved': '✅ ОДОБРЕНО',
        'needs_revision': '⚠️ ТРЕБУЕТСЯ ДОРАБОТКА',
        'rejected': '❌ ОТКЛОНЕНО',
        'pending': '⏳ ОЖИДАЕТ ПРОВЕРКИ'
    }

    lines.append(f"ОБЩАЯ ОЦЕНКА: {average_score}/10")
    lines.append(f"СТАТУС: {status_labels.get(approval_status, approval_status.upper())}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Detailed scores
    lines.append("ДЕТАЛЬНЫЕ ОЦЕНКИ:")
    lines.append("")

    score_fields = {
        'completeness_score': 'Полнота информации',
        'clarity_score': 'Ясность изложения',
        'feasibility_score': 'Реалистичность',
        'innovation_score': 'Инновационность',
        'quality_score': 'Качество'
    }

    for field, label in score_fields.items():
        score = audit_data.get(field, 0)
        score_int = round(score)  # Convert float to int for string multiplication
        bar = '█' * score_int + '░' * (10 - score_int)
        lines.append(f"{label}: {bar} {score:.1f}/10")

    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Recommendations (handle multiple formats)
    recommendations = audit_data.get('recommendations', {})

    # Handle string (JSON)
    if isinstance(recommendations, str):
        try:
            recommendations = json.loads(recommendations)
        except:
            recommendations = {}

    # Handle list (from Agent: ['problem1', 'problem2'])
    elif isinstance(recommendations, list):
        recommendations = {
            'problems': recommendations,
            'suggestions': []
        }

    # Handle invalid types
    elif not isinstance(recommendations, dict):
        recommendations = {}

    if recommendations:
        lines.append("РЕКОМЕНДАЦИИ:")
        lines.append("")

        # Problems
        problems = recommendations.get('problems', [])
        if problems:
            lines.append("ПРОБЛЕМЫ:")
            for i, problem in enumerate(problems, 1):
                lines.append(f"  {i}. {problem}")
            lines.append("")

        # Suggestions
        suggestions = recommendations.get('suggestions', [])
        if suggestions:
            lines.append("ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:")
            for i, suggestion in enumerate(suggestions, 1):
                lines.append(f"  {i}. {suggestion}")
            lines.append("")

    # Footer
    lines.append("=" * 60)
    lines.append(f"Аудит выполнен: {audit_data.get('auditor_llm_provider', 'Unknown')}")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_grant_txt(grant_data: Dict[str, Any]) -> str:
    """
    Generate full grant application as text file

    Args:
        grant_data: Dictionary with grant from grants table
            Required keys: grant_title, grant_content, grant_sections

    Returns:
        Formatted text content for grant file

    Example:
        grant = {
            'id': 456,
            'grant_id': 'GNT456',
            'grant_title': 'Школа юных предпринимателей',
            'grant_content': '...',
            'grant_sections': {...},
            'created_at': '2025-10-26 14:40:00'
        }
        txt = generate_grant_txt(grant)
    """

    # Header
    lines = [
        "=" * 60,
        "ГРАНТОВАЯ ЗАЯВКА",
        "=" * 60,
        ""
    ]

    # Metadata
    grant_id = grant_data.get('grant_id', 'Unknown')
    created_at = grant_data.get('created_at', datetime.now())
    if isinstance(created_at, str):
        created_at_str = created_at
    else:
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"ID заявки: {grant_id}")
    lines.append(f"Дата создания: {created_at_str}")
    lines.append("")

    # Title
    grant_title = grant_data.get('grant_title', 'Без названия')
    lines.append(f"НАЗВАНИЕ: {grant_title}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Sections
    grant_sections = grant_data.get('grant_sections', {})
    if isinstance(grant_sections, str):
        try:
            grant_sections = json.loads(grant_sections)
        except:
            grant_sections = {}

    section_labels = {
        'problem': 'ПРОБЛЕМА',
        'solution': 'РЕШЕНИЕ',
        'methodology': 'МЕТОДОЛОГИЯ',
        'implementation': 'ПЛАН РЕАЛИЗАЦИИ',
        'budget': 'БЮДЖЕТ',
        'timeline': 'ВРЕМЕННЫЕ РАМКИ',
        'team': 'КОМАНДА ПРОЕКТА',
        'impact': 'ОЖИДАЕМЫЙ ЭФФЕКТ',
        'sustainability': 'УСТОЙЧИВОСТЬ',
        'summary': 'КРАТКОЕ ОПИСАНИЕ'
    }

    if grant_sections:
        for key, label in section_labels.items():
            if key in grant_sections:
                lines.append(f"=== {label} ===")
                lines.append("")
                lines.append(grant_sections[key])
                lines.append("")
                lines.append("-" * 60)
                lines.append("")
    else:
        # Fallback: use full content if sections not available
        grant_content = grant_data.get('grant_content', '')
        if grant_content:
            lines.append("СОДЕРЖАНИЕ ЗАЯВКИ:")
            lines.append("")
            lines.append(grant_content)
            lines.append("")

    # Footer
    content_length = len(grant_data.get('grant_content', ''))
    lines.append("=" * 60)
    lines.append(f"Всего символов: {content_length}")
    lines.append(f"Модель: {grant_data.get('llm_provider', 'Unknown')}")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_research_txt(research_data: Dict[str, Any]) -> str:
    """
    Generate research results as text file

    Args:
        research_data: Dictionary with research results from researcher_research table
            Required keys: research_id, anketa_id, research_results, created_at

    Returns:
        Formatted text content for research file

    Example:
        research = {
            'research_id': '#AN-20251028-user-001-RS-001',
            'anketa_id': '#AN-20251028-user-001',
            'research_results': {
                'results': {
                    'block1': {
                        'queries': [...]
                    },
                    'metadata': {
                        'sources_count': 3,
                        'total_queries': 3
                    }
                }
            },
            'created_at': '2025-10-28 23:00:00'
        }
        txt = generate_research_txt(research)
    """

    # Header
    lines = [
        "=" * 60,
        "РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ",
        "=" * 60,
        ""
    ]

    # Metadata
    research_id = research_data.get('research_id', 'Unknown')
    anketa_id = research_data.get('anketa_id', 'Unknown')
    created_at = research_data.get('created_at', datetime.now())
    if isinstance(created_at, str):
        created_at_str = created_at
    else:
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"ID исследования: {research_id}")
    lines.append(f"ID анкеты: {anketa_id}")
    lines.append(f"Дата исследования: {created_at_str}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Parse research results (handle nested structure from Iteration 60)
    research_results = research_data.get('research_results', {})
    if isinstance(research_results, str):
        try:
            research_results = json.loads(research_results)
        except:
            research_results = {}

    # Extract results and metadata
    results = research_results.get('results', {})
    metadata = results.get('metadata', {})

    sources_count = metadata.get('sources_count', 0)
    total_queries = metadata.get('total_queries', 0)

    # Statistics section
    lines.append("СТАТИСТИКА:")
    lines.append("")
    lines.append(f"📊 Найдено источников: {sources_count}")
    lines.append(f"📄 Выполнено запросов: {total_queries}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Block 1 results (queries and answers)
    block1 = results.get('block1', {})
    queries = block1.get('queries', [])

    if queries:
        lines.append("РЕЗУЛЬТАТЫ ПОИСКА:")
        lines.append("")

        for i, query_data in enumerate(queries, 1):
            query_text = query_data.get('query', 'N/A')
            answer = query_data.get('answer', 'N/A')
            sources = query_data.get('sources', [])

            lines.append(f"=== ЗАПРОС {i} ===")
            lines.append("")
            lines.append(f"Вопрос: {query_text}")
            lines.append("")
            lines.append("Ответ:")
            lines.append(answer)
            lines.append("")

            if sources:
                lines.append("Источники:")
                for source in sources:
                    lines.append(f"  • {source}")
                lines.append("")

            lines.append("-" * 60)
            lines.append("")
    else:
        lines.append("⚠️ Результаты поиска недоступны")
        lines.append("")

    # Footer
    llm_provider = research_data.get('llm_provider', 'Unknown')
    lines.append("=" * 60)
    lines.append(f"Исследование выполнено: {llm_provider}")
    lines.append(f"Всего запросов: {total_queries}")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_review_txt(review_data: Dict[str, Any]) -> str:
    """
    Generate review results as text file

    Args:
        review_data: Dictionary with review from grants table
            Required keys: review_score, review_feedback, final_status

    Returns:
        Formatted text content for review file

    Example:
        review = {
            'id': 456,
            'grant_id': 'GNT456',
            'review_score': 8,
            'review_feedback': '...',
            'final_status': 'approved',
            'updated_at': '2025-10-26 14:45:00'
        }
        txt = generate_review_txt(review)
    """

    # Header
    lines = [
        "=" * 60,
        "РЕЗУЛЬТАТЫ РЕВЬЮ ГРАНТОВОЙ ЗАЯВКИ",
        "=" * 60,
        ""
    ]

    # Metadata
    grant_id = review_data.get('grant_id', 'Unknown')
    updated_at = review_data.get('updated_at', datetime.now())
    if isinstance(updated_at, str):
        updated_at_str = updated_at
    else:
        updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"ID заявки: {grant_id}")
    lines.append(f"Дата ревью: {updated_at_str}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Overall score
    review_score = review_data.get('review_score', 0)
    final_status = review_data.get('final_status', 'pending')

    status_labels = {
        'approved': '✅ ОДОБРЕНО',
        'needs_revision': '⚠️ ТРЕБУЕТСЯ ДОРАБОТКА',
        'rejected': '❌ ОТКЛОНЕНО',
        'pending': '⏳ ОЖИДАЕТ ПРОВЕРКИ'
    }

    lines.append(f"ОБЩАЯ ОЦЕНКА: {review_score}/10")
    lines.append(f"СТАТУС: {status_labels.get(final_status, final_status.upper())}")
    lines.append("")

    # Visual score bar
    bar = '█' * int(review_score) + '░' * (10 - int(review_score))  # Iteration_58: Convert float to int
    lines.append(f"Качество: {bar} {review_score}/10")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # Iteration_58: Get strengths/weaknesses/recommendations directly from review_data
    # (Reviewer returns these as lists, not as JSON string)
    strengths = review_data.get('strengths', [])
    weaknesses = review_data.get('weaknesses', [])
    recommendations = review_data.get('recommendations', [])

    # Display strengths
    if strengths and isinstance(strengths, list) and len(strengths) > 0:
        lines.append("СИЛЬНЫЕ СТОРОНЫ:")
        for i, strength in enumerate(strengths, 1):
            lines.append(f"  {i}. {strength}")
        lines.append("")

    # Display weaknesses
    if weaknesses and isinstance(weaknesses, list) and len(weaknesses) > 0:
        lines.append("СЛАБЫЕ СТОРОНЫ:")
        for i, weakness in enumerate(weaknesses, 1):
            lines.append(f"  {i}. {weakness}")
        lines.append("")

    # Display recommendations
    if recommendations and isinstance(recommendations, list) and len(recommendations) > 0:
        lines.append("РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

    # Legacy: Also check for review_feedback (for backward compatibility)
    review_feedback = review_data.get('review_feedback', '')
    if review_feedback and isinstance(review_feedback, str):
        lines.append("ДЕТАЛЬНОЕ РЕВЬЮ:")
        lines.append("")
        lines.append(review_feedback)
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

    # Footer
    lines.append("=" * 60)
    lines.append("Ревью завершено")
    lines.append("=" * 60)

    return "\n".join(lines)


# Helper function for testing
def save_to_file(content: str, filename: str) -> str:
    """
    Helper to save generated content to file

    Args:
        content: Text content to save
        filename: Output filename

    Returns:
        Path to saved file
    """
    import os
    import tempfile

    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.txt',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(content)
        file_path = f.name

    return file_path
