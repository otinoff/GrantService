#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reference Points Framework - адаптивная система интервьюирования

Вместо жестких вопросов используются опорные точки (reference points),
которые определяют ЧТО нужно узнать, а не КАК спрашивать.

Author: Grant Service Architect Agent
Created: 2025-10-21
Version: 1.0
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class Priority(Enum):
    """Приоритет reference point"""
    P0 = 0  # Критично - обязательно
    P1 = 1  # Важно - сильно желательно
    P2 = 2  # Желательно
    P3 = 3  # Опционально


class ConversationState(Enum):
    """Состояния диалога"""
    INIT = "init"               # Приветствие
    EXPLORING = "exploring"     # Исследование базовых RP
    DEEPENING = "deepening"     # Углубление (неполные критичные RP)
    VALIDATING = "validating"   # Валидация собранной информации
    FINALIZING = "finalizing"   # Завершение


class TransitionType(Enum):
    """Типы переходов между вопросами"""
    FIRST_TOUCH = "first_touch"      # Первое касание темы
    DEEP_DIVE = "deep_dive"          # Углубление в тему
    LOOP_BACK = "loop_back"          # Возврат к неполной теме
    VALIDATION = "validation"        # Проверка понимания
    NATURAL_FLOW = "natural_flow"    # Естественный переход


class UserExpertiseLevel(Enum):
    """Уровень экспертизы пользователя"""
    BEGINNER = "beginner"           # Новичок в грантах
    INTERMEDIATE = "intermediate"   # Имеет опыт
    EXPERT = "expert"              # Эксперт


class ProjectType(Enum):
    """Типы проектов"""
    SOCIAL = "social"             # Социальный
    CULTURAL = "cultural"         # Культурный
    EDUCATIONAL = "educational"   # Образовательный
    SCIENTIFIC = "scientific"     # Научный
    SPORTS = "sports"            # Спортивный
    UNKNOWN = "unknown"          # Неизвестно (еще не определен)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ReferencePoint:
    """
    Опорная точка - цель, которую нужно достичь в интервью

    Не содержит жесткий вопрос, а описывает ЧТО нужно узнать.
    Вопросы генерируются динамически на основе контекста.
    """
    id: str                          # Уникальный ID
    name: str                        # Название (для людей)
    priority: Priority               # Приоритет P0-P3
    required: bool = True            # Обязательно ли?

    # Связанные поля анкеты
    related_fields: List[str] = field(default_factory=list)

    # Подсказки для генерации вопросов
    question_hints: List[str] = field(default_factory=list)

    # Критерии завершенности
    completion_criteria: Dict[str, Any] = field(default_factory=dict)

    # Собранные данные
    collected_data: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False

    def mark_complete(self, data: Dict[str, Any]):
        """Отметить как завершенный"""
        self.collected_data = data
        self.is_complete = True

    def get_completeness_score(self) -> float:
        """Оценить полноту (0.0 - 1.0)"""
        if not self.collected_data:
            return 0.0

        # Простая эвристика: проверяем заполненность related_fields
        if not self.related_fields:
            return 1.0 if self.collected_data else 0.0

        filled = sum(1 for field in self.related_fields
                    if field in self.collected_data and self.collected_data[field])
        return filled / len(self.related_fields)


@dataclass
class ConversationContext:
    """Контекст разговора"""
    current_state: ConversationState = ConversationState.INIT
    covered_topics: List[str] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Метрики
    questions_asked: int = 0
    follow_ups_asked: int = 0

    def add_turn(self, question: str, answer: str, rp_id: str = None):
        """Добавить диалоговый ход"""
        self.conversation_history.append({
            'question': question,
            'answer': answer,
            'rp_id': rp_id
        })
        self.questions_asked += 1

        if rp_id and rp_id not in self.covered_topics:
            self.covered_topics.append(rp_id)


# =============================================================================
# MANAGERS
# =============================================================================

