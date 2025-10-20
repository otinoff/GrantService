#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grant Lifecycle Manager - управление полным жизненным циклом грантовой заявки

Этот модуль отвечает за получение всех артефактов заявки на каждом этапе:
1. Interview - анкетные данные (24 вопроса-ответа)
2. Auditor - оценка проекта (1-10 баллов)
3. Researcher - исследование рынка/конкурентов
4. Planner - структура заявки
5. Writer - финальный грант (13 секций)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.postgres_helper import execute_query

logger = logging.getLogger(__name__)


class GrantLifecycleManager:
    """Менеджер жизненного цикла грантовой заявки"""

    # Определение этапов жизненного цикла
    STAGES = {
        'interview': {
            'name': 'Интервью',
            'emoji': '📝',
            'table': 'user_answers',
            'order': 1
        },
        'auditor': {
            'name': 'Аудит',
            'emoji': '🔍',
            'table': 'auditor_results',
            'order': 2
        },
        'researcher': {
            'name': 'Исследование',
            'emoji': '📊',
            'table': 'researcher_research',
            'order': 3
        },
        'planner': {
            'name': 'Планирование',
            'emoji': '📋',
            'table': 'planner_results',
            'order': 4
        },
        'writer': {
            'name': 'Написание',
            'emoji': '✍️',
            'table': 'grants',
            'order': 5
        }
    }

    def __init__(self, anketa_id: str):
        """
        Инициализация менеджера для конкретной заявки

        Args:
            anketa_id: Идентификатор анкеты (например, AN-20250905-username-001)
        """
        self.anketa_id = anketa_id
        self.artifacts = {}
        self.current_stage = None
        self.progress = 0

    def get_all_artifacts(self) -> Dict[str, Any]:
        """
        Получить все артефакты заявки

        Returns:
            Dict с артефактами всех этапов
        """
        try:
            self.artifacts = {
                'interview': self._get_interview_data(),
                'auditor': self._get_auditor_data(),
                'researcher': self._get_researcher_data(),
                'planner': self._get_planner_data(),
                'writer': self._get_writer_data()
            }

            # Определить текущий этап и прогресс
            self._calculate_progress()

            return {
                'anketa_id': self.anketa_id,
                'artifacts': self.artifacts,
                'current_stage': self.current_stage,
                'progress': self.progress,
                'metadata': self._get_metadata()
            }

        except Exception as e:
            logger.error(f"Error getting artifacts for {self.anketa_id}: {e}")
            return {}

    def _get_interview_data(self) -> Optional[Dict]:
        """Получить данные интервью (анкета)"""
        query = """
        SELECT
            ua.question_id,
            iq.question_text,
            ua.answer_text as answer,
            ua.answer_timestamp as created_at
        FROM user_answers ua
        JOIN sessions s ON ua.session_id = s.id
        LEFT JOIN interview_questions iq ON ua.question_id = iq.question_number
        WHERE s.anketa_id = %s
        ORDER BY ua.question_id
        """

        try:
            result = execute_query(query, (self.anketa_id,))
            if result:
                return {
                    'status': 'completed',
                    'questions_count': len(result),
                    'data': [dict(row) for row in result],
                    'completed_at': result[0]['created_at'] if result else None
                }
            return {'status': 'pending', 'data': []}
        except Exception as e:
            logger.error(f"Error getting interview data: {e}")
            return {'status': 'error', 'data': []}

    def _get_auditor_data(self) -> Optional[Dict]:
        """Получить данные аудита"""
        query = """
        SELECT
            ar.quality_score,
            ar.average_score,
            ar.completeness_score,
            ar.clarity_score,
            ar.feasibility_score,
            ar.innovation_score,
            ar.recommendations,
            ar.approval_status,
            ar.created_at
        FROM auditor_results ar
        JOIN sessions s ON ar.session_id = s.id
        WHERE s.anketa_id = %s
        ORDER BY ar.created_at DESC
        LIMIT 1
        """

        try:
            result = execute_query(query, (self.anketa_id,))
            if result and result[0]:
                row = result[0]

                # Parse recommendations if it's JSON
                recommendations = row.get('recommendations')
                if isinstance(recommendations, str):
                    import json
                    recommendations = json.loads(recommendations)

                return {
                    'status': 'completed',
                    'score': row.get('average_score') or row.get('quality_score'),
                    'quality_score': row.get('quality_score'),
                    'completeness_score': row.get('completeness_score'),
                    'clarity_score': row.get('clarity_score'),
                    'feasibility_score': row.get('feasibility_score'),
                    'innovation_score': row.get('innovation_score'),
                    'approval_status': row.get('approval_status'),
                    'recommendations': recommendations,
                    'completed_at': row.get('created_at')
                }
            return {'status': 'pending'}
        except Exception as e:
            logger.error(f"Error getting auditor data: {e}")
            return {'status': 'error'}

    def _get_researcher_data(self) -> Optional[Dict]:
        """Получить данные исследования"""
        query = """
        SELECT
            research_results,
            metadata,
            status,
            created_at,
            completed_at
        FROM researcher_research
        WHERE anketa_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """

        try:
            result = execute_query(query, (self.anketa_id,))
            if result and result[0]:
                row = result[0]

                # Parse research_results if it's JSON
                research_results = row.get('research_results')
                if isinstance(research_results, str):
                    import json
                    research_results = json.loads(research_results)

                metadata = row.get('metadata')
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)

                return {
                    'status': 'completed',
                    'content': research_results,
                    'metadata': metadata,
                    'research_status': row.get('status'),
                    'created_at': row.get('created_at'),
                    'completed_at': row.get('completed_at')
                }
            return {'status': 'pending'}
        except Exception as e:
            logger.error(f"Error getting researcher data: {e}")
            return {'status': 'error'}

    def _get_planner_data(self) -> Optional[Dict]:
        """Получить данные планирования из planner_structures"""
        query = """
        SELECT
            ps.structure_json,
            ps.sections_count,
            ps.total_word_count_target,
            ps.data_mapping_complete,
            ps.created_at
        FROM planner_structures ps
        JOIN sessions s ON ps.session_id = s.id
        WHERE s.anketa_id = %s
        ORDER BY ps.created_at DESC
        LIMIT 1
        """

        try:
            result = execute_query(query, (self.anketa_id,))
            if result and result[0]:
                row = result[0]

                # Parse structure_json if it's JSON string
                structure_json = row.get('structure_json')
                if isinstance(structure_json, str):
                    import json
                    structure_json = json.loads(structure_json)

                return {
                    'status': 'completed',
                    'structure': structure_json,
                    'sections_count': row.get('sections_count'),
                    'total_word_count_target': row.get('total_word_count_target'),
                    'data_mapping_complete': row.get('data_mapping_complete'),
                    'completed_at': row.get('created_at')
                }
            return {'status': 'pending'}
        except Exception as e:
            logger.error(f"Error getting planner data: {e}")
            return {'status': 'error'}

    def _get_writer_data(self) -> Optional[Dict]:
        """Получить финальный грант"""
        query = """
        SELECT
            grant_id,
            grant_title,
            grant_content,
            grant_sections,
            metadata,
            quality_score,
            llm_provider,
            model,
            created_at
        FROM grants
        WHERE anketa_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """

        try:
            result = execute_query(query, (self.anketa_id,))
            if result and result[0]:
                row = result[0]

                # Handle JSONB fields
                sections = row.get('grant_sections')
                if isinstance(sections, str):
                    import json
                    sections = json.loads(sections)

                metadata = row.get('metadata')
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)

                return {
                    'status': 'completed',
                    'grant_id': row.get('grant_id'),
                    'title': row.get('grant_title'),
                    'content': row.get('grant_content'),
                    'sections': sections or [],
                    'metadata': metadata or {},
                    'quality_score': row.get('quality_score'),
                    'llm_provider': row.get('llm_provider'),
                    'model': row.get('model'),
                    'completed_at': row.get('created_at')
                }
            return {'status': 'pending'}
        except Exception as e:
            logger.error(f"Error getting writer data: {e}")
            return {'status': 'error'}

    def _calculate_progress(self):
        """Вычислить текущий этап и прогресс (0-100%)"""
        completed_stages = 0
        last_completed_stage = None

        for stage_key in ['interview', 'auditor', 'researcher', 'planner', 'writer']:
            if self.artifacts.get(stage_key, {}).get('status') == 'completed':
                completed_stages += 1
                last_completed_stage = stage_key
            else:
                # Первый незавершенный этап - текущий
                if not self.current_stage:
                    self.current_stage = stage_key

        # Если все этапы завершены
        if completed_stages == 5:
            self.current_stage = 'writer'

        # Прогресс: каждый этап = 20%
        self.progress = (completed_stages / 5) * 100

    def _get_metadata(self) -> Dict:
        """Получить метаданные заявки"""
        query = """
        SELECT
            u.telegram_id,
            u.username,
            u.first_name,
            u.last_name,
            s.id as session_id,
            s.started_at as session_started,
            s.last_activity as session_updated
        FROM sessions s
        LEFT JOIN users u ON s.telegram_id = u.id
        WHERE s.anketa_id = %s
        LIMIT 1
        """

        try:
            result = execute_query(query, (self.anketa_id,))
            if result and result[0]:
                row = result[0]
                return {
                    'telegram_id': row.get('telegram_id'),
                    'username': row.get('username'),
                    'first_name': row.get('first_name'),
                    'last_name': row.get('last_name'),
                    'session_id': row.get('session_id'),
                    'session_started': row.get('session_started'),
                    'session_updated': row.get('session_updated')
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return {}


def get_lifecycle_summary(anketa_id: str) -> Dict[str, Any]:
    """
    Получить краткую сводку по жизненному циклу заявки

    Args:
        anketa_id: Идентификатор анкеты

    Returns:
        Dict с кратким статусом каждого этапа
    """
    manager = GrantLifecycleManager(anketa_id)
    full_data = manager.get_all_artifacts()

    if not full_data:
        return {}

    # Создать краткую сводку для UI
    summary = {
        'anketa_id': anketa_id,
        'current_stage': full_data.get('current_stage'),
        'progress': full_data.get('progress'),
        'stages': {}
    }

    for stage_key, stage_info in GrantLifecycleManager.STAGES.items():
        artifact = full_data['artifacts'].get(stage_key, {})
        summary['stages'][stage_key] = {
            'name': stage_info['name'],
            'emoji': stage_info['emoji'],
            'status': artifact.get('status', 'pending'),
            'order': stage_info['order']
        }

    return summary
