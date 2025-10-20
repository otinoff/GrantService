#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grant Lifecycle Test Fixtures
=============================
Reusable fixtures for lifecycle manager tests

Provides:
- Sample anketa_id values
- Mock lifecycle_data with all stages
- Mock artifacts for each stage
- Mock metadata
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any


# ========== SAMPLE ANKETA IDS ==========

@pytest.fixture
def sample_anketa_id():
    """Sample valid anketa_id"""
    return "AN-20250905-testuser-001"


@pytest.fixture
def real_anketa_id():
    """Real anketa_id from database (known to exist)"""
    return "AN-20250905-Natalia_bruzzzz-001"


@pytest.fixture
def invalid_anketa_id():
    """Invalid anketa_id for testing error cases"""
    return "INVALID-ANKETA-ID"


# ========== MOCK METADATA ==========

@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        'telegram_id': 123456789,
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'session_id': 1001,
        'session_started': datetime(2025, 9, 5, 10, 0, 0),
        'session_updated': datetime(2025, 9, 5, 15, 30, 0)
    }


@pytest.fixture
def empty_metadata():
    """Empty metadata for edge case testing"""
    return {}


# ========== MOCK INTERVIEW ARTIFACTS ==========

@pytest.fixture
def interview_artifact_completed():
    """Completed interview artifact"""
    return {
        'status': 'completed',
        'questions_count': 24,
        'completed_at': datetime(2025, 9, 5, 11, 0, 0),
        'data': [
            {
                'question_id': 1,
                'question_text': 'Название вашего проекта?',
                'answer': 'Инновационный проект по развитию образования',
                'created_at': datetime(2025, 9, 5, 10, 10, 0)
            },
            {
                'question_id': 2,
                'question_text': 'Краткое описание проекта?',
                'answer': 'Проект направлен на создание образовательной платформы для молодежи',
                'created_at': datetime(2025, 9, 5, 10, 15, 0)
            },
            {
                'question_id': 3,
                'question_text': 'Целевая аудитория проекта?',
                'answer': 'Молодежь 18-25 лет, студенты вузов',
                'created_at': datetime(2025, 9, 5, 10, 20, 0)
            },
            {
                'question_id': 4,
                'question_text': 'География реализации проекта?',
                'answer': 'Российская Федерация, приоритет - Московская область',
                'created_at': datetime(2025, 9, 5, 10, 25, 0)
            },
            {
                'question_id': 5,
                'question_text': 'Сроки реализации проекта?',
                'answer': '12 месяцев с момента получения гранта',
                'created_at': datetime(2025, 9, 5, 10, 30, 0)
            }
        ]
    }


@pytest.fixture
def interview_artifact_pending():
    """Pending interview artifact"""
    return {
        'status': 'pending',
        'data': []
    }


# ========== MOCK AUDITOR ARTIFACTS ==========

@pytest.fixture
def auditor_artifact_completed():
    """Completed auditor artifact"""
    return {
        'status': 'completed',
        'score': 8.2,
        'quality_score': 8,
        'completeness_score': 9,
        'clarity_score': 8,
        'feasibility_score': 8,
        'innovation_score': 9,
        'approval_status': 'approved',
        'recommendations': {
            'strengths': [
                'Четко определена целевая аудитория',
                'Реалистичные сроки реализации',
                'Социально значимый проект'
            ],
            'improvements': [
                'Уточнить бюджет проекта',
                'Добавить метрики успеха'
            ],
            'risks': [
                'Высокая конкуренция в образовательной сфере',
                'Необходимость привлечения партнеров'
            ]
        },
        'completed_at': datetime(2025, 9, 5, 12, 0, 0)
    }


@pytest.fixture
def auditor_artifact_pending():
    """Pending auditor artifact"""
    return {
        'status': 'pending'
    }


# ========== MOCK RESEARCHER ARTIFACTS ==========

@pytest.fixture
def researcher_artifact_completed():
    """Completed researcher artifact"""
    return {
        'status': 'completed',
        'content': {
            'market_analysis': 'Рынок образовательных технологий растет на 15% ежегодно',
            'target_audience': 'Более 5 млн студентов в России',
            'competitors': [
                'Платформа A - 200k пользователей',
                'Платформа B - 150k пользователей'
            ],
            'trends': [
                'Переход на онлайн-обучение',
                'Геймификация образования',
                'Персонализированное обучение'
            ]
        },
        'metadata': {
            'sources': [
                'https://example.com/education-market-2025',
                'https://example.com/online-learning-trends'
            ],
            'research_date': '2025-09-05',
            'researcher_version': '1.0'
        },
        'research_status': 'completed',
        'created_at': datetime(2025, 9, 5, 13, 0, 0),
        'completed_at': datetime(2025, 9, 5, 13, 30, 0)
    }


