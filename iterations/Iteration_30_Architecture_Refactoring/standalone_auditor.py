#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StandaloneAuditor - Auditor Agent wrapper для standalone testing

ЦЕЛЬ: Отделить Auditor от database dependency + FIX rate limit

АРХИТЕКТУРА (Iteration 30):
- Принимает grant_content (str) вместо dict
- Использует GigaChat-2-Max для анализа
- КРИТИЧНО: Пауза 6 секунд ПЕРЕД запросом (fix 529 errors)
- Exponential backoff при ошибках
- 3 попытки retry
- Возвращает audit_result (Dict)
- БЕЗ сохранения в БД (опционально)

Автор: Claude Code (Iteration 30)
Дата: 2025-10-24
Версия: 1.0
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import asyncio
import time
from datetime import datetime

# Добавляем пути
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "agents"))

from shared.llm.unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Custom exception for rate limit errors"""
    pass


class StandaloneAuditor:
    """
    Standalone Auditor - с паузами для rate limit

    КРИТИЧНЫЕ FIX:
    - Delay 6 секунд ПЕРЕД каждым запросом к GigaChat
    - Exponential backoff при 529/429 errors
    - 3 retry attempts
    - Timeout на запрос

    Example:
        auditor = StandaloneAuditor(
            llm_provider='gigachat',
            rate_limit_delay=6,
            retry_attempts=3
        )

        audit_result = await auditor.audit(grant_content)
    """

    def __init__(
        self,
        llm_provider: str = 'gigachat',
        rate_limit_delay: int = 6,
        retry_attempts: int = 3,
        db=None  # Optional
    ):
        """
        Args:
            llm_provider: LLM провайдер (default: gigachat)
            rate_limit_delay: Задержка ПЕРЕД запросом (секунды)
            retry_attempts: Количество попыток retry
            db: Database instance (опционально)
        """
        self.llm_provider = llm_provider
        self.rate_limit_delay = rate_limit_delay
        self.retry_attempts = retry_attempts
        self.db = db

        # Инициализируем LLM client
        self.llm_client = UnifiedLLMClient(provider=llm_provider)

        logger.info(f"[StandaloneAuditor] Initialized with {llm_provider}")
        logger.info(f"[StandaloneAuditor] Rate limit delay: {rate_limit_delay}s")
        logger.info(f"[StandaloneAuditor] Retry attempts: {retry_attempts}")

    def _build_audit_prompt(self, grant_content: str) -> str:
        """
        Построить промпт для аудита заявки

        Args:
            grant_content: Текст заявки

        Returns:
            str: Промпт для LLM
        """
        prompt = f"""
Ты эксперт по грантовым заявкам с 20-летним стажем работы в комиссиях Фонда президентских грантов.

Твоя задача - провести комплексный анализ заявки и оценить её по следующим критериям:

1. ПОЛНОТА (0-10):
   - Все ли разделы заполнены?
   - Достаточно ли деталей?
   - Есть ли цифры и факты?

2. КАЧЕСТВО (0-10):
   - Профессиональность изложения
   - Наличие цитат и источников
   - Логичность структуры
   - Аргументация проблемы

3. СООТВЕТСТВИЕ ТРЕБОВАНИЯМ ФПГ (0-10):
   - Социальная значимость
   - Измеримость результатов
   - Устойчивость проекта
   - Наличие партнёров

ЗАЯВКА ДЛЯ АНАЛИЗА:

{grant_content}

---

ВЕРНИ РЕЗУЛЬТАТ В ФОРМАТЕ JSON:

{{
  "completeness_score": 8.5,
  "quality_score": 9.0,
  "compliance_score": 8.0,
  "overall_score": 0.85,
  "can_submit": true,
  "strengths": [
    "Сильная сторона 1",
    "Сильная сторона 2",
    "Сильная сторона 3"
  ],
  "weaknesses": [
    "Слабая сторона 1",
    "Слабая сторона 2"
  ],
  "recommendations": [
    "Рекомендация 1",
    "Рекомендация 2",
    "Рекомендация 3"
  ],
  "missing_elements": [
    "Отсутствующий элемент 1 (если есть)"
  ],
  "summary": "Краткое резюме анализа"
}}

