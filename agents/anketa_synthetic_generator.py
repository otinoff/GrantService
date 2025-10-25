#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anketa Synthetic Generator

Генератор синтетических анкет для создания корпуса данных.
Использует GigaChat Lite для экономии токенов.

Iteration: 38 - Synthetic Corpus Generator
Date: 2025-10-25
"""

import json
import logging
import random
from typing import List, Dict, Optional

# Setup logging
logger = logging.getLogger(__name__)


class AnketaSyntheticGenerator:
    """
    Генератор синтетических анкет на основе реальных примеров

    Использует:
    - GigaChat Lite для генерации (экономия токенов!)
    - Реальные анкеты из БД как шаблоны
    - Вариации по региону, теме, качеству
    """

    # Регионы России для вариации
    REGIONS = [
        "Москва",
        "Санкт-Петербург",
        "Кемеровская область - Кузбасс",
        "Новосибирская область",
        "Свердловская область",
        "Краснодарский край",
        "Республика Татарстан",
        "Нижегородская область",
        "Челябинская область",
        "Омская область",
        "Ростовская область",
        "Пермский край"
    ]

    # Темы социальных проектов
    TOPICS = [
        "молодежные инициативы",
        "культурное развитие",
        "образовательные программы",
        "спорт и здоровый образ жизни",
        "поддержка ветеранов",
        "экологические проекты",
        "социальная поддержка",
        "развитие волонтерства",
        "сохранение традиций",
        "цифровизация образования"
    ]

    def __init__(self, db, llm_model: str = 'GigaChat'):
        """
        Args:
            db: Database instance
            llm_model: 'GigaChat' для Lite (экономия токенов), 'GigaChat-Max' для Max, 'GigaChat-Pro' для Pro
        """
        self.db = db
        self.llm_model = llm_model

        # Import LLM client
        from shared.llm.unified_llm_client import UnifiedLLMClient
        self.llm = None  # Will initialize in async context

        logger.info(f"[AnketaSyntheticGenerator] Initialized with model={llm_model}")

    async def _init_llm(self):
        """Initialize LLM client (async)"""
        if not self.llm:
            from shared.llm.unified_llm_client import UnifiedLLMClient
            # Provider is always 'gigachat', model selects Lite/Max/Pro
            # Use higher temperature (0.8) for diversity in synthetic data
            self.llm = UnifiedLLMClient(
                provider='gigachat',
                model=self.llm_model,
                temperature=0.8
            )
        return self.llm

    def _create_generation_prompt(
        self,
        template_anketas: List[Dict],
        quality_level: str,
        topic: Optional[str] = None,
        region: Optional[str] = None
    ) -> str:
        """
        Создать промпт для генерации анкеты

        Args:
            template_anketas: Примеры реальных анкет (3-5 штук)
            quality_level: 'low', 'medium', 'high'
            topic: Тема проекта (опционально)
            region: Регион (опционально)
        """

        # Random region and topic if not specified
        if not region:
            region = random.choice(self.REGIONS)
        if not topic:
            topic = random.choice(self.TOPICS)

        # Format examples
        examples_text = ""
        for i, anketa in enumerate(template_anketas[:3], 1):
            examples_text += f"\nПример {i}:\n"
            examples_text += f"  Проект: {anketa.get('project_name', 'N/A')}\n"
            examples_text += f"  Регион: {anketa.get('region', 'N/A')}\n"
            examples_text += f"  Проблема: {anketa.get('problem', 'N/A')[:200]}...\n"
            examples_text += f"  Решение: {anketa.get('solution', 'N/A')[:200]}...\n"

        # Quality requirements
        quality_requirements = {
            'low': """
LOW качество (4-6/10):
- Размытая формулировка проблемы (без фактов и статистики)
- Нечёткие цели (без SMART критериев)
- Неконкретные результаты (без измеримых показателей)
- Базовый бюджет (округлённые суммы)
НО: Все обязательные поля заполнены!
            """,
            'medium': """
MEDIUM качество (6-8/10):
- Понятная проблема с некоторыми фактами
- Адекватные цели и задачи (частично SMART)
- Измеримые результаты (с показателями)
- Реалистичный бюджет (детализированный)
            """,
            'high': """
HIGH качество (8-10/10):
- Чётко сформулированная проблема с фактами и статистикой
- SMART цели (конкретные, измеримые, достижимые)
- Конкретные измеримые результаты с индикаторами
- Обоснованный детальный бюджет
- Инновационный подход
            """
        }

        prompt = f"""Ты - эксперт по грантовым заявкам Фонда президентских грантов (ФПГ).

ЗАДАЧА: Создай реалистичную анкету для социального проекта.

ПРИМЕРЫ успешных анкет ФПГ:
{examples_text}

ТРЕБОВАНИЯ к новой анкете:
- Тема: {topic}
- Регион: {region}
- Целевое качество: {quality_level.upper()}

{quality_requirements.get(quality_level, quality_requirements['medium'])}

ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
1. Анкета должна быть УНИКАЛЬНОЙ (не копия примеров!)
2. ВСЕ обязательные поля заполнены (15 полей)
3. Реалистичный проект (не фантастика)
4. Соответствует формату ФПГ
5. Проект ОБЯЗАТЕЛЬНО должен быть по теме "{topic}" в регионе "{region}"

