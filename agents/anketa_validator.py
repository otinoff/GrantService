#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AnketaValidator - Validates anketa data quality before generation

ITERATION 37: Two-Stage Quality Control
GATE 1: Validate INPUT (anketa JSON)

Purpose: Prevent garbage data from entering generation pipeline
- Checks required fields exist
- Validates minimum data lengths
- Uses LLM to assess coherence and completeness
- Returns validation score and actionable recommendations

Author: Claude Code (Iteration 37)
Date: 2025-10-25
Version: 1.0
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import json

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))

from shared.llm.unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)


class AnketaValidator:
    """
    Validates anketa JSON data quality

    GATE 1 in Two-Stage Quality Pipeline:
    - Input: Raw anketa JSON (dict)
    - Output: Validation score (0-10), issues, recommendations

    Example:
        validator = AnketaValidator(llm_provider='gigachat')
        result = await validator.validate(anketa_data)

        if result['score'] < 5.0:
            print("Anketa quality too low:", result['issues'])
        else:
            print("Anketa OK, can proceed to generation")
    """

    # Required fields for minimal anketa
    REQUIRED_FIELDS = [
        'project_name',
        'problem',
        'solution',
        'goals',
        'budget'
    ]

    # Minimum character lengths for text fields
    MIN_LENGTHS = {
        'project_name': 10,
        'problem': 200,
        'solution': 150,
        'goals': 50  # Total for all goals if list
    }

    # Score thresholds
    SCORE_THRESHOLD_GOOD = 7.0      # Can proceed with confidence
    SCORE_THRESHOLD_ACCEPTABLE = 5.0  # Can proceed but with warnings
    SCORE_THRESHOLD_POOR = 3.0       # Should not proceed

    def __init__(
        self,
        llm_provider: str = 'gigachat',
        db=None
    ):
        """
        Args:
            llm_provider: LLM provider to use (gigachat, claude_code, etc)
            db: Database instance (optional)
        """
        self.llm_provider = llm_provider
        self.db = db
        self.llm_client = UnifiedLLMClient(provider=llm_provider)

        logger.info(f"[AnketaValidator] Initialized with provider: {llm_provider}")

    def _check_required_fields(self, anketa_data: Dict) -> List[str]:
        """
        Check if all required fields are present and non-empty

        Args:
            anketa_data: Anketa dict

        Returns:
            List of missing/empty field names
        """
        missing = []

        for field in self.REQUIRED_FIELDS:
            value = anketa_data.get(field)

            # Check if field exists and is not empty
            if not value:
                missing.append(field)
            elif isinstance(value, str) and len(value.strip()) == 0:
                missing.append(field)
            elif isinstance(value, list) and len(value) == 0:
                missing.append(field)

        return missing

    def _check_minimum_lengths(self, anketa_data: Dict) -> List[Dict[str, Any]]:
        """
        Check if text fields meet minimum length requirements

        Args:
            anketa_data: Anketa dict

        Returns:
            List of length violations: [{'field': 'problem', 'current': 50, 'required': 200}]
        """
        violations = []

        for field, min_length in self.MIN_LENGTHS.items():
            value = anketa_data.get(field)

            if not value:
                continue  # Already caught by required_fields check

            # Calculate actual length
            if isinstance(value, str):
                actual_length = len(value.strip())
            elif isinstance(value, list):
                # For lists (like goals), sum all text
                actual_length = sum(len(str(item)) for item in value)
            else:
                actual_length = len(str(value))

            # Check if below minimum
            if actual_length < min_length:
                violations.append({
                    'field': field,
                    'current': actual_length,
                    'required': min_length,
                    'deficit': min_length - actual_length
                })

        return violations

    def _build_llm_validation_prompt(self, anketa_data: Dict) -> str:
        """
        Build prompt for LLM to assess anketa coherence and completeness

        Args:
            anketa_data: Anketa dict

        Returns:
            str: Prompt for LLM
        """
        # Format anketa for LLM (pretty JSON)
        anketa_json = json.dumps(anketa_data, ensure_ascii=False, indent=2)

        prompt = f"""Ты эксперт по оценке анкет для грантовых заявок.

ЗАДАЧА: Оцени ДОСТАТОЧНОСТЬ и КАЧЕСТВО данных в анкете для генерации грантовой заявки.

АНКЕТА (JSON):
```json
{anketa_json}
```

КРИТЕРИИ ОЦЕНКИ:

1. **Полнота описания проблемы** (0-3 балла):
   - Есть ли чёткое описание проблемы?
   - Указаны ли причины и масштаб проблемы?
   - Понятно ли, кого затрагивает проблема?

2. **Качество решения** (0-3 балла):
   - Предложено ли конкретное решение?
   - Связано ли решение с проблемой?
   - Реалистично ли решение?

3. **Цели и задачи** (0-2 балла):
   - Указаны ли цели проекта?
   - Конкретны ли цели?
   - Есть ли задачи/мероприятия?

4. **Бюджет и обоснование** (0-2 балла):
   - Указан ли бюджет?
   - Есть ли детализация бюджета?

ОБЩАЯ ОЦЕНКА (0-10):
- 8-10: Отличная анкета, все данные есть, можно генерировать заявку высокого качества
- 5-7: Хорошая анкета, достаточно для генерации, но есть пробелы
- 3-4: Слабая анкета, данных мало, генерация будет низкого качества
- 0-2: Очень плохая анкета, недостаточно данных для генерации

ВАЖНО:
- Оценивай ДАННЫЕ, а не формат JSON
- Если данных мало или они поверхностные - снижай оценку
- Будь строгим: лучше заблокировать плохую анкету, чем генерировать мусор

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "score": X.X,
  "problem_score": X,
  "solution_score": X,
  "goals_score": X,
  "budget_score": X,
  "issues": [
    "конкретная проблема 1",
    "конкретная проблема 2"
  ],
  "recommendations": [
    "что нужно добавить или улучшить 1",
    "что нужно добавить или улучшить 2"
  ],
  "can_proceed": true/false,
  "reasoning": "краткое объяснение оценки (2-3 предложения)"
}}

НАЧИНАЙ АНАЛИЗ:"""

        return prompt

    async def _llm_coherence_check(self, anketa_data: Dict) -> Dict[str, Any]:
        """
        Use LLM to assess anketa coherence and quality

        Args:
            anketa_data: Anketa dict

        Returns:
            dict: {
                'score': float,
                'issues': [...],
                'recommendations': [...],
                'can_proceed': bool,
                'reasoning': str
            }
        """
        try:
            # Build prompt
            prompt = self._build_llm_validation_prompt(anketa_data)

            logger.info(f"[AnketaValidator] Running LLM coherence check...")

            # Call LLM
            async with self.llm_client as client:
                response = await client.generate_text(
                    prompt=prompt,
                    max_tokens=1500
                )

            logger.info(f"[AnketaValidator] LLM response: {len(response)} chars")

            # Parse JSON response
            # LLM might wrap in ```json ... ``` or add extra text - clean it
            response = response.strip()

            # Remove code block markers
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]

            response = response.strip()

            # Try to extract JSON object from response
            # GigaChat may add text after JSON - find first { and last }
            try:
                # Find JSON boundaries
                start = response.find('{')
                end = response.rfind('}')

                if start != -1 and end != -1 and end > start:
                    json_str = response[start:end+1]
                    result = json.loads(json_str)
                else:
                    # Fallback: try to parse as-is
                    result = json.loads(response)
            except json.JSONDecodeError as e:
                # Last resort: try line-by-line to find valid JSON
                logger.warning(f"[AnketaValidator] JSON parse failed, trying to extract: {e}")
                lines = response.split('\n')
                json_lines = []
                in_json = False

                for line in lines:
                    if '{' in line:
                        in_json = True
                    if in_json:
                        json_lines.append(line)
                    if '}' in line and in_json:
                        break

                json_str = '\n'.join(json_lines)
                result = json.loads(json_str)

            # Validate structure
            if 'score' not in result:
                raise ValueError("LLM response missing 'score' field")

            logger.info(f"[AnketaValidator] LLM score: {result['score']}/10")

            return {
                'score': float(result.get('score', 0)),
                'problem_score': result.get('problem_score', 0),
                'solution_score': result.get('solution_score', 0),
                'goals_score': result.get('goals_score', 0),
                'budget_score': result.get('budget_score', 0),
                'issues': result.get('issues', []),
                'recommendations': result.get('recommendations', []),
                'can_proceed': result.get('can_proceed', False),
                'reasoning': result.get('reasoning', '')
            }

        except Exception as e:
            logger.error(f"[AnketaValidator] LLM coherence check failed: {e}")
            # Fallback: allow to proceed but with warning
            return {
                'score': 5.0,  # Neutral score
                'issues': [f"LLM validation failed: {str(e)}"],
                'recommendations': ["LLM validation was unavailable"],
                'can_proceed': True,  # Don't block on LLM error
                'reasoning': 'LLM validation error - proceeding with caution'
            }

    def _calculate_final_score(
        self,
        missing_fields: List[str],
        length_violations: List[Dict],
        llm_result: Dict
    ) -> float:
        """
        Calculate final validation score

        Args:
            missing_fields: List of missing required fields
            length_violations: List of length violations
            llm_result: LLM coherence check result

        Returns:
            float: Final score (0-10)
        """
        # Start with LLM score
        score = llm_result['score']

        # Penalize missing required fields heavily
        missing_penalty = len(missing_fields) * 2.0
        score -= missing_penalty

        # Penalize length violations moderately
        length_penalty = len(length_violations) * 0.5
        score -= length_penalty

        # Floor at 0
        score = max(0.0, score)

        logger.info(
            f"[AnketaValidator] Final score: {score:.1f}/10 "
            f"(LLM: {llm_result['score']:.1f}, "
            f"missing_penalty: -{missing_penalty}, "
            f"length_penalty: -{length_penalty})"
        )

        return score

    async def validate(self, anketa_data: Dict) -> Dict[str, Any]:
        """
        Validate anketa data quality

        This is the main method - validates anketa before generation

        Args:
            anketa_data: Anketa JSON dict

        Returns:
            {
                'valid': bool,              # True if score >= 5.0
                'score': float,             # 0-10
                'issues': [...],            # List of problems found
                'recommendations': [...],   # What to improve
                'can_proceed': bool,        # True if can proceed to generation
                'details': {
                    'missing_fields': [...],
                    'length_violations': [...],
                    'llm_assessment': {...}
                }
            }
        """
        logger.info("")
        logger.info("=" * 60)
        logger.info("🔍 ANKETA VALIDATOR - STARTING")
        logger.info("=" * 60)

        # 1. Check required fields
        logger.info("[1/3] Checking required fields...")
        missing_fields = self._check_required_fields(anketa_data)

        if missing_fields:
            logger.warning(f"⚠️ Missing fields: {missing_fields}")
        else:
            logger.info("✅ All required fields present")

        # 2. Check minimum lengths
        logger.info("[2/3] Checking minimum lengths...")
        length_violations = self._check_minimum_lengths(anketa_data)

        if length_violations:
            logger.warning(f"⚠️ Length violations: {len(length_violations)}")
            for v in length_violations:
                logger.warning(f"   - {v['field']}: {v['current']}/{v['required']} chars")
        else:
            logger.info("✅ All fields meet minimum length")

        # 3. LLM coherence check
        logger.info("[3/3] Running LLM coherence check...")
        llm_result = await self._llm_coherence_check(anketa_data)

        logger.info(f"✅ LLM assessment complete: {llm_result['score']:.1f}/10")

        # 4. Calculate final score
        final_score = self._calculate_final_score(
            missing_fields,
            length_violations,
            llm_result
        )

        # 5. Compile all issues
        all_issues = []

        # Add missing fields to issues
        if missing_fields:
            all_issues.append(f"Отсутствуют обязательные поля: {', '.join(missing_fields)}")

        # Add length violations to issues
        for v in length_violations:
            all_issues.append(
                f"Поле '{v['field']}' слишком короткое: {v['current']} символов "
                f"(минимум {v['required']})"
            )

        # Add LLM issues
        all_issues.extend(llm_result.get('issues', []))

        # 6. Compile recommendations
        all_recommendations = []

        if missing_fields:
            all_recommendations.append(f"Заполните недостающие поля: {', '.join(missing_fields)}")

        for v in length_violations:
            all_recommendations.append(
                f"Расширьте описание в поле '{v['field']}' "
                f"(нужно ещё {v['deficit']} символов)"
            )

        all_recommendations.extend(llm_result.get('recommendations', []))

        # 7. Determine if can proceed
        can_proceed = (
            final_score >= self.SCORE_THRESHOLD_ACCEPTABLE and
            len(missing_fields) == 0  # All required fields must be present
        )

        # 8. Final result
        result = {
            'valid': final_score >= self.SCORE_THRESHOLD_ACCEPTABLE,
            'score': final_score,
            'issues': all_issues,
            'recommendations': all_recommendations,
            'can_proceed': can_proceed,
            'details': {
                'missing_fields': missing_fields,
                'length_violations': length_violations,
                'llm_assessment': llm_result
            }
        }

        # 9. Log summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ ANKETA VALIDATOR - COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Final Score: {final_score:.1f}/10")
        logger.info(f"✅ Valid: {result['valid']}")
        logger.info(f"🚦 Can Proceed: {can_proceed}")
        logger.info(f"⚠️ Issues: {len(all_issues)}")
        logger.info(f"💡 Recommendations: {len(all_recommendations)}")
        logger.info("")

        return result


