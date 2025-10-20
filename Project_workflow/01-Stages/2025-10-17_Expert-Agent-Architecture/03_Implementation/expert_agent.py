# -*- coding: utf-8 -*-
"""
Expert Agent - Центральный агент-эксперт по грантовым заявкам
==============================================================

Назначение:
- Управление базой знаний в PostgreSQL
- Семантический поиск по векторным embeddings
- Дообучение других агентов (Writer, Reviewer, Researcher, Interviewer)
- Обновление знаний через Researcher агента

Технологии:
- PostgreSQL 14+ с расширением pgvector
- asyncpg для асинхронных операций с БД
- sentence-transformers для создания embeddings
- FastAPI для REST API
"""

import asyncio
import asyncpg
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
from dataclasses import dataclass


@dataclass
class KnowledgeSection:
    """Структура для раздела знаний"""
    id: int
    section_name: str
    content: str
    similarity: float
    source_title: str
    char_limit: Optional[int] = None
    priority: int = 5


class ExpertAgent:
    """
    Центральный агент-эксперт по грантам
    Управляет базой знаний и обучает других агентов
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        embeddings_service,
        llm_client,
        config: Optional[Dict] = None
    ):
        """
        Инициализация Expert Agent

        Args:
            db_pool: Connection pool к PostgreSQL
            embeddings_service: Сервис для генерации embeddings (ruBERT/sberGPT)
            llm_client: Клиент для LLM (GigaChat, OpenAI, etc.)
            config: Дополнительная конфигурация
        """
        self.db = db_pool
        self.embeddings = embeddings_service
        self.llm = llm_client
        self.config = config or {}

        # Настройки по умолчанию
        self.default_fund = self.config.get('default_fund', 'fpg')
        self.default_top_k = self.config.get('default_top_k', 5)
        self.default_min_similarity = self.config.get('default_min_similarity', 0.75)

    # ========================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ========================================================================

    async def query_knowledge(
        self,
        question: str,
        fund: str = None,
        top_k: int = None,
        min_similarity: float = None,
        context: Optional[str] = None
    ) -> Dict:
        """
        Семантический поиск по базе знаний

        Args:
            question: Вопрос пользователя
            fund: Фонд ('fpg', 'kultura', etc.). Если None - используется default
            top_k: Количество релевантных разделов
            min_similarity: Минимальная схожесть (0-1)
            context: Дополнительный контекст (опционально)

        Returns:
            {
                'answer': str,
                'sources': List[int],
                'confidence': float,
                'relevant_sections': List[KnowledgeSection],
                'metadata': Dict
            }
        """
        # Использовать значения по умолчанию если не указаны
        fund = fund or self.default_fund
        top_k = top_k or self.default_top_k
        min_similarity = min_similarity or self.default_min_similarity

        # 1. Создать embedding для вопроса
        question_embedding = await self.embeddings.get_embedding(question)

        # 2. Векторный поиск в БД
        relevant_sections = await self._vector_search(
            question_embedding,
            fund,
            top_k,
            min_similarity
        )

        if not relevant_sections:
            return {
                'answer': f'К сожалению, не нашел релевантной информации в базе знаний по фонду {fund.upper()}.',
                'sources': [],
                'confidence': 0.0,
                'relevant_sections': [],
                'metadata': {
                    'query': question,
                    'fund': fund,
                    'found_sections': 0
                }
            }

        # 3. Сформировать контекст для LLM
        llm_context = self._build_context(relevant_sections, additional_context=context)

        # 4. Генерация ответа через LLM
        answer = await self.llm.generate(
            system_prompt=self._get_system_prompt(fund),
            context=llm_context,
            question=question
        )

        # 5. Рассчитать уверенность
        confidence = self._calculate_confidence(relevant_sections)

        return {
            'answer': answer,
            'sources': [s.id for s in relevant_sections],
            'confidence': confidence,
            'relevant_sections': [self._section_to_dict(s) for s in relevant_sections],
            'metadata': {
                'query': question,
                'fund': fund,
                'found_sections': len(relevant_sections),
                'avg_similarity': np.mean([s.similarity for s in relevant_sections])
            }
        }

    async def train_agent(
        self,
        agent_name: str,
        fund: str = None,
        section: Optional[str] = None,
        format: str = 'markdown'
    ) -> Dict:
        """
        Дообучить конкретного агента на основе БЗ
        Генерирует актуальный промпт для агента

        Args:
            agent_name: 'writer', 'reviewer', 'researcher', 'interviewer'
            fund: Фонд (если None - default)
            section: Конкретный раздел (опционально)
            format: Формат вывода ('markdown', 'json', 'plain')

        Returns:
            {
                'status': 'success',
                'agent_name': str,
                'updated_prompt': str,
                'knowledge_items': int,
                'version': str,
                'metadata': Dict
            }
        """
        fund = fund or self.default_fund

        # Валидация agent_name
        valid_agents = ['writer', 'reviewer', 'researcher', 'interviewer']
        if agent_name not in valid_agents:
            raise ValueError(f"Unknown agent: {agent_name}. Valid: {valid_agents}")

        # 1. Получить знания для конкретного агента
        if agent_name == 'writer':
            knowledge = await self._get_writer_knowledge(fund, section)
        elif agent_name == 'reviewer':
            knowledge = await self._get_reviewer_knowledge(fund)
        elif agent_name == 'researcher':
            knowledge = await self._get_researcher_knowledge(fund)
        elif agent_name == 'interviewer':
            knowledge = await self._get_interviewer_knowledge(fund)

        # 2. Подготовить training data
        training_data = self._prepare_training_data(knowledge, agent_name, format)

        # 3. Создать версию
        version = datetime.now().strftime('%Y-%m-%d_v1')

        # 4. Обновить промпт агента (через n8n API или файл)
        updated_prompt = await self._update_agent_prompt(
            agent_name,
            training_data,
            version,
            fund
        )

        return {
            'status': 'success',
            'agent_name': agent_name,
            'updated_prompt': updated_prompt,
            'knowledge_items': len(knowledge),
            'version': version,
            'metadata': {
                'fund': fund,
                'section': section,
                'format': format,
                'timestamp': datetime.now().isoformat()
            }
        }

    async def update_knowledge(
        self,
        topic: str,
        fund: str = None,
        trigger: str = 'manual',
        validate: bool = True
    ) -> Dict:
        """
        Обновить знания через Researcher агента

        Args:
            topic: Тема для обновления
            fund: Фонд (если None - default)
            trigger: 'manual', 'scheduled', 'auto'
            validate: Валидировать информацию перед сохранением

        Returns:
            {
                'status': 'success' | 'no_data' | 'rejected',
                'sections_added': int,
                'sections_updated': int,
                'researcher_task_id': str,
                'metadata': Dict
            }
        """
        fund = fund or self.default_fund

        # 1. Вызвать Researcher агента
        new_info = await self._call_researcher_agent(topic, fund)

        if not new_info or not new_info.get('sections'):
            return {
                'status': 'no_data',
                'message': 'Researcher не нашел новой информации',
                'metadata': {
                    'topic': topic,
                    'fund': fund,
                    'trigger': trigger
                }
            }

        # 2. Валидировать информацию (если требуется)
        if validate:
            validation_result = await self._validate_information(new_info)
            if not validation_result['is_valid']:
                return {
                    'status': 'rejected',
                    'reason': validation_result['reason'],
                    'metadata': validation_result.get('details', {})
                }

        # 3. Сохранить в БД
        sections_added, sections_updated = await self._save_knowledge(new_info, fund)

        # 4. Создать embeddings для новых разделов
        if sections_added:
            await self._create_embeddings_for_new_sections(sections_added)

        # 5. Залогировать обновление
        await self._log_update(
            updated_by='researcher',
            update_type='new' if sections_added else 'update',
            description=f'Updated {topic}',
            record_ids=sections_added + sections_updated
        )

        return {
            'status': 'success',
            'sections_added': len(sections_added),
            'sections_updated': len(sections_updated),
            'metadata': {
                'topic': topic,
                'fund': fund,
                'trigger': trigger,
                'timestamp': datetime.now().isoformat()
            }
        }

    # ========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ: ВЕКТОРНЫЙ ПОИСК
    # ========================================================================

    async def _vector_search(
        self,
        query_embedding: np.ndarray,
        fund: str,
        top_k: int,
        min_similarity: float
    ) -> List[KnowledgeSection]:
        """Векторный поиск похожих разделов"""

        query = """
        SELECT
            ks.id,
            ks.section_name,
            ks.content,
            ks.char_limit,
            ks.priority,
            src.title AS source_title,
            src.url AS source_url,
            1 - (ke.embedding <=> $1::vector) AS similarity
        FROM knowledge_sections ks
        JOIN knowledge_sources src ON src.id = ks.source_id
        JOIN knowledge_embeddings ke ON ke.section_id = ks.id
        WHERE
            src.fund_name = $2
            AND src.is_active = true
            AND (1 - (ke.embedding <=> $1::vector)) >= $3
        ORDER BY ke.embedding <=> $1::vector
        LIMIT $4
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                query,
                query_embedding.tolist(),
                fund,
                min_similarity,
                top_k
            )

        return [
            KnowledgeSection(
                id=row['id'],
                section_name=row['section_name'],
                content=row['content'],
                similarity=row['similarity'],
                source_title=row['source_title'],
                char_limit=row['char_limit'],
                priority=row['priority']
            )
            for row in rows
        ]

    def _build_context(
        self,
        sections: List[KnowledgeSection],
        additional_context: Optional[str] = None
    ) -> str:
        """Построить контекст для LLM из найденных разделов"""
        context_parts = []

        # Добавить дополнительный контекст если есть
        if additional_context:
            context_parts.append(f"**Дополнительный контекст:**\n{additional_context}\n")

        # Добавить найденные разделы
        for i, section in enumerate(sections, 1):
            section_text = f"""
**Источник {i}:** {section.source_title}
**Раздел:** {section.section_name}
**Релевантность:** {section.similarity:.2%}
**Приоритет:** {section.priority}/10
{f"**Ограничение символов:** {section.char_limit}" if section.char_limit else ""}

{section.content}
            """.strip()
            context_parts.append(section_text)

        return "\n\n---\n\n".join(context_parts)

    def _calculate_confidence(self, sections: List[KnowledgeSection]) -> float:
        """Рассчитать уверенность в ответе на основе similarity scores"""
        if not sections:
            return 0.0

        # Средняя similarity с весом на top-1
        top_similarity = sections[0].similarity
        avg_similarity = np.mean([s.similarity for s in sections])

        # Weighted average (60% top-1, 40% average)
        confidence = 0.6 * top_similarity + 0.4 * avg_similarity

        return round(confidence, 3)

    def _get_system_prompt(self, fund: str) -> str:
        """Получить system prompt для LLM в зависимости от фонда"""
        prompts = {
            'fpg': "Ты эксперт по грантовым заявкам Фонда президентских грантов (ФПГ). "
                   "Твоя задача - давать точные, конкретные ответы на основе официальных требований.",
            'kultura': "Ты эксперт по грантовым заявкам фонда КультураРФ. "
                       "Отвечай четко и по существу, ссылаясь на официальные требования.",
            'rosmolodjezh': "Ты эксперт по грантам Росмолодежи. "
                            "Давай конкретные рекомендации на основе официальной документации."
        }
        return prompts.get(fund, f"Ты эксперт по грантовым заявкам фонда {fund.upper()}.")

    # ========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ: ПОЛУЧЕНИЕ ЗНАНИЙ ДЛЯ АГЕНТОВ
    # ========================================================================

    async def _get_writer_knowledge(
        self,
        fund: str,
        section: Optional[str]
    ) -> List[Dict]:
        """Получить знания для Writer агента"""
        query = """
        SELECT
            ks.id,
            ks.section_name,
            ks.content,
            ks.char_limit,
            ks.priority,
            ks.tags,
            src.title,
            src.url
        FROM knowledge_sections ks
        JOIN knowledge_sources src ON src.id = ks.source_id
        WHERE
            src.fund_name = $1
            AND src.is_active = true
            AND ks.section_type IN ('requirement', 'example', 'tip')
        """

        params = [fund]

        if section:
            query += " AND ks.section_name ILIKE $2"
            params.append(f"%{section}%")

        query += " ORDER BY ks.priority DESC, ks.section_name"

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def _get_reviewer_knowledge(self, fund: str) -> List[Dict]:
        """Получить знания для Reviewer агента (критерии оценки)"""
        query = """
        SELECT
            id,
            criterion_number,
            criterion_name,
            max_score,
            description,
            examples,
            tips,
            common_mistakes
        FROM evaluation_criteria
        WHERE fund_name = $1
        ORDER BY criterion_number
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, fund)

        return [dict(row) for row in rows]

    async def _get_researcher_knowledge(self, fund: str) -> List[Dict]:
        """Получить знания для Researcher агента"""
        # Researcher нужна информация об источниках для парсинга
        query = """
        SELECT DISTINCT
            src.url,
            src.title,
            src.source_type,
            src.version
        FROM knowledge_sources src
        WHERE
            src.fund_name = $1
            AND src.is_active = true
            AND src.url IS NOT NULL
        ORDER BY src.title
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, fund)

        return [dict(row) for row in rows]

    async def _get_interviewer_knowledge(self, fund: str) -> List[Dict]:
        """Получить знания для Interviewer агента"""
        # Interviewer нужны required поля для сбора информации
        query = """
        SELECT
            ks.section_name,
            ks.char_limit,
            ks.content,
            ks.priority
        FROM knowledge_sections ks
        JOIN knowledge_sources src ON src.id = ks.source_id
        WHERE
            src.fund_name = $1
            AND src.is_active = true
            AND ks.section_type = 'requirement'
        ORDER BY ks.priority DESC, ks.section_name
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, fund)

        return [dict(row) for row in rows]

    # ========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ: ПОДГОТОВКА TRAINING DATA
    # ========================================================================

    def _prepare_training_data(
        self,
        knowledge: List[Dict],
        agent_name: str,
        format: str = 'markdown'
    ) -> str:
        """Подготовить training data для агента"""

        if agent_name == 'writer':
            return self._format_writer_data(knowledge, format)
        elif agent_name == 'reviewer':
            return self._format_reviewer_data(knowledge, format)
        elif agent_name == 'researcher':
            return self._format_researcher_data(knowledge, format)
        elif agent_name == 'interviewer':
            return self._format_interviewer_data(knowledge, format)

        return ""

    def _format_writer_data(self, knowledge: List[Dict], format: str) -> str:
        """Форматировать требования для Writer"""
        if format == 'markdown':
            sections = []
            for item in knowledge:
                section = f"### {item['section_name']}\n\n"
                if item.get('char_limit'):
                    section += f"**Ограничение:** {item['char_limit']} символов\n\n"
                section += f"{item['content']}\n"
                if item.get('tags'):
                    section += f"\n**Теги:** {', '.join(item['tags'])}\n"
                sections.append(section)
            return "\n".join(sections)

        elif format == 'json':
            return json.dumps(knowledge, ensure_ascii=False, indent=2)

        else:  # plain
            return "\n\n".join([
                f"{item['section_name']}: {item['content']}"
                for item in knowledge
            ])

    def _format_reviewer_data(self, knowledge: List[Dict], format: str) -> str:
        """Форматировать критерии для Reviewer"""
        if format == 'markdown':
            criteria = []
            for item in knowledge:
                criterion = f"""
