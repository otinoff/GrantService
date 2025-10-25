#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск информации в коллекции Sber500 Bootcamp

Назначение: Быстрый semantic search для нахождения нужной информации

Usage:
    python search_bootcamp.py "Критерии оценки"
    python search_bootcamp.py "Воркшопы про метрики"
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

def search_bootcamp(query: str, limit: int = 5, show_full_text: bool = False):
    """
    Поиск информации о буткэмпе

    Args:
        query: Поисковый запрос
        limit: Количество результатов
        show_full_text: Показать полный текст или только начало
    """

    # Initialize
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(host="5.35.88.251", port=6333)

    print("🤖 Loading model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Generate query embedding
    query_vector = model.encode(query).tolist()

    # Search in Qdrant
    print(f"\n🔍 Searching: '{query}'\n")
    print("=" * 80)

    results = client.search(
        collection_name="sber500_bootcamp",
        query_vector=query_vector,
        limit=limit
    )

    if not results:
        print("❌ No results found")
        return

    # Display results
    for i, result in enumerate(results, 1):
        score = result.score
        payload = result.payload

        # Importance emoji
        importance_emoji = {
            "critical": "🔥",
            "high": "⚡",
            "medium": "📌",
            "low": "📄"
        }.get(payload.get("importance", "medium"), "📄")

        # Header
        print(f"\n{i}. [{score:.3f}] {importance_emoji} {payload['title']}")
        print("-" * 80)

        # Metadata
        print(f"📁 Source: {payload['source']}")
        print(f"🏷️  Category: {payload['category']}")
        print(f"📅 Added: {payload['date_added']}")

        if "deadline" in payload:
            print(f"⏰ Deadline: {payload['deadline']}")

        if "url" in payload:
            print(f"🔗 URL: {payload['url']}")

        # Text
        text = payload['text'].strip()
        if show_full_text:
            print(f"\n📄 Full text:\n{text}")
        else:
            # Show first 300 chars
            preview = text[:300] + "..." if len(text) > 300 else text
            print(f"\n📄 Preview:\n{preview}")

        print("=" * 80)

def interactive_search():
    """Интерактивный режим поиска"""

    print("\n" + "=" * 80)
    print("🔍 Sber500 Bootcamp Knowledge Base - Interactive Search")
    print("=" * 80)
    print("\nCommands:")
    print("  - Type your search query")
    print("  - 'full' - toggle full text display")
    print("  - 'exit' or 'quit' - exit")
    print("\n" + "=" * 80 + "\n")

    show_full = False
    limit = 3

    while True:
        try:
            query = input("\n🔍 Search: ").strip()

            if not query:
                continue

            if query.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break

            if query.lower() == 'full':
                show_full = not show_full
                status = "ON" if show_full else "OFF"
                print(f"📄 Full text display: {status}")
                continue

            if query.startswith('limit:'):
                try:
                    limit = int(query.split(':')[1].strip())
                    print(f"📊 Limit set to: {limit}")
                    continue
                except:
                    print("❌ Invalid limit format. Use: limit:5")
                    continue

            # Perform search
            search_bootcamp(query, limit=limit, show_full_text=show_full)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    """Main entry point"""

    if len(sys.argv) > 1:
        # Command line search
        query = " ".join(sys.argv[1:])
        search_bootcamp(query, limit=5, show_full_text=False)
    else:
        # Interactive mode
        interactive_search()

if __name__ == "__main__":
    main()
