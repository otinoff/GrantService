#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate real embeddings for FPG knowledge base on production
Run this ON THE SERVER after simple load
"""
import sys
sys.path.insert(0, '/var/GrantService')

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

QDRANT_HOST = "localhost"  # On server
QDRANT_PORT = 6333
COLLECTION_NAME = "knowledge_sections"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print("=" * 80)
print("GENERATING EMBEDDINGS FOR FPG KNOWLEDGE BASE")
print("=" * 80)

try:
    print(f"\n1. Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print("   OK Model loaded")

    print(f"\n2. Connecting to Qdrant...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print("   OK Connected")

    print(f"\n3. Fetching points from '{COLLECTION_NAME}'...")
    points = []
    offset = None

    while True:
        result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False  # Don't need old vectors
        )

        points.extend(result[0])
        offset = result[1]

        if offset is None:
            break

    print(f"   OK Found {len(points)} points")

    print(f"\n4. Generating embeddings...")
    updated_points = []

    for idx, point in enumerate(points, 1):
        # Get content from payload
        content = point.payload.get('content', '')
        section_name = point.payload.get('section_name', '')

        # Combine section name and content for better embeddings
        text = f"{section_name}\n\n{content}"

        # Generate embedding
        embedding = model.encode(text, convert_to_tensor=False)

        # Create updated point
        updated_point = {
            "id": point.id,
            "vector": embedding.tolist(),
            "payload": point.payload
        }
        updated_points.append(updated_point)

        if idx % 5 == 0:
            print(f"   Progress: {idx}/{len(points)} embeddings generated")

    print(f"   OK All {len(updated_points)} embeddings generated")

    print(f"\n5. Updating points in Qdrant...")
    # Update in batches
    batch_size = 50
    for i in range(0, len(updated_points), batch_size):
        batch = updated_points[i:i+batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        print(f"   Batch {i//batch_size + 1} uploaded ({len(batch)} points)")

    print(f"\n6. Verifying...")
    collection_info = client.get_collection(COLLECTION_NAME)
    print(f"   Points: {collection_info.points_count}")
    print(f"   Vectors: {collection_info.vectors_count}")
    print(f"   Status: {collection_info.status}")

    print("\n" + "=" * 80)
    print("SUCCESS! EMBEDDINGS GENERATED")
    print("=" * 80)

    # Test search
    print("\n7. Testing semantic search...")
    test_query = "Какие требования к бюджету проекта?"
    query_embedding = model.encode(test_query, convert_to_tensor=False)

    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=3
    )

    print(f"\nQuery: {test_query}")
    print("\nTop 3 results:")
    for i, hit in enumerate(search_results, 1):
        print(f"\n{i}. {hit.payload['section_name']}")
        print(f"   Score: {hit.score:.3f}")
        print(f"   Preview: {hit.payload['content'][:150]}...")

    print("\n" + "=" * 80)
    print("READY FOR USE!")
    print("=" * 80)

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