ВАЖНО:
- Название проекта должно отличаться от примеров
- Организация должна быть уникальной
- Проблема должна быть специфична для региона {region}
- Бюджет должен быть от 500,000 до 2,000,000 рублей

Верни ТОЛЬКО JSON (без дополнительного текста):
{{
    "project_name": "...",
    "organization": "...",
    "region": "{region}",
    "problem": "...",
    "solution": "...",
    "goals": ["...", "...", "..."],
    "activities": ["...", "...", "...", "..."],
    "results": ["...", "...", "..."],
    "budget": "...",
    "budget_breakdown": {{
        "equipment": "...",
        "teachers": "...",
        "materials": "...",
        "other": "..."
    }}
}}
"""

        return prompt

    async def generate_synthetic_anketa(
        self,
        template_anketas: List[Dict],
        quality_level: str = 'medium',
        topic: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict:
        """
        Генерировать 1 синтетическую анкету

        Args:
            template_anketas: Примеры реальных анкет из БД
            quality_level: 'low', 'medium', 'high'
            topic: Тема проекта (опционально)
            region: Регион (опционально)

        Returns:
            {
                'project_name': '...',
                'organization': '...',
                'region': '...',
                'problem': '...',
                'solution': '...',
                'goals': [...],
                'activities': [...],
                'results': [...],
                'budget': '...',
                'budget_breakdown': {...},
                'synthetic': True,
                'quality_target': 'medium'
            }
        """

        # Retry logic (GigaChat sometimes truncates responses)
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Initialize LLM
                llm = await self._init_llm()

                # Create prompt
                prompt = self._create_generation_prompt(
                    template_anketas=template_anketas,
                    quality_level=quality_level,
                    topic=topic,
                    region=region
                )

                logger.info(f"[Generator] Generating anketa (attempt {attempt}/{max_retries}): quality={quality_level}, region={region}, topic={topic}")

                # Generate
                async with llm:
                    response = await llm.generate_text(
                        prompt=prompt,
                        max_tokens=8192  # МАКСИМУМ для GigaChat (для тестов - тратим больше токенов!)
                    )

                # Parse JSON
                anketa = self._extract_json_from_response(response)

                # Add metadata
                anketa['synthetic'] = True
                anketa['quality_target'] = quality_level

                logger.info(f"[Generator] Generated anketa: {anketa.get('project_name', 'N/A')}")

                return anketa

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"[Generator] JSON parse failed on attempt {attempt}/{max_retries}: {e}")
                if attempt < max_retries:
                    logger.info(f"[Generator] Retrying...")
                    continue
                else:
                    logger.error(f"[Generator] All {max_retries} attempts failed")
                    raise

            except Exception as e:
                logger.error(f"[Generator] Failed to generate anketa: {e}")
                raise

    def _extract_json_from_response(self, response: str) -> Dict:
        """
        Извлечь JSON из ответа LLM

        Обрабатывает случаи когда LLM добавляет текст до/после JSON
        """
        import re

        response = response.strip()

        # Remove markdown code blocks
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]

        response = response.strip()

        # Try to find JSON boundaries
        try:
            start = response.find('{')
            end = response.rfind('}')

            if start != -1 and end != -1 and end > start:
                json_str = response[start:end+1]

                # Clean invalid control characters
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)

                return json.loads(json_str)
            else:
                # Try as-is
                response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response)
                return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"[Generator] JSON parse failed: {e}")
            logger.error(f"[Generator] Response: {response[:500]}")

            # Fallback: try line-by-line extraction
            lines = response.split('\n')
            json_lines = []
            in_json = False

            for line in lines:
                if '{' in line:
                    in_json = True
                if in_json:
                    # Clean line from control characters
                    clean_line = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', line)
                    json_lines.append(clean_line)
                if '}' in line and in_json:
                    break

            json_str = '\n'.join(json_lines)

            # Last attempt: aggressive cleaning
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Remove trailing commas before closing braces/brackets
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                # Fix quotes
                json_str = json_str.replace('»', '"').replace('«', '"')
                return json.loads(json_str)

    async def generate_batch(
        self,
        template_anketas: List[Dict],
        count: int = 10,
        quality_distribution: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Генерировать batch анкет

        Args:
            template_anketas: Примеры из БД
            count: Количество анкет (1-100)
            quality_distribution: {
                'low': 0.2,    # 20%
                'medium': 0.5, # 50%
                'high': 0.3    # 30%
            }

        Returns:
            List of generated anketas
        """

        # Default distribution
        if not quality_distribution:
            quality_distribution = {
                'low': 0.2,
                'medium': 0.5,
                'high': 0.3
            }

        # Calculate counts
        low_count = int(count * quality_distribution.get('low', 0))
        medium_count = int(count * quality_distribution.get('medium', 0))
        high_count = count - low_count - medium_count

        logger.info(f"[Generator] Batch generation: {count} anketas (low:{low_count}, medium:{medium_count}, high:{high_count})")

        # Generate
        anketas = []

        for quality, qty in [('low', low_count), ('medium', medium_count), ('high', high_count)]:
            for i in range(qty):
                anketa = await self.generate_synthetic_anketa(
                    template_anketas=template_anketas,
                    quality_level=quality
                )
                anketas.append(anketa)

        return anketas

