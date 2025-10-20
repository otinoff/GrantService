#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive Question Generator - Генератор контекстно-зависимых вопросов

НЕ использует жёсткие шаблоны!
Генерирует вопросы на основе:
- Reference Point (что узнать)
- Контекста разговора (что уже известно)
- Уровня пользователя (новичок/эксперт)
- Базы знаний ФПГ (Qdrant)

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 1.0
"""

from typing import Dict, Any, List, Optional
import logging
from enum import Enum

from .reference_point import ReferencePoint

logger = logging.getLogger(__name__)


class UserExpertiseLevel(Enum):
    """Уровень экспертизы пользователя"""
    NOVICE = "novice"           # Новичок - никогда не писал заявки
    INTERMEDIATE = "intermediate"  # Средний - есть опыт
    EXPERT = "expert"           # Эксперт - много заявок


class ProjectType(Enum):
    """Тип проекта (классификация)"""
    SOCIAL = "social"              # Социальный проект
    EDUCATIONAL = "educational"    # Образовательный
    CULTURAL = "cultural"          # Культурный
    SPORTS = "sports"              # Спортивный
    HEALTHCARE = "healthcare"      # Здравоохранение
    ENVIRONMENT = "environment"    # Экология
    UNKNOWN = "unknown"            # Неопределён


class AdaptiveQuestionGenerator:
    """
    Генератор адаптивных вопросов

    Использует LLM для генерации вопросов на основе контекста.
    НЕ полагается на жёсткие шаблоны!

    Example:
        >>> gen = AdaptiveQuestionGenerator(llm_client, qdrant_client)
        >>> question = await gen.generate_question(
        ...     reference_point=rp,
        ...     conversation_context=context,
        ...     user_level=UserExpertiseLevel.NOVICE
        ... )
    """

    def __init__(
        self,
        llm_client: Any,  # UnifiedLLMClient
        qdrant_client: Optional[Any] = None,  # QdrantClient
        qdrant_collection: str = "knowledge_sections"
    ):
        """
        Инициализация генератора

        Args:
            llm_client: LLM клиент для генерации
            qdrant_client: Qdrant клиент для контекста (optional)
            qdrant_collection: Название коллекции в Qdrant
        """
        self.llm = llm_client
        self.qdrant = qdrant_client
        self.collection_name = qdrant_collection

    async def generate_question(
        self,
        reference_point: ReferencePoint,
        conversation_context: Dict[str, Any],
        user_level: UserExpertiseLevel = UserExpertiseLevel.INTERMEDIATE,
        project_type: ProjectType = ProjectType.UNKNOWN
    ) -> str:
        """
        Сгенерировать вопрос для данного Reference Point

        Args:
            reference_point: RP для которого генерируем вопрос
            conversation_context: Контекст разговора (что уже известно)
            user_level: Уровень экспертизы пользователя
            project_type: Тип проекта (если известен)

        Returns:
            Сгенерированный вопрос
        """
        # 1. Проверить, не был ли уже ответ (skip logic)
        if self._already_covered(reference_point, conversation_context):
            logger.info(f"RP {reference_point.id} already covered, skipping")
            return None

        # 2. Классифицировать тип проекта (если ещё не известен)
        if project_type == ProjectType.UNKNOWN:
            project_type = self._classify_project_type(conversation_context)

        # 3. Оценить уровень пользователя (если не передан)
        if user_level == UserExpertiseLevel.INTERMEDIATE:
            user_level = self._assess_user_level(conversation_context)

        # 4. Получить контекст из Qdrant (база ФПГ)
        fpg_context = await self._get_fpg_context(reference_point, project_type)

        # 5. Определить пробелы в информации
        gaps = self._identify_information_gaps(reference_point, conversation_context)

        # 6. Сгенерировать вопрос с помощью LLM
        question = await self._llm_generate_question(
            reference_point=reference_point,
            conversation_context=conversation_context,
            user_level=user_level,
            project_type=project_type,
            fpg_context=fpg_context,
            gaps=gaps
        )

        return question

    def _already_covered(
        self,
        reference_point: ReferencePoint,
        context: Dict[str, Any]
    ) -> bool:
        """
        Проверить, уже ли был ответ на этот RP

        Args:
            reference_point: RP для проверки
            context: Контекст разговора

        Returns:
            True если информация уже есть
        """
        # Проверить по тегам RP
        for tag in reference_point.tags:
            if tag in context.get('covered_topics', []):
                return True

        # Проверить по имени поля
        field_name = reference_point.id.split('_', 2)[-1]  # rp_001_project_essence -> project_essence
        if field_name in context.get('collected_fields', {}):
            return True

        return False

    def _classify_project_type(self, context: Dict[str, Any]) -> ProjectType:
        """
        Классифицировать тип проекта

        Args:
            context: Контекст разговора

        Returns:
            Тип проекта
        """
        # Простая эвристика на основе ключевых слов
        text = ' '.join([
            str(context.get('project_essence', '')),
            str(context.get('problem', '')),
            str(context.get('target_audience', ''))
        ]).lower()

        if any(word in text for word in ['образование', 'обучение', 'школ', 'студент']):
            return ProjectType.EDUCATIONAL
        elif any(word in text for word in ['культур', 'искусство', 'музей', 'театр']):
            return ProjectType.CULTURAL
        elif any(word in text for word in ['спорт', 'физкультур', 'соревнован']):
            return ProjectType.SPORTS
        elif any(word in text for word in ['здоровье', 'медицин', 'лечение', 'терапи']):
            return ProjectType.HEALTHCARE
        elif any(word in text for word in ['эколог', 'природ', 'окружающ']):
            return ProjectType.ENVIRONMENT
        elif any(word in text for word in ['социальн', 'помощ', 'поддержк', 'включени']):
            return ProjectType.SOCIAL

        return ProjectType.UNKNOWN

    def _assess_user_level(self, context: Dict[str, Any]) -> UserExpertiseLevel:
        """
        Оценить уровень экспертизы пользователя

        Критерии:
        - Длина ответов
        - Использование профессиональной терминологии
        - Структурированность ответов

        Args:
            context: Контекст разговора

        Returns:
            Уровень пользователя
        """
        # Средняя длина ответов
        answers = [v for k, v in context.items() if isinstance(v, str)]
        if not answers:
            return UserExpertiseLevel.NOVICE

        avg_length = sum(len(a) for a in answers) / len(answers)

        # Профессиональные термины
        professional_terms = [
            'методология', 'бенефициар', 'индикатор', 'критерий',
            'мониторинг', 'оценка', 'эффективность', 'реализация'
        ]
        text = ' '.join(answers).lower()
        term_count = sum(1 for term in professional_terms if term in text)

        # Оценка
        if avg_length > 200 and term_count >= 3:
            return UserExpertiseLevel.EXPERT
        elif avg_length > 100 and term_count >= 1:
            return UserExpertiseLevel.INTERMEDIATE
        else:
            return UserExpertiseLevel.NOVICE

    async def _get_fpg_context(
        self,
        reference_point: ReferencePoint,
        project_type: ProjectType
    ) -> str:
        """
        Получить контекст из базы знаний ФПГ (Qdrant)

        Args:
            reference_point: RP для контекста
            project_type: Тип проекта

        Returns:
            Релевантный контекст из базы ФПГ
        """
        if not self.qdrant:
            return ""

        try:
            # Поисковый запрос
            query_parts = [
                reference_point.name,
                project_type.value if project_type != ProjectType.UNKNOWN else "",
                "ФПГ требования"
            ]
            query = ' '.join([p for p in query_parts if p])

            # Поиск в Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_text=query,
                limit=2
            )

            if not results:
                return ""

            # Взять топ-1 результат
            top_result = results[0]
            context = top_result.payload.get('content', '')

            # Извлечь ключевой момент (первые 500 символов)
            return context[:500] if len(context) > 500 else context

        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return ""

    def _identify_information_gaps(
        self,
        reference_point: ReferencePoint,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Определить пробелы в информации для данного RP

        Args:
            reference_point: RP для анализа
            context: Контекст разговора

        Returns:
            Список пробелов (что не хватает)
        """
        gaps = []

        # Проверить критерии завершённости
        if reference_point.completion_criteria.required_keywords:
            text = ' '.join([str(v) for v in context.values() if isinstance(v, str)]).lower()
            for keyword in reference_point.completion_criteria.required_keywords:
                if keyword.lower() not in text:
                    gaps.append(f"Отсутствует: {keyword}")

        if reference_point.completion_criteria.required_fields:
            for field in reference_point.completion_criteria.required_fields:
                if field not in context:
                    gaps.append(f"Не заполнено поле: {field}")

        return gaps

    async def _llm_generate_question(
        self,
        reference_point: ReferencePoint,
        conversation_context: Dict[str, Any],
        user_level: UserExpertiseLevel,
        project_type: ProjectType,
        fpg_context: str,
        gaps: List[str]
    ) -> str:
        """
        Сгенерировать вопрос с помощью LLM

        Args:
            reference_point: RP для генерации
            conversation_context: Контекст разговора
            user_level: Уровень пользователя
            project_type: Тип проекта
            fpg_context: Контекст из базы ФПГ
            gaps: Пробелы в информации

        Returns:
            Сгенерированный вопрос
        """
        # Системный промпт
        system_prompt = """Ты - эксперт по грантам Фонда президентских грантов (ФПГ).

Твоя задача - задать ОДИН уточняющий вопрос, чтобы получить нужную информацию о проекте.

ВАЖНО:
- Вопрос должен быть естественным, не шаблонным
- Адаптируй формулировку под уровень пользователя
- Используй контекст предыдущих ответов
- Не дублируй уже заданные вопросы
- Будь конкретным и понятным

Стиль:
- Для новичков: простые вопросы с подсказками
- Для экспертов: профессиональные термины, краткость
"""

        # Пользовательский промпт
        user_prompt = f"""# Задача
Нужно узнать: {reference_point.name}
Описание: {reference_point.description}

# Контекст проекта
{self._format_context(conversation_context)}

# Уровень пользователя
{user_level.value}

# Тип проекта
{project_type.value}

# Что уже собрано
{self._format_collected_data(conversation_context)}

# Пробелы в информации
{gaps if gaps else "Нет явных пробелов"}

# Контекст ФПГ
{fpg_context if fpg_context else "Нет специфичных требований"}

# Примеры вопросов (можешь использовать как референс, но НЕ КОПИРУЙ)
{reference_point.question_hints}

Сгенерируй ОДИН вопрос, который поможет получить нужную информацию.
Вопрос должен быть естественным и учитывать весь контекст.

Верни ТОЛЬКО текст вопроса, без комментариев."""

        try:
            # Вызов LLM - UnifiedLLMClient использует generate_async с единым промптом
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = await self.llm.generate_async(
                prompt=full_prompt,
                temperature=0.7  # Креативность
            )

            question = response.strip()

            # Валидация
            if not question or len(question) < 10:
                logger.warning("Generated question too short, using fallback")
                return self._fallback_question(reference_point)

            logger.info(f"Generated question for {reference_point.id}: {question}")
            return question

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self._fallback_question(reference_point)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Форматировать контекст для промпта"""
        if not context:
            return "Контекст пустой"

        lines = []
        for key, value in context.items():
            if isinstance(value, str) and value:
                lines.append(f"- {key}: {value[:100]}{'...' if len(value) > 100 else ''}")

        return '\n'.join(lines) if lines else "Нет данных"

    def _format_collected_data(self, context: Dict[str, Any]) -> str:
        """Форматировать собранные данные"""
        collected = context.get('collected_fields', {})
        if not collected:
            return "Ничего не собрано"

        return ', '.join(collected.keys())

    def _fallback_question(self, reference_point: ReferencePoint) -> str:
        """
        Fallback вопрос если LLM не сработал

        Args:
            reference_point: RP для fallback

        Returns:
            Базовый вопрос из hints
        """
        if reference_point.question_hints:
            return reference_point.question_hints[0]

        # Генерировать из имени
        return f"Расскажите подробнее: {reference_point.name.lower()}"


# Пример использования
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    # Мок LLM клиент
    class MockLLMClient:
        async def chat(self, messages, temperature=0.7):
            # Симуляция LLM ответа
            await asyncio.sleep(0.1)
            return "Какую конкретную социальную проблему решает ваш проект?"

    # Пример
    async def main():
        from .reference_point import ReferencePoint, ReferencePointPriority, CompletionCriteria

        llm = MockLLMClient()
        gen = AdaptiveQuestionGenerator(llm, qdrant_client=None)

        rp = ReferencePoint(
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
                "Почему эта проблема важна?"
            ]
        )

        context = {
            'project_essence': 'Создание инклюзивных пространств для детей с ОВЗ',
            'collected_fields': {'project_essence'}
        }

        question = await gen.generate_question(
            reference_point=rp,
            conversation_context=context,
            user_level=UserExpertiseLevel.NOVICE,
            project_type=ProjectType.SOCIAL
        )

        print(f"Generated question: {question}")

    asyncio.run(main())
