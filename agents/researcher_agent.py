#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Researcher Agent - агент для проведения исследований по грантовым заявкам
"""
import sys
import os
from typing import Dict, Any, List
import logging
import asyncio

# Добавляем пути к модулям
sys.path.append('/var/GrantService/shared')
sys.path.append('/var/GrantService/telegram-bot/services')

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    UNIFIED_CLIENT_AVAILABLE = False
    UnifiedLLMClient = None
    AGENT_CONFIGS = {}

try:
    from services.llm_router import LLMRouter, LLMProvider
    LLM_ROUTER_AVAILABLE = True
except ImportError:
    logger.warning("LLM Router not available")
    LLMRouter = None
    LLMProvider = None
    LLM_ROUTER_AVAILABLE = False

class ResearcherAgent(BaseAgent):
    """Агент-исследователь для анализа рынка и поиска грантов"""
    
    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("researcher", db, llm_provider)
        
        if UNIFIED_CLIENT_AVAILABLE:
            self.llm_client = UnifiedLLMClient()
            self.config = AGENT_CONFIGS.get("researcher", AGENT_CONFIGS.get("writer", {}))
        elif LLM_ROUTER_AVAILABLE:
            self.llm_router = LLMRouter()
        else:
            self.llm_client = None
            self.llm_router = None
            logger.warning("Researcher agent working without LLM services")
    
    def _get_goal(self) -> str:
        return "Провести комплексное исследование рынка, конкурентов и грантовых возможностей"
    
    def _get_backstory(self) -> str:
        return """Ты опытный аналитик рынка с 15-летним стажем в области грантового финансирования. 
        Ты специализируешься на анализе стартапов, технологических проектов и инновационных решений. 
        Твоя задача - провести глубокое исследование и найти лучшие грантовые возможности."""
    
    async def research_grant_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Асинхронное проведение исследования для грантовой заявки"""
        try:
            # Извлекаем данные
            description = data.get('description', '')
            llm_provider = data.get('llm_provider', 'auto')
            model = data.get('model', 'auto')
            temperature = data.get('temperature', 0.3)
            max_tokens = data.get('max_tokens', 1000)
            
            logger.info(f"🔍 Начинаем исследование проекта: {description[:100]}...")
            
            if UNIFIED_CLIENT_AVAILABLE:
                # Используем UnifiedLLMClient
                config = AGENT_CONFIGS.get("researcher", AGENT_CONFIGS["writer"])
                
                async with UnifiedLLMClient(
                    provider=config["provider"],
                    model=config["model"],
                    temperature=config["temperature"]
                ) as client:
                    
                    prompt = f"""
                    Проведи комплексное исследование для грантовой заявки:
                    
                    {description}
                    
                    Проанализируй:
                    1. Рыночные возможности и потенциал
                    2. Конкурентную среду
                    3. Грантовые программы и требования
                    4. Рекомендации по улучшению заявки
                    
                    Дай структурированный анализ с конкретными рекомендациями.
                    """
                    
                    result_text = await client.generate_text(prompt, config["max_tokens"])
                    
                    return {
                        'status': 'success',
                        'result': result_text,
                        'agent_type': 'researcher',
                        'provider_used': config["provider"],
                        'input_data': description,
                        'llm_settings': {
                            'provider': config["provider"],
                            'model': config["model"],
                            'temperature': config["temperature"],
                            'max_tokens': config["max_tokens"]
                        }
                    }
            else:
                # Fallback на старую логику
                return self.research_grant(data)
                
        except Exception as e:
            logger.error(f"❌ Ошибка исследования: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка исследования: {str(e)}",
                'agent_type': 'researcher',
                'provider_used': llm_provider if 'llm_provider' in locals() else 'unknown'
            }
    
    def research_grant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронное проведение исследования для грантовой заявки (fallback)"""
        try:
            # Извлекаем данные
            description = data.get('description', '')
            llm_provider = data.get('llm_provider', 'auto')
            model = data.get('model', 'auto')
            temperature = data.get('temperature', 0.3)
            max_tokens = data.get('max_tokens', 1000)
            
            logger.info(f"🔍 Начинаем исследование проекта: {description[:100]}...")
            
            if not UNIFIED_CLIENT_AVAILABLE:
                # Определяем провайдера
                if llm_provider == "auto":
                    target_provider = None  # Автоматический выбор
                elif llm_provider == "gigachat":
                    target_provider = LLMProvider.GIGACHAT
                elif llm_provider == "local":
                    target_provider = LLMProvider.LOCAL
                else:
                    target_provider = None
                
                # Проводим исследование через LLM Router
                result = self.llm_router.analyze_grant_application(
                    application_text=description,
                    grant_criteria="Исследование рынка, конкурентов и грантовых возможностей",
                    preferred_provider=target_provider
                )
                
                # Добавляем метаданные
                result['agent_type'] = 'researcher'
                result['input_data'] = description
                result['llm_settings'] = {
                    'provider': llm_provider,
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                
                logger.info(f"✅ Исследование завершено. Провайдер: {result.get('provider_used', 'Unknown')}")
                
                return result
            else:
                # Запускаем асинхронную версию
                return asyncio.run(self.research_grant_async(data))
            
        except Exception as e:
            logger.error(f"❌ Ошибка исследования: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка исследования: {str(e)}",
                'agent_type': 'researcher',
                'provider_used': llm_provider if 'llm_provider' in locals() else 'unknown'
            }
    
    def analyze_market(self, project_description: str) -> Dict[str, Any]:
        """Анализ рынка для проекта"""
        try:
            prompt = f"""
