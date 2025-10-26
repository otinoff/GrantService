"""
Load FPG Requirements to Qdrant with GigaChat Embeddings

This script loads fpg_requirements_gigachat collection to Qdrant.

Content: 18 requirements
- 5 evaluation criteria
- 4 research methodologies
- 9 budget templates

Iteration 51: AI Enhancement - Phase 2
Date: 2025-10-26

Usage:
    python scripts/load_fpg_requirements_to_qdrant.py

Expected tokens: ~1M tokens (18 requirements × ~50K tokens avg)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Import Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError:
    print("[ERROR] qdrant-client not installed")
    sys.exit(1)

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import custom modules
from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient
from shared.llm.embeddings_models import FPGRequirement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QdrantFPGRequirementsLoader:
    """
    Loader for FPG Requirements to Qdrant

    Collection: fpg_requirements_gigachat
    - 18 requirements (1 vector each)
    - Content: evaluation criteria + methodologies + budget templates
    - Vector dimension: 1024
    - Distance metric: Cosine
    """

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "fpg_requirements_gigachat",
        use_memory: bool = False
    ):
        """Initialize Qdrant loader"""
        self.collection_name = collection_name
        self.vector_dim = 1024

        # Connect to Qdrant
        if use_memory:
            logger.info(f"[QDRANT] Using in-memory Qdrant client...")
            self.qdrant = QdrantClient(":memory:")
        else:
            logger.info(f"[QDRANT] Connecting to {qdrant_host}:{qdrant_port}...")
            try:
                self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
                self.qdrant.get_collections()
                logger.info(f"[OK] Connected to Qdrant")
            except Exception as e:
                logger.warning(f"[WARN] Cannot connect: {e}")
                logger.info(f"[FALLBACK] Switching to in-memory Qdrant...")
                self.qdrant = QdrantClient(":memory:")

        # Initialize GigaChat Embeddings client
        logger.info("[GIGACHAT] Initializing embeddings client...")
        self.embeddings = GigaChatEmbeddingsClient()

        # Test connection
        if not self.embeddings.test_connection():
            raise RuntimeError("[ERROR] GigaChat Embeddings API connection failed")

        logger.info("[READY] Loader initialized successfully\n")

    def create_collection(self, recreate: bool = False):
        """Create Qdrant collection"""
        logger.info(f"[COLLECTION] Creating '{self.collection_name}'...")

        collections = [c.name for c in self.qdrant.get_collections().collections]

        if self.collection_name in collections:
            if recreate:
                logger.info(f"[DELETE] Removing existing collection...")
                self.qdrant.delete_collection(self.collection_name)
            else:
                logger.info(f"[EXISTS] Collection already exists")
                return

        # Create collection
        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_dim,
                distance=Distance.COSINE
            ),
            on_disk_payload=True
        )

        logger.info(f"[OK] Collection '{self.collection_name}' created\n")

    def load_requirements_from_json(self, json_path: Path) -> List[FPGRequirement]:
        """Load requirements from JSON dataset"""
        logger.info(f"[LOAD] Reading {json_path}...")

        with open(json_path, 'r', encoding='utf-8') as f:
            requirements_data = json.load(f)

        # Convert to Pydantic models
        requirements = [FPGRequirement(**req) for req in requirements_data]

        logger.info(f"[OK] Loaded {len(requirements)} requirements\n")
        return requirements

    def upload_to_qdrant(self, requirements: List[FPGRequirement]):
        """
        Upload requirements to Qdrant

        Each requirement → 1 vector
        """
        logger.info(f"[START] Embedding and uploading {len(requirements)} requirements...\n")

        points = []
        point_id = 1

        for i, req in enumerate(requirements, 1):
            logger.info(f"[{i}/{len(requirements)}] Processing {req.requirement_type}: {req.content[:50]}...")

            # Embed content
            vector = self.embeddings.embed_text(req.content)

            if vector:
                # Prepare metadata payload
                payload = {
                    "requirement_type": req.requirement_type,
                    "fund_name": req.fund_name,
                    "category": req.category,
                    "content": req.content,
                    "content_length": len(req.content)
                }

                # Add specific data based on type
                if req.criterion_data:
                    payload["criterion_name"] = req.criterion_data.criterion_name
                    payload["weight"] = req.criterion_data.weight
                elif req.methodology_data:
                    payload["methodology_name"] = req.methodology_data.methodology_name
                elif req.budget_data:
                    payload["budget_project_type"] = req.budget_data.project_type
                    payload["budget_total"] = req.budget_data.total_amount

                # Create Qdrant point
                point = PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )

                points.append(point)
                point_id += 1

                logger.info(f"  [OK] Vector created (1024-dim)")
            else:
                logger.warning(f"  [SKIP] Embedding failed")

        # Upsert all points
        if points:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"\n[UPLOAD] Uploaded {len(points)} vectors")

    def print_collection_info(self):
        """Print Qdrant collection statistics"""
        info = self.qdrant.get_collection(self.collection_name)

        logger.info(f"\n{'='*60}")
        logger.info(f"Collection: {self.collection_name}")
        logger.info(f"Vectors count: {info.vectors_count}")
        logger.info(f"Points count: {info.points_count}")
        logger.info(f"Vector dimension: {self.vector_dim}")
        logger.info(f"Distance metric: Cosine")
        logger.info(f"{'='*60}\n")

    def test_search(self, query: str):
        """Test semantic search"""
        logger.info(f"[TEST] Searching for: '{query}'")

        # Embed query
        query_vector = self.embeddings.embed_text(query)

        if not query_vector:
            logger.error("[ERROR] Failed to embed query")
            return

        # Search in Qdrant
        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=3
        )

        logger.info(f"\n[RESULTS] Top 3 matches:\n")
        for i, hit in enumerate(results.points, 1):
            logger.info(f"{i}. [{hit.payload['requirement_type']}] {hit.payload.get('criterion_name') or hit.payload.get('methodology_name') or 'Budget'}")
            logger.info(f"   Score: {hit.score:.4f}")
            logger.info(f"   Content: {hit.payload['content'][:100]}...\n")


def main():
    """Main entry point"""
    # Paths
    iteration_dir = Path(__file__).parent.parent / "iterations" / "Iteration_51_AI_Enhancement"
    dataset_path = iteration_dir / "fpg_requirements_dataset.json"

    # Check dataset exists
    if not dataset_path.exists():
        logger.error(f"[ERROR] Dataset not found: {dataset_path}")
        return

    # Initialize loader
    loader = QdrantFPGRequirementsLoader(
        qdrant_host="localhost",
        qdrant_port=6333,
        collection_name="fpg_requirements_gigachat",
        use_memory=False  # Auto-fallback to in-memory
    )

    # Create collection
    loader.create_collection(recreate=True)

    # Load requirements
    requirements = loader.load_requirements_from_json(dataset_path)

    # Upload to Qdrant
    loader.upload_to_qdrant(requirements)

    # Print statistics
    loader.print_collection_info()

    # Test search
    loader.test_search("как составить бюджет проекта")
    loader.test_search("SMART цели")
    loader.test_search("критерии оценки заявки")

    # Print embeddings stats
    stats = loader.embeddings.get_statistics()
    logger.info(f"\n[EMBEDDINGS STATS]")
    logger.info(f"  Total API calls: {stats['total_api_calls']}")
    logger.info(f"  Total tokens embedded: {stats['total_tokens_embedded']}")
    logger.info(f"  Model: {stats['model']}")

    logger.info(f"\n[SUCCESS] Iteration 51 Phase 2: fpg_requirements_gigachat collection ready!")


if __name__ == "__main__":
    main()
