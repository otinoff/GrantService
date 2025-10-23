#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reference Point Manager - Управление коллекцией Reference Points

Отвечает за:
- Определение следующего RP для работы
- Отслеживание прогресса
- Управление зависимостями
- Приоритизацию

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 1.0
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass, field

from .reference_point import (
    ReferencePoint,
    ReferencePointPriority,
    ReferencePointState,
    CompletionCriteria
)

logger = logging.getLogger(__name__)


@dataclass
class ReferencePointsProgress:
    """Прогресс по reference points"""
    total_rps: int = 0
    completed_rps: int = 0
    in_progress_rps: int = 0
    not_started_rps: int = 0
    overall_completion: float = 0.0  # 0-1
    critical_completed: bool = False  # Все P0 завершены?
    important_completed: bool = False  # Все P0+P1 завершены?

    def __repr__(self) -> str:
        return (f"Progress: {self.completed_rps}/{self.total_rps} "
                f"({self.overall_completion:.1%})")


class ReferencePointManager:
    """
    Менеджер коллекции Reference Points

    Управляет всеми RP для одного интервью, определяет:
    - Какой RP брать следующим
    - Завершён ли RP
    - Общий прогресс
    - Когда можно останавливаться

    Example:
        >>> manager = ReferencePointManager()
        >>> manager.load_fpg_reference_points()
        >>> next_rp = manager.get_next_reference_point()
        >>> manager.mark_completed(next_rp.id)
        >>> progress = manager.get_progress()
    """

    def __init__(self):
        """Инициализация менеджера"""
        self.reference_points: Dict[str, ReferencePoint] = {}
        self._rp_order: List[str] = []  # Порядок RPs

    def add_reference_point(self, rp: ReferencePoint):
        """
        Добавить reference point

        Args:
            rp: Reference point для добавления
        """
        if rp.id in self.reference_points:
            logger.warning(f"RP {rp.id} already exists, overwriting")

        self.reference_points[rp.id] = rp
        if rp.id not in self._rp_order:
            self._rp_order.append(rp.id)

        logger.info(f"Added RP: {rp.id} ({rp.name}) [P{rp.priority.value}]")

    def get_reference_point(self, rp_id: str) -> Optional[ReferencePoint]:
        """Получить RP по ID"""
        return self.reference_points.get(rp_id)

    def get_next_reference_point(
        self,
        exclude_completed: bool = True
    ) -> Optional[ReferencePoint]:
        """
        Определить следующий RP для работы

        Логика:
        1. Исключить заблокированные (зависимости не выполнены)
        2. Приоритизировать по P0 → P1 → P2 → P3
        3. Внутри приоритета: in_progress → not_started

        Args:
            exclude_completed: Исключить завершённые

        Returns:
            Следующий RP для работы или None
        """
        completed_ids = self.get_completed_rp_ids()

        # DEBUG: Логируем начало поиска
        logger.info(f"[get_next_reference_point] Searching for next RP...")
        logger.info(f"[get_next_reference_point] Total RPs: {len(self.reference_points)}, Completed IDs: {completed_ids}")

        candidates = []
        skipped_completed = 0
        skipped_blocked = 0

        for rp_id in self._rp_order:
            rp = self.reference_points[rp_id]

            # DEBUG: Подробное логирование для каждого RP
            logger.debug(f"[get_next_reference_point] Checking {rp_id}: "
                        f"state={rp.state.value}, is_complete={rp.is_complete()}, "
                        f"data_length={len(rp.collected_data)}")

            # Пропустить завершённые
            if exclude_completed and rp.is_complete():
                skipped_completed += 1
                logger.info(f"[get_next_reference_point] ❌ SKIPPED (completed): {rp_id} "
                           f"(state={rp.state.value}, data={len(rp.collected_data)} items)")
                continue

            # Пропустить заблокированные
            if rp.is_blocked(completed_ids):
                skipped_blocked += 1
                logger.info(f"[get_next_reference_point] ❌ SKIPPED (blocked): {rp_id}")
                continue

            logger.info(f"[get_next_reference_point] ✅ CANDIDATE: {rp_id}")
            candidates.append(rp)

        if not candidates:
            logger.error(f"[get_next_reference_point] ❌ NO CANDIDATES FOUND!")
            logger.error(f"  Total RPs: {len(self.reference_points)}")
            logger.error(f"  Skipped (completed): {skipped_completed}")
            logger.error(f"  Skipped (blocked): {skipped_blocked}")

            # DEBUG: Покажем состояние всех RP
            logger.error(f"  All RPs states:")
            for rp_id in self._rp_order[:5]:  # Первые 5 для дебага
                rp = self.reference_points[rp_id]
                logger.error(f"    {rp_id}: state={rp.state.value}, complete={rp.is_complete()}, "
                           f"data={list(rp.collected_data.keys())}")

            return None

        # Сортировка:
        # 1. По приоритету (меньше = важнее)
        # 2. По состоянию (in_progress > not_started)
        # 3. По обязательности (required > optional)
        def sort_key(rp: ReferencePoint) -> Tuple:
            state_priority = 0 if rp.state == ReferencePointState.IN_PROGRESS else 1
            required_priority = 0 if rp.required else 1
            return (rp.priority.value, state_priority, required_priority)

        candidates.sort(key=sort_key)

        next_rp = candidates[0]
        logger.info(f"Next RP: {next_rp.id} ({next_rp.name}) [P{next_rp.priority.value}]")

        return next_rp

    def mark_completed(self, rp_id: str, confidence: float = 1.0):
        """
        Отметить RP как завершённый

        Args:
            rp_id: ID reference point
            confidence: Уверенность в завершённости (0-1)
        """
        rp = self.reference_points.get(rp_id)
        if not rp:
            logger.error(f"RP {rp_id} not found")
            return

        rp.update_state(ReferencePointState.COMPLETED)
        rp.confidence_score = confidence

        logger.info(f"Completed: {rp.id} ({rp.name}) [confidence={confidence:.2f}]")

    def get_completed_rp_ids(self) -> List[str]:
        """Получить список ID завершённых RPs"""
        return [
            rp_id for rp_id, rp in self.reference_points.items()
            if rp.is_complete()
        ]

    def get_progress(self) -> ReferencePointsProgress:
        """
        Получить прогресс по всем RPs

        Returns:
            Объект с информацией о прогрессе
        """
        total = len(self.reference_points)
        completed = sum(1 for rp in self.reference_points.values() if rp.is_complete())
        in_progress = sum(1 for rp in self.reference_points.values()
                         if rp.state == ReferencePointState.IN_PROGRESS)
        not_started = sum(1 for rp in self.reference_points.values()
                         if rp.state == ReferencePointState.NOT_STARTED)

        # Проверить критичные и важные
        critical_rps = [rp for rp in self.reference_points.values()
                       if rp.priority == ReferencePointPriority.P0_CRITICAL]
        # SAFETY: all([]) возвращает True, но нам нужно False если список пуст!
        critical_completed = len(critical_rps) > 0 and all(rp.is_complete() for rp in critical_rps)

        important_rps = [rp for rp in self.reference_points.values()
                        if rp.priority in [ReferencePointPriority.P0_CRITICAL,
                                          ReferencePointPriority.P1_IMPORTANT]]
        # SAFETY: all([]) возвращает True, но нам нужно False если список пуст!
        important_completed = len(important_rps) > 0 and all(rp.is_complete() for rp in important_rps)

        # Общая завершённость
        overall = completed / total if total > 0 else 0.0

        return ReferencePointsProgress(
            total_rps=total,
            completed_rps=completed,
            in_progress_rps=in_progress,
            not_started_rps=not_started,
            overall_completion=overall,
            critical_completed=critical_completed,
            important_completed=important_completed
        )

    def can_stop_interview(self, min_completion: float = 0.8) -> bool:
        """
        Можно ли остановить интервью?

        Критерии:
        - Все P0 (критичные) завершены
        - Все P1 (важные) завершены
        - Общая завершённость >= min_completion

        Args:
            min_completion: Минимальная общая завершённость (0-1)

        Returns:
            True если можно останавливаться
        """
        progress = self.get_progress()

        if not progress.critical_completed:
            logger.info("Cannot stop: critical RPs not completed")
            return False

        if not progress.important_completed:
            logger.info("Cannot stop: important RPs not completed")
            return False

        if progress.overall_completion < min_completion:
            logger.info(f"Cannot stop: completion {progress.overall_completion:.1%} < {min_completion:.1%}")
            return False

        logger.info(f"Can stop interview: {progress}")
        return True

    def get_incomplete_critical_rps(self) -> List[ReferencePoint]:
        """Получить незавершённые критичные (P0) RPs"""
        return [
            rp for rp in self.reference_points.values()
            if rp.priority == ReferencePointPriority.P0_CRITICAL and not rp.is_complete()
        ]

    def get_incomplete_important_rps(self) -> List[ReferencePoint]:
        """Получить незавершённые важные (P1) RPs"""
        return [
            rp for rp in self.reference_points.values()
            if rp.priority == ReferencePointPriority.P1_IMPORTANT and not rp.is_complete()
        ]

    def load_fpg_reference_points(self):
        """
        Загрузить стандартный набор RP для ФПГ

        Основано на требованиях Фонда президентских грантов
        """
        # TIER 0: Критичные - без этого проект непонятен
        self.add_reference_point(ReferencePoint(
            id="rp_001_project_essence",
            name="Понять суть проекта",
            description="Получить чёткое понимание того, что делает проект",
            priority=ReferencePointPriority.P0_CRITICAL,
            required=True,
            completion_criteria=CompletionCriteria(
                min_length=100,
                required_keywords=["проект"]
            ),
            question_hints=[
                "Что конкретно делает ваш проект?",
                "В чём основная идея проекта?",
                "Какую главную задачу решает проект?"
            ],
            tags=["основа", "цель", "суть"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_002_problem",
            name="Определить проблему",
            description="Понять, какую социальную проблему решает проект",
            priority=ReferencePointPriority.P0_CRITICAL,
            required=True,
            completion_criteria=CompletionCriteria(
                min_length=100,
                required_keywords=["проблема"]
            ),
            question_hints=[
                "Какую проблему решает ваш проект?",
                "Почему эта проблема важна?",
                "Кого эта проблема затрагивает?"
            ],
            tags=["проблема", "актуальность"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_003_target_audience",
            name="Найти целевую аудиторию",
            description="Определить, кому помогает проект",
            priority=ReferencePointPriority.P0_CRITICAL,
            required=True,
            completion_criteria=CompletionCriteria(
                min_length=50,
                required_keywords=["аудитория", "группа", "люди", "дети", "подростки"]
            ),
            question_hints=[
                "Кто ваша целевая аудитория?",
                "Кому конкретно помогает проект?",
                "Сколько людей охватит проект?"
            ],
            tags=["целевая аудитория", "бенефициары"],
            grant_fund_specific="fpg"
        ))

        # TIER 1: Важные - нужно для оценки заявки
        self.add_reference_point(ReferencePoint(
            id="rp_004_methodology",
            name="Узнать методологию",
            description="Понять, КАК будет реализован проект",
            priority=ReferencePointPriority.P1_IMPORTANT,
            required=True,
            completion_criteria=CompletionCriteria(
                min_length=150,
                required_keywords=["метод", "шаг", "этап", "реализация"]
            ),
            depends_on=["rp_001_project_essence"],
            question_hints=[
                "Как вы планируете реализовать проект?",
                "Какие конкретные шаги предпримете?",
                "Какие методы будете использовать?"
            ],
            tags=["методология", "реализация", "план"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_005_budget",
            name="Оценить бюджет",
            description="Определить общий бюджет проекта",
            priority=ReferencePointPriority.P1_IMPORTANT,
            required=True,
            completion_criteria=CompletionCriteria(
                min_length=20,
                required_fields=["amount"]
            ),
            question_hints=[
                "Какой общий бюджет проекта?",
                "Сколько средств требуется?",
                "На какую сумму гранта рассчитываете?"
            ],
            tags=["бюджет", "финансы"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_006_budget_breakdown",
            name="Детализировать бюджет",
            description="Получить разбивку бюджета по статьям",
            priority=ReferencePointPriority.P1_IMPORTANT,
            required=True,
            depends_on=["rp_005_budget"],
            completion_criteria=CompletionCriteria(
                min_length=100,
                required_keywords=["статья", "расход", "затрат"]
            ),
            question_hints=[
                "Распределите бюджет по основным статьям",
                "На что пойдут деньги?",
                "Какие основные статьи расходов?"
            ],
            tags=["бюджет", "детализация"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_007_results",
            name="Определить результаты",
            description="Понять ожидаемые измеримые результаты",
            priority=ReferencePointPriority.P1_IMPORTANT,
            required=True,
            depends_on=["rp_001_project_essence", "rp_004_methodology"],
            completion_criteria=CompletionCriteria(
                min_length=100,
                required_keywords=["результат", "достиг", "получ"]
            ),
            question_hints=[
                "Какие конкретные результаты ожидаете?",
                "Как измерите успех проекта?",
                "Что изменится благодаря проекту?"
            ],
            tags=["результаты", "KPI", "эффективность"],
            grant_fund_specific="fpg"
        ))

        # TIER 2: Желательные - улучшают заявку
        self.add_reference_point(ReferencePoint(
            id="rp_008_team",
            name="Узнать команду",
            description="Понять состав команды проекта",
            priority=ReferencePointPriority.P2_DESIRABLE,
            required=False,
            completion_criteria=CompletionCriteria(
                min_length=80
            ),
            question_hints=[
                "Кто будет реализовывать проект?",
                "Опишите команду проекта",
                "Какие компетенции есть у команды?"
            ],
            tags=["команда", "люди", "компетенции"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_009_partners",
            name="Найти партнёров",
            description="Определить партнёров и поддержку",
            priority=ReferencePointPriority.P2_DESIRABLE,
            required=False,
            completion_criteria=CompletionCriteria(
                min_length=50
            ),
            question_hints=[
                "Есть ли у вас партнёры?",
                "Кто поддерживает проект?",
                "С кем планируете сотрудничать?"
            ],
            tags=["партнёры", "сотрудничество"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_010_risks",
            name="Оценить риски",
            description="Понять возможные риски проекта",
            priority=ReferencePointPriority.P2_DESIRABLE,
            required=False,
            completion_criteria=CompletionCriteria(
                min_length=80
            ),
            question_hints=[
                "Какие риски видите?",
                "Что может помешать проекту?",
                "Как будете снижать риски?"
            ],
            tags=["риски", "препятствия"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_011_sustainability",
            name="Проверить устойчивость",
            description="Понять, как проект будет существовать после гранта",
            priority=ReferencePointPriority.P2_DESIRABLE,
            required=False,
            depends_on=["rp_007_results"],
            completion_criteria=CompletionCriteria(
                min_length=80
            ),
            question_hints=[
                "Что будет после окончания гранта?",
                "Как проект продолжит работу?",
                "Есть ли план развития?"
            ],
            tags=["устойчивость", "развитие"],
            grant_fund_specific="fpg"
        ))

        # TIER 3: Опциональные
        self.add_reference_point(ReferencePoint(
            id="rp_012_geography",
            name="Уточнить географию",
            description="Где будет реализован проект",
            priority=ReferencePointPriority.P3_OPTIONAL,
            required=False,
            completion_criteria=CompletionCriteria(
                min_length=20
            ),
            question_hints=[
                "Где будет реализован проект?",
                "В каком регионе?",
                "На какую территорию рассчитан?"
            ],
            tags=["география", "регион"],
            grant_fund_specific="fpg"
        ))

        self.add_reference_point(ReferencePoint(
            id="rp_013_timeline",
            name="Определить сроки",
            description="Когда и как долго реализуется проект",
            priority=ReferencePointPriority.P3_OPTIONAL,
            required=False,
            depends_on=["rp_004_methodology"],
            completion_criteria=CompletionCriteria(
                min_length=30
            ),
            question_hints=[
                "Сколько времени займёт проект?",
                "Какие сроки реализации?",
                "За сколько месяцев планируете?"
            ],
            tags=["сроки", "timeline"],
            grant_fund_specific="fpg"
        ))

        logger.info(f"Loaded {len(self.reference_points)} FPG reference points")

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в dict"""
        return {
            'reference_points': {
                rp_id: rp.to_dict() for rp_id, rp in self.reference_points.items()
            },
            'rp_order': self._rp_order,
            'progress': self.get_progress().__dict__
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReferencePointManager':
        """Десериализация из dict"""
        manager = cls()

        # Восстановить RPs
        for rp_id, rp_data in data.get('reference_points', {}).items():
            rp = ReferencePoint.from_dict(rp_data)
            manager.reference_points[rp_id] = rp

        manager._rp_order = data.get('rp_order', [])

        return manager


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Создать менеджер и загрузить ФПГ reference points
    manager = ReferencePointManager()
    manager.load_fpg_reference_points()

    # Посмотреть прогресс
    progress = manager.get_progress()
    print(f"\nInitial progress: {progress}")

    # Получить следующий RP
    next_rp = manager.get_next_reference_point()
    print(f"\nNext RP: {next_rp}")

    # Симуляция работы: отметить как завершённый
    next_rp.add_data('text', 'Наш проект создаёт инклюзивные пространства для детей с ОВЗ')
    manager.mark_completed(next_rp.id, confidence=0.9)

    # Ещё один
    next_rp = manager.get_next_reference_point()
    print(f"\nNext RP: {next_rp}")

    next_rp.add_data('text', 'Основная проблема - отсутствие доступных инклюзивных пространств в регионе')
    manager.mark_completed(next_rp.id, confidence=0.85)

    # Прогресс
    progress = manager.get_progress()
    print(f"\nProgress: {progress}")

    # Можно ли остановиться?
    can_stop = manager.can_stop_interview(min_completion=0.8)
    print(f"\nCan stop: {can_stop}")

    # Незавершённые критичные
    incomplete = manager.get_incomplete_critical_rps()
    print(f"\nIncomplete critical RPs: {[rp.name for rp in incomplete]}")