Проведи анализ рынка для следующего проекта:

{project_description}

Проанализируй:
1. Размер рынка и потенциал роста
2. Ключевые тренды в отрасли
3. Целевая аудитория
4. Рыночные возможности
5. Потенциальные риски

Дай конкретные цифры и факты.
"""
            
            if UNIFIED_CLIENT_AVAILABLE:
                # Используем UnifiedLLMClient
                config = AGENT_CONFIGS.get("researcher", AGENT_CONFIGS["writer"])
                
                async def analyze_async():
                    async with UnifiedLLMClient(
                        provider=config["provider"],
                        model=config["model"],
                        temperature=config["temperature"]
                    ) as client:
                        return await client.generate_text(prompt, config["max_tokens"])
                
                result_text = asyncio.run(analyze_async())
                
                return {
                    'status': 'success',
                    'result': result_text,
                    'agent_type': 'researcher',
                    'provider_used': config["provider"]
                }
            else:
                # Fallback на старую логику
                result = self.llm_router.analyze_grant_application(
                    application_text=project_description,
                    grant_criteria="Анализ рынка и конкурентной среды"
                )
                return result
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа рынка: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка анализа рынка: {str(e)}",
                'agent_type': 'researcher'
            }
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод обработки данных"""
        return self.research_grant(data)
    
    def research_anketa(self, anketa_id: str) -> Dict[str, Any]:
        """
        Исследование через Claude Code WebSearch

        Выполняет специализированные запросы по промтам эксперта:
        - Блок 1: Проблема и социальная значимость (3 запроса - MVP)

        Полная реализация 27 запросов будет добавлена позже.
        """
        try:
            logger.info(f"🔍 Начинаем исследование для {anketa_id}")

            # Получаем анкету
            anketa = self.db.get_session_by_anketa_id(anketa_id)

            if not anketa:
                return {
                    'status': 'error',
                    'message': f'Анкета {anketa_id} не найдена',
                    'agent_type': 'researcher'
                }

            # Извлекаем placeholders
            placeholders = self._extract_placeholders_from_anketa(anketa)
            logger.info(f"📋 Placeholders: {placeholders}")

            # БЛОК 1 (MVP): Проблема и социальная значимость (3 запроса)
            block1_results = self._research_block1_mvp(placeholders)
            logger.info(f"✅ Блок 1 завершён: {len(block1_results.get('queries', []))} запросов")

            # Формируем итоговые результаты
            research_results_data = {
                'block1': block1_results,
                'metadata': {
                    'total_queries': len(block1_results.get('queries', [])),
                    'sources_count': self._count_sources([block1_results]),
                    'version': 'MVP-1.0'
                }
            }

            # Сохраняем в БД
            from datetime import datetime
            research_data = {
                "anketa_id": anketa_id,
                "user_id": anketa.get('telegram_id'),
                "session_id": anketa.get('id'),
                "research_type": "comprehensive_websearch_mvp",
                "llm_provider": "claude_code",
                "model": "sonnet-4.5",
                "status": "completed",
                "completed_at": datetime.now(),
                "research_results": research_results_data,
                "metadata": {
                    "queries_executed": len(block1_results.get('queries', [])),
                    "processing_time": 0
                }
            }

            # Сохраняем через метод БД
            research_id = self.db.save_research_results(research_data)

            logger.info(f"✅ Исследование завершено! ID: {research_id}")

            return {
                'status': 'success',
                'research_id': research_id,
                'anketa_id': anketa_id,
                'results': research_results_data,
                'agent_type': 'researcher',
                'provider_used': 'claude_code'
            }

        except Exception as e:
            logger.error(f"❌ Ошибка исследования анкеты {anketa_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Ошибка исследования анкеты: {str(e)}",
                'agent_type': 'researcher'
            }

    def _extract_placeholders_from_anketa(self, anketa: Dict) -> Dict:
        """Извлечь placeholders из анкеты"""
        # Попробуем извлечь из разных полей
        return {
            'РЕГИОН': anketa.get('geography', anketa.get('region', 'Россия')),
            'ПРОБЛЕМА': anketa.get('problem', anketa.get('project_description', 'неизвестная проблема')),
            'ЦЕЛЕВАЯ_ГРУППА': anketa.get('target_group', 'широкая аудитория'),
            'СФЕРА': anketa.get('sphere', anketa.get('category', 'социальная сфера')),
            'ПЕРИОД': '2022-2025'
        }

    def _research_block1_mvp(self, p: Dict) -> Dict:
        """
        MVP: Блок 1 - Проблема и социальная значимость (3 запроса)

        Полная версия будет иметь 10 запросов.
        """
        import requests
        import json

        results = {
            'block_name': 'Проблема и социальная значимость (MVP)',
            'queries': []
        }

        # Получаем Claude Code настройки
        claude_api_key = os.getenv('CLAUDE_CODE_API_KEY', '1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732')
        claude_base_url = os.getenv('CLAUDE_CODE_BASE_URL', 'http://178.236.17.55:8000')

        # Запрос 1: Официальная статистика
        logger.info("🔍 Запрос 1: Официальная статистика")
        q1 = self._websearch_simple(
            query=f"официальная статистика {p['ПРОБЛЕМА']} {p['РЕГИОН']} 2022-2025",
            claude_api_key=claude_api_key,
            claude_base_url=claude_base_url,
            context="Найди точные цифры и динамику проблемы из официальных источников (Росстат, министерства)"
        )
        results['queries'].append({
            'name': 'Официальная статистика',
            'query': q1['query'],
            'result': q1['result']
        })

        # Запрос 2: Государственные программы
        logger.info("🔍 Запрос 2: Государственные программы")
        q2 = self._websearch_simple(
            query=f"государственные программы нацпроекты {p['СФЕРА']} {p['ПРОБЛЕМА']} 2024-2025",
            claude_api_key=claude_api_key,
            claude_base_url=claude_base_url,
            context="Найди связь с нацпроектами и целевые показатели"
        )
        results['queries'].append({
            'name': 'Государственные программы',
            'query': q2['query'],
            'result': q2['result']
        })

        # Запрос 3: Успешные кейсы
        logger.info("🔍 Запрос 3: Успешные кейсы")
        q3 = self._websearch_simple(
            query=f"успешные проекты решение {p['ПРОБЛЕМА']} {p['РЕГИОН']} примеры 2022-2025",
            claude_api_key=claude_api_key,
            claude_base_url=claude_base_url,
            context="Найди 2-3 успешных кейса с измеримыми результатами"
        )
        results['queries'].append({
            'name': 'Успешные кейсы',
            'query': q3['query'],
            'result': q3['result']
        })

        return results

    def _websearch_simple(self, query: str, claude_api_key: str, claude_base_url: str, context: str = "") -> Dict:
        """
        Упрощенный WebSearch через Claude Code /chat endpoint

        Claude Code автоматически использует WebSearch tool при необходимости.
        """
        import requests
        import json

        headers = {
            "Authorization": f"Bearer {claude_api_key}",
            "Content-Type": "application/json"
        }

        # Промпт для Claude с инструкцией использовать WebSearch
        prompt = f"""
Выполни поиск информации по запросу: "{query}"

Задача: {context}

Требования:
- Используй WebSearch для поиска актуальной информации
- Приоритет российским источникам (rosstat.gov.ru, gov.ru, министерства)
- Данные не старше 3 лет (2022-2025)
- Верни краткое резюме (3-5 предложений) с конкретными фактами и цифрами
- Укажи 1-2 источника

Формат ответа:
РЕЗЮМЕ: [краткое резюме с фактами]
ИСТОЧНИКИ: [список URL источников]
"""

        payload = {
            "message": prompt,
            "model": "sonnet",
            "temperature": 0.3,
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                f"{claude_base_url}/chat",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                claude_response = data.get('response', 'Нет ответа')

                return {
                    'query': query,
                    'result': {
                        'summary': claude_response,
                        'raw_response': claude_response
                    }
                }
            else:
                logger.error(f"Claude API error: {response.status_code}")
                return {
                    'query': query,
                    'result': {
                        'summary': f"Ошибка API: {response.status_code}",
                        'raw_response': ''
                    }
                }

        except Exception as e:
            logger.error(f"❌ WebSearch ошибка: {e}")
            return {
                'query': query,
                'result': {
                    'summary': f"Ошибка поиска: {str(e)}",
                    'raw_response': ''
                }
            }

    def _count_sources(self, blocks: List[Dict]) -> int:
        """Подсчитать количество источников"""
        total = 0
        for block in blocks:
            for query in block.get('queries', []):
                # Простой подсчёт - позже улучшим
                result = query.get('result', {}).get('summary', '')
                if 'http' in result or 'gov.ru' in result:
                    total += 1
        return total