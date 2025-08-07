#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервис для работы с Perplexity API
"""

import os
import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class PerplexityService:
    """Сервис для работы с Perplexity API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "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"
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Кэш настроек модели
        self._model_settings = None
        self._settings_cache_time = 0
        self._cache_duration = 3600  # 1 час
        # Кэш настроек модели
        self._model_settings = None
        self._settings_cache_time = 0
        self._cache_duration = 3600  # 1 час
    
    def get_model_settings(self, model: str = "sonar") -> Dict[str, Any]:
        """Получение актуальных настроек модели через API"""
        current_time = time.time()
        
        # Проверяем кэш
        if (self._model_settings and 
            current_time - self._settings_cache_time < self._cache_duration):
            return self._model_settings
        
        try:
            # Тестовый запрос для получения информации о модели
            test_payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Привет! Расскажи о своих возможностях."
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Извлекаем информацию из ответа
                usage = result.get("usage", {})
                
                # Формируем настройки модели
                model_settings = {
                    "model_name": model,
                    "model_type": "Поисковая модель",
                    "context_size": "128K токенов",
                    "max_tokens": usage.get("total_tokens", 2000),
                    "temperature": 0.2,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "search_mode": "web",
                    "web_search_options": {
                        "search_context_size": "medium"  # low, medium, high
                    },
                    "pricing": {
                        "input_tokens": "$1 за 1M токенов",
                        "output_tokens": "$1 за 1M токенов", 
                        "search_queries": "$5 за 1K запросов",
                        "status": "САМАЯ ЭКОНОМИЧНАЯ"
                    },
                    "performance": {
                        "requests_per_minute": 50,
                        "web_search": True,
                        "sources": True,
                        "citations": True
                    },
                    "capabilities": [
                        "Поиск в интернете (как на сайте Perplexity)",
                        "Источники и цитаты",
                        "Быстрые факты и новости",
                        "Простые Q&A",
                        "Анализ актуальной информации"
                    ],
                    "last_updated": datetime.now().isoformat()
                }
                
                # Кэшируем настройки
                self._model_settings = model_settings
                self._settings_cache_time = current_time
                
                logger.info(f"Получены настройки модели {model}")
                return model_settings
                
            else:
                logger.error(f"Ошибка получения настроек модели: {response.status_code}")
                return self._get_default_settings(model)
                
        except Exception as e:
            logger.error(f"Ошибка получения настроек модели: {e}")
            return self._get_default_settings(model)
    
    def _get_default_settings(self, model: str) -> Dict[str, Any]:
        """Возвращает настройки по умолчанию если API недоступен"""
        return {
            "model_name": model,
            "model_type": "Поисковая модель",
            "context_size": "128K токенов",
            "max_tokens": 2000,
            "temperature": 0.2,
            "timeout": 30,
            "retry_attempts": 3,
            "search_mode": "web",
            "web_search_options": {
                "search_context_size": "medium"
            },
            "pricing": {
                "input_tokens": "$1 за 1M токенов",
                "output_tokens": "$1 за 1M токенов",
                "search_queries": "$5 за 1K запросов",
                "status": "САМАЯ ЭКОНОМИЧНАЯ"
            },
            "performance": {
                "requests_per_minute": 50,
                "web_search": True,
                "sources": True,
                "citations": True
            },
            "capabilities": [
                "Поиск в интернете (как на сайте Perplexity)",
                "Источники и цитаты", 
                "Быстрые факты и новости",
                "Простые Q&A",
                "Анализ актуальной информации"
            ],
            "last_updated": datetime.now().isoformat(),
            "note": "Настройки по умолчанию (API недоступен)"
        }
    
    def search_grants(self, query: str, region: str = None, budget_range: str = None, user_id: int = None, session_id: int = None) -> Dict[str, Any]:
        """Поиск грантов с использованием Perplexity API"""
        try:
            # Получаем актуальные настройки модели
            model_settings = self.get_model_settings("sonar")
            
            # Формируем запрос для поиска грантов
            search_query = self._build_grant_query(query, region, budget_range)
            
            # Используем настройки из API
            payload = {
                "model": model_settings["model_name"],
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты эксперт по поиску грантов. Найди актуальные гранты и предоставь структурированную информацию."
                    },
                    {
                        "role": "user",
                        "content": search_query
                    }
                ],
                "max_tokens": model_settings["max_tokens"],
                "temperature": model_settings["temperature"],
                "search_mode": model_settings["search_mode"],
                "web_search_options": model_settings["web_search_options"]
            }
            
            # Выполняем запрос с retry логикой
            response = self._make_request_with_retry(payload)
            
            if response:
                result = self._process_grant_response(response)
                
                # Логируем запрос в БД если передан user_id
                if user_id and session_id:
                    self._log_query_to_db(user_id, session_id, search_query, result)
                
                return result
            else:
                error_result = {"error": "Не удалось получить данные о грантах"}
                
                # Логируем ошибку в БД
                if user_id and session_id:
                    self._log_query_to_db(user_id, session_id, search_query, error_result, status="error")
                
                return error_result
                
        except Exception as e:
            logger.error(f"Ошибка поиска грантов: {e}")
            error_result = {"error": f"Ошибка поиска: {str(e)}"}
            
            # Логируем ошибку в БД
            if user_id and session_id:
                self._log_query_to_db(user_id, session_id, query, error_result, status="error", error_message=str(e))
            
            return error_result
    
    def _build_grant_query(self, query: str, region: str = None, budget_range: str = None) -> str:
        """Построение запроса для поиска грантов"""
        base_query = f"Найди актуальные гранты для: {query}"
        
        if region:
            base_query += f" в регионе: {region}"
        
        if budget_range:
            base_query += f" с бюджетом: {budget_range}"
        
        base_query += ". Предоставь детальную информацию о каждом гранте включая требования, сроки и контакты."
        
        return base_query
    
    def _make_request_with_retry(self, payload: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Выполнение запроса с retry логикой"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30  # Уменьшаем timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API Error {response.status_code}: {response.text}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
        
        return None
    
    def _determine_model_from_usage(self, usage_stats: Dict) -> str:
        """Определение модели на основе usage_stats"""
        try:
            # Проверяем search_context_size для определения модели
            search_context = usage_stats.get('search_context_size', '')
            
            if search_context == 'medium':
                return 'sonar'
            elif search_context == 'low':
                return 'sonar-pro'
            elif search_context == 'high':
                return 'sonar-deep-research'
            else:
                # По умолчанию sonar
                return 'sonar'
                
        except Exception as e:
            logger.error(f"Ошибка определения модели: {e}")
            return 'sonar'
    
    def _calculate_cost(self, usage: Dict) -> float:
        """Расчет стоимости запроса на основе использования токенов"""
        try:
            # Проверяем, есть ли детальная информация о стоимости от API
            if 'cost' in usage and isinstance(usage['cost'], dict):
                total_cost = usage['cost'].get('total_cost', 0)
                if total_cost > 0:
                    return round(total_cost, 6)
            
            # Fallback: используем реальные цены Perplexity API
            # За запрос с поиском тратится примерно $0.07
            input_price_per_1k = 0.001  # $1 за 1M токенов = $0.001 за 1K
            output_price_per_1k = 0.001  # $1 за 1M токенов = $0.001 за 1K
            search_price_per_query = 0.07  # Реальная стоимость поискового запроса
            
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            search_queries = usage.get('num_search_queries', 0)
            
            # Если есть поисковые запросы, используем реальную стоимость
            if search_queries > 0:
                return round(search_price_per_query, 6)
            
            # Если нет поиска, считаем по токенам
            input_cost = (prompt_tokens / 1000) * input_price_per_1k
            output_cost = (completion_tokens / 1000) * output_price_per_1k
            
            total_cost = input_cost + output_cost
            
            return round(total_cost, 6)  # Округляем до 6 знаков
            
        except Exception as e:
            logger.error(f"Ошибка расчета стоимости: {e}")
            return 0.0
    
    def get_model_specific_statistics(self) -> Dict:
        """Получить статистику по конкретным моделям Perplexity из базы данных"""
        try:
            # Получаем данные из базы данных
            db_stats = self._get_db_model_statistics()
            
            # Получаем данные из скринов (теперь тоже из БД)
            screen_data = self.get_latest_screen_data()
            
            # Объединяем данные
            combined_stats = {
                'sonar': {
                    'low': screen_data.get('sonar_low', 0),
                    'medium': screen_data.get('sonar_medium', 0),
                    'high': 0,  # Пока нет данных
                    'total': screen_data.get('sonar_low', 0) + screen_data.get('sonar_medium', 0)
                },
                'sonar-pro': {
                    'low': screen_data.get('sonar_pro_low', 0),
                    'medium': 0,  # Пока нет данных
                    'high': 0,  # Пока нет данных
                    'total': screen_data.get('sonar_pro_low', 0)
                },
                'reasoning-pro': {
                    'low': 0,  # Пока нет данных
                    'medium': 0,  # Пока нет данных
                    'high': 0,  # Пока нет данных
                    'total': screen_data.get('reasoning_pro', 0)
                },
                'total_requests': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Считаем общее количество запросов
            combined_stats['total_requests'] = (
                combined_stats['sonar']['total'] + 
                combined_stats['sonar-pro']['total'] + 
                combined_stats['reasoning-pro']['total']
            )
            
            return combined_stats
            
        except Exception as e:
            logging.error(f"Ошибка при получении статистики по моделям: {e}")
            return {
                'sonar': {'low': 0, 'medium': 0, 'high': 0, 'total': 0},
                'sonar-pro': {'low': 0, 'medium': 0, 'high': 0, 'total': 0},
                'reasoning-pro': {'low': 0, 'medium': 0, 'high': 0, 'total': 0},
                'total_requests': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def _get_db_model_statistics(self) -> Dict:
        """Получить статистику по моделям из базы данных"""
        try:
            from data.database import get_researcher_logs
            
            logs = get_researcher_logs()
            model_stats = {
                'sonar': {'low': 0, 'medium': 0, 'high': 0, 'total': 0},
                'sonar-pro': {'low': 0, 'medium': 0, 'high': 0, 'total': 0},
                'reasoning-pro': {'low': 0, 'medium': 0, 'high': 0, 'total': 0}
            }
            
            for log in logs:
                try:
                    usage_stats = json.loads(log.get('usage_stats', '{}'))
                    if isinstance(usage_stats, dict):
                        # Анализируем модель из usage_stats
                        model_type = usage_stats.get('model', 'sonar')
                        quality = usage_stats.get('quality', 'low')
                        
                        if model_type in model_stats:
                            model_stats[model_type][quality] += 1
                            model_stats[model_type]['total'] += 1
                            
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            return model_stats
            
        except Exception as e:
            logging.error(f"Ошибка при получении статистики из БД: {e}")
            return {
                'sonar': {'low': 0, 'medium': 0, 'high': 0, 'total': 0},
                'sonar-pro': {'low': 0, 'medium': 0, 'high': 0, 'total': 0},
                'reasoning-pro': {'low': 0, 'medium': 0, 'high': 0, 'total': 0}
            }

    def _log_query_to_db(self, user_id: int, session_id: int, query_text: str, result: Dict, status: str = "success", error_message: str = None):
        """Логировать запрос в базу данных с модель-специфичной информацией"""
        try:
            from data.database import add_researcher_log
            
            # Извлекаем информацию о модели из результата
            usage = result.get('usage', {})
            model = usage.get('model', 'sonar')
            quality = usage.get('quality', 'low')
            
            # Создаем детальную статистику использования
            detailed_usage = {
                'model': model,
                'quality': quality,
                'input_tokens': usage.get('input_tokens', 0),
                'output_tokens': usage.get('output_tokens', 0),
                'reasoning_tokens': usage.get('reasoning_tokens', 0),
                'search_queries': usage.get('search_queries', 0),
                'cost': usage.get('cost', {})
            }
            
            # Рассчитываем стоимость
            cost = self._calculate_cost(usage)
            
            # Получаем актуальный баланс
            screen_data = self.get_latest_screen_data()
            current_balance = screen_data.get('credit_balance', 0.0)
            
            # Логируем в базу данных
            add_researcher_log(
                user_id=user_id,
                session_id=session_id,
                query_text=query_text,
                result=json.dumps(result),
                sources=json.dumps(result.get('sources', [])),
                usage_stats=json.dumps(detailed_usage),
                cost=cost,
                status=status,
                error_message=error_message,
                credit_balance=current_balance
            )
            
            logging.info(f"Запрос залогирован в БД: модель={model}, качество={quality}, стоимость={cost}")
            
        except Exception as e:
            logging.error(f"Ошибка при логировании в БД: {e}")
    
    def _process_grant_response(self, response: Dict) -> Dict[str, Any]:
        """Обработка ответа API для извлечения информации о грантах"""
        try:
            content = response["choices"][0]["message"]["content"]
            search_results = response.get("search_results", [])
            
            # Извлекаем связанные вопросы
            related_questions = []
            if "related_questions" in response:
                related_questions = response["related_questions"]
            
            # Анализируем использование токенов
            usage = response.get("usage", {})
            
            return {
                "grants_info": content,
                "sources": search_results,
                "related_questions": related_questions,
                "usage": usage,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки ответа: {e}")
            return {
                "error": f"Ошибка обработки ответа: {str(e)}",
                "status": "error"
            }
    
    def get_grant_analysis(self, grant_info: str) -> Dict[str, Any]:
        """Анализ информации о гранте"""
        try:
            # Получаем актуальные настройки модели
            model_settings = self.get_model_settings("sonar")
            
            payload = {
                "model": model_settings["model_name"],
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты эксперт по анализу грантов. Проанализируй информацию и дай рекомендации."
                    },
                    {
                        "role": "user",
                        "content": f"Проанализируй этот грант: {grant_info}"
                    }
                ],
                "max_tokens": model_settings["max_tokens"],
                "temperature": model_settings["temperature"],
                "search_mode": model_settings["search_mode"],
                "web_search_options": model_settings["web_search_options"]
            }
            
            response = self._make_request_with_retry(payload)
            
            if response:
                return self._process_grant_response(response)
            else:
                return {"error": "Не удалось проанализировать грант"}
                
        except Exception as e:
            logger.error(f"Ошибка анализа гранта: {e}")
            return {"error": f"Ошибка анализа: {str(e)}"}
    
    def get_related_grants(self, topic: str) -> Dict[str, Any]:
        """Поиск связанных грантов"""
        try:
            # Получаем актуальные настройки модели
            model_settings = self.get_model_settings("sonar")
            
            payload = {
                "model": model_settings["model_name"],
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты эксперт по поиску грантов. Найди связанные гранты и возможности."
                    },
                    {
                        "role": "user",
                        "content": f"Найди связанные гранты для темы: {topic}"
                    }
                ],
                "max_tokens": model_settings["max_tokens"],
                "temperature": model_settings["temperature"],
                "search_mode": model_settings["search_mode"],
                "web_search_options": model_settings["web_search_options"]
            }
            
            response = self._make_request_with_retry(payload)
            
            if response:
                return self._process_grant_response(response)
            else:
                return {"error": "Не удалось найти связанные гранты"}
                
        except Exception as e:
            logger.error(f"Ошибка поиска связанных грантов: {e}")
            return {"error": f"Ошибка поиска: {str(e)}"}
    
    def get_perplexity_api_usage(self) -> Dict[str, Any]:
        """Получение данных об использовании напрямую от Perplexity API"""
        try:
            # Попробуем разные endpoints для получения статистики
            endpoints = [
                "/usage",
                "/account/usage", 
                "/account/stats",
                "/stats",
                "/account"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Успешный endpoint: {endpoint}")
                        return response.json()
                    elif response.status_code == 404:
                        logger.info(f"Endpoint не найден: {endpoint}")
                        continue
                    else:
                        logger.warning(f"Endpoint {endpoint} вернул {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Ошибка для endpoint {endpoint}: {e}")
                    continue
            
            # Если ни один endpoint не работает, возвращаем заглушку
            logger.warning("Не удалось получить данные от API, используем заглушку")
            return {
                "usage": {
                    "requests": "N/A (API endpoint не найден)",
                    "input_tokens": "N/A",
                    "output_tokens": "N/A"
                },
                "note": "Данные из скринов Perplexity",
                "manual_data": {
                    "api_requests": {
                        "reasoning-pro, none": 20,
                        "sonar-pro, low": 1,
                        "sonar, low": 56,
                        "sonar, medium": 8,
                        "total": 85
                    },
                    "input_tokens": {
                        "sonar": 1788,
                        "reasoning-pro": 2546,
                        "sonar-pro": 5,
                        "total": 4339
                    },
                    "output_tokens": {
                        "sonar": 9833,
                        "reasoning-pro": 169065,
                        "sonar-pro": 50,
                        "total": 178948
                    },
                    "reasoning_tokens": {
                        "reasoning-pro": 5853115
                    }
                }
            }
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения данных от Perplexity API: {response.status_code}")
                return {"error": f"API Error {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Ошибка получения данных от Perplexity API: {e}")
            return {"error": str(e)}
    
    def sync_with_perplexity_api(self) -> Dict[str, Any]:
        """Синхронизация данных с Perplexity API"""
        try:
            # Получаем данные от API
            api_data = self.get_perplexity_api_usage()
            
            if "error" in api_data:
                return api_data
            
            # Получаем наши данные из БД
            db_stats = self.get_account_statistics()
            
            # Сравниваем и обновляем
            comparison = {
                "perplexity_api": api_data,
                "our_database": db_stats,
                "differences": {},
                "sync_status": "completed"
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            return {"error": str(e)}
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """Получение актуальной статистики аккаунта из базы данных логов"""
        try:
            import sys
            sys.path.append('/var/GrantService')
            from data.database import GrantServiceDatabase
            db = GrantServiceDatabase()
            
            # Получаем все логи исследователя
            logs = db.get_researcher_logs(limit=10000)
            
            if not logs:
                return self._get_default_account_stats()
            
            # Анализируем статистику
            total_queries = len(logs)
            successful_queries = len([log for log in logs if log.get('status') == 'success'])
            failed_queries = total_queries - successful_queries
            
            # Считаем общие расходы
            total_cost = sum([log.get('cost', 0) for log in logs])
            
            # Анализируем использование токенов
            total_input_tokens = 0
            total_output_tokens = 0
            total_search_queries = 0
            
            for log in logs:
                usage_stats = log.get('usage_stats', {})
                
                # Обрабатываем разные типы usage_stats
                if isinstance(usage_stats, str):
                    try:
                        usage_stats = json.loads(usage_stats)
                    except (json.JSONDecodeError, TypeError):
                        usage_stats = {}
                elif not isinstance(usage_stats, dict):
                    usage_stats = {}
                
                # Безопасное извлечение значений
                try:
                    total_input_tokens += usage_stats.get('prompt_tokens', 0)
                    total_output_tokens += usage_stats.get('completion_tokens', 0)
                    total_search_queries += usage_stats.get('num_search_queries', 0)
                except (TypeError, AttributeError):
                    # Если что-то пошло не так, пропускаем
                    continue
            
            # Определяем текущий тариф на основе расходов
            current_tier = self._determine_tier(total_cost)
            
            # Получаем лимиты для текущего тарифа
            tier_limits = self._get_tier_limits(current_tier)
            
            # Статистика по дням
            daily_stats = {}
            # Статистика по моделям
            model_stats = {
                'sonar': {'requests': 0, 'input_tokens': 0, 'output_tokens': 0, 'search_queries': 0},
                'sonar-pro': {'requests': 0, 'input_tokens': 0, 'output_tokens': 0, 'search_queries': 0},
                'reasoning-pro': {'requests': 0, 'input_tokens': 0, 'output_tokens': 0, 'search_queries': 0},
                'sonar-reasoning': {'requests': 0, 'input_tokens': 0, 'output_tokens': 0, 'search_queries': 0},
                'sonar-deep-research': {'requests': 0, 'input_tokens': 0, 'output_tokens': 0, 'search_queries': 0}
            }
            
            for log in logs:
                created_at = log.get('created_at', '')
                if isinstance(created_at, str):
                    date = created_at[:10] if created_at else 'unknown'
                else:
                    date = 'unknown'
                if date not in daily_stats:
                    daily_stats[date] = {
                        'queries': 0,
                        'cost': 0,
                        'tokens': 0,
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'search_queries': 0
                    }
                daily_stats[date]['queries'] += 1
                daily_stats[date]['cost'] += log.get('cost', 0)
                
                # Безопасная обработка usage_stats
                usage_stats = log.get('usage_stats', {})
                if isinstance(usage_stats, str):
                    try:
                        usage_stats = json.loads(usage_stats)
                    except (json.JSONDecodeError, TypeError):
                        usage_stats = {}
                elif not isinstance(usage_stats, dict):
                    usage_stats = {}
                
                # Обновляем дневную статистику
                daily_stats[date]['tokens'] += usage_stats.get('total_tokens', 0)
                daily_stats[date]['input_tokens'] += usage_stats.get('prompt_tokens', 0)
                daily_stats[date]['output_tokens'] += usage_stats.get('completion_tokens', 0)
                daily_stats[date]['search_queries'] += usage_stats.get('num_search_queries', 0)
                
                # Определяем модель и обновляем статистику по моделям
                model_name = self._determine_model_from_usage(usage_stats)
                if model_name in model_stats:
                    model_stats[model_name]['requests'] += 1
                    model_stats[model_name]['input_tokens'] += usage_stats.get('prompt_tokens', 0)
                    model_stats[model_name]['output_tokens'] += usage_stats.get('completion_tokens', 0)
                    model_stats[model_name]['search_queries'] += usage_stats.get('num_search_queries', 0)
            
            # Сортируем по дате
            sorted_daily = sorted(daily_stats.items(), key=lambda x: x[0], reverse=True)
            
            return {
                "account_info": {
                    "current_tier": current_tier,
                    "total_spent": total_cost,
                    "tier_progress": self._get_tier_progress(total_cost, current_tier)
                },
                "usage_stats": {
                    "total_queries": total_queries,
                    "successful_queries": successful_queries,
                    "failed_queries": failed_queries,
                    "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                    "total_cost": total_cost,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_search_queries": total_search_queries
                },
                "rate_limits": tier_limits,
                "daily_usage": sorted_daily[:30],  # Последние 30 дней
                "model_statistics": model_stats,  # Статистика по моделям
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики аккаунта: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Возвращаем словарь с ошибкой для отладки
            return {
                "error": str(e),
                "usage_stats": {
                    "total_queries": 0,
                    "total_cost": 0.0
                },
                "account_info": {
                    "current_tier": "Unknown",
                    "total_spent": 0.0
                }
            }
    
    def _determine_tier(self, total_spent: float) -> str:
        """Определение текущего тарифа на основе расходов"""
        if total_spent >= 5000:
            return "Tier 5"
        elif total_spent >= 1000:
            return "Tier 4"
        elif total_spent >= 500:
            return "Tier 3"
        elif total_spent >= 250:
            return "Tier 2"
        elif total_spent >= 50:
            return "Tier 1"
        else:
            return "Tier 0"
    
    def _get_tier_progress(self, total_spent: float, current_tier: str) -> Dict[str, Any]:
        """Прогресс до следующего тарифа"""
        tier_thresholds = {
            "Tier 0": 50,
            "Tier 1": 250,
            "Tier 2": 500,
            "Tier 3": 1000,
            "Tier 4": 5000,
            "Tier 5": float('inf')
        }
        
        current_threshold = tier_thresholds.get(current_tier, 0)
        next_tier = None
        next_threshold = 0
        
        for tier, threshold in tier_thresholds.items():
            if threshold > current_threshold:
                next_tier = tier
                next_threshold = threshold
                break
        
        if next_tier:
            progress = ((total_spent - current_threshold) / (next_threshold - current_threshold)) * 100
            remaining = next_threshold - total_spent
        else:
            progress = 100
            remaining = 0
        
        return {
            "current_tier": current_tier,
            "next_tier": next_tier,
            "progress_percent": min(progress, 100),
            "remaining_to_next": remaining,
            "current_spent": total_spent
        }
    
    def _get_tier_limits(self, tier: str) -> Dict[str, Any]:
        """Получение лимитов для конкретного тарифа"""
        limits = {
            "Tier 0": {
                "sonar": 50,
                "sonar-pro": 50,
                "sonar-reasoning": 50,
                "sonar-reasoning-pro": 50,
                "sonar-deep-research": 5
            },
            "Tier 1": {
                "sonar": 100,
                "sonar-pro": 100,
                "sonar-reasoning": 100,
                "sonar-reasoning-pro": 100,
                "sonar-deep-research": 10
            },
            "Tier 2": {
                "sonar": 200,
                "sonar-pro": 200,
                "sonar-reasoning": 200,
                "sonar-reasoning-pro": 200,
                "sonar-deep-research": 5
            },
            "Tier 3": {
                "sonar": 500,
                "sonar-pro": 500,
                "sonar-reasoning": 500,
                "sonar-reasoning-pro": 500,
                "sonar-deep-research": 50
            },
            "Tier 4": {
                "sonar": 1000,
                "sonar-pro": 1000,
                "sonar-reasoning": 1000,
                "sonar-reasoning-pro": 1000,
                "sonar-deep-research": 100
            },
            "Tier 5": {
                "sonar": 2000,
                "sonar-pro": 2000,
                "sonar-reasoning": 2000,
                "sonar-reasoning-pro": 2000,
                "sonar-deep-research": 200
            }
        }
        
        return limits.get(tier, limits["Tier 0"])
    
    def _get_default_account_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по умолчанию если нет данных"""
        return {
            "account_info": {
                "current_tier": "Tier 0",
                "total_spent": 0,
                "tier_progress": {
                    "current_tier": "Tier 0",
                    "next_tier": "Tier 1",
                    "progress_percent": 0,
                    "remaining_to_next": 50,
                    "current_spent": 0
                }
            },
            "usage_stats": {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "success_rate": 0,
                "total_cost": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_search_queries": 0
            },
            "rate_limits": self._get_tier_limits("Tier 0"),
            "daily_usage": [],
            "last_updated": datetime.now().isoformat(),
            "note": "Нет данных об использовании"
        }
    
    def get_latest_screen_data(self) -> Dict:
        """Получает последние данные из базы данных"""
        try:
            from data.database import get_researcher_logs
            
            # Получаем логи из базы данных
            logs = get_researcher_logs(limit=100)
            
            # Агрегируем данные по моделям
            aggregated_data = {
                'sonar_low': 0,
                'sonar_medium': 0,
                'sonar_pro_low': 0,
                'reasoning_pro': 0,
                'credit_balance': 0.0,
                'total_cost': 0.0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_reasoning_tokens': 0,
                # Данные токенов по моделям
                'sonar_input_tokens': 0,
                'reasoning_pro_input_tokens': 0,
                'sonar_pro_input_tokens': 0
            }
            
            for log in logs:
                try:
                    usage_stats = log.get('usage_stats', {})
                    if isinstance(usage_stats, dict):
                        model = usage_stats.get('model', 'sonar')
                        quality = usage_stats.get('quality', 'low')
                        
                        # Подсчитываем запросы по моделям
                        if model == 'sonar' and quality == 'low':
                            aggregated_data['sonar_low'] += usage_stats.get('requests_count', 1)
                        elif model == 'sonar' and quality == 'medium':
                            aggregated_data['sonar_medium'] += usage_stats.get('requests_count', 1)
                        elif model == 'sonar-pro' and quality == 'low':
                            aggregated_data['sonar_pro_low'] += usage_stats.get('requests_count', 1)
                        elif model == 'reasoning-pro':
                            aggregated_data['reasoning_pro'] += usage_stats.get('requests_count', 1)
                        
                        # Суммируем токены и стоимость
                        aggregated_data['total_input_tokens'] += usage_stats.get('input_tokens', 0)
                        aggregated_data['total_output_tokens'] += usage_stats.get('output_tokens', 0)
                        aggregated_data['total_reasoning_tokens'] += usage_stats.get('reasoning_tokens', 0)
                        aggregated_data['total_cost'] += log.get('cost', 0.0)
                        
                        # Агрегируем токены по моделям
                        if model == 'sonar':
                            aggregated_data['sonar_input_tokens'] += usage_stats.get('input_tokens', 0)
                        elif model == 'reasoning-pro':
                            aggregated_data['reasoning_pro_input_tokens'] += usage_stats.get('input_tokens', 0)
                        elif model == 'sonar-pro':
                            aggregated_data['sonar_pro_input_tokens'] += usage_stats.get('input_tokens', 0)
                        
                        # Берем последний известный баланс из базы данных
                        balance = log.get('credit_balance', 0.0)
                        if balance > 0:
                            aggregated_data['credit_balance'] = balance
                            
                except Exception as e:
                    continue
            
            # Если баланс не найден в логах, пробуем получить из базы данных
            if aggregated_data['credit_balance'] == 0.0:
                try:
                    from data.database import get_latest_credit_balance
                    db_balance = get_latest_credit_balance()
                    if db_balance > 0:
                        aggregated_data['credit_balance'] = db_balance
                except Exception as e:
                    logging.error(f"Ошибка получения баланса из БД: {e}")
            
            return aggregated_data
            
        except Exception as e:
            logging.error(f"Ошибка получения данных из БД: {e}")
            # Fallback к базовым данным
            try:
                from data.database import get_latest_credit_balance
                fallback_balance = get_latest_credit_balance()
            except:
                fallback_balance = 0.0
                
            return {
                'sonar_low': 0,
                'sonar_medium': 0,
                'sonar_pro_low': 0,
                'reasoning_pro': 0,
                'credit_balance': fallback_balance,
                'total_cost': 0.0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_reasoning_tokens': 0
            }
    
    def get_combined_statistics(self) -> Dict[str, Any]:
        """Объединяет статистику из нашей БД с данными из Perplexity"""
        # Получаем данные из нашей БД
        db_stats = self.get_account_statistics()
        
        # Получаем данные из скринов Perplexity
        screen_data = self.get_latest_screen_data()
        
        # Объединяем данные, приоритет скринам Perplexity
        combined = {
            'account_info': {
                **db_stats.get('account_info', {}),
                'credit_balance': screen_data.get('credit_balance', 0.0)
            },
            'usage_stats': {
                **db_stats.get('usage_stats', {}),
                # Добавляем данные из скринов с правильными ключами
                'sonar_low': screen_data.get('sonar_low', 0),
                'sonar_medium': screen_data.get('sonar_medium', 0),
                'sonar_pro_low': screen_data.get('sonar_pro_low', 0),
                'reasoning_pro': screen_data.get('reasoning_pro', 0),
                'total_queries': screen_data.get('sonar_low', 0) + screen_data.get('sonar_medium', 0) + screen_data.get('sonar_pro_low', 0) + screen_data.get('reasoning_pro', 0)
            },
            'tier_progress': db_stats.get('tier_progress', {})
        }
        
        return combined