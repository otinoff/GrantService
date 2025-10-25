#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавить детальную информацию "О Буткемпе" Sber500xGigaChat
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import uuid

def add_bootcamp_about():
    """Добавить детальную информацию о буткемпе"""

    # Initialize
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(host="5.35.88.251", port=6333)

    print("🤖 Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Document
    documents = [
        {
            "text": """
О Буткемпе Sber500×GigaChat

ОПИСАНИЕ:
Буткемп Sber500×GigaChat — это заочный этап программы, открытый для всех стартапов,
готовых интегрировать GigaChat в свои решения или создать продукт на его основе.

ЧТО ПОЛУЧАЮТ УЧАСТНИКИ:

1. Доступ к токенам для тестирования гипотез с GigaChat
   - 6,000,000 токенов GigaChat (для GrantService)
   - 5,000,000 токенов Embeddings
   - Срок действия: до октября 2026

2. База онлайн-материалов и обучающий контент
   - Раздел 1: О программе
   - Раздел 2: Курсы от GigaChat
   - Раздел 3: 9 бизнес-воркшопов
   - Раздел 4: Live Sessions

3. Шанс продемонстрировать результаты интеграции
   - Демо-день для лучших проектов
   - Презентация на Moscow Startup Summit
   - Visibility перед инвесторами и партнёрами

ГЛАВНАЯ ЦЕЛЬ БУТКЕМПА:
Проверить возможные сценарии применения GigaChat и доказать бизнес-ценность этого решения.

КРИТЕРИИ ОТБОРА В ТОП50:
- Зрелость кейса использования GigaChat
- Объём использованных токенов
- Качество интеграции
- Бизнес-применимость решения
- Демонстрируемые результаты

ЧТО ПОЛУЧАЮТ ТОП50 (ОСНОВНОЙ ЭТАП - АКСЕЛЕРАТОР):

1. Поддержку международных менторов Sber500
   - Опытные предприниматели и инвесторы
   - Экспертиза в AI и стартапах
   - Индивидуальные сессии

2. Доступ к специалистам GigaChat
   - Техническая поддержка
   - Best practices интеграции
   - Advanced features

3. Доступ к API и RAG-технологиям GigaChat
   - Extended API access
   - RAG (Retrieval-Augmented Generation)
   - Advanced models
   - Priority support

4. Пилотные проекты со Сбером и партнёрами
   - Реальные проекты
   - Внедрение в production
   - Reference cases
   - B2B connections

5. Возможность привлечения инвестиций
   - Pitch перед инвесторами
   - Demo Day
   - Investor networking
   - Funding opportunities

СТРУКТУРА ПРОГРАММЫ:

Этап 1: Онлайн-буткемп (4 недели)
├─ Неделя 1: Intensive testing
├─ Неделя 2-3: Scale & optimization
├─ Неделя 4: Quality demonstration
└─ Результат: Отбор ТОП50

Этап 2: Акселератор (10 онлайн-недель)
├─ Недели 1-3: Менторинг и доработка
├─ Недели 4-7: Пилотные проекты
├─ Недели 8-9: Подготовка к Demo Day
└─ Неделя 10: Demo Day + Инвестиции

ФИНАЛЬНОЕ СОБЫТИЕ:
Demo Day на Moscow Startup Summit
- Презентация продукта на сцене
- Встречи с инвесторами
- Media visibility
- Partnership opportunities

ПУТЬ РОСТА:
Онлайн-буткемп → ТОП50 → Акселератор → Demo Day → Инвестиции

Длительность полной программы: ~14 недель (4 недели буткемп + 10 недель акселератор)

ДОСТУП К ПОРТАЛУ:
URL: https://sber500.2080vc.io
Login: otinoff@gmail.com
Тип доступа: Одноразовый код (при каждом входе)

РАЗДЕЛЫ ПОРТАЛА:
- Раздел 1: О программе Sber500xGigaChat
- Раздел 2: Курсы от GigaChat
- Раздел 3: Бизнес-воркшопы (9 воркшопов)
- Раздел 4: Live Sessions

ЦЕННОСТЬ ДЛЯ GRANTSERVICE:

1. Validation
   - Проверка бизнес-модели с экспертами
   - Feedback от менторов
   - Testing гипотез

2. Network
   - Доступ к Sber экосистеме
   - Partnership opportunities
   - Investor connections

3. Resources
   - 6M токенов GigaChat
   - Технические ресурсы
   - Обучающие материалы

4. Market Access
   - B2B клиенты через Сбер
   - Пилотные проекты
   - Reference cases

5. Investment
   - Возможность привлечь funding
   - Visibility перед инвесторами
   - Demo Day exposure

КЛЮЧЕВЫЕ ТРЕБОВАНИЯ:
- Интеграция GigaChat в продукт
- Демонстрация бизнес-ценности
- Активное использование токенов
- Презентация результатов

TIMELINE:
- Начало буткемпа: октябрь 2025
- Отбор ТОП50: через 4 недели
- Акселератор: 10 недель
- Demo Day: ~март 2026

КОНКУРЕНТНОЕ ПРЕИМУЩЕСТВО GRANTSERVICE:
- Real production product (Telegram bot)
- Real users (НКО, соискатели грантов)
- High token consumption (50-80k на заявку)
- Multi-agent architecture (4 агента)
- Social impact (помощь НКО)
- Scalable (batch processing готов)

ШАНСЫ ПОПАСТЬ В ТОП50: Высокие
Причины:
✓ Real use case (не синтетика)
✓ Production deployment
✓ Multi-agent = больше токенов
✓ Social impact
✓ Technical excellence
✓ Scalability demonstrated
            """,
            "title": "О Буткемпе Sber500×GigaChat: Полное описание программы",
            "source": "portal",
            "category": "program_info",
            "section": "about_bootcamp",
            "date_added": "2025-10-23",
            "url": "https://sber500.2080vc.io/members/courses/sber500xgigachat/intro-ot-komandy-gigachat-900194949061",
            "importance": "critical",
            "stage": "bootcamp",
            "duration": "14 weeks total"
        }
    ]

    # Add document
    print(f"\n📝 Adding detailed bootcamp information...\n")

    for doc in documents:
        # Generate embedding
        embedding = model.encode(doc["text"]).tolist()

        # Upload to Qdrant
        client.upsert(
            collection_name="sber500_bootcamp",
            points=[
                {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": doc
                }
            ]
        )

        importance_emoji = {
            "critical": "🔥",
            "high": "⚡",
            "medium": "📌",
            "low": "📄"
        }.get(doc.get("importance", "medium"), "📄")

        print(f"✅ {importance_emoji} {doc['title']}")
        print(f"   Source: {doc['source']} | Category: {doc['category']}")
        print(f"   Duration: {doc['duration']}")
        print()

    print(f"✅ Document added successfully!")

    # Get collection info
    collection_info = client.get_collection(collection_name="sber500_bootcamp")
    print(f"\n📊 Collection 'sber500_bootcamp' now has {collection_info.points_count} documents")

    # Print key info
    print("\n" + "="*80)
    print("🎯 KEY INFORMATION")
    print("="*80)
    print("📚 Буткемп: 4 недели (intensive testing)")
    print("🚀 Акселератор: 10 недель (для ТОП50)")
    print("🎤 Demo Day: Moscow Startup Summit")
    print("\n💰 Что получаем:")
    print("   ✓ Токены: 6M GigaChat + 5M Embeddings")
    print("   ✓ Менторы: Международные эксперты")
    print("   ✓ Пилоты: Проекты со Сбером")
    print("   ✓ Инвестиции: Demo Day + investor networking")
    print("\n🎯 Цель: Попасть в ТОП50 для акселератора!")
    print("="*80)

if __name__ == "__main__":
    add_bootcamp_about()