class ReferencePointManager:
    """
    Управляет Reference Points

    Responsibilities:
    - Хранение и загрузка RP
    - Определение следующего RP для вопроса
    - Оценка общей полноты
    """

    def __init__(self):
        self.reference_points: Dict[str, ReferencePoint] = {}

    def load_fpg_reference_points(self):
        """Загрузить Reference Points для ФПГ"""
        # P0 - Критичные
        self.add_reference_point(ReferencePoint(
            id="understand_essence",
            name="Понять суть проекта",
            priority=Priority.P0,
            required=True,
            related_fields=['project_name', 'project_goal', 'project_description'],
            question_hints=[
                "Расскажите о вашем проекте...",
                "В чем суть вашей идеи?",
                "Что вы хотите сделать?"
            ],
            completion_criteria={
                'min_length': 50,
                'has_name': True,
                'has_goal': True
            }
        ))

        self.add_reference_point(ReferencePoint(
            id="identify_problem",
            name="Определить проблему",
            priority=Priority.P0,
            required=True,
            related_fields=['problem_description', 'problem_severity'],
            question_hints=[
                "Какую проблему решает ваш проект?",
                "Почему это важно?",
                "Что произойдет, если проблема не будет решена?"
            ],
            completion_criteria={
                'min_length': 50,
                'has_specifics': True
            }
        ))

        self.add_reference_point(ReferencePoint(
            id="find_target_audience",
            name="Найти целевую аудиторию",
            priority=Priority.P0,
            required=True,
            related_fields=['target_audience', 'beneficiaries_count'],
            question_hints=[
                "Кто ваша целевая аудитория?",
                "Кому поможет проект?",
                "Сколько человек получат пользу?"
            ],
            completion_criteria={
                'min_length': 30,
                'is_specific': True
            }
        ))

        # P1 - Важные
        self.add_reference_point(ReferencePoint(
            id="understand_methodology",
            name="Узнать методологию реализации",
            priority=Priority.P1,
            required=True,
            related_fields=['methodology', 'tasks', 'timeline'],
            question_hints=[
                "Как вы планируете реализовать проект?",
                "Какие конкретные шаги будете делать?",
                "Какие мероприятия запланированы?"
            ],
            completion_criteria={
                'min_length': 100,
                'has_steps': True
            }
        ))

        self.add_reference_point(ReferencePoint(
            id="assess_budget",
            name="Оценить бюджет",
            priority=Priority.P1,
            required=True,
            related_fields=['budget_total', 'budget_breakdown'],
            question_hints=[
                "Какой бюджет требуется?",
                "Как распределены средства?",
                "На что пойдут деньги?"
            ],
            completion_criteria={
                'has_total': True,
                'has_breakdown': True
            }
        ))

        self.add_reference_point(ReferencePoint(
            id="understand_team",
            name="Понять команду",
            priority=Priority.P1,
            required=False,
            related_fields=['team_description', 'team_experience'],
            question_hints=[
                "Кто будет реализовывать проект?",
                "Какой у вас опыт?",
                "Кто ваши партнеры?"
            ],
            completion_criteria={
                'min_length': 30
            }
        ))

        # P2 - Желательные
        self.add_reference_point(ReferencePoint(
            id="identify_risks",
            name="Выявить риски",
            priority=Priority.P2,
            required=True,
            related_fields=['risks', 'mitigation'],
            question_hints=[
                "Какие риски видите?",
                "Что может пойти не так?",
                "Как будете минимизировать риски?"
            ],
            completion_criteria={
                'min_length': 30
            }
        ))

        self.add_reference_point(ReferencePoint(
            id="assess_sustainability",
            name="Оценить устойчивость",
            priority=Priority.P2,
            required=True,
            related_fields=['sustainability', 'future_plans'],
            question_hints=[
                "Что будет после окончания гранта?",
                "Как проект будет развиваться дальше?",
                "Планируете ли масштабирование?"
            ],
            completion_criteria={
                'min_length': 30
            }
        ))

        logger.info(f"✅ Loaded {len(self.reference_points)} reference points for FPG")

    def add_reference_point(self, rp: ReferencePoint):
        """Добавить reference point"""
        self.reference_points[rp.id] = rp

    def get_next_priority_rp(self, context: ConversationContext) -> Optional[ReferencePoint]:
        """
        Получить следующий приоритетный RP

        Логика:
        1. P0 неполные (required)
        2. P1 неполные (required)
        3. P2 неполные (required)
        4. P1/P2 опциональные
        """
        # Сортировать по приоритету
        sorted_rps = sorted(
            self.reference_points.values(),
            key=lambda rp: (rp.priority.value, not rp.required)
        )

        # Найти первый неполный
        for rp in sorted_rps:
            if not rp.is_complete and rp.id not in context.covered_topics:
                return rp

        # Все основные покрыты - вернуть None (завершение)
        return None

    def get_overall_completeness(self) -> float:
        """Общая полнота (0.0 - 1.0)"""
        if not self.reference_points:
            return 0.0

        scores = [rp.get_completeness_score() for rp in self.reference_points.values()]
        return sum(scores) / len(scores)


