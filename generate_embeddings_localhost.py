#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate embeddings for FPG knowledge base - LOCALHOST VERSION
"""
import requests
import json

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "knowledge_sections"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print("=" * 80)
print("GENERATING EMBEDDINGS FOR FPG KNOWLEDGE BASE (LOCALHOST)")
print("=" * 80)

print(f"\n1. Loading model: {MODEL_NAME}...")
print("   (This may take a minute on first run - downloading model...)")

from sentence_transformers import SentenceTransformer
model = SentenceTransformer(MODEL_NAME)
print("   OK Model loaded")

print(f"\n2. Connecting to Qdrant ({QDRANT_HOST}:{QDRANT_PORT})...")
url_base = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

print(f"\n3. Fetching points from '{COLLECTION_NAME}'...")
points = []
offset = None

while True:
    # Fetch points via HTTP API
    payload = {
        "limit": 100,
        "with_payload": True,
        "with_vector": False
    }
    if offset:
        payload["offset"] = offset

    response = requests.post(
        f"{url_base}/collections/{COLLECTION_NAME}/points/scroll",
        json=payload
    )

    if response.status_code != 200:
        print(f"   ERROR fetching points: {response.status_code}")
        print(response.text)
        exit(1)

    data = response.json()
    result = data.get('result', {})
    batch_points = result.get('points', [])
    points.extend(batch_points)

    next_offset = result.get('next_page_offset')
    if not next_offset:
        break
    offset = next_offset

print(f"   OK Fetched {len(points)} points")

print(f"\n4. Generating embeddings...")
updated_points = []

for idx, point in enumerate(points, 1):
    # Get content from payload
    payload_data = point.get('payload', {})
    content = payload_data.get('content', '')
    section_name = payload_data.get('section_name', '')

    # Combine for better embeddings
    text = f"{section_name}\n\n{content}"

    # Generate embedding
    embedding = model.encode(text, convert_to_tensor=False)

    # Create updated point
    updated_point = {
        "id": point['id'],
        "vector": embedding.tolist(),
        "payload": payload_data
    }
    updated_points.append(updated_point)

    if idx % 5 == 0:
        print(f"   Progress: {idx}/{len(points)} embeddings")

print(f"   OK All {len(updated_points)} embeddings generated")

print(f"\n5. Updating points in Qdrant...")
batch_size = 50
for i in range(0, len(updated_points), batch_size):
    batch = updated_points[i:i+batch_size]

    response = requests.put(
        f"{url_base}/collections/{COLLECTION_NAME}/points",
        json={"points": batch}
    )

    if response.status_code == 200:
        print(f"   OK Batch {i//batch_size + 1} uploaded ({len(batch)} points)")
    else:
        print(f"   ERROR batch {i//batch_size + 1}: {response.status_code}")

print(f"\n6. Verifying...")
response = requests.get(f"{url_base}/collections/{COLLECTION_NAME}")
if response.status_code == 200:
    data = response.json()
    result = data.get('result', {})
    print(f"   Points: {result.get('points_count')}")
    print(f"   Vectors: {result.get('vectors_count')}")
    print(f"   Indexed vectors: {result.get('indexed_vectors_count')}")
    print(f"   Status: {result.get('status')}")

print("\n" + "=" * 80)
print("SUCCESS! EMBEDDINGS GENERATED")
print("=" * 80)

# Test search
print("\n7. Testing semantic search...")
test_query = "Какие требования к бюджету проекта?"
query_embedding = model.encode(test_query, convert_to_tensor=False)

response = requests.post(
    f"{url_base}/collections/{COLLECTION_NAME}/points/search",
    json={
        "vector": query_embedding.tolist(),
        "limit": 3,
        "with_payload": True
    }
)

if response.status_code == 200:
    data = response.json()
    results = data.get('result', [])

    print(f"\nQuery: {test_query}")
    print("\nTop 3 results:")
    for i, hit in enumerate(results, 1):
        payload = hit.get('payload', {})
        score = hit.get('score', 0)
        section_name = payload.get('section_name', 'Unknown')
        content = payload.get('content', '')

        print(f"\n{i}. {section_name}")
        print(f"   Score: {score:.3f}")
        print(f"   Preview: {content[:150]}...")

print("\n" + "=" * 80)
print("LOCALHOST QDRANT READY FOR SYNC TO PRODUCTION!")
print("=" * 80)
