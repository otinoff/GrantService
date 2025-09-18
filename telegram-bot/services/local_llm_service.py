"""
Сервис для работы с локальными LLM через Ollama
"""
import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LocalLLMService:
    """Сервис для работы с локальными LLM через Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Инициализация сервиса
        
        Args:
            base_url: URL сервера Ollama
        """
        self.base_url = base_url
        self.default_model = "qwen2.5:3b"
        
    def check_connection(self) -> bool:
        """Проверка подключения к Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка подключения к Ollama: {e}")
            return False
    
    def list_models(self) -> list:
        """Получение списка доступных моделей"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Ошибка получения списка моделей: {e}")
            return []
    
    def generate_response(self, 
                         prompt: str, 
                         model: Optional[str] = None,
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> Optional[str]:
        """
        Генерация ответа от локальной LLM
        
        Args:
            prompt: Пользовательский промпт
            model: Название модели (по умолчанию self.default_model)
            system_prompt: Системный промпт
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов
            
        Returns:
            Ответ модели или None в случае ошибки
        """
        if not model:
            model = self.default_model
            
        # Формируем сообщения
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.info(f"Отправка запроса к модели {model}")
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120  # Увеличенный таймаут для локальных моделей
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('message', {}).get('content', '')
                logger.info(f"Получен ответ длиной {len(content)} символов")
                return content
            else:
                logger.error(f"Ошибка API Ollama: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return None
    
    def analyze_grant_application(self, 
                                application_text: str, 
                                grant_criteria: str) -> Dict[str, Any]:
        """
        Анализ заявки на грант с помощью локальной LLM
        
        Args:
            application_text: Текст заявки
            grant_criteria: Критерии гранта
            
        Returns:
            Результат анализа
        """
        system_prompt = """Ты - эксперт по анализу грантовых заявок. 
Твоя задача - провести детальный анализ заявки и дать рекомендации.
Отвечай на русском языке, структурированно и объективно."""
        
        user_prompt = f"""
Проанализируй следующую заявку на грант:

ЗАЯВКА:
{application_text}

КРИТЕРИИ ГРАНТА:
{grant_criteria}

Проведи анализ по следующим параметрам:
1. СООТВЕТСТВИЕ КРИТЕРИЯМ (оценка 1-10)
2. СИЛЬНЫЕ СТОРОНЫ
3. СЛАБЫЕ СТОРОНЫ  
4. РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ
5. ОБЩАЯ ОЦЕНКА (1-10)

Формат ответа:
ОЦЕНКА: [число от 1 до 10]
СИЛЬНЫЕ СТОРОНЫ: [список]
СЛАБЫЕ СТОРОНЫ: [список]
РЕКОМЕНДАЦИИ: [список рекомендаций]
ОБЩАЯ ОЦЕНКА: [число от 1 до 10]
"""
        
        try:
            response = self.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Низкая температура для более консистентного анализа
                max_tokens=1500
            )
            
            if response:
                return self._parse_analysis_response(response)
            else:
                return {
                    'score': 0,
                    'strengths': ['Ошибка анализа'],
                    'weaknesses': ['Не удалось получить ответ от модели'],
                    'recommendations': ['Попробуйте повторить анализ'],
                    'overall_score': 0,
                    'raw_response': ''
                }
                
        except Exception as e:
            logger.error(f"Ошибка анализа заявки: {e}")
            return {
                'score': 0,
                'strengths': [],
                'weaknesses': [f'Системная ошибка: {str(e)}'],
                'recommendations': [],
                'overall_score': 0,
                'raw_response': ''
            }
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Парсинг ответа анализа в структурированный формат"""
        try:
            lines = response.split('\n')
            result = {
                'score': 5,
                'strengths': [],
                'weaknesses': [],
                'recommendations': [],
                'overall_score': 5,
                'raw_response': response
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Поиск секций
                if line.upper().startswith('ОЦЕНКА:'):
                    try:
                        score = int(''.join(filter(str.isdigit, line.split(':')[1])))
                        result['score'] = max(1, min(10, score))
                    except:
                        pass
                        
                elif line.upper().startswith('СИЛЬНЫЕ СТОРОНЫ:'):
                    current_section = 'strengths'
                    content = line.split(':', 1)[1].strip()
                    if content:
                        result['strengths'].append(content)
                        
                elif line.upper().startswith('СЛАБЫЕ СТОРОНЫ:'):
                    current_section = 'weaknesses'
                    content = line.split(':', 1)[1].strip()
                    if content:
                        result['weaknesses'].append(content)
                        
                elif line.upper().startswith('РЕКОМЕНДАЦИИ:'):
                    current_section = 'recommendations'
                    content = line.split(':', 1)[1].strip()
                    if content:
                        result['recommendations'].append(content)
                        
                elif line.upper().startswith('ОБЩАЯ ОЦЕНКА:'):
                    try:
                        score = int(''.join(filter(str.isdigit, line.split(':')[1])))
                        result['overall_score'] = max(1, min(10, score))
                    except:
                        pass
                    current_section = None
                    
                # Добавление элементов списка
                elif current_section and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    item = line[1:].strip()
                    if item:
                        result[current_section].append(item)
                        
                # Простые строки в текущей секции
                elif current_section and line and not line.upper().startswith(('ОЦЕНКА:', 'СИЛЬНЫЕ', 'СЛАБЫЕ', 'РЕКОМЕНДАЦИИ:', 'ОБЩАЯ')):
                    result[current_section].append(line)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа: {e}")
            return {
                'score': 5,
                'strengths': [],
                'weaknesses': ['Ошибка парсинга ответа'],
                'recommendations': [],
                'overall_score': 5,
                'raw_response': response
            }
