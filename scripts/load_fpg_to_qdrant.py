"""
Load FPG Real Winners to Qdrant with GigaChat Embeddings

This script:
1. Reads fpg_real_winners_dataset.json (17 grants from Perplexity AI)
2. Creates 4 embeddings per grant (problem, solution, kpi, budget)
3. Uploads to Qdrant collection "fpg_real_winners"

Iteration 51: AI Enhancement - Embeddings + RL
Date: 2025-10-26

Usage:
    python scripts/load_fpg_to_qdrant.py

Expected tokens: ~1.2M tokens
Expected cost: ~0 руб (Sber500 bootcamp quota)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

# Import Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError:
    print("[ERROR] qdrant-client not installed. Run: pip install qdrant-client")
    sys.exit(1)

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import custom modules
from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient
from shared.llm.embeddings_models import FPGRealWinner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QdrantFPGLoader:
    """
    Loader for FPG Real Winners to Qdrant

    Architecture:
    - Each grant → 4 vectors (problem, solution, kpi, budget)
    - 17 grants × 4 = 68 vectors total
    - Qdrant collection: fpg_real_winners
    - Vector dimension: 1024
    - Distance metric: Cosine
    """

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "fpg_real_winners",
        use_memory: bool = False
    ):
        """
        Initialize Qdrant loader

        Args:
            qdrant_host: Qdrant server host (ignored if use_memory=True)
            qdrant_port: Qdrant server port (ignored if use_memory=True)
            collection_name: Name of Qdrant collection
            use_memory: Use in-memory Qdrant (for development/testing)
        """
        self.collection_name = collection_name
        self.vector_dim = 1024

        # Connect to Qdrant
        if use_memory:
            logger.info(f"[QDRANT] Using in-memory Qdrant client (development mode)...")
            self.qdrant = QdrantClient(":memory:")
        else:
            logger.info(f"[QDRANT] Connecting to {qdrant_host}:{qdrant_port}...")
            try:
                self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
                # Test connection
                self.qdrant.get_collections()
                logger.info(f"[OK] Connected to Qdrant at {qdrant_host}:{qdrant_port}")
            except Exception as e:
                logger.warning(f"[WARN] Cannot connect to {qdrant_host}:{qdrant_port}: {e}")
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
        """
        Create Qdrant collection (or recreate if exists)

        Args:
            recreate: If True, delete existing collection first
        """
        logger.info(f"[COLLECTION] Creating '{self.collection_name}'...")

        # Check if collection exists
        collections = [c.name for c in self.qdrant.get_collections().collections]

        if self.collection_name in collections:
            if recreate:
                logger.info(f"[DELETE] Removing existing collection...")
                self.qdrant.delete_collection(self.collection_name)
            else:
                logger.info(f"[EXISTS] Collection already exists, skipping creation")
                return

        # Create new collection
        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_dim,
                distance=Distance.COSINE
            ),
            on_disk_payload=True  # Store metadata on disk
        )

        logger.info(f"[OK] Collection '{self.collection_name}' created\n")

    def load_grants_from_json(self, json_path: Path) -> List[FPGRealWinner]:
        """
        Load grants from JSON dataset

        Args:
            json_path: Path to fpg_real_winners_dataset.json

        Returns:
            List of FPGRealWinner objects
        """
        logger.info(f"[LOAD] Reading {json_path}...")

        with open(json_path, 'r', encoding='utf-8') as f:
            grants_data = json.load(f)

        # Convert to Pydantic models
        grants = [FPGRealWinner(**grant) for grant in grants_data]

        logger.info(f"[OK] Loaded {len(grants)} grants\n")
        return grants

    def embed_grant_sections(self, grant: FPGRealWinner) -> Dict[str, List[float]]:
        """
        Embed 4 sections of grant into vectors

        Args:
            grant: FPGRealWinner object

        Returns:
            Dictionary: {"problem": vector, "solution": vector, "kpi": vector, "budget": vector}
        """
        sections = {
            "problem": grant.problem,
            "solution": grant.solution,
            "kpi": grant.kpi,
            "budget": grant.budget
        }

        embeddings = {}

        for section_name, text in sections.items():
            if text:  # Only embed non-empty sections
                vector = self.embeddings.embed_text(text)
                if vector:
                    embeddings[section_name] = vector
                    logger.info(f"  [OK] {section_name}: {len(vector)}-dim vector")
                else:
                    logger.warning(f"  [SKIP] {section_name}: embedding failed")
            else:
                logger.warning(f"  [SKIP] {section_name}: empty text")

        return embeddings

    def upload_grant_to_qdrant(
        self,
        grant: FPGRealWinner,
        embeddings: Dict[str, List[float]],
        point_id_offset: int
    ):
        """
        Upload grant vectors to Qdrant

        Args:
            grant: FPGRealWinner object
            embeddings: Dictionary of section embeddings
            point_id_offset: Starting point ID for this grant
        """
        points = []

        for idx, (section_name, vector) in enumerate(embeddings.items()):
            point_id = point_id_offset + idx

            # Prepare metadata payload
            payload = {
                "grant_id": f"{grant.fund_name}_{grant.year}_{grant.title[:30]}",
                "section": section_name,
                "title": grant.title,
                "organization": grant.organization,
                "fund_name": grant.fund_name,
                "year": grant.year,
                "region": grant.region,
                "amount": grant.amount,
                "category": grant.category,
                "source_url": grant.source_url,
                "scraped_at": grant.scraped_at.isoformat() if grant.scraped_at else None
            }

            # Create Qdrant point
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )

            points.append(point)

        # Upsert batch
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )

        logger.info(f"  [UPLOAD] Uploaded {len(points)} vectors for '{grant.title[:40]}...'")

    def load_all_grants(self, json_path: Path):
        """
        Load all grants from JSON and upload to Qdrant

        Args:
            json_path: Path to fpg_real_winners_dataset.json
        """
        # Load grants
        grants = self.load_grants_from_json(json_path)

        logger.info(f"[START] Embedding and uploading {len(grants)} grants...\n")

        point_id = 1  # Start point IDs from 1

        for i, grant in enumerate(grants, 1):
            logger.info(f"\n[{i}/{len(grants)}] Processing: {grant.title}")

            # Embed grant sections
            embeddings = self.embed_grant_sections(grant)

            # Upload to Qdrant
            if embeddings:
                self.upload_grant_to_qdrant(grant, embeddings, point_id)
                point_id += len(embeddings)
            else:
                logger.warning(f"  [SKIP] No embeddings generated for '{grant.title}'")

        logger.info(f"\n[DONE] Uploaded {point_id - 1} vectors from {len(grants)} grants")

    def print_collection_info(self):
        """
        Print Qdrant collection statistics
        """
        info = self.qdrant.get_collection(self.collection_name)

        logger.info(f"\n{'='*60}")
        logger.info(f"Collection: {self.collection_name}")
        logger.info(f"Vectors count: {info.vectors_count}")
        logger.info(f"Points count: {info.points_count}")
        logger.info(f"Vector dimension: {self.vector_dim}")
        logger.info(f"Distance metric: Cosine")
        logger.info(f"{'='*60}\n")

    def test_search(self, query: str = "поддержка молодежи"):
        """
        Test semantic search in loaded collection

        Args:
            query: Test search query
        """
        logger.info(f"[TEST] Searching for: '{query}'")

        # Embed query
        query_vector = self.embeddings.embed_text(query)

        if not query_vector:
            logger.error("[ERROR] Failed to embed query")
            return

        # Search in Qdrant
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=3
        )

        logger.info(f"\n[RESULTS] Top 3 matches:\n")
        for i, hit in enumerate(results, 1):
            logger.info(f"{i}. [{hit.payload['section']}] {hit.payload['title']}")
            logger.info(f"   Score: {hit.score:.4f}")
            logger.info(f"   Organization: {hit.payload['organization']}")
            logger.info(f"   Year: {hit.payload['year']}, Region: {hit.payload['region']}\n")


def main():
    """
    Main entry point
    """
    # Paths
    iteration_dir = Path(__file__).parent.parent / "iterations" / "Iteration_51_AI_Enhancement"
    dataset_path = iteration_dir / "fpg_real_winners_dataset.json"

    # Check dataset exists
    if not dataset_path.exists():
        logger.error(f"[ERROR] Dataset not found: {dataset_path}")
        logger.error("[HINT] Run: python scripts/fpg_data_parser.py first")
        return

    # Initialize loader (auto-fallback to in-memory if Qdrant not running)
    loader = QdrantFPGLoader(
        qdrant_host="localhost",
        qdrant_port=6333,
        collection_name="fpg_real_winners",
        use_memory=False  # Will auto-fallback to in-memory if connection fails
    )

    # Create collection
    loader.create_collection(recreate=True)

    # Load all grants
    loader.load_all_grants(dataset_path)

    # Print statistics
    loader.print_collection_info()

    # Test search
    loader.test_search("поддержка молодежи")
    loader.test_search("образовательный проект")

    # Print embeddings stats
    stats = loader.embeddings.get_statistics()
    logger.info(f"\n[EMBEDDINGS STATS]")
    logger.info(f"  Total API calls: {stats['total_api_calls']}")
    logger.info(f"  Total tokens embedded: {stats['total_tokens_embedded']}")
    logger.info(f"  Model: {stats['model']}")
    logger.info(f"  Vector dimension: {stats['vector_dim']}")

    logger.info(f"\n[SUCCESS] Iteration 51: fpg_real_winners collection ready!")


if __name__ == "__main__":
    main()
