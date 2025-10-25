#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic User Simulator - Генератор реалистичных ответов пользователя

Симулирует ответы российского грантозаявителя на вопросы интервьюера.
Поддерживает 3 уровня качества: low, medium, high.

Created: 2025-10-25
Iteration: 41 - Realistic Interview Simulation
"""

import logging
from typing import Dict, Optional
from shared.llm.unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)


class SyntheticUserSimulator:
    """
    Симулирует реалистичные ответы пользователя на вопросы интервьюера

    Используется для создания realistic interview datasets для:
    - Тестирования InteractiveInterviewer
    - Сбора данных для RL optimization
    - Генерации разнообразных анкет
    """

    # Регионы России для разнообразия
    REGIONS = [
        'Москва', 'Санкт-Петербург', 'Кемеровская область', 'Новосибирск',
        'Екатеринбург', 'Казань', 'Нижний Новгород', 'Красноярск',
        'Челябинск', 'Самара', 'Уфа', 'Ростов-на-Дону'
    ]

    # Темы/направления проектов
    TOPICS = [
        'молодёжь', 'культура', 'образование', 'спорт',
        'экология', 'волонтёрство', 'социальная поддержка',
        'наука', 'технологии', 'искусство'
    ]

    # Типы организаций
    ORG_TYPES = ['АНО', 'Фонд', 'Ассоциация', 'Центр', 'Клуб']

    def __init__(self, quality_level: str = 'medium', context: Optional[Dict] = None):
        """
        Инициализация симулятора

        Args:
            quality_level: Уровень качества ответов ('low', 'medium', 'high')
            context: Контекст проекта {region, topic, organization}
        """
        if quality_level not in ['low', 'medium', 'high']:
            raise ValueError(f"Invalid quality_level: {quality_level}. Must be 'low', 'medium', or 'high'")

        self.quality_level = quality_level
        self.context = context or {}

        # Инициализируем LLM
        self.llm = UnifiedLLMClient(
            provider='gigachat',
            model='GigaChat',
            temperature=self._get_temperature()
        )

        logger.info(f"[SyntheticUserSimulator] Initialized with quality_level={quality_level}, context={context}")

    def _get_temperature(self) -> float:
        """Возвращает temperature в зависимости от quality_level"""
        return {
            'low': 0.9,    # Более хаотичные ответы
            'medium': 0.7,  # Сбалансированные
            'high': 0.5     # Более точные и структурированные
        }[self.quality_level]

    def _get_max_tokens(self) -> int:
        """Возвращает max_tokens в зависимости от quality_level"""
        return {
            'low': 500,     # Короткие ответы
            'medium': 1500,  # Средние ответы
            'high': 3000    # Подробные ответы
        }[self.quality_level]

    def _get_detail_instruction(self) -> str:
        """Возвращает инструкцию по детализации ответа"""
        return {
            'low': '''Ответь КРАТКО и ПРОСТО (100-200 слов).
Используй общие фразы без конкретных примеров.
Не углубляйся в детали.
Ответ должен быть поверхностным.''',

            'medium': '''Ответь со СРЕДНЕЙ детализацией (200-400 слов).
Включи основные факты и 1-2 конкретных примера.
Структурируй ответ логически.
Баланс между краткостью и информативностью.''',

            'high': '''Ответь ПОДРОБНО и ДЕТАЛЬНО (400-800 слов).
Включи:
- Конкретные примеры и кейсы
- Цифры и статистику
- Детальное описание
- Обоснование каждого пункта
- Профессиональную терминологию'''
        }[self.quality_level]

    async def answer_question(self, question: str, field_name: str) -> str:
        """
        Генерирует реалистичный ответ на вопрос интервьюера

        Args:
            question: Вопрос от интервьюера
            field_name: Название поля (problem, solution, budget, etc.)

        Returns:
            Текстовый ответ пользователя
        """
        # Контекст проекта
        region = self.context.get('region', 'Москва')
        topic = self.context.get('topic', 'молодёжь')
        organization = self.context.get('organization', 'АНО "Развитие"')

        # Специальные инструкции для конкретных полей
        field_specific_instructions = {
            'project_name': 'Придумай краткое название (2-5 слов) для проекта в сфере "{topic}".',
            'organization': f'Укажи полное название организации (уже известно: {organization}).',
            'region': f'Укажи регион реализации проекта (уже известно: {region}).',
            'problem': 'Опиши социальную проблему, которую решает проект. Будь конкретным и используй статистику если можешь.',
            'solution': 'Опиши предлагаемое решение проблемы. Объясни КАК именно проект поможет.',
            'goals': 'Перечисли 3-5 конкретных целей проекта. Каждая цель должна быть измеримой.',
            'activities': 'Опиши 3-5 основных мероприятий проекта. Будь конкретным в датах и форматах.',
            'results': 'Опиши ожидаемые результаты проекта. Используй конкретные показатели (сколько человек, какие изменения).',
            'budget': 'Укажи общий бюджет проекта в рублях. Дай только число.',
            'budget_breakdown': 'Распредели бюджет по категориям (оборудование, зарплаты, материалы, прочее). Укажи суммы в рублях.'
        }

        field_instruction = field_specific_instructions.get(field_name, '')

        # Формируем промпт
        prompt = f"""Ты - представитель российской некоммерческой организации "{organization}".
Ты подаёшь заявку на грант для проекта в сфере "{topic}" в регионе "{region}".

Сейчас у тебя интервью с менеджером грантового фонда.

Вопрос менеджера:
"{question}"

{field_instruction}

{self._get_detail_instruction()}

ВАЖНО:
- Отвечай как РЕАЛЬНЫЙ заявитель российского гранта
- Используй профессиональную терминологию НКО-сектора
- Ссылайся на российскую специфику (законы, программы, реалии)
- Будь конкретным в цифрах и фактах
- Не придумывай несуществующие программы или организации

Твой ответ:"""

        try:
            # Генерируем ответ
            response = await self.llm.generate_text(
                prompt=prompt,
                max_tokens=self._get_max_tokens()
            )

            answer = response.strip()

            logger.info(f"[SyntheticUserSimulator] Generated answer for field={field_name}, quality={self.quality_level}, length={len(answer)} chars")

            return answer

        except Exception as e:
            logger.error(f"[SyntheticUserSimulator] Failed to generate answer: {e}")
            raise

    def get_context_summary(self) -> str:
        """Возвращает текстовое описание контекста"""
        return f"Region: {self.context.get('region', 'N/A')}, Topic: {self.context.get('topic', 'N/A')}, Org: {self.context.get('organization', 'N/A')}"


# Example usage:
if __name__ == "__main__":
    import asyncio

    async def test_simulator():
        """Тестируем симулятор"""
        context = {
            'region': 'Москва',
            'topic': 'молодёжь',
            'organization': 'АНО "Молодежные инициативы"'
        }

        simulator = SyntheticUserSimulator(
            quality_level='medium',
            context=context
        )

        question = "Опишите подробно проблему, которую решает ваш проект?"

        answer = await simulator.answer_question(question, field_name='problem')

        print(f"Question: {question}")
        print(f"Answer ({len(answer)} chars): {answer}")

    asyncio.run(test_simulator())
