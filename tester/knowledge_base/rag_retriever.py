"""
RAG Retriever for Test Engineer Agent

Retrieves relevant context from knowhow/ knowledge base using:
- Qdrant vector search
- GigaChat embeddings for query vectorization
"""

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient


class RAGRetriever:
    """Retrieve relevant context from knowledge base"""

    COLLECTION_NAME = "test_engineer_kb"

    def __init__(
        self,
        qdrant_client: QdrantClient,
        top_k: int = 5,
        score_threshold: float = 0.7
    ):
        """
        Initialize RAG retriever

        Args:
            qdrant_client: Qdrant client instance
            top_k: Number of results to retrieve
            score_threshold: Minimum similarity score (0-1)
        """
        self.qdrant_client = qdrant_client
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.embeddings_client = GigaChatEmbeddingsClient()

    async def retrieve(
        self,
        query: str,
        file_filter: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Retrieve relevant context for query

        Args:
            query: Search query text
            file_filter: Optional file name filter (e.g., "TESTING-METHODOLOGY.md")

        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embeddings_client.get_embeddings([query])

            if not query_embedding:
                print("❌ Failed to generate query embedding")
                return []

            query_vector = query_embedding[0]

            # Build filter if needed
            search_filter = None
            if file_filter:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="file",
                            match=MatchValue(value=file_filter)
                        )
                    ]
                )

            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                limit=self.top_k,
                score_threshold=self.score_threshold,
                query_filter=search_filter
            )

            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "text": hit.payload["text"],
                    "file": hit.payload["file"],
                    "score": hit.score,
                    "start": hit.payload.get("start", 0),
                    "end": hit.payload.get("end", 0)
                })

            return results

        except Exception as e:
            print(f"❌ RAG retrieval failed: {e}")
            return []

    async def retrieve_for_context(
        self,
        query: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Retrieve and format context for LLM prompt

        Args:
            query: Search query
            max_tokens: Approximate max tokens for context (~4 chars/token)

        Returns:
            Formatted context string
        """
        results = await self.retrieve(query)

        if not results:
            return ""

        # Format context
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate

        for i, result in enumerate(results, 1):
            chunk = f"[{i}] From {result['file']} (score: {result['score']:.2f}):\n{result['text']}\n"

            if total_chars + len(chunk) > max_chars:
                break

            context_parts.append(chunk)
            total_chars += len(chunk)

        return "\n".join(context_parts)

    async def retrieve_similar_issues(
        self,
        error_message: str,
        top_k: int = 3
    ) -> List[Dict[str, any]]:
        """
        Find similar issues from past experience

        Args:
            error_message: Error message or description
            top_k: Number of similar issues to retrieve

        Returns:
            List of similar issues with solutions
        """
        # Focus on error-related documents
        query = f"error issue problem: {error_message}"

        old_top_k = self.top_k
        self.top_k = top_k

        results = await self.retrieve(query)

        self.top_k = old_top_k

        return results

    def get_stats(self) -> Dict[str, any]:
        """Get knowledge base statistics"""
        try:
            collection = self.qdrant_client.get_collection(self.COLLECTION_NAME)
            return {
                "vectors_count": collection.vectors_count,
                "points_count": collection.points_count,
                "status": collection.status
            }
        except Exception as e:
            return {"error": str(e)}


async def main():
    """Test RAG retriever"""
    from .qdrant_setup import QdrantSetup

    # Setup
    setup = QdrantSetup()

    if not setup.check_connection():
        print("❌ Qdrant not running!")
        return

    # Initialize retriever
    retriever = RAGRetriever(setup.client, top_k=5)

    # Get stats
    stats = retriever.get_stats()
    print(f"📊 Knowledge Base Stats:")
    print(f"   Vectors: {stats.get('vectors_count', 0)}")
    print(f"   Points: {stats.get('points_count', 0)}")

    if stats.get('vectors_count', 0) == 0:
        print("\n⚠️ Knowledge base is empty! Run embeddings_generator.py first.")
        return

    # Test queries
    test_queries = [
        "How to fix async errors in Python?",
        "What are best practices for testing?",
        "Database connection issues PostgreSQL"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = await retriever.retrieve(query)

        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"   [{i}] {result['file']} (score: {result['score']:.3f})")
                print(f"       {result['text'][:100]}...")
        else:
            print("   No results found")

        # Test formatted context
        context = await retriever.retrieve_for_context(query, max_tokens=500)
        print(f"\n📝 Formatted context ({len(context)} chars):")
        print(context[:300] + "..." if len(context) > 300 else context)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
