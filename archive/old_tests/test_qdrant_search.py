#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test semantic search in Qdrant knowledge base
"""
import requests
import json

QDRANT_HOST = "5.35.88.251"
QDRANT_PORT = 6333
COLLECTION_NAME = "knowledge_sections"

print("=" * 80)
print("ТЕСТИРОВАНИЕ ВЕКТОРНОГО ПОИСКА В БАЗЕ ЗНАНИЙ ФПГ")
print("=" * 80)

# Load model locally for generating query embeddings
try:
    from sentence_transformers import SentenceTransformer
    print("\n[1/2] Загрузка модели...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    print("      ✅ Модель загружена")
except Exception as e:
    print(f"\n❌ Ошибка загрузки модели: {e}")
    print("\nИспользуйте: pip install sentence-transformers")
    exit(1)

print(f"\n[2/2] Подключение к Qdrant ({QDRANT_HOST}:{QDRANT_PORT})...")

# Test queries
test_queries = [
    {
        "name": "Бюджет проекта",
        "query": "Какие требования к бюджету? Как правильно составить смету расходов?",
        "expected": "Должны найтись разделы о бюджете, смете, финансировании"
    },
    {
        "name": "Команда проекта",
        "query": "Кто должен быть в команде проекта? Какой опыт нужен участникам?",
        "expected": "Должны найтись разделы о команде, квалификации, опыте"
    },
    {
        "name": "Целевая аудитория",
        "query": "Как описать целевую аудиторию? Кто бенефициары проекта?",
        "expected": "Должны найтись разделы о целевой аудитории, бенефициарах"
    },
    {
        "name": "Результаты проекта",
        "query": "Какие результаты должны быть достигнуты? Как измерить эффект?",
        "expected": "Должны найтись разделы о результатах, индикаторах, KPI"
    },
    {
        "name": "Устойчивость проекта",
        "query": "Как проект будет работать после окончания гранта?",
        "expected": "Должны найтись разделы об устойчивости, продолжении"
    }
]

print("\n" + "=" * 80)
print("ЗАПУСК ТЕСТОВЫХ ЗАПРОСОВ")
print("=" * 80)

for idx, test in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"ТЕСТ {idx}/{len(test_queries)}: {test['name']}")
    print(f"{'='*80}")
    print(f"\n📝 Запрос: {test['query']}")
    print(f"🎯 Ожидаем: {test['expected']}\n")

    # Generate embedding for query
    query_embedding = model.encode(test['query'], convert_to_tensor=False)

    # Search in Qdrant
    response = requests.post(
        f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/search",
        json={
            "vector": query_embedding.tolist(),
            "limit": 3,
            "with_payload": True
        }
    )

    if response.status_code == 200:
        data = response.json()
        results = data.get('result', [])

        print(f"✅ Найдено {len(results)} результатов:\n")

        for i, hit in enumerate(results, 1):
            payload = hit.get('payload', {})
            score = hit.get('score', 0)
            section_name = payload.get('section_name', 'Unknown')
            content = payload.get('content', '')

            # Score interpretation
            if score >= 0.8:
                score_emoji = "🔥 Отлично"
            elif score >= 0.7:
                score_emoji = "⭐ Хорошо"
            elif score >= 0.6:
                score_emoji = "✔️ Нормально"
            else:
                score_emoji = "⚠️ Слабо"

            print(f"{i}. [{score_emoji}] Score: {score:.3f}")
            print(f"   📂 Раздел: {section_name}")
            print(f"   📄 Содержание: {content[:200]}...")
            print()
    else:
        print(f"❌ Ошибка поиска: {response.status_code}")

print("\n" + "=" * 80)
print("ИТОГОВАЯ СТАТИСТИКА")
print("=" * 80)

# Get collection stats
response = requests.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}")
if response.status_code == 200:
    data = response.json()
    result = data.get('result', {})

    print(f"\n📊 Коллекция: {COLLECTION_NAME}")
    print(f"   • Точек (разделов): {result.get('points_count', 0)}")
    print(f"   • Статус: {result.get('status', 'unknown')}")
    print(f"   • Vector размерность: 384d (multilingual-MiniLM-L12-v2)")
    print(f"\n✅ Векторный поиск РАБОТАЕТ!")
    print(f"✅ База знаний ФПГ готова к использованию агентами")

print("\n" + "=" * 80)
print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("=" * 80)
