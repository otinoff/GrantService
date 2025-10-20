import asyncio
import aiohttp
import json
import base64
import uuid
from typing import Optional, List, Dict
import time
import logging

from .config import (
    GIGACHAT_BASE_URL, GIGACHAT_AUTH_URL, GIGACHAT_API_KEY, GIGACHAT_CLIENT_ID,
    PERPLEXITY_BASE_URL, PERPLEXITY_API_KEY,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    CLAUDE_CODE_BASE_URL, CLAUDE_CODE_API_KEY, CLAUDE_CODE_DEFAULT_MODEL,
    DEFAULT_TEMPERATURE, MAX_TOKENS, REQUEST_TIMEOUT,
    ASYNC_CONNECTION_LIMIT, ASYNC_CONNECTION_LIMIT_PER_HOST, ASYNC_REQUEST_TIMEOUT
)

logger = logging.getLogger(__name__)

class UnifiedLLMClient:
    def __init__(self, provider: str = "gigachat", model: str = "GigaChat", 
                 temperature: float = DEFAULT_TEMPERATURE, prompt_config: Optional[Dict] = None, **kwargs):
        """
        Унифицированный клиент для работы с различными LLM провайдерами
        Адаптирован для GrantService на основе review_generator
        
        Args:
            provider: "ollama", "gigachat" или "perplexity"
            model: Название модели
            temperature: Температура генерации
            prompt_config: Конфигурация промптов
            **kwargs: Дополнительные параметры (api_key для GigaChat)
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.prompt_config = prompt_config or {}
        self.session = None
        
        # Настройки для разных провайдеров
        if self.provider == "ollama":
            self.base_url = kwargs.get("base_url", OLLAMA_BASE_URL)
        elif self.provider == "gigachat":
            self.base_url = GIGACHAT_BASE_URL
            self.auth_url = GIGACHAT_AUTH_URL
            self.api_key = kwargs.get("api_key", GIGACHAT_API_KEY)
            self.client_id = kwargs.get("client_id", GIGACHAT_CLIENT_ID)
            self.access_token = None
            self.token_expires_at = 0
        elif self.provider == "perplexity":
            self.base_url = PERPLEXITY_BASE_URL
            self.api_key = kwargs.get("api_key", PERPLEXITY_API_KEY)
        elif self.provider in ["claude_code", "claude"]:
            self.base_url = CLAUDE_CODE_BASE_URL
            self.api_key = kwargs.get("api_key", CLAUDE_CODE_API_KEY)
            if not self.model or self.model == "GigaChat":
                self.model = CLAUDE_CODE_DEFAULT_MODEL
        else:
            raise ValueError(f"Неподдерживаемый провайдер: {provider}")
        
        logger.info(f"🔧 Инициализирован {self.provider.upper()} клиент с моделью '{self.model}'")
        self.debug_log = []  # Детальный лог для Web Admin отладки
    
    async def __aenter__(self):
        """Создаём aiohttp сессию при входе в контекст"""
        # Отключаем SSL проверку для GigaChat (часто проблемы с корпоративными сертификатами)
        connector = aiohttp.TCPConnector(
            limit=ASYNC_CONNECTION_LIMIT, 
            limit_per_host=ASYNC_CONNECTION_LIMIT_PER_HOST,
            ssl=False  # Отключаем SSL проверку
        )
        timeout = aiohttp.ClientTimeout(total=ASYNC_REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        # Для GigaChat получаем токен авторизации
        if self.provider == "gigachat":
            await self._get_gigachat_token()
        
        return self
    
    async def generate_async(self, prompt: str, provider: str = None, **kwargs) -> str:
        """
        Универсальный метод для генерации текста

        Args:
            prompt: Текст промпта
            provider: Провайдер ('gigachat', 'ollama', 'perplexity') или None для автоопределения
            **kwargs: Дополнительные параметры (temperature, max_tokens и т.д.)

        Returns:
            Сгенерированный текст
        """
        # ВАЖНО: Инициализируем session если его нет (для использования БЕЗ context manager)
        if self.session is None:
            await self.__aenter__()

        # Определяем провайдера
        target_provider = provider or self.provider

        # Применяем параметры из kwargs
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', MAX_TOKENS)

        try:
            if target_provider == "gigachat":
                return await self._generate_gigachat(prompt, temperature, max_tokens)
            elif target_provider == "ollama":
                return await self._generate_ollama(prompt, temperature, max_tokens)
            elif target_provider == "perplexity":
                return await self._generate_perplexity(prompt, temperature, max_tokens)
            elif target_provider in ["claude_code", "claude"]:
                return await self._generate_claude_code(prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Неподдерживаемый провайдер: {target_provider}")
                
        except Exception as e:
            logger.error(f"Ошибка генерации через {target_provider}: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрываем aiohttp сессию при выходе из контекста"""
        if self.session:
            await self.session.close()
    
    async def _get_gigachat_token(self):
        """Получает токен авторизации для GigaChat"""
        if self.access_token and time.time() < self.token_expires_at:
            return  # Токен ещё действителен
        
        logger.info(f"🔐 Получаем токен авторизации для GigaChat...")
        self.debug_log.append(f"🔐 Запрос токена GigaChat: {self.auth_url}")
        
        url = self.auth_url
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = "scope=GIGACHAT_API_PERS"
        
        try:
            async with self.session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    # Токен действует 30 минут, обновляем за 5 минут до истечения
                    self.token_expires_at = time.time() + token_data.get("expires_in", 1800) - 300
                    logger.info(f"✅ Токен GigaChat получен успешно")
                    self.debug_log.append(f"✅ Токен получен, срок действия: {token_data.get('expires_in', 1800)}сек")
                else:
                    error_text = await response.text()
                    raise Exception(f"Ошибка получения токена: {response.status} - {error_text}")
        except Exception as e:
            raise Exception(f"Ошибка авторизации GigaChat: {e}")
    
    async def generate_text(self, prompt: str, max_tokens: int = None) -> str:
        """
        Генерация текста через выбранный провайдер
        
        Args:
            prompt: Промпт для генерации
            max_tokens: Максимальное количество токенов
            
        Returns:
            Сгенерированный текст
        """
        # Используем универсальный метод generate_async
        return await self.generate_async(prompt, temperature=self.temperature, max_tokens=max_tokens)
    
    def _clean_markdown_formatting(self, text: str) -> str:
        """Очищает текст от markdown разметки и лишнего форматирования"""
        import re
        
        # Убираем звёздочки для выделения (**text**, *text*)
        text = re.sub(r'\*{1,2}([^*]+?)\*{1,2}', r'\1', text)
        
        # Убираем квадратные скобки [text]
        text = re.sub(r'\[([^\]]+?)\]', r'\1', text)
        
        # Убираем обычные скобки с объяснениями
        text = re.sub(r'\s*\([^)]*синоним[^)]*\)', '', text)
        text = re.sub(r'\s*\([^)]*замен[^)]*\)', '', text)
        text = re.sub(r'\s*\([^)]*вариант[^)]*\)', '', text)
        
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _generate_ollama(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """Генерация через Ollama API"""
        url = f"{self.base_url}/api/generate"
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or MAX_TOKENS
            },
            "stream": True
        }
        
        async with self.session.post(url, json=data) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
            
            # Ollama возвращает NDJSON
            full_response = ""
            async for line in response.content:
                if line.strip():
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'response' in chunk:
                            full_response += chunk['response']
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            return full_response.strip()
    
    async def _generate_gigachat(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """Генерация через GigaChat API с обработкой rate limits"""
        self.debug_log.append(f"🤖 Начинаем генерацию GigaChat: {len(prompt)} символов")
        # Проверяем и обновляем токен если нужно
        await self._get_gigachat_token()
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or MAX_TOKENS
        }
        
        # Retry логика для обработки rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # Извлекаем ответ из GigaChat формата
                        if "choices" in response_data and len(response_data["choices"]) > 0:
                            response_text = response_data["choices"][0]["message"]["content"].strip()
                            self.debug_log.append(f"✅ GigaChat ответ получен: {len(response_text)} символов")
                            return response_text
                        else:
                            self.debug_log.append("❌ Пустой ответ от GigaChat")
                            raise Exception("Пустой ответ от GigaChat")
                    
                    elif response.status == 429:  # Too Many Requests
                        error_text = await response.text()
                        wait_time = 2 ** attempt  # Экспоненциальная задержка
                        logger.warning(f"⚠️ Rate limit GigaChat. Попытка {attempt + 1}/{max_retries}, ждём {wait_time}с...")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"GigaChat rate limit превышен: {error_text}")
                    
                    else:
                        error_text = await response.text()
                        raise Exception(f"GigaChat HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ GigaChat timeout. Повтор {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception("GigaChat timeout после нескольких попыток")
    
    async def _generate_perplexity(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """Генерация через Perplexity API"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens
        }

        async with self.session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()

                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"].strip()
                else:
                    raise Exception("Пустой ответ от Perplexity")
            else:
                error_text = await response.text()
                raise Exception(f"Perplexity HTTP {response.status}: {error_text}")

    async def _generate_claude_code(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """
        Генерация через Claude Code HTTP API

        NOTE: Использует HTTP API вместо локального Claude CLI subprocess из-за OAuth IP ограничений.
        OAuth токены привязаны к IP сервера где были созданы и не работают на production сервере.

        Production architecture:
        - GrantService (production): 5.35.88.251 -> HTTP API call ->
        - Claude Code API Server: 178.236.17.55:8000 (с валидным OAuth)

        TODO: Migrate to fully local solution when OAuth IP limitation is resolved.
        """
        self.debug_log.append(f"🤖 Начинаем генерацию Claude Code API: {len(prompt)} символов")

        url = f"{self.base_url}/chat"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "message": prompt,
            "model": self.model if self.model != "GigaChat" else "sonnet",
            "temperature": temperature or self.temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                response_text = await response.text()

                if response.status == 200:
                    data = json.loads(response_text)
                    result = data.get("response", "").strip()

                    # Логируем статистику если доступна
                    model_used = data.get("model", self.model)
                    session_id = data.get("session_id")

                    self.debug_log.append(
                        f"✅ Claude API ответ: {len(result)} символов, "
                        f"model={model_used}"
                    )

                    logger.info(
                        f"Claude API: {len(result)} chars, model={model_used}"
                    )

                    return result

                else:
                    error_msg = f"Claude API error: {response.status} - {response_text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except asyncio.TimeoutError:
            error_msg = "Claude API timeout"
            logger.error(error_msg)
            raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Claude API execution error: {e}")
            raise
    
    async def check_connection_async(self) -> bool:
        """Асинхронная проверка подключения"""
        try:
            if not self.session:
                connector = aiohttp.TCPConnector()
                timeout = aiohttp.ClientTimeout(total=10)
                self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
                should_close = True
            else:
                should_close = False
            
            if self.provider == "ollama":
                url = f"{self.base_url}/api/tags"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        model_names = [model.get('name', '') for model in data.get('models', [])]
                        result = self.model in model_names
                    else:
                        result = False
            
            elif self.provider == "gigachat":
                # Для GigaChat просто пробуем получить токен
                await self._get_gigachat_token()
                result = self.access_token is not None
            
            elif self.provider == "perplexity":
                # Для Perplexity делаем простой запрос
                url = f"{self.base_url}/models"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with self.session.get(url, headers=headers) as response:
                    result = response.status == 200

            elif self.provider in ["claude_code", "claude"]:
                # Для Claude Code делаем проверку доступности API
                url = f"{self.base_url}/health"  # Правильный endpoint для проверки здоровья
                async with self.session.get(url) as response:
                    result = response.status == 200
            else:
                result = False

            if should_close:
                await self.session.close()
                self.session = None
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка проверки подключения {self.provider}: {e}")
            return False
    
    def get_debug_log(self) -> list:
        """Возвращает детальный лог операций для отладки"""
        return self.debug_log.copy()
    
    def clear_debug_log(self):
        """Очищает лог отладки"""
        self.debug_log.clear()
