"""
Базовый класс для всех агентов GrantService
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from config.crewai_config import create_agent_with_perplexity, create_agent_with_gigachat
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from data.database import GrantServiceDatabase as Database

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, agent_type: str, db: Database):
        self.agent_type = agent_type
        self.db = db
        self.crewai_agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Настройка CrewAI агента"""
        try:
            # Получаем промпты из базы данных
            prompts = self.db.get_agent_prompts(self.agent_type)
            if not prompts:
                logger.warning(f"Нет промптов для агента {self.agent_type}")
                return
            
            # Основной системный промпт
            system_prompt = next((p['prompt_content'] for p in prompts if p['prompt_type'] == 'system'), '')
            
            # Выбираем LLM в зависимости от типа агента
            if self.agent_type == 'researcher':
                # Researcher использует Perplexity
                self.crewai_agent = create_agent_with_perplexity(
                    role=self.agent_type.title(),
                    goal=self._get_goal(),
                    backstory=self._get_backstory(),
                    system_message=system_prompt
                )
                logger.info(f"Агент {self.agent_type} создан с Perplexity")
            else:
                # Writer и Auditor используют GigaChat
                self.crewai_agent = create_agent_with_gigachat(
                    role=self.agent_type.title(),
                    goal=self._get_goal(),
                    backstory=self._get_backstory(),
                    system_message=system_prompt
                )
                logger.info(f"Агент {self.agent_type} создан с GigaChat")
            
        except Exception as e:
            logger.error(f"Ошибка создания агента {self.agent_type}: {e}")
    
    @abstractmethod
    def _get_goal(self) -> str:
        """Цель агента"""
        pass
    
    @abstractmethod
    def _get_backstory(self) -> str:
        """История агента"""
        pass
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка входных данных"""
        pass
    
    def get_prompts(self) -> list:
        """Получить все промпты агента"""
        return self.db.get_agent_prompts(self.agent_type)
    
    def update_prompt(self, prompt_id: int, content: str) -> bool:
        """Обновить промпт агента"""
        try:
            return self.db.update_agent_prompt(prompt_id, content)
        except Exception as e:
            logger.error(f"Ошибка обновления промпта: {e}")
            return False 