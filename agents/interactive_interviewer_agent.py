#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Interviewer Agent - интервьюер с встроенным интерактивным аудитом

АРХИТЕКТУРА:
- Интервью разбито на 3 блока по 5 вопросов
- После каждого блока: промежуточный аудит
- Аудит анализирует ответы и задаёт уточняющие вопросы
- Финальный аудит после всех 15 вопросов
- Сохранение анкеты + audit_score в БД

Flow:
1. Блок 1 (вопросы 1-5) → Interim Audit → Clarifying Questions
2. Блок 2 (вопросы 6-10) → Interim Audit → Clarifying Questions
3. Блок 3 (вопросы 11-15) → Interim Audit → Clarifying Questions
4. Final Audit → Recommendations → Save to DB

Author: Grant Service Architect Agent
Created: 2025-10-12
Version: 1.0
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

from typing import Dict, Any, List, Optional, Tuple

import logging
import asyncio
import time
from datetime import datetime

# Add paths

from base_agent import BaseAgent
from auditor_agent import AuditorAgent

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    UNIFIED_CLIENT_AVAILABLE = False
    print("[WARN] UnifiedLLMClient недоступен")

logger = logging.getLogger(__name__)


def extract_json_from_response(text: str) -> dict:
    """
    Умный парсинг JSON из ответа LLM

    Поддерживает:
    - Чистый JSON
    - JSON в markdown блоке ```json...```
    - JSON с текстом до/после
    """
    import json
    import re

    # 1. Попытка парсить как есть
    try:
        return json.loads(text.strip())
    except:
        pass

    # 2. Извлечь из markdown блока ```json
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # 3. Извлечь из markdown блока ``` (без json)
    match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # 4. Найти любой JSON объект в тексте (с вложенностью)
    # Ищем от первой { до последней }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1:
        json_text = text[first_brace:last_brace+1]
        try:
            return json.loads(json_text)
        except:
            pass

    # 5. Fallback - возвращаем пустой dict
    logger.error(f"❌ Не удалось извлечь JSON из ответа: {text[:200]}...")
    return {}


# Базовые вопросы (15 штук, разбиты на 3 блока)
INTERVIEW_QUESTIONS = {
    "block_1": [
        "Как называется ваш проект? (100-150 символов)",
        "Какова основная цель вашего проекта?",
        "Какую проблему решает ваш проект? Опишите проблему конкретно.",
        "Кто является целевой аудиторией проекта?",
        "В каком регионе/городе будет реализован проект?"
    ],
    "block_2": [
        "Какие конкретные задачи вы планируете решить в рамках проекта?",
        "Опишите методологию реализации проекта (как будете делать?)",
        "Какие результаты вы планируете получить? (конкретные, измеримые)",
        "Каков планируемый бюджет проекта? (в рублях)",
        "Расшифруйте основные статьи бюджета (на что пойдут деньги?)"
    ],
    "block_3": [
        "Опишите вашу команду: кто будет реализовывать проект?",
        "Есть ли у вас партнёры для реализации проекта? Кто?",
        "Какие риски видите в реализации проекта и как будете их минимизировать?",
        "Как проект будет работать после окончания гранта? (устойчивость)",
        "На какой срок рассчитан проект? (в месяцах)"
    ]
}


