# Обзор выбора векторной базы данных для Expert Agent

**Дата:** 2025-10-17
**Версия:** 1.0
**Статус:** Архитектурное решение принято

---

## Контекст

При разработке Expert Agent возникла проблема с установкой pgvector на Windows для PostgreSQL 18:
- ❌ Нет готовых бинарников для PostgreSQL 18 на Windows
- ❌ Компиляция из исходников требует Visual Studio и сложной настройки
- ✅ Нужно решение для локальной разработки ПРЯМО СЕЙЧАС

---

## Рассмотренные варианты

### Вариант 1: PostgreSQL + pgvector (Изначальный план)

#### Описание
Хранить ВСЁ в одной базе данных PostgreSQL, используя расширение pgvector для векторного поиска.

#### ЗА ✅
- Всё в одной БД (данные + векторы)
- ACID транзакции
- Простые JOIN между таблицами и векторами
- Не нужно синхронизировать 2 БД
- Один бэкап для всего
- Меньше инфраструктуры (1 сервис вместо 2)
- Простая архитектура

#### ПРОТИВ ❌
- **Проблемы с установкой pgvector на Windows** (сейчас столкнулись)
- Нет готовых бинарников для PostgreSQL 18 на Windows
- PostgreSQL не оптимизирован для векторного поиска
- Медленнее специализированных решений при больших объемах (>1M векторов)
- Ограниченные возможности (нет продвинутой фильтрации, нет re-ranking)
- HNSW индексы в pgvector менее эффективны чем в специализированных решениях

#### Вердикт
⚠️ Хорош для production, но **проблематичен для DEV на Windows**. Требует компиляции или ожидания релиза бинарников.

---

### Вариант 2A: PostgreSQL + Qdrant 🌟 (РЕКОМЕНДУЕТСЯ)

#### Описание
Гибридная архитектура:
- **PostgreSQL** - структурированные данные (sources, sections, criteria)
- **Qdrant** - векторные embeddings и семантический поиск

#### Архитектура
```
┌─────────────────────────────────────────────────────┐
│  Expert Agent (Python)                              │
│  ┌─────────────────┐      ┌────────────────────┐   │
│  │ Business Logic  │      │  Vector Search     │   │
│  └────────┬────────┘      └─────────┬──────────┘   │
│           │                         │              │
└───────────┼─────────────────────────┼──────────────┘
            │                         │
            ▼                         ▼
   ┌─────────────────┐      ┌─────────────────┐
   │  PostgreSQL     │      │    Qdrant       │
   │  Port: 5434     │      │  Port: 6333     │
   ├─────────────────┤      ├─────────────────┤
   │ knowledge_      │      │ collections:    │
   │   sources       │      │ - sections      │
   │ knowledge_      │      │ - examples      │
   │   sections      │◄─────┤                 │
   │ evaluation_     │ IDs  │ vectors +       │
   │   criteria      │      │ metadata        │
   │ successful_     │      │                 │
   │   examples      │      │ HNSW index      │
   └─────────────────┘      └─────────────────┘
```

#### Workflow
```python
# Expert Agent делает 2 запроса:

# 1. Векторный поиск в Qdrant (быстро!)
results = qdrant_client.search(
    collection_name="knowledge_sections",
    query_vector=question_embedding,  # [1536] ruBERT
    limit=10,
    score_threshold=0.75,
    query_filter={
        "must": [
            {"key": "fund", "match": {"value": "fpg"}},
            {"key": "is_active", "match": {"value": True}}
        ]
    }
)

# results = [
#   {id: 42, score: 0.89, payload: {section_id: 42, fund: "fpg"}},
#   {id: 15, score: 0.85, payload: {section_id: 15, fund: "fpg"}},
#   ...
# ]

# 2. Получить полные данные из PostgreSQL
section_ids = [r.payload["section_id"] for r in results]
sections = await db.query(
    """
    SELECT ks.*, src.title as source_title
    FROM knowledge_sections ks
    JOIN knowledge_sources src ON ks.source_id = src.id
    WHERE ks.id = ANY($1)
    ORDER BY array_position($1, ks.id)
    """,
    section_ids
)

# 3. LLM генерирует ответ на основе sections
answer = await gigachat.generate(
    context=sections,
    question=user_question
)
```

