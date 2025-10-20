#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSearch Provider Router
=========================

Router for Claude Code CLI WebSearch ONLY.

Architecture:
- Database-Driven: Reads provider from ai_agent_settings.config
- NO Automatic Fallback: Claude Code CLI is the ONLY provider
- Failure = Call @claude-code-expert agent to fix
- $200 subscription active - use it exclusively

Policy:
- Primary: Claude Code CLI WebSearch (ONLY option)
- Fallback: NONE - call @claude-code-expert to restore service
- Perplexity/GigaChat: ONLY for hardcoded production emergency

Author: AI Integration Specialist
Date: 2025-10-13
Version: 2.0 (No Fallback Policy)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import asyncio

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.llm.claude_code_websearch_client import ClaudeCodeWebSearchClient

# Setup logging
logger = logging.getLogger(__name__)


class ClaudeCodeServiceException(Exception):
    """
    Exception raised when Claude Code CLI service fails

    This exception signals that @claude-code-expert agent should be called
    to restore Claude Code CLI service.

    Attributes:
        message: Error description
        provider: Provider that failed (claude_code)
        error_type: Type of error (auth, network, timeout, etc.)
        recovery_action: Suggested recovery action
    """
    def __init__(self, message: str, error_type: str = "unknown", recovery_action: str = None):
        self.message = message
        self.provider = "claude_code"
        self.error_type = error_type
        self.recovery_action = recovery_action or "Call @claude-code-expert to restore Claude Code CLI service"
        super().__init__(self.message)


