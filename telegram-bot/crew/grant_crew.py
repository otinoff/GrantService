"""
Grant Crew - оркестратор для координации работы агентов
"""
from typing import Dict, Any, List
import logging
from config.crewai_config import create_task_with_perplexity, create_task_with_gigachat, create_crew_with_gigachat
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.auditor_agent import AuditorAgent
from data.database import GrantServiceDatabase as Database

logger = logging.getLogger(__name__)

class GrantCrew:
    """Оркестратор для координации работы агентов"""
    
    def __init__(self, db: Database):
        self.db = db
        self.researcher = ResearcherAgent(db)
        self.writer = WriterAgent(db)
        self.auditor = AuditorAgent(db)
        self.crew = None
        self._setup_crew()
    
    def _setup_crew(self):
        """Настройка команды агентов"""
        try:
            # Создаем задачи для каждого агента
            research_task = create_task_with_perplexity(
                description="Найти подходящие гранты и собрать информацию",
                agent=self.researcher.crewai_agent,
                expected_output="Список подходящих грантов с детальной информацией"
            )
            
            writing_task = create_task_with_gigachat(
                description="Создать заявку на грант на основе найденной информации",
                agent=self.writer.crewai_agent,
                expected_output="Полная заявка на грант со всеми разделами",
                context=[research_task]
            )
            
            audit_task = create_task_with_gigachat(
                description="Провести анализ качества заявки и дать рекомендации",
                agent=self.auditor.crewai_agent,
                expected_output="Отчет о качестве заявки с рекомендациями",
                context=[writing_task]
            )
            
            # Создаем команду
            self.crew = create_crew_with_gigachat(
                agents=[self.researcher.crewai_agent, self.writer.crewai_agent, self.auditor.crewai_agent],
                tasks=[research_task, writing_task, audit_task]
            )
            
            logger.info("Команда агентов успешно создана")
            
        except Exception as e:
            logger.error(f"Ошибка создания команды: {e}")
    
    def process_application(self, user_answers: Dict[str, Any], project_description: str = "") -> Dict[str, Any]:
        """Обработка заявки через команду агентов"""
        try:
            # Подготавливаем входные данные
            input_data = {
                'user_answers': user_answers,
                'project_description': project_description
            }
            
            # Запускаем команду
            if self.crew:
                result = self.crew.kickoff(inputs=input_data)
                
                # Обрабатываем результаты
                processed_result = self._process_crew_result(result, input_data)
                
                return {
                    'status': 'success',
                    'result': processed_result,
                    'crew_output': result
                }
            else:
                # Fallback - обработка без CrewAI
                return self._process_without_crew(input_data)
                
        except Exception as e:
            logger.error(f"Ошибка обработки заявки командой: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка обработки: {str(e)}"
            }
    
    def _process_crew_result(self, crew_result: Any, input_data: Dict) -> Dict[str, Any]:
        """Обработка результата команды"""
        try:
            # Извлекаем результаты каждого агента
            research_result = self.researcher.process(input_data)
            writing_result = self.writer.process({
                **input_data,
                'research_data': research_result
            })
            audit_result = self.auditor.process({
                **input_data,
                'application': writing_result.get('application', {}),
                'research_data': research_result
            })
            
            return {
                'research': research_result,
                'writing': writing_result,
                'audit': audit_result,
                'crew_output': str(crew_result)
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки результата команды: {e}")
            return {
                'error': str(e),
                'crew_output': str(crew_result)
            }
    
    def _process_without_crew(self, input_data: Dict) -> Dict[str, Any]:
        """Обработка без CrewAI (fallback)"""
        try:
            # Последовательная обработка агентами
            research_result = self.researcher.process(input_data)
            
            if research_result.get('status') == 'success':
                writing_result = self.writer.process({
                    **input_data,
                    'research_data': research_result
                })
                
                if writing_result.get('status') == 'success':
                    audit_result = self.auditor.process({
                        **input_data,
                        'application': writing_result.get('application', {}),
                        'research_data': research_result
                    })
                    
                    return {
                        'status': 'success',
                        'research': research_result,
                        'writing': writing_result,
                        'audit': audit_result,
                        'method': 'sequential'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Ошибка создания заявки',
                        'research': research_result
                    }
            else:
                return {
                    'status': 'error',
                    'message': 'Ошибка поиска грантов',
                    'research': research_result
                }
                
        except Exception as e:
            logger.error(f"Ошибка последовательной обработки: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка обработки: {str(e)}"
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Получить статус агентов"""
        return {
            'researcher': {
                'available': self.researcher.crewai_agent is not None,
                'prompts_count': len(self.researcher.get_prompts())
            },
            'writer': {
                'available': self.writer.crewai_agent is not None,
                'prompts_count': len(self.writer.get_prompts())
            },
            'auditor': {
                'available': self.auditor.crewai_agent is not None,
                'prompts_count': len(self.auditor.get_prompts())
            },
            'crew_available': self.crew is not None
        }
    
    def test_agents(self) -> Dict[str, Any]:
        """Тестирование агентов"""
        test_data = {
            'user_answers': {
                'project_type': 'малый бизнес',
                'region': 'Кемеровская область',
                'budget': '500 000'
            },
            'project_description': 'Развитие малого бизнеса в регионе'
        }
        
        results = {}
        
        # Тестируем каждого агента отдельно
        try:
            results['researcher'] = self.researcher.process(test_data)
        except Exception as e:
            results['researcher'] = {'status': 'error', 'message': str(e)}
        
        try:
            results['writer'] = self.writer.process(test_data)
        except Exception as e:
            results['writer'] = {'status': 'error', 'message': str(e)}
        
        try:
            results['auditor'] = self.auditor.process(test_data)
        except Exception as e:
            results['auditor'] = {'status': 'error', 'message': str(e)}
        
        return results 