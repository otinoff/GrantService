"""
Qdrant Setup for Test Engineer Knowledge Base

Sets up Qdrant collection for storing knowhow/ document embeddings.
"""

import os
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class QdrantSetup:
    """Setup and manage Qdrant collection for Test Engineer KB"""

    COLLECTION_NAME = "test_engineer_kb"
    VECTOR_SIZE = 1024  # GigaChat Embeddings dimension

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None
    ):
        """
        Initialize Qdrant client

        Args:
            host: Qdrant host (default: localhost)
            port: Qdrant port (default: 6333)
            api_key: Optional API key for Qdrant Cloud
        """
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key
        )

    def create_collection(self, force_recreate: bool = False) -> bool:
        """
        Create Qdrant collection for knowledge base

        Args:
            force_recreate: If True, delete existing collection first

        Returns:
            bool: True if collection created successfully
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(
                c.name == self.COLLECTION_NAME for c in collections
            )

            if collection_exists:
                if force_recreate:
                    print(f"🗑️ Deleting existing collection: {self.COLLECTION_NAME}")
                    self.client.delete_collection(self.COLLECTION_NAME)
                else:
                    print(f"✅ Collection already exists: {self.COLLECTION_NAME}")
                    return True

            # Create collection
            print(f"📦 Creating collection: {self.COLLECTION_NAME}")
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

            print(f"✅ Collection created: {self.COLLECTION_NAME}")
            return True

        except Exception as e:
            print(f"❌ Failed to create collection: {e}")
            return False

    def get_collection_info(self) -> dict:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.COLLECTION_NAME)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            return {"error": str(e)}

    def check_connection(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            print(f"❌ Qdrant connection failed: {e}")
            return False


if __name__ == "__main__":
    """Test Qdrant setup"""

    # Check if Qdrant is running
    setup = QdrantSetup()

    if not setup.check_connection():
        print("\n❌ Qdrant is not running!")
        print("\nTo start Qdrant:")
        print("  docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant")
        exit(1)

    print("\n✅ Qdrant is running!")

    # Create collection
    if setup.create_collection(force_recreate=False):
        info = setup.get_collection_info()
        print(f"\n📊 Collection Info:")
        print(f"   Name: {info.get('name')}")
        print(f"   Vectors: {info.get('vectors_count', 0)}")
        print(f"   Points: {info.get('points_count', 0)}")
        print(f"   Status: {info.get('status')}")
