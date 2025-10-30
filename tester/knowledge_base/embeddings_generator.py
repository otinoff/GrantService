"""
Embeddings Generator for Test Engineer Knowledge Base

Generates embeddings for knowhow/ documents using GigaChat Embeddings API.
"""

import os
import glob
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Import GigaChat embeddings client
from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient


class EmbeddingsGenerator:
    """Generate and store embeddings for knowhow documents"""

    COLLECTION_NAME = "test_engineer_kb"
    CHUNK_SIZE = 1000  # Characters per chunk
    CHUNK_OVERLAP = 200  # Overlap between chunks

    def __init__(
        self,
        qdrant_client: QdrantClient,
        knowhow_dir: str = "knowhow"
    ):
        """
        Initialize embeddings generator

        Args:
            qdrant_client: Qdrant client instance
            knowhow_dir: Directory with knowhow markdown files
        """
        self.qdrant_client = qdrant_client
        self.knowhow_dir = Path(knowhow_dir)
        self.embeddings_client = GigaChatEmbeddingsClient()

    def chunk_text(self, text: str, file_path: str) -> List[Dict[str, str]]:
        """
        Split text into overlapping chunks

        Args:
            text: Document text
            file_path: Source file path

        Returns:
            List of chunks with metadata
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunk_text = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind(". ")
                last_newline = chunk_text.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > self.CHUNK_SIZE // 2:
                    end = start + break_point + 1
                    chunk_text = text[start:end]

            chunk_id = hashlib.md5(
                f"{file_path}_{start}".encode()
            ).hexdigest()

            chunks.append({
                "id": chunk_id,
                "text": chunk_text.strip(),
                "file": file_path,
                "start": start,
                "end": end
            })

            start = end - self.CHUNK_OVERLAP

        return chunks

    def load_markdown_files(self) -> List[Dict[str, str]]:
        """
        Load all markdown files from knowhow directory

        Returns:
            List of documents with content and metadata
        """
        documents = []

        # Find all .md files
        md_files = glob.glob(str(self.knowhow_dir / "**/*.md"), recursive=True)

        print(f"📁 Found {len(md_files)} markdown files in {self.knowhow_dir}")

        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract relative path
                rel_path = str(Path(file_path).relative_to(self.knowhow_dir))

                documents.append({
                    "file": rel_path,
                    "content": content,
                    "size": len(content)
                })

            except Exception as e:
                print(f"⚠️ Failed to read {file_path}: {e}")

        return documents

    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for batch of texts

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            embeddings = await self.embeddings_client.get_embeddings_batch(texts)
            return embeddings
        except Exception as e:
            print(f"❌ Failed to generate embeddings: {e}")
            return []

    async def index_documents(
        self,
        batch_size: int = 10
    ) -> Dict[str, int]:
        """
        Index all knowhow documents into Qdrant

        Args:
            batch_size: Number of chunks to process at once

        Returns:
            Statistics about indexed documents
        """
        # Load documents
        documents = self.load_markdown_files()

        if not documents:
            print("❌ No documents found!")
            return {"documents": 0, "chunks": 0, "indexed": 0}

        # Chunk all documents
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(doc["content"], doc["file"])
            all_chunks.extend(chunks)

        print(f"📄 Processing {len(all_chunks)} chunks from {len(documents)} documents")

        # Generate embeddings in batches
        indexed_count = 0

        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            texts = [chunk["text"] for chunk in batch]

            print(f"⏳ Processing batch {i // batch_size + 1}/{(len(all_chunks) + batch_size - 1) // batch_size}")

            # Generate embeddings
            embeddings = await self.generate_embeddings_batch(texts)

            if not embeddings:
                print(f"⚠️ Skipping batch {i // batch_size + 1} - no embeddings")
                continue

            # Prepare points for Qdrant
            points = []
            for chunk, embedding in zip(batch, embeddings):
                points.append(PointStruct(
                    id=chunk["id"],
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "file": chunk["file"],
                        "start": chunk["start"],
                        "end": chunk["end"]
                    }
                ))

            # Upload to Qdrant
            try:
                self.qdrant_client.upsert(
                    collection_name=self.COLLECTION_NAME,
                    points=points
                )
                indexed_count += len(points)
                print(f"✅ Indexed {len(points)} chunks")

            except Exception as e:
                print(f"❌ Failed to upload batch: {e}")

        return {
            "documents": len(documents),
            "chunks": len(all_chunks),
            "indexed": indexed_count
        }


async def main():
    """Test embeddings generation"""
    from .qdrant_setup import QdrantSetup

    # Setup Qdrant
    setup = QdrantSetup()

    if not setup.check_connection():
        print("\n❌ Qdrant is not running! Start it first:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        return

    # Create collection
    setup.create_collection(force_recreate=False)

    # Generate embeddings
    generator = EmbeddingsGenerator(setup.client)

    print("\n📊 Starting embeddings generation...")
    stats = await generator.index_documents(batch_size=10)

    print(f"\n✅ Indexing complete!")
    print(f"   Documents: {stats['documents']}")
    print(f"   Chunks: {stats['chunks']}")
    print(f"   Indexed: {stats['indexed']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