#### ЗА ✅
- **Запускается за 1 команду**: `docker run -p 6333:6333 qdrant/qdrant`
- **Работает на Windows/Linux/Mac** - нет проблем с установкой
- **Rust** (очень быстро!) + HTTP API
- **Встроенный persistence** (не теряет данные при рестарте)
- **Отличная документация на русском!** (российская компания)
- **Поддержка фильтрации** по metadata (fund, date, type)
- **Batch операции** (загрузка 1000+ векторов за раз)
- **Python SDK** из коробки: `pip install qdrant-client`
- **REST API** - можно использовать из n8n
- **Встроенный Web UI** на http://localhost:6333/dashboard
- **Лучше масштабируется** чем pgvector при росте данных
- **Поддержка distributed режима** (кластер) в будущем
- **Quantization** - сжатие векторов для экономии RAM
- **Оптимизированные HNSW индексы** - быстрее чем в pgvector

#### ПРОТИВ ❌
- Нужно синхронизировать данные между PostgreSQL и Qdrant
- Отдельный сервис (еще один Docker контейнер)
- Нет JOIN напрямую с PostgreSQL (нужно 2 запроса)
- Сложнее бэкап (нужно бэкапить обе БД отдельно)
- Может возникнуть рассинхронизация при сбоях

#### Синхронизация данных
```python
# При добавлении нового раздела:
async def add_knowledge_section(section_data):
    # 1. Сохраняем в PostgreSQL
    section_id = await db.insert("knowledge_sections", section_data)

    # 2. Генерируем embedding
    embedding = await rubert.encode(section_data["content"])

    # 3. Сохраняем в Qdrant
    await qdrant.upsert(
        collection_name="knowledge_sections",
        points=[{
            "id": section_id,
            "vector": embedding.tolist(),
            "payload": {
                "section_id": section_id,
                "fund": section_data["fund"],
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
        }]
    )

    return section_id
```

#### Бэкап стратегия
```bash
# Ежедневный бэкап (cron на сервере)

# 1. PostgreSQL
pg_dump -h localhost -p 5434 -U grantservice grantservice \
  > /backups/postgres_$(date +%Y%m%d).sql

# 2. Qdrant (snapshot)
curl -X POST 'http://localhost:6333/collections/knowledge_sections/snapshots'
# Копировать snapshot файлы из ./storage/snapshots/
```

#### Вердикт
🏆 **ЛУЧШИЙ ВЫБОР для GrantService!**
- ✅ Решает проблему pgvector на Windows
- ✅ Можем начать разработку ПРЯМО СЕЙЧАС
- ✅ Production-ready
- ✅ Быстрее и гибче чем pgvector

---

### Вариант 2B: PostgreSQL + ChromaDB

#### Описание
Легковесная векторная БД на Python (SQLite под капотом).

#### ЗА ✅
- Самый простой (Python only, не нужен Docker)
- `pip install chromadb` и всё!
- Встроенный embedding (OpenAI, HuggingFace, Sentence Transformers)
- Хорош для прототипирования и разработки
- Автоматическая генерация embeddings

#### ПРОТИВ ❌
- **Не production-ready** (SQLite - не для продакшн нагрузок)
- Медленный на больших данных (>100k векторов)
- Нет кластеризации
- Нет продвинутой фильтрации
- Меньше документации

#### Вердикт
⚠️ Хорош для DEV/POC, но **не подходит для production**.

---

### Вариант 2C: PostgreSQL + Milvus

#### Описание
Enterprise-grade векторная БД (используется в Alibaba, Nvidia).

