#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interviewer Agent - агент для создания вопросов для интервью
ОБНОВЛЕНО: Использует DatabasePromptManager для загрузки промптов из БД
"""
import sys
import os
from typing import Dict, Any, List, Optional
import logging
import asyncio
import time

# Добавляем пути к модулям
sys.path.append('/var/GrantService/shared')
sys.path.append('/var/GrantService/telegram-bot/services')
sys.path.append('/var/GrantService/web-admin')

from base_agent import BaseAgent

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    try:
        from services.llm_router import LLMRouter, LLMProvider
        UNIFIED_CLIENT_AVAILABLE = False
    except ImportError:
        print("⚠️ LLM сервисы недоступны")
        UNIFIED_CLIENT_AVAILABLE = False

# Импортируем DatabasePromptManager для загрузки промптов из БД
try:
    from utils.prompt_manager import DatabasePromptManager, get_database_prompt_manager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    print("⚠️ DatabasePromptManager недоступен, используются hardcoded промпты")
    PROMPT_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)

class InterviewerAgent(BaseAgent):
    """
    Агент-интервьюер для создания вопросов

    ВАЖНО: Используется только в ИНТЕРАКТИВНОМ режиме.
    Для обычного режима используются 15 фиксированных вопросов из таблицы interview_questions.
    """

    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("interviewer", db, llm_provider)

        if UNIFIED_CLIENT_AVAILABLE:
            # Передаем provider в конструктор UnifiedLLMClient
            self.llm_client = UnifiedLLMClient(provider=llm_provider)
            self.config = AGENT_CONFIGS.get("interviewer", AGENT_CONFIGS["interviewer"])
        else:
            self.llm_router = LLMRouter()

        # Инициализируем DatabasePromptManager для интерактивного режима
        self.prompt_manager: Optional[DatabasePromptManager] = None
        if PROMPT_MANAGER_AVAILABLE:
            try:
                self.prompt_manager = get_database_prompt_manager()
                logger.info("✅ Interviewer Agent: DatabasePromptManager подключен")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось инициализировать PromptManager: {e}")

    def _get_goal(self) -> str:
        """
        Получить goal агента
        Сначала пытаемся загрузить из БД, затем fallback на hardcoded
        """
        if self.prompt_manager:
            try:
                goal = self.prompt_manager.get_prompt('interviewer', 'goal')
                if goal:
                    return goal
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки goal из БД: {e}")

        # Fallback на hardcoded
        return "Создать персонализированные вопросы для интервью на основе профиля пользователя и требований гранта"

    def _get_backstory(self) -> str:
        """
        Получить backstory агента
        Сначала пытаемся загрузить из БД, затем fallback на hardcoded
        """
        if self.prompt_manager:
            try:
                backstory = self.prompt_manager.get_prompt('interviewer', 'backstory')
                if backstory:
                    return backstory
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки backstory из БД: {e}")

        # Fallback на hardcoded
        return """Ты опытный интервьюер и консультант по грантам с психологическим образованием.
        Ты умеешь задавать правильные вопросы, которые помогают раскрыть сильные стороны проекта
        и получить всю необходимую информацию для успешной заявки."""
    
    async def create_questions_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Асинхронное создание вопросов для интервью"""
        try:
            start_time = time.time()
            self.log_activity("question_creation_started", {"input_keys": list(input_data.keys())})
            
            # Извлекаем данные
            user_profile = input_data.get('user_profile', '')
            project_description = input_data.get('project_description', '')
            grant_requirements = input_data.get('grant_requirements', '')
            question_count = input_data.get('question_count', 15)
            
            # Создаем разные типы вопросов
            questions = await self._generate_comprehensive_questions(
                user_profile, project_description, grant_requirements, question_count
            )
            
            # Структурируем вопросы по категориям
            structured_questions = self._structure_questions(questions)
            
            # Создаем последовательность интервью
            interview_flow = self._create_interview_flow(structured_questions)
            
            processing_time = time.time() - start_time
            
            result = {
                'status': 'success',
                'provider': 'gigachat' if UNIFIED_CLIENT_AVAILABLE else 'router',
                'processing_time': processing_time,
                'questions': structured_questions,
                'interview_flow': interview_flow,
                'total_questions': len(questions),
                'estimated_duration': len(questions) * 2,  # 2 минуты на вопрос
                'result': self._format_questions_for_display(structured_questions),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.log_activity("questions_created", {
                "total_questions": len(questions),
                "processing_time": processing_time
            })
            
            return self.prepare_output(result)
            
        except Exception as e:
            logger.error(f"Ошибка создания вопросов: {e}")
            return self.handle_error(e, "create_questions_async")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронная обертка для совместимости"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.create_questions_async(input_data))
        except RuntimeError:
            return asyncio.run(self.create_questions_async(input_data))
    
    def create_questions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Совместимость с существующим интерфейсом"""
        return self.process(input_data)
    
    async def _generate_comprehensive_questions(self, user_profile: str, project_description: str, 
                                             grant_requirements: str, question_count: int) -> List[Dict]:
        """Создание комплексного набора вопросов"""
        questions = []
        
        if UNIFIED_CLIENT_AVAILABLE:
            # Используем LLM для создания персонализированных вопросов
            questions.extend(await self._generate_llm_questions(
                user_profile, project_description, grant_requirements, question_count
            ))
        else:
            # Fallback на предустановленные вопросы
            questions.extend(self._get_fallback_questions(user_profile, project_description))
        
        return questions[:question_count]
    
    async def _generate_llm_questions(self, user_profile: str, project_description: str, 
                                    grant_requirements: str, question_count: int) -> List[Dict]:
        """Генерация вопросов с помощью LLM"""
        try:
            # Создаем вопросы по категориям
            question_categories = [
                ("project_basics", "о проекте и его целях", 4),
                ("team_experience", "о команде и опыте", 3),
                ("implementation", "о реализации и планах", 4),
                ("budget_finances", "о бюджете и финансах", 2),
                ("impact_results", "о результатах и влиянии", 2)
            ]
            
            all_questions = []
            
            for category, description, count in question_categories:
                # Пытаемся получить промпт из БД
                prompt = None
                if self.prompt_manager:
                    try:
                        prompt = self.prompt_manager.get_prompt(
                            'interviewer',
                            'llm_question_generation',
                            variables={
                                'user_profile': user_profile,
                                'project_description': project_description,
                                'grant_requirements': grant_requirements,
                                'category_description': description,
                                'question_count': count
                            }
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка загрузки LLM промпта из БД: {e}")

                if not prompt:
                    # Fallback промпт (hardcoded)
                    prompt = f"""Создай {count} вопросов {description} для интервью с заявителем гранта.

ПРОФИЛЬ ЗАЯВИТЕЛЯ:
{user_profile}

ОПИСАНИЕ ПРОЕКТА:
{project_description}

ТРЕБОВАНИЯ ГРАНТА:
{grant_requirements}

Создай открытые вопросы, которые помогут раскрыть важные детали проекта.
Формат ответа:
1. Вопрос 1
2. Вопрос 2
..."""
                
                try:
                    async with self.llm_client:
                        response = await self.llm_client.generate_async(
                            prompt,
                            provider=self.llm_provider,
                            **{k: v for k, v in self.config.items() if k != 'provider'}
                        )

                    category_questions = self._parse_questions_from_response(response, category)
                    all_questions.extend(category_questions)

                except Exception as e:
                    logger.error(f"Ошибка создания вопросов для категории {category}: {e}")
                    # Добавляем fallback вопросы для этой категории
                    all_questions.extend(self._get_fallback_questions_by_category(category, count))
            
            return all_questions
            
        except Exception as e:
            logger.error(f"Ошибка LLM генерации вопросов: {e}")
            return self._get_fallback_questions(user_profile, project_description)
    
    def _parse_questions_from_response(self, response: str, category: str) -> List[Dict]:
        """Парсинг вопросов из ответа LLM"""
        questions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Ищем строки, которые выглядят как вопросы
            if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•']):
                # Убираем нумерацию и символы списка
                clean_question = line.lstrip('0123456789.-• ').strip()
                if len(clean_question) > 10 and clean_question.endswith('?'):
                    questions.append({
                        'text': clean_question,
                        'category': category,
                        'type': 'open',
                        'required': True,
                        'source': 'llm'
                    })
            elif line.endswith('?') and len(line) > 15:
                questions.append({
                    'text': line,
                    'category': category,
                    'type': 'open',
                    'required': True,
                    'source': 'llm'
                })
        
        return questions
    
    def _get_fallback_questions(self, user_profile: str, project_description: str) -> List[Dict]:
        """
        Предустановленные вопросы для fallback
        Загружаются из БД (10 вопросов) или используются hardcoded если БД недоступна
        """
        base_questions = []

        # Пытаемся загрузить fallback вопросы из БД
        if self.prompt_manager:
            try:
                db_questions = self.prompt_manager.get_all_prompts('interviewer', 'fallback_question')
                if db_questions:
                    logger.info(f"✅ Загружено {len(db_questions)} fallback вопросов из БД")
                    for q in db_questions:
                        # Парсим variables из JSONB
                        variables = q.get('variables', {})
                        base_questions.append({
                            'text': q['prompt_template'],
                            'category': variables.get('category', 'general'),
                            'type': variables.get('type', 'open'),
                            'required': variables.get('required', True),
                            'source': 'database'
                        })
                    return base_questions
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки fallback вопросов из БД: {e}")

        # Fallback на hardcoded вопросы
        logger.info("Используются hardcoded fallback вопросы")
        base_questions = [
            {
                'text': 'Расскажите подробнее о вашем проекте и его основной идее?',
                'category': 'project_basics',
                'type': 'open',
                'required': True,
                'source': 'fallback'
            },
            {
                'text': 'Какую проблему решает ваш проект и почему это важно?',
                'category': 'project_basics',
                'type': 'open',
                'required': True,
                'source': 'fallback'
            },
            {
                'text': 'Кто входит в вашу команду и какой у участников опыт?',
                'category': 'team_experience',
                'type': 'open',
                'required': True,
                'source': 'fallback'
            },
            {
                'text': 'Как вы планируете реализовать проект пошагово?',
                'category': 'implementation',
                'type': 'open',
                'required': True,
                'source': 'fallback'
            },
            {
                'text': 'На что конкретно будут потрачены запрашиваемые средства?',
                'category': 'budget_finances',
                'type': 'open',
                'required': True,
                'source': 'fallback'
            },
            {
                'text': 'Какие результаты вы ожидаете получить от проекта?',
                'category': 'impact_results',
                'type': 'open',
                'required': True,
                'source': 'fallback'
            },
            {
                'text': 'Как вы будете измерять успех проекта?',
                'category': 'impact_results',
                'type': 'open',
                'required': True,
                'source': 'fallback'
            },
            {
                'text': 'Какие риски видите в реализации проекта и как их минимизировать?',
                'category': 'implementation',
                'type': 'open',
                'required': False,
                'source': 'fallback'
            },
            {
                'text': 'Есть ли у вас опыт управления подобными проектами?',
                'category': 'team_experience',
                'type': 'open',
                'required': False,
                'source': 'fallback'
            },
            {
                'text': 'Как ваш проект будет продолжаться после окончания гранта?',
                'category': 'implementation',
                'type': 'open',
                'required': False,
                'source': 'fallback'
            }
        ]
        
        # Персонализируем вопросы на основе профиля
        if 'технол' in user_profile.lower() or 'IT' in user_profile:
            base_questions.append({
                'text': 'Какие технологии вы планируете использовать и почему именно их?',
                'category': 'implementation',
                'type': 'open',
                'required': False,
                'source': 'fallback'
            })
        
        if 'социальн' in user_profile.lower() or 'общество' in user_profile.lower():
            base_questions.append({
                'text': 'Как ваш проект повлияет на целевую аудиторию и общество?',
                'category': 'impact_results',
                'type': 'open',
                'required': False,
                'source': 'fallback'
            })
        
        return base_questions
    
    def _get_fallback_questions_by_category(self, category: str, count: int) -> List[Dict]:
        """Получение fallback вопросов по категории"""
        fallback_by_category = {
            'project_basics': [
                'Опишите суть вашего проекта?',
                'В чем уникальность вашего подхода?',
                'Какие цели вы преследуете?',
                'Кто ваша целевая аудитория?'
            ],
            'team_experience': [
                'Расскажите о составе команды?',
                'Какой опыт у ключевых участников?',
                'Кто будет отвечать за реализацию?'
            ],
            'implementation': [
                'Как вы планируете реализовать проект?',
                'Какие этапы выделяете?',
                'Сколько времени потребуется?',
                'Какие ресурсы нужны?'
            ],
            'budget_finances': [
                'Обоснуйте запрашиваемую сумму?',
                'На что пойдет основная часть бюджета?'
            ],
            'impact_results': [
                'Какие результаты ожидаете?',
                'Как будете измерять эффективность?'
            ]
        }
        
        category_questions = fallback_by_category.get(category, ['Расскажите подробнее?'])
        
        return [{
            'text': q if q.endswith('?') else q + '?',
            'category': category,
            'type': 'open',
            'required': True,
            'source': 'fallback'
        } for q in category_questions[:count]]
    
    def _structure_questions(self, questions: List[Dict]) -> Dict[str, List[Dict]]:
        """Структурирование вопросов по категориям"""
        structured = {}
        
        for question in questions:
            category = question.get('category', 'general')
            if category not in structured:
                structured[category] = []
            structured[category].append(question)
        
        return structured
    
    def _create_interview_flow(self, structured_questions: Dict[str, List[Dict]]) -> List[Dict]:
        """Создание последовательности интервью"""
        flow = []
        
        # Определяем порядок категорий
        category_order = [
            ('project_basics', 'Основные вопросы о проекте'),
            ('team_experience', 'Команда и опыт'),
            ('implementation', 'Реализация и планы'),
            ('budget_finances', 'Бюджет и финансы'),
            ('impact_results', 'Результаты и влияние')
        ]
        
        for category, title in category_order:
            if category in structured_questions:
                flow.append({
                    'stage': category,
                    'title': title,
                    'questions': structured_questions[category],
                    'estimated_time': len(structured_questions[category]) * 2
                })
        
        return flow
    
    def _format_questions_for_display(self, structured_questions: Dict[str, List[Dict]]) -> str:
        """Форматирование вопросов для отображения"""
        output = []
        
        category_titles = {
            'project_basics': '🎯 ОСНОВНЫЕ ВОПРОСЫ О ПРОЕКТЕ',
            'team_experience': '👥 КОМАНДА И ОПЫТ', 
            'implementation': '⚙️ РЕАЛИЗАЦИЯ И ПЛАНЫ',
            'budget_finances': '💰 БЮДЖЕТ И ФИНАНСЫ',
            'impact_results': '📈 РЕЗУЛЬТАТЫ И ВЛИЯНИЕ'
        }
        
        for category, questions in structured_questions.items():
            title = category_titles.get(category, category.upper())
            output.append(f"\n{title}")
            output.append("=" * len(title))
            
            for i, question in enumerate(questions, 1):
                required_mark = "⭐" if question.get('required', True) else "💡"
                output.append(f"{i}. {required_mark} {question['text']}")
        
        total_questions = sum(len(questions) for questions in structured_questions.values())
        estimated_time = total_questions * 2
        
        output.insert(0, f"📋 ВОПРОСЫ ДЛЯ ИНТЕРВЬЮ ({total_questions} вопросов, ~{estimated_time} мин)")
        output.insert(1, "=" * 60)
        
        return "\n".join(output)
    
    async def analyze_answers_async(self, questions: List[Dict], answers: Dict[str, str]) -> Dict[str, Any]:
        """Анализ ответов интервью"""
        try:
            if not UNIFIED_CLIENT_AVAILABLE:
                return self._basic_answer_analysis(answers)
            
            analysis_prompt = f"""Проанализируй ответы интервью заявителя гранта:

ВОПРОСЫ И ОТВЕТЫ:
{self._format_qa_for_analysis(questions, answers)}

Дай анализ по критериям:
1. Полнота ответов (1-10)
2. Качество проработки проекта (1-10)
3. Готовность команды (1-10)
4. Реалистичность планов (1-10)
5. Дополнительные вопросы, которые стоит задать

Укажи сильные и слабые стороны."""

            async with self.llm_client:
                analysis = await self.llm_client.generate_async(
                    analysis_prompt,
                    provider=self.llm_provider,
                    max_tokens=1500,
                    temperature=0.3
                )

            return {
                'status': 'success',
                'analysis': analysis,
                'completeness_score': self._extract_score_from_text(analysis, 'полнота'),
                'quality_score': self._extract_score_from_text(analysis, 'качество'),
                'readiness_score': self._extract_score_from_text(analysis, 'готовность'),
                'realism_score': self._extract_score_from_text(analysis, 'реалистичность'),
                'additional_questions': self._extract_additional_questions(analysis)
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа ответов: {e}")
            return self._basic_answer_analysis(answers)
    
    def _format_qa_for_analysis(self, questions: List[Dict], answers: Dict[str, str]) -> str:
        """Форматирование вопросов и ответов для анализа"""
        formatted = []
        
        for i, question in enumerate(questions):
            q_id = f"q_{i+1}"
            answer = answers.get(q_id, "Ответ не предоставлен")
            formatted.append(f"Вопрос {i+1}: {question['text']}")
            formatted.append(f"Ответ: {answer}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _extract_score_from_text(self, text: str, criterion: str) -> float:
        """Извлечение оценки из текста"""
        try:
            import re
            # Ищем оценки рядом с критерием
            pattern = rf'{criterion}[:\s]*(\d+(?:\.\d+)?)'
            match = re.search(pattern, text.lower())
            if match:
                score = float(match.group(1))
                return min(score / 10.0, 1.0) if score > 1 else score
            return 0.7  # Базовая оценка
        except:
            return 0.7
    
    def _extract_additional_questions(self, analysis: str) -> List[str]:
        """Извлечение дополнительных вопросов из анализа"""
        questions = []
        lines = analysis.split('\n')
        in_questions = False
        
        for line in lines:
            line = line.strip()
            if 'дополнительн' in line.lower() and 'вопрос' in line.lower():
                in_questions = True
                continue
            
            if in_questions and line:
                if line.startswith(('-', '•', '*')) or line.endswith('?'):
                    clean_q = line.lstrip('-•*0123456789. ').strip()
                    if len(clean_q) > 10:
                        questions.append(clean_q)
        
        return questions[:5]
    
    def _basic_answer_analysis(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Базовый анализ ответов без LLM"""
        total_answers = len(answers)
        non_empty_answers = len([a for a in answers.values() if a.strip()])
        avg_length = sum(len(a) for a in answers.values()) / max(total_answers, 1)
        
        completeness = non_empty_answers / max(total_answers, 1)
        quality = min(avg_length / 100, 1.0)  # Качество на основе длины ответов
        
        return {
            'status': 'success',
            'analysis': f"Базовый анализ: получено {non_empty_answers} из {total_answers} ответов. Средняя длина ответа: {avg_length:.0f} символов.",
            'completeness_score': completeness,
            'quality_score': quality,
            'readiness_score': (completeness + quality) / 2,
            'realism_score': 0.7,
            'additional_questions': []
        }


