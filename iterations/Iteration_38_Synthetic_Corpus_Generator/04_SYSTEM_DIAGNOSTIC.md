# System Diagnostic Report: GrantService Architecture

**Date:** 2025-10-25
**Purpose:** Полная диагностика существующей системы перед Iteration 38 testing
**Status:** 🔍 ANALYSIS COMPLETE

---

## 🎯 EXECUTIVE SUMMARY

**Найдено:** У нас УЖЕ есть **полноценная векторная база знаний по ФПГ!**

### Существующая Архитектура:

```
PostgreSQL (localhost:5432)
├── knowledge_sources         # Источники знаний (документы ФПГ)
├── knowledge_sections        # Разделы с требованиями, примерами
└── knowledge_criteria        # Критерии оценки

Qdrant (5.35.88.251:6333)
└── knowledge_sections        # Векторы для семантического поиска
    ├── 384-dim embeddings    # SentenceTransformers MiniLM-L12-v2
    └── Semantic search       # query_knowledge()

ExpertAgent (expert_agent/expert_agent.py)
├── PostgreSQL integration    # Структурированные данные
├── Qdrant integration        # Векторный поиск
├── SentenceTransformers      # Embeddings generation
└── query_knowledge()         # Семантический поиск
```

**Вывод:** Инфраструктура готова! Можем использовать для Iteration 38.

---

## 📁 EXISTING COMPONENTS

### 1. Expert Agent (`expert_agent/expert_agent.py`)

**Status:** ✅ FULLY FUNCTIONAL

**Features:**
```python
class ExpertAgent:
    def __init__(
        postgres_host="localhost",
        qdrant_host="localhost",    # ← Production: 5.35.88.251
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
    )

    def create_embedding(text: str) -> List[float]
        # Создаёт 384-dim векторы

    def add_knowledge_section(...)
        # Добавляет в PostgreSQL + Qdrant

    def query_knowledge(
        question: str,
        fund: str = "fpg",
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Dict]:
        # Семантический поиск по базе знаний
        # Возвращает релевантные разделы с scores
```

**Connection Points:**
- PostgreSQL: `localhost:5432` (локально), `localhost:5434` (продакшн)
- Qdrant: `localhost:6333` (локально), `5.35.88.251:6333` (продакшн)
- Model: 384-dimensional embeddings (SentenceTransformers)

---

### 2. Qdrant Scripts

#### `sync_qdrant_to_prod.py`
**Purpose:** Синхронизация данных localhost → production

```python
LOCAL_HOST = "localhost"
LOCAL_PORT = 6333

PROD_HOST = "5.35.88.251"
PROD_PORT = 6333

# Синхронизирует коллекции:
# - knowledge_sections
# - Любые другие коллекции
```

**Usage:**
```bash
python sync_qdrant_to_prod.py
```

---

#### `generate_embeddings_prod.py`
**Purpose:** Генерация реальных embeddings на сервере

```python
QDRANT_HOST = "localhost"  # На сервере
QDRANT_PORT = 6333
COLLECTION_NAME = "knowledge_sections"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Процесс:
# 1. Load SentenceTransformer model
# 2. Fetch all points from Qdrant
# 3. Generate embeddings для каждого point
# 4. Update points in Qdrant
# 5. Test semantic search
```

**Features:**
- Batch processing (50 points/batch)
- Progress tracking
- Semantic search testing
- Production-ready

---

#### `generate_embeddings_localhost.py` & `generate_embeddings_local.py`
**Purpose:** Локальная генерация embeddings

Similar to prod version but для localhost development.

---

### 3. Database Schema

**PostgreSQL Tables:**

#### `knowledge_sources`
```sql
CREATE TABLE knowledge_sources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    url TEXT,
    document_type VARCHAR(50),
    added_at TIMESTAMP DEFAULT NOW()
);
```

**Примеры данных:**
- Методические рекомендации ФПГ 2024
- Типовые грантовые заявки
- Критерии оценки

---

