#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent Settings Manager
==========================
Управление настройками AI-агентов из таблицы ai_agent_settings

Author: Grant Service Architect Agent
Created: 2025-10-06
"""

from typing import Dict, Any, Optional
import json
import logging
from .postgres_helper import execute_query, execute_update

logger = logging.getLogger(__name__)


def get_agent_settings(agent_name: str) -> Dict[str, Any]:
    """
    Получить настройки агента из таблицы ai_agent_settings

    Args:
        agent_name: Имя агента (interviewer, writer, auditor, planner, researcher)

    Returns:
        Dict с настройками агента:
            - mode: режим работы (для interviewer: structured/ai_powered)
            - provider: LLM провайдер (gigachat/claude_code)
            - execution_mode: режим запуска (automatic/manual)
            - config: дополнительные параметры (JSONB)

    Example:
        >>> settings = get_agent_settings('interviewer')
        >>> print(settings['mode'])  # 'structured'
        >>> print(settings['execution_mode'])  # 'manual'
    """
    try:
        result = execute_query(
            "SELECT mode, provider, execution_mode, config FROM ai_agent_settings WHERE agent_name = %s",
            (agent_name,)
        )

        if not result:
            # Default settings when no record exists
            logger.warning(f"No settings found for agent '{agent_name}', using defaults")
            return {
                'mode': 'structured' if agent_name == 'interviewer' else 'active',
                'provider': 'gigachat',
                'execution_mode': 'manual',
                'config': {}
            }

        # execute_query returns list of dicts (RealDictCursor)
        settings = result[0]

        # JSONB config is already parsed by PostgreSQL
        config = settings.get('config', {})
        if isinstance(config, str):
            # Fallback: parse if it's somehow a string
            config = json.loads(config)

        return {
            'mode': settings.get('mode'),
            'provider': settings.get('provider'),
            'execution_mode': settings.get('execution_mode', 'manual'),
            'config': config
        }

    except Exception as e:
        logger.error(f"Error getting settings for agent '{agent_name}': {e}")
        # Return safe defaults
        return {
            'mode': 'structured' if agent_name == 'interviewer' else 'active',
            'provider': 'gigachat',
            'execution_mode': 'manual',
            'config': {}
        }


def save_agent_settings(
    agent_name: str,
    mode: Optional[str] = None,
    provider: Optional[str] = None,
    execution_mode: Optional[str] = None,
    config: Optional[Dict] = None
) -> bool:
    """
    Сохранить или обновить настройки агента

    Args:
        agent_name: Имя агента
        mode: Режим работы (для interviewer: structured/ai_powered)
        provider: LLM провайдер (gigachat/claude_code)
        execution_mode: Режим запуска (automatic/manual)
        config: Дополнительные параметры (будут сохранены как JSONB)

    Returns:
        True если успешно, False если ошибка

    Example:
        >>> save_agent_settings('interviewer', mode='ai_powered')
        True
        >>> save_agent_settings('writer', execution_mode='automatic')
        True
        >>> save_agent_settings('writer', provider='claude_code', config={'temperature': 0.8})
        True
    """
    try:
        # Build SET clause for UPDATE dynamically
        updates = []
        params = []

        if mode is not None:
            updates.append("mode = %s")
            params.append(mode)

        if provider is not None:
            updates.append("provider = %s")
            params.append(provider)

        if execution_mode is not None:
            updates.append("execution_mode = %s")
            params.append(execution_mode)

        if config is not None:
            updates.append("config = %s::jsonb")
            # PostgreSQL accepts JSON string for JSONB
            params.append(json.dumps(config))

        if not updates:
            logger.warning(f"No fields to update for agent '{agent_name}'")
            return False

        # Always update timestamp
        updates.append("updated_at = NOW()")

        # Add agent_name for WHERE clause
        params.append(agent_name)

        query = f"""
            UPDATE ai_agent_settings
            SET {', '.join(updates)}
            WHERE agent_name = %s
        """

        rowcount = execute_update(query, tuple(params))

        if rowcount > 0:
            logger.info(f"Updated settings for agent '{agent_name}'")
            return True
        else:
            logger.warning(f"No agent found with name '{agent_name}' - cannot update")
            return False

    except Exception as e:
        logger.error(f"Error saving settings for agent '{agent_name}': {e}")
        return False


def get_interviewer_mode() -> str:
    """
    Получить режим работы интервьюера

    Returns:
        'structured' или 'ai_powered'

    Example:
        >>> mode = get_interviewer_mode()
        >>> if mode == 'ai_powered':
        ...     print("Using Claude Code for interview")
    """
    settings = get_agent_settings('interviewer')
    return settings.get('mode', 'structured')


def get_agent_provider(agent_name: str) -> str:
    """
    Получить LLM провайдера для агента

    Args:
        agent_name: Имя агента (writer, auditor, planner, researcher)

    Returns:
        'gigachat' или 'claude_code'

    Example:
        >>> provider = get_agent_provider('writer')
        >>> print(f"Writer using: {provider}")
    """
    settings = get_agent_settings(agent_name)
    return settings.get('provider', 'gigachat')


def is_claude_code_enabled(agent_name: str) -> bool:
    """
    Проверить включен ли Claude Code для агента

    Для interviewer: проверяет mode == 'ai_powered'
    Для остальных: проверяет provider == 'claude_code'

    Args:
        agent_name: Имя агента

    Returns:
        True если Claude Code включен

    Example:
        >>> if is_claude_code_enabled('auditor'):
        ...     print("Using Claude Code for audit")
        ... else:
        ...     print("Using GigaChat for audit")
    """
    if agent_name == 'interviewer':
        return get_interviewer_mode() == 'ai_powered'
    else:
        return get_agent_provider(agent_name) == 'claude_code'


def get_execution_mode(agent_name: str) -> str:
    """
    Получить режим запуска агента

    Args:
        agent_name: Имя агента

    Returns:
        'automatic' или 'manual'

    Example:
        >>> mode = get_execution_mode('writer')
        >>> if mode == 'manual':
        ...     print("Agent requires manual trigger")
    """
    settings = get_agent_settings(agent_name)
    return settings.get('execution_mode', 'manual')


def is_auto_execution_enabled(agent_name: str) -> bool:
    """
    Проверить включен ли автоматический запуск для агента

    Args:
        agent_name: Имя агента

    Returns:
        True если execution_mode == 'automatic'

    Example:
        >>> if is_auto_execution_enabled('auditor'):
        ...     print("Auditor will auto-process")
        ... else:
        ...     print("Auditor requires manual trigger")
    """
    return get_execution_mode(agent_name) == 'automatic'


def get_auditor_mode() -> str:
    """
    Получить режим работы Auditor

    Returns:
        'live' | 'batch' | 'hybrid'
        - live: аудит после каждого ответа (уточняющие вопросы сразу)
        - batch: аудит всей анкеты после заполнения (по умолчанию)
        - hybrid: аудит критичных пробелов после заполнения (баланс)

    Example:
        >>> mode = get_auditor_mode()
        >>> if mode == 'live':
        ...     print("Live auditing enabled")
    """
    settings = get_agent_settings('auditor')
    config = settings.get('config', {})
    return config.get('auditor_mode', 'batch')


def save_auditor_mode(mode: str) -> bool:
    """
    Сохранить режим работы Auditor

    Args:
        mode: 'live' | 'batch' | 'hybrid'

    Returns:
        True если успешно

    Example:
        >>> save_auditor_mode('hybrid')
        True
    """
    if mode not in ['live', 'batch', 'hybrid']:
        logger.error(f"Invalid auditor mode: {mode}")
        return False

    settings = get_agent_settings('auditor')
    config = settings.get('config', {})
    config['auditor_mode'] = mode

    return save_agent_settings('auditor', config=config)


__all__ = [
    'get_agent_settings',
    'save_agent_settings',
    'get_interviewer_mode',
    'get_agent_provider',
    'is_claude_code_enabled',
    'get_execution_mode',
    'is_auto_execution_enabled',
    'get_auditor_mode',
    'save_auditor_mode',
]
