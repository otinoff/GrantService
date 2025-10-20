"""
Claude Code API Client для GrantService

Клиент для работы с Claude Code API Wrapper
API: http://178.236.17.55:8000
"""

import aiohttp
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClaudeCodeClient:
    """Асинхронный клиент для работы с Claude Code API Wrapper"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://178.236.17.55:8000",
        default_model: str = "sonnet",
        default_temperature: float = 0.7,
        timeout: int = 60
    ):
        """
        Инициализация клиента

        Args:
            api_key: API ключ для авторизации
            base_url: Базовый URL API
            default_model: Модель по умолчанию (sonnet/opus)
            default_temperature: Температура генерации (0.0-1.0)
            timeout: Таймаут запросов в секундах
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.debug_log = []

        logger.info(f"🔧 ClaudeCodeClient инициализирован: {base_url}, model={default_model}")

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

        logger.info("✅ ClaudeCodeClient сессия создана")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие HTTP сессии при выходе из контекста"""
        if self.session:
            await self.session.close()
            logger.info("🔒 ClaudeCodeClient сессия закрыта")

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Чат с Claude

        Args:
            message: Сообщение для Claude
            session_id: ID сессии для сохранения контекста (опционально)
            model: Модель Claude (sonnet/opus, по умолчанию sonnet)
            temperature: Температура генерации (0.0-1.0, по умолчанию 0.7)
            max_tokens: Максимум токенов в ответе (1-8000, опционально)

        Returns:
            Ответ Claude в виде строки

        Raises:
            Exception: При ошибке API
        """
        url = f"{self.base_url}/chat"

        payload = {
            "message": message,
            "model": model or self.default_model,
            "temperature": temperature or self.default_temperature,
        }

        if session_id:
            payload["session_id"] = session_id
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Логирование запроса
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/chat",
            "model": payload["model"],
            "message_length": len(message),
            "has_session": session_id is not None
        }
        self.debug_log.append(log_entry)

        try:
            async with self.session.post(url, json=payload) as response:
                response_text = await response.text()

                if response.status == 200:
                    data = json.loads(response_text)
                    result = data.get("response", "")

                    log_entry.update({
                        "status": "success",
                        "response_length": len(result),
                        "session_id": data.get("session_id")
                    })
                    self.debug_log.append(log_entry)

                    logger.info(f"✅ Claude chat: {len(message)} chars → {len(result)} chars")
                    return result

                else:
                    error_msg = f"Claude API error: {response.status} - {response_text}"
                    logger.error(error_msg)

                    log_entry.update({
                        "status": "error",
                        "error": response_text,
                        "status_code": response.status
                    })
                    self.debug_log.append(log_entry)

                    raise Exception(error_msg)

        except asyncio.TimeoutError:
            error_msg = f"Claude API timeout ({self.timeout}s)"
            logger.error(error_msg)
            raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Claude chat error: {e}")
            raise

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Выполнение кода через Claude Code

        Args:
            code: Код для выполнения
            language: Язык программирования (python по умолчанию)
            session_id: ID сессии (опционально)

        Returns:
            Dict с результатом выполнения:
            {
                "result": "output",
                "session_id": "...",
                "language": "python",
                "timestamp": "2025-10-05T...",
                "status": "success"
            }

        Raises:
            Exception: При ошибке выполнения
        """
        url = f"{self.base_url}/code"

        payload = {
            "code": code,
            "language": language
        }

        if session_id:
            payload["session_id"] = session_id

        # Логирование запроса
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/code",
            "language": language,
            "code_length": len(code),
            "has_session": session_id is not None
        }
        self.debug_log.append(log_entry)

        try:
            async with self.session.post(url, json=payload) as response:
                response_text = await response.text()

                if response.status == 200:
                    data = json.loads(response_text)

                    log_entry.update({
                        "status": "success",
                        "result_length": len(data.get("result", "")),
                        "session_id": data.get("session_id")
                    })
                    self.debug_log.append(log_entry)

                    logger.info(f"✅ Code execution: {language}, {len(code)} chars")
                    return data

                else:
                    error_msg = f"Code execution error: {response.status} - {response_text}"
                    logger.error(error_msg)

                    log_entry.update({
                        "status": "error",
                        "error": response_text,
                        "status_code": response.status
                    })
                    self.debug_log.append(log_entry)

                    raise Exception(error_msg)

        except asyncio.TimeoutError:
            error_msg = f"Code execution timeout ({self.timeout}s)"
            logger.error(error_msg)
            raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            raise

    async def list_sessions(self) -> List[Dict]:
        """
        Получить список активных сессий

        Returns:
            Список сессий
        """
        url = f"{self.base_url}/sessions"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    sessions = await response.json()
                    logger.info(f"📋 Получено сессий: {len(sessions)}")
                    return sessions
                else:
                    logger.warning(f"Не удалось получить сессии: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    async def delete_session(self, session_id: str) -> bool:
        """
        Удалить сессию

        Args:
            session_id: ID сессии для удаления

        Returns:
            True если успешно, False иначе
        """
        url = f"{self.base_url}/sessions/{session_id}"

        try:
            async with self.session.delete(url) as response:
                success = response.status == 200

                if success:
                    logger.info(f"🗑️ Сессия удалена: {session_id}")
                else:
                    logger.warning(f"Не удалось удалить сессию {session_id}: {response.status}")

                return success

        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    async def list_models(self) -> List[str]:
        """
        Получить список доступных моделей

        Returns:
            Список названий моделей
        """
        url = f"{self.base_url}/models"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    models = await response.json()
                    logger.info(f"📚 Доступные модели: {models}")
                    return models
                else:
                    logger.warning(f"Не удалось получить модели: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

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
        total_requests = len(self.debug_log)
        successful = len([log for log in self.debug_log if log.get("status") == "success"])
        failed = len([log for log in self.debug_log if log.get("status") == "error"])

        chat_requests = len([log for log in self.debug_log if log.get("endpoint") == "/chat"])
        code_requests = len([log for log in self.debug_log if log.get("endpoint") == "/code"])

        return {
            "total_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_requests * 100) if total_requests > 0 else 0,
            "chat_requests": chat_requests,
            "code_requests": code_requests
        }


# Синхронная обёртка для совместимости с существующим кодом
class ClaudeCodeClientSync:
    """Синхронная обёртка над асинхронным клиентом"""

    def __init__(self, *args, **kwargs):
        self.async_client = ClaudeCodeClient(*args, **kwargs)
        self.loop = asyncio.get_event_loop()

    def chat(self, message: str, **kwargs) -> str:
        """Синхронный чат"""
        async def _chat():
            async with self.async_client as client:
                return await client.chat(message, **kwargs)

        return self.loop.run_until_complete(_chat())

    def execute_code(self, code: str, **kwargs) -> Dict[str, Any]:
        """Синхронное выполнение кода"""
        async def _execute():
            async with self.async_client as client:
                return await client.execute_code(code, **kwargs)

        return self.loop.run_until_complete(_execute())

    def check_health(self) -> bool:
        """Синхронная проверка здоровья"""
        async def _health():
            async with self.async_client as client:
                return await client.check_health()

        return self.loop.run_until_complete(_health())


# Пример использования
async def example_usage():
    """Пример использования клиента"""

    api_key = "1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732"

    async with ClaudeCodeClient(api_key=api_key) as client:
        # 1. Проверка здоровья
        healthy = await client.check_health()
        print(f"API Health: {healthy}")

        # 2. Список моделей
        models = await client.list_models()
        print(f"Available models: {models}")

        # 3. Простой чат
        response = await client.chat(
            message="Привет! Оцени этот проект по шкале 1-10.",
            model="sonnet",
            temperature=0.3
        )
        print(f"Response: {response}")

        # 4. Чат с сессией
        session_id = "grant_project_123"

        response1 = await client.chat(
            message="Запомни: проект о социальной поддержке молодёжи",
            session_id=session_id
        )

        response2 = await client.chat(
            message="О чём был проект?",
            session_id=session_id
        )
        print(f"Remembered: {response2}")

        # 5. Выполнение кода
        code = """
import json

data = {"актуальность": 8, "новизна": 7, "методология": 9}
total = sum(data.values())

print(json.dumps({
    "scores": data,
    "total": total,
    "average": round(total / len(data), 2)
}))
"""

        result = await client.execute_code(code, language="python")
        print(f"Code result: {result['result']}")

        # 6. Статистика
        stats = await client.get_statistics()
        print(f"Statistics: {stats}")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_usage())
