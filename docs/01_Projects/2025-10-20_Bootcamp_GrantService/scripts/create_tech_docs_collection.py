#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создать коллекцию для технической документации GrantService
Все пароли, API keys, команды, структура - в векторной БД для быстрого поиска
"""

import sys
from pathlib import Path

# Пути
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import uuid
from sentence_transformers import SentenceTransformer

def create_tech_docs_collection():
    """Создать коллекцию grantservice_tech_docs"""

    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(host="5.35.88.251", port=6333)

    collection_name = "grantservice_tech_docs"

    # Проверить существование
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)

    if exists:
        print(f"⚠️  Коллекция '{collection_name}' уже существует")
        user_input = input("Удалить и пересоздать? (y/n): ")
        if user_input.lower() == 'y':
            client.delete_collection(collection_name)
            print(f"🗑️  Коллекция '{collection_name}' удалена")
        else:
            print("❌ Отменено")
            return

    # Создать коллекцию
    print(f"📦 Создание коллекции '{collection_name}'...")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=768,  # paraphrase-multilingual-MiniLM-L12-v2
            distance=Distance.COSINE
        )
    )

    print(f"✅ Коллекция '{collection_name}' создана!")

    # Информация
    collection_info = client.get_collection(collection_name)
    print(f"\n📊 Информация о коллекции:")
    print(f"   Название: {collection_name}")
    print(f"   Размерность: 768")
    print(f"   Метрика: COSINE")
    print(f"   Векторов: {collection_info.points_count}")

    print(f"\n🎯 Готово к добавлению документов!")
    print(f"   Следующий шаг: python add_tech_docs.py")

if __name__ == "__main__":
    create_tech_docs_collection()
