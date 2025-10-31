#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reviewer Agent (Final Auditor) - финальная оценка готовности гранта к подаче
Проверяет заявку после Writer Agent V2 на основе 4 критериев
"""
import sys
import os
from typing import Dict, Any, List, Optional
import logging
import asyncio
import time
import json
import re

# Добавляем пути к модулям (работает на Windows и Linux)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'shared'))
sys.path.insert(0, os.path.join(project_root, 'telegram-bot', 'services'))
sys.path.insert(0, os.path.join(project_root, 'web-admin'))

# Initialize logger before any imports that might use it
logger = logging.getLogger(__name__)

try:
    from agents.base_agent import BaseAgent
except ImportError:
    # Fallback если BaseAgent недоступен
    class BaseAgent:
        def __init__(self, name, db, llm_provider=None):
            self.name = name
            self.db = db
            self.llm_provider = llm_provider

# Импорт Expert Agent для получения требований из векторной БД
try:
    sys.path.insert(0, os.path.join(project_root, 'expert_agent'))
    from expert_agent import ExpertAgent
    EXPERT_AGENT_AVAILABLE = True
except ImportError:
    EXPERT_AGENT_AVAILABLE = False
    ExpertAgent = None
    logger.warning("⚠️ ExpertAgent недоступен - review будет без векторной БД")

# Импорт DatabasePromptManager для загрузки промптов из БД
try:
    from utils.prompt_manager import DatabasePromptManager, get_database_prompt_manager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    PROMPT_MANAGER_AVAILABLE = False
    DatabasePromptManager = None

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    UNIFIED_CLIENT_AVAILABLE = False
    UnifiedLLMClient = None
    AGENT_CONFIGS = {}

logger = logging.getLogger(__name__)

class ReviewerAgent(BaseAgent):
    """Final Auditor - агент для финальной оценки готовности гранта"""

    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("reviewer", db, llm_provider)

        # Инициализация Expert Agent для получения требований из векторной БД
        self.expert_agent: Optional[ExpertAgent] = None
        if EXPERT_AGENT_AVAILABLE:
            try:
                self.expert_agent = ExpertAgent()
                logger.info("✅ Reviewer Agent: Expert Agent подключен (требования ФПГ из векторной БД)")
            except Exception as e:
                logger.warning(f"⚠️ Reviewer: Не удалось инициализировать Expert Agent: {e}")
                self.expert_agent = None

        # Инициализация DatabasePromptManager для загрузки промптов из БД
        self.prompt_manager: Optional[DatabasePromptManager] = None
        if PROMPT_MANAGER_AVAILABLE:
            try:
                self.prompt_manager = get_database_prompt_manager()
                logger.info("✅ Reviewer Agent: DatabasePromptManager подключен (goal, backstory из БД)")
            except Exception as e:
                logger.warning(f"⚠️ Reviewer: Не удалось инициализировать PromptManager: {e}")

        if UNIFIED_CLIENT_AVAILABLE:
            # Передаем provider в конструктор UnifiedLLMClient
            self.llm_client = UnifiedLLMClient(provider=llm_provider)
            self.config = AGENT_CONFIGS.get("reviewer", AGENT_CONFIGS.get("auditor", {}))

        # Веса критериев оценки (сумма = 100%)
        self.WEIGHTS = {
            'evidence_base': 0.40,      # 40% - доказательная база
            'structure': 0.30,           # 30% - структура и полнота
            'matching': 0.20,            # 20% - индикаторный матчинг
            'economics': 0.10            # 10% - экономическое обоснование
        }

    def _get_goal(self) -> str:
        """Получить goal агента из БД с fallback"""
        if self.prompt_manager:
            try:
                goal = self.prompt_manager.get_prompt('reviewer', 'goal')
                if goal:
                    logger.info("✅ Reviewer: Goal загружен из БД")
                    return goal
            except Exception as e:
                logger.warning(f"⚠️ Reviewer: Ошибка загрузки goal из БД: {e}")

        # Fallback на hardcoded
        logger.info("Reviewer: Используется hardcoded goal")
        return "Провести финальную оценку готовности гранта к подаче и рассчитать вероятность одобрения (40-50%)"

    def _get_backstory(self) -> str:
        """Получить backstory агента из БД с fallback"""
        if self.prompt_manager:
            try:
                backstory = self.prompt_manager.get_prompt('reviewer', 'backstory')
                if backstory:
                    logger.info("✅ Reviewer: Backstory загружен из БД")
                    return backstory
            except Exception as e:
                logger.warning(f"⚠️ Reviewer: Ошибка загрузки backstory из БД: {e}")

        # Fallback на hardcoded
        logger.info("Reviewer: Используется hardcoded backstory")
        return """Ты эксперт-ревьюер грантовых заявок с 25-летним опытом работы в экспертных комиссиях.
        Ты оцениваешь готовность заявок к подаче на основе 4 критериев: доказательная база (40%),
        структура (30%), индикаторный матчинг (20%), экономика (10%). Твоя оценка точно предсказывает
        вероятность одобрения заявки."""

    async def _get_fpg_requirements_async(self) -> Dict[str, List[Dict]]:
        """Получить требования ФПГ из векторной БД через Expert Agent"""
        requirements = {
            'evidence_base': [],
            'structure': [],
            'matching': [],
            'economics': []
        }

        if not self.expert_agent:
            logger.warning("⚠️ Expert Agent недоступен - пропускаем получение требований")
            return requirements

        try:
            logger.info("📚 Reviewer: Запрашиваю требования ФПГ из векторной БД...")

            # Запросы по каждому критерию
            queries = {
                'evidence_base': "Какие требования к доказательной базе в грантовой заявке? Цитаты, статистика, источники",
                'structure': "Какие требования к структуре и полноте грантовой заявки? Разделы, объем текста",
                'matching': "Какие требования к целям и индикаторам в грантовой заявке? SMART-цели, KPI",
                'economics': "Какие требования к бюджету и экономическому обоснованию в грантовой заявке?"
            }

            for criterion, query in queries.items():
                try:
                    results = self.expert_agent.query_knowledge(
                        question=query,
                        fund="fpg",
                        top_k=3,
                        min_score=0.4
                    )
                    requirements[criterion] = results
                    logger.info(f"✅ Reviewer: {criterion} - найдено {len(results)} требований")
                except Exception as e:
                    logger.error(f"❌ Reviewer: Ошибка запроса {criterion}: {e}")

            total_requirements = sum(len(v) for v in requirements.values())
            logger.info(f"✅ Reviewer: Всего получено {total_requirements} требований из векторной БД")

            return requirements

        except Exception as e:
            logger.error(f"❌ Reviewer: Ошибка получения требований: {e}")
            return requirements

    async def review_grant_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Асинхронная финальная оценка готовности гранта"""
        try:
            start_time = time.time()
            logger.info("🔍 Reviewer: Начинаем финальную оценку гранта")

            # Получаем требования ФПГ из векторной БД через Expert Agent
            fpg_requirements = await self._get_fpg_requirements_async()

            # Извлекаем данные с защитой от None (Iteration_58)
            grant_content = input_data.get('grant_content', {})
            research_results = input_data.get('research_results', {})
            user_answers = input_data.get('user_answers', {})
            citations = input_data.get('citations', []) or []  # Защита от None
            tables = input_data.get('tables', []) or []  # Защита от None
            selected_grant = input_data.get('selected_grant', {})

            logger.info(f"📊 Reviewer: Получены данные - цитаты: {len(citations)}, таблицы: {len(tables)}")

            # Критерий 1: Доказательная база (40%)
            evidence_score = await self._evaluate_evidence_base_async(
                grant_content, research_results, citations, tables
            )

            # Критерий 2: Структура и полнота (30%)
            structure_score = await self._evaluate_structure_async(
                grant_content, user_answers
            )

            # Критерий 3: Индикаторный матчинг (20%)
            matching_score = await self._evaluate_matching_async(
                grant_content, research_results, selected_grant
            )

            # Критерий 4: Экономическое обоснование (10%)
            economics_score = await self._evaluate_economics_async(
                grant_content, user_answers
            )

            # Рассчитываем взвешенную оценку готовности (0-10)
            readiness_score = (
                evidence_score['score'] * self.WEIGHTS['evidence_base'] +
                structure_score['score'] * self.WEIGHTS['structure'] +
                matching_score['score'] * self.WEIGHTS['matching'] +
                economics_score['score'] * self.WEIGHTS['economics']
            )

            # Рассчитываем вероятность одобрения (0-100%)
            # Формула: base_probability + (readiness_score * multiplier)
            # Для readiness_score = 8: 15 + (8 * 4.375) = 15 + 35 = 50%
            base_probability = 15  # базовая вероятность для любой заявки
            multiplier = 4.375     # множитель для перевода в проценты (макс 50% при score=8)
            approval_probability = min(100, base_probability + (readiness_score * multiplier))

            # Собираем сильные стороны и слабости
            strengths = self._collect_strengths(
                evidence_score, structure_score, matching_score, economics_score
            )
            weaknesses = self._collect_weaknesses(
                evidence_score, structure_score, matching_score, economics_score
            )

            # Генерируем рекомендации
            recommendations = self._generate_recommendations(
                evidence_score, structure_score, matching_score, economics_score, readiness_score
            )

            processing_time = time.time() - start_time

            result = {
                'status': 'success',
                'agent_type': 'reviewer',
                'readiness_score': round(readiness_score, 2),
                'approval_probability': round(approval_probability, 1),

                # Field aliases for compatibility with handler/file_generators (Iteration_57)
                'review_score': round(readiness_score, 2),  # Alias for readiness_score
                'final_status': (  # Derived from readiness_score
                    'approved' if readiness_score >= 7.0
                    else 'needs_revision' if readiness_score >= 5.0
                    else 'rejected'
                ),

                'fpg_requirements': fpg_requirements,  # Требования из векторной БД
                'criteria_scores': {
                    'evidence_base': {
                        'score': round(evidence_score['score'], 2),
                        'weight': self.WEIGHTS['evidence_base'],
                        'weighted_score': round(evidence_score['score'] * self.WEIGHTS['evidence_base'], 2),
                        'details': evidence_score
                    },
                    'structure': {
                        'score': round(structure_score['score'], 2),
                        'weight': self.WEIGHTS['structure'],
                        'weighted_score': round(structure_score['score'] * self.WEIGHTS['structure'], 2),
                        'details': structure_score
                    },
                    'matching': {
                        'score': round(matching_score['score'], 2),
                        'weight': self.WEIGHTS['matching'],
                        'weighted_score': round(matching_score['score'] * self.WEIGHTS['matching'], 2),
                        'details': matching_score
                    },
                    'economics': {
                        'score': round(economics_score['score'], 2),
                        'weight': self.WEIGHTS['economics'],
                        'weighted_score': round(economics_score['score'] * self.WEIGHTS['economics'], 2),
                        'details': economics_score
                    }
                },
                'strengths': strengths,
                'weaknesses': weaknesses,
                'recommendations': recommendations,
                'can_submit': readiness_score >= 7.0,  # Порог готовности
                'quality_tier': self._determine_quality_tier(readiness_score),
                'processing_time': round(processing_time, 2),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"✅ Reviewer: Оценка завершена - readiness: {readiness_score:.2f}/10, approval: {approval_probability:.1f}%")

            return result

        except Exception as e:
            logger.error(f"❌ Reviewer: Ошибка оценки: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f"Ошибка финальной оценки: {str(e)}",
                'agent_type': 'reviewer'
            }

    async def _evaluate_evidence_base_async(self, grant_content: Dict, research_results: Dict,
                                           citations: List, tables: List) -> Dict[str, Any]:
        """Критерий 1: Доказательная база (40% веса)"""
        logger.info("📚 Reviewer: Оценка доказательной базы...")

        score = 0.0  # 0-10
        details = {
            'official_stats': False,
            'gov_programs': False,
            'national_projects': False,
            'success_cases': False,
            'citations_count': len(citations),
            'tables_count': len(tables),
            'sources_count': 0
        }

        try:
            # 1. Проверка наличия официальной статистики (Росстат, министерства)
            official_sources = ['rosstat', 'минстат', 'минздрав', 'минобр', 'минспорт', 'fedstat']
            has_official = any(
                any(source.lower() in c.get('source', '').lower() for source in official_sources)
                for c in citations if isinstance(c, dict)  # Iteration_58: Type safety
            )
            details['official_stats'] = has_official
            if has_official:
                score += 2.0

            # 2. Проверка ссылок на госпрограммы
            gov_program_keywords = ['нацпроект', 'госпрограмм', 'паспорт проекта', 'стратегия']
            has_gov_programs = False
            if research_results and isinstance(research_results, dict):  # Iteration_58: Type safety
                block1 = research_results.get('block1_problem', {})
                programs = block1.get('programs', [])
                has_gov_programs = len(programs) > 0
            details['gov_programs'] = has_gov_programs
            if has_gov_programs:
                score += 2.0

            # 3. Проверка наличия успешных кейсов (минимум 3)
            success_cases_count = 0
            if research_results and isinstance(research_results, dict):  # Iteration_58: Type safety
                block1 = research_results.get('block1_problem', {})
                success_cases_count = len(block1.get('success_cases', []))
            details['success_cases'] = success_cases_count >= 3
            if success_cases_count >= 3:
                score += 2.0
            elif success_cases_count >= 1:
                score += 1.0

            # 4. Количество цитат (минимум 10)
            if len(citations) >= 10:
                score += 2.0
            elif len(citations) >= 7:
                score += 1.5
            elif len(citations) >= 5:
                score += 1.0

            # 5. Количество таблиц (минимум 2)
            if len(tables) >= 2:
                score += 1.5
            elif len(tables) >= 1:
                score += 0.75

            # 6. Разнообразие источников (минимум 5)
            unique_sources = set([c.get('source', '') for c in citations if isinstance(c, dict) and c.get('source')])  # Iteration_58: Type safety
            details['sources_count'] = len(unique_sources)
            if len(unique_sources) >= 5:
                score += 0.5

            logger.info(f"✅ Reviewer Evidence: score={score:.2f}/10, цитаты={len(citations)}, таблицы={len(tables)}, источники={len(unique_sources)}")

            return {
                'score': min(10.0, score),
                'details': details,
                'comments': f"Доказательная база: {len(citations)} цитат, {len(tables)} таблиц, {len(unique_sources)} источников"
            }

        except Exception as e:
            logger.error(f"❌ Reviewer Evidence: Ошибка оценки: {e}")
            return {
                'score': 5.0,  # средняя оценка при ошибке
                'details': details,
                'comments': 'Оценка с ошибкой'
            }

    async def _evaluate_structure_async(self, grant_content: Dict, user_answers: Dict) -> Dict[str, Any]:
        """Критерий 2: Структура и полнота (30% веса)"""
        logger.info("📐 Reviewer: Оценка структуры и полноты...")

        score = 0.0
        details = {
            'required_sections': 0,
            'total_sections': 0,
            'min_length_met': False,
            'logical_flow': True,
            'formatting': True
        }

        try:
            # Обязательные разделы
            required_sections = ['problem', 'geography', 'goals', 'solution', 'budget', 'timeline']
            present_sections = [s for s in required_sections if grant_content.get(s)]
            details['required_sections'] = len(present_sections)
            details['total_sections'] = len(required_sections)

            # 1. Наличие всех обязательных разделов
            if len(present_sections) == len(required_sections):
                score += 3.0
            elif len(present_sections) >= 4:
                score += 2.0
            elif len(present_sections) >= 2:
                score += 1.0

            # 2. Минимальная длина текста (15,000 символов)
            full_text = grant_content.get('full_text', '')
            if not full_text:
                # Собираем из секций
                full_text = ' '.join([str(grant_content.get(s, '')) for s in required_sections])

            total_length = len(full_text)
            details['min_length_met'] = total_length >= 15000

            if total_length >= 15000:
                score += 3.0
            elif total_length >= 12000:
                score += 2.5
            elif total_length >= 10000:
                score += 2.0
            elif total_length >= 7000:
                score += 1.5
            elif total_length >= 5000:
                score += 1.0

            # 3. Наличие метаданных из Writer V2
            metadata = grant_content.get('metadata', {})
            if metadata and metadata.get('plan_followed'):
                score += 2.0
            else:
                score += 1.0

            # 4. Детальность разделов
            avg_section_length = total_length / len(present_sections) if present_sections else 0
            if avg_section_length >= 2000:
                score += 1.0
            elif avg_section_length >= 1000:
                score += 0.5

            # 5. Наличие ключевых элементов в каждом разделе
            if grant_content.get('problem') and len(str(grant_content.get('problem', ''))) > 500:
                score += 0.5
            if grant_content.get('goals') and len(str(grant_content.get('goals', ''))) > 500:
                score += 0.5

            logger.info(f"✅ Reviewer Structure: score={score:.2f}/10, секции={len(present_sections)}/{len(required_sections)}, длина={total_length}")

            return {
                'score': min(10.0, score),
                'details': details,
                'comments': f"Структура: {len(present_sections)}/{len(required_sections)} разделов, {total_length} символов"
            }

        except Exception as e:
            logger.error(f"❌ Reviewer Structure: Ошибка оценки: {e}")
            return {
                'score': 6.0,
                'details': details,
                'comments': 'Оценка с ошибкой'
            }

    async def _evaluate_matching_async(self, grant_content: Dict, research_results: Dict,
                                      selected_grant: Dict) -> Dict[str, Any]:
        """Критерий 3: Индикаторный матчинг (20% веса)"""
        logger.info("🎯 Reviewer: Оценка индикаторного матчинга...")

        score = 0.0
        details = {
            'smart_goals': False,
            'measurable_kpi': False,
            'regional_alignment': False,
            'national_projects_aligned': False
        }

        try:
            # 1. SMART-цели (из block3_goals)
            if research_results and isinstance(research_results, dict):  # Iteration_58: Type safety
                block3 = research_results.get('block3_goals', {})
                main_goals = block3.get('main_goal_variants', [])
                if main_goals and len(main_goals) > 0:
                    first_goal = main_goals[0]
                    if isinstance(first_goal, dict):  # Iteration_58: Type safety
                        smart_check = first_goal.get('smart_check', {})
                        if all(smart_check.values()):
                            details['smart_goals'] = True
                            score += 3.0
                        elif sum(smart_check.values()) >= 3:
                            details['smart_goals'] = True
                            score += 2.0

            # 2. Измеримые KPI
            if research_results and isinstance(research_results, dict):  # Iteration_58: Type safety
                block3 = research_results.get('block3_goals', {})
                key_tasks = block3.get('key_tasks', [])
                has_kpi = any(task.get('kpi') for task in key_tasks if isinstance(task, dict))  # Iteration_58: Type safety
                details['measurable_kpi'] = has_kpi
                if has_kpi:
                    score += 2.5

            # 3. Региональная привязка
            if research_results and isinstance(research_results, dict):  # Iteration_58: Type safety
                block2 = research_results.get('block2_geography', {})
                target_audience = block2.get('target_audience', {})
                infrastructure = block2.get('infrastructure', {})
                has_regional = bool(target_audience or infrastructure)
                details['regional_alignment'] = has_regional
                if has_regional:
                    score += 2.5

            # 4. Соответствие нацпроектам
            if research_results and isinstance(research_results, dict):  # Iteration_58: Type safety
                block1 = research_results.get('block1_problem', {})
                programs = block1.get('programs', [])
                has_natproject = any('нацпроект' in p.get('name', '').lower() for p in programs if isinstance(p, dict))  # Iteration_58: Type safety
                details['national_projects_aligned'] = has_natproject
                if has_natproject:
                    score += 2.0

            logger.info(f"✅ Reviewer Matching: score={score:.2f}/10, SMART={details['smart_goals']}, KPI={details['measurable_kpi']}")

            return {
                'score': min(10.0, score),
                'details': details,
                'comments': f"Индикаторный матчинг: SMART-цели={details['smart_goals']}, KPI={details['measurable_kpi']}"
            }

        except Exception as e:
            logger.error(f"❌ Reviewer Matching: Ошибка оценки: {e}")
            return {
                'score': 6.0,
                'details': details,
                'comments': 'Оценка с ошибкой'
            }

    async def _evaluate_economics_async(self, grant_content: Dict, user_answers: Dict) -> Dict[str, Any]:
        """Критерий 4: Экономическое обоснование (10% веса)"""
        logger.info("💰 Reviewer: Оценка экономики...")

        score = 0.0
        details = {
            'budget_present': False,
            'budget_detailed': False,
            'efficiency': 'unknown',
            'sustainability': False
        }

        try:
            # 1. Наличие бюджета
            budget_text = grant_content.get('budget', '') or user_answers.get('budget', '')
            details['budget_present'] = bool(budget_text)
            if budget_text:
                score += 2.5

            # 2. Детальность бюджета (наличие разбивки)
            budget_keywords = ['статья', 'расход', 'смета', 'калькуляция', 'обоснование']
            has_details = any(kw in str(budget_text).lower() for kw in budget_keywords)
            details['budget_detailed'] = has_details
            if has_details:
                score += 2.5

            # 3. Устойчивость после окончания гранта
            sustainability_text = grant_content.get('sustainability', '')
            details['sustainability'] = len(sustainability_text) > 100
            if len(sustainability_text) > 100:
                score += 2.5
            elif len(sustainability_text) > 50:
                score += 1.5

            # 4. Эффективность расходов (наличие аналогов/обоснования)
            efficiency_keywords = ['аналог', 'рыночная цена', 'обоснован', 'эффективн']
            has_efficiency = any(kw in str(budget_text).lower() for kw in efficiency_keywords)
            if has_efficiency:
                details['efficiency'] = 'justified'
                score += 2.5
            else:
                details['efficiency'] = 'not_justified'

            logger.info(f"✅ Reviewer Economics: score={score:.2f}/10, бюджет={details['budget_present']}, детальность={details['budget_detailed']}")

            return {
                'score': min(10.0, score),
                'details': details,
                'comments': f"Экономика: бюджет={'есть' if details['budget_present'] else 'нет'}, детальность={details['budget_detailed']}"
            }

        except Exception as e:
            logger.error(f"❌ Reviewer Economics: Ошибка оценки: {e}")
            return {
                'score': 6.0,
                'details': details,
                'comments': 'Оценка с ошибкой'
            }

    def _collect_strengths(self, evidence: Dict, structure: Dict, matching: Dict, economics: Dict) -> List[str]:
        """Собрать сильные стороны заявки"""
        strengths = []

        # Доказательная база
        if evidence['score'] >= 8:
            strengths.append("Сильная доказательная база с официальной статистикой")
        if evidence['details'].get('citations_count', 0) >= 10:
            strengths.append(f"Много цитат из надежных источников ({evidence['details']['citations_count']})")
        if evidence['details'].get('tables_count', 0) >= 2:
            strengths.append(f"Наглядные сравнительные таблицы ({evidence['details']['tables_count']})")

        # Структура
        if structure['score'] >= 8:
            strengths.append("Полная и логичная структура заявки")
        if structure['details'].get('min_length_met'):
            strengths.append("Достаточный объем текста (15,000+ символов)")

        # Матчинг
        if matching['details'].get('smart_goals'):
            strengths.append("Четкие SMART-цели")
        if matching['details'].get('national_projects_aligned'):
            strengths.append("Соответствие национальным проектам")

        # Экономика
        if economics['details'].get('budget_detailed'):
            strengths.append("Детальный и обоснованный бюджет")

        return strengths

    def _collect_weaknesses(self, evidence: Dict, structure: Dict, matching: Dict, economics: Dict) -> List[str]:
        """Собрать слабые стороны заявки"""
        weaknesses = []

        # Доказательная база
        if evidence['details'].get('citations_count', 0) < 10:
            weaknesses.append(f"Недостаточно цитат ({evidence['details']['citations_count']}, нужно 10+)")
        if evidence['details'].get('tables_count', 0) < 2:
            weaknesses.append(f"Недостаточно таблиц ({evidence['details']['tables_count']}, нужно 2+)")
        if not evidence['details'].get('official_stats'):
            weaknesses.append("Отсутствует официальная статистика (Росстат, министерства)")

        # Структура
        if not structure['details'].get('min_length_met'):
            weaknesses.append("Недостаточный объем текста (нужно 15,000+ символов)")
        if structure['details']['required_sections'] < structure['details']['total_sections']:
            missing = structure['details']['total_sections'] - structure['details']['required_sections']
            weaknesses.append(f"Отсутствуют {missing} обязательных раздела")

        # Матчинг
        if not matching['details'].get('smart_goals'):
            weaknesses.append("Цели не соответствуют SMART-критериям")
        if not matching['details'].get('measurable_kpi'):
            weaknesses.append("Отсутствуют измеримые KPI")

        # Экономика
        if not economics['details'].get('budget_present'):
            weaknesses.append("Отсутствует бюджет проекта")
        if not economics['details'].get('sustainability'):
            weaknesses.append("Не описана устойчивость после завершения гранта")

        return weaknesses

    def _generate_recommendations(self, evidence: Dict, structure: Dict, matching: Dict,
                                 economics: Dict, overall_score: float) -> List[str]:
        """Сгенерировать рекомендации по улучшению"""
        recommendations = []

        if overall_score >= 8.0:
            recommendations.append("✅ Заявка готова к подаче! Высокая вероятность одобрения.")
        elif overall_score >= 7.0:
            recommendations.append("⚠️ Заявка хорошего качества, но требует небольших доработок.")
        else:
            recommendations.append("❌ Заявка требует существенной доработки перед подачей.")

        # Рекомендации по критериям
        if evidence['score'] < 7:
            recommendations.append("Добавьте больше официальной статистики и успешных кейсов")
        if structure['score'] < 7:
            recommendations.append("Увеличьте детальность описания и объем текста")
        if matching['score'] < 7:
            recommendations.append("Уточните SMART-цели и добавьте измеримые KPI")
        if economics['score'] < 7:
            recommendations.append("Детализируйте бюджет и обоснуйте эффективность расходов")

        return recommendations

    def _determine_quality_tier(self, readiness_score: float) -> str:
        """Определить уровень качества заявки"""
        if readiness_score >= 8.5:
            return "Excellent"
        elif readiness_score >= 7.5:
            return "Good"
        elif readiness_score >= 6.5:
            return "Acceptable"
        elif readiness_score >= 5.0:
            return "Needs Improvement"
        else:
            return "Poor"

    def review_grant(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронная версия (wrapper для async)"""
        return asyncio.run(self.review_grant_async(input_data))

    async def review_and_save_grant_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Асинхронная финальная оценка гранта с сохранением результатов в БД и экспортом MD/PDF

        Review - это независимое экспертное мнение о готовом гранте.
        Review НЕ изменяет грант, а создает отдельную оценочную запись.

        Args:
            input_data: Словарь с данными для оценки:
                - anketa_id: ID анкеты (обязательно)
                - grant_id: ID гранта (обязательно)
                - grant_content: Содержимое гранта
                - research_results: Результаты research
                - user_answers: Ответы пользователя
                - citations: Список цитат
                - tables: Список таблиц
                - selected_grant: Выбранный грант
                - export_formats: Список форматов для экспорта ['md', 'pdf'] (optional, default: ['md', 'pdf'])
                - output_dir: Директория для сохранения файлов (optional, default: 'reports')

        Returns:
            Словарь с результатами review, review_id и путями к экспортированным файлам
        """
        try:
            # Проверяем обязательные параметры
            anketa_id = input_data.get('anketa_id')
            grant_id = input_data.get('grant_id')

            if not anketa_id or not grant_id:
                raise ValueError("anketa_id and grant_id are required")

            # Выполняем review
            review_results = await self.review_grant_async(input_data)

            if review_results.get('status') != 'success':
                logger.error(f"Review failed: {review_results.get('message')}")
                return review_results

            # Добавляем anketa_id и grant_id в результаты
            review_results['anketa_id'] = anketa_id
            review_results['grant_id'] = grant_id

            # Генерируем review_id для именования файлов
            review_id = self.db.generate_review_id(anketa_id)
            review_results['review_id'] = review_id

            # Экспорт MD и PDF
            export_formats = input_data.get('export_formats', ['md', 'pdf'])
            output_dir = input_data.get('output_dir', 'reports')

            try:
                # Импортируем ArtifactSaver
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from utils.artifact_saver import ArtifactSaver

                saver = ArtifactSaver(output_dir=output_dir)

                # Формируем имя файла: review_id без символа #
                filename = review_id.replace('#', '')

                # Сохраняем артефакты
                saved_files = await saver.save_artifact(
                    data=review_results,
                    filename=filename,
                    artifact_type='review',
                    formats=export_formats
                )

                # Добавляем пути к файлам в результаты
                if 'md' in saved_files:
                    review_results['review_md_path'] = str(saved_files['md'])
                    logger.info(f"📄 Review MD saved: {saved_files['md']}")

                if 'pdf' in saved_files:
                    review_results['review_pdf_path'] = str(saved_files['pdf'])
                    logger.info(f"📄 Review PDF saved: {saved_files['pdf']}")

            except Exception as export_error:
                logger.error(f"⚠️ Export failed: {export_error}")
                # Продолжаем даже если экспорт не удался

            # Сохраняем результаты в БД (с путями к файлам)
            saved_review_id = self.db.save_review_results(review_results)

            if saved_review_id:
                logger.info(f"✅ Review saved to database: {saved_review_id}")
            else:
                logger.warning("⚠️ Review completed but not saved to database")

            return review_results

        except Exception as e:
            logger.error(f"❌ Review and save failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f"Ошибка review и сохранения: {str(e)}",
                'agent_type': 'reviewer'
            }

    def review_and_save_grant(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронная версия review_and_save_grant_async"""
        return asyncio.run(self.review_and_save_grant_async(input_data))

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод обработки данных"""
        return self.review_grant(data)
