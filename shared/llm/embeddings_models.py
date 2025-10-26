"""
Pydantic models for GigaChat Embeddings collections

This module defines data schemas for 3 optimized Qdrant collections:
1. fpg_real_winners - real FPG grant winners from web
2. fpg_requirements_gigachat - consolidated requirements/methodologies/budgets
3. user_grants_all - user grants from PostgreSQL grant_applications

Iteration 51: AI Enhancement - Embeddings + RL
Date: 2025-10-26
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Collection 1: fpg_real_winners (1.2M tokens)
# ============================================================================

class FPGRealWinner(BaseModel):
    """
    Single real FPG grant winner from web (Perplexity/Parallel AI)

    Source: Web scraping победителей ФПГ 2020-2024
    Embedding: GigaChat Embeddings API (1024-dim)
    Vectors per grant: 4 (problem, solution, kpi, budget)
    """
    # Core fields
    title: str = Field(..., description="Название проекта")
    organization: str = Field(..., description="Организация-победитель")

    # Content fields (будут векторизованы отдельно)
    problem: str = Field(..., description="Описание проблемы (300-500 слов)")
    solution: str = Field(..., description="Решение (500-1000 слов)")
    kpi: str = Field(..., description="Измеримые результаты (KPI)")
    budget: str = Field(..., description="Бюджет и статьи расходов")

    # Structured fields
    target_audience: Optional[str] = Field(None, description="Целевая аудитория")
    social_impact: Optional[str] = Field(None, description="Социальная значимость")

    # Metadata (для фильтрации в Qdrant)
    fund_name: str = Field(..., description="ФПГ/РНФ/РФФИ")
    year: int = Field(..., description="Год победы")
    region: Optional[str] = Field(None, description="Регион")
    amount: Optional[int] = Field(None, description="Сумма гранта (руб)")
    category: Optional[str] = Field(None, description="Категория конкурса")
    rating_score: Optional[float] = Field(None, description="Экспертная оценка (если доступна)")

    # Service fields
    source_url: Optional[str] = Field(None, description="URL источника")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Дата парсинга")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Развитие научного творчества школьников",
                "organization": "Фонд поддержки науки",
                "problem": "Низкая вовлеченность школьников в научные исследования...",
                "solution": "Создание сети научных лабораторий для школьников...",
                "kpi": "1000 школьников участвуют в исследованиях, 50 публикаций...",
                "budget": "Оборудование: 1.5 млн руб, Зарплаты: 800 тыс руб...",
                "target_audience": "Школьники 14-17 лет",
                "social_impact": "Популяризация науки среди молодежи",
                "fund_name": "ФПГ",
                "year": 2024,
                "region": "Москва",
                "amount": 3000000,
                "category": "Образование"
            }
        }


class FPGRealWinnerVector(BaseModel):
    """
    Single vector for Qdrant storage from FPGRealWinner

    Each grant creates 4 vectors: problem, solution, kpi, budget
    """
    grant_id: str = Field(..., description="Unique ID: {fund}_{year}_{title_slug}")
    section: str = Field(..., description="problem | solution | kpi | budget")
    text: str = Field(..., description="Text to embed")

    # Metadata payload (for Qdrant)
    metadata: Dict[str, Any] = Field(..., description="All FPGRealWinner fields")


# ============================================================================
# Collection 2: fpg_requirements_gigachat (1M tokens)
# ============================================================================

class GrantCriterion(BaseModel):
    """
    Grant evaluation criterion from specific fund

    Part of fpg_requirements_gigachat collection (40% of content)
    """
    fund_name: str = Field(..., description="ФПГ/РНФ/РФФИ/региональные")
    criterion_name: str = Field(..., description="Название критерия")
    criterion_description: str = Field(..., description="Описание критерия")
    weight: float = Field(..., ge=0, le=100, description="Вес в оценке (0-100%)")
    requirements: str = Field(..., description="Конкретные требования")
    examples: Optional[str] = Field(None, description="Примеры соответствия")

    class Config:
        json_schema_extra = {
            "example": {
                "fund_name": "ФПГ",
                "criterion_name": "Социальная значимость",
                "criterion_description": "Оценка влияния проекта на общество",
                "weight": 30.0,
                "requirements": "Четкое описание целевой аудитории, измеримые социальные эффекты",
                "examples": "Снижение безработицы на 15%, охват 5000 человек"
            }
        }


class ResearchMethodology(BaseModel):
    """
    Research methodology description (SMART, Agile, Design Thinking, etc.)

    Part of fpg_requirements_gigachat collection (30% of content)
    """
    methodology_name: str = Field(..., description="SMART, Agile, Design Thinking")
    description: str = Field(..., description="Описание методологии")
    application_area: Optional[str] = Field(None, description="Область применения")
    kpi_examples: Optional[List[str]] = Field(None, description="Примеры KPI")
    smart_goals_examples: Optional[List[str]] = Field(None, description="Примеры SMART-целей")

    class Config:
        json_schema_extra = {
            "example": {
                "methodology_name": "SMART",
                "description": "Specific, Measurable, Achievable, Relevant, Time-bound",
                "application_area": "Постановка целей проекта",
                "kpi_examples": ["Охват: 1000 человек за 6 месяцев", "Удовлетворенность: 85%+"],
                "smart_goals_examples": ["Провести 50 мероприятий для 1000 участников до 31.12.2025"]
            }
        }


class BudgetTemplate(BaseModel):
    """
    Budget template from winning grant applications

    Part of fpg_requirements_gigachat collection (30% of content)
    """
    fund_name: str = Field(..., description="Фонд")
    project_type: str = Field(..., description="Тип проекта")
    budget_categories: List[str] = Field(..., description="Категории расходов")
    justification: str = Field(..., description="Обоснование бюджета")
    total_amount: int = Field(..., description="Общая сумма (руб)")
    duration_months: int = Field(..., description="Длительность (месяцев)")

    class Config:
        json_schema_extra = {
            "example": {
                "fund_name": "ФПГ",
                "project_type": "Образовательный",
                "budget_categories": [
                    "Оборудование: 1,500,000 руб",
                    "Зарплаты: 800,000 руб",
                    "Материалы: 200,000 руб",
                    "Аренда: 300,000 руб",
                    "Прочие: 200,000 руб"
                ],
                "justification": "Оборудование необходимо для создания 3 лабораторий...",
                "total_amount": 3000000,
                "duration_months": 12
            }
        }


class FPGRequirement(BaseModel):
    """
    Consolidated requirement (criterion OR methodology OR budget)

    Unified model for fpg_requirements_gigachat collection
    """
    requirement_type: str = Field(..., description="criterion | methodology | budget")
    content: str = Field(..., description="Main text content")
    fund_name: Optional[str] = Field(None, description="Фонд (if applicable)")
    category: Optional[str] = Field(None, description="Category/domain")

    # Raw data (one of these will be filled)
    criterion_data: Optional[GrantCriterion] = None
    methodology_data: Optional[ResearchMethodology] = None
    budget_data: Optional[BudgetTemplate] = None


# ============================================================================
# Collection 3: user_grants_all (800K tokens)
# ============================================================================

class UserGrantSection(BaseModel):
    """
    Single section of user grant application

    Source: PostgreSQL grant_applications.content_json
    10 sections per grant × 174 grants = 1,740 vectors
    """
    # Grant metadata
    grant_id: int = Field(..., description="grant_applications.id")
    user_id: Optional[int] = Field(None, description="User ID")
    title: str = Field(..., description="Grant title")

    # Section data
    section_name: str = Field(
        ...,
        description="problem | solution | target_audience | goals | methodology | timeline | budget | team | risks | impact"
    )
    section_content: str = Field(..., description="Section text content")

    # Application metadata (for Qdrant filtering)
    status: str = Field(..., description="draft | approved | submitted")
    quality_score: Optional[float] = Field(None, description="ReviewerAgent score (0-10)")
    created_at: datetime = Field(..., description="Creation date")
    fund_target: Optional[str] = Field(None, description="Целевой фонд")

    class Config:
        json_schema_extra = {
            "example": {
                "grant_id": 123,
                "user_id": 456,
                "title": "Развитие молодежного спорта",
                "section_name": "problem",
                "section_content": "В нашем регионе недостаточно спортивных секций для молодежи...",
                "status": "approved",
                "quality_score": 8.5,
                "created_at": "2024-10-15T10:30:00",
                "fund_target": "ФПГ"
            }
        }


# ============================================================================
# Qdrant Collection Schemas
# ============================================================================

class QdrantCollectionConfig(BaseModel):
    """
    Configuration for Qdrant collection creation
    """
    collection_name: str
    vector_size: int = Field(default=1024, description="GigaChat Embeddings dimension")
    distance: str = Field(default="Cosine", description="Distance metric")
    on_disk: bool = Field(default=True, description="Store on disk for large collections")

    class Config:
        json_schema_extra = {
            "fpg_real_winners": {
                "collection_name": "fpg_real_winners",
                "vector_size": 1024,
                "distance": "Cosine",
                "on_disk": True
            },
            "fpg_requirements_gigachat": {
                "collection_name": "fpg_requirements_gigachat",
                "vector_size": 1024,
                "distance": "Cosine",
                "on_disk": True
            },
            "user_grants_all": {
                "collection_name": "user_grants_all",
                "vector_size": 1024,
                "distance": "Cosine",
                "on_disk": True
            }
        }
