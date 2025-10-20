"""
LLM Router для GrantService

Автоматический выбор оптимального LLM провайдера для задачи:
- GigaChat: генерация русского текста, общение с пользователем
- Claude Code: анализ, оценка, структурирование, выполнение кода
"""

from typing import Optional, Dict, Any, Literal
from enum import Enum
import logging
import asyncio

from .unified_llm_client import UnifiedLLMClient
from .claude_code_client import ClaudeCodeClient
from .config import (
    GIGACHAT_API_KEY,
    CLAUDE_CODE_API_KEY,
    CLAUDE_CODE_BASE_URL,
    DEFAULT_TEMPERATURE,
    MAX_TOKENS
)

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Типы задач для LLM"""

    # GigaChat - лучше для русского текста
    GENERATION = "generation"          # Генерация текста заявки
    CONVERSATION = "conversation"      # Общение с пользователем
    TRANSLATION = "translation"        # Перевод/локализация

    # Claude Code - лучше для аналитики
    ANALYSIS = "analysis"              # Анализ проекта
    EVALUATION = "evaluation"          # Оценка по критериям
    STRUCTURING = "structuring"        # Структурирование заявки
    RESEARCH = "research"              # Исследование аналогов
    CODE = "code"                      # Выполнение кода
    VALIDATION = "validation"          # Валидация данных


class ProviderType(str, Enum):
    """Типы провайдеров"""
    GIGACHAT = "gigachat"
    CLAUDE = "claude"
    AUTO = "auto"  # Автоматический выбор


class LLMRouter:
    """
    Роутер для автоматического выбора LLM провайдера

    Выбирает оптимальный провайдер на основе типа задачи:
    - GigaChat: русский текст, общение
    - Claude Code: аналитика, оценка, код

    Fallback: если один провайдер недоступен, использует другой
    """

    def __init__(
        self,
        gigachat_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        claude_base_url: Optional[str] = None
    ):
        """
        Инициализация роутера

        Args:
            gigachat_api_key: API ключ GigaChat (опционально, из config)
            claude_api_key: API ключ Claude Code (опционально, из config)
            claude_base_url: URL Claude Code API (опционально, из config)
        """
        self.gigachat_api_key = gigachat_api_key or GIGACHAT_API_KEY
        self.claude_api_key = claude_api_key or CLAUDE_CODE_API_KEY
        self.claude_base_url = claude_base_url or CLAUDE_CODE_BASE_URL

        self.gigachat_client: Optional[UnifiedLLMClient] = None
        self.claude_client: Optional[ClaudeCodeClient] = None

        # Матрица выбора провайдера по типу задачи
        self.provider_matrix = {
            TaskType.GENERATION: ProviderType.GIGACHAT,
            TaskType.CONVERSATION: ProviderType.GIGACHAT,
            TaskType.TRANSLATION: ProviderType.GIGACHAT,

            TaskType.ANALYSIS: ProviderType.CLAUDE,
            TaskType.EVALUATION: ProviderType.CLAUDE,
            TaskType.STRUCTURING: ProviderType.CLAUDE,
            TaskType.RESEARCH: ProviderType.CLAUDE,
            TaskType.CODE: ProviderType.CLAUDE,
            TaskType.VALIDATION: ProviderType.CLAUDE,
        }

        # Статистика использования
        self.stats = {
            "gigachat_requests": 0,
            "claude_requests": 0,
            "fallback_count": 0,
            "errors": []
        }

        logger.info("🚦 LLMRouter инициализирован")

    async def __aenter__(self):
        """Создание клиентов при входе в контекст"""
        # Инициализация GigaChat
        if self.gigachat_api_key:
            self.gigachat_client = UnifiedLLMClient(
                provider="gigachat",
                api_key=self.gigachat_api_key,
                temperature=DEFAULT_TEMPERATURE
            )
            await self.gigachat_client.__aenter__()
            logger.info("✅ GigaChat клиент инициализирован")
        else:
            logger.warning("⚠️ GigaChat API key не задан")

        # Инициализация Claude Code
        if self.claude_api_key:
            self.claude_client = ClaudeCodeClient(
                api_key=self.claude_api_key,
                base_url=self.claude_base_url,
                default_temperature=DEFAULT_TEMPERATURE
            )
            await self.claude_client.__aenter__()
            logger.info("✅ Claude Code клиент инициализирован")
        else:
            logger.warning("⚠️ Claude Code API key не задан")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие клиентов при выходе из контекста"""
        if self.gigachat_client:
            await self.gigachat_client.__aexit__(exc_type, exc_val, exc_tb)
            logger.info("🔒 GigaChat клиент закрыт")

        if self.claude_client:
            await self.claude_client.__aexit__(exc_type, exc_val, exc_tb)
            logger.info("🔒 Claude Code клиент закрыт")

    def _select_provider(
        self,
        task_type: TaskType,
        provider: Optional[ProviderType] = None
    ) -> ProviderType:
        """
        Выбор провайдера для задачи

        Args:
            task_type: Тип задачи
            provider: Явное указание провайдера (приоритет над авто-выбором)

        Returns:
            Выбранный провайдер
        """
        # Явное указание имеет приоритет
        if provider and provider != ProviderType.AUTO:
            logger.info(f"🎯 Явный выбор провайдера: {provider.value}")
            return provider

        # Автоматический выбор по типу задачи
        selected = self.provider_matrix.get(task_type, ProviderType.GIGACHAT)
        logger.info(f"🤖 Авто-выбор для {task_type.value}: {selected.value}")
        return selected

    async def generate(
        self,
        prompt: str,
        task_type: TaskType,
        provider: Optional[ProviderType] = None,
        session_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Универсальная генерация текста с автоматическим выбором провайдера

        Args:
            prompt: Промпт для генерации
            task_type: Тип задачи (определяет провайдера)
            provider: Явное указание провайдера (опционально)
            session_id: ID сессии для Claude (опционально)
            temperature: Температура генерации
            max_tokens: Максимум токенов
            **kwargs: Дополнительные параметры

        Returns:
            Сгенерированный текст

        Raises:
            Exception: Если оба провайдера недоступны
        """
        # Выбор провайдера
        target_provider = self._select_provider(task_type, provider)

        # Параметры генерации
        gen_params = {
            "temperature": temperature or DEFAULT_TEMPERATURE,
            "max_tokens": max_tokens or MAX_TOKENS,
            **kwargs
        }

        logger.info(
            f"📝 Генерация: task={task_type.value}, "
            f"provider={target_provider.value}, "
            f"prompt_len={len(prompt)}"
        )

        # Попытка генерации с основным провайдером
        try:
            if target_provider == ProviderType.CLAUDE:
                if not self.claude_client:
                    raise Exception("Claude Code клиент не инициализирован")

                self.stats["claude_requests"] += 1

                result = await self.claude_client.chat(
                    message=prompt,
                    session_id=session_id,
                    temperature=gen_params["temperature"],
                    max_tokens=gen_params["max_tokens"]
                )

                logger.info(f"✅ Claude сгенерировал: {len(result)} символов")
                return result

            else:  # GigaChat
                if not self.gigachat_client:
                    raise Exception("GigaChat клиент не инициализирован")

                self.stats["gigachat_requests"] += 1

                result = await self.gigachat_client.generate_async(
                    prompt=prompt,
                    temperature=gen_params["temperature"],
                    max_tokens=gen_params["max_tokens"]
                )

                logger.info(f"✅ GigaChat сгенерировал: {len(result)} символов")
                return result

        except Exception as e:
            error_msg = f"Ошибка {target_provider.value}: {e}"
            logger.error(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)

            # Fallback на другой провайдер
            fallback_provider = (
                ProviderType.GIGACHAT if target_provider == ProviderType.CLAUDE
                else ProviderType.CLAUDE
            )

            logger.warning(f"🔄 Fallback на {fallback_provider.value}")
            self.stats["fallback_count"] += 1

            try:
                if fallback_provider == ProviderType.CLAUDE and self.claude_client:
                    self.stats["claude_requests"] += 1
                    result = await self.claude_client.chat(
                        message=prompt,
                        session_id=session_id,
                        temperature=gen_params["temperature"],
                        max_tokens=gen_params["max_tokens"]
                    )
                    logger.info(f"✅ Fallback успешен (Claude): {len(result)} символов")
                    return result

                elif fallback_provider == ProviderType.GIGACHAT and self.gigachat_client:
                    self.stats["gigachat_requests"] += 1
                    result = await self.gigachat_client.generate_async(
                        prompt=prompt,
                        temperature=gen_params["temperature"],
                        max_tokens=gen_params["max_tokens"]
                    )
                    logger.info(f"✅ Fallback успешен (GigaChat): {len(result)} символов")
                    return result

                else:
                    raise Exception(f"Fallback провайдер {fallback_provider.value} недоступен")

            except Exception as fallback_error:
                error_msg = f"Fallback также неудачен: {fallback_error}"
                logger.error(f"❌ {error_msg}")
                self.stats["errors"].append(error_msg)
                raise Exception(f"Все провайдеры недоступны. Основной: {e}, Fallback: {fallback_error}")

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
            language: Язык программирования
            session_id: ID сессии

        Returns:
            Результат выполнения кода

        Raises:
            Exception: Если Claude Code недоступен
        """
        if not self.claude_client:
            raise Exception("Claude Code клиент не инициализирован")

        logger.info(f"🔧 Выполнение кода: {language}, {len(code)} символов")
        self.stats["claude_requests"] += 1

        try:
            result = await self.claude_client.execute_code(
                code=code,
                language=language,
                session_id=session_id
            )

            logger.info(f"✅ Код выполнен успешно")
            return result

        except Exception as e:
            error_msg = f"Ошибка выполнения кода: {e}"
            logger.error(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            raise

    async def create_session(self, user_id: str) -> str:
        """
        Создать сессию для пользователя

        Args:
            user_id: ID пользователя (telegram_id)

        Returns:
            ID сессии
        """
        session_id = f"grant_session_{user_id}"
        logger.info(f"📝 Создана сессия: {session_id}")
        return session_id

    async def delete_session(self, session_id: str) -> bool:
        """
        Удалить сессию

        Args:
            session_id: ID сессии для удаления

        Returns:
            True если успешно
        """
        if not self.claude_client:
            logger.warning("Claude Code клиент не инициализирован")
            return False

        success = await self.claude_client.delete_session(session_id)

        if success:
            logger.info(f"🗑️ Сессия удалена: {session_id}")
        else:
            logger.warning(f"⚠️ Не удалось удалить сессию: {session_id}")

        return success

    async def check_providers_health(self) -> Dict[str, bool]:
        """
        Проверка здоровья всех провайдеров

        Returns:
            Dict с результатами проверки
        """
        health = {}

        # GigaChat
        if self.gigachat_client:
            try:
                health["gigachat"] = await self.gigachat_client.check_connection_async()
            except:
                health["gigachat"] = False
        else:
            health["gigachat"] = False

        # Claude Code
        if self.claude_client:
            try:
                health["claude"] = await self.claude_client.check_health()
            except:
                health["claude"] = False
        else:
            health["claude"] = False

        logger.info(f"🏥 Health check: {health}")
        return health

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику использования роутера

        Returns:
            Dict со статистикой
        """
        total_requests = self.stats["gigachat_requests"] + self.stats["claude_requests"]

        return {
            "total_requests": total_requests,
            "gigachat_requests": self.stats["gigachat_requests"],
            "claude_requests": self.stats["claude_requests"],
            "gigachat_percent": (
                (self.stats["gigachat_requests"] / total_requests * 100)
                if total_requests > 0 else 0
            ),
            "claude_percent": (
                (self.stats["claude_requests"] / total_requests * 100)
                if total_requests > 0 else 0
            ),
            "fallback_count": self.stats["fallback_count"],
            "errors_count": len(self.stats["errors"]),
            "recent_errors": self.stats["errors"][-5:] if self.stats["errors"] else []
        }

    def reset_statistics(self):
        """Сброс статистики"""
        self.stats = {
            "gigachat_requests": 0,
            "claude_requests": 0,
            "fallback_count": 0,
            "errors": []
        }
        logger.info("📊 Статистика сброшена")


# Пример использования
async def example_usage():
    """Пример использования LLM Router"""

    async with LLMRouter() as router:
        # 1. Проверка здоровья провайдеров
        health = await router.check_providers_health()
        print(f"Health: {health}")

        # 2. Оценка проекта (автоматически выберет Claude)
        evaluation = await router.generate(
            prompt="Оцени проект по 10 критериям от 1 до 10...",
            task_type=TaskType.EVALUATION,
            temperature=0.3,
            max_tokens=2000
        )
        print(f"Evaluation: {evaluation}")

        # 3. Генерация русского текста (автоматически выберет GigaChat)
        grant_text = await router.generate(
            prompt="Напиши введение к грантовой заявке на тему...",
            task_type=TaskType.GENERATION,
            temperature=0.7,
            max_tokens=1000
        )
        print(f"Grant text: {grant_text}")

        # 4. Выполнение кода (только Claude)
        code_result = await router.execute_code(
            code="""
import json
data = {"актуальность": 8, "новизна": 7}
print(json.dumps(data))
""",
            language="python"
        )
        print(f"Code result: {code_result}")

        # 5. Работа с сессиями
        session_id = await router.create_session(user_id="123456")

        response1 = await router.generate(
            prompt="Запомни: проект о социальной поддержке",
            task_type=TaskType.ANALYSIS,
            session_id=session_id
        )

        response2 = await router.generate(
            prompt="О чём был проект?",
            task_type=TaskType.ANALYSIS,
            session_id=session_id
        )
        print(f"Remembered: {response2}")

        # 6. Статистика
        stats = router.get_statistics()
        print(f"Statistics: {stats}")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_usage())
