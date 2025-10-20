"""
Скрипт для синхронизации данных PostgreSQL → Qdrant
Создаёт embeddings для существующих разделов и загружает в Qdrant
"""

import sys
sys.path.append('C:\\SnowWhiteAI\\GrantService')

from expert_agent import ExpertAgent
from qdrant_client.models import PointStruct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_all_sections():
    """Синхронизировать все разделы из PostgreSQL в Qdrant"""
    agent = ExpertAgent()

    logger.info("Загрузка разделов из PostgreSQL...")

    # Получить все разделы
    cursor = agent.pg_conn.cursor()
    cursor.execute("""
        SELECT
            ks.id,
            ks.content,
            ks.section_name,
            ks.section_type,
            ks.priority,
            ks.char_limit,
            ks.tags,
            src.fund_name
        FROM knowledge_sections ks
        JOIN knowledge_sources src ON ks.source_id = src.id
        WHERE src.is_active = true
    """)

    rows = cursor.fetchall()
    logger.info(f"Найдено {len(rows)} разделов для синхронизации")

    # Создать embeddings и загрузить в Qdrant
    points = []

    for row in rows:
        section_id = row[0]
        content = row[1]
        section_name = row[2]
        section_type = row[3]
        priority = row[4]
        char_limit = row[5]
        tags = row[6]
        fund_name = row[7]

        logger.info(f"Создание embedding для раздела {section_id}: {section_name}")

        # Создать embedding
        embedding = agent.create_embedding(content)

        # Создать точку для Qdrant
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

        points.append(point)

    # Загрузить в Qdrant batch'ем
    if points:
        logger.info(f"Загрузка {len(points)} векторов в Qdrant...")
        agent.qdrant.upsert(
            collection_name=agent.collection_name,
            points=points
        )
        logger.info(f"✅ {len(points)} векторов загружено!")
    else:
        logger.warning("Нет данных для загрузки")

    agent.close()


if __name__ == "__main__":
    sync_all_sections()
