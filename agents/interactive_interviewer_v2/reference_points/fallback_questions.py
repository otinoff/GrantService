#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fallback Question Bank for InteractiveInterviewer

Purpose: Provide additional questions when all RPs are covered but MIN_QUESTIONS not reached
Theory: Extended Mind - Question bank as cognitive extension
Date: 2025-10-21
"""

import logging
import random
from typing import List, Dict, Optional

# Импорт функции для получения вопросов из БД
try:
    from data.database.interview import get_interview_questions
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Could not import get_interview_questions, using hardcoded fallbacks only")

logger = logging.getLogger(__name__)


class FallbackQuestionBank:
    """
    Extended Mind pattern: Question bank as external cognitive resource

    When all Reference Points are covered but we need more questions,
    this bank provides deepening/clarifying questions from:
    1. Database (interview_questions table)
    2. Hardcoded fallbacks (backup)
    """

    def __init__(self):
        self.db_questions = self._load_db_questions()
        self.hardcoded_fallbacks = self._init_hardcoded_fallbacks()

    def _load_db_questions(self) -> List[Dict]:
        """Load active questions from interview_questions table"""
        if not DB_AVAILABLE:
            logger.info("DB questions not available, using hardcoded fallbacks")
            return []

        try:
            questions = get_interview_questions()
            active = [q for q in questions if q.get('is_active', True)]
            logger.info(f"Loaded {len(active)} active questions from DB")
            return active
        except Exception as e:
            logger.error(f"Failed to load questions from DB: {e}")
            return []

    def _init_hardcoded_fallbacks(self) -> Dict[str, List[str]]:
        """
        Hardcoded fallback questions organized by topic

        These are used if DB questions exhausted or DB unavailable
        Based on FPG requirements analysis
        """
        return {
            "problem_deepening": [
                "Расскажите подробнее: почему эта проблема важна именно сейчас?",
                "Кто еще сталкивается с этой проблемой кроме вашей целевой аудитории?",
                "Что произойдет если эту проблему не решать?",
                "Какие попытки решения этой проблемы предпринимались ранее и почему они не сработали?",
            ],

            "solution_deepening": [
                "Какие альтернативные подходы вы рассматривали?",
                "Почему именно этот метод решения наиболее эффективен?",
                "Какие ресурсы критически необходимы для реализации?",
                "Какие препятствия могут возникнуть и как вы их преодолеете?",
            ],

            "target_audience_deepening": [
                "Как вы планируете привлекать участников целевой группы?",
                "Какие конкретные потребности целевой группы закроет проект?",
                "Как вы определили именно эту целевую группу?",
                "Какие характеристики целевой группы важны для проекта?",
            ],

            "activities_deepening": [
                "Опишите подробнее последовательность основных мероприятий",
                "Кто будет выполнять каждое из мероприятий?",
                "Какие мероприятия являются наиболее важными для достижения цели?",
                "Как вы будете координировать разные мероприятия?",
            ],

            "results_deepening": [
                "Как вы будете измерять успех проекта?",
                "Какие конкретные изменения произойдут в жизни благополучателей?",
                "Какие долгосрочные эффекты ожидаются?",
                "Какие количественные показатели подтвердят достижение результатов?",
            ],

            "team_deepening": [
                "Какой опыт команды наиболее важен для этого проекта?",
                "Как распределены роли между членами команды?",
                "Какие компетенции команды критичны для успеха?",
                "Есть ли у команды опыт реализации похожих проектов?",
            ],

            "budget_deepening": [
                "Какие расходы составляют основную часть бюджета?",
                "Почему именно эти статьи расходов критичны?",
                "Как вы обосновали запрашиваемую сумму?",
                "Есть ли софинансирование из других источников?",
            ],

            "sustainability_deepening": [
                "Как проект будет продолжаться после окончания гранта?",
                "Какие источники финансирования планируете привлечь после гранта?",
                "Как вы планируете масштабировать результаты проекта?",
                "Какие партнёры поддержат проект после окончания финансирования?",
            ],

            "uniqueness_deepening": [
                "Чем ваш подход отличается от существующих решений?",
                "Какие инновационные элементы есть в проекте?",
                "Почему именно ваша организация должна реализовать этот проект?",
                "Какой уникальный опыт или ресурсы вы привносите?",
            ],

            "geography_deepening": [
                "Почему выбрана именно эта география?",
                "Как специфика региона влияет на реализацию проекта?",
                "Планируете ли расширение географии в будущем?",
                "Какие региональные особенности учитываете?",
            ],
        }

    def get_fallback_question(
        self,
        category: Optional[str] = None,
        used_questions: Optional[List[str]] = None
    ) -> str:
        """
        Get a fallback question to continue interview

        Args:
            category: Topic category (e.g., "problem", "solution")
            used_questions: List of already asked questions (to avoid repetition)

        Returns:
            Fallback question text
        """
        used_questions = used_questions or []

        # Try to get unused DB question first
        db_question = self._get_unused_db_question(used_questions)
        if db_question:
            logger.info(f"Using DB question: {db_question[:50]}...")
            return db_question

        # Fall back to hardcoded questions
        logger.info("DB questions exhausted, using hardcoded fallbacks")

        # Select category
        if category:
            # Try to match category to our fallback topics
            category_key = self._map_category_to_topic(category)
        else:
            # Random category if not specified
            category_key = random.choice(list(self.hardcoded_fallbacks.keys()))

        # Get questions from category
        questions = self.hardcoded_fallbacks.get(category_key, [])

        # Filter out already used
        unused = [q for q in questions if q not in used_questions]

        if unused:
            question = random.choice(unused)
            logger.info(f"Using hardcoded fallback ({category_key}): {question[:50]}...")
            return question
        else:
            # All questions used - pick any random question
            logger.warning("All fallback questions used, picking random")
            all_questions = []
            for qs in self.hardcoded_fallbacks.values():
                all_questions.extend(qs)
            return random.choice(all_questions)

    def _get_unused_db_question(self, used_questions: List[str]) -> Optional[str]:
        """Get a question from DB that hasn't been asked yet"""
        if not self.db_questions:
            return None

        # Filter out used questions
        unused = [
            q for q in self.db_questions
            if q.get('question_text') not in used_questions
        ]

        if not unused:
            return None

        # Prefer required questions
        required = [q for q in unused if q.get('is_required', False)]

        if required:
            question = random.choice(required)
        else:
            question = random.choice(unused)

        return question.get('question_text')

    def _map_category_to_topic(self, category: str) -> str:
        """Map RP category to fallback topic"""
        category_lower = category.lower()

        # Mapping dictionary
        mapping = {
            'problem': 'problem_deepening',
            'проблем': 'problem_deepening',
            'solution': 'solution_deepening',
            'решение': 'solution_deepening',
            'target': 'target_audience_deepening',
            'аудитор': 'target_audience_deepening',
            'целев': 'target_audience_deepening',
            'activity': 'activities_deepening',
            'мероприят': 'activities_deepening',
            'result': 'results_deepening',
            'результат': 'results_deepening',
            'team': 'team_deepening',
            'команд': 'team_deepening',
            'budget': 'budget_deepening',
            'бюджет': 'budget_deepening',
            'sustain': 'sustainability_deepening',
            'устойчив': 'sustainability_deepening',
            'unique': 'uniqueness_deepening',
            'уникальн': 'uniqueness_deepening',
            'geogr': 'geography_deepening',
            'географ': 'geography_deepening',
        }

        # Try to find match
        for key, topic in mapping.items():
            if key in category_lower:
                return topic

        # Default to problem deepening if no match
        return 'problem_deepening'

    def get_deepening_question_for_rp(self, rp_id: str, used_questions: List[str]) -> str:
        """
        Get a deepening question for a specific Reference Point

        Args:
            rp_id: Reference Point ID (e.g., "rp_002_problem")
            used_questions: Already asked questions

        Returns:
            Deepening question
        """
        # Extract category from RP ID
        # e.g., "rp_002_problem" -> "problem"
        parts = rp_id.split('_')
        category = parts[-1] if len(parts) > 1 else None

        return self.get_fallback_question(category, used_questions)

    def get_question_count(self) -> Dict[str, int]:
        """Get statistics about available questions"""
        return {
            'db_questions': len(self.db_questions),
            'db_required': len([q for q in self.db_questions if q.get('is_required')]),
            'db_optional': len([q for q in self.db_questions if not q.get('is_required')]),
            'hardcoded_categories': len(self.hardcoded_fallbacks),
            'hardcoded_total': sum(len(qs) for qs in self.hardcoded_fallbacks.values()),
        }


# Singleton instance
_fallback_bank = None

def get_fallback_bank() -> FallbackQuestionBank:
    """Get singleton instance of FallbackQuestionBank"""
    global _fallback_bank
    if _fallback_bank is None:
        _fallback_bank = FallbackQuestionBank()
        stats = _fallback_bank.get_question_count()
        logger.info(f"Fallback bank initialized: {stats}")
    return _fallback_bank
