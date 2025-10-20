#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code WebSearch Client для Researcher Agent

Расширение ClaudeCodeClient с поддержкой WebSearch API
для выполнения 27 экспертных запросов

API: http://178.236.17.55:8000
Альтернативный: http://5.35.88.251:8000

Автор: AI Integration Specialist
Дата: 2025-10-08
"""

import aiohttp
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class ClaudeCodeWebSearchClient:
    """Асинхронный клиент для WebSearch через Claude Code API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://178.236.17.55:8000",
        timeout: int = 120  # Увеличен таймаут для WebSearch
    ):
        """
        Инициализация клиента

        Args:
            api_key: API ключ (или из CLAUDE_CODE_API_KEY env)
            base_url: Базовый URL API
            timeout: Таймаут запросов в секундах
        """
        self.api_key = api_key or os.getenv('CLAUDE_CODE_API_KEY', '1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732')
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.debug_log = []

        logger.info(f"🔧 ClaudeCodeWebSearchClient инициализирован: {base_url}")

    async def __aenter__(self):
        """Создание HTTP сессии при входе в контекст"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)

        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout_config
        )

        logger.info("✅ ClaudeCodeWebSearchClient сессия создана")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие HTTP сессии при выходе из контекста"""
        if self.session:
            await self.session.close()
            logger.info("🔒 ClaudeCodeWebSearchClient сессия закрыта")

    async def websearch(
        self,
        query: str,
        allowed_domains: Optional[List[str]] = None,
        max_results: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Выполнить WebSearch запрос через Claude Code

        Args:
            query: Поисковый запрос
            allowed_domains: Список разрешенных доменов (например ['rosstat.gov.ru', 'gov.ru'])
            max_results: Максимум результатов (1-10)
            session_id: ID сессии для контекста (опционально)

        Returns:
            {
                'query': 'original query',
                'results': [
                    {
                        'title': 'Result title',
                        'url': 'https://...',
                        'snippet': 'Text snippet',
                        'source': 'rosstat.gov.ru',
                        'date': '2024-03-15',
                        'relevance_score': 0.95
                    }
                ],
                'sources': ['rosstat.gov.ru', 'government.ru'],
                'total_results': 5,
                'search_time': 1.23
            }

        Raises:
            Exception: При ошибке API
        """
        url = f"{self.base_url}/websearch"

        payload = {
            "query": query,
            "max_results": min(max_results, 10)  # Limit to 10
        }

        if allowed_domains:
            payload["allowed_domains"] = allowed_domains
        if session_id:
            payload["session_id"] = session_id

        # Логирование запроса
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/websearch",
            "query_length": len(query),
            "max_results": max_results,
            "allowed_domains": allowed_domains,
            "has_session": session_id is not None
        }
        self.debug_log.append(log_entry)

        try:
            start_time = datetime.now()

            async with self.session.post(url, json=payload) as response:
                response_text = await response.text()

                search_time = (datetime.now() - start_time).total_seconds()

                if response.status == 200:
                    data = json.loads(response_text)

                    # Извлечь уникальные источники
                    sources = list(set([
                        result.get('source', '')
                        for result in data.get('results', [])
                        if result.get('source')
                    ]))

                    result_data = {
                        'status': 'success',
                        'query': query,
                        'content': data.get('content', ''),  # КРИТИЧНО: синтезированный ответ
                        'results': data.get('results', []),
                        'sources': sources,
                        'total_results': len(data.get('results', [])),
                        'search_time': search_time,
                        'session_id': data.get('session_id'),
                        'cost': data.get('cost', 0),  # Для совместимости с EKATERINA
                        'usage': data.get('usage', {}),  # Token usage
                        'provider': 'claude_code'
                    }

                    log_entry.update({
                        "status": "success",
                        "results_count": result_data['total_results'],
                        "sources_count": len(sources),
                        "search_time": search_time
                    })
                    self.debug_log.append(log_entry)

                    logger.info(f"✅ WebSearch: '{query[:50]}...' → {result_data['total_results']} results, {len(sources)} sources ({search_time:.2f}s)")
                    return result_data

                else:
                    error_msg = f"WebSearch error: {response.status} - {response_text}"
                    logger.error(error_msg)

                    log_entry.update({
                        "status": "error",
                        "error": response_text,
                        "status_code": response.status
                    })
                    self.debug_log.append(log_entry)

                    # Вернуть пустой результат вместо исключения (graceful degradation)
                    return {
                        'status': 'error',
                        'query': query,
                        'results': [],
                        'sources': [],
                        'total_results': 0,
                        'search_time': search_time,
                        'error': error_msg
                    }

        except asyncio.TimeoutError:
            error_msg = f"WebSearch timeout ({self.timeout}s)"
            logger.error(f"⏱️ {error_msg}")

            return {
                'status': 'error',
                'query': query,
                'results': [],
                'sources': [],
                'total_results': 0,
                'search_time': self.timeout,
                'error': error_msg
            }

        except Exception as e:
            logger.error(f"❌ WebSearch error: {e}")

            return {
                'status': 'error',
                'query': query,
                'results': [],
                'sources': [],
                'total_results': 0,
                'search_time': 0,
                'error': str(e)
            }

    async def batch_websearch(
        self,
        queries: List[str],
        allowed_domains: Optional[List[str]] = None,
        max_results: int = 5,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Выполнить несколько WebSearch запросов параллельно

        Args:
            queries: Список поисковых запросов
            allowed_domains: Список разрешенных доменов
            max_results: Максимум результатов на запрос
            max_concurrent: Максимум одновременных запросов (чтобы не перегрузить API)

        Returns:
            Список результатов для каждого запроса:
            [
                {
                    'index': 0,
                    'query': 'query text',
                    'result': {...},  # Результат websearch()
                    'error': None или 'error message'
                }
            ]
        """
        logger.info(f"🔍 Batch WebSearch: {len(queries)} queries, max_concurrent={max_concurrent}")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _search_with_semaphore(query: str, index: int):
            async with semaphore:
                try:
                    logger.info(f"   [{index+1}/{len(queries)}] Searching: {query[:60]}...")
                    result = await self.websearch(
                        query=query,
                        allowed_domains=allowed_domains,
                        max_results=max_results
                    )

                    # Проверить есть ли ошибка в результате
                    error = result.get('error')
                    if error:
                        logger.warning(f"   [{index+1}/{len(queries)}] Warning: {error}")

                    return {
                        'index': index,
                        'query': query,
                        'result': result,
                        'error': error
                    }

                except Exception as e:
                    logger.error(f"   [{index+1}/{len(queries)}] Error: {e}")
                    return {
                        'index': index,
                        'query': query,
                        'result': {
                            'query': query,
                            'results': [],
                            'sources': [],
                            'total_results': 0,
                            'error': str(e)
                        },
                        'error': str(e)
                    }

        # Выполнить все запросы параллельно с ограничением
        tasks = [_search_with_semaphore(query, i) for i, query in enumerate(queries)]
        batch_results = await asyncio.gather(*tasks)

        # Отсортировать по индексу (чтобы сохранить порядок)
        batch_results.sort(key=lambda x: x['index'])

        # Подсчитать статистику
        successful = len([r for r in batch_results if r['error'] is None])
        failed = len([r for r in batch_results if r['error'] is not None])
        total_sources = sum(len(r['result'].get('sources', [])) for r in batch_results)
        total_results = sum(r['result'].get('total_results', 0) for r in batch_results)

        logger.info(f"✅ Batch WebSearch completed:")
        logger.info(f"   - Successful: {successful}/{len(queries)}")
        logger.info(f"   - Failed: {failed}/{len(queries)}")
        logger.info(f"   - Total sources: {total_sources}")
        logger.info(f"   - Total results: {total_results}")

        return batch_results

    async def check_health(self) -> bool:
        """
        Проверка здоровья API

        Returns:
            True если API доступен, False иначе
        """
        url = f"{self.base_url}/health"

        try:
            async with self.session.get(url) as response:
                healthy = response.status == 200

                if healthy:
                    logger.info("✅ Claude Code API здоров")
                else:
                    logger.warning(f"⚠️ Claude Code API нездоров: {response.status}")

                return healthy

        except Exception as e:
            logger.error(f"❌ Claude Code API недоступен: {e}")
            return False

    def get_debug_log(self) -> List[Dict]:
        """
        Получить лог отладки

        Returns:
            Список записей лога
        """
        return self.debug_log.copy()

    def clear_debug_log(self):
        """Очистить лог отладки"""
        self.debug_log.clear()
        logger.info("🧹 Debug log очищен")

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику использования клиента

        Returns:
            Dict со статистикой
        """
        websearch_logs = [log for log in self.debug_log if log.get("endpoint") == "/websearch"]

        total_requests = len(websearch_logs)
        successful = len([log for log in websearch_logs if log.get("status") == "success"])
        failed = len([log for log in websearch_logs if log.get("status") == "error"])

        total_results = sum(log.get("results_count", 0) for log in websearch_logs)
        total_sources = sum(log.get("sources_count", 0) for log in websearch_logs)

        avg_search_time = (
            sum(log.get("search_time", 0) for log in websearch_logs) / total_requests
            if total_requests > 0 else 0
        )

        return {
            "total_websearch_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_requests * 100) if total_requests > 0 else 0,
            "total_results": total_results,
            "total_sources": total_sources,
            "avg_results_per_query": total_results / total_requests if total_requests > 0 else 0,
            "avg_search_time": round(avg_search_time, 2)
        }


# Пример использования
async def example_researcher_websearch():
    """Пример использования для Researcher Agent"""

    api_key = os.getenv('CLAUDE_CODE_API_KEY', '1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732')

    async with ClaudeCodeWebSearchClient(api_key=api_key) as client:
        # 1. Проверка здоровья
        healthy = await client.check_health()
        print(f"API Health: {healthy}")

        # 2. Один запрос
        result = await client.websearch(
            query="Найди официальную статистику Росстат по доступности спортивных секций в Астраханской области за 2022-2024",
            allowed_domains=['rosstat.gov.ru', 'fedstat.ru', 'gov.ru'],
            max_results=5
        )

        print(f"\nSingle query result:")
        print(f"  - Query: {result['query'][:80]}...")
        print(f"  - Results: {result['total_results']}")
        print(f"  - Sources: {result['sources']}")
        print(f"  - Time: {result['search_time']:.2f}s")

        # 3. Batch запросы (как для Блока 1)
        block1_queries = [
            "Найди нацпроекты 2024-2030 связанные со спортом для детей",
            "Найди региональные программы Астраханской области по развитию детского спорта",
            "Найди 3 успешных кейса спортивных проектов для детей в РФ"
        ]

        batch_results = await client.batch_websearch(
            queries=block1_queries,
            allowed_domains=['rosstat.gov.ru', 'gov.ru', 'nationalprojects.ru'],
            max_results=5,
            max_concurrent=3
        )

        print(f"\nBatch search results:")
        for item in batch_results:
            result = item['result']
            print(f"  [{item['index']+1}] {item['query'][:60]}...")
            print(f"      → {result['total_results']} results, {len(result['sources'])} sources")

        # 4. Статистика
        stats = await client.get_statistics()
        print(f"\nStatistics:")
        print(f"  - Total requests: {stats['total_websearch_requests']}")
        print(f"  - Success rate: {stats['success_rate']:.1f}%")
        print(f"  - Avg results per query: {stats['avg_results_per_query']:.1f}")
        print(f"  - Avg search time: {stats['avg_search_time']:.2f}s")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_researcher_websearch())
