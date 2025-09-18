#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервис для работы с GigaChat API
"""

import os
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class GigaChatService:
    """Сервис для работы с GigaChat API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5Ojk4MmM0NjIyLTU3OWQtNDYxNi04YzVlLWIyMTY3YTZlNzI0NQ=="
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.access_token = None
        self.token_expires_at = 0
        
    def _get_access_token(self) -> str:
        """Получение access token для GigaChat"""
        try:
            # Проверяем, не истек ли токен
            if self.access_token and time.time() < self.token_expires_at:
                return self.access_token
                
            # Получаем новый токен
            auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": f"Basic {self.api_key}"
            }
            
            payload = {
                "scope": "GIGACHAT_API_PERS"
            }
            
            response = requests.post(auth_url, headers=headers, data=payload, verify=False)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                # Токен действует 30 минут, оставляем 5 минут запаса
                self.token_expires_at = time.time() + (25 * 60)
                return self.access_token
            else:
                logger.error(f"Ошибка получения токена: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка авторизации в GigaChat: {e}")
            return None
    
    def _make_request(self, payload: Dict) -> Optional[Dict]:
        """Выполнение запроса к GigaChat API"""
        try:
            token = self._get_access_token()
            if not token:
                return None
                
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                verify=False
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка API запроса: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка запроса к GigaChat: {e}")
            return None
    
    def analyze_grant_application(self, application_text: str, grant_criteria: str = "") -> Dict[str, Any]:
        """Анализ заявки на грант"""
        try:
            system_prompt = """Ты опытный эксперт по грантовым заявкам с 20-летним стажем. 
            Ты работал в комиссиях по рассмотрению заявок и знаешь все критерии оценки. 
            Твоя задача - объективно оценить заявку и дать конкретные рекомендации по улучшению.
            
            Проанализируй заявку по следующим критериям:
            1. Актуальность и новизна проекта (0-20 баллов)
            2. Обоснованность целей и задач (0-20 баллов)
            3. Методология и план реализации (0-20 баллов)
            4. Бюджет и ресурсы (0-20 баллов)
            5. Ожидаемые результаты и их значимость (0-20 баллов)
            
            Для каждого критерия дай:
            - Оценку в баллах
            - Краткий анализ сильных сторон
            - Конкретные рекомендации по улучшению
            
            В конце дай общую оценку готовности заявки к подаче."""
            
            user_prompt = f"""Проанализируй эту заявку на грант:

{application_text}

{f"Критерии гранта: {grant_criteria}" if grant_criteria else ""}

Дай подробный анализ по всем критериям и рекомендации."""
            
            payload = {
                "model": "GigaChat:latest",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,  # Низкая температура для аналитической задачи
                "max_tokens": 2000
            }
            
            response = self._make_request(payload)
            
            if response and 'choices' in response:
                analysis_text = response['choices'][0]['message']['content']
                
                return {
                    "status": "success",
                    "analysis": analysis_text,
                    "raw_response": response,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"status": "error", "message": "Не удалось получить ответ от GigaChat"}
                
        except Exception as e:
            logger.error(f"Ошибка анализа заявки: {e}")
            return {"status": "error", "message": f"Ошибка анализа: {str(e)}"}
    
    def improve_grant_text(self, text: str, improvement_type: str = "general") -> Dict[str, Any]:
        """Улучшение текста заявки"""
        try:
            improvement_prompts = {
                "general": "Улучши этот текст заявки, сделай его более убедительным и профессиональным",
                "budget": "Улучши обоснование бюджета в этой заявке",
                "methodology": "Улучши описание методологии в этой заявке",
                "goals": "Улучши формулировку целей и задач в этой заявке"
            }
            
            prompt = improvement_prompts.get(improvement_type, improvement_prompts["general"])
            
            payload = {
                "model": "GigaChat:latest",
                "messages": [
                    {"role": "user", "content": f"{prompt}:\n\n{text}"}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            response = self._make_request(payload)
            
            if response and 'choices' in response:
                improved_text = response['choices'][0]['message']['content']
                
                return {
                    "status": "success",
                    "improved_text": improved_text,
                    "original_text": text,
                    "improvement_type": improvement_type
                }
            else:
                return {"status": "error", "message": "Не удалось улучшить текст"}
                
        except Exception as e:
            logger.error(f"Ошибка улучшения текста: {e}")
            return {"status": "error", "message": f"Ошибка: {str(e)}"}
