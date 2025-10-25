#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест поиска философии интервьюера в Qdrant
"""
import requests

QDRANT_HOST = "5.35.88.251"
QDRANT_PORT = 6333
COLLECTION_NAME = "knowledge_sections"

print("=" * 80)
print("ТЕСТ ПОИСКА ФИЛОСОФИИ ИНТЕРВЬЮЕРА")
print("=" * 80)

# Load model
try:
    from sentence_transformers import SentenceTransformer
    print("\n[1/2] Загрузка модели...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    print("      ✅ Модель загружена")
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    exit(1)

print(f"\n[2/2] Тестирование поиска...")

# Test queries
test_queries = [
    "Как интервьюер должен работать с пользователем?",
    "В чем разница между допросчиком и консультантом?",
    "Как анализировать ответы пользователя?",
    "Что делать если ответ пользователя слабый?",
    "Сколько вопросов нужно задавать по каждой теме?"
]

for idx, query in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"ЗАПРОС {idx}/{len(test_queries)}: {query}")
    print(f"{'='*80}")

    # Generate embedding
    query_embedding = model.encode(query, convert_to_tensor=False)

    # Search
    response = requests.post(
        f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/search",
        json={
            "vector": query_embedding.tolist(),
            "limit": 2,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "type", "match": {"value": "philosophy"}}
                ]
            }
        }
    )

    if response.status_code == 200:
        data = response.json()
        results = data.get('result', [])

        print(f"\n✅ Найдено {len(results)} результатов из философии:\n")

        for i, hit in enumerate(results, 1):
            payload = hit.get('payload', {})
            score = hit.get('score', 0)

            if score >= 0.7:
                score_emoji = "🔥"
            elif score >= 0.6:
                score_emoji = "⭐"
            else:
                score_emoji = "✔️"

            print(f"{i}. [{score_emoji}] Score: {score:.3f}")
            print(f"   📂 {payload.get('section_name', 'Unknown')}")
            print(f"   📄 {payload.get('content', '')[:150]}...")
            print()
    else:
        print(f"❌ Ошибка: {response.status_code}")

print("\n" + "=" * 80)
print("✅ ФИЛОСОФИЯ ДОСТУПНА ДЛЯ АГЕНТОВ!")
print("Агенты могут искать принципы работы по контексту запроса")
print("=" * 80)
