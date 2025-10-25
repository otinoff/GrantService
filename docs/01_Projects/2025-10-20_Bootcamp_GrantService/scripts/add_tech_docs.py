#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавить техническую документацию GrantService в Qdrant
Пароли, API keys, команды, структура
"""

import sys
from pathlib import Path
import uuid

# Пути
project_root = Path(__file__).parent.parent.parent.parent.parent / "GrantService"
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

def add_tech_docs():
    """Добавить технические документы"""

    # Initialize
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(host="5.35.88.251", port=6333)

    print("🤖 Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Документы
    documents = [
        # ===== POSTGRESQL =====
        {
            "text": """
PostgreSQL Database - GrantService

PRODUCTION (5.35.88.251):
Host: 5.35.88.251
Port: 5434
Database: grantservice
User: grantservice
Password: jPsGn%Nt%q#THnUB&&cqo*1Q

Подключение:
psql -h 5.35.88.251 -p 5434 -U grantservice -d grantservice

Environment variables:
export PGHOST=5.35.88.251
export PGPORT=5434
export PGDATABASE=grantservice
export PGUSER=grantservice
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'

Python:
import psycopg2
conn = psycopg2.connect(
    host='5.35.88.251',
    port=5434,
    database='grantservice',
    user='grantservice',
    password='jPsGn%Nt%q#THnUB&&cqo*1Q'
)

ЛОКАЛЬНО (Windows):
PostgreSQL 18.0
Path: C:\\Program Files\\PostgreSQL\\18
psql: C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe
            """,
            "title": "PostgreSQL - Доступы и пароли",
            "category": "database",
            "importance": "critical",
            "tags": ["postgresql", "database", "password", "credentials"]
        },

        # ===== API KEYS =====
        {
            "text": """
API Keys - GrantService

GIGACHAT (Сбер):
API Key: OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5Ojk4MmM0NjIyLTU3OWQtNDYxNi04YzVlLWIyMTY3YTZlNzI0NQ==
Model: GigaChat-Max (для буткэмпа)
Токены доступны: 2,000,000 (из пакета)
Dashboard: https://developers.sber.ru/

Environment:
export GIGACHAT_API_KEY="OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5Ojk4MmM0NjIyLTU3OWQtNDYxNi04YzVlLWIyMTY3YTZlNzI0NQ=="

PERPLEXITY (WebSearch):
API Key: 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
Usage: Researcher Agent (27 запросов)

Environment:
export PERPLEXITY_API_KEY="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"

TELEGRAM BOT:
Token: 7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo
            """,
            "title": "API Keys - GigaChat, Perplexity, Telegram",
            "category": "credentials",
            "importance": "critical",
            "tags": ["api", "keys", "gigachat", "perplexity", "telegram"]
        },

        # ===== КОМАНДЫ ЗАПУСКА =====
        {
            "text": """
Команды запуска - GrantService

PRODUCTION (5.35.88.251):

SSH подключение:
ssh -i "C:\\Users\\Андрей\\.ssh\\id_rsa" root@5.35.88.251

Telegram Bot:
systemctl status grantservice-bot
systemctl restart grantservice-bot
systemctl stop grantservice-bot
systemctl start grantservice-bot

Логи:
journalctl -u grantservice-bot -f
tail -f /var/GrantService/logs/bot.log

Web Admin:
systemctl status grantservice-admin
cd /var/GrantService/web-admin
streamlit run main_admin.py

Проверка процессов:
ps aux | grep python
ps aux | grep grantservice

ЛОКАЛЬНО (Windows):

Telegram Bot:
cd C:\\SnowWhiteAI\\GrantService\\telegram-bot
python main.py

Web Admin:
cd C:\\SnowWhiteAI\\GrantService\\web-admin
streamlit run main_admin.py

E2E Test:
cd C:\\SnowWhiteAI\\GrantService_Project\\01_Projects\\2025-10-20_Bootcamp_GrantService\\scripts
python run_e2e_local_windows.py
            """,
            "title": "Команды запуска - Production и Local",
            "category": "commands",
            "importance": "high",
            "tags": ["commands", "systemctl", "ssh", "bot", "admin"]
        },

        # ===== СТРУКТУРА ПРОЕКТА =====
        {
            "text": """
Структура проекта - GrantService

PRODUCTION (/var/GrantService):
/var/GrantService/
├── agents/
│   ├── researcher_agent_v2.py      ← 27 экспертных запросов
│   ├── writer_agent_v2.py          ← Генерация через GigaChat
│   ├── interactive_interviewer_agent_v2.py
│   └── auditor_agent_v2.py
├── telegram-bot/
│   ├── main.py                     ← Telegram bot entry point
│   └── handlers/
├── web-admin/
│   ├── main_admin.py               ← Streamlit admin panel
│   └── pages/
├── shared/
│   ├── llm/                        ← UnifiedLLMClient
│   └── database/                   ← DB utils
├── data/
│   └── database/                   ← Database models
├── config/
│   └── .env                        ← Environment variables
└── tests/
    ├── run_e2e_simple.py           ← E2E тест
    └── run_e2e_with_env.sh

ЛОКАЛЬНО (C:\\SnowWhiteAI\\GrantService):
Такая же структура + дополнительные dev файлы