class WebSearchRouter:
    """
    Router for automatic WebSearch provider selection

    Reads configuration from ai_agent_settings table:
    - websearch_provider: Primary provider (perplexity | claude_code)
    - websearch_fallback: Fallback provider

    Usage:
        async with WebSearchRouter(db) as router:
            results = await router.websearch(query="test query")

    Features:
    - Automatic provider selection based on DB settings
    - Graceful fallback on provider failure
    - Compatible interface for both providers
    - Health check support
    """

    def __init__(self, db):
        """
        Initialize WebSearchRouter (Claude Code CLI ONLY)

        Args:
            db: Database connection or session manager
        """
        self.db = db
        self.claude_websearch_client: Optional[ClaudeCodeWebSearchClient] = None
        self.primary_provider: str = 'claude_code'  # ONLY Claude Code

        logger.info("[WebSearchRouter] Initialized (Claude Code CLI ONLY policy)")

    async def __aenter__(self):
        """
        Async context manager entry

        Initializes Claude Code CLI WebSearch client ONLY
        """
        try:
            # Initialize ONLY Claude Code client
            self.claude_websearch_client = ClaudeCodeWebSearchClient()
            await self.claude_websearch_client.__aenter__()
            logger.info("[WebSearchRouter] ✅ Claude Code WebSearch client initialized")
            logger.info("[WebSearchRouter] Policy: NO fallback - Claude Code CLI ONLY")

        except Exception as e:
            error_msg = f"Failed to initialize Claude Code CLI WebSearch: {e}"
            logger.error(f"[WebSearchRouter] {error_msg}")
            raise ClaudeCodeServiceException(
                message=error_msg,
                error_type="initialization",
                recovery_action="Call @claude-code-expert to check: 1) Wrapper server status 2) OAuth token 3) Network connectivity"
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit

        Cleanup Claude Code client
        """
        try:
            if self.claude_websearch_client:
                await self.claude_websearch_client.__aexit__(exc_type, exc_val, exc_tb)
                logger.info("[WebSearchRouter] Claude Code client closed")
        except Exception as e:
            logger.warning(f"[WebSearchRouter] Error closing Claude Code client: {e}")

    async def websearch(
        self,
        query: str,
        allowed_domains: Optional[List[str]] = None,
        max_results: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute WebSearch query via Claude Code CLI ONLY

        Args:
            query: Search query
            allowed_domains: Optional list of allowed domains (e.g., ['gov.ru', 'rosstat.gov.ru'])
            max_results: Maximum number of results to return
            session_id: Optional session ID for tracking

        Returns:
            Dict with search results in unified format:
            {
                'status': 'success',
                'query': str,
                'results': List[Dict],
                'sources': List[str],
                'total_results': int,
                'search_time': float,
                'cost': float,
                'provider': 'claude_code'
            }

        Raises:
            ClaudeCodeServiceException: If Claude Code CLI fails (call @claude-code-expert)
        """
        try:
            if not self.claude_websearch_client:
                raise ClaudeCodeServiceException(
                    message="Claude Code WebSearch client not initialized",
                    error_type="not_initialized",
                    recovery_action="Call @claude-code-expert to restore Claude Code CLI"
                )

            # Execute via Claude Code CLI
            result = await self.claude_websearch_client.websearch(
                query=query,
                allowed_domains=allowed_domains,
                max_results=max_results
            )

            # Add provider info
            result['provider'] = 'claude_code'
            logger.info(f"[WebSearchRouter] ✅ Success with Claude Code CLI")
            return result

        except Exception as e:
            error_msg = f"Claude Code CLI WebSearch failed: {e}"
            logger.error(f"[WebSearchRouter] {error_msg}")

            # NO FALLBACK - raise exception to trigger @claude-code-expert
            raise ClaudeCodeServiceException(
                message=error_msg,
                error_type="websearch_failed",
                recovery_action="Call @claude-code-expert to diagnose: 1) Check wrapper server (178.236.17.55:8000) 2) Verify OAuth token 3) Test connectivity"
            )


    async def batch_websearch(
        self,
        queries: List[str],
        allowed_domains: Optional[List[str]] = None,
        max_results: int = 5,
        max_concurrent: int = 3,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple WebSearch queries in parallel

        Args:
            queries: List of search queries
            allowed_domains: Optional list of allowed domains
            max_results: Maximum results per query
            max_concurrent: Maximum concurrent requests
            session_id: Optional session ID for tracking

        Returns:
            List of result dicts, one per query
        """
        logger.info(f"[WebSearchRouter] Batch search: {len(queries)} queries, max_concurrent={max_concurrent}")

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        async def search_with_semaphore(query: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.websearch(
                    query=query,
                    allowed_domains=allowed_domains,
                    max_results=max_results,
                    session_id=session_id
                )

        # Execute all queries concurrently with rate limiting
        results = await asyncio.gather(
            *[search_with_semaphore(q) for q in queries],
            return_exceptions=True
        )

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[WebSearchRouter] Query {i} failed: {result}")
                processed_results.append({
                    'status': 'error',
                    'query': queries[i],
                    'results': [],
                    'sources': [],
                    'total_results': 0,
                    'error': str(result),
                    'provider': 'none'
                })
            else:
                processed_results.append(result)

        # Calculate stats
        successful = sum(1 for r in processed_results if r.get('status') == 'success')
        logger.info(f"[WebSearchRouter] Batch complete: {successful}/{len(queries)} successful")

        return processed_results

    async def check_health(self) -> bool:
        """
        Check health of Claude Code WebSearch service

        Returns:
            True if Claude Code is healthy, False otherwise
        """
        try:
            if not self.claude_websearch_client:
                return False
            return await self.claude_websearch_client.check_health()

        except Exception as e:
            logger.error(f"[WebSearchRouter] Health check failed: {e}")
            return False

    def get_current_provider(self) -> str:
        """Get current provider (always 'claude_code')"""
        return self.primary_provider


# Example usage and testing
async def main():
    """Test WebSearchRouter"""
    import sys
    from pathlib import Path

    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    # Mock database (for testing without actual DB)
    class MockDB:
        pass

    db = MockDB()

    print("=" * 80)
    print("WebSearchRouter Test")
    print("=" * 80)

    try:
        async with WebSearchRouter(db) as router:
            print(f"\n[INFO] Provider: {router.get_current_provider()} (Claude Code CLI ONLY)")

            # Health check
            print("\n[TEST] Health check...")
            healthy = await router.check_health()
            print(f"[RESULT] Healthy: {healthy}")

            # Single query test
            print("\n[TEST] Single query...")
            result = await router.websearch(
                query="статистика инвалидов России 2024",
                allowed_domains=['gov.ru', 'rosstat.gov.ru'],
                max_results=5
            )

            print(f"[RESULT] Status: {result['status']}")
            print(f"[RESULT] Provider: {result.get('provider', 'unknown')}")
            print(f"[RESULT] Total results: {result['total_results']}")
            print(f"[RESULT] Sources: {len(result['sources'])}")
            if result.get('cost'):
                print(f"[RESULT] Cost: ${result['cost']:.4f}")

            if result['results']:
                print(f"\n[SAMPLE] First result:")
                first = result['results'][0]
                print(f"  Title: {first.get('title', 'N/A')[:60]}...")
                print(f"  URL: {first.get('url', 'N/A')}")
                print(f"  Source: {first.get('source', 'N/A')}")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Test complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
