"""
FPG Requirements Parser - Extract evaluation criteria, methodologies, and budget templates

This script parses fpg_parallel_ai_analysis.json to create fpg_requirements_gigachat collection.

Content distribution:
- 40% Evaluation criteria (GrantCriterion)
- 30% Research methodologies (ResearchMethodology)
- 30% Budget templates (BudgetTemplate)

Iteration 51: AI Enhancement - Phase 2
Date: 2025-10-26

Usage:
    python scripts/fpg_requirements_parser.py

Expected tokens: ~1M tokens
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import Pydantic models
from shared.llm.embeddings_models import (
    GrantCriterion,
    ResearchMethodology,
    BudgetTemplate,
    FPGRequirement
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FPGRequirementsParser:
    """
    Parser for FPG requirements from Parallel AI analysis

    Structure:
    - 40% Evaluation criteria (6-8 criteria)
    - 30% Research methodologies (4-5 methodologies)
    - 30% Budget templates (9 categories)
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.requirements: List[FPGRequirement] = []

    def parse_json_analysis(self, filepath: Path) -> Dict[str, Any]:
        """
        Load fpg_parallel_ai_analysis.json
        """
        logger.info(f"[LOAD] Reading {filepath.name}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"[OK] JSON loaded successfully\n")
        return data

    def extract_evaluation_criteria(self, analysis: Dict[str, Any]) -> List[GrantCriterion]:
        """
        Extract evaluation criteria (40% of content)

        Criteria from analysis:
        1. Realism of project budget
        2. Social significance
        3. Logical connection (budget-plan-objectives)
        4. Co-financing level
        5. Sustainability planning
        6. Innovation and competitive advantage
        """
        logger.info("[CRITERIA] Extracting evaluation criteria...")

        criteria = []

        # Criterion 1: Realism of project budget
        criteria.append(GrantCriterion(
            fund_name="ФПГ",
            criterion_name="Реалистичность бюджета проекта",
            criterion_description="Оценка реалистичности и обоснованности бюджета проекта",
            weight=30.0,  # High weight (multiplier 1.5 in PFCI)
            requirements=analysis['output']['budget_justification_and_cost_efficiency']['line_item_justification_requirements'],
            examples=analysis['output']['budget_justification_and_cost_efficiency']['price_benchmarking_guidance']
        ))

        # Criterion 2: Social significance
        criteria.append(GrantCriterion(
            fund_name="ФПГ",
            criterion_name="Социальная значимость",
            criterion_description="Оценка влияния проекта на общество и решение социальных проблем",
            weight=25.0,
            requirements=analysis['output']['social_impact_and_community_engagement'][:500],
            examples=analysis['output']['target_audience_and_needs_assessment_guide'][:500]
        ))

        # Criterion 3: Logical connection
        criteria.append(GrantCriterion(
            fund_name="ФПГ",
            criterion_name="Логическая связь бюджета и плана",
            criterion_description="Соответствие бюджета календарному плану и целям проекта",
            weight=20.0,
            requirements=analysis['output']['budget_justification_and_cost_efficiency']['link_to_project_plan'],
            examples=analysis['output']['solution_articulation_blueprint']['implementation_timeline_and_milestones'][:500]
        ))

        # Criterion 4: Co-financing level
        criteria.append(GrantCriterion(
            fund_name="ФПГ",
            criterion_name="Уровень софинансирования",
            criterion_description="Доля собственного вклада организации в проект",
            weight=15.0,
            requirements=analysis['output']['co_financing_and_sustainability_planning']['co_financing_guidelines'],
            examples="Идеальный уровень: 25%+, оптимальный: 50%+. Средний по ФПГ 2024: 92%"
        ))

        # Criterion 5: Sustainability planning
        criteria.append(GrantCriterion(
            fund_name="ФПГ",
            criterion_name="План устойчивости",
            criterion_description="Стратегия продолжения проекта после окончания гранта",
            weight=10.0,
            requirements=analysis['output']['co_financing_and_sustainability_planning']['sustainability_strategy_components'],
            examples=analysis['output']['co_financing_and_sustainability_planning']['post_grant_revenue_generation']
        ))

        logger.info(f"[OK] Extracted {len(criteria)} evaluation criteria\n")
        return criteria

    def extract_methodologies(self, analysis: Dict[str, Any]) -> List[ResearchMethodology]:
        """
        Extract research methodologies (30% of content)

        Methodologies:
        1. SMART Goals
        2. Logic Model / Theory of Change
        3. Risk Management
        4. Monitoring & Evaluation (M&E)
        """
        logger.info("[METHODOLOGIES] Extracting research methodologies...")

        methodologies = []

        # Methodology 1: SMART Goals
        methodologies.append(ResearchMethodology(
            methodology_name="SMART Goals",
            description="Specific, Measurable, Achievable, Relevant, Time-bound цели проекта",
            application_area="Постановка целей и задач проекта",
            kpi_examples=[
                "Провести 50 мероприятий для 1000 участников до 31.12.2025",
                "Охват: 500 молодых людей из группы риска за 6 месяцев",
                "Достижение 20% улучшения показателей психического здоровья участников"
            ],
            smart_goals_examples=[
                "Обучить 100 волонтёров навыкам работы с бездомными к концу первого квартала",
                "Открыть 3 новых центра помощи в регионах к июню 2025",
                "Достичь уровня удовлетворённости участников 85%+ по итогам проекта"
            ]
        ))

        # Methodology 2: Logic Model / Theory of Change
        methodologies.append(ResearchMethodology(
            methodology_name="Logic Model (Theory of Change)",
            description="Логическая модель причинно-следственных связей: ресурсы → активности → результаты → влияние",
            application_area="Проектирование логики проекта и обоснование бюджета",
            kpi_examples=[
                "Inputs: 3 млн руб гранта + 2 млн софинансирование",
                "Activities: 20 воркшопов, 5 тренингов, 10 публичных событий",
                "Outputs: 1000 обученных участников, 50 публикаций",
                "Outcomes: Снижение безработицы на 15%, рост вовлечённости в НКО на 25%"
            ],
            smart_goals_examples=[
                analysis['output']['solution_articulation_blueprint']['theory_of_change_narrative'][:200]
            ]
        ))

        # Methodology 3: Risk Management
        methodologies.append(ResearchMethodology(
            methodology_name="Risk Management (Управление рисками)",
            description="Систематический подход к идентификации, оценке и митигации рисков проекта",
            application_area="Планирование рисков и разработка стратегий их снижения",
            kpi_examples=[
                "Риск: низкая явка участников (вероятность: средняя, влияние: высокое)",
                "Митигация: дополнительные каналы рекрутинга, материальные стимулы",
                "Риск: задержка поставки оборудования (вероятность: низкая, влияние: среднее)"
            ],
            smart_goals_examples=[
                analysis['output']['risk_management_and_monitoring_plans']['risk_register_guidelines'][:200]
            ]
        ))

        # Methodology 4: Monitoring & Evaluation (M&E)
        methodologies.append(ResearchMethodology(
            methodology_name="Monitoring & Evaluation (M&E)",
            description="Система непрерывного отслеживания прогресса и итоговой оценки результатов проекта",
            application_area="Мониторинг прогресса и оценка эффективности проекта",
            kpi_examples=[
                "Мониторинг: ежемесячные отчёты по охвату участников",
                "Оценка: опросы до/после участия, анализ изменений показателей",
                "Данные: регистрационные формы, post-event surveys, фокус-группы"
            ],
            smart_goals_examples=[
                analysis['output']['risk_management_and_monitoring_plans']['monitoring_plan_structure'][:200],
                analysis['output']['risk_management_and_monitoring_plans']['evaluation_plan_structure'][:200]
            ]
        ))

        logger.info(f"[OK] Extracted {len(methodologies)} methodologies\n")
        return methodologies

    def extract_budget_templates(self, analysis: Dict[str, Any]) -> List[BudgetTemplate]:
        """
        Extract budget templates (30% of content)

        9 standard budget categories from FPG methodology
        """
        logger.info("[BUDGETS] Extracting budget templates...")

        budget_categories_data = analysis['output']['standard_budget_categories']

        templates = []

        # Create budget template for each category
        for category_data in budget_categories_data:
            category_name = category_data['category_name']
            description = category_data['description_and_examples']

            # Create template
            template = BudgetTemplate(
                fund_name="ФПГ",
                project_type="Универсальный шаблон",
                budget_categories=[f"{category_name}: {description[:200]}..."],
                justification=description,
                total_amount=3000000,  # Example: 3M rubles average
                duration_months=12
            )

            templates.append(template)

        logger.info(f"[OK] Extracted {len(templates)} budget templates\n")
        return templates

    def create_fpg_requirement_objects(
        self,
        criteria: List[GrantCriterion],
        methodologies: List[ResearchMethodology],
        budget_templates: List[BudgetTemplate]
    ) -> List[FPGRequirement]:
        """
        Convert parsed data to FPGRequirement Pydantic objects
        """
        logger.info("[CONVERT] Creating FPGRequirement objects...")

        requirements = []

        # Add criteria (40%)
        for criterion in criteria:
            req = FPGRequirement(
                requirement_type="criterion",
                content=f"{criterion.criterion_name}: {criterion.criterion_description}. {criterion.requirements}",
                fund_name=criterion.fund_name,
                category="Evaluation Criteria",
                criterion_data=criterion
            )
            requirements.append(req)

        # Add methodologies (30%)
        for methodology in methodologies:
            req = FPGRequirement(
                requirement_type="methodology",
                content=f"{methodology.methodology_name}: {methodology.description}. {' '.join(methodology.kpi_examples or [])}",
                fund_name="ФПГ",
                category="Research Methodologies",
                methodology_data=methodology
            )
            requirements.append(req)

        # Add budget templates (30%)
        for template in budget_templates:
            req = FPGRequirement(
                requirement_type="budget",
                content=f"Budget Category: {' '.join(template.budget_categories)}. {template.justification}",
                fund_name=template.fund_name,
                category="Budget Templates",
                budget_data=template
            )
            requirements.append(req)

        logger.info(f"[OK] Created {len(requirements)} FPGRequirement objects\n")
        return requirements

    def parse_all_sources(self) -> List[FPGRequirement]:
        """
        Parse all requirements from JSON analysis
        """
        logger.info("[START] Starting FPG requirements parsing...\n")

        # Load JSON
        json_file = self.data_dir / "fpg_parallel_ai_analysis.json"
        if not json_file.exists():
            logger.error(f"[ERROR] File not found: {json_file}")
            return []

        analysis = self.parse_json_analysis(json_file)

        # Extract components
        criteria = self.extract_evaluation_criteria(analysis)
        methodologies = self.extract_methodologies(analysis)
        budget_templates = self.extract_budget_templates(analysis)

        # Convert to FPGRequirement objects
        requirements = self.create_fpg_requirement_objects(
            criteria,
            methodologies,
            budget_templates
        )

        self.requirements = requirements
        return requirements

    def save_to_json(self, output_file: Path):
        """
        Save parsed requirements to JSON file for embeddings
        """
        logger.info(f"[SAVE] Saving to {output_file}...")

        requirements_json = [req.model_dump(mode='json') for req in self.requirements]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(requirements_json, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"[OK] Saved {len(requirements_json)} requirements to {output_file}\n")

    def print_statistics(self):
        """Print dataset statistics"""
        if not self.requirements:
            logger.info("[WARN] No requirements parsed yet")
            return

        logger.info("[STATS] Dataset Statistics:")
        logger.info(f"  Total requirements: {len(self.requirements)}")

        # By type
        types = {}
        for req in self.requirements:
            types[req.requirement_type] = types.get(req.requirement_type, 0) + 1

        logger.info(f"\n  By type:")
        for req_type, count in sorted(types.items()):
            percentage = count / len(self.requirements) * 100
            logger.info(f"    {req_type}: {count} ({percentage:.1f}%)")

        # Content length statistics
        content_lengths = [len(req.content) for req in self.requirements]

        logger.info(f"\n  Content lengths:")
        logger.info(f"    Min: {min(content_lengths)} chars")
        logger.info(f"    Max: {max(content_lengths)} chars")
        logger.info(f"    Avg: {sum(content_lengths)//len(content_lengths)} chars")


def main():
    """Main entry point"""
    # Paths
    iteration_dir = Path(__file__).parent.parent / "iterations" / "Iteration_51_AI_Enhancement"
    output_file = iteration_dir / "fpg_requirements_dataset.json"

    # Parse data
    parser = FPGRequirementsParser(iteration_dir)
    requirements = parser.parse_all_sources()

    # Save results
    parser.save_to_json(output_file)

    # Print statistics
    parser.print_statistics()

    logger.info(f"\n[DONE] Dataset ready for GigaChat Embeddings API")
    logger.info(f"[OUTPUT] File: {output_file}")


if __name__ == "__main__":
    main()