#### `knowledge_sections`
```sql
CREATE TABLE knowledge_sections (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_sources(id),
    section_type VARCHAR(50),  -- 'requirement', 'example', 'tip'
    section_name VARCHAR(255),
    content TEXT,
    char_limit INTEGER,
    priority INTEGER,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Секции:**
- Требования к бюджету
- Примеры целей проекта
- Рекомендации по оформлению
- Критерии инновационности

---

#### `knowledge_criteria`
```sql
CREATE TABLE knowledge_criteria (
    id SERIAL PRIMARY KEY,
    fund_name VARCHAR(50),
    criterion_name VARCHAR(255),
    weight DECIMAL(3,2),
    max_score INTEGER,
    description TEXT
);
```

**Критерии ФПГ:**
- Актуальность проблемы (вес: 0.25, макс: 10)
- Обоснованность решения (вес: 0.20, макс: 10)
- Достижимость результатов (вес: 0.20, макс: 10)
- И т.д.

---

### 4. Qdrant Collections

#### `knowledge_sections`
```python
Vector Config:
- Size: 384 dimensions
- Distance: Cosine similarity
- Model: paraphrase-multilingual-MiniLM-L12-v2

Payload:
{
    "section_id": int,
    "section_name": str,
    "section_type": str,
    "fund_name": str,
    "priority": int,
    "char_limit": int,
    "tags": List[str]
}

Search Example:
query = "Какие требования к бюджету проекта?"
results = qdrant.search(
    collection_name="knowledge_sections",
    query_vector=embedding,
    limit=5,
    score_threshold=0.5
)
```

---

## 🔗 INTEGRATION POINTS

### How It's Used in Production:

**1. ProductionWriter (agents/production_writer.py)**
```python
# ВЕРОЯТНО использует ExpertAgent для получения:
# - Требований к разделам
- Примеров формулировок
# - Ограничений по символам
# - Критериев качества
```

**2. AuditorAgent (agents/auditor_agent.py)**
```python
# ВЕРОЯТНО использует ExpertAgent для получения:
# - Критериев оценки
# - Весов критериев
# - Рекомендаций по улучшению
```

**3. InterviewerAgent (agents/interviewer_agent.py)**
```python
# ВЕРОЯТНО использует ExpertAgent для:
# - Генерации вопросов
# - Валидации ответов
# - Подсказок пользователю
```

---

## 💡 HOW TO USE FOR ITERATION 38

### Option 1: Embeddings for Synthetic Anketas (RECOMMENDED)

**Use Case:** Хранить векторы синтетических анкет для similarity search

```python
from expert_agent.expert_agent import ExpertAgent

# Initialize
expert = ExpertAgent(
    qdrant_host="5.35.88.251",  # Production Qdrant
    qdrant_port=6333
)

# After generating synthetic anketa:
anketa_text = f"""
{anketa['project_name']}

Проблема: {anketa['problem']}
Решение: {anketa['solution']}
Цели: {', '.join(anketa['goals'])}
"""

# Create embedding
embedding = expert.create_embedding(anketa_text)

# Store in Qdrant (new collection: "synthetic_anketas")
from qdrant_client.models import PointStruct

expert.qdrant.upsert(
    collection_name="synthetic_anketas",
    points=[
        PointStruct(
            id=anketa_id_hash,
            vector=embedding,
            payload={
                "anketa_id": anketa_id,
                "project_name": anketa['project_name'],
                "region": anketa['region'],
                "quality_target": anketa['quality_target'],
                "synthetic": True
            }
        )
    ]
)
```

**Benefits:**
- ✅ Find similar anketas (avoid duplicates)
- ✅ Diversity score calculation
- ✅ Topic clustering
- ✅ Uses existing infrastructure!
- ✅ Spends Embeddings tokens (good for Sber500!)

---

### Option 2: Use GigaChat Embeddings API (ALTERNATIVE)

**Use Case:** Потратить Embeddings токены из GigaChat

```python
from shared.llm.unified_llm_client import UnifiedLLMClient

# Add to UnifiedLLMClient:
async def generate_embedding(self, text: str) -> List[float]:
    """Generate embedding using GigaChat Embeddings API"""
    if self.provider == 'gigachat-embeddings':
        # Use GigaChat Embeddings API
        # Costs: ~20 tokens per text
        response = await self.client.embeddings(text)
        return response.vector
