#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reference Points Framework - Адаптивная система интервью для грантов

Компоненты:
- ReferencePoint - базовый класс точки референса
- ReferencePointManager - управление коллекцией RP
- AdaptiveQuestionGenerator - генерация контекстных вопросов
- ConversationFlowManager - управление потоком диалога

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 1.0
"""

from .reference_point import (
    ReferencePoint,
    ReferencePointPriority,
    ReferencePointState,
    CompletionCriteria
)

from .reference_point_manager import (
    ReferencePointManager,
    ReferencePointsProgress
)

from .adaptive_question_generator import (
    AdaptiveQuestionGenerator,
    UserExpertiseLevel,
    ProjectType
)

from .conversation_flow_manager import (
    ConversationFlowManager,
    ConversationState,
    TransitionType,
    ConversationContext
)

__all__ = [
    # Core
    'ReferencePoint',
    'ReferencePointPriority',
    'ReferencePointState',
    'CompletionCriteria',

    # Manager
    'ReferencePointManager',
    'ReferencePointsProgress',

    # Generator
    'AdaptiveQuestionGenerator',
    'UserExpertiseLevel',
    'ProjectType',

    # Flow
    'ConversationFlowManager',
    'ConversationState',
    'TransitionType',
    'ConversationContext',
]

__version__ = '1.0.0'
__author__ = 'Grant Service Architect Agent'
