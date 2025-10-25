#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple FPG knowledge base loader - uses only Qdrant HTTP API
No heavy dependencies required
"""
import requests
import json
import re

QDRANT_URL = "http://5.35.88.251:6333"
COLLECTION_NAME = "knowledge_sections"
FPG_KB_FILE = "fpg_docs_2025/UNIFIED_KNOWLEDGE_BASE.md"

print("=" * 80)
print("SIMPLE FPG KNOWLEDGE BASE LOADER")
print("=" * 80)

print(f"\n1. Parsing {FPG_KB_FILE}...")
with open(FPG_KB_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

sections = []
current_category = "Общие"
current_article = None
current_url = None
article_text = []
collecting_text = False

category_pattern = r'^# ([^#\n]+)$'
article_pattern = r'^## (.+)$'
url_pattern = r'\*\*Источник:\*\* \[([^\]]+)\]\(([^\)]+)\)'

for line in content.split('\n'):
    category_match = re.match(category_pattern, line)
    if category_match:
        current_category = category_match.group(1).strip()
        continue

    article_match = re.match(article_pattern, line)
    if article_match:
        if current_article and article_text:
            full_text = '\n'.join(article_text).strip()
            if len(full_text) > 100:
                sections.append({
                    'title': current_article,
                    'url': current_url,
                    'content': full_text,
                    'category': current_category
                })

        current_article = article_match.group(1).strip()
        current_url = None
        article_text = []
        collecting_text = False
        continue

    url_match = re.search(url_pattern, line)
    if url_match:
        current_url = url_match.group(2)
        continue

    if '### Полный текст' in line or '### Текст' in line:
        collecting_text = True
        continue

    if collecting_text and current_article:
        if line.strip() not in ['---', ''] and not line.startswith('##'):
            article_text.append(line)

# Last section
if current_article and article_text:
    full_text = '\n'.join(article_text).strip()
    if len(full_text) > 100:
        sections.append({
            'title': current_article,
            'url': current_url,
            'content': full_text,
            'category': current_category
        })

print(f"   OK Parsed {len(sections)} sections")

print(f"\n2. Creating collection '{COLLECTION_NAME}'...")
# Create collection with dummy vectors (will use direct text search)
collection_config = {
    "vectors": {
        "size": 384,
        "distance": "Cosine"
    }
}

response = requests.put(
    f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
    json=collection_config
)

if response.status_code in [200, 201]:
    print("   OK Collection created")
elif response.status_code == 409:
    print("   OK Collection already exists")
else:
    print(f"   ERROR: {response.status_code} - {response.text}")

print(f"\n3. Uploading {len(sections)} points...")
points = []

for idx, section in enumerate(sections, 1):
    # Simple embedding: just zeros for now (we'll add real embeddings later)
    vector = [0.0] * 384

    point = {
        "id": idx,
        "vector": vector,
        "payload": {
            "section_name": section['title'],
            "content": section['content'],
            "source_url": section.get('url', ''),
            "fund_name": "fpg",
            "category": section['category'],
            "section_type": "general"
        }
    }
    points.append(point)

# Upload in batches
batch_size = 50
for i in range(0, len(points), batch_size):
    batch = points[i:i+batch_size]
    response = requests.put(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points",
        json={"points": batch}
    )

    if response.status_code == 200:
        print(f"   OK Uploaded batch {i//batch_size + 1} ({len(batch)} points)")
    else:
        print(f"   ERROR batch {i//batch_size + 1}: {response.status_code}")

print(f"\n4. Verifying...")
response = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
if response.status_code == 200:
    data = response.json()
    result = data.get('result', {})
    print(f"   Points count: {result.get('points_count', 0)}")
    print(f"   Status: {result.get('status', 'unknown')}")

print("\n" + "=" * 80)
print("SUCCESS! FPG KNOWLEDGE BASE LOADED")
print("=" * 80)
print("\nNOTE: Vectors are placeholder (zeros).")
print("For semantic search, run with sentence-transformers on server.")
