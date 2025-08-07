#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Агент-исследователь для поиска грантов с использованием Perplexity API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from .base_agent import BaseAgent
from services.perplexity_service import PerplexityService
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """Агент-исследователь для поиска грантов"""
    
    def __init__(self, db):
        super().__init__('researcher', db)
        self.perplexity_service = PerplexityService()
    
    def _get_goal(self) -> str:
        return "Найти актуальные гранты и программы поддержки, соответствующие требованиям проекта"
    
    def _get_backstory(self) -> str:
        return """Ты опытный исследователь грантов с 10-летним стажем. 
        Ты специализируешься на поиске актуальных грантов и программ поддержки 
        для различных проектов. Ты знаешь все основные источники грантов 
        в России и за рубежом, умеешь анализировать требования и оценивать 
        шансы на получение финансирования."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка запроса на поиск грантов"""
        try:
            user_answers = input_data.get('user_answers', {})
            project_description = input_data.get('project_description', '')
            user_id = input_data.get('user_id', 0)
            session_id = input_data.get('session_id', 0)
            
            # Извлекаем ключевую информацию
            project_type = user_answers.get('project_type', '')
            region = user_answers.get('region', '')
            budget = user_answers.get('budget', '')
            experience = user_answers.get('experience', '')
            
            # Получаем промпты из базы данных
            researcher_prompts = self.db.get_agent_prompts('researcher')
            task_prompts = [p for p in researcher_prompts if p['prompt_type'] == 'task']
            
            all_results = []
            total_cost = 0.0
            
            # Выполняем каждый запрос из базы промптов
            for prompt in task_prompts:
                try:
                    # Формируем запрос на основе промпта и данных пользователя
                    query = self._build_query_from_prompt(prompt['prompt_content'], user_answers, project_description)
                    
                    # Выполняем поиск через Perplexity
                    search_result = self.perplexity_service.search_grants(
                        query=query,
                        region=region,
                        budget_range=budget
                    )
                    
                    # Логируем запрос
                    cost = search_result.get('usage', {}).get('cost', {}).get('total_cost', 0.0)
                    total_cost += cost
                    
                    self.db.log_researcher_query(
                        user_id=user_id,
                        session_id=session_id,
                        query_text=query,
                        perplexity_response=search_result.get('grants_info', ''),
                        sources=search_result.get('sources', []),
                        usage_stats=search_result.get('usage', {}),
                        cost=cost,
                        status='success' if search_result.get('status') == 'success' else 'error',
                        error_message=search_result.get('error')
                    )
                    
                    if search_result.get('status') == 'success':
                        all_results.append({
                            'prompt_name': prompt['prompt_name'],
                            'query': query,
                            'result': search_result.get('grants_info', ''),
                            'sources': search_result.get('sources', []),
                            'cost': cost
                        })
                        
                except Exception as e:
                    logger.error(f"Ошибка выполнения промпта {prompt['prompt_name']}: {e}")
                    self.db.log_researcher_query(
                        user_id=user_id,
                        session_id=session_id,
                        query_text=query if 'query' in locals() else prompt['prompt_content'],
                        status='error',
                        error_message=str(e)
                    )
            
            # Агрегируем результаты
            if all_results:
                aggregated_result = self._aggregate_results(all_results)
                
                return {
                    'status': 'success',
                    'results': all_results,
                    'aggregated_result': aggregated_result,
                    'total_cost': total_cost,
                    'queries_count': len(all_results),
                    'user_id': user_id,
                    'session_id': session_id
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Не удалось получить результаты ни по одному запросу',
                    'total_cost': total_cost,
                    'user_id': user_id,
                    'session_id': session_id
                }
                
        except Exception as e:
            logger.error(f"Ошибка обработки в Researcher Agent: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка обработки: {str(e)}"
            }
    
    def _build_search_query(self, project_type: str, region: str, budget: str, 
                           experience: str, project_description: str) -> str:
        """Построение поискового запроса"""
        query_parts = []
        
        if project_type:
            query_parts.append(f"проект типа: {project_type}")
        
        if region:
            query_parts.append(f"регион: {region}")
        
        if budget:
            query_parts.append(f"бюджет: {budget}")
        
        if experience:
            query_parts.append(f"опыт команды: {experience}")
        
        if project_description:
            query_parts.append(f"описание: {project_description}")
        
        # Формируем основной запрос
        if query_parts:
            base_query = f"Найди гранты для {' '.join(query_parts)}"
        else:
            base_query = "Найди актуальные гранты для малого бизнеса"
        
        return base_query
    
    def _analyze_grants(self, search_result: Dict, related_result: Dict) -> str:
        """Анализ найденных грантов"""
        try:
            # Анализируем основные гранты
            main_grants = search_result.get('grants_info', '')
            related_grants = related_result.get('related_grants', '')
            
            analysis_parts = []
            
            if main_grants:
                analysis_parts.append("## Основные найденные гранты:")
                analysis_parts.append(main_grants)
            
            if related_grants:
                analysis_parts.append("\n## Связанные программы поддержки:")
                analysis_parts.append(related_grants)
            
            # Добавляем рекомендации
            analysis_parts.append("\n## Рекомендации:")
            analysis_parts.append("- Приоритизируйте гранты с ближайшими сроками подачи")
            analysis_parts.append("- Обратите внимание на требования к заявителям")
            analysis_parts.append("- Подготовьте необходимые документы заранее")
            analysis_parts.append("- Рассмотрите возможность подачи в несколько программ")
            
            return "\n".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"Ошибка анализа грантов: {e}")
            return "Не удалось проанализировать найденные гранты"
    
    def generate_search_queries(self, user_answers: Dict[str, Any]) -> List[str]:
        """Генерация поисковых запросов на основе ответов пользователя"""
        queries = []
        
        project_type = user_answers.get('project_type', '')
        region = user_answers.get('region', '')
        budget = user_answers.get('budget', '')
        
        # Основной запрос
        if project_type:
            queries.append(f"гранты для {project_type}")
        
        # Региональные гранты
        if region:
            queries.append(f"гранты {region} {project_type}")
        
        # Бюджетные гранты
        if budget:
            queries.append(f"гранты {budget} {project_type}")
        
        # Комбинированные запросы
        if project_type and region:
            queries.append(f"программы поддержки {project_type} {region}")
        
        if project_type and budget:
            queries.append(f"финансирование {project_type} {budget}")
        
        # Общие запросы
        queries.extend([
            "гранты для малого бизнеса",
            "программы поддержки предпринимателей",
            "гранты для стартапов",
            "финансирование инновационных проектов"
        ])
        
        return queries[:10]  # Ограничиваем 10 запросами
    
    def test_perplexity_connection(self) -> Dict[str, Any]:
        """Тестирование подключения к Perplexity API"""
        try:
            test_result = self.perplexity_service.search_grants(
                query="гранты для малого бизнеса",
                region="Кемеровская область"
            )
            
            if test_result.get('status') == 'success':
                return {
                    'status': 'success',
                    'message': 'Perplexity API работает корректно',
                    'usage': test_result.get('usage', {})
                }
            else:
                return {
                    'status': 'error',
                    'message': test_result.get('error', 'Ошибка подключения к Perplexity')
                }
                
        except Exception as e:
            logger.error(f"Ошибка тестирования Perplexity: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка тестирования: {str(e)}"
            } 

    def _build_query_from_prompt(self, prompt_template: str, user_answers: Dict, project_description: str) -> str:
        """Формирование запроса на основе промпта и данных пользователя"""
        try:
            # Заменяем плейсхолдеры в промпте
            query = prompt_template
            
            # Заменяем переменные
            replacements = {
                '{project_type}': user_answers.get('project_type', ''),
                '{region}': user_answers.get('region', ''),
                '{budget}': user_answers.get('budget', ''),
                '{experience}': user_answers.get('experience', ''),
                '{team_size}': user_answers.get('team_size', ''),
                '{project_description}': project_description
            }
            
            for placeholder, value in replacements.items():
                query = query.replace(placeholder, str(value))
            
            return query
            
        except Exception as e:
            logger.error(f"Ошибка формирования запроса: {e}")
            return prompt_template
    
    def _aggregate_results(self, results: List[Dict]) -> str:
        """Агрегация результатов всех запросов"""
        try:
            aggregated_parts = []
            
            for result in results:
                aggregated_parts.append(f"## {result['prompt_name']}")
                aggregated_parts.append(result['result'])
                aggregated_parts.append("")  # Пустая строка для разделения
            
            # Добавляем общую статистику
            total_sources = sum(len(r['sources']) for r in results)
            total_cost = sum(r['cost'] for r in results)
            
            aggregated_parts.append("## Общая статистика")
            aggregated_parts.append(f"- Выполнено запросов: {len(results)}")
            aggregated_parts.append(f"- Найдено источников: {total_sources}")
            aggregated_parts.append(f"- Общая стоимость: ${total_cost:.4f}")
            
            return "\n".join(aggregated_parts)
            
        except Exception as e:
            logger.error(f"Ошибка агрегации результатов: {e}")
            return "Ошибка агрегации результатов" 