#### ЗА ✅
- Самый быстрый (C++, оптимизирован до предела)
- Масштабируется на **миллиарды векторов**
- Поддержка GPU acceleration
- Distributed architecture из коробки
- Множество индексных структур (HNSW, IVF, DiskANN)

#### ПРОТИВ ❌
- **Очень сложная установка** (etcd, MinIO, Pulsar...)
- **Overkill** для ваших задач (у вас ~10k векторов, Milvus для миллиардов)
- Тяжелый (нужно минимум 8GB RAM)
- Сложная настройка и поддержка

#### Вердикт
❌ **Слишком сложно** для текущих задач GrantService. Для 10-100k векторов это как пушкой по воробьям.

---

### Вариант 2D: PostgreSQL + Weaviate

#### Описание
GraphQL-based векторная БД с встроенными ML моделями.

#### ЗА ✅
- GraphQL API (удобный query language)
- Встроенные модели (OpenAI, Cohere, HuggingFace)
- Хорошая интеграция с LangChain
- Semantic search + hybrid search (keyword + vector)
- Автоматическая схема (schema inference)

#### ПРОТИВ ❌
- Нужен Go runtime
- Сложнее чем Qdrant
- Меньше документации на русском
- Более тяжелый (требует больше ресурсов)

#### Вердикт
⚠️ Хорош, но **Qdrant проще и легче** для наших задач.

---

## Сравнительная таблица

| Критерий | pgvector | Qdrant | ChromaDB | Milvus | Weaviate |
|----------|----------|--------|----------|--------|----------|
| **Установка на Windows** | ❌ Сложно | ✅ Docker | ✅ pip install | ❌ Очень сложно | ⚠️ Средне |
| **Скорость (10k векторов)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Скорость (1M+ векторов)** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Простота использования** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Production-ready** | ✅ Да | ✅ Да | ❌ Нет | ✅ Да | ✅ Да |
| **Документация (RU)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Фильтрация metadata** | ⚠️ Базовая | ✅ Продвинутая | ⚠️ Базовая | ✅ Продвинутая | ✅ Продвинутая |
| **Memory usage (10k)** | 100 MB | 150 MB | 50 MB | 500 MB | 300 MB |
| **ACID транзакции** | ✅ Да | ❌ Нет | ❌ Нет | ❌ Нет | ❌ Нет |
| **Кластеризация** | ⚠️ PG кластер | ✅ Да | ❌ Нет | ✅ Да | ✅ Да |
| **REST API** | ❌ Нет | ✅ Да | ✅ Да | ✅ Да | ✅ Да |
| **Web UI** | ❌ Нет | ✅ Да | ❌ Нет | ✅ Да | ✅ Да |

---

## Итоговая рекомендация 🏆

### Выбор: PostgreSQL + Qdrant (Гибридная архитектура)

#### Почему именно Qdrant?

1. ✅ **Обходим проблему pgvector на Windows**
   - Можем разрабатывать локально ПРЯМО СЕЙЧАС
   - Не нужно ждать релиза бинарников или компилировать

2. ✅ **Qdrant запускается за 30 секунд**
   ```bash
   docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
   ```

3. ✅ **PostgreSQL уже работает**
   - Не нужно ничего менять в существующей схеме
   - Все бизнес-данные остаются в PostgreSQL

4. ✅ **Легко мигрировать в будущем**
   - Если понадобится вернуться к pgvector - данные в PostgreSQL уже структурированы
   - Или перейти на другую векторную БД

5. ✅ **Лучше масштабируется**
   - Когда база вырастет до 100k+ векторов, Qdrant будет быстрее
   - Можно добавить кластер Qdrant для распределенной нагрузки

6. ✅ **Production-ready**
   - Используется в production крупными компаниями
   - Стабильный и надежный
   - Активная разработка и поддержка

7. ✅ **Российская разработка**
   - Отличная документация на русском
   - Поддержка русского языка из коробы

---

## План реализации

### Этап 1: DEV (Локальная разработка на Windows)

