"""
LLM Router для переключения между различными провайдерами LLM
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from .gigachat_service import GigaChatService
from .local_llm_service import LocalLLMService

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Доступные провайдеры LLM"""
    LOCAL = "local"
    GIGACHAT = "gigachat"
    AUTO = "auto"

class LLMRouter:
    """Роутер для переключения между различными LLM провайдерами"""
    
    def __init__(self):
        """Инициализация роутера"""
        self.providers = {}
        self.current_provider = LLMProvider.AUTO
        self.fallback_order = [LLMProvider.LOCAL, LLMProvider.GIGACHAT]
        
        # Инициализация провайдеров
        self._init_providers()
        
    def _init_providers(self):
        """Инициализация всех доступных провайдеров"""
        try:
            # Локальный провайдер (Ollama)
            self.providers[LLMProvider.LOCAL] = LocalLLMService()
            logger.info("LocalLLMService инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации LocalLLMService: {e}")
            
        try:
            # GigaChat провайдер
            self.providers[LLMProvider.GIGACHAT] = GigaChatService()
            logger.info("GigaChatService инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации GigaChatService: {e}")
    
    def check_provider_health(self, provider: LLMProvider) -> bool:
        """
        Проверка работоспособности провайдера
        
        Args:
            provider: Провайдер для проверки
            
        Returns:
            True если провайдер работает
        """
        if provider not in self.providers:
            return False
            
        try:
            service = self.providers[provider]
            
            if provider == LLMProvider.LOCAL:
                return service.check_connection()
            elif provider == LLMProvider.GIGACHAT:
                # Для GigaChat можем проверить через простой запрос
                return True  # Пока считаем что работает
                
        except Exception as e:
            logger.error(f"Ошибка проверки провайдера {provider.value}: {e}")
            return False
            
        return False
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Получение списка доступных провайдеров"""
        available = []
        for provider in [LLMProvider.LOCAL, LLMProvider.GIGACHAT]:
            if self.check_provider_health(provider):
                available.append(provider)
        return available
    
    def set_provider(self, provider: LLMProvider):
        """
        Установка текущего провайдера
        
        Args:
            provider: Провайдер для использования
        """
        if provider in self.providers or provider == LLMProvider.AUTO:
            self.current_provider = provider
            logger.info(f"Установлен провайдер: {provider.value}")
        else:
            logger.error(f"Неизвестный провайдер: {provider}")
    
    def _select_best_provider(self) -> Optional[LLMProvider]:
        """Автоматический выбор лучшего доступного провайдера"""
        for provider in self.fallback_order:
            if self.check_provider_health(provider):
                logger.info(f"Выбран провайдер: {provider.value}")
                return provider
        
        logger.error("Нет доступных провайдеров!")
        return None
    
    def analyze_grant_application(self, 
                                application_text: str, 
                                grant_criteria: str,
                                preferred_provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """
        Анализ заявки на грант через выбранный провайдер
        
        Args:
            application_text: Текст заявки
            grant_criteria: Критерии гранта
            preferred_provider: Предпочитаемый провайдер (опционально)
            
        Returns:
            Результат анализа
        """
        # Определяем провайдера
        if preferred_provider and preferred_provider != LLMProvider.AUTO:
            target_provider = preferred_provider
        elif self.current_provider != LLMProvider.AUTO:
            target_provider = self.current_provider
        else:
            target_provider = self._select_best_provider()
        
        if not target_provider:
            return {
                'error': 'Нет доступных LLM провайдеров',
                'provider_used': None,
                'score': 0,
                'strengths': [],
                'weaknesses': ['Сервис временно недоступен'],
                'recommendations': ['Попробуйте позже'],
                'overall_score': 0
            }
        
        # Проверяем работоспособность провайдера
        if not self.check_provider_health(target_provider):
            logger.warning(f"Провайдер {target_provider.value} недоступен, пробуем fallback")
            target_provider = self._select_best_provider()
            
            if not target_provider:
                return {
                    'error': 'Все провайдеры недоступны',
                    'provider_used': None,
                    'score': 0,
                    'strengths': [],
                    'weaknesses': ['Сервис временно недоступен'],
                    'recommendations': ['Попробуйте позже'],
                    'overall_score': 0
                }
        
        try:
            service = self.providers[target_provider]
            logger.info(f"Использую провайдер: {target_provider.value}")
            
            # Вызываем анализ в зависимости от провайдера
            if target_provider == LLMProvider.LOCAL:
                result = service.analyze_grant_application(application_text, grant_criteria)
            elif target_provider == LLMProvider.GIGACHAT:
                # Для GigaChat используем существующий метод
                gigachat_result = service.analyze_grant_application(application_text, grant_criteria)
                
                # Преобразуем ответ GigaChat в стандартный формат
                if gigachat_result.get('status') == 'success':
                    result = {
                        'score': 8,  # Базовая оценка
                        'strengths': ['Анализ выполнен GigaChat'],
                        'weaknesses': [],
                        'recommendations': ['Рекомендации от GigaChat'],
                        'overall_score': 8,
                        'analysis': gigachat_result.get('analysis', ''),
                        'raw_response': gigachat_result
                    }
                else:
                    result = {
                        'error': gigachat_result.get('message', 'Ошибка GigaChat'),
                        'score': 0,
                        'strengths': [],
                        'weaknesses': ['Ошибка анализа'],
                        'recommendations': ['Попробуйте позже'],
                        'overall_score': 0
                    }
            else:
                result = {'error': f'Неподдерживаемый провайдер: {target_provider.value}'}
            
            # Добавляем информацию о провайдере
            result['provider_used'] = target_provider.value
            result['available_providers'] = [p.value for p in self.get_available_providers()]
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа через {target_provider.value}: {e}")
            
            # Пробуем fallback провайдер
            fallback_provider = self._select_best_provider()
            if fallback_provider and fallback_provider != target_provider:
                logger.info(f"Пробуем fallback провайдер: {fallback_provider.value}")
                return self.analyze_grant_application(
                    application_text, 
                    grant_criteria, 
                    fallback_provider
                )
            
            return {
                'error': f'Ошибка анализа: {str(e)}',
                'provider_used': target_provider.value,
                'score': 0,
                'strengths': [],
                'weaknesses': ['Техническая ошибка анализа'],
                'recommendations': ['Попробуйте повторить запрос'],
                'overall_score': 0
            }
    
    def _format_for_gigachat(self, application_text: str, grant_criteria: str) -> str:
        """Форматирование текста для GigaChat"""
        return f"""
Заявка на грант:
{application_text}

Критерии оценки:
{grant_criteria}

Проведи детальный анализ заявки.
"""
    
    def _parse_gigachat_response(self, response: str) -> Dict[str, Any]:
        """Парсинг ответа от GigaChat в стандартный формат"""
        # Базовый парсер - можно улучшить
        return {
            'score': 7,  # Заглушка
            'strengths': ['Анализ от GigaChat'],
            'weaknesses': [],
            'recommendations': ['Рекомендации от GigaChat'],
            'overall_score': 7,
            'raw_response': response
        }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Получение статуса всех провайдеров"""
        status = {
            'current_provider': self.current_provider.value,
            'providers': {}
        }
        
        for provider in [LLMProvider.LOCAL, LLMProvider.GIGACHAT]:
            is_healthy = self.check_provider_health(provider)
            provider_info = {
                'available': is_healthy,
                'name': provider.value
            }
            
            if provider == LLMProvider.LOCAL and provider in self.providers:
                try:
                    local_service = self.providers[provider]
                    provider_info['models'] = local_service.list_models()
                except:
                    provider_info['models'] = []
            
            status['providers'][provider.value] = provider_info
        
        status['available_providers'] = [p.value for p in self.get_available_providers()]
        
        return status

