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

# Для генерации embeddings (Qdrant search)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, Qdrant search will be disabled")

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

        # Lazy loading: НЕ загружаем модель в __init__!
        # Модель будет загружена асинхронно при первом использовании
        self.embedding_model = None
        self._model_loading_task = None
        self._model_load_attempted = False

        logger.info("AdaptiveQuestionGenerator initialized (embedding model will load on demand)")

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
        import asyncio
        import time

        start_time = time.time()

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

        # 4-5. ПАРАЛЛЕЛЬНАЯ ОБРАБОТКА: Qdrant search + information gaps
        # Вместо последовательного выполнения, запускаем параллельно
        try:
            # Создать задачи
            qdrant_task = asyncio.create_task(
                self._get_fpg_context_with_timeout(reference_point, project_type, timeout=2.0)
            )

            # gaps - синхронная функция, оборачиваем в корутину
            gaps_task = asyncio.create_task(
                self._async_identify_gaps(reference_point, conversation_context)
            )

            # Запустить параллельно и дождаться результатов
            fpg_context, gaps = await asyncio.gather(qdrant_task, gaps_task)

            parallel_time = time.time() - start_time
            logger.info(f"⚡ Parallel processing took {parallel_time:.2f}s (Qdrant + gaps)")

        except asyncio.TimeoutError:
            logger.warning("Qdrant search timeout, using fallback")
            fpg_context = ""
            gaps = self._identify_information_gaps(reference_point, conversation_context)
        except Exception as e:
            logger.error(f"Parallel processing error: {e}")
            fpg_context = ""
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

        total_time = time.time() - start_time
        logger.info(f"✅ Question generated in {total_time:.2f}s total")

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
        # DEBUG: Логируем context для отладки
        logger.debug(f"[_already_covered] Checking RP: {reference_point.id}")
        logger.debug(f"[_already_covered] covered_topics: {context.get('covered_topics', [])}")
        logger.debug(f"[_already_covered] collected_fields keys: {list(context.get('collected_fields', {}).keys())}")

        # Проверить по тегам RP
        for tag in reference_point.tags:
            if tag in context.get('covered_topics', []):
                logger.debug(f"[_already_covered] Found tag '{tag}' in covered_topics")
                return True

        # Проверить по имени поля - ИСПРАВЛЕНО: проверяем наличие данных!
        field_name = reference_point.id.split('_', 2)[-1]  # rp_001_project_essence -> project_essence
        collected_fields = context.get('collected_fields', {})

        # ИСПРАВЛЕНИЕ: проверяем не просто наличие ключа, а наличие НЕПУСТЫХ данных
        if field_name in collected_fields:
            field_value = collected_fields[field_name]
            # Считаем покрытым только если есть реальные данные
            if field_value and len(str(field_value).strip()) > 0:
                logger.debug(f"[_already_covered] Field '{field_name}' has data: {field_value[:50]}...")
                return True
            else:
                logger.debug(f"[_already_covered] Field '{field_name}' exists but empty, not covered")

        # Также проверяем контекст напрямую (может быть в **collected_data)
        if field_name in context:
            field_value = context[field_name]
            if field_value and len(str(field_value).strip()) > 0:
                logger.debug(f"[_already_covered] Field '{field_name}' in context: {field_value[:50]}...")
                return True

        logger.debug(f"[_already_covered] RP {reference_point.id} NOT covered")
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

        # Проверить что embedding модель готова (с timeout 3 сек)
        model_ready = await self._ensure_embedding_model_loaded(timeout=3.0)
        if not model_ready:
            logger.info("Embedding model not ready, skipping Qdrant search")
            return ""

        try:
            # Поисковый запрос
            query_parts = [
                reference_point.name,
                project_type.value if project_type != ProjectType.UNKNOWN else "",
                "ФПГ требования"
            ]
            query = ' '.join([p for p in query_parts if p])

            # Генерация embedding вектора из текста запроса
            query_vector = self.embedding_model.encode(query).tolist()

            # Поиск в Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
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

    async def _get_fpg_context_with_timeout(
        self,
        reference_point: ReferencePoint,
        project_type: ProjectType,
        timeout: float = 2.0
    ) -> str:
        """
        Получить контекст из Qdrant с timeout

        Args:
            reference_point: RP для контекста
            project_type: Тип проекта
            timeout: Максимальное время ожидания (секунды)

        Returns:
            Релевантный контекст или пустая строка при timeout
        """
        import asyncio

        try:
            return await asyncio.wait_for(
                self._get_fpg_context(reference_point, project_type),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Qdrant search timeout ({timeout}s), using fallback")
            return ""
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return ""

    async def _async_identify_gaps(
        self,
        reference_point: ReferencePoint,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Асинхронная обертка для _identify_information_gaps

        Args:
            reference_point: RP для анализа
            context: Контекст разговора

        Returns:
            Список пробелов
        """
        import asyncio

        # Выполнить синхронную функцию в executor чтобы не блокировать
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._identify_information_gaps,
            reference_point,
            context
        )

    async def _ensure_embedding_model_loaded(self, timeout: float = 3.0) -> bool:
        """
        Убедиться что embedding модель загружена

        Lazy loading: загружает модель только при первом использовании.
        Если модель уже загружена, возвращает True сразу.
        Если загрузка в процессе, ждет завершения (с timeout).
        Если модель недоступна, возвращает False.

        Args:
            timeout: Максимальное время ожидания загрузки (секунды)

        Returns:
            True если модель готова, False если нет
        """
        import asyncio

        # Модель уже загружена
        if self.embedding_model is not None:
            return True

        # Проверка что SentenceTransformers доступен
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not available, model loading skipped")
            return False

        # Проверка что Qdrant клиент есть
        if self.qdrant is None:
            logger.info("Qdrant client not configured, model loading skipped")
            return False

        # Если уже пытались загрузить и не удалось, не пытаться снова
        if self._model_load_attempted and self.embedding_model is None:
            logger.debug("Model loading was attempted before and failed, skipping")
            return False

        # Если задача загрузки еще не запущена, запустить
        if self._model_loading_task is None:
            logger.info("[LAZY] Starting embedding model loading in background")
            self._model_loading_task = asyncio.create_task(self._load_embedding_model_async())

        # Дождаться завершения загрузки (с timeout)
        try:
            await asyncio.wait_for(self._model_loading_task, timeout=timeout)

            # Проверить что модель действительно загружена
            if self.embedding_model is not None:
                logger.info(f"[OK] Embedding model loaded successfully (waited {timeout:.1f}s max)")
                return True
            else:
                logger.warning("Embedding model loading completed but model is None")
                return False

        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] Embedding model loading timeout ({timeout}s), using fallback")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Embedding model loading failed: {e}")
            return False

    async def _load_embedding_model_async(self):
        """
        Асинхронно загрузить embedding модель

        Выполняет синхронную SentenceTransformer() в executor
        чтобы не блокировать event loop.
        """
        import asyncio

        self._model_load_attempted = True

        try:
            logger.info("[LOADING] Starting SentenceTransformer load in executor")
            loop = asyncio.get_event_loop()

            # Загрузить модель в отдельном thread
            self.embedding_model = await loop.run_in_executor(
                None,
                SentenceTransformer,
                'paraphrase-multilingual-MiniLM-L12-v2'
            )

            logger.info("[SUCCESS] Embedding model loaded successfully")

        except Exception as e:
            logger.error(f"[FAILED] Failed to load embedding model: {e}")
            self.embedding_model = None

    def start_loading_in_background(self):
        """
        Запустить загрузку модели в фоне (опционально)

        Можно вызывать сразу после создания агента, чтобы модель
        начала загружаться заранее, пока пользователь печатает ответ.

        Example:
            agent = InteractiveInterviewerAgentV2(...)
            agent.question_generator.start_loading_in_background()
        """
        import asyncio

        if self._model_loading_task is None and SENTENCE_TRANSFORMERS_AVAILABLE and self.qdrant is not None:
            logger.info("[PRELOAD] Starting embedding model preloading")
            try:
                # Создать задачу в текущем event loop
                loop = asyncio.get_event_loop()
                self._model_loading_task = loop.create_task(self._load_embedding_model_async())
            except RuntimeError:
                # Нет event loop (не в async контексте)
                logger.warning("Cannot preload model: no event loop running")

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

Твоя задача - провести структурированное интервью и собрать информацию о проекте.

ВСЕ КЛЮЧЕВЫЕ ВОПРОСЫ ИНТЕРВЬЮ (12 тем):
1. Имя заявителя - Как Ваше имя, как я могу к Вам обращаться?
2. Суть проекта - Расскажите о вашем проекте, в чем его суть и главная цель?
3. Проблема - Какую конкретную проблему решает ваш проект? Почему это важно?
4. Целевая аудитория - Кто ваша целевая аудитория? Сколько человек получат пользу?
5. География - В каком регионе будет реализован проект?
6. Методология - Как вы планируете реализовать проект? Какие конкретные мероприятия запланированы?
7. Результаты - Какие конкретные результаты и изменения вы планируете достичь?
8. Бюджет - Какой бюджет требуется? Как распределены средства по статьям?
9. Команда - Кто будет реализовывать проект? Какой у команды опыт? Есть ли партнеры?
10. Риски - Какие риски вы видите в проекте? Как планируете их минимизировать?
11. Устойчивость - Что будет с проектом после окончания гранта? Планируете ли развивать дальше?
12. Уникальность - Чем ваш проект отличается от других подобных инициатив?

ВАЖНО:
- Задавай ОДИН вопрос за раз, не дублируй уже заданные
- Проверяй собранный контекст перед вопросом
- Обращайся по имени если известно
- Говори как живой человек, используй естественные переходы
"""

        # Пользовательский промпт (ITERATION 25: оптимизирован для скорости)
        # Собрать контекст разговора
        covered = ', '.join(conversation_context.get('covered_topics', []))
        collected = self._format_collected_data(conversation_context)

        user_prompt = f"""# Задача
Узнать: {reference_point.name}
{reference_point.description}

# Контекст разговора
Уже обсуждено: {covered if covered else 'ничего'}
Собрано: {collected}
Тип проекта: {project_type.value}"""

        # Добавить пробелы если есть
        if gaps and gaps != "Нет явных пробелов":
            user_prompt += f"\nПробелы: {gaps}"

        # Добавить контекст ФПГ только если есть
        if fpg_context and fpg_context != "Нет специфичных требований" and len(fpg_context) > 20:
            user_prompt += f"\n\n# Контекст ФПГ\n{fpg_context[:300]}{'...' if len(fpg_context) > 300 else ''}"

        # Ограничить примеры до 2 (question_hints уже список)
        if reference_point.question_hints:
            limited_hints = '\n'.join(reference_point.question_hints[:2])
            user_prompt += f"\n\n# Референс (не копируй)\n{limited_hints}"

        user_prompt += "\n\nСгенерируй ОДИН вопрос. Верни ТОЛЬКО текст вопроса."""

        try:
            # Вызов LLM - UnifiedLLMClient использует generate_async с единым промптом
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # ITERATION 25: Reduced temperature for faster generation
            response = await self.llm.generate_async(
                prompt=full_prompt,
                temperature=0.5  # Баланс между естественностью и скоростью
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
