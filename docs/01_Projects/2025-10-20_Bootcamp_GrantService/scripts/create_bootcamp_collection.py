#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создать коллекцию Sber500 Bootcamp в Qdrant

Назначение: Личная база знаний о буткэмпе для быстрого поиска информации
НЕ для агентов - для внутреннего использования!

Usage:
    python create_bootcamp_collection.py
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def create_collection():
    """Создать коллекцию sber500_bootcamp"""

    # Connect to Qdrant
    print("🔌 Connecting to Qdrant (5.35.88.251:6333)...")
    client = QdrantClient(host="5.35.88.251", port=6333)

    # Check if collection exists
    collections = client.get_collections()
    collection_names = [col.name for col in collections.collections]

    if "sber500_bootcamp" in collection_names:
        print("⚠️  Collection 'sber500_bootcamp' already exists")

        response = input("Delete and recreate? (y/N): ")
        if response.lower() == 'y':
            client.delete_collection(collection_name="sber500_bootcamp")
            print("🗑️  Deleted old collection")
        else:
            print("❌ Aborted")
            return False

    # Create collection
    print("📦 Creating collection 'sber500_bootcamp'...")
    client.create_collection(
        collection_name="sber500_bootcamp",
        vectors_config=VectorParams(
            size=768,  # paraphrase-multilingual-MiniLM-L12-v2
            distance=Distance.COSINE
        )
    )

    print("✅ Collection 'sber500_bootcamp' created successfully!")
    print("\n📊 Collection info:")
    print("  - Vector size: 768")
    print("  - Distance: Cosine")
    print("  - Model: paraphrase-multilingual-MiniLM-L12-v2")
    print("\n🎯 Purpose: Personal knowledge base for Sber500 bootcamp")
    print("   (NOT for agents - for internal use only!)")

    return True

if __name__ == "__main__":
    create_collection()