if __name__ == "__main__":
    """
    Quick test of AnketaValidator
    """
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test data: good anketa
    good_anketa = {
        'project_name': 'Молодежный образовательный центр "Цифровое будущее"',
        'problem': """В Кемеровской области наблюдается острый дефицит доступных образовательных
        программ по цифровым технологиям для молодежи из малых городов. Согласно данным
        регионального министерства образования, только 15% молодых людей в возрасте 14-25 лет
        имеют доступ к качественному обучению в сфере IT. Это приводит к оттоку талантливой
        молодежи в крупные города и снижению инновационного потенциала региона.""",
        'solution': """Создание молодежного образовательного центра с бесплатными курсами по
        программированию, веб-дизайну, и цифровому маркетингу. Центр будет оснащен современным
        оборудованием и работать на базе местного ДК.""",
        'goals': [
            'Обучить 200 молодых людей цифровым навыкам',
            'Создать 3 постоянные образовательные программы',
            'Организовать стажировки для 50 выпускников'
        ],
        'budget': '850000'
    }

    # Test data: poor anketa
    poor_anketa = {
        'project_name': 'Проект',
        'problem': 'Есть проблема',
        'solution': '',
        'goals': [],
        'budget': '0'
    }

    async def test():
        print("\n" + "="*60)
        print("TEST 1: Good Anketa")
        print("="*60)

        validator = AnketaValidator(llm_provider='gigachat')
        result = await validator.validate(good_anketa)

        print(f"\nRESULT:")
        print(f"  Score: {result['score']:.1f}/10")
        print(f"  Valid: {result['valid']}")
        print(f"  Can Proceed: {result['can_proceed']}")
        print(f"  Issues: {len(result['issues'])}")

        print("\n" + "="*60)
        print("TEST 2: Poor Anketa")
        print("="*60)

        result2 = await validator.validate(poor_anketa)

        print(f"\nRESULT:")
        print(f"  Score: {result2['score']:.1f}/10")
        print(f"  Valid: {result2['valid']}")
        print(f"  Can Proceed: {result2['can_proceed']}")
        print(f"  Issues: {len(result2['issues'])}")
        if result2['issues']:
            print(f"\nISSUES:")
            for issue in result2['issues']:
                print(f"  - {issue}")

    asyncio.run(test())
