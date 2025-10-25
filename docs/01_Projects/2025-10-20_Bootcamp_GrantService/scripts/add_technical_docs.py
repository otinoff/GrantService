#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавить техническую документацию GigaChat и стратегию использования токенов
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import uuid

def add_technical_docs():
    """Добавить техническую документацию и инструкции"""

    # Initialize
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(host="5.35.88.251", port=6333)

    print("🤖 Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Documents
    documents = [
        {
            "text": """
Техническая документация GigaChat - Полезные ресурсы

ОФИЦИАЛЬНЫЕ РЕСУРСЫ:

1. Официальная документация GigaChat
   URL: https://developers.sber.ru/docs/ru/gigachat/api/overview

   Содержит:
   - Подробное описание API
   - Инструкции по подключению
   - Примеры интеграций
   - Reference всех endpoints
   - Best practices

   Ключевые разделы:
   - Authentication (OAuth 2.0)
   - /chat/completions endpoint
   - /embeddings endpoint
   - Error handling
   - Rate limits
   - Streaming responses

2. GigaChain
   URL: https://developers.sber.ru/docs/ru/gigachain/overview

   Описание:
   Фреймворк для построения приложений с использованием LLM GigaChat.
   Аналог LangChain, но оптимизирован для GigaChat.

   Возможности:
   - Chains (цепочки вызовов)
   - Memory (контекст диалога)
   - Agents (автономные агенты)
   - Tools (интеграции с внешними API)
   - Retrieval (RAG - Retrieval-Augmented Generation)

   Use cases:
   - Chatbots с памятью
   - RAG systems (поиск + генерация)
   - Multi-step reasoning
   - Tool-using agents

3. Библиотека кейсов GigaChat
   URL: https://giga.chat/b2b/cases

   Содержит:
   Реальные примеры внедрения GigaChat в бизнесе:
   - Автоматизация процессов
   - Создание новых продуктов
   - Customer service automation
   - Document processing
   - Content generation

   Полезно для:
   - Вдохновения (что можно сделать)
   - Best practices (как делать правильно)
   - Benchmarking (сравнение с другими)

ЗАЧЕМ ИЗУЧАТЬ:

1. Для буткэмпа:
   - Понять возможности GigaChat
   - Найти готовые решения
   - Избежать частых ошибок
   - Оптимизировать использование токенов

2. Для GrantService:
   - Улучшить качество генерации
   - Оптимизировать промпты
   - Использовать advanced features (streaming, embeddings)
   - Интеграция GigaChain для улучшения агентов

РЕКОМЕНДАЦИИ:

Критичное для изучения:
1. Authentication flow (как правильно получать токены)
2. /chat/completions parameters (temperature, max_tokens, etc.)
3. Error handling (что делать при 429 Too Many Requests)
4. Best practices для промптов

Полезное для улучшения:
1. GigaChain для multi-agent workflows
2. RAG для интеграции с Qdrant
3. Streaming для real-time ответов
4. Кейсы похожих продуктов

ИНТЕГРАЦИЯ С GRANTSERVICE:

Текущее состояние:
✓ UnifiedLLMClient уже использует /chat/completions
✓ Базовая авторизация реализована
✓ Rate limiting handling есть

Можно улучшить:
☐ Streaming responses (показывать текст по мере генерации)
☐ GigaChain integration (для сложных workflows)
☐ RAG с Qdrant (через GigaChain)
☐ Better error handling
☐ Token usage optimization
            """,
            "title": "Техническая документация GigaChat: Официальные ресурсы",
            "source": "portal",
            "category": "documentation",
            "section": "technical",
            "date_added": "2025-10-23",
            "urls": [
                "https://developers.sber.ru/docs/ru/gigachat/api/overview",
                "https://developers.sber.ru/docs/ru/gigachain/overview",
                "https://giga.chat/b2b/cases"
            ],
            "importance": "high"
        },
        {
            "text": """
Как тратить токены из ПАКЕТОВ для буткэмпа Sber500

ВОПРОС: Как начать тратить токены из пакетов, а не из подписки?

ЛОГИКА СПИСАНИЯ ТОКЕНОВ:

1. Сначала тратятся токены "По подписке"
2. Когда подписка заканчивается → начинают тратиться "По пакетам"

ТЕКУЩИЙ БАЛАНС (23 октября 2025):

GigaChat Max:
├─ По подписке: Закончились ✅
└─ По пакетам: 2,000,000 ← БУДУТ ТРАТИТЬСЯ СРАЗУ!

GigaChat Pro:
├─ По подписке: 50,000 ← Сначала эти
└─ По пакетам: 2,000,000 ← Потом эти

GigaChat Lite:
├─ По подписке: 739,055 ← Сначала эти
└─ По пакетам: 2,000,000 ← Потом эти

СТРАТЕГИЯ ДЛЯ БУТКЭМПА:

ВАРИАНТ А: Использовать ТОЛЬКО Max (РЕКОМЕНДУЕТСЯ!)

Причина:
✓ У Max подписка уже закончилась
✓ Сразу будут тратиться токены из ПАКЕТА (2M)
✓ Для буткэмпа важно показать использование пакетных токенов
✓ Max = самая мощная модель = лучшее качество

Настройка:
```python
# В agents/interactive_interviewer_agent_v2.py
LLM_MODEL = "GigaChat-Max"

# В shared/llm/unified_llm_client.py
self.model = "GigaChat-Max"
```

Ожидаемое использование:
- Interviewer: 10-15 вопросов × 100 интервью = 800k-1.2M токенов
- Writer: 50 заявок × 15-20k = 750k-1M токенов
- ИТОГО: ~2M токенов = весь пакет Max!

ВАРИАНТ Б: Смешанная стратегия (Максимум токенов)

Этап 1: Израсходовать подписки (739k Lite + 50k Pro = 789k)
Настройка: Использовать Lite для простых задач, Pro для сложных

Этап 2: Переключиться на Max (2M из пакета)
Настройка: Переключить на Max когда подписки кончатся

Этап 3: Продолжить с Lite и Pro пакетами (4M)
Настройка: После Max использовать Lite/Pro пакеты

ИТОГО: 6,789,055 токенов максимум!

ВАРИАНТ С: Параллельная стратегия (Быстро + Качество)

Распределение:
- Lite (подписка + пакет): Validation, simple Q&A, быстрые задачи
- Max (пакет): Основная генерация (Interviewer, Writer)
- Pro (подписка + пакет): Research, сложный анализ

Плюсы:
✓ Быстрое расходование токенов (параллельно)
✓ Оптимальное качество для каждой задачи
✓ Диверсификация (используем все модели)

РЕКОМЕНДАЦИЯ ДЛЯ GRANTSERVICE:

ШАГ 1: Переключить на Max (СЕЙЧАС!)
```bash
# В production:
ssh root@5.35.88.251
cd /var/GrantService

# Изменить настройку модели в коде
# agents/interactive_interviewer_agent_v2.py: model="GigaChat-Max"

# Restart service
systemctl restart grantservice-bot
```

ШАГ 2: Запустить intensive testing
- 50-100 интервью
- 30-50 грантовых заявок
- Target: 1-1.5M токенов за неделю

ШАГ 3: Мониторинг расхода
- Dashboard: https://developers.sber.ru/
- Проверять баланс ежедневно
- Корректировать стратегию

ШАГ 4: Отчётность
- Tracking использования токенов
- Screenshots dashboard
- Отправка в чат буткэмпа

ВАЖНО ДЛЯ ТОП50:

Комиссия оценивает:
✓ Объём использованных токенов из ПАКЕТОВ (для буткэмпа)
✓ Качество use case
✓ Бизнес-применимость

Поэтому:
- Использовать Max (пакет) = правильно
- Показывать real use case = правильно
- Документировать всё = правильно

TIMELINE:

Неделя 1 (сейчас):
- Переключиться на Max
- Intensive testing
- Target: 1M токенов Max

Неделя 2-3:
- Продолжить Max до конца (еще 1M)
- При необходимости: Lite/Pro подписки

Неделя 4 (перед оценкой):
- Финальный push
- Lite/Pro пакеты если нужно больше
- Подготовка отчётов

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:

Минимум: 2M токенов (весь пакет Max)
Оптимум: 4-5M токенов (Max + часть других)
Максимум: 6.7M токенов (всё!)

Для ТОП50 достаточно: 3-4M токенов
(В 6-8x больше чем средний участник)

НАСТРОЙКА В КОДЕ:

Файл: shared/llm/unified_llm_client.py
```python
# Было:
self.model = model  # может быть любая модель

# Стало (для буткэмпа):
self.model = "GigaChat-Max"  # форсируем Max для пакета
```

Файл: agents/interactive_interviewer_agent_v2.py
```python
# Было:
llm_provider = "gigachat"  # использует default модель

# Стало:
llm_provider = "gigachat"
model = "GigaChat-Max"  # явно указываем Max
```

ПРОВЕРКА ЧТО РАБОТАЕТ:

После переключения:
1. Запустить 1 интервью в Telegram
2. Проверить в dashboard (https://developers.sber.ru/)
3. Убедиться что токены списались с "Max" "По пакетам"
4. Если нет - скорректировать настройки
            """,
            "title": "Как тратить токены из ПАКЕТОВ для буткэмпа",
            "source": "internal",
            "category": "strategy",
            "section": "token_usage",
            "date_added": "2025-10-23",
            "importance": "critical",
            "action_required": "Switch to GigaChat-Max NOW"
        }
    ]

    # Add documents
    print(f"\n📝 Adding {len(documents)} technical documents...\n")

    for i, doc in enumerate(documents, 1):
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

        print(f"{i}. {importance_emoji} {doc['title']}")
        print(f"   Source: {doc['source']} | Category: {doc['category']}")
        if "action_required" in doc:
            print(f"   ⚠️  ACTION: {doc['action_required']}")
        print()

    print(f"✅ Documents added successfully!")

    # Get collection info
    collection_info = client.get_collection(collection_name="sber500_bootcamp")
    print(f"\n📊 Collection 'sber500_bootcamp' now has {collection_info.points_count} documents")

    # Print strategy
    print("\n" + "="*80)
    print("🎯 РЕКОМЕНДАЦИЯ: Переключиться на GigaChat-Max")
    print("="*80)
    print("ПОЧЕМУ:")
    print("  ✓ У Max подписка закончилась")
    print("  ✓ Токены будут тратиться из ПАКЕТА (2M)")
    print("  ✓ Для буткэмпа важно показать использование пакетов")
    print("  ✓ Max = лучшее качество")
    print("\nЧТО ДЕЛАТЬ:")
    print("  1. Изменить модель на 'GigaChat-Max' в коде")
    print("  2. Restart bot на production")
    print("  3. Запустить intensive testing (50-100 интервью)")
    print("  4. Мониторить расход в dashboard")
    print("\nTARGET:")
    print("  • Week 1: 1M токенов")
    print("  • Total: 2M токенов (весь пакет Max)")
    print("="*80)

if __name__ == "__main__":
    add_technical_docs()
