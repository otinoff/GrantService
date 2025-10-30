"""
Knowledge Base for Test Engineer Agent

Provides RAG (Retrieval Augmented Generation) capabilities using:
- Qdrant for vector storage
- GigaChat Embeddings for text vectorization
- Document indexing from knowhow/ directory

Components:
- embeddings_generator.py: Generate embeddings for knowhow documents
- qdrant_setup.py: Setup Qdrant collection
- rag_retriever.py: Retrieve relevant context
"""

from .rag_retriever import RAGRetriever
from .embeddings_generator import EmbeddingsGenerator
from .qdrant_setup import QdrantSetup

__all__ = ["RAGRetriever", "EmbeddingsGenerator", "QdrantSetup"]