@pytest.fixture
def researcher_artifact_pending():
    """Pending researcher artifact"""
    return {
        'status': 'pending'
    }


# ========== MOCK PLANNER ARTIFACTS ==========

@pytest.fixture
def planner_artifact_completed():
    """Completed planner artifact"""
    return {
        'status': 'completed',
        'structure': {
            'sections': [
                {'id': 1, 'title': 'Введение', 'order': 1},
                {'id': 2, 'title': 'Актуальность проекта', 'order': 2},
                {'id': 3, 'title': 'Цели и задачи', 'order': 3},
                {'id': 4, 'title': 'Методология', 'order': 4},
                {'id': 5, 'title': 'План реализации', 'order': 5},
                {'id': 6, 'title': 'Бюджет', 'order': 6},
                {'id': 7, 'title': 'Ожидаемые результаты', 'order': 7},
                {'id': 8, 'title': 'Команда проекта', 'order': 8},
                {'id': 9, 'title': 'Заключение', 'order': 9}
            ],
            'estimated_length': 15000,
            'recommended_structure': 'presidential_grant'
        },
        'sections': [
            'Введение',
            'Актуальность проекта',
            'Цели и задачи',
            'Методология',
            'План реализации',
            'Бюджет',
            'Ожидаемые результаты',
            'Команда проекта',
            'Заключение'
        ],
        'recommendations': 'Рекомендуется детально проработать раздел бюджета и добавить конкретные метрики',
        'completed_at': datetime(2025, 9, 5, 14, 0, 0)
    }


@pytest.fixture
def planner_artifact_pending():
    """Pending planner artifact"""
    return {
        'status': 'pending'
    }


# ========== MOCK WRITER ARTIFACTS ==========

@pytest.fixture
def writer_artifact_completed():
    """Completed writer artifact"""
    return {
        'status': 'completed',
        'grant_id': 'GR-20250905-001',
        'title': 'Образовательная платформа для молодежи',
        'content': '''# ГРАНТОВАЯ ЗАЯВКА

## Введение
Данный проект направлен на создание инновационной образовательной платформы...

## Актуальность проекта
В современных условиях цифровизации образования...

## Цели и задачи
Основная цель проекта - создание доступной образовательной платформы...

[Полный текст грантовой заявки продолжается...]
''',
        'sections': [
            {
                'title': 'Введение',
                'content': 'Данный проект направлен на создание инновационной образовательной платформы для молодежи...'
            },
            {
                'title': 'Актуальность проекта',
                'content': 'В современных условиях цифровизации образования существует острая необходимость...'
            },
            {
                'title': 'Цели и задачи',
                'content': 'Основная цель проекта - создание доступной образовательной платформы. Задачи: 1) Разработка платформы, 2) Привлечение пользователей...'
            },
            {
                'title': 'Методология',
                'content': 'Проект будет реализован с использованием современных образовательных технологий...'
            },
            {
                'title': 'План реализации',
                'content': 'Этап 1 (месяцы 1-3): Разработка концепции. Этап 2 (месяцы 4-6): Техническая разработка...'
            },
            {
                'title': 'Бюджет',
                'content': 'Общий бюджет проекта: 500 000 руб. Статьи расходов: 1) Технические разработки - 200к...'
            },
            {
                'title': 'Ожидаемые результаты',
                'content': 'К концу проекта планируется привлечь 10 000 пользователей, создать 50 курсов...'
            },
            {
                'title': 'Команда проекта',
                'content': 'Руководитель проекта: опыт 10 лет. Технический директор: опыт 7 лет...'
            },
            {
                'title': 'Заключение',
                'content': 'Проект имеет высокий потенциал социального воздействия и устойчивого развития...'
            }
        ],
        'metadata': {
            'word_count': 5000,
            'generation_time': '45 seconds',
            'tokens_used': 8500
        },
        'quality_score': 9.1,
        'llm_provider': 'gigachat',
        'model': 'GigaChat-Pro',
        'completed_at': datetime(2025, 9, 5, 15, 0, 0)
    }


@pytest.fixture
def writer_artifact_pending():
    """Pending writer artifact"""
    return {
        'status': 'pending'
    }


# ========== COMPLETE LIFECYCLE DATA ==========

@pytest.fixture
def full_lifecycle_data(
    sample_anketa_id,
    sample_metadata,
    interview_artifact_completed,
    auditor_artifact_completed,
    researcher_artifact_completed,
    planner_artifact_completed,
    writer_artifact_completed
):
    """Complete lifecycle data with all stages completed"""
    return {
        'anketa_id': sample_anketa_id,
        'progress': 100,
        'current_stage': 'writer',
        'metadata': sample_metadata,
        'artifacts': {
            'interview': interview_artifact_completed,
            'auditor': auditor_artifact_completed,
            'researcher': researcher_artifact_completed,
            'planner': planner_artifact_completed,
            'writer': writer_artifact_completed
        }
    }


