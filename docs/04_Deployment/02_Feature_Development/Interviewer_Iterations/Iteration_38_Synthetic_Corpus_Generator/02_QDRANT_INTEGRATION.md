# Qdrant Integration для Iteration 38

**Date:** 2025-10-25
**Objective:** Использовать Qdrant + GigaChat Embeddings для поиска похожих анкет
**Impact:** Тратим Embeddings токены + улучшаем качество корпуса

---

## 🎯 ЗАЧЕМ НУЖЕН QDRANT

### 1. Тратим Embeddings токены для Sber500
```
У нас: 5,000,000 токенов Embeddings
Используем: ~100K токенов за неделю
Показываем: Активное использование всех типов токенов
```

### 2. Поиск дубликатов и похожих
```
После генерации 100 анкет:
→ Vectorize каждую через GigaChat Embeddings
→ Сохранить в Qdrant
→ Найти похожие (similarity > 0.8)
→ Удалить почти дубликаты
```

### 3. Quality control
```
Проверка разнообразия:
- Если много похожих → генератор повторяется
- Если все разные → хорошее разнообразие
- Metric: Avg similarity < 0.7 (хорошо)
```

### 4. Recommendation engine
```
При создании реальной анкеты:
→ Найти 5 похожих из корпуса
→ Показать примеры пользователю
→ "Вот похожие успешные проекты"
```

---

## 🔧 АРХИТЕКТУРА

### Компоненты:

```
┌─────────────────────────────────────────────────────────┐
│  ПОТОК ДАННЫХ                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Synthetic Anketa (JSON)                            │
│      ↓                                                  │
│  2. GigaChat Embeddings API                            │
│      ↓ (vectorize)                                     │
│  3. Vector (384 dimensions)                            │
│      ↓                                                  │
│  4. Qdrant (5.35.88.251:6333)                         │
│      ↓ (store)                                         │
│  5. Search похожих                                     │
│      ↓                                                  │
│  6. Results (top 5 similar)                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Qdrant Collection:

```python
collection_name = "synthetic_anketas"

vector_config = {
    "size": 384,  # GigaChat Embeddings dimension
    "distance": "Cosine"
}

