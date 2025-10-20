#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Базовый класс для всех агентов GrantService
"""
import sys
import os

# Cross-platform path setup
from pathlib import Path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "telegram-bot" / "services"))
sys.path.insert(0, str(_project_root / "web-admin"))
sys.path.insert(0, str(_project_root / "web-admin" / "utils"))
sys.path.insert(0, str(_project_root / "data" / "database"))
sys.path.insert(0, str(_project_root / "agents"))

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

import json
from datetime import datetime

# Добавляем путь к модулям базы данных

try:
    from data.database.prompts import get_prompts_by_agent, format_prompt
    PROMPTS_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Модуль промптов недоступен: {e}")
    PROMPTS_AVAILABLE = False

class BaseAgent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, agent_type: str, db, llm_provider: str = "claude_code"):
        self.agent_type = agent_type
        self.db = db
        self.llm_provider = llm_provider
        self.prompts = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Загрузить промпты из базы данных"""
        if not PROMPTS_AVAILABLE:
            print(f"[WARN] Промпты для агента {self.agent_type} не загружены (модуль недоступен)")
            return

        try:
            prompts = get_prompts_by_agent(self.agent_type)
            for prompt in prompts:
                self.prompts[prompt['name']] = prompt
            print(f"[OK] Загружено {len(prompts)} промптов для агента {self.agent_type}")
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки промптов для агента {self.agent_type}: {e}")
    
    def get_prompt(self, prompt_name: str) -> Optional[Dict]:
        """Получить промпт по названию"""
        return self.prompts.get(prompt_name)
    
    def format_prompt(self, prompt_name: str, variables: Dict[str, Any]) -> Optional[str]:
        """Форматировать промпт с переменными"""
        prompt_data = self.get_prompt(prompt_name)
        if not prompt_data:
            print(f"[WARN] Промпт '{prompt_name}' не найден для агента {self.agent_type}")
            return None

        try:
            return format_prompt(prompt_data['prompt_template'], variables)
        except Exception as e:
            print(f"[ERROR] Ошибка форматирования промпта '{prompt_name}': {e}")
            return None
    
    def get_available_prompts(self) -> List[str]:
        """Получить список доступных промптов"""
        return list(self.prompts.keys())
    
    def log_activity(self, action: str, data: Dict[str, Any] = None):
        """Логировать активность агента"""
        try:
            log_entry = {
                'agent_type': self.agent_type,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'data': data or {}
            }

            # Здесь можно добавить логирование в базу данных или файл
            print(f"[LOG] [{self.agent_type}] {action}: {json.dumps(log_entry, ensure_ascii=False)}")

        except Exception as e:
            print(f"[ERROR] Ошибка логирования активности агента {self.agent_type}: {e}")
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод обработки данных"""
        pass
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Валидация входных данных"""
        # Базовая валидация - можно переопределить в наследниках
        return isinstance(data, dict) and len(data) > 0
    
    def prepare_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка выходных данных"""
        output = {
            'agent_type': self.agent_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'result': result
        }
        
        self.log_activity('output_prepared', {'output_keys': list(result.keys())})
        return output
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Обработка ошибок"""
        error_output = {
            'agent_type': self.agent_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': str(error),
            'error_type': type(error).__name__,
            'context': context
        }
        
        self.log_activity('error_occurred', error_output)
        return error_output