ВАЖНО: Верни ТОЛЬКО JSON, без дополнительного текста!
"""
        return prompt

    def _parse_audit_response(self, response_text: str) -> Dict[str, Any]:
        """
        Парсинг ответа LLM в structured dict

        Args:
            response_text: Текст ответа от LLM

        Returns:
            Dict: Структурированный результат аудита
        """
        import json
        import re

        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                audit_result = json.loads(json_str)

                # Валидация обязательных полей
                required_fields = [
                    'completeness_score', 'quality_score', 'compliance_score',
                    'overall_score', 'can_submit', 'recommendations'
                ]

                for field in required_fields:
                    if field not in audit_result:
                        logger.warning(f"⚠️ Missing field '{field}' in audit result")

                return audit_result
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.error(f"❌ Failed to parse audit response: {e}")
            logger.error(f"Response text: {response_text[:500]}")

            # Fallback структура
            return {
                "completeness_score": 0.0,
                "quality_score": 0.0,
                "compliance_score": 0.0,
                "overall_score": 0.0,
                "can_submit": False,
                "strengths": [],
                "weaknesses": ["Ошибка парсинга результата аудита"],
                "recommendations": ["Повторить анализ"],
                "missing_elements": [],
                "summary": "Не удалось обработать результат аудита",
                "error": str(e)
            }

    async def _audit_with_retry(self, grant_content: str) -> Dict[str, Any]:
        """
        Выполнить аудит с retry logic

        Args:
            grant_content: Текст заявки

        Returns:
            Dict: Результат аудита

        Raises:
            RateLimitError: Если все попытки исчерпаны
        """
        prompt = self._build_audit_prompt(grant_content)

        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"🔍 Auditor attempt {attempt + 1}/{self.retry_attempts}")

                # КРИТИЧНО: Пауза ПЕРЕД запросом!
                if attempt > 0:
                    # Exponential backoff для повторных попыток
                    wait_time = self.rate_limit_delay * (2 ** attempt)
                    logger.info(f"⏳ Exponential backoff: waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # Первая попытка - обычная пауза
                    logger.info(f"⏳ Rate limit delay: waiting {self.rate_limit_delay}s...")
                    await asyncio.sleep(self.rate_limit_delay)

                # Выполняем запрос
                async with self.llm_client as client:
                    response_text = await client.generate_text(
                        prompt=prompt,
                        max_tokens=4000
                    )

                # Парсим результат
                audit_result = self._parse_audit_response(response_text)

                logger.info(f"✅ Auditor succeeded on attempt {attempt + 1}")
                return audit_result

            except Exception as e:
                error_str = str(e).lower()

                # Проверяем на rate limit errors
                if '529' in error_str or '429' in error_str or 'rate limit' in error_str:
                    logger.warning(f"⚠️ Rate limit error (attempt {attempt + 1}/{self.retry_attempts}): {e}")

                    if attempt < self.retry_attempts - 1:
                        continue  # Retry
                    else:
                        raise RateLimitError(f"Rate limit exceeded after {self.retry_attempts} attempts")
                else:
                    # Другая ошибка - не retry
                    logger.error(f"❌ Auditor error: {e}")
                    raise

        # Если все попытки исчерпаны
        raise RateLimitError(f"Failed after {self.retry_attempts} attempts")

    async def audit(self, grant_content: str) -> Dict[str, Any]:
        """
        Выполнить аудит заявки БЕЗ БД зависимостей

        Args:
            grant_content: str (полный текст заявки)

        Returns:
            audit_result: {
                "overall_score": 0.85,
                "completeness_score": 8.5,
                "quality_score": 9.0,
                "compliance_score": 8.0,
                "can_submit": true,
                "recommendations": [...]
            }
        """
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("📊 STANDALONE AUDITOR - STARTING")
        logger.info("=" * 80)
        logger.info(f"Grant length: {len(grant_content)} characters")
        logger.info(f"LLM Provider: {self.llm_provider}")
        logger.info("")

        try:
            # Выполняем аудит с retry
            audit_result = await self._audit_with_retry(grant_content)

            # Добавляем метаданные
            audit_result['metadata'] = {
                "timestamp": datetime.now().isoformat(),
                "llm_provider": self.llm_provider,
                "grant_length": len(grant_content),
                "rate_limit_delay": self.rate_limit_delay
            }

            duration = time.time() - start_time

            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ STANDALONE AUDITOR - COMPLETED")
            logger.info("=" * 80)
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Overall score: {audit_result['overall_score'] * 100:.1f}%")
            logger.info(f"Can submit: {audit_result['can_submit']}")
            logger.info(f"Recommendations: {len(audit_result.get('recommendations', []))}")
            logger.info("")

            return audit_result

        except RateLimitError as e:
            logger.error(f"❌ Rate limit error: {e}")

            # Возвращаем fallback результат с ошибкой
            return {
                "overall_score": 0.0,
                "completeness_score": 0.0,
                "quality_score": 0.0,
                "compliance_score": 0.0,
                "can_submit": False,
                "strengths": [],
                "weaknesses": ["Rate limit error"],
                "recommendations": [
                    "Увеличить rate_limit_delay до 10+ секунд",
                    "Проверить квоты GigaChat API"
                ],
                "missing_elements": [],
                "summary": f"Аудит не завершён из-за rate limit: {e}",
                "error": str(e)
            }

        except Exception as e:
            logger.error(f"❌ Auditor failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    """
    Quick test of StandaloneAuditor
    """
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_grant_content = """
# ГРАНТОВАЯ ЗАЯВКА

## Описание проблемы
Уроки физкультуры не могут в полной мере привлечь детей к спорту.
Согласно данным Росстат [Источник №1], только 30% детей регулярно занимаются спортом.

## Цель проекта
Спортивно-патриотическое воспитание детей через стрельбу из лука.

## География
г. Кемерово, 50+ школ

## Ожидаемые результаты
- 1000 участников
- 20 мастер-классов
- 4 турнира

## Партнёры
Лига стрельбы из лука Кузбасса
"""

    async def main():
        auditor = StandaloneAuditor(
            llm_provider='gigachat',
            rate_limit_delay=6,
            retry_attempts=3
        )

        audit_result = await auditor.audit(test_grant_content)

        print("\n📊 AUDIT RESULT:")
        import json
        print(json.dumps(audit_result, indent=2, ensure_ascii=False))

    asyncio.run(main())
