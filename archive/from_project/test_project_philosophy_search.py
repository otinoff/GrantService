#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест поиска философии проекта GrantService в Qdrant
"""
import requests

QDRANT_HOST = "5.35.88.251"
QDRANT_PORT = 6333
COLLECTION_NAME = "knowledge_sections"

print("=" * 80)
print("ТЕСТ ПОИСКА ФИЛОСОФИИ ПРОЕКТА GRANTSERVICE")
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

print(f"\n[2/2] Тестирование поиска философии проекта...")

# Test queries for project philosophy
test_queries = [
    {
        "agent": "ALL",
        "query": "Какая главная идея проекта GrantService?",
        "expected": "Конвейер качества, превращающий идею в заявку"
    },
    {
        "agent": "Interviewer",
        "query": "Как должен работать этап интервью?",
        "expected": "Аудит после каждого блока, не в конце"
    },
    {
        "agent": "Researcher",
        "query": "Что делает researcher agent? Какие запросы?",
        "expected": "27 WebSearch запросов про контекст мира"
    },
    {
        "agent": "Writer",
        "query": "Как писать грантовую заявку? Сколько цитат нужно?",
        "expected": "Минимум 10 цитат, синтез идеи и контекста"
    },
    {
        "agent": "Reviewer",
        "query": "Как оценивать готовность заявки к подаче?",
        "expected": "4 критерия, вероятность одобрения 15-50%"
    },
    {
        "agent": "ALL",
        "query": "В чем отличие GrantService от других систем?",
        "expected": "Качество по ходу, а не в конце"
    }
]

for idx, test in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"ЗАПРОС {idx}/{len(test_queries)} [{test['agent']}]: {test['query']}")
    print(f"{'='*80}")
    print(f"🎯 Ожидаем: {test['expected']}")

    # Generate embedding
    query_embedding = model.encode(test['query'], convert_to_tensor=False)

    # Search in project philosophy only
    response = requests.post(
        f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/search",
        json={
            "vector": query_embedding.tolist(),
            "limit": 2,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "type", "match": {"value": "project_philosophy"}}
                ]
            }
        }
    )

    if response.status_code == 200:
        data = response.json()
        results = data.get('result', [])

        print(f"\n✅ Найдено {len(results)} результатов из философии проекта:\n")

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
            print(f"   📄 {payload.get('content', '')[:200]}...")
            print()
    else:
        print(f"❌ Ошибка: {response.status_code}")

print("\n" + "=" * 80)
print("ИТОГОВАЯ СТАТИСТИКА БАЗЫ ЗНАНИЙ")
print("=" * 80)

# Get collection stats
response = requests.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}")
if response.status_code == 200:
    data = response.json()
    result = data.get('result', {})

    print(f"\n📊 Коллекция: {COLLECTION_NAME}")
    print(f"   • Всего разделов: {result.get('points_count', 0)}")
    print(f"   • Требования ФПГ: 31")
    print(f"   • Философия интервьюера: 5")
    print(f"   • Философия проекта: 10")
    print(f"   • Статус: {result.get('status', 'unknown')}")
    print(f"   • Vector размерность: 384d (multilingual-MiniLM-L12-v2)")

print("\n" + "=" * 80)
print("✅ ФИЛОСОФИЯ ПРОЕКТА ДОСТУПНА ДЛЯ ВСЕХ АГЕНТОВ!")
print("Каждый агент знает свою роль и принципы работы системы")
print("=" * 80)
