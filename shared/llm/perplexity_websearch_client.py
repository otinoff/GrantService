#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Perplexity WebSearch Client for Researcher Agent
Drop-in replacement for Claude Code WebSearch

API: https://api.perplexity.ai
Model: sonar (with web search capabilities)
Cost: ~$0.01 per query (includes search)

Author: AI Integration Specialist
Date: 2025-10-11
"""

import aiohttp
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class PerplexityWebSearchClient:
    """Async client for WebSearch using Perplexity API (drop-in replacement for Claude Code)"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.perplexity.ai",
        timeout: int = 120  # Same as Claude Code client
    ):
        """
        Initialize Perplexity WebSearch client

        Args:
            api_key: Perplexity API key (or from PERPLEXITY_API_KEY env)
            base_url: Base URL for Perplexity API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY', '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')
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.debug_log = []

        logger.info(f"[OK] PerplexityWebSearchClient initialized: {base_url}")

    async def __aenter__(self):
        """Create HTTP session on context enter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)

        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout_config
        )

        logger.info("[OK] PerplexityWebSearchClient session created")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close HTTP session on context exit"""
        if self.session:
            await self.session.close()
            logger.info("[CLOSE] PerplexityWebSearchClient session closed")

    async def websearch(
        self,
        query: str,
        allowed_domains: Optional[List[str]] = None,
        max_results: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute WebSearch query using Perplexity API

        Compatible with ClaudeCodeWebSearchClient.websearch() interface

        Args:
            query: Search query
            allowed_domains: List of allowed domains (e.g. ['rosstat.gov.ru', 'gov.ru'])
            max_results: Maximum results (Perplexity returns ~5-10 sources automatically)
            session_id: Session ID for context (optional, ignored by Perplexity)

        Returns:
            {
                'status': 'success',
                'query': 'original query',
                'results': [
                    {
                        'title': 'Result title',
                        'url': 'https://...',
                        'snippet': 'Text snippet',
                        'source': 'rosstat.gov.ru',
                        'relevance_score': 0.95
                    }
                ],
                'sources': ['rosstat.gov.ru', 'government.ru'],
                'total_results': 5,
                'search_time': 1.23,
                'content': 'Full Perplexity response text',
                'cost': 0.01  # Approximate cost
            }
        """
        url = f"{self.base_url}/chat/completions"

        # Build search prompt with domain filtering if requested
        search_prompt = query
        if allowed_domains:
            domains_str = ', '.join(allowed_domains)
            search_prompt = f"{query}\n\nИСПОЛЬЗУЙ только официальные источники: {domains_str}"

        payload = {
            "model": "sonar",  # Perplexity's search model
            "messages": [
                {
                    "role": "system",
                    "content": "Ты эксперт-аналитик. Найди актуальную информацию в интернете и предоставь детальный ответ с указанием источников."
                },
                {
                    "role": "user",
                    "content": search_prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.2,
            "search_mode": "web"
        }

        # Log request
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/chat/completions",
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

                    # Extract content
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # Extract citations/sources from Perplexity response
                    citations = data.get("citations", [])

                    # Parse sources from response if no citations field
                    if not citations:
                        citations = self._extract_citations_from_content(content)

                    # Build results array in Claude Code format
                    results = []
                    sources = []

                    for idx, citation in enumerate(citations[:max_results]):
                        if isinstance(citation, str):
                            # Simple URL citation
                            url_value = citation
                            domain = self._extract_domain(url_value)
                            results.append({
                                'title': f'Source {idx+1}',
                                'url': url_value,
                                'snippet': content[:200] + "...",
                                'source': domain,
                                'relevance_score': 0.9 - (idx * 0.05)  # Decreasing relevance
                            })
                            sources.append(domain)
                        elif isinstance(citation, dict):
                            # Rich citation with metadata
                            url_value = citation.get('url', '')
                            domain = self._extract_domain(url_value)
                            results.append({
                                'title': citation.get('title', f'Source {idx+1}'),
                                'url': url_value,
                                'snippet': citation.get('snippet', content[:200]),
                                'source': domain,
                                'relevance_score': citation.get('relevance', 0.9)
                            })
                            sources.append(domain)

                    # Remove duplicate sources
                    sources = list(set(sources))

                    # Calculate approximate cost (Perplexity search query)
                    usage = data.get("usage", {})
                    cost = self._calculate_cost(usage)

                    result_data = {
                        'status': 'success',
                        'query': query,
                        'results': results,
                        'sources': sources,
                        'total_results': len(results),
                        'search_time': search_time,
                        'content': content,  # Full Perplexity response
                        'cost': cost,
                        'usage': usage,
                        'session_id': session_id
                    }

                    log_entry.update({
                        "status": "success",
                        "results_count": result_data['total_results'],
                        "sources_count": len(sources),
                        "search_time": search_time,
                        "cost": cost
                    })
                    self.debug_log.append(log_entry)

                    logger.info(f"[OK] Perplexity WebSearch: '{query[:50]}...' -> {result_data['total_results']} results, {len(sources)} sources ({search_time:.2f}s, ${cost:.4f})")
                    return result_data

                else:
                    error_msg = f"Perplexity API error: {response.status} - {response_text[:200]}"
                    logger.error(f"[ERROR] {error_msg}")

                    log_entry.update({
                        "status": "error",
                        "error": response_text[:200],
                        "status_code": response.status
                    })
                    self.debug_log.append(log_entry)

                    # Return empty result (graceful degradation)
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
            error_msg = f"Perplexity timeout ({self.timeout}s)"
            logger.error(f"[TIMEOUT] {error_msg}")

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
            logger.error(f"[ERROR] Perplexity WebSearch error: {e}")

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
        Execute multiple WebSearch queries in parallel

        Args:
            queries: List of search queries
            allowed_domains: List of allowed domains
            max_results: Maximum results per query
            max_concurrent: Maximum concurrent requests (to avoid rate limits)

        Returns:
            List of results for each query
        """
        logger.info(f"[BATCH] Perplexity WebSearch: {len(queries)} queries, max_concurrent={max_concurrent}")

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

        # Execute all queries in parallel with limit
        tasks = [_search_with_semaphore(query, i) for i, query in enumerate(queries)]
        batch_results = await asyncio.gather(*tasks)

        # Sort by index (preserve order)
        batch_results.sort(key=lambda x: x['index'])

        # Calculate statistics
        successful = len([r for r in batch_results if r['error'] is None])
        failed = len([r for r in batch_results if r['error'] is not None])
        total_sources = sum(len(r['result'].get('sources', [])) for r in batch_results)
        total_results = sum(r['result'].get('total_results', 0) for r in batch_results)
        total_cost = sum(r['result'].get('cost', 0) for r in batch_results)

        logger.info(f"[OK] Batch Perplexity WebSearch completed:")
        logger.info(f"   - Successful: {successful}/{len(queries)}")
        logger.info(f"   - Failed: {failed}/{len(queries)}")
        logger.info(f"   - Total sources: {total_sources}")
        logger.info(f"   - Total results: {total_results}")
        logger.info(f"   - Total cost: ${total_cost:.4f}")

        return batch_results

    async def check_health(self) -> bool:
        """
        Check Perplexity API health

        Returns:
            True if API is available, False otherwise
        """
        try:
            # Test with simple query
            test_payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }

            url = f"{self.base_url}/chat/completions"
            async with self.session.post(url, json=test_payload) as response:
                healthy = response.status == 200

                if healthy:
                    logger.info("[OK] Perplexity API healthy")
                else:
                    logger.warning(f"[WARN] Perplexity API unhealthy: {response.status}")

                return healthy

        except Exception as e:
            logger.error(f"[ERROR] Perplexity API unavailable: {e}")
            return False

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"

    def _extract_citations_from_content(self, content: str) -> List[str]:
        """Extract URLs from content (fallback if no citations field)"""
        import re
        urls = re.findall(r'https?://[^\s\)]+', content)
        return urls[:10]  # Limit to 10

    def _calculate_cost(self, usage: Dict) -> float:
        """
        Calculate approximate query cost

        Perplexity pricing:
        - Input: $1 per 1M tokens
        - Output: $1 per 1M tokens
        - Search: ~$5 per 1K queries = $0.005 per query

        Average search query: ~$0.01 (includes tokens + search)
        """
        try:
            # Perplexity search queries cost ~$0.005-0.01 per query
            base_search_cost = 0.01

            # Token costs (minimal)
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            token_cost = ((prompt_tokens + completion_tokens) / 1_000_000) * 1.0

            total_cost = base_search_cost + token_cost
            return round(total_cost, 6)

        except Exception as e:
            logger.error(f"[ERROR] Cost calculation error: {e}")
            return 0.01  # Default estimate

    def get_debug_log(self) -> List[Dict]:
        """Get debug log"""
        return self.debug_log.copy()

    def clear_debug_log(self):
        """Clear debug log"""
        self.debug_log.clear()
        logger.info("[CLEAR] Debug log cleared")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        search_logs = [log for log in self.debug_log if log.get("endpoint") == "/chat/completions"]

        total_requests = len(search_logs)
        successful = len([log for log in search_logs if log.get("status") == "success"])
        failed = len([log for log in search_logs if log.get("status") == "error"])

        total_results = sum(log.get("results_count", 0) for log in search_logs)
        total_sources = sum(log.get("sources_count", 0) for log in search_logs)
        total_cost = sum(log.get("cost", 0) for log in search_logs)

        avg_search_time = (
            sum(log.get("search_time", 0) for log in search_logs) / total_requests
            if total_requests > 0 else 0
        )

        return {
            "provider": "Perplexity API",
            "total_websearch_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_requests * 100) if total_requests > 0 else 0,
            "total_results": total_results,
            "total_sources": total_sources,
            "total_cost": round(total_cost, 4),
            "avg_cost_per_query": round(total_cost / total_requests, 4) if total_requests > 0 else 0,
            "avg_results_per_query": total_results / total_requests if total_requests > 0 else 0,
            "avg_search_time": round(avg_search_time, 2)
        }


# Example usage
async def example_perplexity_websearch():
    """Example usage for testing"""

    async with PerplexityWebSearchClient() as client:
        # 1. Health check
        healthy = await client.check_health()
        print(f"API Health: {healthy}")

        # 2. Single query
        result = await client.websearch(
            query="Найди официальную статистику по доступности спортивных секций в России 2024",
            allowed_domains=['rosstat.gov.ru', 'gov.ru'],
            max_results=5
        )

        print(f"\nSingle query result:")
        print(f"  - Query: {result['query'][:80]}...")
        print(f"  - Results: {result['total_results']}")
        print(f"  - Sources: {result['sources']}")
        print(f"  - Time: {result['search_time']:.2f}s")
        print(f"  - Cost: ${result.get('cost', 0):.4f}")

        # 3. Statistics
        stats = await client.get_statistics()
        print(f"\nStatistics:")
        print(f"  - Total requests: {stats['total_websearch_requests']}")
        print(f"  - Success rate: {stats['success_rate']:.1f}%")
        print(f"  - Total cost: ${stats['total_cost']:.4f}")


if __name__ == "__main__":
    asyncio.run(example_perplexity_websearch())