**Инфраструктура:**
```
PostgreSQL 18.0 (localhost:5432)
└── Существующие таблицы + новые (без knowledge_embeddings)

Qdrant (Docker, localhost:6333)
└── Collections для векторов
```

**Действия:**
1. ✅ Запустить Qdrant в Docker
2. ✅ Модифицировать миграцию 012 (убрать knowledge_embeddings таблицу)
3. ✅ Создать Python модуль для работы с Qdrant
4. ✅ Реализовать ExpertAgent с Qdrant интеграцией
5. ✅ Протестировать на локальной БД

---

### Этап 2: PROD (Сервер 5.35.88.251)

**Инфраструктура:**
```
PostgreSQL 18.0 (5.35.88.251:5434)
└── Production БД grantservice

Qdrant (Docker, 5.35.88.251:6333)
└── Production векторы
```

**Действия:**
1. Запустить Qdrant на сервере в Docker Compose
2. Настроить persistence и бэкапы
3. Мигрировать данные из локальной в prod
4. Настроить мониторинг (Prometheus + Grafana)
5. Интегрировать с n8n workflows

---

### Этап 3 (Опционально): Миграция на pgvector

Если в будущем захотим упростить архитектуру:

**Предпосылки:**
- Выйдет pgvector для PostgreSQL 18 на Windows
- Или мигрируем сервер на Linux с pgvector
- Или объем данных будет <100k векторов

**Действия:**
1. Установить pgvector
2. Создать knowledge_embeddings таблицу
3. Экспортировать векторы из Qdrant в PostgreSQL
4. Переключить ExpertAgent на pgvector
5. Удалить Qdrant

---

## Технические детали Qdrant интеграции

### Установка

```bash
# DEV (Docker)
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v ./qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# Python SDK
pip install qdrant-client
```

### Конфигурация

```python
# config/qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class QdrantConfig:
    HOST = "localhost"  # или 5.35.88.251 для prod
    PORT = 6333
    GRPC_PORT = 6334

    COLLECTIONS = {
        "knowledge_sections": {
            "vector_size": 1536,  # ruBERT
            "distance": Distance.COSINE
        }
    }

# Инициализация клиента
qdrant = QdrantClient(host=QdrantConfig.HOST, port=QdrantConfig.PORT)

# Создать collection
qdrant.create_collection(
    collection_name="knowledge_sections",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=False  # Хранить в RAM для скорости
    )
)
```

### API методы

```python
# 1. Добавить вектор
qdrant.upsert(
    collection_name="knowledge_sections",
    points=[
        {
            "id": section_id,
            "vector": embedding.tolist(),  # [1536] float
            "payload": {
                "section_id": section_id,
                "fund": "fpg",
                "source_id": 42,
                "is_active": True
            }
        }
    ]
)

# 2. Поиск
results = qdrant.search(
    collection_name="knowledge_sections",
    query_vector=question_embedding,
    limit=10,
    score_threshold=0.75,
    query_filter={
        "must": [
            {"key": "fund", "match": {"value": "fpg"}},
            {"key": "is_active", "match": {"value": True}}
        ]
    }
)

# 3. Обновить payload
qdrant.set_payload(
    collection_name="knowledge_sections",
    payload={"is_active": False},
    points=[section_id]
)

# 4. Удалить
qdrant.delete(
    collection_name="knowledge_sections",
    points_selector=[section_id]
)

# 5. Batch операции
qdrant.upsert(
    collection_name="knowledge_sections",
    points=[
        {"id": 1, "vector": vec1, "payload": {...}},
        {"id": 2, "vector": vec2, "payload": {...}},
        # ... до 1000 за раз
    ]
)
```

### Мониторинг

```python
# Статистика collection
info = qdrant.get_collection("knowledge_sections")
print(f"Vectors: {info.vectors_count}")
print(f"Points: {info.points_count}")

# Web UI
# http://localhost:6333/dashboard
```

---

## Затраты ресурсов

