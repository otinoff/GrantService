#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Interview Wrapper для интеграции с Telegram Bot
Обертка для InteractiveInterviewerAgent
"""

import sys
import logging
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


async def run_ai_audit_for_anketa(anketa_id: str, db):
    """
    Запустить AI аудит для существующей анкеты

    Args:
        anketa_id: ID анкеты (напр. AN-20251020-username-123)
        db: Database instance

    Returns:
        dict: {
            'success': bool,
            'audit_score': int (0-100),
            'recommendations': list[str],
            'message': str
        }
    """
    try:
        from agents.interactive_interviewer_agent import InteractiveInterviewerAgent

        # Загружаем данные анкеты из БД
        anketa_data = db.get_session_by_anketa_id(anketa_id)

        if not anketa_data:
            return {
                'success': False,
                'audit_score': 0,
                'recommendations': [],
                'message': f"Анкета {anketa_id} не найдена"
            }

        # Подготавливаем user_data для агента
        user_data = {
            'telegram_id': anketa_data.get('user_id', 0),
            'username': anketa_data.get('username', 'unknown'),
            'first_name': anketa_data.get('first_name', ''),
            'last_name': anketa_data.get('last_name', ''),
            'email': anketa_data.get('email', ''),
            'phone': anketa_data.get('phone', ''),
            'grant_fund': anketa_data.get('grant_fund', 'Фонд не указан')
        }

        # Добавляем ответы из анкеты
        # Предполагаем что в БД хранится interview_data JSONB
        interview_data = anketa_data.get('interview_data', {})

        # Мапим поля анкеты на формат InteractiveInterviewerAgent
        block_1_fields = {
            'block_1_q1': interview_data.get('project_name', ''),
            'block_1_q2': interview_data.get('project_goal', ''),
            'block_1_q3': interview_data.get('problem_statement', ''),
            'block_1_q4': interview_data.get('target_audience', ''),
            'block_1_q5': interview_data.get('geography', '')
        }

        block_2_fields = {
            'block_2_q1': interview_data.get('project_tasks', ''),
            'block_2_q2': interview_data.get('methodology', ''),
            'block_2_q3': interview_data.get('expected_results', ''),
            'block_2_q4': interview_data.get('budget', ''),
            'block_2_q5': interview_data.get('budget_breakdown', '')
        }

        block_3_fields = {
            'block_3_q1': interview_data.get('team_experience', ''),
            'block_3_q2': interview_data.get('partnerships', ''),
            'block_3_q3': interview_data.get('risk_management', ''),
            'block_3_q4': interview_data.get('sustainability', ''),
            'block_3_q5': interview_data.get('project_duration', '')
        }

        user_data.update(block_1_fields)
        user_data.update(block_2_fields)
        user_data.update(block_3_fields)

        # Создаем агента
        agent = InteractiveInterviewerAgent(db, llm_provider="claude_code")

        # Запускаем аудит
        logger.info(f"Running AI audit for anketa {anketa_id}...")
        result = await agent.conduct_interview_with_audit(user_data=user_data)

        if result['status'] == 'success':
            # Обновляем audit_score в БД
            try:
                db.update_anketa_audit_score(anketa_id, result['audit_score'])
            except Exception as e:
                logger.warning(f"Failed to update audit_score in DB: {e}")

            return {
                'success': True,
                'audit_score': result['audit_score'],
                'recommendations': result.get('recommendations', []),
                'message': f"AI аудит завершен. Оценка: {result['audit_score']}/100"
            }
        else:
            return {
                'success': False,
                'audit_score': 0,
                'recommendations': [],
                'message': f"Ошибка аудита: {result.get('error', 'Unknown error')}"
            }

    except ImportError as e:
        logger.error(f"Import error in AI audit: {e}")
        return {
            'success': False,
            'audit_score': 0,
            'recommendations': [],
            'message': f"InteractiveInterviewerAgent не доступен: {e}"
        }
    except Exception as e:
        logger.error(f"Error in AI audit: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'audit_score': 0,
            'recommendations': [],
            'message': f"Ошибка: {e}"
        }


def format_ai_audit_message(audit_result):
    """
    Форматировать сообщение с результатами AI аудита для Telegram

    Args:
        audit_result: dict from run_ai_audit_for_anketa()

    Returns:
        str: Formatted message for Telegram
    """
    if not audit_result['success']:
        return f"❌ {audit_result['message']}"

    score = audit_result['audit_score']

    # Эмодзи в зависимости от оценки
    if score >= 80:
        emoji = "🌟"
        status = "Отлично!"
    elif score >= 60:
        emoji = "✅"
        status = "Хорошо"
    elif score >= 40:
        emoji = "⚠️"
        status = "Требует доработки"
    else:
        emoji = "❌"
        status = "Недостаточно информации"

    message = f"""
{emoji} *AI Аудит завершен!*

*Оценка:* {score}/100
*Статус:* {status}
"""

    # Добавляем рекомендации если есть
    recommendations = audit_result.get('recommendations', [])
    if recommendations:
        message += "\n*💡 Рекомендации:*\n"
        for i, rec in enumerate(recommendations[:5], 1):  # Первые 5
            message += f"{i}. {rec}\n"

    return message