ПРОЕКТ БУТКЭМПА:
C:\\SnowWhiteAI\\GrantService_Project\\01_Projects\\2025-10-20_Bootcamp_GrantService/
├── test_data/
│   └── natalia_anketa_20251012.json
├── scripts/
│   ├── run_e2e_local_windows.py
│   ├── search_bootcamp.py
│   └── add_tech_docs.py             ← Этот скрипт
├── test_results/
└── .env.local
            """,
            "title": "Структура проекта - Файлы и директории",
            "category": "structure",
            "importance": "high",
            "tags": ["structure", "files", "directories", "project"]
        },

        # ===== QDRANT =====
        {
            "text": """
Qdrant Vector Database - GrantService

SERVER:
Host: 5.35.88.251
Port: 6333
Web UI: http://5.35.88.251:6333/dashboard

КОЛЛЕКЦИИ:

1. sber500_bootcamp (15 документов)
   - Информация о буткэмпе
   - Баланс токенов
   - Стратегия ТОП50
   - Техническая документация

2. grantservice_tech_docs (новая)
   - Пароли и доступы
   - API keys
   - Команды запуска
   - Структура проекта

Python подключение:
from qdrant_client import QdrantClient
client = QdrantClient(host="5.35.88.251", port=6333)

Поиск по буткэмпу:
python scripts/search_bootcamp.py "токены gigachat"

Добавление документов:
python scripts/add_tech_docs.py
            """,
            "title": "Qdrant - Векторная база данных",
            "category": "qdrant",
            "importance": "high",
            "tags": ["qdrant", "vector", "database", "search"]
        },

        # ===== ИТЕРАЦИИ =====
        {
            "text": """
Итерации проекта - GrantService

ТЕКУЩАЯ: Итерация 27
Status: В процессе
Задача: E2E тест с GigaChat-Max для буткэмпа

СЛЕДУЮЩАЯ: Итерация 28
Планируется после успешного E2E теста

ПОСЛЕДНИЕ ЗАВЕРШЕННЫЕ:

Iteration 26.3 (2025-10-23):
- Instant Interview Start
- Performance: -99% latency
- User feedback: "супер мега!!!"
- Deploy 5 на production

Iteration 26 (2025-10-20):
- Interview V2 improvements
- UX enhancements

Iteration 25 (2025-10-15):
- Researcher Agent V2
- 27 экспертных запросов

ИСТОРИЯ:
.claude/README.md                    ← Список всех итераций
Strategy/02_Completed_Iterations/    ← Архив
Strategy/03_Planned_Sessions/        ← Backlog (1000+)
            """,
            "title": "Итерации проекта - История и планы",
            "category": "iterations",
            "importance": "medium",
            "tags": ["iterations", "history", "planning", "versions"]
        },

        # ===== БУТКЭМП SBER500 =====
        {
            "text": """
Sber500 Bootcamp - Ключевая информация

TARGET: Попасть в ТОП50

ТОКЕНЫ:
- Доступно: 6,000,000 (GigaChat)
- Модель: GigaChat-Max (2M из пакета)
- Target для недели: 1,000,000
- Одна заявка: ~18,500 токенов
- Нужно: ~54 заявки

DEADLINE: 2025-10-30 (через неделю!)

КРИТЕРИИ ОТБОРА:
1. Объём использованных токенов
2. Зрелость кейса
3. Качество интеграции
4. Бизнес-применимость

ПРЕИМУЩЕСТВА:
✓ Real use case (production bot)
✓ Multi-agent (4 агента)
✓ High consumption (50-80k на заявку)
✓ Social impact
✓ Scalability

ПЛАН:
Week 1: 1M токенов (intensive testing)
Week 2-3: 2M токенов (scale)
Week 4: 1M токенов (quality demos)

ПОРТАЛ: https://sber500.2080vc.io
LOGIN: otinoff@gmail.com

ДОКУМЕНТАЦИЯ В QDRANT:
Коллекция: sber500_bootcamp
Поиск: python scripts/search_bootcamp.py
            """,
            "title": "Sber500 Bootcamp - Стратегия и цели",
            "category": "bootcamp",
            "importance": "critical",
            "tags": ["bootcamp", "sber500", "gigachat", "strategy", "top50"]
        }
    ]

    # Добавить документы
    print(f"\n📝 Добавление {len(documents)} технических документов...\n")

    for i, doc in enumerate(documents, 1):
        # Generate embedding
        embedding = model.encode(doc["text"]).tolist()

        # Upload to Qdrant
        client.upsert(
            collection_name="grantservice_tech_docs",
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
        print(f"   Category: {doc['category']} | Tags: {', '.join(doc.get('tags', []))}")
        print()

    print(f"✅ Документы добавлены!")

    # Get collection info
    collection_info = client.get_collection(collection_name="grantservice_tech_docs")
    print(f"\n📊 Коллекция 'grantservice_tech_docs' содержит {collection_info.points_count} документов")

    # Примеры поиска
    print("\n" + "="*80)
    print("🔍 ПРИМЕРЫ ПОИСКА")
    print("="*80)
    print("python search_tech_docs.py 'пароль базы данных'")
    print("python search_tech_docs.py 'api key gigachat'")
    print("python search_tech_docs.py 'как запустить бота'")
    print("python search_tech_docs.py 'postgresql подключение'")
    print("python search_tech_docs.py 'буткэмп deadline'")
    print("="*80)

if __name__ == "__main__":
    add_tech_docs()