class ConversationFlowManager:
    """
    Управляет потоком разговора

    Responsibilities:
    - Определение текущего состояния
    - Решение о следующем действии
    - Transitions между состояниями
    """

    def __init__(self, rp_manager: ReferencePointManager):
        self.rp_manager = rp_manager
        self.context = ConversationContext()

    def decide_next_action(self, last_answer: Optional[str] = None) -> Dict[str, Any]:
        """
        Решить что делать дальше

        Returns:
            {
                'type': 'ask' | 'finalize',
                'reference_point': ReferencePoint | None,
                'transition': TransitionType,
                'message': str (переходное сообщение)
            }
        """
        # Обновить состояние
        self._update_state()

        # Проверить условия завершения
        if self._should_finalize():
            return {
                'type': 'finalize',
                'reference_point': None,
                'transition': TransitionType.NATURAL_FLOW,
                'message': self._get_finalization_message()
            }

        # Получить следующий RP
        next_rp = self.rp_manager.get_next_priority_rp(self.context)

        if not next_rp:
            # Все покрыто - завершить
            return {
                'type': 'finalize',
                'reference_point': None,
                'transition': TransitionType.NATURAL_FLOW,
                'message': "Отлично! Я собрал достаточно информации."
            }

        # Определить тип перехода
        transition = self._get_transition_type(next_rp, last_answer)

        # Сообщение перехода
        transition_msg = self._get_transition_message(transition, next_rp)

        return {
            'type': 'ask',
            'reference_point': next_rp,
            'transition': transition,
            'message': transition_msg
        }

    def _update_state(self):
        """Обновить состояние диалога"""
        completeness = self.rp_manager.get_overall_completeness()

        if self.context.questions_asked == 0:
            self.context.current_state = ConversationState.INIT
        elif completeness < 0.3:
            self.context.current_state = ConversationState.EXPLORING
        elif completeness < 0.7:
            self.context.current_state = ConversationState.DEEPENING
        elif completeness < 0.9:
            self.context.current_state = ConversationState.VALIDATING
        else:
            self.context.current_state = ConversationState.FINALIZING

    def _should_finalize(self) -> bool:
        """Проверить нужно ли завершать"""
        # Все P0 заполнены?
        p0_complete = all(
            rp.is_complete or rp.id in self.context.covered_topics
            for rp in self.rp_manager.reference_points.values()
            if rp.priority == Priority.P0 and rp.required
        )

        # Макс вопросов
        if self.context.questions_asked >= 20:
            return True

        # P0 + 80% P1
        if p0_complete:
            p1_complete = sum(
                1 for rp in self.rp_manager.reference_points.values()
                if rp.priority == Priority.P1 and rp.required and
                   (rp.is_complete or rp.id in self.context.covered_topics)
            )
            p1_total = sum(
                1 for rp in self.rp_manager.reference_points.values()
                if rp.priority == Priority.P1 and rp.required
            )

            if p1_total > 0 and p1_complete / p1_total >= 0.8:
                return True

        return False

    def _get_transition_type(
        self,
        next_rp: ReferencePoint,
        last_answer: Optional[str]
    ) -> TransitionType:
        """Определить тип перехода"""
        if next_rp.id in self.context.covered_topics:
            return TransitionType.LOOP_BACK

        if self.context.questions_asked == 0:
            return TransitionType.FIRST_TOUCH

        if next_rp.priority.value <= 1:
            return TransitionType.DEEP_DIVE

        return TransitionType.NATURAL_FLOW

    def _get_transition_message(
        self,
        transition: TransitionType,
        rp: ReferencePoint
    ) -> str:
        """Получить сообщение перехода"""
        if transition == TransitionType.FIRST_TOUCH:
            return ""  # Без перехода, сразу вопрос

        if transition == TransitionType.LOOP_BACK:
            return "Давайте вернемся к этому вопросу и уточним детали."

        if transition == TransitionType.DEEP_DIVE:
            return "Хорошо, теперь давайте поговорим подробнее."

        return ""

    def _get_finalization_message(self) -> str:
        """Сообщение завершения"""
        return (
            "Отлично! Спасибо за подробные ответы. "
            "Я собрал достаточно информации о вашем проекте."
        )

    def add_follow_up(self):
        """Отметить уточняющий вопрос"""
        self.context.follow_ups_asked += 1

    def get_progress_message(self) -> str:
        """Сообщение о прогрессе"""
        completeness = self.rp_manager.get_overall_completeness()
        percent = int(completeness * 100)

        return (
            f"📊 Прогресс интервью: {percent}%\n"
            f"Задано вопросов: {self.context.questions_asked}\n"
            f"Уточнений: {self.context.follow_ups_asked}"
        )