class InteractiveInterviewerAgent(BaseAgent):
    """
    Интерактивный интервьюер с встроенным аудитом

    Отличия от обычного InterviewerAgent:
    - Интерактивные уточняющие вопросы на основе анализа ответов
    - Промежуточные аудиты после каждого блока
    - Финальный комплексный аудит
    - Рекомендации по улучшению в процессе интервью
    """

    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("interactive_interviewer", db, llm_provider)

        if UNIFIED_CLIENT_AVAILABLE:
            self.llm_client = UnifiedLLMClient(provider=llm_provider)
            self.config = AGENT_CONFIGS.get("interviewer", {})

        # Встроенный аудитор (тот же provider что и интервьюер)
        self.auditor = AuditorAgent(db, llm_provider=llm_provider)

        # Инициализируем DatabasePromptManager для загрузки промптов из БД
        self.prompt_manager = None
        try:
            from utils.prompt_manager import get_database_prompt_manager
            self.prompt_manager = get_database_prompt_manager()
            logger.info("✅ InteractiveInterviewer: DatabasePromptManager подключен")
        except Exception as e:
            logger.warning(f"⚠️ DatabasePromptManager недоступен: {e}")

        logger.info(f"✅ InteractiveInterviewerAgent initialized (provider={llm_provider})")

    async def conduct_interview_with_audit(
        self,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Основной метод: проведение интервью с интерактивным аудитом

        Args:
            user_data: Базовые данные пользователя
                - telegram_id
                - username
                - first_name, last_name
                - email, phone
                - grant_fund (Фонд президентских грантов)

        Returns:
            {
                'anketa': {...},  # 24 поля
                'audit_score': 75,  # 1-100
                'audit_details': {...},  # по 10 критериям
                'recommendations': [...],  # улучшения
                'interactive_feedback': [...]  # уточняющие вопросы и ответы
            }
        """
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("НАЧАЛО ИНТЕРАКТИВНОГО ИНТЕРВЬЮ С АУДИТОМ")
        logger.info("=" * 80)

        # Инициализация
        anketa = self._init_anketa(user_data)
        interactive_feedback = []

        # БЛОК 1: Базовая информация
        logger.info("\n[БЛОК 1/3] Базовая информация о проекте")
        block1_answers = await self._ask_question_block(
            block_num=1,
            questions=INTERVIEW_QUESTIONS["block_1"],
            user_data=user_data
        )
        anketa.update(self._map_block1_answers(block1_answers))

        # Interim Audit #1
        audit1_result = await self._interim_audit(anketa, block_num=1)
        clarifying1 = await self._ask_clarifying_questions(audit1_result, block_num=1)
        interactive_feedback.append({
            'block': 1,
            'audit_score': audit1_result.get('partial_score', 0),
            'clarifications': clarifying1
        })
        anketa.update(clarifying1)

        # БЛОК 2: Методология и бюджет
        logger.info("\n[БЛОК 2/3] Методология и бюджет")
        block2_answers = await self._ask_question_block(
            block_num=2,
            questions=INTERVIEW_QUESTIONS["block_2"],
            user_data=user_data
        )
        anketa.update(self._map_block2_answers(block2_answers))

        # Interim Audit #2
        audit2_result = await self._interim_audit(anketa, block_num=2)
        clarifying2 = await self._ask_clarifying_questions(audit2_result, block_num=2)
        interactive_feedback.append({
            'block': 2,
            'audit_score': audit2_result.get('partial_score', 0),
            'clarifications': clarifying2
        })
        anketa.update(clarifying2)

        # БЛОК 3: Команда, партнёры, риски
        logger.info("\n[БЛОК 3/3] Команда, партнёры, устойчивость")
        block3_answers = await self._ask_question_block(
            block_num=3,
            questions=INTERVIEW_QUESTIONS["block_3"],
            user_data=user_data
        )
        anketa.update(self._map_block3_answers(block3_answers))

        # Interim Audit #3
        audit3_result = await self._interim_audit(anketa, block_num=3)
        clarifying3 = await self._ask_clarifying_questions(audit3_result, block_num=3)
        interactive_feedback.append({
            'block': 3,
            'audit_score': audit3_result.get('partial_score', 0),
            'clarifications': clarifying3
        })
        anketa.update(clarifying3)

        # ФИНАЛЬНЫЙ АУДИТ
        logger.info("\n[ФИНАЛЬНЫЙ АУДИТ] Комплексная оценка заявки")
        final_audit = await self._final_audit(anketa)

        # Сохранение в БД
        anketa_id = await self._save_anketa_to_db(anketa, final_audit)

        processing_time = time.time() - start_time

        # Convert overall_score (0-1) to audit_score (0-100)
        audit_score = int(final_audit.get('overall_score', 0) * 100)

        result = {
            'status': 'success',
            'anketa': anketa,
            'anketa_id': anketa_id,
            'audit_score': audit_score,
            'audit_details': final_audit.get('analysis', {}),
            'recommendations': final_audit.get('recommendations', []),
            'interactive_feedback': interactive_feedback,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        }

        logger.info("=" * 80)
        logger.info(f"✅ ИНТЕРВЬЮ ЗАВЕРШЕНО (audit score: {audit_score}/100)")
        logger.info("=" * 80)

        return result

    def _init_anketa(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Инициализация анкеты с базовыми данными"""
        return {
            'telegram_id': user_data.get('telegram_id'),
            'username': user_data.get('username'),
            'email': user_data.get('email', ''),
            'phone': user_data.get('phone', ''),
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'grant_fund': user_data.get('grant_fund', 'Фонд президентских грантов'),
            'created_at': datetime.now().isoformat()
        }

    async def _ask_question_block(
        self,
        block_num: int,
        questions: List[str],
        user_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Задать блок вопросов

        NOTE: В реальной реализации это будет интерактивный диалог через Telegram.
        Для тестирования используем данные из user_data.
        """
        logger.info(f"  Задаём {len(questions)} вопросов блока {block_num}...")

        answers = {}

        # Имитация ответов (в реальности - через Telegram)
        # В тесте user_data будет содержать готовые ответы
        for i, question in enumerate(questions, 1):
            question_key = f"block_{block_num}_q{i}"
            answer = user_data.get(question_key, f"[Ответ на вопрос {block_num}.{i}]")
            answers[question_key] = answer
            logger.info(f"    Q{i}: {question[:50]}...")
            logger.info(f"    A{i}: {answer[:100]}...")

        return answers

    def _map_block1_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Маппинг ответов блока 1 на поля анкеты"""
        return {
            'project_name': answers.get('block_1_q1', ''),
            'project_goal': answers.get('block_1_q2', ''),
            'problem_statement': answers.get('block_1_q3', ''),
            'target_audience': answers.get('block_1_q4', ''),
            'geography': answers.get('block_1_q5', '')
        }

    def _map_block2_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Маппинг ответов блока 2 на поля анкеты"""
        return {
            'project_tasks': answers.get('block_2_q1', ''),
            'methodology': answers.get('block_2_q2', ''),
            'expected_results': answers.get('block_2_q3', ''),
            'budget': answers.get('block_2_q4', ''),
            'budget_breakdown': answers.get('block_2_q5', '')
        }

    def _map_block3_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Маппинг ответов блока 3 на поля анкеты"""
        return {
            'team_experience': answers.get('block_3_q1', ''),
            'partnerships': answers.get('block_3_q2', ''),
            'risk_management': answers.get('block_3_q3', ''),
            'sustainability': answers.get('block_3_q4', ''),
            'project_duration': answers.get('block_3_q5', '')
        }

    async def _interim_audit(
        self,
        partial_anketa: Dict[str, Any],
        block_num: int
    ) -> Dict[str, Any]:
        """
        Промежуточный аудит после блока вопросов

        Анализирует текущие ответы и выявляет слабые места
        """
        logger.info(f"  [Interim Audit #{block_num}] Анализ ответов...")

        # Пытаемся загрузить промпт из БД
        audit_prompt = None
        if self.prompt_manager:
            try:
                audit_prompt = self.prompt_manager.get_prompt(
                    'interactive_interviewer',
                    'block_audit',
                    variables={
                        'block_num': block_num,
                        'block_answers': self._format_partial_anketa(partial_anketa)
                    }
                )
                logger.info(f"    Загружен промпт block_audit из БД")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки промпта: {e}")

        # Fallback: hardcoded промпт
        if not audit_prompt:
            audit_prompt = f"""
Проведи быстрый аудит ответов на вопросы блока {block_num}.

Данные проекта:
{self._format_partial_anketa(partial_anketa)}

Оцени качество ответов по шкале 1-10 и укажи, что нужно уточнить.

Верни JSON:
{{
    "partial_score": 7,
    "weak_points": ["бюджет не расшифрован", "риски описаны поверхностно"],
    "clarification_needed": [
        {{"topic": "бюджет", "question": "Расшифруйте статьи бюджета конкретно"}},
        {{"topic": "риски", "question": "Опишите 2-3 конкретных риска с мерами"}}
    ]
}}
"""

        try:
            if UNIFIED_CLIENT_AVAILABLE:
                response = await self.llm_client.generate_async(
                    prompt=audit_prompt,
                    temperature=0.3,
                    max_tokens=500
                )

                # Умный парсинг JSON из ответа (поддерживает markdown обертки)
                logger.info(f"    LLM response preview: {response[:200]}...")
                audit_result = extract_json_from_response(response)

                if not audit_result:
                    # Если парсинг не удался - fallback
                    logger.warning("    ⚠️ Парсинг JSON не удался, использую fallback оценку")
                    audit_result = {
                        'partial_score': 5,
                        'weak_points': [],
                        'clarification_needed': []
                    }
                else:
                    # Нормализуем формат (поддержка старого и нового промптов)
                    score = audit_result.get('block_score', audit_result.get('partial_score', 0))
                    clarifications = audit_result.get('need_clarifications', audit_result.get('clarification_needed', []))

                    audit_result = {
                        'partial_score': score,
                        'block_score': score,
                        'weak_points': audit_result.get('weak_points', []),
                        'clarification_needed': clarifications,
                        'need_clarifications': clarifications
                    }
            else:
                # Fallback: базовая оценка
                audit_result = {
                    'partial_score': 7,
                    'weak_points': [],
                    'clarification_needed': []
                }

            logger.info(f"    Block score: {audit_result.get('partial_score', 0)}/10")
            logger.info(f"    Weak points: {len(audit_result.get('weak_points', []))}")
            logger.info(f"    Clarifications needed: {len(audit_result.get('clarification_needed', []))}")

            return audit_result

        except Exception as e:
            logger.error(f"❌ Ошибка interim audit: {e}")
            return {
                'partial_score': 5,
                'weak_points': [],
                'clarification_needed': []
            }

    async def _ask_clarifying_questions(
        self,
        audit_result: Dict[str, Any],
        block_num: int
    ) -> Dict[str, str]:
        """
        Задать уточняющие вопросы на основе аудита

        NOTE: В реальности - интерактивный диалог через Telegram
        """
        clarifications = audit_result.get('clarification_needed', [])

        if not clarifications:
            logger.info("  [Clarifying] Уточнений не требуется")
            return {}

        logger.info(f"  [Clarifying] Задаём {len(clarifications)} уточняющих вопросов...")

        clarified_answers = {}

        for i, clarification in enumerate(clarifications, 1):
            topic = clarification['topic']
            question = clarification['question']

            logger.info(f"    Clarify #{i}: {question}")

            # В реальности - ждём ответа от пользователя через Telegram
            # Для теста - placeholder
            answer = f"[Уточнение по теме '{topic}']"
            clarified_answers[f'clarification_{block_num}_{topic}'] = answer

        return clarified_answers

    def _format_partial_anketa(self, anketa: Dict[str, Any]) -> str:
        """Форматирование частичной анкеты для промпта"""
        fields = [
            'project_name', 'project_goal', 'problem_statement',
            'target_audience', 'geography', 'project_tasks',
            'methodology', 'expected_results', 'budget',
            'budget_breakdown', 'team_experience', 'partnerships',
            'risk_management', 'sustainability', 'project_duration'
        ]

        formatted = []
        for field in fields:
            value = anketa.get(field)
            if value:
                formatted.append(f"{field}: {value}")

        return "\n".join(formatted)

    async def _final_audit(self, anketa: Dict[str, Any]) -> Dict[str, Any]:
        """
        Финальный комплексный аудит всей анкеты

        Использует AuditorAgent для полной оценки по 10 критериям
        """
        logger.info("  [Final Audit] Запуск комплексного аудита...")

        try:
            # Формируем input для AuditorAgent
            audit_input = {
                'application': anketa,
                'user_answers': anketa,
                'selected_grant': {
                    'fund_name': anketa.get('grant_fund', 'Фонд президентских грантов')
                }
            }

            # Вызываем аудитор
            audit_wrapped = await self.auditor.audit_application_async(audit_input)

            # BaseAgent.prepare_output() оборачивает результат в {'result': {...}}
            audit_result = audit_wrapped.get('result', audit_wrapped)

            # Debug: выводим что вернул аудитор
            overall_score = audit_result.get('overall_score', 0)
            logger.info(f"    Overall score: {overall_score:.3f} ({int(overall_score * 100)}/100)")
            logger.info(f"    Readiness: {audit_result.get('readiness_status', 'N/A')}")
            logger.info(f"    Analysis keys: {list(audit_result.get('analysis', {}).keys())}")

            return audit_result

        except Exception as e:
            logger.error(f"❌ Ошибка final audit: {e}")
            # Fallback: базовая оценка
            return {
                'total_score': 60,
                'scores': {},
                'improvement_suggestions': [],
                'final_verdict': 'Аудит не удалось выполнить полностью'
            }

    async def _save_anketa_to_db(
        self,
        anketa: Dict[str, Any],
        audit_result: Dict[str, Any]
    ) -> str:
        """
        Сохранить анкету в БД

        Таблица: sessions (данные в JSONB полях interview_data и audit_result)
        """
        logger.info("  [Save] Сохранение анкеты в БД...")

        try:
            # Генерация anketa_id (номенклатура)
            import random
            import json
            anketa_id = f"AN-{datetime.now().strftime('%Y%m%d')}-{anketa['username']}-{random.randint(1, 999):03d}"

            audit_score = int(audit_result.get('overall_score', 0) * 100)
            logger.info(f"    Anketa ID: {anketa_id}")
            logger.info(f"    Audit score: {audit_score}/100")

            # Подготовить данные для JSONB полей
            interview_data_json = json.dumps(anketa, ensure_ascii=False)
            audit_result_json = json.dumps(audit_result, ensure_ascii=False)

            # INSERT в таблицу sessions (согласно реальной схеме)
            with self.db.connect() as conn:
                cursor = conn.cursor()

                # Сначала убедиться, что пользователь существует в users (foreign key requirement)
                cursor.execute(
                    """
                    INSERT INTO users (telegram_id, username, first_name, last_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (telegram_id) DO NOTHING
                    """,
                    (
                        anketa.get('telegram_id'),
                        anketa.get('username', 'unknown'),
                        anketa.get('first_name', ''),
                        anketa.get('last_name', ''),
                        'user'
                    )
                )
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        anketa_id, telegram_id, project_name,
                        interview_data, audit_result,
                        status, completion_status,
                        started_at, completed_at,
                        current_stage, progress_percentage
                    ) VALUES (
                        %s, %s, %s,
                        %s::jsonb, %s::jsonb,
                        %s, %s,
                        %s, %s,
                        %s, %s
                    )
                    """,
                    (
                        anketa_id,
                        anketa.get('telegram_id'),
                        anketa.get('project_name', 'Untitled Project'),
                        interview_data_json,
                        audit_result_json,
                        'active', 'completed',
                        datetime.now(), datetime.now(),
                        'completed', 100
                    )
                )
                conn.commit()
                cursor.close()

            logger.info(f"    ✅ Анкета сохранена в БД: {anketa_id}")

            return anketa_id

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения анкеты: {e}", exc_info=True)
            return f"AN-ERROR-{int(time.time())}"

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основной метод обработки (синхронная обёртка для BaseAgent)

        Args:
            data: Данные пользователя + ответы на вопросы

        Returns:
            Результат интервью с анкетой и аудитом
        """
        return asyncio.run(self.conduct_interview_with_audit(data))


# Удобная обёртка для быстрого вызова
async def conduct_interactive_interview(
    db,
    user_data: Dict[str, Any],
    llm_provider: str = "claude_code"
) -> Dict[str, Any]:
    """
    Провести интерактивное интервью с аудитом

    Args:
        db: Database instance
        user_data: Данные пользователя + ответы на вопросы
        llm_provider: LLM провайдер (default: claude_code, можно выбрать gigachat)

    Returns:
        Результат интервью с анкетой и аудитом
    """
    interviewer = InteractiveInterviewerAgent(db, llm_provider=llm_provider)
    return await interviewer.conduct_interview_with_audit(user_data)


if __name__ == "__main__":
    # Тестовый запуск
    print("InteractiveInterviewerAgent - тестовый модуль")
    print("Используйте: test_archery_club_fpg_e2e.py для полного E2E теста")
