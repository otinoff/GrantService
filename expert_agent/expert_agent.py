"""
Expert Agent - центральный агент-эксперт по грантам
Версия: 1.0 (MVP)
Дата: 2025-10-17

Архитектура:
- PostgreSQL: структурированные данные (sources, sections, criteria, examples)
- Qdrant: векторные embeddings для семантического поиска
- Sentence Transformers: создание embeddings (multilingual-MiniLM-L6-v2)
"""

import psycopg2
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpertAgent:
    """
    Expert Agent для работы с базой знаний о грантах

    Возможности:
    - Семантический поиск по базе знаний
    - Добавление новых знаний
    - Получение релевантной информации для агентов (Writer, Reviewer и др.)
    """

    def __init__(
        self,
        postgres_host: str = "localhost",
        postgres_port: int = 5432,
        postgres_user: str = "postgres",
        postgres_password: str = "root",
        postgres_db: str = "grantservice",
        qdrant_host: str = "5.35.88.251",  # Production Qdrant на хостинге
        qdrant_port: int = 6333,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Инициализация Expert Agent

        Args:
            postgres_*: параметры подключения к PostgreSQL
            qdrant_*: параметры подключения к Qdrant
            embedding_model: модель для создания embeddings (384 размерность)
        """
        logger.info("Инициализация Expert Agent...")

        # Подключение к PostgreSQL
        self.pg_conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database=postgres_db
        )
        logger.info(f"✅ PostgreSQL подключен ({postgres_host}:{postgres_port})")

        # Подключение к Qdrant
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        logger.info(f"✅ Qdrant подключен ({qdrant_host}:{qdrant_port})")

        # Загрузка модели embeddings
        logger.info(f"Загрузка модели: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info("✅ Модель загружена")

        self.collection_name = "knowledge_sections"

        logger.info("🎉 Expert Agent готов к работе!")

    def create_embedding(self, text: str) -> List[float]:
        """
        Создать векторное представление текста

        Args:
            text: текст для векторизации

        Returns:
            Вектор размерности 384
        """
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def add_knowledge_section(
        self,
        source_id: int,
        section_type: str,
        section_name: str,
        content: str,
        fund_name: str = "fpg",
        char_limit: Optional[int] = None,
        priority: int = 5,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Добавить новый раздел знаний

        Args:
            source_id: ID источника из knowledge_sources
            section_type: тип раздела ('requirement', 'example', 'tip', etc.)
            section_name: название раздела
            content: содержимое
            fund_name: название фонда
            char_limit: ограничение символов
            priority: приоритет (1-10)
            tags: теги для классификации

        Returns:
            ID созданного раздела
        """
        logger.info(f"Добавление раздела: {section_name}")

        # 1. Добавить в PostgreSQL
        cursor = self.pg_conn.cursor()

        cursor.execute("""
            INSERT INTO knowledge_sections
            (source_id, section_type, section_name, content, char_limit, priority, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (source_id, section_type, section_name, content, char_limit, priority, tags or []))

        section_id = cursor.fetchone()[0]
        self.pg_conn.commit()

        logger.info(f"✅ Раздел добавлен в PostgreSQL (ID: {section_id})")

        # 2. Создать embedding
        embedding = self.create_embedding(content)

        # 3. Добавить в Qdrant
        point = PointStruct(
            id=section_id,
            vector=embedding,
            payload={
                "section_id": section_id,
                "section_name": section_name,
                "section_type": section_type,
                "fund_name": fund_name,
                "priority": priority,
                "char_limit": char_limit,
                "tags": tags or []
            }
        )

        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

        logger.info(f"✅ Embedding добавлен в Qdrant (ID: {section_id})")

        return section_id

    def query_knowledge(
        self,
        question: str,
        fund: str = "fpg",
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Семантический поиск по базе знаний

        Args:
            question: вопрос пользователя
            fund: фильтр по фонду
            top_k: количество результатов
            min_score: минимальный score (0.0 - 1.0)

        Returns:
            Список релевантных разделов с метаданными
        """
        logger.info(f"Запрос: {question[:100]}...")

        # 1. Создать embedding для вопроса
        question_embedding = self.create_embedding(question)

        # 2. Поиск в Qdrant
        search_result = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=question_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="fund_name",
                        match=MatchValue(value=fund)
                    )
                ]
            ),
            limit=top_k,
            score_threshold=min_score
        )

        if not search_result:
            logger.warning("Релевантные разделы не найдены")
            return []

        logger.info(f"Найдено {len(search_result)} релевантных разделов")

        # 3. Получить полные данные из PostgreSQL
        section_ids = [hit.id for hit in search_result]

        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT
                ks.id,
                ks.section_name,
                ks.content,
                ks.section_type,
                ks.char_limit,
                ks.priority,
                ks.tags,
                src.title AS source_title,
                src.url AS source_url
            FROM knowledge_sections ks
            JOIN knowledge_sources src ON ks.source_id = src.id
            WHERE ks.id = ANY(%s)
        """, (section_ids,))

        rows = cursor.fetchall()

        # 4. Создать результат с scores
        results = []
        scores = {hit.id: hit.score for hit in search_result}

        for row in rows:
            results.append({
                "id": row[0],
                "section_name": row[1],
                "content": row[2],
                "section_type": row[3],
                "char_limit": row[4],
                "priority": row[5],
                "tags": row[6],
                "source_title": row[7],
                "source_url": row[8],
                "relevance_score": scores[row[0]]
            })

        # Сортировать по score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results

    def get_section_by_id(self, section_id: int) -> Optional[Dict[str, Any]]:
        """Получить раздел по ID"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT
                ks.id,
                ks.section_name,
                ks.content,
                ks.section_type,
                ks.char_limit,
                ks.priority,
                ks.tags,
                src.title AS source_title
            FROM knowledge_sections ks
            JOIN knowledge_sources src ON ks.source_id = src.id
            WHERE ks.id = %s
        """, (section_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "section_name": row[1],
            "content": row[2],
            "section_type": row[3],
            "char_limit": row[4],
            "priority": row[5],
            "tags": row[6],
            "source_title": row[7]
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику базы знаний"""
        cursor = self.pg_conn.cursor()

        # PostgreSQL статистика
        cursor.execute("SELECT COUNT(*) FROM knowledge_sources WHERE is_active = true")
        active_sources = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM knowledge_sections")
        total_sections = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM evaluation_criteria")
        total_criteria = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM successful_grant_examples")
        total_examples = cursor.fetchone()[0]

        # Qdrant статистика
        collection_info = self.qdrant.get_collection(self.collection_name)
        vectors_count = collection_info.points_count

        return {
            "postgres": {
                "active_sources": active_sources,
                "sections": total_sections,
                "criteria": total_criteria,
                "examples": total_examples
            },
            "qdrant": {
                "vectors": vectors_count,
                "collection_status": collection_info.status
            }
        }

    def close(self):
        """Закрыть соединения"""
        self.pg_conn.close()
        logger.info("Соединения закрыты")


# ============================================================================
# Пример использования
# ============================================================================

if __name__ == "__main__":
    # Создать Expert Agent
    agent = ExpertAgent()

    # Статистика
    stats = agent.get_statistics()
    print("\n📊 Статистика базы знаний:")
    print(f"  PostgreSQL:")
    print(f"    - Активных источников: {stats['postgres']['active_sources']}")
    print(f"    - Разделов: {stats['postgres']['sections']}")
    print(f"    - Критериев оценки: {stats['postgres']['criteria']}")
    print(f"    - Примеров заявок: {stats['postgres']['examples']}")
    print(f"  Qdrant:")
    print(f"    - Векторов: {stats['qdrant']['vectors']}")
    print(f"    - Статус: {stats['qdrant']['collection_status']}")

    # Пример запроса
    print("\n🔍 Тестовый запрос:")
    results = agent.query_knowledge(
        question="Какие требования к названию проекта?",
        fund="fpg",
        top_k=3
    )

    if results:
        print(f"\n✅ Найдено {len(results)} результатов:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['section_name']} (score: {result['relevance_score']:.3f})")
            print(f"   {result['content'][:200]}...")
            print()
    else:
        print("❌ Результаты не найдены")

    agent.close()
