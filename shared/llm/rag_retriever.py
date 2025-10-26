"""
RAG (Retrieval Augmented Generation) retriever for WriterAgent

Uses GigaChat Embeddings + Qdrant to retrieve relevant examples from:
- fpg_real_winners: 17 real FPG grant winners (42 vectors)
- fpg_requirements_gigachat: Criteria, methodologies, budgets (18 vectors)

Iteration 51: AI Enhancement - Phase 4
Date: 2025-10-26
"""

from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class QdrantRAGRetriever:
    """
    RAG retriever for WriterAgent using GigaChat Embeddings + Qdrant

    Strategy: Hybrid approach
    - Upfront retrieval: Top-3 similar grants for general context
    - Section-specific retrieval: Targeted examples per section

    Collections:
    - fpg_real_winners: Real FPG grants (problem, solution, kpi, budget)
    - fpg_requirements_gigachat: Criteria, methodologies, budget templates
    """

    def __init__(self, qdrant_client: QdrantClient, embeddings_client):
        """
        Initialize RAG retriever

        Args:
            qdrant_client: Qdrant client instance
            embeddings_client: GigaChatEmbeddingsClient instance
        """
        self.qdrant = qdrant_client
        self.embeddings = embeddings_client

        # Collection names
        self.WINNERS_COLLECTION = "fpg_real_winners"
        self.REQUIREMENTS_COLLECTION = "fpg_requirements_gigachat"

        logger.info("[OK] QdrantRAGRetriever: Initialized")

    def retrieve_similar_grants(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Upfront retrieval: Find top-k most similar grants

        Args:
            query_text: Project description to search for
            top_k: Number of grants to retrieve (default: 3)

        Returns:
            List of grant dictionaries with metadata and all sections

        Example:
            [
                {
                    "title": "Развитие молодежного спорта",
                    "organization": "Спортивный фонд",
                    "year": 2023,
                    "amount": 2500000,
                    "category": "Физическая культура",
                    "problem": "В регионе низкая физическая активность...",
                    "solution": "Создание сети спортивных площадок...",
                    "kpi": "1000 участников, 85% удовлетворенность",
                    "budget": "Оборудование: 1.5 млн, Зарплаты: 800 тыс"
                },
                ...
            ]
        """
        try:
            logger.info(f"[SEARCH] RAG: Retrieving similar grants for: '{query_text[:100]}...'")

            # Embed query
            query_vector = self.embeddings.embed_text(query_text)

            # Search in fpg_real_winners collection
            search_results = self.qdrant.search(
                collection_name=self.WINNERS_COLLECTION,
                query_vector=query_vector,
                limit=top_k * 4  # Get more results since we need to group by grant_id
            )

            # Group results by grant_id (each grant has 4 vectors)
            grants_dict = {}
            for result in search_results:
                grant_id = result.payload.get("grant_id")
                section = result.payload.get("section")

                if grant_id not in grants_dict:
                    grants_dict[grant_id] = {
                        "grant_id": grant_id,
                        "title": result.payload.get("title", ""),
                        "organization": result.payload.get("organization", ""),
                        "year": result.payload.get("year", 0),
                        "amount": result.payload.get("amount", 0),
                        "category": result.payload.get("category", ""),
                        "fund_name": result.payload.get("fund_name", ""),
                        "region": result.payload.get("region", ""),
                        "max_score": result.score,
                        "problem": "",
                        "solution": "",
                        "kpi": "",
                        "budget": ""
                    }

                # Add section content
                if section in ["problem", "solution", "kpi", "budget"]:
                    grants_dict[grant_id][section] = result.payload.get("text", "")

                # Update max score if this section scored higher
                grants_dict[grant_id]["max_score"] = max(
                    grants_dict[grant_id]["max_score"],
                    result.score
                )

            # Sort by max_score and take top_k
            sorted_grants = sorted(
                grants_dict.values(),
                key=lambda g: g["max_score"],
                reverse=True
            )[:top_k]

            logger.info(f"[OK] RAG: Retrieved {len(sorted_grants)} similar grants")
            for i, grant in enumerate(sorted_grants):
                logger.info(f"  {i+1}. {grant['title']} (score: {grant['max_score']:.3f})")

            return sorted_grants

        except Exception as e:
            logger.error(f"[ERROR] RAG: Failed to retrieve similar grants - {e}")
            return []

    def retrieve_section_examples(
        self,
        section_name: str,
        query_text: str,
        top_k: int = 2
    ) -> List[str]:
        """
        Section-specific retrieval from fpg_real_winners

        Args:
            section_name: Section type ("problem" | "solution" | "kpi" | "budget")
            query_text: Query for semantic search
            top_k: Number of examples (default: 2)

        Returns:
            List of text examples with metadata

        Example:
            [
                "Проблема: В регионе наблюдается снижение...\n(Проект: Молодежный спорт, 2023, 2.5 млн руб.)",
                "Проблема: Современные школьники испытывают...\n(Проект: Киноклуб, 2024, 1.8 млн руб.)"
            ]
        """
        try:
            logger.info(f"[SEARCH] RAG: Retrieving {section_name} examples for: '{query_text[:100]}...'")

            # Validate section_name
            valid_sections = ["problem", "solution", "kpi", "budget"]
            if section_name not in valid_sections:
                logger.warning(f"[WARNING] RAG: Invalid section '{section_name}', must be one of {valid_sections}")
                return []

            # Embed query
            query_vector = self.embeddings.embed_text(query_text)

            # Search with filter for specific section
            search_results = self.qdrant.search(
                collection_name=self.WINNERS_COLLECTION,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="section",
                            match=MatchValue(value=section_name)
                        )
                    ]
                ),
                limit=top_k
            )

            # Format results
            examples = []
            for result in search_results:
                text = result.payload.get("text", "")
                title = result.payload.get("title", "Неизвестный проект")
                year = result.payload.get("year", "")
                amount = result.payload.get("amount", 0)

                # Format amount
                amount_str = f"{amount/1000000:.1f} млн руб." if amount >= 1000000 else f"{amount/1000:.0f} тыс. руб."

                # Create formatted example
                example = f"{text}\n\n(Проект: {title}, {year}, {amount_str}, similarity: {result.score:.2f})"
                examples.append(example)

            logger.info(f"[OK] RAG: Retrieved {len(examples)} {section_name} examples")

            return examples

        except Exception as e:
            logger.error(f"[ERROR] RAG: Failed to retrieve {section_name} examples - {e}")
            return []

    def retrieve_requirements(
        self,
        requirement_type: str,
        query_text: str,
        top_k: int = 2
    ) -> List[str]:
        """
        Retrieve requirements/methodologies/templates from fpg_requirements_gigachat

        Args:
            requirement_type: Type ("criterion" | "methodology" | "budget")
            query_text: Query for semantic search
            top_k: Number of requirements (default: 2)

        Returns:
            List of requirement descriptions

        Example:
            [
                "SMART-цели: Specific, Measurable, Achievable, Relevant, Time-bound\nПример: Провести 50 мероприятий для 1000 участников до 31.12.2025",
                "Логическая модель: Вход → Процесс → Выход → Результат → Эффект"
            ]
        """
        try:
            logger.info(f"[SEARCH] RAG: Retrieving {requirement_type} requirements for: '{query_text[:100]}...'")

            # Validate requirement_type
            valid_types = ["criterion", "methodology", "budget"]
            if requirement_type not in valid_types:
                logger.warning(f"[WARNING] RAG: Invalid type '{requirement_type}', must be one of {valid_types}")
                return []

            # Embed query
            query_vector = self.embeddings.embed_text(query_text)

            # Search with filter for specific requirement type
            search_results = self.qdrant.search(
                collection_name=self.REQUIREMENTS_COLLECTION,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="requirement_type",
                            match=MatchValue(value=requirement_type)
                        )
                    ]
                ),
                limit=top_k
            )

            # Format results
            requirements = []
            for result in search_results:
                content = result.payload.get("content", "")
                requirements.append(f"{content}\n(similarity: {result.score:.2f})")

            logger.info(f"[OK] RAG: Retrieved {len(requirements)} {requirement_type} requirements")

            return requirements

        except Exception as e:
            logger.error(f"[ERROR] RAG: Failed to retrieve {requirement_type} requirements - {e}")
            return []


# ============================================================================
# Helper Functions for Prompt Formatting
# ============================================================================

def format_grant_for_prompt(grant: Dict[str, Any]) -> str:
    """
    Format retrieved grant for prompt injection

    Args:
        grant: Grant dictionary from retrieve_similar_grants()

    Returns:
        Formatted string for prompt injection

    Example:
        ---
        ПРИМЕР УСПЕШНОЙ ЗАЯВКИ:
        Проект: Развитие молодежного спорта
        Организация: Спортивный фонд
        Год: 2023, Сумма: 2,500,000 руб., Категория: Физическая культура

        Проблема: В регионе наблюдается...
        Решение: Создание сети площадок...
        ---
    """
    title = grant.get("title", "Неизвестный проект")
    org = grant.get("organization", "")
    year = grant.get("year", "")
    amount = grant.get("amount", 0)
    category = grant.get("category", "")

    # Format amount
    if amount >= 1000000:
        amount_str = f"{amount/1000000:.1f} млн руб."
    elif amount > 0:
        amount_str = f"{amount/1000:.0f} тыс. руб."
    else:
        amount_str = "сумма не указана"

    # Build formatted string
    formatted = "---\n"
    formatted += "ПРИМЕР УСПЕШНОЙ ЗАЯВКИ:\n"
    formatted += f"Проект: {title}\n"

    if org:
        formatted += f"Организация: {org}\n"

    formatted += f"Год: {year}, Сумма: {amount_str}"
    if category:
        formatted += f", Категория: {category}"
    formatted += "\n\n"

    # Add sections (if not empty)
    if grant.get("problem"):
        formatted += f"Проблема:\n{grant['problem']}\n\n"

    if grant.get("solution"):
        formatted += f"Решение:\n{grant['solution']}\n\n"

    if grant.get("kpi"):
        formatted += f"Результаты (KPI):\n{grant['kpi']}\n\n"

    if grant.get("budget"):
        formatted += f"Бюджет:\n{grant['budget']}\n\n"

    formatted += "---\n"

    return formatted


def format_requirements_for_prompt(requirements: List[str]) -> str:
    """
    Format requirements/methodologies for prompt injection

    Args:
        requirements: List of requirement strings

    Returns:
        Formatted string for prompt injection

    Example:
        ---
        РЕКОМЕНДУЕМЫЕ МЕТОДОЛОГИИ:

        1. SMART-цели: Specific, Measurable, Achievable, Relevant, Time-bound
           Пример: "Провести 50 мероприятий для 1000 участников до 31.12.2025"

        2. Логическая модель: Вход → Процесс → Выход → Результат → Эффект
        ---
    """
    if not requirements:
        return ""

    formatted = "---\n"
    formatted += "РЕКОМЕНДУЕМЫЕ МЕТОДОЛОГИИ:\n\n"

    for i, req in enumerate(requirements):
        formatted += f"{i+1}. {req}\n\n"

    formatted += "---\n"

    return formatted


def format_section_examples_for_prompt(
    section_name: str,
    examples: List[str]
) -> str:
    """
    Format section examples for prompt injection

    Args:
        section_name: Section name ("problem", "solution", etc.)
        examples: List of example strings

    Returns:
        Formatted string for prompt injection

    Example:
        ---
        ПРИМЕРЫ ОПИСАНИЯ ПРОБЛЕМЫ:

        1. В регионе наблюдается снижение физической активности...
           (Проект: Молодежный спорт, 2023, 2.5 млн руб.)

        2. Современные школьники испытывают дефицит медиаграмотности...
           (Проект: Киноклуб, 2024, 1.8 млн руб.)
        ---
    """
    if not examples:
        return ""

    # Map section name to Russian
    section_names_ru = {
        "problem": "ПРОБЛЕМЫ",
        "solution": "РЕШЕНИЯ",
        "kpi": "РЕЗУЛЬТАТОВ (KPI)",
        "budget": "БЮДЖЕТА"
    }

    section_ru = section_names_ru.get(section_name, section_name.upper())

    formatted = "---\n"
    formatted += f"ПРИМЕРЫ ОПИСАНИЯ {section_ru}:\n\n"

    for i, example in enumerate(examples):
        formatted += f"{i+1}. {example}\n\n"

    formatted += "---\n"

    return formatted


# ============================================================================
# Utility Functions
# ============================================================================

def test_rag_retriever():
    """
    Test RAG retriever with sample queries

    Usage:
        python -c "from shared.llm.rag_retriever import test_rag_retriever; test_rag_retriever()"
    """
    try:
        from qdrant_client import QdrantClient
        from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient

        # Initialize clients
        qdrant = QdrantClient(":memory:")  # Or production URL
        embeddings = GigaChatEmbeddingsClient()

        # Initialize RAG retriever
        retriever = QdrantRAGRetriever(qdrant, embeddings)

        # Test 1: Retrieve similar grants
        print("\n" + "="*80)
        print("TEST 1: Retrieve Similar Grants")
        print("="*80)

        grants = retriever.retrieve_similar_grants(
            query_text="Проект по развитию молодежного предпринимательства в регионе",
            top_k=3
        )

        print(f"\nRetrieved {len(grants)} grants:")
        for i, grant in enumerate(grants):
            print(f"\n{i+1}. {grant['title']}")
            print(f"   Score: {grant.get('max_score', 0):.3f}")
            print(f"   Organization: {grant['organization']}")
            print(f"   Year: {grant['year']}, Amount: {grant['amount']} руб.")

        # Test 2: Retrieve section examples
        print("\n" + "="*80)
        print("TEST 2: Retrieve Problem Examples")
        print("="*80)

        examples = retriever.retrieve_section_examples(
            section_name="problem",
            query_text="Молодежная безработица и низкая экономическая активность",
            top_k=2
        )

        print(f"\nRetrieved {len(examples)} examples:")
        for i, example in enumerate(examples):
            print(f"\n{i+1}. {example[:200]}...")

        # Test 3: Retrieve requirements
        print("\n" + "="*80)
        print("TEST 3: Retrieve Methodologies")
        print("="*80)

        requirements = retriever.retrieve_requirements(
            requirement_type="methodology",
            query_text="Постановка целей и измерение результатов проекта",
            top_k=2
        )

        print(f"\nRetrieved {len(requirements)} methodologies:")
        for i, req in enumerate(requirements):
            print(f"\n{i+1}. {req[:200]}...")

        print("\n" + "="*80)
        print("[OK] ALL TESTS PASSED")
        print("="*80)

    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run tests when module is executed directly
    test_rag_retriever()