**Критерий {item['criterion_number']}: {item['criterion_name']}**
Максимум баллов: {item['max_score']}

Описание:
{item['description']}
                """.strip()

                if item.get('tips'):
                    criterion += f"\n\n**Советы:**\n{item['tips']}"

                if item.get('common_mistakes'):
                    criterion += f"\n\n**Частые ошибки:**\n{item['common_mistakes']}"

                criteria.append(criterion)

            return "\n\n---\n\n".join(criteria)

        elif format == 'json':
            return json.dumps(knowledge, ensure_ascii=False, indent=2)

        else:  # plain
            return "\n\n".join([
                f"Критерий {item['criterion_number']}: {item['criterion_name']} ({item['max_score']} баллов)"
                for item in knowledge
            ])

    def _format_researcher_data(self, knowledge: List[Dict], format: str) -> str:
        """Форматировать источники для Researcher"""
        if format == 'markdown':
            sources = []
            for item in knowledge:
                source = f"- **{item['title']}**\n  URL: {item['url']}\n  Тип: {item['source_type']}"
                sources.append(source)
            return "\n".join(sources)

        elif format == 'json':
            return json.dumps(knowledge, ensure_ascii=False, indent=2)

        else:  # plain
            return "\n".join([item['url'] for item in knowledge])

    def _format_interviewer_data(self, knowledge: List[Dict], format: str) -> str:
        """Форматировать вопросы для Interviewer"""
        if format == 'markdown':
            questions = []
            for item in knowledge:
                q = f"**{item['section_name']}**"
                if item.get('char_limit'):
                    q += f" (макс {item['char_limit']} символов)"
                q += f"\n{item['content'][:200]}..."
                questions.append(q)
            return "\n\n".join(questions)

        elif format == 'json':
            return json.dumps(knowledge, ensure_ascii=False, indent=2)

        else:  # plain
            return "\n".join([item['section_name'] for item in knowledge])

    async def _update_agent_prompt(
        self,
        agent_name: str,
        training_data: str,
        version: str,
        fund: str
    ) -> str:
        """Обновить промпт агента"""
        # TODO: Реализовать интеграцию с n8n или файловой системой
        # Например, обновить файл .claude/agents/{agent_name}.md

        updated_prompt = f"""