@pytest.fixture
def partial_lifecycle_data(
    sample_anketa_id,
    sample_metadata,
    interview_artifact_completed,
    auditor_artifact_completed,
    researcher_artifact_pending,
    planner_artifact_pending,
    writer_artifact_pending
):
    """Partial lifecycle data (only interview and auditor completed)"""
    return {
        'anketa_id': sample_anketa_id,
        'progress': 40,
        'current_stage': 'researcher',
        'metadata': sample_metadata,
        'artifacts': {
            'interview': interview_artifact_completed,
            'auditor': auditor_artifact_completed,
            'researcher': researcher_artifact_pending,
            'planner': planner_artifact_pending,
            'writer': writer_artifact_pending
        }
    }


@pytest.fixture
def empty_lifecycle_data(sample_anketa_id, empty_metadata):
    """Empty lifecycle data with no completed stages"""
    return {
        'anketa_id': sample_anketa_id,
        'progress': 0,
        'current_stage': 'interview',
        'metadata': empty_metadata,
        'artifacts': {
            'interview': {'status': 'pending'},
            'auditor': {'status': 'pending'},
            'researcher': {'status': 'pending'},
            'planner': {'status': 'pending'},
            'writer': {'status': 'pending'}
        }
    }


# ========== DATABASE QUERY RESULTS ==========

@pytest.fixture
def mock_interview_query_result():
    """Mock database query result for interview data"""
    return [
        {
            'question_id': 1,
            'question_text': 'Название проекта?',
            'answer': 'Тестовый проект',
            'created_at': datetime(2025, 9, 5, 10, 10, 0)
        },
        {
            'question_id': 2,
            'question_text': 'Описание проекта?',
            'answer': 'Описание тестового проекта',
            'created_at': datetime(2025, 9, 5, 10, 15, 0)
        }
    ]


@pytest.fixture
def mock_auditor_query_result():
    """Mock database query result for auditor data"""
    return [
        {
            'quality_score': 8,
            'average_score': 8.5,
            'completeness_score': 9,
            'clarity_score': 8,
            'feasibility_score': 8,
            'innovation_score': 9,
            'recommendations': '{"improve": ["A", "B"]}',
            'approval_status': 'approved',
            'created_at': datetime(2025, 9, 5, 12, 0, 0)
        }
    ]


@pytest.fixture
def mock_researcher_query_result():
    """Mock database query result for researcher data"""
    return [
        {
            'research_results': '{"market": "data", "trends": ["trend1", "trend2"]}',
            'metadata': '{"sources": ["source1"], "version": "1.0"}',
            'status': 'completed',
            'created_at': datetime(2025, 9, 5, 13, 0, 0),
            'completed_at': datetime(2025, 9, 5, 13, 30, 0)
        }
    ]


@pytest.fixture
def mock_planner_query_result():
    """Mock database query result for planner data"""
    return [
        {
            'plan_structure': '{"sections": ["Section1", "Section2"], "count": 9}',
            'last_activity': datetime(2025, 9, 5, 14, 0, 0)
        }
    ]


@pytest.fixture
def mock_writer_query_result():
    """Mock database query result for writer data"""
    return [
        {
            'grant_id': 'GR-001',
            'grant_title': 'Grant Title',
            'grant_content': 'Full grant content...',
            'grant_sections': '[{"title": "Intro", "content": "..."}]',
            'metadata': '{"version": "1.0", "tokens": 5000}',
            'quality_score': 9,
            'llm_provider': 'gigachat',
            'model': 'GigaChat-Pro',
            'created_at': datetime(2025, 9, 5, 15, 0, 0)
        }
    ]


@pytest.fixture
def mock_metadata_query_result():
    """Mock database query result for metadata"""
    return [
        {
            'telegram_id': 123456789,
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'session_id': 1001,
            'session_started': datetime(2025, 9, 5, 10, 0, 0),
            'session_updated': datetime(2025, 9, 5, 15, 30, 0)
        }
    ]


# ========== UTILITY FIXTURES ==========

@pytest.fixture
def date_range():
    """Date range for testing timeline"""
    base_date = datetime(2025, 9, 5, 10, 0, 0)
    return {
        'start': base_date,
        'interview': base_date + timedelta(hours=1),
        'auditor': base_date + timedelta(hours=2),
        'researcher': base_date + timedelta(hours=3),
        'planner': base_date + timedelta(hours=4),
        'writer': base_date + timedelta(hours=5),
        'end': base_date + timedelta(hours=5, minutes=30)
    }


@pytest.fixture
def export_formats():
    """List of supported export formats"""
    return ['txt', 'pdf', 'docx']


@pytest.fixture
def stage_names():
    """List of all lifecycle stage names"""
    return ['interview', 'auditor', 'researcher', 'planner', 'writer']