class AdaptiveQuestionGenerator:
    """
    Генерирует адаптивные вопросы на основе:
    - Reference Point (что узнать)
    - Context (что уже знаем)
    - User level (кто отвечает)
    - Qdrant (база знаний ФПГ)
    """

    def __init__(
        self,
        llm_client,
        qdrant_client=None,
        qdrant_collection: str = "knowledge_sections"
    ):
        self.llm = llm_client
        self.qdrant = qdrant_client
        self.qdrant_collection = qdrant_collection

    async def generate_question(
        self,
        reference_point: ReferencePoint,
        conversation_context: Dict[str, Any],
        user_level: UserExpertiseLevel = UserExpertiseLevel.INTERMEDIATE,
        project_type: ProjectType = ProjectType.UNKNOWN
    ) -> str:
        """
        Сгенерировать адаптивный вопрос

        Args:
            reference_point: RP для которого генерируем вопрос
            conversation_context: Контекст разговора
            user_level: Уровень пользователя
            project_type: Тип проекта

        Returns:
            Сгенерированный вопрос
        """
        # Fallback: использовать hints из RP
        if not self.llm:
            logger.warning("LLM not available, using hint")
            return reference_point.question_hints[0] if reference_point.question_hints else \
                   f"Расскажите о: {reference_point.name}"

        # Получить контекст из Qdrant (опционально)
        fpg_context = ""
        if self.qdrant:
            fpg_context = await self._get_fpg_context(reference_point)

        # Сформировать prompt
        prompt = self._build_prompt(
            reference_point,
            conversation_context,
            user_level,
            project_type,
            fpg_context
        )

        # Генерация через LLM
        try:
            question = await self.llm.generate_async(prompt)
            return question.strip()
        except Exception as e:
            logger.error(f"Failed to generate question: {e}")
            # Fallback
            return reference_point.question_hints[0] if reference_point.question_hints else \
                   f"Расскажите подробнее о: {reference_point.name}"

    async def _get_fpg_context(self, rp: ReferencePoint) -> str:
        """Получить релевантный контекст из Qdrant"""
        # TODO: Implement Qdrant search
        return ""

    def _build_prompt(
        self,
        rp: ReferencePoint,
        context: Dict[str, Any],
        user_level: UserExpertiseLevel,
        project_type: ProjectType,
        fpg_context: str
    ) -> str:
        """Построить prompt для LLM"""
        # История разговора (последние 3 обмена)
        history = context.get('conversation_history', [])[-3:]
        history_text = "\n".join([
            f"Q: {turn.get('question', '')}\nA: {turn.get('answer', '')}"
            for turn in history
        ])

        prompt = f"""Ты - эксперт по грантовым заявкам ФПГ, проводящий интервью.

ЦЕЛЬ: {rp.name}

КОНТЕКСТ ПРОЕКТА:
- Тип: {project_type.value}
- Уровень заявителя: {user_level.value}

ЧТО УЖЕ ОБСУДИЛИ:
{history_text if history_text else "Это первый вопрос"}

ЗАДАЧА: Сформулируй ЕСТЕСТВЕННЫЙ вопрос, который:
1. Поможет достичь цели: "{rp.name}"
2. Учитывает предыдущий контекст беседы
3. Адаптирован под уровень человека
4. Не дублирует то, что уже обсуждалось

ВАЖНО:
- Говори как живой человек, а не как форма
- Используй "вы" (уважительно)
- Один вопрос, не более 2-3 предложений
- Без вступлений, сразу вопрос

ВОПРОС:"""

        return prompt


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("Reference Points Framework - Тестирование")
    print("=" * 80)

    # Создать менеджер
    rp_manager = ReferencePointManager()
    rp_manager.load_fpg_reference_points()

    print(f"\n✅ Загружено {len(rp_manager.reference_points)} reference points")

    # Показать по приоритетам
    for priority in Priority:
        rps = [rp for rp in rp_manager.reference_points.values()
               if rp.priority == priority]
        print(f"\n{priority.name} ({len(rps)}):")
        for rp in rps:
            required = "✓" if rp.required else "○"
            print(f"  {required} {rp.name}")

    # Тест flow manager
    print("\n" + "=" * 80)
    print("Conversation Flow Manager - Тестирование")
    print("=" * 80)

    flow_manager = ConversationFlowManager(rp_manager)

    # Симуляция 3 шагов
    for i in range(3):
        action = flow_manager.decide_next_action()
        print(f"\n--- Turn {i+1} ---")
        print(f"Action: {action['type']}")
        if action['reference_point']:
            rp = action['reference_point']
            print(f"RP: {rp.name} (P{rp.priority.value})")
            print(f"Transition: {action['transition'].value}")

            # Отметить как покрытый
            flow_manager.context.add_turn(
                question="Тестовый вопрос",
                answer="Тестовый ответ",
                rp_id=rp.id
            )
            rp.mark_complete({'test': 'data'})

    print("\n" + "=" * 80)
    print("✅ Тестирование завершено")
    print("=" * 80)
