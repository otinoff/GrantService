#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expert Agent - RAG-based grant application evaluator

Evaluates grant applications against fund requirements using RAG retrieval.
Checks structure, content quality, compliance with requirements.

Created: 2025-10-31
Iteration: 69 - Autonomous Night Testing
"""

import logging
from typing import Dict, List, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ExpertAgent:
    """
    Expert Agent with RAG knowledge base

    Evaluates grant applications using:
    - RAG retrieval from fund requirements (Qdrant: fpg_requirements)
    - Structure validation
    - Content quality checks
    - Compliance verification

    Returns score 0-10 with detailed feedback
    """

    # Minimum requirements
    MIN_GRANT_LENGTH = 15000  # characters
    MIN_SECTIONS = 8  # minimum sections
    MIN_RESEARCH_SOURCES = 2

    # Required sections in grant
    REQUIRED_SECTIONS = [
        "Название проекта",
        "Цель проекта",
        "Задачи проекта",
        "Обоснование проекта",
        "Целевая аудитория",
        "План реализации",
        "Бюджет",
        "Ожидаемые результаты"
    ]

    def __init__(self, use_rag: bool = True, qdrant_collection: str = "fpg_requirements"):
        """
        Initialize Expert Agent

        Args:
            use_rag: Use RAG retrieval for evaluation
            qdrant_collection: Qdrant collection name
        """
        self.use_rag = use_rag
        self.qdrant_collection = qdrant_collection
        self.rag_retriever = None

        if use_rag:
            try:
                from qdrant_client import QdrantClient
                from tester.knowledge_base.rag_retriever import RAGRetriever

                # Connect to Qdrant
                qdrant_client = QdrantClient(host="5.35.88.251", port=6333)
                self.rag_retriever = RAGRetriever(qdrant_client=qdrant_client)
                self.qdrant_collection = qdrant_collection
                logger.info(f"[ExpertAgent] RAG enabled: collection={qdrant_collection}")
            except Exception as e:
                logger.warning(f"[ExpertAgent] RAG initialization failed: {e}. Running without RAG.")
                self.use_rag = False

        logger.info(f"[ExpertAgent] Initialized (RAG={'enabled' if self.use_rag else 'disabled'})")

    def evaluate_grant(
        self,
        grant_text: str,
        profile: Dict,
        research_text: Optional[str] = None,
        audit_text: Optional[str] = None
    ) -> Dict:
        """
        Evaluate grant application

        Args:
            grant_text: Full grant text
            profile: User profile dictionary
            research_text: Research/investigation text (optional)
            audit_text: Audit/review text (optional)

        Returns:
            {
                "score": 8.5,  # 0-10
                "strengths": ["Clear goals", "Good budget"],
                "weaknesses": ["Too short research section"],
                "recommendations": ["Add more sources", "Expand methodology"],
                "compliance": {
                    "structure": True,
                    "length": True,
                    "required_sections": False,
                    "research_quality": True
                },
                "details": {
                    "grant_length": 18500,
                    "sections_found": 9,
                    "research_sources": 3,
                    "rag_relevance": 0.85
                }
            }
        """
        logger.info(f"[ExpertAgent] Evaluating grant: {profile.get('name', 'Unknown')}")

        # 1. Structure validation
        compliance = self._check_compliance(grant_text, research_text)

        # 2. Content quality checks
        strengths, weaknesses = self._analyze_content_quality(grant_text, compliance)

        # 3. RAG-based evaluation (if enabled)
        rag_score = 0.0
        rag_feedback = []

        if self.use_rag and self.rag_retriever:
            rag_score, rag_feedback = self._evaluate_with_rag(grant_text, profile)

        # 4. Calculate total score
        score = self._calculate_score(compliance, rag_score)

        # 5. Generate recommendations
        recommendations = self._generate_recommendations(weaknesses, rag_feedback)

        # 6. Compile details
        details = {
            "grant_length": len(grant_text),
            "sections_found": compliance["sections_count"],
            "research_sources": compliance.get("research_sources", 0),
            "rag_relevance": rag_score if self.use_rag else None
        }

        result = {
            "score": round(score, 1),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "compliance": {
                "structure": compliance["structure_ok"],
                "length": compliance["length_ok"],
                "required_sections": compliance["required_sections_ok"],
                "research_quality": compliance.get("research_ok", True)
            },
            "details": details
        }

        logger.info(f"[ExpertAgent] Score: {result['score']}/10 - {len(strengths)} strengths, {len(weaknesses)} weaknesses")

        return result

    def _check_compliance(self, grant_text: str, research_text: Optional[str]) -> Dict:
        """
        Check compliance with basic requirements

        Returns:
            Compliance dictionary
        """
        compliance = {}

        # Check length
        grant_length = len(grant_text)
        compliance["length_ok"] = grant_length >= self.MIN_GRANT_LENGTH
        compliance["grant_length"] = grant_length

        # Check sections
        sections_found = sum(1 for section in self.REQUIRED_SECTIONS if section.lower() in grant_text.lower())
        compliance["sections_found"] = sections_found
        compliance["sections_count"] = sections_found
        compliance["required_sections_ok"] = sections_found >= self.MIN_SECTIONS

        # Structure check
        compliance["structure_ok"] = compliance["length_ok"] and compliance["required_sections_ok"]

        # Check research sources (if available)
        if research_text:
            # Count sources (URLs, citations)
            sources_count = research_text.count("http") + research_text.count("источник")
            compliance["research_sources"] = sources_count
            compliance["research_ok"] = sources_count >= self.MIN_RESEARCH_SOURCES
        else:
            compliance["research_sources"] = 0
            compliance["research_ok"] = False

        return compliance

    def _analyze_content_quality(self, grant_text: str, compliance: Dict) -> tuple:
        """
        Analyze content quality

        Returns:
            (strengths, weaknesses) tuple of lists
        """
        strengths = []
        weaknesses = []

        # Length
        if compliance["grant_length"] >= self.MIN_GRANT_LENGTH:
            strengths.append("Достаточный объем текста")
        else:
            weaknesses.append(f"Недостаточный объем: {compliance['grant_length']} символов (требуется >= {self.MIN_GRANT_LENGTH})")

        # Sections
        if compliance["sections_found"] >= self.MIN_SECTIONS:
            strengths.append(f"Все необходимые разделы присутствуют ({compliance['sections_found']})")
        else:
            weaknesses.append(f"Не хватает разделов: {compliance['sections_found']}/{len(self.REQUIRED_SECTIONS)}")

        # Research
        if compliance.get("research_sources", 0) >= self.MIN_RESEARCH_SOURCES:
            strengths.append(f"Качественное исследование ({compliance['research_sources']} источников)")
        elif compliance.get("research_sources", 0) > 0:
            weaknesses.append(f"Недостаточно источников в исследовании ({compliance['research_sources']})")

        # Check for specific quality markers
        quality_markers = {
            "Конкретные цели (SMART)": ["измеримая", "достижимая", "конкретная"],
            "Обоснование бюджета": ["бюджет", "смета", "расходы", "финансирование"],
            "Целевая аудитория": ["целевая аудитория", "участники", "бенефициары"],
            "Ожидаемые результаты": ["результаты", "эффект", "impact", "достижения"]
        }

        for marker_name, keywords in quality_markers.items():
            if any(keyword.lower() in grant_text.lower() for keyword in keywords):
                strengths.append(marker_name)

        return strengths, weaknesses

    def _evaluate_with_rag(self, grant_text: str, profile: Dict) -> tuple:
        """
        Evaluate using RAG retrieval

        Returns:
            (rag_score, rag_feedback) tuple
        """
        try:
            # Query RAG for relevant requirements
            query = f"{profile.get('type', '')} проект {profile.get('goal', '')}"
            results = self.rag_retriever.retrieve(query, top_k=5)

            if not results:
                logger.warning("[ExpertAgent] No RAG results found")
                return 0.0, []

            # Calculate relevance score
            avg_score = sum(r["score"] for r in results) / len(results)

            # Generate feedback based on top results
            feedback = []
            for result in results[:3]:
                if result["score"] > 0.7:
                    feedback.append(f"Соответствие требованиям: {result['text'][:200]}...")

            logger.debug(f"[ExpertAgent] RAG score: {avg_score:.2f}, {len(feedback)} feedback items")

            return avg_score, feedback

        except Exception as e:
            logger.error(f"[ExpertAgent] RAG evaluation failed: {e}")
            return 0.0, []

    def _calculate_score(self, compliance: Dict, rag_score: float) -> float:
        """
        Calculate total score

        Weights:
        - Structure: 30%
        - Length: 20%
        - Sections: 20%
        - Research: 15%
        - RAG: 15%
        """
        score = 0.0

        # Structure (30%)
        if compliance["structure_ok"]:
            score += 3.0

        # Length (20%)
        length_ratio = min(compliance["grant_length"] / self.MIN_GRANT_LENGTH, 1.5)
        score += 2.0 * length_ratio

        # Sections (20%)
        sections_ratio = compliance["sections_found"] / len(self.REQUIRED_SECTIONS)
        score += 2.0 * sections_ratio

        # Research (15%)
        if compliance.get("research_ok", False):
            score += 1.5

        # RAG (15%)
        if self.use_rag:
            score += 1.5 * rag_score

        return min(score, 10.0)

    def _generate_recommendations(self, weaknesses: List[str], rag_feedback: List[str]) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []

        # Convert weaknesses to recommendations
        for weakness in weaknesses:
            if "объем" in weakness.lower():
                recommendations.append("Расширить описание проекта, добавить больше деталей")
            elif "разделов" in weakness.lower():
                recommendations.append("Добавить недостающие разделы заявки")
            elif "источников" in weakness.lower():
                recommendations.append("Провести более глубокое исследование, добавить источники")

        # Add RAG-based recommendations
        if rag_feedback:
            recommendations.append("Учесть требования фондов из базы знаний")

        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("Заявка соответствует требованиям, продолжайте в том же духе")

        return recommendations[:5]  # Top 5 recommendations

    def save_evaluation(self, evaluation: Dict, output_path: Path):
        """
        Save evaluation to JSON file

        Args:
            evaluation: Evaluation result
            output_path: Path to save JSON
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation, f, ensure_ascii=False, indent=2)

            logger.info(f"[ExpertAgent] Evaluation saved: {output_path}")

        except Exception as e:
            logger.error(f"[ExpertAgent] Failed to save evaluation: {e}")


