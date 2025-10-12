#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grant Crew - оркестратор для координации работы агентов
"""
from typing import Dict, Any, List
import logging
import sys
import os
import asyncio
import time

# Добавляем пути к модулям
sys.path.append('/var/GrantService/shared')
sys.path.append('/var/GrantService/telegram-bot/services')
sys.path.append('/var/GrantService/agents')

try:
    from agents.researcher_agent import ResearcherAgent
    from agents.writer_agent import WriterAgent
    from agents.auditor_agent import AuditorAgent
    from agents.interviewer_agent import InterviewerAgent
except ImportError as e:
    logger.error(f"Ошибка импорта агентов: {e}")
    # Fallback для случаев, когда импорт не работает
    ResearcherAgent = None
    WriterAgent = None
    AuditorAgent = None
    InterviewerAgent = None

logger = logging.getLogger(__name__)

class GrantCrew:
    """Оркестратор для координации работы агентов согласно AGENTS_DATA_FLOW.md"""
    
    def __init__(self, db=None):
        self.db = db
        self.agents = {}
        self.workflow_results = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Инициализация всех агентов"""
        try:
            if ResearcherAgent:
                self.agents['researcher'] = ResearcherAgent(self.db)
            if WriterAgent:
                self.agents['writer'] = WriterAgent(self.db)
            if AuditorAgent:
                self.agents['auditor'] = AuditorAgent(self.db)
            if InterviewerAgent:
                self.agents['interviewer'] = InterviewerAgent(self.db)
                
            logger.info(f"Инициализированы агенты: {list(self.agents.keys())}")
        except Exception as e:
            logger.error(f"Ошибка инициализации агентов: {e}")
    
    async def execute_full_workflow_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение полного workflow согласно AGENTS_DATA_FLOW.md:
        Interviewer → Analyst → Researcher → Writer → Auditor
        """
        try:
            start_time = time.time()
            logger.info("🚀 Запуск полного workflow агентов")
            
            workflow_result = {
                'status': 'success',
                'stages': {},
                'final_application': None,
                'audit_results': None,
                'processing_time': 0,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Этап 1: Interviewer - создание персонализированных вопросов
            if 'interviewer' in self.agents:
                logger.info("📋 Этап 1: Создание вопросов (Interviewer)")
                interviewer_result = await self.agents['interviewer'].create_questions_async(input_data)
                workflow_result['stages']['interviewer'] = interviewer_result
                
                # Передаем результат дальше
                input_data['interview_questions'] = interviewer_result.get('questions', {})
            
            # Этап 2: Auditor - проверка корректности анкеты
            if 'auditor' in self.agents:
                logger.info("✅ Этап 2: Проверка анкеты (Auditor)")
                auditor_result = await self.agents['auditor'].audit_anketa_async(input_data)
                workflow_result['stages']['auditor'] = auditor_result

                # Проверяем одобрение
                if auditor_result.get('approval_status') != 'approved':
                    logger.warning(f"⚠️ Auditor не одобрил анкету: {auditor_result.get('approval_status')}")
                    workflow_result['status'] = 'rejected_by_auditor'
                    workflow_result['rejection_reason'] = auditor_result.get('feedback', 'Анкета не прошла проверку')
                    return workflow_result

                logger.info(f"✅ Auditor одобрил анкету (score: {auditor_result.get('quality_score', 0)}/10)")

            # Этап 3: Researcher V2 - 27 экспертных запросов через Claude Code WebSearch
            logger.info("🔍 Этап 3: Исследование через 27 запросов (Researcher V2)")

            try:
                from agents.researcher_agent_v2 import ResearcherAgentV2

                researcher_v2 = ResearcherAgentV2(self.db, llm_provider="claude_code")

                # Получаем anketa_id из input_data
                anketa_id = input_data.get('anketa_id') or input_data.get('session_id')

                if not anketa_id:
                    logger.error("❌ Не найден anketa_id для Researcher")
                    workflow_result['stages']['researcher'] = {
                        'status': 'error',
                        'message': 'anketa_id не передан'
                    }
                else:
                    # Запускаем 27 запросов
                    research_result = await researcher_v2.research_with_expert_prompts(anketa_id)
                    workflow_result['stages']['researcher'] = research_result

                    # Передаем результат дальше (для Writer)
                    if research_result.get('status') == 'completed':
                        input_data['research_data'] = research_result.get('research_results', {})
                        logger.info(f"✅ Researcher V2 завершен: {research_result.get('metadata', {}).get('total_queries', 0)} запросов")
                    else:
                        logger.warning(f"⚠️ Researcher V2 не завершился: {research_result.get('status')}")

            except ImportError as e:
                logger.error(f"❌ ResearcherAgentV2 не найден: {e}")
                workflow_result['stages']['researcher'] = {
                    'status': 'error',
                    'message': f'ResearcherAgentV2 import failed: {str(e)}'
                }
            except Exception as e:
                logger.error(f"❌ Researcher V2 error: {e}")
                workflow_result['stages']['researcher'] = {
                    'status': 'error',
                    'message': str(e)
                }
            
            # Этап 4: Writer - создание заявки
            if 'writer' in self.agents:
                logger.info("✍️ Этап 4: Создание заявки (Writer)")
                writer_result = await self.agents['writer'].write_application_async(input_data)
                workflow_result['stages']['writer'] = writer_result
                
                # Передаем результат дальше
                input_data['application'] = writer_result.get('application', {})
                workflow_result['final_application'] = writer_result.get('application', {})
            
            # Этап 5: Reviewer - финальная оценка готовности гранта
            if 'reviewer' in self.agents:
                logger.info("🔎 Этап 5: Финальная оценка гранта (Reviewer)")
                review_result = await self.agents['reviewer'].review_grant_async(input_data)
                workflow_result['stages']['reviewer'] = review_result
                workflow_result['review_results'] = review_result

                # Логируем вероятность одобрения
                approval_prob = review_result.get('approval_probability', 0)
                readiness_score = review_result.get('readiness_score', 0)
                logger.info(f"📊 Reviewer оценка: {readiness_score}/10, вероятность одобрения: {approval_prob}%")
            else:
                logger.warning("⚠️ Reviewer agent не инициализирован, пропускаем этап 5")
            
            # Завершение workflow
            processing_time = time.time() - start_time
            workflow_result['processing_time'] = processing_time
            
            # Определяем общий статус
            failed_stages = [stage for stage, result in workflow_result['stages'].items() 
                           if result.get('status') == 'error']
            
            if failed_stages:
                workflow_result['status'] = 'partial_success'
                workflow_result['failed_stages'] = failed_stages
            
            logger.info(f"✅ Workflow завершен за {processing_time:.2f}с")
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения workflow: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'stages': getattr(self, 'workflow_results', {}),
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def execute_full_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронная обертка для полного workflow"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.execute_full_workflow_async(input_data))
        except RuntimeError:
            return asyncio.run(self.execute_full_workflow_async(input_data))
    
    async def execute_stage_async(self, stage_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение отдельного этапа workflow"""
        try:
            if stage_name not in self.agents:
                return {
                    'status': 'error',
                    'message': f'Агент {stage_name} не найден'
                }
            
            agent = self.agents[stage_name]
            
            # Маршрутизация к соответствующему методу агента
            if stage_name == 'interviewer':
                return await agent.create_questions_async(input_data)
            elif stage_name == 'researcher':
                return await agent.research_grants_async(input_data)
            elif stage_name == 'writer':
                return await agent.write_application_async(input_data)
            elif stage_name == 'auditor':
                return await agent.audit_application_async(input_data)
            else:
                return await agent.process_async(input_data)
                
        except Exception as e:
            logger.error(f"Ошибка выполнения этапа {stage_name}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'stage': stage_name
            }
    
    def execute_stage(self, stage_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронная обертка для выполнения этапа"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.execute_stage_async(stage_name, input_data))
        except RuntimeError:
            return asyncio.run(self.execute_stage_async(stage_name, input_data))
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Получение статуса workflow"""
        return {
            'available_agents': list(self.agents.keys()),
            'workflow_stages': [
                'interviewer', 'analyst', 'researcher', 'writer', 'auditor'
            ],
            'implemented_stages': [stage for stage in ['interviewer', 'researcher', 'writer', 'auditor'] 
                                 if stage in self.agents],
            'missing_stages': ['analyst'],
            'last_results': getattr(self, 'workflow_results', {})
        }
    
    def create_questions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание вопросов для интервью"""
        if 'interviewer' not in self.agents:
            return {'status': 'error', 'message': 'Interviewer agent недоступен'}
        
        return self.agents['interviewer'].create_questions(input_data)
    
    def research_grants(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Исследование грантов"""
        if 'researcher' not in self.agents:
            return {'status': 'error', 'message': 'Researcher agent недоступен'}
        
        return self.agents['researcher'].research_grants(input_data)
    
    def write_application(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки"""
        if 'writer' not in self.agents:
            return {'status': 'error', 'message': 'Writer agent недоступен'}
        
        return self.agents['writer'].write_application(input_data)
    
    def audit_application(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Аудит заявки"""
        if 'auditor' not in self.agents:
            return {'status': 'error', 'message': 'Auditor agent недоступен'}
        
        return self.agents['auditor'].audit_application(input_data)
    
    # Методы для совместимости с CrewAI (если понадобится)
    def kickoff(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Совместимость с CrewAI интерфейсом"""
        return self.execute_full_workflow(inputs)
    
    def get_execution_logs(self) -> List[str]:
        """Получение логов выполнения"""
        # Можно добавить более детальное логирование
        return [
            f"Workflow status: {len(self.agents)} agents initialized",
            f"Available stages: {', '.join(self.agents.keys())}"
        ]

# Фабричная функция для создания crew
def create_grant_crew(db=None) -> GrantCrew:
    """Создание экземпляра GrantCrew"""
    return GrantCrew(db)

# Совместимость с существующим кодом
class LegacyGrantCrew:
    """Legacy совместимость для старого кода"""
    
    def __init__(self, db=None):
        self.modern_crew = GrantCrew(db)
    
    def research_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.modern_crew.research_grants(input_data)
    
    def writing_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.modern_crew.write_application(input_data)
    
    def audit_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.modern_crew.audit_application(input_data)