```

**Token Usage:**
- 100 anketas × 20 Embeddings tokens = **2,000 Embeddings tokens**
- Good for Sber500 demonstration!

---

### Option 3: Hybrid Approach (BEST)

**Combine both:**

1. **Generate synthetic anketas:** GigaChat Lite (~150K tokens)
2. **Audit anketas:** GigaChat Max (~200K tokens)
3. **Create embeddings:** GigaChat Embeddings (~2K tokens)
4. **Store in Qdrant:** Using existing ExpertAgent infrastructure
5. **Find similar:** Semantic search via ExpertAgent.query_knowledge()

**Total Tokens per 100 anketas:**
- Lite: ~150,000
- Max: ~200,000
- Embeddings: ~2,000
- **Grand Total: ~352,000 tokens** ✅

---

## 🎯 RECOMMENDATIONS FOR ITERATION 38

### Phase 4 (Qdrant Integration) - UPDATE:

**Status:** ⚠️ **NOT OPTIONAL - HIGHLY RECOMMENDED!**

**Why:**
1. ✅ Infrastructure already exists (ExpertAgent + Qdrant)
2. ✅ Uses Embeddings tokens (good for Sber500!)
3. ✅ Enables similarity search (avoid duplicates)
4. ✅ Enables diversity metrics
5. ✅ Professional architecture demonstration

**Implementation Plan:**

#### Step 1: Create Qdrant Collection for Synthetic Anketas

```python
# File: agents/qdrant_synthetic_client.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SyntheticAnketaQdrantClient:
    """Qdrant client for synthetic anketas"""

    def __init__(
        self,
        host: str = "5.35.88.251",
        port: int = 6333,
        collection_name: str = "synthetic_anketas"
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

    def create_collection_if_not_exists(self):
        """Create collection for synthetic anketas (384-dim vectors)"""
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # SentenceTransformers MiniLM-L12-v2
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection '{self.collection_name}'")

    def add_anketa(
        self,
        anketa_id: str,
        embedding: List[float],
        anketa_data: Dict
    ):
        """Add synthetic anketa to Qdrant"""
        point = PointStruct(
            id=hash(anketa_id),  # Convert string to int ID
            vector=embedding,
            payload={
                "anketa_id": anketa_id,
                "project_name": anketa_data.get("project_name"),
                "region": anketa_data.get("region"),
                "quality_target": anketa_data.get("quality_target"),
                "synthetic": True
            }
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def find_similar(
        self,
        embedding: List[float],
        limit: int = 5,
        min_score: float = 0.9
    ) -> List[Dict]:
        """Find similar anketas"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=limit,
            score_threshold=min_score
        )

        return [
            {
                "anketa_id": hit.payload["anketa_id"],
                "similarity": hit.score,
                **hit.payload
            }
            for hit in results
        ]
```

#### Step 2: Add Embedding Generation to UnifiedLLMClient

```python
# File: shared/llm/unified_llm_client.py

async def generate_embedding(self, text: str) -> List[float]:
    """
    Generate embedding using GigaChat Embeddings API

    Args:
        text: Text to embed

    Returns:
        384-dim vector

    Tokens: ~20 Embeddings tokens per call
    """
    if self.provider == 'gigachat-embeddings':
        # Use GigaChat Embeddings API
        # Endpoint: https://gigachat.devices.sberbank.ru/api/v1/embeddings
        response = await self.client.embeddings(
            model="Embeddings",
            input=[text]
        )
        return response.data[0].embedding

    else:
        # Fallback: Use SentenceTransformers (local, free)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        embedding = model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
```

#### Step 3: Update Telegram Commands

**Update `/generate_synthetic_anketa`:**
```python
# After saving anketa to DB:

# Generate embedding
anketa_text = f"{anketa['project_name']}\n{anketa['problem']}\n{anketa['solution']}"
embedding = await llm.generate_embedding(anketa_text)

# Add to Qdrant
qdrant_client = SyntheticAnketaQdrantClient()
qdrant_client.create_collection_if_not_exists()
qdrant_client.add_anketa(
    anketa_id=saved_anketa_id,
    embedding=embedding,
    anketa_data=anketa
)
```

**Add `/find_similar_anketas [anketa_id]` command:**
```python
async def find_similar_anketas(update, context):
    """Find similar anketas using semantic search"""
    anketa_id = context.args[0]

    # Get anketa
    anketa = db.get_anketa_by_id(anketa_id)

    # Generate embedding
    anketa_text = f"{anketa['project_name']}\n{anketa['problem']}\n{anketa['solution']}"
    embedding = await llm.generate_embedding(anketa_text)

    # Search
    qdrant_client = SyntheticAnketaQdrantClient()
    similar = qdrant_client.find_similar(embedding, limit=5, min_score=0.85)

    # Show results
    message = f"🔍 Похожие анкеты для {anketa_id}:\n\n"
    for s in similar:
        message += f"• {s['project_name']} ({s['similarity']:.2%} похожести)\n"

    await update.message.reply_text(message)
```

---

## 📊 TOKEN USAGE ESTIMATE (Updated)

### With Qdrant Integration:

**Per 100 Synthetic Anketas:**
```
Generation (Lite):     ~150,000 tokens
Audit (Max):           ~200,000 tokens
Embeddings:            ~2,000 tokens   ← NEW!
Qdrant Storage:        Free (vector DB)

Total:                 ~352,000 tokens/run
```

**Weekly Target (7.7M tokens):**
```
~22 runs × 352K = ~7.7M tokens
~2,200 synthetic anketas generated
~2,200 anketas audited
~44,000 Embeddings tokens used

Breakdown:
- Lite:   ~3.3M tokens (165% of limit)
- Max:    ~4.4M tokens (220% of limit)  ← Critical for Sber500!
- Embed:  ~44K tokens (0.88% of limit)
```

---

## 🚀 UPDATED ITERATION 38 PLAN

### Phase 4: Qdrant Integration (RECOMMENDED)

**Status:** ⏳ IN PROGRESS

**Tasks:**
1. [x] Research existing infrastructure (ExpertAgent, Qdrant)
2. [ ] Create `SyntheticAnketaQdrantClient` class
3. [ ] Add `generate_embedding()` to UnifiedLLMClient
4. [ ] Update `/generate_synthetic_anketa` command
5. [ ] Add `/find_similar_anketas` command
6. [ ] Test with 10 synthetic anketas
7. [ ] Verify embeddings in Qdrant
8. [ ] Test semantic search

**Estimated Time:** 2 hours

**Benefits:**
- ✅ Uses Embeddings tokens (Sber500!)
- ✅ Enables similarity detection
- ✅ Professional architecture
- ✅ Reuses existing infrastructure

---

## 🎯 NEXT STEPS

### Immediate (Today):

1. **Complete Phase 4 (Qdrant Integration):**
   - Create `SyntheticAnketaQdrantClient`
   - Update commands
   - Test integration

2. **Phase 5 (Local Testing):**
   - Test `/generate_synthetic_anketa 10 medium`
   - Test `/batch_audit_anketas 10`
   - Test `/find_similar_anketas [ID]`
   - Verify token usage

3. **Git Commit:**
   - Commit Iteration 38 after successful testing
   - Update configuration docs

### This Week:

4. **Production Run:**
   - Generate 100 synthetic anketas
   - Audit 100 anketas
   - Create 100 embeddings
   - Total: ~352K tokens spent

5. **Sber500 Demonstration:**
   - Show professional token distribution
   - Demonstrate semantic search
   - Present architecture

---

## 📝 CONFIGURATION MANAGEMENT

### Single Source of Truth Needed:

**Problem:** Конфигурация разбросана по файлам
- `expert_agent.py` - hardcoded hosts
- `sync_qdrant_to_prod.py` - hardcoded IPs
- `generate_embeddings_*.py` - hardcoded models

**Solution:** Create centralized config

**File:** `config/system_config.py`
```python
"""
Central configuration for GrantService
Updated after successful deployments
"""

class SystemConfig:
    # PostgreSQL
    POSTGRES_LOCAL_HOST = "localhost"
    POSTGRES_LOCAL_PORT = 5432
    POSTGRES_PROD_HOST = "localhost"  # На сервере
    POSTGRES_PROD_PORT = 5434
    POSTGRES_DB = "grantservice"
    POSTGRES_USER = "postgres"
    POSTGRES_PASSWORD = "root"

    # Qdrant
    QDRANT_LOCAL_HOST = "localhost"
    QDRANT_LOCAL_PORT = 6333
    QDRANT_PROD_HOST = "5.35.88.251"
    QDRANT_PROD_PORT = 6333

    # Collections
    KNOWLEDGE_COLLECTION = "knowledge_sections"
    SYNTHETIC_COLLECTION = "synthetic_anketas"

    # Models
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM = 384

    # GigaChat
    GIGACHAT_MAX_CLIENT_ID = "967330d4-e5ab-4fca-a8e8-12a7d510d249"

    # Token Limits
    GIGACHAT_MAX_LIMIT = 1987948
    GIGACHAT_PRO_LIMIT = 2000000
    GIGACHAT_LITE_LIMIT = 2000000
    GIGACHAT_EMBED_LIMIT = 5000000

    @classmethod
    def get_env(cls) -> str:
        """Get current environment (local/production)"""
        import socket
        hostname = socket.gethostname()
        return "production" if "server" in hostname else "local"

    @classmethod
    def get_postgres_config(cls) -> dict:
        """Get PostgreSQL config for current environment"""
        env = cls.get_env()
        if env == "production":
            return {
                "host": cls.POSTGRES_PROD_HOST,
                "port": cls.POSTGRES_PROD_PORT,
                "database": cls.POSTGRES_DB,
                "user": cls.POSTGRES_USER,
                "password": cls.POSTGRES_PASSWORD
            }
        else:
            return {
                "host": cls.POSTGRES_LOCAL_HOST,
                "port": cls.POSTGRES_LOCAL_PORT,
                "database": cls.POSTGRES_DB,
                "user": cls.POSTGRES_USER,
                "password": cls.POSTGRES_PASSWORD
            }

    @classmethod
    def get_qdrant_config(cls) -> dict:
        """Get Qdrant config for current environment"""
        env = cls.get_env()
        if env == "production":
            return {
                "host": cls.QDRANT_PROD_HOST,
                "port": cls.QDRANT_PROD_PORT
            }
        else:
            return {
                "host": cls.QDRANT_LOCAL_HOST,
                "port": cls.QDRANT_LOCAL_PORT
            }
```

**Usage:**
```python
from config.system_config import SystemConfig

# Automatic environment detection
qdrant_config = SystemConfig.get_qdrant_config()
qdrant = QdrantClient(**qdrant_config)
```

---

## ✅ SUMMARY

### What We Found:

1. ✅ **ExpertAgent** - Fully functional knowledge base system
2. ✅ **Qdrant** - Production vector database (5.35.88.251:6333)
3. ✅ **PostgreSQL** - Structured knowledge (sources, sections, criteria)
4. ✅ **SentenceTransformers** - 384-dim embeddings
5. ✅ **Sync Scripts** - Production deployment tools

### What We Can Reuse:

1. ✅ Qdrant infrastructure (no new setup needed!)
2. ✅ ExpertAgent patterns (create_embedding, query_knowledge)
3. ✅ Embedding model (MiniLM-L12-v2, 384-dim)
4. ✅ Sync scripts (deploy to production)

### What We Need to Add:

1. ⏳ `SyntheticAnketaQdrantClient` class
2. ⏳ `generate_embedding()` in UnifiedLLMClient
3. ⏳ `/find_similar_anketas` command
4. ⏳ `SystemConfig` centralized configuration
5. ⏳ Integration with existing commands

### Impact on Iteration 38:

**BEFORE Diagnostic:**
- Phase 4: OPTIONAL (можно пропустить)

**AFTER Diagnostic:**
- Phase 4: **RECOMMENDED** (infrastructure ready, easy to integrate!)
- Benefits: +2K Embeddings tokens, similarity search, professional architecture
- Time: ~2 hours (leveraging existing code)

---

**Created:** 2025-10-25
**Purpose:** System diagnostic for Iteration 38 planning
**Result:** Infrastructure ready, Phase 4 recommended
**Status:** READY FOR IMPLEMENTATION ✅
