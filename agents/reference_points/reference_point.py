#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reference Point - Базовый класс для точки референса

Reference Point - это НЕ вопрос, а ЦЕЛЬ УЗНАТЬ что-то о проекте.
Например:
- "Понять суть проекта"
- "Определить проблему"
- "Узнать целевую аудиторию"

Вопросы генерируются адаптивно на основе контекста.

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 1.0
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class ReferencePointPriority(Enum):
    """Приоритет Reference Point"""
    P0_CRITICAL = 0    # Критично - без этого проект непонятен
    P1_IMPORTANT = 1   # Важно - нужно для оценки заявки
    P2_DESIRABLE = 2   # Желательно - улучшает заявку
    P3_OPTIONAL = 3    # Опционально - nice to have


class ReferencePointState(Enum):
    """Состояние жизненного цикла Reference Point"""
    NOT_STARTED = "not_started"      # Ещё не начинали собирать
    IN_PROGRESS = "in_progress"      # Частично собрано
    COMPLETED = "completed"          # Полностью собрано
    VALIDATED = "validated"          # Проверено и подтверждено
    ENRICHED = "enriched"           # Обогащено дополнительным контекстом


@dataclass
class CompletionCriteria:
    """Критерии завершённости Reference Point"""
    min_length: Optional[int] = None           # Минимальная длина ответа
    required_keywords: List[str] = field(default_factory=list)  # Обязательные ключевые слова
    semantic_completeness: float = 0.7         # Порог семантической полноты (0-1)
    required_fields: List[str] = field(default_factory=list)    # Обязательные поля
    custom_validator: Optional[callable] = None  # Кастомная функция валидации

    def is_complete(self, collected_data: Dict[str, Any]) -> bool:
        """
        Проверить, выполнены ли критерии завершённости

        Args:
            collected_data: Собранные данные для этого reference point

        Returns:
            True если все критерии выполнены
        """
        # Проверка минимальной длины
        if self.min_length:
            text = collected_data.get('text', '')
            if len(text) < self.min_length:
                return False

        # Проверка обязательных ключевых слов
        if self.required_keywords:
            text = collected_data.get('text', '').lower()
            for keyword in self.required_keywords:
                if keyword.lower() not in text:
                    return False

        # Проверка обязательных полей
        if self.required_fields:
            for field_name in self.required_fields:
                if field_name not in collected_data or not collected_data[field_name]:
                    return False

        # Кастомная валидация
        if self.custom_validator:
            try:
                return self.custom_validator(collected_data)
            except Exception as e:
                logger.error(f"Custom validator error: {e}")
                return False

        return True


