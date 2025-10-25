#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавить документы о Sber500 Bootcamp в Qdrant

Назначение: Загрузка информации из писем, портала, и других источников
для быстрого semantic search

Usage:
    python add_bootcamp_docs.py
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime

def add_documents():
    """Добавить документы в коллекцию sber500_bootcamp"""

    # Initialize
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(host="5.35.88.251", port=6333)

    print("🤖 Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Documents to add
    documents = [
        # ===== EMAIL INFORMATION =====
        {
            "text": """
Письмо: Добро пожаловать в Sber500 x GigaChat Bootcamp

Для вас создана учётная запись на сайте Sber500 x GigaChat Bootcamp — онлайн-платформе,
где собраны все материалы и инструменты программы.

Доступ:
- Логин: otinoff@gmail.com
- Пароль: Одноразовый код
- Страница входа: http://sber500.2080vc.io/members/login

Что доступно:
- Учебные материалы от Sber500 и GigaChat
- Подробная инструкция о том, как подготовить и сдать свой бизнес-кейс
- Telegram-группа для общения с другими участниками

Цель программы:
Усовершенствовать продукт с помощью GigaChat и продемонстрировать результаты.

Дедлайн: 27 сентября
Команды, показавшие результат до 27 сентября, получат возможность представить
свой продукт на сцене Moscow Startup Summit.
            """,
            "title": "Письмо: Доступ к платформе Sber500 x GigaChat Bootcamp",
            "source": "email",
            "category": "access",
            "section": "intro",
            "date_added": "2025-10-23",
            "url": "http://sber500.2080vc.io",
            "importance": "high"
        },

        # ===== PARTNER REQUIREMENTS =====
        {
            "text": """
Задачи от партнёра (Наталья Брызгина):

1. Промониторить победившие проекты Сбер500 прошлый год
   - Какие проекты победили?
   - Что у них было хорошего?
   - Какие паттерны успешных заявок?

2. Сделать прогоны заявок используя токены GigaChat
   - Создать несколько полных заявок через систему
   - Активно использовать GigaChat (все агенты)
   - Показать количество использованных токенов

3. Отправить заявки в чат буткэмпа
   - Демонстрация работы системы
   - Показать результаты использования GigaChat

Критерий оценки (через неделю):
- Количество использованных токенов GigaChat
- Для каких целей используются токены
- Качество использования и результаты

Цель:
Показать СБеру активное и эффективное использование GigaChat для прохождения
в следующий этап буткэмпа.
            """,
            "title": "Задачи от партнёра: Критерии оценки через неделю",
            "source": "partner",
            "category": "requirements",
            "section": "tasks",
            "date_added": "2025-10-23",
            "importance": "critical",
            "deadline": "2025-10-30"
        },

        # ===== PORTAL STRUCTURE =====
        {
            "text": """
Структура портала Sber500 x GigaChat Bootcamp:

Раздел 1: О программе Sber500xGigaChat
  1.1 О Буткемпе
  1.2 Как сдать свой бизнес-кейс с GigaChat?

Раздел 2: Курсы от GigaChat
  2.1 Интро от команды GigaChat
  2.2 Курсы по GigaChat
  2.3 Техническая документация GigaChat

Раздел 3: Бизнес-воркшопы
  3.1 Описание воркшопов
  3.2 Воркшоп № 1 Jobs-To-Be-Done
  3.3 Воркшоп №2 Value Proposition
  3.4 Воркшоп № 3 Гипотезы и приоритезация
  3.5 Воркшоп № 4 Инженирия в AI стартапах
  3.6 Воркшоп № 5 Growth Hacking
  3.7 Воркшоп № 6 Метрики AI-продуктов
  3.8 Воркшоп № 7 Монетизация AI-функций
  3.9 Воркшоп №8 Pricing
  3.10 Воркшоп № 9 Продуктовые демо

Раздел 4: Live Sessions
  4.1 Live Sessions — coming soon!
  4.2 Открытая дискуссия: AI в бизнесе: влияние и применение (Язык — английский)

Общая цель программы:
Усовершенствовать продукт с помощью GigaChat и представить результаты.

Финальное событие:
Moscow Startup Summit - возможность выступить на сцене для команд,
показавших лучший результат.
            """,
            "title": "Структура онлайн-платформы буткэмпа",
            "source": "portal",
            "category": "structure",
            "section": "overview",
            "date_added": "2025-10-23",
            "url": "http://sber500.2080vc.io",
            "importance": "high"
        },

        # ===== SECTION 1: ABOUT =====
        {
            "text": """
Раздел 1: О программе Sber500xGigaChat

1.1 О Буткемпе
Программа направлена на усовершенствование продуктов с помощью технологии GigaChat.
Участники получают доступ к обучающим материалам, воркшопам и live-сессиям.

1.2 Как сдать свой бизнес-кейс с GigaChat?
Инструкция по подготовке и сдаче бизнес-кейса, демонстрирующего
использование GigaChat в продукте.

Ключевые элементы:
- Интеграция GigaChat в продукт
- Демонстрация результатов
- Метрики использования
- Бизнес-эффект

Дедлайн: 27 сентября
Лучшие команды выступят на Moscow Startup Summit.
            """,
            "title": "О программе и требования к бизнес-кейсу",
            "source": "portal",
            "category": "requirements",
            "section": "section1",
            "date_added": "2025-10-23",
            "importance": "critical"
        },

        # ===== SECTION 2: GIGACHAT COURSES =====
        {
            "text": """
Раздел 2: Курсы от GigaChat

2.1 Интро от команды GigaChat
Введение в возможности GigaChat для бизнес-приложений.

2.2 Курсы по GigaChat
Обучающие материалы по работе с GigaChat API:
- Основы работы с API
- Best practices интеграции
- Оптимизация запросов
- Работа с токенами

2.3 Техническая документация GigaChat
Полная техническая документация:
- API Reference
- Примеры кода
- Troubleshooting
- FAQ

Цель: Научить участников эффективно использовать GigaChat в своих продуктах.
            """,
            "title": "Курсы и техническая документация GigaChat",
            "source": "portal",
            "category": "education",
            "section": "section2",
            "date_added": "2025-10-23",
            "importance": "high"
        },

        # ===== SECTION 3: WORKSHOPS =====
        {
            "text": """
Раздел 3: Бизнес-воркшопы (9 воркшопов)

3.1 Описание воркшопов
Серия практических воркшопов по ключевым аспектам AI-стартапов.

3.2 Воркшоп № 1: Jobs-To-Be-Done
Методология понимания потребностей пользователей.
Ключевой вопрос: Какую работу выполняет ваш продукт для пользователя?

3.3 Воркшоп № 2: Value Proposition
Формулировка ценностного предложения.
Как донести ценность AI-функций до клиентов?

3.4 Воркшоп № 3: Гипотезы и приоритизация
Формирование и приоритизация гипотез развития продукта.
Какие функции важнее всего для пользователей?

3.5 Воркшоп № 4: Инженирия в AI стартапах
Технические аспекты построения AI-продуктов.
Best practices разработки и масштабирования.

3.6 Воркшоп № 5: Growth Hacking
Стратегии быстрого роста AI-продуктов.
Как привлечь первых пользователей и масштабироваться?

3.7 Воркшоп № 6: Метрики AI-продуктов
Ключевые метрики для оценки успеха AI-функций.
- Технические метрики (latency, quality, cost)
- Бизнес-метрики (conversion, retention, revenue)

3.8 Воркшоп № 7: Монетизация AI-функций
Модели монетизации AI-возможностей.
Как зарабатывать на AI?

3.9 Воркшоп № 8: Pricing
Ценообразование для AI-продуктов.
Token-based vs subscription vs usage-based pricing.

3.10 Воркшоп № 9: Продуктовые демо
Как эффективно демонстрировать AI-продукт.
Подготовка презентации для инвесторов и партнёров.

Цель воркшопов:
Дать участникам практические инструменты для развития AI-стартапов.
            """,
            "title": "Бизнес-воркшопы: 9 практических сессий",
            "source": "portal",
            "category": "workshops",
            "section": "section3",
            "date_added": "2025-10-23",
            "importance": "high"
        },

        # ===== SECTION 4: LIVE SESSIONS =====
        {
            "text": """
Раздел 4: Live Sessions

4.1 Live Sessions — coming soon!
Запланированы live-сессии с экспертами и успешными AI-стартапами.
Формат: Q&A, разборы кейсов, networking.

4.2 Открытая дискуссия: AI в бизнесе: влияние и применение
Язык: английский
Тема: Влияние AI на различные индустрии и примеры успешного применения.

Участники:
- Представители Sber500
- Команда GigaChat
- Эксперты из AI-индустрии
- Успешные стартапы

Цель: Обмен опытом и networking между участниками программы.
            """,
            "title": "Live Sessions: общение с экспертами",
            "source": "portal",
            "category": "events",
            "section": "section4",
            "date_added": "2025-10-23",
            "importance": "medium"
        },

        # ===== GRANTSERVICE PROJECT INFO =====
        {
            "text": """
Проект GrantService для Sber500 Bootcamp

Описание продукта:
AI-powered платформа для автоматической подготовки грантовых заявок
с использованием GigaChat.

Использование GigaChat:
1. Interactive Interviewer V2 (основной агент)
   - Адаптивные вопросы для сбора информации о проекте
   - 13 обязательных полей анкеты ФПГ
   - Естественный диалог через Telegram

2. Writer Agent
   - Генерация 9 разделов грантовой заявки
   - 15,000-20,000 символов текста
   - Интеграция с research данными

3. Researcher Agent
   - Анализ контекста проекта
   - Поиск статистики и кейсов
   - Подбор партнёров

4. Reviewer Agent
   - Оценка готовности заявки
   - Вероятность одобрения
   - Рекомендации по улучшению

Текущий статус:
- Version 1.0 deployed (5.35.88.251)
- Telegram bot: @grant_service_bot
- Production ready

План для буткэмпа:
1. Переключить всех users на GigaChat
2. Создать tracking использования токенов
3. Провести 20-30 тестовых интервью
4. Создать 10-15 полных заявок
5. Сгенерировать отчёты для комиссии

Ожидаемые метрики:
- 50,000-100,000 токенов за неделю
- 4 агента задействовано
- 10-20 грантовых заявок создано
            """,
            "title": "GrantService: план использования GigaChat для буткэмпа",
            "source": "internal",
            "category": "strategy",
            "section": "grantservice",
            "date_added": "2025-10-23",
            "importance": "critical"
        },
    ]

    # Add documents
    print(f"\n📝 Adding {len(documents)} documents...\n")

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
        if "deadline" in doc:
            print(f"   ⏰ Deadline: {doc['deadline']}")
        print()

    print(f"✅ Total documents added: {len(documents)}")

    # Get collection info
    collection_info = client.get_collection(collection_name="sber500_bootcamp")
    print(f"\n📊 Collection 'sber500_bootcamp' now has {collection_info.points_count} documents")

if __name__ == "__main__":
    add_documents()