# {agent_name.title()} Agent - {fund.upper()}

**Версия:** {version}
**Обновлено Expert Agent:** {datetime.now().isoformat()}
**Фонд:** {fund.upper()}

## Актуальные требования

{training_data}

## Инструкции для агента

[... остальной промпт агента ...]
        """.strip()

        return updated_prompt

    # ========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ: ОБНОВЛЕНИЕ ЗНАНИЙ
    # ========================================================================

    async def _call_researcher_agent(self, topic: str, fund: str) -> Optional[Dict]:
        """Вызвать Researcher агента через n8n"""
        # TODO: Реализовать вызов n8n webhook
        # POST https://n8n.example.com/webhook/researcher
        # {
        #     "task": "fetch_requirements",
        #     "fund": fund,
        #     "topic": topic
        # }

        # Заглушка для тестирования
        return {
            'source_type': 'official_article',
            'title': f'Новые требования {topic}',
            'source_url': f'https://example.com/{topic}',
            'version': '2025',
            'sections': [
                {
                    'type': 'requirement',
                    'name': topic,
                    'content': f'Новое содержание для {topic}',
                    'char_limit': None,
                    'priority': 5
                }
            ]
        }

    async def _validate_information(self, info: Dict) -> Dict:
        """Валидировать новую информацию"""
        # Проверки:
        # 1. Есть ли разделы?
        if not info.get('sections') or len(info['sections']) == 0:
            return {'is_valid': False, 'reason': 'No sections provided'}

        # 2. Указан ли источник (URL)?
        if not info.get('source_url'):
            return {'is_valid': False, 'reason': 'No source URL'}

        # 3. Есть ли title?
        if not info.get('title'):
            return {'is_valid': False, 'reason': 'No title'}

        # 4. Проверка качества контента
        for section in info['sections']:
            if not section.get('content') or len(section['content']) < 50:
                return {
                    'is_valid': False,
                    'reason': f"Section '{section.get('name')}' content too short"
                }

        # TODO: Проверка на дубликаты
        # TODO: Проверка качества через LLM

        return {'is_valid': True}

    async def _save_knowledge(
        self,
        info: Dict,
        fund: str
    ) -> Tuple[List[int], List[int]]:
        """Сохранить знания в БД"""
        sections_added = []
        sections_updated = []

        async with self.db.acquire() as conn:
            # 1. Создать/найти source
            source_id = await conn.fetchval("""
                INSERT INTO knowledge_sources
                (fund_name, source_type, title, url, version, is_active)
                VALUES ($1, $2, $3, $4, $5, true)
                ON CONFLICT (url)
                DO UPDATE SET
                    updated_at = NOW(),
                    is_active = true
                RETURNING id
            """, fund, info['source_type'], info['title'],
               info['source_url'], info.get('version', '2025'))

            # 2. Добавить/обновить разделы
            for section in info['sections']:
                # Проверить существование
                existing = await conn.fetchval("""
                    SELECT id FROM knowledge_sections
                    WHERE source_id = $1 AND section_name = $2
                """, source_id, section['name'])

                if existing:
                    # Обновить существующий
                    await conn.execute("""
                        UPDATE knowledge_sections
                        SET content = $1, updated_at = NOW()
                        WHERE id = $2
                    """, section['content'], existing)
                    sections_updated.append(existing)
                else:
                    # Создать новый
                    section_id = await conn.fetchval("""
                        INSERT INTO knowledge_sections
                        (source_id, section_type, section_name, content, char_limit, priority)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING id
                    """, source_id, section['type'], section['name'],
                       section['content'], section.get('char_limit'),
                       section.get('priority', 5))
                    sections_added.append(section_id)

        return sections_added, sections_updated

    async def _create_embeddings_for_new_sections(self, section_ids: List[int]):
        """Создать embeddings для новых разделов"""
        async with self.db.acquire() as conn:
            for section_id in section_ids:
                # Получить текст
                content = await conn.fetchval(
                    "SELECT content FROM knowledge_sections WHERE id = $1",
                    section_id
                )

                # Создать embedding
                embedding = await self.embeddings.get_embedding(content)

                # Сохранить
                await conn.execute("""
                    INSERT INTO knowledge_embeddings (section_id, embedding, model_name)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (section_id, model_name)
                    DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        created_at = NOW()
                """, section_id, embedding.tolist(), self.embeddings.model_name)

    async def _log_update(
        self,
        updated_by: str,
        update_type: str,
        description: str,
        record_ids: List[int]
    ):
        """Залогировать обновление в knowledge_updates"""
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO knowledge_updates
                (updated_by, update_type, description, affected_tables, record_ids)
                VALUES ($1, $2, $3, $4, $5)
            """, updated_by, update_type, description,
               ['knowledge_sections'], record_ids)

    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================

    def _section_to_dict(self, section: KnowledgeSection) -> Dict:
        """Конвертировать KnowledgeSection в dict"""
        return {
            'id': section.id,
            'section_name': section.section_name,
            'content': section.content[:500] + '...' if len(section.content) > 500 else section.content,
            'similarity': section.similarity,
            'source_title': section.source_title,
            'char_limit': section.char_limit,
            'priority': section.priority
        }

    async def health_check(self) -> Dict:
        """Проверить здоровье Expert Agent"""
        try:
            async with self.db.acquire() as conn:
                # Проверить подключение к БД
                db_version = await conn.fetchval("SELECT version()")

                # Получить статистику
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(DISTINCT id) as total_sources,
                        COUNT(DISTINCT CASE WHEN is_active THEN id END) as active_sources
                    FROM knowledge_sources
                """)

                sections_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM knowledge_sections"
                )

                embeddings_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM knowledge_embeddings"
                )

            return {
                'status': 'healthy',
                'database': {
                    'connected': True,
                    'version': db_version.split()[1] if db_version else 'unknown'
                },
                'statistics': {
                    'total_sources': stats['total_sources'],
                    'active_sources': stats['active_sources'],
                    'sections': sections_count,
                    'embeddings': embeddings_count
                },
                'embeddings_service': {
                    'status': 'available',
                    'model': self.embeddings.model_name
                }
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ
# ============================================================================

class EmbeddingsService:
    """Заглушка для сервиса embeddings"""
    def __init__(self, model_name: str = 'rubert'):
        self.model_name = model_name

    async def get_embedding(self, text: str) -> np.ndarray:
        """Создать embedding для текста"""
        # TODO: Реализовать реальный embeddings service
        # Например, через sentence-transformers или API
        return np.random.rand(1536)  # Заглушка


class LLMClient:
    """Заглушка для LLM клиента"""
    async def generate(
        self,
        system_prompt: str,
        context: str,
        question: str
    ) -> str:
        """Генерация ответа через LLM"""
        # TODO: Реализовать реальный LLM client (GigaChat, OpenAI, etc.)
        return f"Ответ на вопрос '{question}' на основе контекста..."
