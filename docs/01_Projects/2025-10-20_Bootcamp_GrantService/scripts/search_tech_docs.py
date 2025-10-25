#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Search по технической документации GrantService
Быстрый поиск паролей, API keys, команд
"""

import sys
from pathlib import Path

# Пути
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

def search_tech_docs(query: str, limit: int = 3, show_full: bool = False):
    """Поиск по технической документации"""

    # Connect
    client = QdrantClient(host="5.35.88.251", port=6333)
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Search
    query_vector = model.encode(query).tolist()
    results = client.search(
        collection_name="grantservice_tech_docs",
        query_vector=query_vector,
        limit=limit
    )

    # Display
    print(f"\n🔍 Поиск: '{query}'")
    print(f"📊 Найдено: {len(results)} результатов\n")

    for i, hit in enumerate(results, 1):
        score = hit.score
        payload = hit.payload

        importance_emoji = {
            "critical": "🔥",
            "high": "⚡",
            "medium": "📌",
            "low": "📄"
        }.get(payload.get("importance", "medium"), "📄")

        print(f"{i}. {importance_emoji} {payload.get('title', 'Без названия')}")
        print(f"   Score: {score:.3f} | Category: {payload.get('category', 'unknown')}")

        if 'tags' in payload:
            print(f"   Tags: {', '.join(payload['tags'])}")

        print()

        # Показать текст
        if show_full:
            print("   " + "─" * 70)
            print(payload.get('text', '').strip())
            print("   " + "─" * 70)
            print()
        else:
            # Показать первые 300 символов
            text = payload.get('text', '').strip()
            preview = text[:300] + "..." if len(text) > 300 else text
            print(f"   {preview}")
            print()

    print("-" * 80)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Поиск по технической документации GrantService")
    parser.add_argument("query", nargs="?", help="Поисковый запрос")
    parser.add_argument("-l", "--limit", type=int, default=3, help="Количество результатов")
    parser.add_argument("-f", "--full", action="store_true", help="Показать полный текст")

    args = parser.parse_args()

    if args.query:
        # Single search
        search_tech_docs(args.query, limit=args.limit, show_full=args.full)
    else:
        # Interactive mode
        print("="*80)
        print("🔍 Semantic Search - Техническая документация GrantService")
        print("="*80)
        print("\nПримеры запросов:")
        print("  • пароль базы данных")
        print("  • api key gigachat")
        print("  • как запустить бота")
        print("  • postgresql подключение")
        print("  • команды ssh")
        print("\nВведите 'exit' для выхода\n")

        while True:
            try:
                query = input("🔍 Search: ").strip()

                if not query:
                    continue

                if query.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 До свидания!")
                    break

                search_tech_docs(query, limit=args.limit, show_full=args.full)

            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}\n")

if __name__ == "__main__":
    main()
