# Knowledge Base (RAG) для Test Engineer Agent

**Status:** ✅ Implemented (Iteration 67)

Система RAG (Retrieval Augmented Generation) для извлечения релевантного контекста из базы знаний проекта.

---

## 🎯 Возможности

- **Vector Search:** Поиск по embedding через Qdrant
- **GigaChat Embeddings:** Vectorization текста (1024-dim)
- **Context Retrieval:** Top-K релевантных chunks для LLM
- **Similar Issues:** Поиск похожих проблем из истории
- **Graceful Degradation:** Работает без Qdrant (fallback mode)

---

## 🏗️ Архитектура

```
knowledge_base/
├── __init__.py               # Package exports
├── qdrant_setup.py          # Qdrant collection setup
├── embeddings_generator.py  # Embeddings generation
├── rag_retriever.py         # Retrieval logic
├── test_rag.py              # Test suite
└── README.md                # This file
```

### Data Flow:

```
┌─────────────┐
│  knowhow/   │  Markdown files
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ EmbeddingsGenerator │  Chunk + Embed
└──────┬──────────────┘
       │
       ▼  GigaChat Embeddings API
┌─────────────┐
│   Qdrant    │  Vector storage
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ RAGRetriever│  Query → Top-K results
└─────────────┘
```

---

## 🚀 Quick Start

### 1. Start Qdrant

```bash
# Docker
docker run -d -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant qdrant/qdrant

# Check status
curl http://localhost:6333/
```

### 2. Setup Collection

```bash
cd tester/knowledge_base
python qdrant_setup.py
```

**Output:**
```
✅ Qdrant is running!
📦 Creating collection: test_engineer_kb
✅ Collection created: test_engineer_kb
📊 Collection Info:
   Name: test_engineer_kb
   Vectors: 0
   Points: 0
   Status: green
```

### 3. Generate Embeddings

```bash
python embeddings_generator.py
```

**Output:**
```
📁 Found 52 markdown files in ../../knowhow
📄 Processing 237 chunks from 52 documents
⏳ Processing batch 1/24
✅ Indexed 10 chunks
...
✅ Indexing complete!
   Documents: 52
   Chunks: 237
   Indexed: 237
```

### 4. Test Retrieval

```bash
python test_rag.py
```

**Output:**
```
🧪 RAG KNOWLEDGE BASE - FULL TEST SUITE

TEST 1: Qdrant Setup
✅ Qdrant connection OK
✅ Collection created

TEST 2: Embeddings Generation
✅ Knowledge base already indexed: 237 vectors

TEST 3: RAG Retrieval
📊 Knowledge Base Stats:
   Vectors: 237
   Points: 237

🔍 Query: How to fix async errors in Python?
✅ Found 5 results:
   [1] TESTING-METHODOLOGY.md (score: 0.856)
   [2] E2E_TESTING_GUIDE.md (score: 0.823)
   [3] ITERATION_LEARNINGS.md (score: 0.809)
...

✅ ALL TESTS PASSED
```

---

## 📚 API Usage

### In Test Engineer Agent

```python
from tester.knowledge_base import QdrantSetup, RAGRetriever

# Initialize
setup = QdrantSetup()
retriever = RAGRetriever(setup.client, top_k=5)

# Retrieve context for decision-making
context = await retriever.retrieve_for_context(
    query="How to fix KeyError in Python?",
    max_tokens=1000
)
print(context)

# Find similar issues
similar = await retriever.retrieve_similar_issues(
    error_message="KeyError: 'user_answers'",
    top_k=3
)
for issue in similar:
    print(f"📄 {issue['file']} (score: {issue['score']:.2f})")
    print(f"   {issue['text'][:100]}...")
```

### Standalone Search

```python
from tester.knowledge_base import RAGRetriever, QdrantSetup

setup = QdrantSetup()
retriever = RAGRetriever(setup.client)

# Simple search
results = await retriever.retrieve(
    query="Testing best practices",
    file_filter=None  # Optional: "TESTING-METHODOLOGY.md"
)

for result in results:
    print(f"[{result['score']:.3f}] {result['file']}")
    print(result['text'])
```

---

## 🔧 Configuration

### Qdrant Setup

```python
# Default: localhost:6333
setup = QdrantSetup(host="localhost", port=6333)

# Qdrant Cloud
setup = QdrantSetup(
    host="xxxxx.cloud.qdrant.io",
    api_key="your-api-key"
)
```

### RAG Retriever

```python
retriever = RAGRetriever(
    qdrant_client=setup.client,
    top_k=5,              # Number of results
    score_threshold=0.7   # Minimum similarity (0-1)
)
```

### Embeddings Generator

```python
generator = EmbeddingsGenerator(
    qdrant_client=setup.client,
    knowhow_dir="../../knowhow"  # Path to docs
)

# Chunking params
generator.CHUNK_SIZE = 1000      # Characters
generator.CHUNK_OVERLAP = 200    # Overlap between chunks
```

---

## 📊 Performance

### Expected Metrics:
- **Indexing:** ~10 documents/sec
- **Retrieval:** <500ms per query
- **Accuracy:** >80% relevant results
- **Vector size:** 1024 dimensions (GigaChat)

### Optimization:
- Use batch processing (10-20 docs)
- Enable Qdrant disk storage for large KB
- Cache frequent queries
- Use score_threshold to filter low-quality results

---

## 🐛 Troubleshooting

### Qdrant Not Running

```bash
# Check if Qdrant is running
curl http://localhost:6333/

# Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant
```

### GigaChat API Errors

```python
# Check credentials
echo $GIGACHAT_CREDENTIALS

# Test embeddings
from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient
client = GigaChatEmbeddingsClient()
embeddings = await client.get_embeddings(["test"])
print(len(embeddings[0]))  # Should be 1024
```

### Empty Results

```python
# Check collection
setup = QdrantSetup()
info = setup.get_collection_info()
print(info)  # Should show vectors_count > 0

# Re-index if needed
generator = EmbeddingsGenerator(setup.client)
await generator.index_documents()
```

### Low Quality Results

```python
# Adjust score threshold
retriever = RAGRetriever(setup.client, score_threshold=0.75)

# Increase top_k
retriever.top_k = 10

# Use file filter
results = await retriever.retrieve(
    query="your query",
    file_filter="TESTING-METHODOLOGY.md"
)
```

---

## 🔄 Maintenance

### Update Knowledge Base

```bash
# When knowhow/ files change:
cd tester/knowledge_base

# Re-index with force_recreate
python embeddings_generator.py --force-reindex
```

### Backup/Restore

```bash
# Backup Qdrant data
docker cp qdrant:/qdrant/storage ./qdrant_backup

# Restore
docker cp ./qdrant_backup qdrant:/qdrant/storage
```

---

## 📈 Roadmap

### Completed (Iteration 67):
- ✅ Qdrant setup
- ✅ GigaChat embeddings
- ✅ RAG retriever
- ✅ Test Engineer Agent integration

### Future Enhancements:
- [ ] Query caching
- [ ] Incremental updates (only changed files)
- [ ] Multi-language support
- [ ] Hybrid search (keywords + vectors)
- [ ] Relevance feedback loop

---

## 📚 References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [GigaChat Embeddings API](https://developers.sber.ru/docs/ru/gigachat/embeddings)
- [RAG Best Practices](https://www.anthropic.com/index/contextual-retrieval)

---

**Created:** 2025-10-30 (Iteration 67)
**Maintainer:** Test Engineer Agent
