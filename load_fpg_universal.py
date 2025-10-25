#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal FPG knowledge base loader - handles both structured and unstructured sections
"""
import requests
import json
import re

QDRANT_URL = "http://5.35.88.251:6333"
COLLECTION_NAME = "knowledge_sections"
FPG_KB_FILE = "fpg_docs_2025/UNIFIED_KNOWLEDGE_BASE.md"

print("=" * 80)
print("UNIVERSAL FPG KNOWLEDGE BASE LOADER")
print("=" * 80)

print(f"\n1. Parsing {FPG_KB_FILE}...")
with open(FPG_KB_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

sections = []
lines = content.split('\n')
i = 0
current_category = "Общие"

while i < len(lines):
    line = lines[i]

    # Category (# Level 1 heading)
    if line.startswith('# ') and not line.startswith('## '):
        category_text = line[2:].strip()
        # Skip meta headers
        if category_text not in ['ПОЛНАЯ БАЗА ЗНАНИЙ: Грантовые заявки ФПГ',
                                  'База знаний: Грантовые заявки ФПГ',
                                  'База знаний по созданию заявки в Фонд президентских грантов']:
            current_category = category_text
        i += 1
        continue

    # Section (## Level 2 heading)
    if line.startswith('## '):
        section_title = line[3:].strip()

        # Skip meta sections
        if section_title in ['О базе знаний', 'Содержание']:
            i += 1
            continue

        # Collect section content
        i += 1
        section_lines = []
        source_url = None

        # Read until next section or end
        while i < len(lines):
            current_line = lines[i]

            # Stop at next section
            if current_line.startswith('## ') or current_line.startswith('# '):
                break

            # Extract source URL if present
            url_match = re.search(r'\*\*Источник:\*\* \[([^\]]+)\]\(([^\)]+)\)', current_line)
            if url_match:
                source_url = url_match.group(2)

            # Collect content (skip meta lines)
            if current_line.strip() and \
               not current_line.startswith('**Размер:**') and \
               not current_line.startswith('**Источник:**') and \
               current_line.strip() != '### Полный текст' and \
               current_line.strip() != '---':
                section_lines.append(current_line)

            i += 1

        # Join content
        section_content = '\n'.join(section_lines).strip()

        # Only add if has substantial content (>200 chars)
        if len(section_content) > 200:
            sections.append({
                'title': section_title,
                'url': source_url,
                'content': section_content,
                'category': current_category
            })

        continue

    i += 1

print(f"   OK Parsed {len(sections)} sections")

# Show first few sections for verification
print("\nFirst 5 sections:")
for idx, sec in enumerate(sections[:5], 1):
    print(f"  {idx}. {sec['title'][:60]}... ({len(sec['content'])} chars)")

print("\nLast 5 sections:")
for idx, sec in enumerate(sections[-5:], 1):
    print(f"  {idx}. {sec['title'][:60]}... ({len(sec['content'])} chars)")

print(f"\n2. Recreating collection '{COLLECTION_NAME}'...")
# Delete old collection
response = requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
print(f"   Deleted old collection: {response.status_code}")

# Create new collection
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
else:
    print(f"   ERROR: {response.status_code} - {response.text}")
    exit(1)

print(f"\n3. Uploading {len(sections)} points...")
points = []

for idx, section in enumerate(sections, 1):
    # Simple embedding: zeros for now (will generate real embeddings later)
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
            "section_type": "knowledge"
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
print("SUCCESS! FULL FPG KNOWLEDGE BASE LOADED")
print("=" * 80)
print(f"\nLoaded {len(sections)} sections:")
print(f"  - Part 1 (Official requirements): ~15 sections")
print(f"  - Part 2 (Practical recommendations): ~{len(sections)-15} sections")
print("\nNOTE: Vectors are placeholder (zeros).")
print("Next step: Generate embeddings with sentence-transformers")
print("Run on server: python generate_embeddings_prod.py")
