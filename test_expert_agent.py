"""Простой тест Expert Agent"""
import sys
sys.path.append('C:\\SnowWhiteAI\\GrantService')

print("1. Импорт модулей...")
from expert_agent import ExpertAgent

print("2. Создание Expert Agent (это займёт ~30 секунд - загружается модель)...")
agent = ExpertAgent()

print("3. Получение статистики...")
stats = agent.get_statistics()

print("\nСтатистика:")
print(f"  PostgreSQL разделов: {stats['postgres']['sections']}")
print(f"  Qdrant векторов: {stats['qdrant']['vectors']}")

if stats['qdrant']['vectors'] == 0:
    print("\n4. Создание embeddings для существующих разделов...")

    # Получить разделы
    cursor = agent.pg_conn.cursor()
    cursor.execute("""
        SELECT ks.id, ks.content, ks.section_name, ks.section_type,
               ks.priority, ks.char_limit, ks.tags, src.fund_name
        FROM knowledge_sections ks
        JOIN knowledge_sources src ON ks.source_id = src.id
        LIMIT 10
    """)

    rows = cursor.fetchall()
    print(f"   Найдено {len(rows)} разделов")

    from qdrant_client.models import PointStruct
    points = []

    for row in rows:
        print(f"   - Создание embedding для: {row[2]}")
        embedding = agent.create_embedding(row[1])

        points.append(PointStruct(
            id=row[0],
            vector=embedding,
            payload={
                "section_id": row[0],
                "section_name": row[2],
                "section_type": row[3],
                "fund_name": row[7],
                "priority": row[4],
                "char_limit": row[5],
                "tags": row[6] or []
            }
        ))

    print(f"   Загрузка {len(points)} векторов в Qdrant...")
    agent.qdrant.upsert(collection_name=agent.collection_name, points=points)
    print(f"   OK! Векторы загружены!")

print("\n5. Тестовый запрос...")
results = agent.query_knowledge(
    question="Какие требования к названию проекта?",
    fund="fpg",
    top_k=3
)

print(f"\nНайдено {len(results)} результатов:\n")
for i, r in enumerate(results, 1):
    print(f"{i}. {r['section_name']} (score: {r['relevance_score']:.3f})")
    print(f"   {r['content'][:150]}...")
    print()

agent.close()
print("\nТест завершён успешно!")