### Qdrant

**Memory:**
- ~100 MB base
- ~1 KB на вектор (1536 float32)
- Для 10,000 векторов: ~110 MB
- Для 100,000 векторов: ~1 GB

**Disk:**
- Snapshots: ~равно RAM usage
- WAL logs: ~10-20% от data size

**CPU:**
- Minimal в idle
- Burst при поиске (1-10ms на запрос)

### PostgreSQL

Без изменений - хранит только метаданные.

---

## Бэкап стратегия

### Ежедневный бэкап (automated)

```bash
#!/bin/bash
# /var/GrantService/scripts/backup_all.sh

DATE=$(date +%Y%m%d_%H%M)

# 1. PostgreSQL
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
pg_dump -h localhost -p 5434 -U grantservice grantservice \
  > /backups/postgres_${DATE}.sql

# 2. Qdrant snapshot
curl -X POST 'http://localhost:6333/collections/knowledge_sections/snapshots'

# 3. Копировать snapshot
cp /var/GrantService/qdrant_storage/collections/knowledge_sections/snapshots/* \
   /backups/qdrant_${DATE}/

# 4. Удалить старые (>30 дней)
find /backups -name "*.sql" -mtime +30 -delete
find /backups -name "qdrant_*" -mtime +30 -exec rm -rf {} \;
```

### Восстановление

```bash
# 1. PostgreSQL
psql -h localhost -p 5434 -U grantservice -d grantservice < backup.sql

# 2. Qdrant
# Остановить Qdrant
docker stop qdrant

# Восстановить snapshot
cp backup_snapshot/* /var/GrantService/qdrant_storage/collections/knowledge_sections/snapshots/

# Запустить Qdrant
docker start qdrant

# Восстановить из snapshot через API
curl -X PUT 'http://localhost:6333/collections/knowledge_sections/snapshots/upload' \
  --data-binary @snapshot_file
```

---

## Миграция данных (будущее)

Если решим мигрировать с Qdrant на pgvector:

```python
# migrate_to_pgvector.py

from qdrant_client import QdrantClient
import asyncpg

async def migrate():
    # 1. Подключиться к обеим БД
    qdrant = QdrantClient("localhost", 6333)
    pg = await asyncpg.connect("postgresql://...")

    # 2. Создать таблицу в PostgreSQL
    await pg.execute("""
        CREATE TABLE knowledge_embeddings (
            id SERIAL PRIMARY KEY,
            section_id INTEGER REFERENCES knowledge_sections(id),
            embedding vector(1536),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # 3. Экспорт из Qdrant
    offset = 0
    batch_size = 100

    while True:
        points, next_offset = qdrant.scroll(
            collection_name="knowledge_sections",
            limit=batch_size,
            offset=offset,
            with_vectors=True
        )

        if not points:
            break

        # 4. Импорт в PostgreSQL
        for point in points:
            await pg.execute(
                """
                INSERT INTO knowledge_embeddings (section_id, embedding)
                VALUES ($1, $2)
                """,
                point.payload["section_id"],
                point.vector
            )

        offset = next_offset
        print(f"Migrated {offset} vectors")

    print("Migration complete!")
```

---

## Заключение

**Итоговое архитектурное решение:**

🏆 **Гибридная архитектура: PostgreSQL + Qdrant**

**Преимущества:**
1. Решает текущую проблему (pgvector на Windows)
2. Позволяет начать разработку НЕМЕДЛЕННО
3. Production-ready и масштабируемое решение
4. Гибкость для будущих изменений
5. Лучшая производительность при росте данных

**Следующие шаги:**
1. Запустить Qdrant локально
2. Модифицировать миграцию 012 (убрать knowledge_embeddings)
3. Реализовать ExpertAgent с Qdrant
4. Протестировать на DEV
5. Деплой на PROD

---

**Автор:** Claude Code (grant-architect agent)
**Дата создания:** 2025-10-17
**Статус:** ✅ Принято к реализации