@dataclass
class ReferencePoint:
    """
    Reference Point - цель узнать определённую информацию о проекте

    Это НЕ вопрос, а milestone информации.
    Вопросы генерируются адаптивно на основе контекста.

    Example:
        >>> rp = ReferencePoint(
        ...     id="rp_001",
        ...     name="Понять суть проекта",
        ...     description="Получить чёткое понимание того, что делает проект",
        ...     priority=ReferencePointPriority.P0_CRITICAL,
        ...     required=True,
        ...     completion_criteria=CompletionCriteria(min_length=100),
        ...     question_hints=[
        ...         "Что конкретно делает ваш проект?",
        ...         "В чём основная идея?",
        ...         "Какую главную задачу решает проект?"
        ...     ],
        ...     tags=["основа", "цель", "суть"]
        ... )
    """

    id: str                                  # Уникальный ID (rp_001, rp_002, ...)
    name: str                                # Название (что узнать)
    description: str                         # Подробное описание
    priority: ReferencePointPriority         # Приоритет (P0-P3)
    required: bool = True                    # Обязательно ли?

    # Критерии завершённости
    completion_criteria: CompletionCriteria = field(default_factory=CompletionCriteria)

    # Зависимости
    depends_on: List[str] = field(default_factory=list)  # Зависит от других RP (IDs)
    enables: List[str] = field(default_factory=list)     # Разблокирует другие RP (IDs)

    # Подсказки для генерации вопросов
    question_hints: List[str] = field(default_factory=list)  # Примеры вопросов

    # Метаданные
    tags: List[str] = field(default_factory=list)        # Теги для поиска
    grant_fund_specific: Optional[str] = None            # Специфичен для фонда (fpg, president, ...)

    # Состояние (runtime)
    state: ReferencePointState = ReferencePointState.NOT_STARTED
    collected_data: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0            # Уверенность в полноте (0-1)

    def __post_init__(self):
        """Валидация после инициализации"""
        if not self.id:
            raise ValueError("ReferencePoint must have an ID")
        if not self.name:
            raise ValueError("ReferencePoint must have a name")

    def is_blocked(self, completed_rp_ids: List[str]) -> bool:
        """
        Проверить, заблокирован ли этот RP зависимостями

        Args:
            completed_rp_ids: Список ID уже завершённых RP

        Returns:
            True если есть незавершённые зависимости
        """
        if not self.depends_on:
            return False

        for dep_id in self.depends_on:
            if dep_id not in completed_rp_ids:
                return True

        return False

    def update_state(self, new_state: ReferencePointState):
        """Обновить состояние RP"""
        old_state = self.state
        self.state = new_state
        logger.info(f"RP {self.id} ({self.name}): {old_state.value} → {new_state.value}")

    def add_data(self, key: str, value: Any):
        """
        Добавить собранные данные

        Args:
            key: Ключ данных
            value: Значение
        """
        self.collected_data[key] = value

        # Автоматически обновить состояние
        if self.state == ReferencePointState.NOT_STARTED:
            self.update_state(ReferencePointState.IN_PROGRESS)

        # Проверить завершённость
        if self.completion_criteria.is_complete(self.collected_data):
            if self.state != ReferencePointState.COMPLETED:
                self.update_state(ReferencePointState.COMPLETED)

            # Вычислить уверенность
            self.confidence_score = self._calculate_confidence()

    def _calculate_confidence(self) -> float:
        """
        Вычислить уровень уверенности в полноте данных

        Returns:
            Оценка 0-1
        """
        # Базовая логика: наличие данных и выполнение критериев
        if not self.collected_data:
            return 0.0

        score = 0.0

        # Выполнены ли базовые критерии
        if self.completion_criteria.is_complete(self.collected_data):
            score += 0.7

        # Есть ли богатые данные (не только текст)
        if len(self.collected_data) > 1:
            score += 0.2

        # Есть ли длинный осмысленный ответ
        text = self.collected_data.get('text', '')
        if len(text) > 200:
            score += 0.1

        return min(score, 1.0)

    def is_complete(self) -> bool:
        """Проверить завершённость"""
        return self.state in [ReferencePointState.COMPLETED,
                             ReferencePointState.VALIDATED,
                             ReferencePointState.ENRICHED]

    def needs_enrichment(self) -> bool:
        """
        Нужно ли обогащение данных

        Returns:
            True если данные есть, но неполные
        """
        return (
            self.state == ReferencePointState.COMPLETED and
            self.confidence_score < 0.8 and
            not self.required
        )

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в dict"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority.value,
            'required': self.required,
            'state': self.state.value,
            'collected_data': self.collected_data,
            'confidence_score': self.confidence_score,
            'tags': self.tags,
            'depends_on': self.depends_on,
            'enables': self.enables
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReferencePoint':
        """Десериализация из dict"""
        # Восстановить enums
        priority = ReferencePointPriority(data.get('priority', 0))
        state = ReferencePointState(data.get('state', 'not_started'))

        rp = cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            priority=priority,
            required=data.get('required', True),
            depends_on=data.get('depends_on', []),
            enables=data.get('enables', []),
            tags=data.get('tags', [])
        )

        rp.state = state
        rp.collected_data = data.get('collected_data', {})
        rp.confidence_score = data.get('confidence_score', 0.0)

        return rp

    def __repr__(self) -> str:
        return (f"ReferencePoint(id={self.id}, name={self.name}, "
                f"priority={self.priority.name}, state={self.state.value}, "
                f"confidence={self.confidence_score:.2f})")


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Создать reference point
    rp = ReferencePoint(
        id="rp_001",
        name="Понять суть проекта",
        description="Получить чёткое понимание того, что делает проект",
        priority=ReferencePointPriority.P0_CRITICAL,
        required=True,
        completion_criteria=CompletionCriteria(
            min_length=100,
            required_keywords=["проект", "цель"]
        ),
        question_hints=[
            "Что конкретно делает ваш проект?",
            "В чём основная идея?",
            "Какую главную задачу решает проект?"
        ],
        tags=["основа", "цель", "суть"]
    )

    print(rp)

    # Добавить данные
    rp.add_data('text', 'Наш проект создаёт мобильное приложение для помощи детям с аутизмом в развитии коммуникативных навыков. Основная цель - облегчить взаимодействие таких детей с окружающим миром.')

    print(f"State: {rp.state}")
    print(f"Complete: {rp.is_complete()}")
    print(f"Confidence: {rp.confidence_score}")

    # Сериализация
    data = rp.to_dict()
    print(f"\nSerialized: {data}")

    # Десериализация
    rp2 = ReferencePoint.from_dict(data)
    print(f"\nDeserialized: {rp2}")
