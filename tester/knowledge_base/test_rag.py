"""
Test RAG Knowledge Base

Tests all RAG components:
1. Qdrant setup
2. Embeddings generation
3. RAG retrieval
"""

import asyncio
from qdrant_setup import QdrantSetup
from embeddings_generator import EmbeddingsGenerator
from rag_retriever import RAGRetriever


async def test_qdrant_setup():
    """Test Qdrant connection and collection setup"""
    print("\n" + "="*80)
    print("TEST 1: Qdrant Setup")
    print("="*80)

    setup = QdrantSetup()

    # Test connection
    if not setup.check_connection():
        print("❌ Qdrant not running!")
        print("\nTo start Qdrant:")
        print("  docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant")
        return False

    print("✅ Qdrant connection OK")

    # Create collection
    if setup.create_collection(force_recreate=False):
        info = setup.get_collection_info()
        print(f"✅ Collection created:")
        print(f"   Name: {info.get('name')}")
        print(f"   Vectors: {info.get('vectors_count', 0)}")
        print(f"   Points: {info.get('points_count', 0)}")
        return True
    else:
        print("❌ Collection creation failed")
        return False


async def test_embeddings_generation(force_reindex: bool = False):
    """Test embeddings generation"""
    print("\n" + "="*80)
    print("TEST 2: Embeddings Generation")
    print("="*80)

    setup = QdrantSetup()
    generator = EmbeddingsGenerator(setup.client, knowhow_dir="../../knowhow")

    # Check if already indexed
    stats = setup.get_collection_info()
    current_count = stats.get('vectors_count', 0)

    if current_count > 0 and not force_reindex:
        print(f"✅ Knowledge base already indexed: {current_count} vectors")
        print("   Use --force-reindex to regenerate")
        return True

    print("⏳ Generating embeddings...")
    result = await generator.index_documents(batch_size=10)

    print(f"\n✅ Embeddings generated:")
    print(f"   Documents: {result['documents']}")
    print(f"   Chunks: {result['chunks']}")
    print(f"   Indexed: {result['indexed']}")

    return result['indexed'] > 0


async def test_rag_retrieval():
    """Test RAG retrieval"""
    print("\n" + "="*80)
    print("TEST 3: RAG Retrieval")
    print("="*80)

    setup = QdrantSetup()
    retriever = RAGRetriever(setup.client, top_k=5)

    # Check stats
    stats = retriever.get_stats()
    print(f"📊 Knowledge Base Stats:")
    print(f"   Vectors: {stats.get('vectors_count', 0)}")
    print(f"   Points: {stats.get('points_count', 0)}")

    if stats.get('vectors_count', 0) == 0:
        print("\n⚠️ Knowledge base is empty! Run test_embeddings_generation first.")
        return False

    # Test queries
    test_queries = [
        "How to fix async errors in Python?",
        "Database connection issues PostgreSQL",
        "Testing best practices for production",
        "Error handling in E2E tests",
        "How to fix KeyError in dict?"
    ]

    all_passed = True

    for query in test_queries:
        print(f"\n🔍 Query: {query}")

        # Retrieve
        results = await retriever.retrieve(query)

        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results[:3], 1):
                print(f"   [{i}] {result['file']} (score: {result['score']:.3f})")
                preview = result['text'][:100].replace('\n', ' ')
                print(f"       {preview}...")
        else:
            print("❌ No results found")
            all_passed = False

        # Test formatted context
        context = await retriever.retrieve_for_context(query, max_tokens=500)
        print(f"📝 Context length: {len(context)} chars")

    return all_passed


async def test_similar_issues():
    """Test similar issues search"""
    print("\n" + "="*80)
    print("TEST 4: Similar Issues Search")
    print("="*80)

    setup = QdrantSetup()
    retriever = RAGRetriever(setup.client)

    test_errors = [
        "KeyError: 'user_answers'",
        "NameError: name 'logger' is not defined",
        "TypeError: missing required positional argument 'db'",
        "AttributeError: object has no attribute 'run_interview'"
    ]

    for error in test_errors:
        print(f"\n🔍 Error: {error}")

        similar = await retriever.retrieve_similar_issues(error, top_k=3)

        if similar:
            print(f"✅ Found {len(similar)} similar issues:")
            for i, issue in enumerate(similar, 1):
                print(f"   [{i}] {issue['file']} (score: {issue['score']:.3f})")
        else:
            print("   No similar issues found")


async def main():
    """Run all tests"""
    print("\n🧪 RAG KNOWLEDGE BASE - FULL TEST SUITE")

    # Test 1: Qdrant setup
    if not await test_qdrant_setup():
        print("\n❌ Test suite failed at Qdrant setup")
        return

    # Test 2: Embeddings generation
    if not await test_embeddings_generation(force_reindex=False):
        print("\n❌ Test suite failed at embeddings generation")
        return

    # Test 3: RAG retrieval
    if not await test_rag_retrieval():
        print("\n❌ Test suite failed at RAG retrieval")
        return

    # Test 4: Similar issues
    await test_similar_issues()

    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
