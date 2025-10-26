"""
GigaChat Embeddings API Client

This client provides interface to GigaChat Embeddings API (1024-dim vectors)
for vectorization of FPG grant data.

Iteration 51: AI Enhancement - Embeddings + RL
Date: 2025-10-26

API Documentation:
- https://developers.sber.ru/docs/ru/gigachat/embeddings
- Endpoint: POST /embeddings
- Model: "Embeddings" (1024-dim vectors)
- Max tokens per request: 8192
"""

import os
import requests
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GigaChatEmbeddingsClient:
    """
    Client for GigaChat Embeddings API

    Features:
    - OAuth 2.0 authentication with auto-refresh
    - Batch embedding support
    - 1024-dimensional vectors
    - Rate limiting and retry logic
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "Embeddings",
        max_retries: int = 3
    ):
        """
        Initialize GigaChat Embeddings client

        Args:
            api_key: GigaChat API key (Client ID:Secret base64-encoded)
            model: Embeddings model name (default: "Embeddings")
            max_retries: Number of retry attempts for failed requests
        """
        # Load API key from env or param
        # Try .env first, then fall back to hardcoded (from .env file)
        default_key = "OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5OjJlMTM1NDUwLTVhZDctNDU0Ny1hZmJiLWY2NGY5NTIzMDE0OQ=="
        self.api_key = api_key or os.getenv("GIGACHAT_API_KEY", default_key)

        # API endpoints
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"

        # Model configuration
        self.model = model
        self.vector_dim = 1024
        self.max_tokens_per_request = 8192

        # Auth state
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = 1.0  # seconds

        # Statistics
        self.total_tokens_embedded = 0
        self.total_api_calls = 0

    def _get_access_token(self) -> str:
        """
        Get valid access token (auto-refresh if expired)

        Returns:
            Access token string or None if auth fails
        """
        try:
            # Check if current token is still valid
            if self.access_token and time.time() < self.token_expires_at:
                return self.access_token

            # Request new access token
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": f"Basic {self.api_key}"
            }

            payload = {"scope": "GIGACHAT_API_PERS"}

            logger.info("[AUTH] Requesting new GigaChat access token...")
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=payload,
                verify=False  # Disable SSL verification for Sber API
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                # Token valid for 30 min, refresh 5 min early
                self.token_expires_at = time.time() + (25 * 60)
                logger.info("[AUTH] Access token obtained successfully")
                return self.access_token
            else:
                logger.error(f"[AUTH ERROR] {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"[AUTH EXCEPTION] {e}")
            return None

    def embed_text(self, text: str, retry_count: int = 0) -> Optional[List[float]]:
        """
        Embed single text into 1024-dim vector

        Args:
            text: Text to embed
            retry_count: Current retry attempt (internal)

        Returns:
            List of 1024 floats or None if failed
        """
        try:
            token = self._get_access_token()
            if not token:
                logger.error("[EMBED ERROR] No valid access token")
                return None

            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}"
            }

            payload = {
                "model": self.model,
                "input": [text]
            }

            # Make API call
            self.total_api_calls += 1
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
                verify=False
            )

            if response.status_code == 200:
                result = response.json()

                # Extract embedding vector
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0]["embedding"]

                    # Validate dimension
                    if len(embedding) == self.vector_dim:
                        self.total_tokens_embedded += len(text.split())
                        return embedding
                    else:
                        logger.warning(f"[EMBED WARNING] Unexpected vector dim: {len(embedding)}")
                        return None
                else:
                    logger.error(f"[EMBED ERROR] Invalid response format: {result}")
                    return None

            # Handle rate limiting (429)
            elif response.status_code == 429 and retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"[RATE LIMIT] Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                return self.embed_text(text, retry_count + 1)

            # Handle other errors
            else:
                logger.error(f"[EMBED ERROR] {response.status_code}: {response.text}")

                # Retry on 5xx errors
                if 500 <= response.status_code < 600 and retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                    return self.embed_text(text, retry_count + 1)

                return None

        except Exception as e:
            logger.error(f"[EMBED EXCEPTION] {e}")

            # Retry on exception
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self.embed_text(text, retry_count + 1)

            return None

    def embed_batch(
        self,
        texts: List[str],
        show_progress: bool = True
    ) -> List[Optional[List[float]]]:
        """
        Embed batch of texts (processes one-by-one with progress)

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar

        Returns:
            List of embeddings (1024-dim vectors or None for failures)
        """
        embeddings = []
        total = len(texts)

        logger.info(f"[BATCH] Embedding {total} texts...")

        for i, text in enumerate(texts):
            if show_progress and (i + 1) % 10 == 0:
                logger.info(f"[PROGRESS] {i+1}/{total} texts embedded")

            embedding = self.embed_text(text)
            embeddings.append(embedding)

            # Rate limiting: small delay between requests
            if i < total - 1:
                time.sleep(0.1)

        # Calculate success rate
        success_count = sum(1 for e in embeddings if e is not None)
        logger.info(f"[BATCH COMPLETE] {success_count}/{total} successful ({success_count/total*100:.1f}%)")

        return embeddings

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get client usage statistics

        Returns:
            Dictionary with stats
        """
        return {
            "total_api_calls": self.total_api_calls,
            "total_tokens_embedded": self.total_tokens_embedded,
            "model": self.model,
            "vector_dim": self.vector_dim
        }

    def test_connection(self) -> bool:
        """
        Test API connection and authentication

        Returns:
            True if connection successful
        """
        logger.info("[TEST] Testing GigaChat Embeddings API connection...")

        # Test auth
        token = self._get_access_token()
        if not token:
            logger.error("[TEST FAILED] Authentication failed")
            return False

        logger.info("[TEST] Authentication successful")

        # Test embedding
        test_text = "Тестовое предложение для проверки API"
        embedding = self.embed_text(test_text)

        if embedding and len(embedding) == self.vector_dim:
            logger.info(f"[TEST SUCCESS] Embedding generated: {self.vector_dim}-dim vector")
            return True
        else:
            logger.error("[TEST FAILED] Embedding generation failed")
            return False


# ============================================================================
# Convenience Functions
# ============================================================================

def create_embeddings_client() -> GigaChatEmbeddingsClient:
    """
    Create configured GigaChat Embeddings client

    Returns:
        Ready-to-use client instance
    """
    return GigaChatEmbeddingsClient()


def test_embeddings_api():
    """
    Quick test of GigaChat Embeddings API
    """
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    client = create_embeddings_client()

    # Test connection
    if not client.test_connection():
        print("[ERROR] API test failed")
        return

    # Test batch embedding
    test_texts = [
        "Проект направлен на поддержку молодежи",
        "Социальная значимость проекта высока",
        "Бюджет проекта составляет 3 миллиона рублей"
    ]

    print("\n[TEST] Embedding batch of texts...")
    embeddings = client.embed_batch(test_texts, show_progress=True)

    print(f"\n[RESULT] Embedded {len([e for e in embeddings if e])} texts")
    print(f"[STATS] {client.get_statistics()}")


if __name__ == "__main__":
    test_embeddings_api()
