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
    print("⚠️ LLM Router недоступен")
    LLMRouter = None
    LLMProvider = None
    LLM_ROUTER_AVAILABLE = False

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """Агент-исследователь для анализа рынка и поиска грантов"""
    
    def __init__(self, db, llm_provider: str = "auto"):
        super().__init__("researcher", db, llm_provider)
        
        if UNIFIED_CLIENT_AVAILABLE:
            self.llm_client = UnifiedLLMClient()
            self.config = AGENT_CONFIGS.get("researcher", AGENT_CONFIGS.get("writer", {}))
        elif LLM_ROUTER_AVAILABLE:
            self.llm_router = LLMRouter()
        else:
            self.llm_client = None
            self.llm_router = None
            print("⚠️ Researcher агент работает без LLM сервисов")
    
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
        """Исследование на основе анкеты"""
        try:
            # Получаем анкету из базы данных
            anketa = self.db.get_session_by_anketa_id(anketa_id)
            
            if not anketa:
                return {
                    'status': 'error',
                    'message': f'Анкета {anketa_id} не найдена',
                    'agent_type': 'researcher'
                }
            
            # Получаем данные пользователя
            user_data = {
                "telegram_id": anketa["telegram_id"],
                "username": anketa.get("username"),
                "first_name": anketa.get("first_name"),
                "last_name": anketa.get("last_name")
            }
            
            # Проводим исследование
            # Преобразуем данные интервью в строку для исследования
            interview_text = ""
            if isinstance(anketa["interview_data"], dict):
                for key, value in anketa["interview_data"].items():
                    interview_text += f"{key}: {value}\n"
            else:
                interview_text = str(anketa["interview_data"])
            
            research_results = self.research_grant({
                "description": interview_text,
                "llm_provider": "perplexity"  # Используем Perplexity для исследований
            })
            
            if research_results.get('status') == 'error':
                return research_results
            
            # Сохраняем результаты исследования
            research_data = {
                "anketa_id": anketa_id,
                "user_data": user_data,
                "session_id": anketa["id"],
                "research_type": "comprehensive",
                "llm_provider": research_results.get('provider_used', 'perplexity'),
                "model": research_results.get('llm_settings', {}).get('model', 'sonar'),
                "research_results": research_results.get('result', ''),
                "metadata": {
                    "tokens_used": research_results.get('llm_settings', {}).get('tokens_used', 0),
                    "processing_time_seconds": research_results.get('processing_time', 0),
                    "cost": research_results.get('cost', 0.0)
                }
            }
            
            # Сохраняем в базу данных
            research_id = self.db.save_research_results(research_data)
            
            if research_id:
                return {
                    'status': 'success',
                    'research_id': research_id,
                    'anketa_id': anketa_id,
                    'result': research_results.get('result', ''),
                    'agent_type': 'researcher',
                    'provider_used': research_results.get('provider_used', 'perplexity')
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Ошибка сохранения результатов исследования',
                    'agent_type': 'researcher'
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка исследования анкеты {anketa_id}: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка исследования анкеты: {str(e)}",
                'agent_type': 'researcher'
            }