"""
Загрузка данных из UNIFIED_KNOWLEDGE_BASE.md в PostgreSQL + Qdrant
"""

import sys
sys.path.append('C:\\SnowWhiteAI\\GrantService')

from expert_agent import ExpertAgent
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def parse_fpg_knowledge_base(file_path: str):
    """
    Парсинг UNIFIED_KNOWLEDGE_BASE.md

    Возвращает список разделов:
    [
        {
            'title': 'Общие требования к заполнению заявки',
            'url': 'https://...',
            'content': '...',
            'category': 'Общие правила',
            'size': 4990
        },
        ...
    ]
    """
    logger.info(f"Чтение файла: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    logger.info(f"Размер файла: {len(content)} символов")

    # Разделить на статьи по паттерну ## Заголовок
    # Каждая статья содержит: заголовок, URL, размер, полный текст

    sections = []
    current_category = "Общие"

    # Паттерн для заголовков категорий (# Общие правила)
    category_pattern = r'^# ([^#\n]+)$'

    # Паттерн для статей (## Заголовок)
    article_pattern = r'^## (.+)$'

    # Паттерн для URL
    url_pattern = r'\*\*Источник:\*\* \[([^\]]+)\]\(([^\)]+)\)'

    # Паттерн для размера
    size_pattern = r'\*\*Размер:\*\* (\d+) символов'

    lines = content.split('\n')

    current_article = None
    current_url = None
    current_size = None
    collecting_text = False
    article_text = []

    for line in lines:
        # Проверка на категорию
        category_match = re.match(category_pattern, line, re.MULTILINE)
        if category_match:
            current_category = category_match.group(1).strip()
            logger.info(f"Категория: {current_category}")
            continue

        # Проверка на заголовок статьи
        article_match = re.match(article_pattern, line)
        if article_match:
            # Сохранить предыдущую статью
            if current_article and article_text:
                full_text = '\n'.join(article_text).strip()
                if len(full_text) > 100:  # Минимум 100 символов
                    sections.append({
                        'title': current_article,
                        'url': current_url,
                        'content': full_text,
                        'category': current_category,
                        'size': current_size or len(full_text)
                    })
                    logger.info(f"  Добавлена статья: {current_article} ({len(full_text)} символов)")

            # Начать новую статью
            current_article = article_match.group(1).strip()
            current_url = None
            current_size = None
            article_text = []
            collecting_text = False
            continue

        # Проверка на URL
        url_match = re.search(url_pattern, line)
        if url_match:
            current_url = url_match.group(2)
            continue

        # Проверка на размер
        size_match = re.search(size_pattern, line)
        if size_match:
            current_size = int(size_match.group(1))
            continue

        # Начать сбор текста после "### Полный текст"
        if '### Полный текст' in line or '### Текст' in line:
            collecting_text = True
            continue

        # Собирать текст
        if collecting_text and current_article:
            # Пропустить разделители
            if line.strip() in ['---', '']:
                continue
            # Пропустить следующий заголовок статьи
            if line.startswith('##'):
                continue

            article_text.append(line)

    # Добавить последнюю статью
    if current_article and article_text:
        full_text = '\n'.join(article_text).strip()
        if len(full_text) > 100:
            sections.append({
                'title': current_article,
                'url': current_url,
                'content': full_text,
                'category': current_category,
                'size': current_size or len(full_text)
            })
            logger.info(f"  Добавлена статья: {current_article} ({len(full_text)} символов)")

    logger.info(f"\nВсего найдено статей: {len(sections)}")
    return sections


def load_to_database(sections, agent):
    """Загрузить разделы в PostgreSQL + Qdrant"""

    logger.info("\nЗагрузка в базу данных...")

    # 1. Создать источник для ФПГ (если ещё нет)
    cursor = agent.pg_conn.cursor()

    cursor.execute("""
        SELECT id FROM knowledge_sources
        WHERE fund_name = 'fpg' AND source_type = 'unified_kb'
        LIMIT 1
    """)

    row = cursor.fetchone()

    if row:
        source_id = row[0]
        logger.info(f"Используем существующий источник (ID: {source_id})")
    else:
        cursor.execute("""
            INSERT INTO knowledge_sources
            (fund_name, source_type, title, url, version, is_active, priority)
            VALUES ('fpg', 'unified_kb', 'Единая база знаний ФПГ',
                    'https://президентскиегранты.рф', '2025', true, 10)
            RETURNING id
        """)
        source_id = cursor.fetchone()[0]
        agent.pg_conn.commit()
        logger.info(f"Создан новый источник (ID: {source_id})")

    # 2. Загрузить все разделы
    loaded_count = 0
    skipped_count = 0

    from qdrant_client.models import PointStruct

    for i, section in enumerate(sections, 1):
        try:
            # Проверить, есть ли уже такой раздел
            cursor.execute("""
                SELECT id FROM knowledge_sections
                WHERE section_name = %s AND source_id = %s
            """, (section['title'], source_id))

            if cursor.fetchone():
                logger.info(f"[{i}/{len(sections)}] Пропуск (уже есть): {section['title'][:50]}...")
                skipped_count += 1
                continue

            # Добавить в PostgreSQL
            cursor.execute("""
                INSERT INTO knowledge_sections
                (source_id, section_type, section_name, content, priority, tags)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                source_id,
                'requirement',  # Тип раздела
                section['title'],
                section['content'],
                8,  # Высокий приоритет для официальных требований
                [section['category']] if section['category'] else []
            ))

            section_id = cursor.fetchone()[0]
            agent.pg_conn.commit()

            # Создать embedding
            embedding = agent.create_embedding(section['content'])

            # Добавить в Qdrant
            point = PointStruct(
                id=section_id,
                vector=embedding,
                payload={
                    "section_id": section_id,
                    "section_name": section['title'],
                    "section_type": "requirement",
                    "fund_name": "fpg",
                    "priority": 8,
                    "category": section['category'],
                    "url": section['url']
                }
            )

            agent.qdrant.upsert(
                collection_name=agent.collection_name,
                points=[point]
            )

            loaded_count += 1
            logger.info(f"[{i}/{len(sections)}] Загружено: {section['title'][:50]}...")

        except Exception as e:
            logger.error(f"Ошибка при загрузке раздела '{section['title']}': {e}")
            agent.pg_conn.rollback()

    logger.info(f"\n✓ Загружено: {loaded_count}")
    logger.info(f"  Пропущено: {skipped_count}")
    logger.info(f"  Всего: {loaded_count + skipped_count}")


def main():
    """Главная функция"""

    logger.info("=" * 60)
    logger.info("Загрузка базы знаний ФПГ в Expert Agent")
    logger.info("=" * 60)

    # 1. Парсинг файла
    kb_file = 'C:\\SnowWhiteAI\\GrantService\\fpg_docs_2025\\UNIFIED_KNOWLEDGE_BASE.md'
    sections = parse_fpg_knowledge_base(kb_file)

    if not sections:
        logger.error("Не удалось распарсить разделы!")
        return

    # 2. Создать Expert Agent
    logger.info("\nИнициализация Expert Agent...")
    agent = ExpertAgent()

    # 3. Загрузить в БД
    load_to_database(sections, agent)

    # 4. Статистика
    stats = agent.get_statistics()
    logger.info("\n" + "=" * 60)
    logger.info("Финальная статистика:")
    logger.info("=" * 60)
    logger.info(f"PostgreSQL разделов: {stats['postgres']['sections']}")
    logger.info(f"Qdrant векторов: {stats['qdrant']['vectors']}")
    logger.info("=" * 60)

    agent.close()


if __name__ == "__main__":
    main()