if __name__ == "__main__":
    # Test Expert Agent
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n=== Testing Expert Agent ===\n")

    # Test profile
    profile = {
        "name": "Стрелковый клуб Лучник",
        "type": "sports",
        "goal": "Развитие юношеской секции стрельбы из лука"
    }

    # Test grant text (short)
    grant_text = """
Название проекта: Стрелковый клуб Лучник

Цель проекта: Развитие юношеской секции стрельбы из лука

Задачи проекта:
1. Набор участников
2. Обучение технике стрельбы
3. Организация соревнований

Обоснование проекта: Стрельба из лука развивает концентрацию и дисциплину

Целевая аудитория: Молодежь 12-18 лет

План реализации:
- Месяц 1-3: Набор и обучение
- Месяц 4-6: Тренировки
- Месяц 7-12: Соревнования

Бюджет: 500,000 рублей

Ожидаемые результаты: 50 обученных участников
""" * 20  # Repeat to meet length requirement

    # Initialize expert (without RAG for testing)
    expert = ExpertAgent(use_rag=False)

    # Evaluate
    evaluation = expert.evaluate_grant(
        grant_text=grant_text,
        profile=profile,
        research_text="Исследование показало высокий интерес к стрельбе из лука. Источник: http://example.com"
    )

    # Print results
    print(f"Score: {evaluation['score']}/10\n")

    print("Strengths:")
    for strength in evaluation['strengths']:
        print(f"  + {strength}")

    print("\nWeaknesses:")
    for weakness in evaluation['weaknesses']:
        print(f"  - {weakness}")

    print("\nRecommendations:")
    for i, rec in enumerate(evaluation['recommendations'], 1):
        print(f"  {i}. {rec}")

    print("\nCompliance:")
    for key, value in evaluation['compliance'].items():
        print(f"  {key}: {'✓' if value else '✗'}")

    print("\nDetails:")
    for key, value in evaluation['details'].items():
        print(f"  {key}: {value}")
