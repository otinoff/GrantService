"""
Production Smoke Tests - Iteration 26.2

Быстрые тесты для проверки работоспособности production системы.
Выполняются после каждого деплоя для проверки базового здоровья.

Тесты:
1. Service Running - systemd service активен
2. PostgreSQL Connection - БД доступна
3. Qdrant Connection - Vector DB доступна
4. Telegram API - Бот может подключиться к Telegram
5. Environment Variables - Все необходимые env vars загружены

Expected time: <10 seconds
"""

import pytest
import subprocess
import os
import psycopg2
from qdrant_client import QdrantClient
import httpx


class TestProductionSmoke:
    """Smoke tests для production окружения"""

    def test_service_running(self):
        """
        Test: Systemd service должен быть running

        Проверяет что grantservice-bot.service активен и работает
        """
        result = subprocess.run(
            ["systemctl", "is-active", "grantservice-bot"],
            capture_output=True,
            text=True
        )

        assert result.stdout.strip() == "active", (
            f"Service not running. Status: {result.stdout.strip()}"
        )
        print("✅ Service is running")

    def test_postgresql_connection(self):
        """
        Test: PostgreSQL должен быть доступен

        Проверяет подключение к БД и наличие основных таблиц
        """
        # Load .env
        from dotenv import load_dotenv
        load_dotenv("/var/GrantService/config/.env")

        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "grantservice")
        db_user = os.getenv("DB_USER", "grantservice_user")
        db_password = os.getenv("DB_PASSWORD")

        assert db_password, "DB_PASSWORD not set in environment"

        # Try to connect
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=3
        )

        cursor = conn.cursor()

        # Check if main tables exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'users'
            );
        """)
        users_table_exists = cursor.fetchone()[0]

        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'interview_sessions'
            );
        """)
        sessions_table_exists = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        assert users_table_exists, "users table does not exist"
        assert sessions_table_exists, "interview_sessions table does not exist"

        print(f"✅ PostgreSQL connected: {db_host}:{db_port}/{db_name}")
        print(f"✅ Tables exist: users, interview_sessions")

    def test_qdrant_connection(self):
        """
        Test: Qdrant должен быть доступен

        Проверяет подключение к Qdrant и наличие коллекций
        """
        try:
            client = QdrantClient(host="localhost", port=6333, timeout=3)

            # Get collections
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]

            # Check for expected collections
            expected_collections = ["fpg_questions", "knowledge_sections"]

            for coll_name in expected_collections:
                assert coll_name in collection_names, (
                    f"Collection '{coll_name}' not found. "
                    f"Available: {collection_names}"
                )

            # Get collection info
            fpg_info = client.get_collection("fpg_questions")
            knowledge_info = client.get_collection("knowledge_sections")

            print(f"✅ Qdrant connected: localhost:6333")
            print(f"✅ Collection fpg_questions: {fpg_info.points_count} points")
            print(f"✅ Collection knowledge_sections: {knowledge_info.points_count} points")

        except Exception as e:
            pytest.fail(f"Qdrant connection failed: {str(e)}")

    def test_telegram_api_polling(self):
        """
        Test: Telegram API должен быть доступен

        Проверяет что бот может подключиться к Telegram API
        """
        from dotenv import load_dotenv
        load_dotenv("/var/GrantService/config/.env")

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        assert bot_token, "TELEGRAM_BOT_TOKEN not set in environment"

        # Try to get bot info
        url = f"https://api.telegram.org/bot{bot_token}/getMe"

        try:
            response = httpx.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            assert data["ok"], f"Telegram API returned ok=False: {data}"

            bot_info = data["result"]
            print(f"✅ Telegram API connected: @{bot_info['username']}")
            print(f"✅ Bot name: {bot_info['first_name']}")

        except httpx.HTTPError as e:
            pytest.fail(f"Telegram API request failed: {str(e)}")

    def test_environment_loaded(self):
        """
        Test: Environment variables должны быть загружены

        Проверяет наличие всех критичных env variables
        """
        from dotenv import load_dotenv
        load_dotenv("/var/GrantService/config/.env")

        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "DB_HOST",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "ANTHROPIC_API_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        assert not missing_vars, (
            f"Missing environment variables: {missing_vars}"
        )

        print(f"✅ All {len(required_vars)} required env vars loaded")


if __name__ == "__main__":
    # Run smoke tests
    pytest.main([__file__, "-v", "-s"])
