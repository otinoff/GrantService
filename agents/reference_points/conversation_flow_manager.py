#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversation Flow Manager - Управление потоком разговора

Реализует state machine для естественного диалога:
INIT → EXPLORING → DEEPENING → VALIDATING → FINALIZING

Определяет:
- Когда переходить к следующему RP
- Когда задавать follow-up вопрос
- Когда валидировать ответ
- Когда завершать интервью

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 1.0
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging

from .reference_point import ReferencePoint, ReferencePointState
from .reference_point_manager import ReferencePointManager

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Состояния разговора"""
    INIT = "init"                    # Приветствие, знакомство
    EXPLORING = "exploring"          # Исследование - задаём базовые вопросы
    DEEPENING = "deepening"          # Углубление - follow-up вопросы
    VALIDATING = "validating"        # Валидация - проверка понимания
    FINALIZING = "finalizing"        # Завершение - финальные штрихи


class TransitionType(Enum):
    """Типы переходов в диалоге"""
    LINEAR = "linear"                # Обычный прогресс (следующий RP)
    SKIP = "skip"                    # Пропуск (уже отвечено)
    LOOP_BACK = "loop_back"          # Возврат (уточнить предыдущее)
    DEEP_DIVE = "deep_dive"          # Углубление (интересная тема)
    FAST_FORWARD = "fast_forward"    # Быстрый прогресс (очень полный ответ)
    FINALIZE = "finalize"            # Завершение интервью


@dataclass
class ConversationContext:
    """Контекст разговора"""
    current_state: ConversationState = ConversationState.INIT
    current_rp: Optional[ReferencePoint] = None
    previous_rp: Optional[ReferencePoint] = None

    # Счётчики
    questions_asked: int = 0
    follow_ups_asked: int = 0
    max_follow_ups: int = 5  # Бюджет уточняющих вопросов

    # История
    dialogue_history: List[Dict[str, Any]] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    covered_topics: List[str] = field(default_factory=list)

    # Метрики
    user_engagement_score: float = 1.0  # 0-1, насколько охотно отвечает
    conversation_quality: float = 0.5   # 0-1, насколько качественный диалог

    def add_turn(
        self,
        question: str,
        answer: str,
        rp_id: str
    ):
        """Добавить ход разговора"""
        self.dialogue_history.append({
            'turn': len(self.dialogue_history) + 1,
            'question': question,
            'answer': answer,
            'rp_id': rp_id,
            'state': self.current_state.value
        })
        self.questions_asked += 1

    def get_remaining_follow_ups(self) -> int:
        """Сколько осталось уточняющих вопросов"""
        return max(0, self.max_follow_ups - self.follow_ups_asked)


class ConversationFlowManager:
    """
    Менеджер потока разговора

    Управляет state machine диалога и определяет:
    - Текущее состояние разговора
    - Следующее действие (какой вопрос)
    - Когда переходить между состояниями
    - Когда завершать интервью

    Example:
        >>> flow = ConversationFlowManager(rp_manager)
        >>> next_action = flow.decide_next_action(context)
        >>> if next_action['type'] == 'ask_question':
        ...     question = next_action['question']
    """

    def __init__(
        self,
        rp_manager: ReferencePointManager
    ):
        """
        Инициализация

        Args:
            rp_manager: Менеджер reference points
        """
        self.rp_manager = rp_manager
        self.context = ConversationContext()

    def decide_next_action(
        self,
        last_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Решить, что делать дальше

        Args:
            last_answer: Последний ответ пользователя

        Returns:
            Словарь с действием:
            {
                'type': 'ask_question' | 'validate' | 'finalize',
                'reference_point': ReferencePoint,
                'transition': TransitionType,
                'message': str  # Опциональное сообщение
            }
        """
        # Обработать последний ответ (если есть)
        if last_answer and self.context.current_rp:
            self._process_answer(last_answer, self.context.current_rp)

        # Определить состояние
        self._update_conversation_state()

        # Проверить условия завершения
        if self._should_finalize():
            return {
                'type': 'finalize',
                'transition': TransitionType.FINALIZE,
                'message': 'Спасибо! У меня достаточно информации для создания заявки.'
            }

        # Определить следующий RP
        next_rp, transition = self._select_next_reference_point()

        if not next_rp:
            # Нет следующего RP - завершаем
            return {
                'type': 'finalize',
                'transition': TransitionType.FINALIZE,
                'message': 'Отлично! Мы собрали всю нужную информацию.'
            }

        # Обновить контекст
        self.context.previous_rp = self.context.current_rp
        self.context.current_rp = next_rp

        # Вернуть действие
        return {
            'type': 'ask_question',
            'reference_point': next_rp,
            'transition': transition,
            'message': self._get_transition_message(transition)
        }

    def _process_answer(
        self,
        answer: str,
        reference_point: ReferencePoint
    ):
        """
        Обработать ответ пользователя

        Args:
            answer: Ответ пользователя
            reference_point: RP на который отвечали
        """
        # Сохранить данные
        reference_point.add_data('text', answer)
        self.context.collected_data[reference_point.id] = answer

        # Обновить covered topics
        for tag in reference_point.tags:
            if tag not in self.context.covered_topics:
                self.context.covered_topics.append(tag)

        # Оценить engagement
        answer_length = len(answer.strip())
        if answer_length < 30:
            self.context.user_engagement_score *= 0.9  # Короткий ответ - снизить
        elif answer_length > 150:
            self.context.user_engagement_score = min(1.0, self.context.user_engagement_score * 1.1)

        # Оценить качество
        if reference_point.is_complete():
            self.context.conversation_quality = min(1.0, self.context.conversation_quality + 0.1)

        logger.info(f"Processed answer for {reference_point.id}: "
                   f"length={answer_length}, "
                   f"complete={reference_point.is_complete()}")

    def _update_conversation_state(self):
        """Обновить состояние разговора"""
        progress = self.rp_manager.get_progress()

        # Логика переходов состояний
        if self.context.current_state == ConversationState.INIT:
            if self.context.questions_asked > 0:
                self.context.current_state = ConversationState.EXPLORING

        elif self.context.current_state == ConversationState.EXPLORING:
            # Переход к DEEPENING если:
            # - Есть неполные критичные RP
            # - Или собрано >= 50% базовой информации
            incomplete_critical = self.rp_manager.get_incomplete_critical_rps()

            if progress.overall_completion >= 0.5 and incomplete_critical:
                self.context.current_state = ConversationState.DEEPENING
            elif progress.critical_completed:
                self.context.current_state = ConversationState.VALIDATING

        elif self.context.current_state == ConversationState.DEEPENING:
            # Переход к VALIDATING если все критичные завершены
            if progress.critical_completed:
                self.context.current_state = ConversationState.VALIDATING

        elif self.context.current_state == ConversationState.VALIDATING:
            # Переход к FINALIZING если можем остановиться
            if self.rp_manager.can_stop_interview(min_completion=0.8):
                self.context.current_state = ConversationState.FINALIZING

        logger.info(f"Conversation state: {self.context.current_state.value}")

    def _should_finalize(self) -> bool:
        """Нужно ли завершать интервью?"""
        # Финализируем если:
        # 1. В состоянии FINALIZING
        # 2. ИЛИ все критичные + важные завершены и общая полнота >= 80%
        # 3. ИЛИ задано слишком много вопросов (>25)

        if self.context.current_state == ConversationState.FINALIZING:
            return True

        progress = self.rp_manager.get_progress()

        if (progress.critical_completed and
            progress.important_completed and
            progress.overall_completion >= 0.8):
            return True

        if self.context.questions_asked > 25:
            logger.warning("Too many questions asked, force finalize")
            return True

        return False

    def _select_next_reference_point(self) -> Tuple[Optional[ReferencePoint], TransitionType]:
        """
        Выбрать следующий RP и тип перехода

        Returns:
            (ReferencePoint, TransitionType) или (None, TransitionType.FINALIZE)
        """
        # Проверить бюджет follow-ups
        remaining_follow_ups = self.context.get_remaining_follow_ups()

        # Логика выбора в зависимости от состояния
        if self.context.current_state == ConversationState.EXPLORING:
            # В режиме исследования: брать следующий незавершённый RP
            next_rp = self.rp_manager.get_next_reference_point(exclude_completed=True)
            if next_rp:
                return (next_rp, TransitionType.LINEAR)

        elif self.context.current_state == ConversationState.DEEPENING:
            # В режиме углубления: приоритет неполным критичным
            incomplete_critical = self.rp_manager.get_incomplete_critical_rps()

            if incomplete_critical and remaining_follow_ups > 0:
                # Взять первый неполный критичный
                return (incomplete_critical[0], TransitionType.DEEP_DIVE)
            else:
                # Критичные завершены, переходим к важным
                incomplete_important = self.rp_manager.get_incomplete_important_rps()
                if incomplete_important:
                    return (incomplete_important[0], TransitionType.LINEAR)

        elif self.context.current_state == ConversationState.VALIDATING:
            # В режиме валидации: проверить неполные критичные и важные
            incomplete_critical = self.rp_manager.get_incomplete_critical_rps()
            if incomplete_critical and remaining_follow_ups > 0:
                return (incomplete_critical[0], TransitionType.LOOP_BACK)

            incomplete_important = self.rp_manager.get_incomplete_important_rps()
            if incomplete_important and remaining_follow_ups > 0:
                return (incomplete_important[0], TransitionType.LOOP_BACK)

            # Все критичные и важные готовы - переходим к опциональным
            next_rp = self.rp_manager.get_next_reference_point(exclude_completed=True)
            if next_rp and remaining_follow_ups > 0:
                return (next_rp, TransitionType.LINEAR)

        # Нет следующего RP
        return (None, TransitionType.FINALIZE)

    def _get_transition_message(self, transition: TransitionType) -> str:
        """
        Получить сообщение для перехода

        Args:
            transition: Тип перехода

        Returns:
            Сообщение пользователю
        """
        messages = {
            TransitionType.LINEAR: "",  # Нет сообщения, просто следующий вопрос
            TransitionType.SKIP: "Отлично, переходим к следующему.",
            TransitionType.LOOP_BACK: "Давайте уточним один момент...",
            TransitionType.DEEP_DIVE: "Интересно! Расскажите подробнее:",
            TransitionType.FAST_FORWARD: "Супер! Вы дали очень полный ответ.",
            TransitionType.FINALIZE: ""
        }
        return messages.get(transition, "")

    def get_progress_message(self) -> str:
        """
        Получить сообщение о прогрессе

        Returns:
            Текстовое сообщение о прогрессе
        """
        progress = self.rp_manager.get_progress()

        # Процент
        percentage = int(progress.overall_completion * 100)

        # Прогресс-бар
        bar_length = 20
        filled = int(bar_length * progress.overall_completion)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Состояние блоков
        blocks = []
        if progress.critical_completed:
            blocks.append("✓ Критичная информация")
        else:
            blocks.append("→ Критичная информация")

        if progress.important_completed:
            blocks.append("✓ Важная информация")
        else:
            blocks.append("  Важная информация")

        # Оставшиеся вопросы
        remaining = self.context.get_remaining_follow_ups()

        message = f"""
[{bar}] {progress.completed_rps}/{progress.total_rps} разделов ({percentage}%)

{chr(10).join(blocks)}

Осталось уточняющих вопросов: {remaining}
"""
        return message

    def add_follow_up(self):
        """Отметить что задали follow-up вопрос"""
        self.context.follow_ups_asked += 1
        logger.info(f"Follow-ups: {self.context.follow_ups_asked}/{self.context.max_follow_ups}")

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в dict"""
        return {
            'state': self.context.current_state.value,
            'questions_asked': self.context.questions_asked,
            'follow_ups_asked': self.context.follow_ups_asked,
            'collected_data': self.context.collected_data,
            'covered_topics': self.context.covered_topics,
            'engagement': self.context.user_engagement_score,
            'quality': self.context.conversation_quality,
            'rp_manager': self.rp_manager.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationFlowManager':
        """Десериализация из dict"""
        rp_manager = ReferencePointManager.from_dict(data['rp_manager'])
        flow = cls(rp_manager)

        flow.context.current_state = ConversationState(data['state'])
        flow.context.questions_asked = data['questions_asked']
        flow.context.follow_ups_asked = data['follow_ups_asked']
        flow.context.collected_data = data['collected_data']
        flow.context.covered_topics = data['covered_topics']
        flow.context.user_engagement_score = data['engagement']
        flow.context.conversation_quality = data['quality']

        return flow


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Создать менеджер RP
    rp_manager = ReferencePointManager()
    rp_manager.load_fpg_reference_points()

    # Создать flow manager
    flow = ConversationFlowManager(rp_manager)

    print("=== Симуляция разговора ===\n")

    # Цикл разговора
    turn = 1
    while turn <= 20:
        print(f"\n--- Turn {turn} ---")

        # Решить следующее действие
        action = flow.decide_next_action()

        print(f"Action: {action['type']}")
        print(f"Transition: {action['transition'].value}")

        if action['type'] == 'finalize':
            print(f"\n{action['message']}")
            break

        # Показать вопрос
        rp = action['reference_point']
        print(f"\nRP: {rp.name}")
        if action.get('message'):
            print(f"Message: {action['message']}")

        # Симуляция ответа
        mock_answer = f"Это ответ на вопрос о {rp.name}. " * 5
        print(f"Answer: {mock_answer[:80]}...")

        # Обработать ответ
        next_action = flow.decide_next_action(last_answer=mock_answer)

        # Показать прогресс
        if turn % 5 == 0:
            print(flow.get_progress_message())

        turn += 1

    print("\n=== Финальный прогресс ===")
    print(flow.get_progress_message())