payload_schema = {
    "anketa_id": str,
    "project_name": str,
    "region": str,
    "quality_target": str,  # low/medium/high
    "validation_score": float,
    "created_at": str
}
```

---

## 📝 IMPLEMENTATION

### Phase 1: Qdrant Client (30 минут)

**Создать:** `shared/vector_db/qdrant_client.py`

```python
"""
Qdrant Client для работы с векторной БД
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GrantServiceQdrantClient:
    """Клиент для работы с Qdrant"""

    def __init__(
        self,
        host: str = "5.35.88.251",
        port: int = 6333
    ):
        """
        Args:
            host: Qdrant server host
            port: Qdrant server port
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "synthetic_anketas"

    def create_collection_if_not_exists(self):
        """Создать collection если не существует"""

        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # GigaChat Embeddings
                    distance=Distance.COSINE
                )
            )
            logger.info(f"[Qdrant] Created collection: {self.collection_name}")
        else:
            logger.info(f"[Qdrant] Collection exists: {self.collection_name}")

    async def add_anketa(
        self,
        anketa_id: str,
        embedding: List[float],
        anketa_data: Dict
    ):
        """
        Добавить анкету в Qdrant

        Args:
            anketa_id: ID анкеты
            embedding: Вектор (384 dimensions)
            anketa_data: Метаданные анкеты
        """

        try:
            point = PointStruct(
                id=anketa_id,
                vector=embedding,
                payload={
                    "anketa_id": anketa_id,
                    "project_name": anketa_data.get('project_name'),
                    "region": anketa_data.get('region'),
                    "organization": anketa_data.get('organization'),
                    "quality_target": anketa_data.get('quality_target'),
                    "budget": anketa_data.get('budget'),
                    "synthetic": True
                }
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.info(f"[Qdrant] Added anketa: {anketa_id}")

        except Exception as e:
            logger.error(f"[Qdrant] Failed to add anketa: {e}")

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Поиск похожих анкет

        Args:
            query_embedding: Вектор запроса
            limit: Количество результатов
            score_threshold: Минимальный similarity score

        Returns:
            [
                {
                    'anketa_id': 'AN-xxx',
                    'score': 0.85,
                    'project_name': '...',
                    ...
                }
            ]
        """

        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )

            return [
                {
                    'anketa_id': hit.payload['anketa_id'],
                    'score': hit.score,
                    'project_name': hit.payload.get('project_name'),
                    'region': hit.payload.get('region'),
                    'quality_target': hit.payload.get('quality_target')
                }
                for hit in results
            ]

        except Exception as e:
            logger.error(f"[Qdrant] Search failed: {e}")
            return []

    async def find_duplicates(
        self,
        threshold: float = 0.9
    ) -> List[tuple]:
        """
        Найти почти дубликаты в корпусе

        Args:
            threshold: Similarity > threshold = дубликат

        Returns:
            [(anketa_id_1, anketa_id_2, score), ...]
        """

        # Получить все векторы
        all_points = self.client.scroll(
            collection_name=self.collection_name,
            limit=1000
        )[0]

        duplicates = []

        for point in all_points:
            # Поиск похожих
            similar = await self.search_similar(
                query_embedding=point.vector,
                limit=2,  # себя + 1 похожий
                score_threshold=threshold
            )

            # Если нашли похожих (кроме себя)
            if len(similar) > 1:
                duplicates.append((
                    point.payload['anketa_id'],
                    similar[1]['anketa_id'],
                    similar[1]['score']
                ))

        return duplicates

    async def calculate_diversity_score(self) -> float:
        """
        Рассчитать diversity score корпуса

        Returns:
            0.0 - все одинаковые
            1.0 - все разные

        Метод: Средняя similarity всех пар
        """

        all_points = self.client.scroll(
            collection_name=self.collection_name,
            limit=1000
        )[0]

        if len(all_points) < 2:
            return 1.0

        similarities = []

        # Sample 100 случайных пар (не все, слишком долго)
        import random
        for _ in range(min(100, len(all_points))):
            p1, p2 = random.sample(all_points, 2)

            # Cosine similarity
            from numpy import dot
            from numpy.linalg import norm

            sim = dot(p1.vector, p2.vector) / (norm(p1.vector) * norm(p2.vector))
            similarities.append(sim)

        avg_similarity = sum(similarities) / len(similarities)

        # Diversity = 1 - similarity
        diversity = 1.0 - avg_similarity

        return diversity
```

---

### Phase 2: GigaChat Embeddings (30 минут)

**Добавить в:** `shared/llm/unified_llm_client.py`

```python
async def generate_embedding(self, text: str) -> List[float]:
    """
    Генерировать embedding через GigaChat Embeddings API

    Args:
        text: Текст для векторизации

    Returns:
        Вектор (384 dimensions)
    """

    if self.provider != 'gigachat':
        raise ValueError("Embeddings only for GigaChat provider")

    # Авторизация
    access_token = await self._get_gigachat_token()

    url = "https://gigachat.devices.sberbank.ru/api/v1/embeddings"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "Embeddings",  # GigaChat Embeddings model
        "input": [text]
    }

    try:
        async with self.session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()

                # Extract embedding
                embedding = response_data["data"][0]["embedding"]

                # Log token usage
                usage = response_data.get("usage", {})
                logger.info(f"[Embeddings] Tokens: {usage.get('total_tokens', 0)}")

                return embedding

            else:
                error = await response.text()
                raise Exception(f"Embeddings API error: {response.status} - {error}")

    except Exception as e:
        logger.error(f"[Embeddings] Failed: {e}")
        raise
```

---

### Phase 3: Integration в Telegram Commands (30 минут)

**Добавить в:** `telegram-bot/handlers/anketa_management_handler.py`

```python
async def _add_to_qdrant(self, anketa_id: str, anketa_data: Dict):
    """
    Добавить анкету в Qdrant для поиска

    Использует GigaChat Embeddings API
    """

    try:
        from shared.vector_db.qdrant_client import GrantServiceQdrantClient
        from shared.llm.unified_llm_client import UnifiedLLMClient

        # 1. Создать текстовое представление анкеты
        text = self._anketa_to_text(anketa_data)

        # 2. Генерировать embedding
        llm = UnifiedLLMClient(provider='gigachat')
        async with llm:
            embedding = await llm.generate_embedding(text)

        # 3. Добавить в Qdrant
        qdrant = GrantServiceQdrantClient()
        await qdrant.add_anketa(
            anketa_id=anketa_id,
            embedding=embedding,
            anketa_data=anketa_data
        )

        logger.info(f"[Qdrant] Added {anketa_id} to vector DB")

    except Exception as e:
        logger.error(f"[Qdrant] Failed to add {anketa_id}: {e}")
        # Не падаем если Qdrant недоступен

def _anketa_to_text(self, anketa_data: Dict) -> str:
    """
    Конвертировать анкету в текст для embedding

    Формат: все важные поля через пробел
    """

    parts = [
        anketa_data.get('project_name', ''),
        anketa_data.get('organization', ''),
        anketa_data.get('region', ''),
        anketa_data.get('problem', ''),
        anketa_data.get('solution', ''),
        ' '.join(anketa_data.get('goals', [])),
        ' '.join(anketa_data.get('activities', []))
    ]

    return ' '.join(filter(None, parts))
```

**Новая команда:** `/find_similar_anketas`

```python
async def find_similar_anketas(self, update, context):
    """
    Найти похожие анкеты в корпусе

    Использование:
    /find_similar_anketas [anketa_id]
    /find_similar_anketas           (использует последнюю)
    """

    # Parse anketa_id
    anketa_id = context.args[0] if context.args else None

    if not anketa_id:
        # Взять последнюю анкету пользователя
        anketa = self.db.get_user_latest_anketa(update.effective_user.id)
        anketa_id = anketa['anketa_id']

    # Get anketa data
    anketa = self.db.get_anketa_by_id(anketa_id)
    if not anketa:
        await update.message.reply_text(f"❌ Анкета {anketa_id} не найдена")
        return

    await update.message.reply_text(
        f"🔍 Ищу похожие анкеты для {anketa_id}...\n"
        f"Используется GigaChat Embeddings + Qdrant"
    )

    try:
        # 1. Vectorize query anketa
        text = self._anketa_to_text(anketa['interview_data'])

        llm = UnifiedLLMClient(provider='gigachat')
        async with llm:
            embedding = await llm.generate_embedding(text)

        # 2. Search in Qdrant
        qdrant = GrantServiceQdrantClient()
        similar = await qdrant.search_similar(
            query_embedding=embedding,
            limit=5,
            score_threshold=0.5
        )

        # 3. Format results
        if not similar:
            await update.message.reply_text(
                f"📭 Похожих анкет не найдено (similarity < 0.5)"
            )
            return

        message = f"🔍 Найдено {len(similar)} похожих анкет:\n\n"

        for i, item in enumerate(similar, 1):
            message += (
                f"{i}. **{item['anketa_id']}**\n"
                f"   Similarity: {item['score']:.2f}\n"
                f"   Проект: {item['project_name']}\n"
                f"   Регион: {item['region']}\n"
                f"   Качество: {item['quality_target']}\n\n"
            )

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"[FindSimilar] Error: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при поиске похожих анкет: {e}"
        )
```

---

## 💰 TOKEN USAGE

### Embeddings токены:

```python
# Пример расчёта
anketa_text = """
Молодежный образовательный центр "Цифровое будущее"
АНО "Развитие молодежных инициатив"
Кемеровская область - Кузбасс
В Кемеровской области наблюдается острый дефицит...
"""

# Средняя длина: ~1000 символов
# Tokens: ~250 (4 символа = 1 токен)
# Embeddings API: ~100 токенов на запрос

# 100 анкет:
100 * 100 = 10,000 токенов Embeddings ✅

# Поиск похожих (100 запросов):
100 * 100 = 10,000 токенов Embeddings ✅

# ИТОГО: 20,000 токенов из 5,000,000 (0.4%)
```

---

## 📊 USE CASES

### 1. Quality Control
```python
# После генерации 100 анкет
diversity = await qdrant.calculate_diversity_score()

if diversity < 0.5:
    print("⚠️ Низкое разнообразие! Генератор повторяется")
else:
    print(f"✅ Хорошее разнообразие: {diversity:.2f}")
```

### 2. Duplicate Detection
```python
duplicates = await qdrant.find_duplicates(threshold=0.9)

if duplicates:
    print(f"⚠️ Найдено {len(duplicates)} почти дубликатов:")
    for dup in duplicates:
        print(f"  {dup[0]} ≈ {dup[1]} (sim: {dup[2]:.2f})")
```

### 3. Recommendation Engine
```python
# Когда пользователь создаёт анкету
user_anketa = {...}

# Найти 5 похожих из корпуса
similar = await qdrant.search_similar(embedding, limit=5)

# Показать как примеры
message = "💡 Вот похожие успешные проекты:\n"
for item in similar:
    message += f"• {item['project_name']} (оценка: {item['validation_score']}/10)\n"
```

---

## ✅ ИТОГО

### Что получаем:

1. ✅ **Тратим Embeddings токены** (~20K на 100 анкет)
2. ✅ **Quality control** (diversity score)
3. ✅ **Duplicate detection** (находим повторы)
4. ✅ **Recommendation engine** (примеры для пользователей)
5. ✅ **Показываем Sber500** использование Qdrant + Embeddings

### Токены за неделю (5 прогонов):

```
Embeddings: 20K * 5 = 100K токенов
Из лимита: 100K / 5M = 2% использования

+ Max:  1,000K (50% использования)
+ Pro:    500K (25% использования)
+ Lite:   750K (38% использования)
──────────────────────────────────
ИТОГО показываем активное использование ВСЕХ типов токенов! ✅
```

---

**Created:** 2025-10-25
**Iteration:** 38 - Qdrant Integration
**Status:** READY TO IMPLEMENT
