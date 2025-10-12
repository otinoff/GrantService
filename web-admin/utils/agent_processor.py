#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Queue Processor
=====================
Обработка очередей для каждого типа агента

Author: Claude Code
Created: 2025-10-11
"""

import sys
import os
import logging
import traceback
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Добавляем пути к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

from utils.postgres_helper import execute_query, execute_update
from data.database.models import GrantServiceDatabase

logger = logging.getLogger(__name__)


async def _send_audit_pdf_to_admin(
    session_id: int,
    anketa_id: str,
    audit_result: Dict[str, Any],
    average_score: float,
    approval_status: str
):
    """
    Отправить PDF отчет о завершении аудита в админский чат

    Args:
        session_id: ID сессии
        anketa_id: ID анкеты
        audit_result: Результаты аудита от агента
        average_score: Средняя оценка (1-10)
        approval_status: Статус одобрения (approved/needs_revision/rejected)
    """
    try:
        logger.info(f"📄 Начинаем генерацию audit PDF для сессии {session_id}")

        # Подготовка данных для PDF
        audit_data = {
            'session_id': session_id,
            'anketa_id': anketa_id,
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': audit_result.get('overall_score', average_score),
            'average_score': average_score,
            'approval_status': approval_status,
            'completeness_score': audit_result.get('completeness_score', 70),
            'quality_score': audit_result.get('quality_score', 70),
            'compliance_score': audit_result.get('compliance_score', 70),
            'readiness_status': audit_result.get('readiness_status', 'Не готово'),
            'recommendations': audit_result.get('recommendations', []),
            'detailed_analysis': audit_result.get('detailed_analysis', ''),
            'strengths': audit_result.get('strengths', []),
            'weaknesses': audit_result.get('weaknesses', [])
        }

        logger.info(f"✅ Данные для PDF подготовлены: score={average_score}, status={approval_status}")

        # Генерация PDF
        # Импортируем из telegram-bot/utils
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'telegram-bot'))
        from utils.stage_report_generator import generate_stage_pdf

        pdf_bytes = generate_stage_pdf('audit', audit_data)
        logger.info(f"✅ PDF сгенерирован: {len(pdf_bytes)} bytes")

        # Отправка в админский чат
        from utils.admin_notifications import AdminNotifier

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
            return

        notifier = AdminNotifier(bot_token)

        await notifier.send_stage_completion_pdf(
            stage='audit',
            pdf_bytes=pdf_bytes,
            filename=f"{anketa_id}_AUDIT.pdf",
            caption=f"🔍 Аудит завершен\nОценка: {average_score:.1f}/10\nСтатус: {approval_status}\nID: {anketa_id}",
            anketa_id=anketa_id
        )

        logger.info(f"✅ Audit PDF успешно отправлен в админский чат: {anketa_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка отправки audit PDF для сессии {session_id}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def _send_review_pdf_to_admin(
    grant_id: int,
    anketa_id: str,
    review_result: Dict[str, Any]
):
    """
    Отправить PDF отчет о завершении рецензирования в админский чат

    Args:
        grant_id: ID гранта
        anketa_id: ID анкеты
        review_result: Результаты рецензирования от агента
    """
    try:
        logger.info(f"📄 Начинаем генерацию review PDF для гранта {grant_id}")

        # Подготовка данных для PDF
        review_data = {
            'grant_id': grant_id,
            'anketa_id': anketa_id,
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'readiness_score': review_result.get('readiness_score', 0),
            'approval_probability': review_result.get('approval_probability', 0),
            'strengths': review_result.get('strengths', []),
            'weaknesses': review_result.get('weaknesses', []),
            'recommendations': review_result.get('recommendations', []),
            'detailed_review': review_result.get('detailed_review', ''),
            'final_verdict': review_result.get('final_verdict', '')
        }

        logger.info(f"✅ Данные для PDF подготовлены: score={review_data['readiness_score']}/10, probability={review_data['approval_probability']}%")

        # Генерация PDF
        # Импортируем из telegram-bot/utils
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'telegram-bot'))
        from utils.stage_report_generator import generate_stage_pdf

        pdf_bytes = generate_stage_pdf('review', review_data)
        logger.info(f"✅ PDF сгенерирован: {len(pdf_bytes)} bytes")

        # Отправка в админский чат
        from utils.admin_notifications import AdminNotifier

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
            return

        notifier = AdminNotifier(bot_token)

        await notifier.send_stage_completion_pdf(
            stage='review',
            pdf_bytes=pdf_bytes,
            filename=f"{grant_id}_REVIEW.pdf",
            caption=f"👁️ Ревью завершено\nОценка готовности: {review_data['readiness_score']:.1f}/10\nВероятность одобрения: {review_data['approval_probability']}%\nID: {grant_id}",
            anketa_id=anketa_id
        )

        logger.info(f"✅ Review PDF успешно отправлен в админский чат: {grant_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка отправки review PDF для гранта {grant_id}: {e}")
        import traceback
        traceback.print_exc()
        raise


class AgentProcessingResult:
    """Результат обработки одного элемента очереди"""

    def __init__(self, success: bool, item_id: Any, message: str, details: Optional[Dict] = None):
        self.success = success
        self.item_id = item_id
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()


class QueueProcessingStats:
    """Статистика обработки очереди"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.total_items = 0
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        self.results: List[AgentProcessingResult] = []
        self.start_time = datetime.now()
        self.end_time = None

    def add_result(self, result: AgentProcessingResult):
        """Добавить результат обработки"""
        self.results.append(result)
        self.processed += 1
        if result.success:
            self.succeeded += 1
        else:
            self.failed += 1

    def finish(self):
        """Завершить обработку"""
        self.end_time = datetime.now()

    def get_duration(self) -> float:
        """Получить длительность обработки в секундах"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def to_dict(self) -> Dict:
        """Преобразовать в словарь"""
        return {
            'agent_name': self.agent_name,
            'total_items': self.total_items,
            'processed': self.processed,
            'succeeded': self.succeeded,
            'failed': self.failed,
            'duration': self.get_duration(),
            'results': [
                {
                    'success': r.success,
                    'item_id': r.item_id,
                    'message': r.message,
                    'details': r.details
                }
                for r in self.results
            ]
        }


async def process_auditor_queue(limit: int = 10) -> QueueProcessingStats:
    """
    Обработать очередь Auditor агента

    Auditor обрабатывает сессии, у которых:
    - Есть anketa_id
    - current_stage != 'interviewer'
    - Нет записи в auditor_results

    Args:
        limit: Максимальное количество элементов для обработки

    Returns:
        QueueProcessingStats с результатами обработки
    """
    stats = QueueProcessingStats('auditor')

    try:
        print(f"\n{'='*60}")
        print(f"🔍 ЗАПУСК ОБРАБОТКИ ОЧЕРЕДИ AUDITOR (limit={limit})")
        print(f"{'='*60}")
        logger.info(f"🔍 Начинаем обработку очереди Auditor (limit={limit})...")

        # Получить элементы из очереди
        print(f"📋 Запрос элементов из очереди...")
        queue_items = execute_query("""
            SELECT
                s.id as session_id,
                s.anketa_id,
                s.telegram_id,
                s.current_stage,
                s.status
            FROM sessions s
            WHERE s.anketa_id IS NOT NULL
              AND s.status != 'archived'
              AND s.current_stage != 'interviewer'
              AND NOT EXISTS (
                  SELECT 1 FROM auditor_results ar
                  WHERE ar.session_id = s.id
              )
            ORDER BY s.id ASC
            LIMIT %s
        """, (limit,))

        stats.total_items = len(queue_items)
        print(f"📊 Найдено элементов в очереди: {stats.total_items}")
        logger.info(f"📋 Найдено элементов в очереди: {stats.total_items}")

        if stats.total_items == 0:
            print("✅ Очередь Auditor пуста")
            logger.info("✅ Очередь Auditor пуста")
            stats.finish()
            return stats

        # Импортируем агента
        try:
            print(f"📦 Импорт AuditorAgent...")
            from agents.auditor_agent import AuditorAgent
        except ImportError as e:
            print(f"❌ ОШИБКА: Не удалось импортировать AuditorAgent: {e}")
            logger.error(f"❌ Не удалось импортировать AuditorAgent: {e}")
            stats.finish()
            return stats

        # Обработать каждый элемент
        print(f"🔌 Подключение к БД...")
        db = GrantServiceDatabase()
        print(f"🤖 Инициализация AuditorAgent (provider=claude_code)...")
        auditor = AuditorAgent(db=db, llm_provider='claude_code')
        print(f"✅ Агент готов к работе\n")

        for idx, item in enumerate(queue_items, 1):
                session_id = item['session_id']
                anketa_id = item['anketa_id']

                try:
                    print(f"⏳ [{idx}/{stats.total_items}] Обработка сессии {session_id} (anketa: {anketa_id})...")
                    logger.info(f"🔄 Обработка сессии {session_id} (anketa: {anketa_id})...")

                    # Загрузить данные сессии
                    print(f"   📥 Загрузка данных сессии {session_id}...")
                    session_data = db.get_session_by_id(session_id)
                    if not session_data:
                        result = AgentProcessingResult(
                            success=False,
                            item_id=session_id,
                            message=f"Сессия {session_id} не найдена"
                        )
                        stats.add_result(result)
                        continue

                    # Подготовить данные для аудитора
                    input_data = {
                        'session_id': session_id,
                        'anketa_id': anketa_id,
                        'user_answers': session_data.get('user_answers', {}),
                        'application': session_data.get('grant_application', {}),
                        'research_data': {},  # TODO: загрузить research если есть
                        'selected_grant': {}
                    }

                    # Вызвать агента
                    print(f"   🤖 Запуск Auditor агента для сессии {session_id}...")
                    start_audit = time.time()
                    audit_result = auditor.process(input_data)
                    audit_time = time.time() - start_audit
                    print(f"   ✅ Auditor завершил работу за {audit_time:.1f}s")
                    print(f"   📊 Результат: overall_score={audit_result.get('overall_score', 0):.2f}, status={audit_result.get('status')}")

                    if audit_result.get('status') == 'success':
                        # Сохранить результаты в auditor_results
                        # Схема: completeness_score, clarity_score, feasibility_score, innovation_score, quality_score,
                        #        average_score, approval_status, recommendations, auditor_llm_provider, model, metadata

                        # Преобразуем наши scores в схему таблицы (0-100 -> 1-10)
                        completeness = int(audit_result.get('completeness_score', 70))
                        quality = int(audit_result.get('quality_score', 70))
                        compliance = int(audit_result.get('compliance_score', 70))

                        # Рассчитываем 5 оценок по шкале 1-10
                        comp_score = min(10, max(1, completeness // 10))
                        clar_score = min(10, max(1, quality // 10))
                        feas_score = min(10, max(1, compliance // 10))
                        inno_score = min(10, max(1, quality // 10))
                        qual_score = min(10, max(1, quality // 10))

                        # ВАЖНО: average_score должен быть средним арифметическим (database constraint)
                        average_score = round((comp_score + clar_score + feas_score + inno_score + qual_score) / 5.0, 2)

                        # Маппинг статусов
                        status_map = {
                            'Отлично': 'approved',
                            'Хорошо': 'approved',
                            'Удовлетворительно': 'needs_revision',
                            'Требует доработки': 'needs_revision',
                            'Не готово': 'rejected'
                        }
                        approval_status = status_map.get(
                            audit_result.get('readiness_status', 'Не готово'),
                            'needs_revision'
                        )

                        print(f"   💾 Сохранение результатов в БД (avg_score={average_score}, status={approval_status})...")
                        start_db = time.time()

                        execute_update("""
                            INSERT INTO auditor_results (
                                session_id, completeness_score, clarity_score,
                                feasibility_score, innovation_score, quality_score,
                                average_score, approval_status, recommendations,
                                auditor_llm_provider, model, metadata
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            session_id,
                            comp_score,
                            clar_score,
                            feas_score,
                            inno_score,
                            qual_score,
                            average_score,
                            approval_status,
                            json.dumps(audit_result.get('recommendations', []), ensure_ascii=False),
                            'claude_code',
                            'sonnet',
                            json.dumps(audit_result, ensure_ascii=False)
                        ))

                        db_time = time.time() - start_db
                        print(f"   ✅ Результаты сохранены в БД за {db_time:.2f}s")

                        # 📄 ОТПРАВКА PDF АУДИТА В АДМИНСКИЙ ЧАТ
                        try:
                            print(f"   📄 Отправка audit PDF в админский чат...")
                            await _send_audit_pdf_to_admin(
                                session_id=session_id,
                                anketa_id=anketa_id,
                                audit_result=audit_result,
                                average_score=average_score,
                                approval_status=approval_status
                            )
                            print(f"   ✅ Audit PDF отправлен в админский чат")
                        except Exception as pdf_error:
                            print(f"   ⚠️  Ошибка отправки audit PDF: {pdf_error}")
                            logger.error(f"❌ Ошибка отправки audit PDF для сессии {session_id}: {pdf_error}")
                            # Не прерываем выполнение - это не критично

                        result = AgentProcessingResult(
                            success=True,
                            item_id=session_id,
                            message=f"Аудит завершен: {audit_result.get('overall_score', 0):.2f}",
                            details={'score': audit_result.get('overall_score')}
                        )
                        logger.info(f"✅ Сессия {session_id} обработана успешно")
                    else:
                        result = AgentProcessingResult(
                            success=False,
                            item_id=session_id,
                            message=f"Ошибка аудита: {audit_result.get('message', 'Unknown')}"
                        )
                        logger.error(f"❌ Ошибка обработки сессии {session_id}")

                    stats.add_result(result)

                except Exception as e:
                    print(f"   ❌ ОШИБКА обработки сессии {session_id}: {e}")
                    logger.error(f"❌ Ошибка обработки сессии {session_id}: {e}")
                    logger.error(traceback.format_exc())
                    result = AgentProcessingResult(
                        success=False,
                        item_id=session_id,
                        message=f"Исключение: {str(e)}"
                    )
                    stats.add_result(result)

        stats.finish()
        print(f"\n{'='*60}")
        print(f"✅ ОБРАБОТКА ЗАВЕРШЕНА: {stats.succeeded}/{stats.total_items} успешно")
        print(f"⏱️  Время: {stats.get_duration():.1f}s")
        print(f"{'='*60}\n")
        logger.info(f"✅ Обработка Auditor завершена: {stats.succeeded}/{stats.total_items} успешно")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки очереди Auditor: {e}")
        logger.error(traceback.format_exc())
        stats.finish()

    return stats


def process_researcher_queue(limit: int = 10) -> QueueProcessingStats:
    """
    Обработать очередь Researcher агента

    Researcher обрабатывает сессии, у которых:
    - Есть anketa_id
    - Есть auditor_results
    - Нет completed research в researcher_research

    Args:
        limit: Максимальное количество элементов для обработки

    Returns:
        QueueProcessingStats с результатами обработки
    """
    stats = QueueProcessingStats('researcher')

    try:
        logger.info(f"🔍 Начинаем обработку очереди Researcher (limit={limit})...")

        # Получить элементы из очереди
        queue_items = execute_query("""
            SELECT
                s.id as session_id,
                s.anketa_id,
                s.telegram_id,
                s.current_stage
            FROM sessions s
            WHERE s.anketa_id IS NOT NULL
              AND s.status != 'archived'
              AND EXISTS (
                  SELECT 1 FROM auditor_results ar
                  WHERE ar.session_id = s.id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM researcher_research rr
                  WHERE rr.session_id = s.id
                    AND rr.status = 'completed'
              )
            ORDER BY s.id ASC
            LIMIT %s
        """, (limit,))

        stats.total_items = len(queue_items)
        logger.info(f"📋 Найдено элементов в очереди: {stats.total_items}")

        if stats.total_items == 0:
            logger.info("✅ Очередь Researcher пуста")
            stats.finish()
            return stats

        # Импортируем агента
        try:
            from agents.researcher_agent_v2 import ResearcherAgentV2
        except ImportError as e:
            logger.error(f"❌ Не удалось импортировать ResearcherAgentV2: {e}")
            stats.finish()
            return stats

        # Обработать каждый элемент
        db = GrantServiceDatabase()
        researcher = ResearcherAgentV2(db=db, llm_provider='claude_code')

        for item in queue_items:
                session_id = item['session_id']
                anketa_id = item['anketa_id']

                try:
                    logger.info(f"🔄 Обработка исследования для anketa: {anketa_id}...")

                    # Вызвать агента
                    research_result = researcher.process({'anketa_id': anketa_id})

                    if research_result.get('status') == 'completed':
                        result = AgentProcessingResult(
                            success=True,
                            item_id=session_id,
                            message=f"Исследование завершено: {research_result.get('research_id')}",
                            details={
                                'research_id': research_result.get('research_id'),
                                'sources_count': research_result.get('research_results', {}).get('metadata', {}).get('sources_count', 0)
                            }
                        )
                        logger.info(f"✅ Исследование для anketa {anketa_id} завершено")
                    else:
                        result = AgentProcessingResult(
                            success=False,
                            item_id=session_id,
                            message=f"Ошибка исследования: {research_result.get('error', 'Unknown')}"
                        )
                        logger.error(f"❌ Ошибка исследования для anketa {anketa_id}")

                    stats.add_result(result)

                except Exception as e:
                    logger.error(f"❌ Ошибка обработки исследования {anketa_id}: {e}")
                    logger.error(traceback.format_exc())
                    result = AgentProcessingResult(
                        success=False,
                        item_id=session_id,
                        message=f"Исключение: {str(e)}"
                    )
                    stats.add_result(result)

        stats.finish()
        logger.info(f"✅ Обработка Researcher завершена: {stats.succeeded}/{stats.total_items} успешно")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки очереди Researcher: {e}")
        logger.error(traceback.format_exc())
        stats.finish()

    return stats


def process_writer_queue(limit: int = 10) -> QueueProcessingStats:
    """
    Обработать очередь Writer агента

    Writer обрабатывает сессии, у которых:
    - Есть anketa_id
    - Есть completed research
    - Нет гранта в grants

    Args:
        limit: Максимальное количество элементов для обработки

    Returns:
        QueueProcessingStats с результатами обработки
    """
    stats = QueueProcessingStats('writer')

    try:
        logger.info(f"🔍 Начинаем обработку очереди Writer (limit={limit})...")

        # Получить элементы из очереди
        queue_items = execute_query("""
            SELECT
                s.id as session_id,
                s.anketa_id,
                s.telegram_id,
                rr.research_id
            FROM sessions s
            INNER JOIN researcher_research rr ON rr.session_id = s.id
            WHERE s.anketa_id IS NOT NULL
              AND s.status != 'archived'
              AND rr.status = 'completed'
              AND NOT EXISTS (
                  SELECT 1 FROM grants g
                  WHERE g.anketa_id = s.anketa_id
              )
            ORDER BY s.id ASC
            LIMIT %s
        """, (limit,))

        stats.total_items = len(queue_items)
        logger.info(f"📋 Найдено элементов в очереди: {stats.total_items}")

        if stats.total_items == 0:
            logger.info("✅ Очередь Writer пуста")
            stats.finish()
            return stats

        # Импортируем агента
        try:
            from agents.writer_agent_v2 import WriterAgentV2
        except ImportError as e:
            logger.error(f"❌ Не удалось импортировать WriterAgentV2: {e}")
            stats.finish()
            return stats

        # Обработать каждый элемент
        db = GrantServiceDatabase()
        writer = WriterAgentV2(db=db, llm_provider='claude_code')

        for item in queue_items:
                session_id = item['session_id']
                anketa_id = item['anketa_id']
                research_id = item.get('research_id')

                try:
                    logger.info(f"🔄 Генерация гранта для anketa: {anketa_id}...")

                    # Подготовить данные для райтера
                    input_data = {
                        'anketa_id': anketa_id,
                        'session_id': session_id,
                        'research_id': research_id
                    }

                    # Вызвать агента
                    writer_result = writer.process(input_data)

                    if writer_result.get('status') == 'success':
                        result = AgentProcessingResult(
                            success=True,
                            item_id=session_id,
                            message=f"Грант создан: {writer_result.get('grant_id')}",
                            details={
                                'grant_id': writer_result.get('grant_id'),
                                'grant_number': writer_result.get('grant_number')
                            }
                        )
                        logger.info(f"✅ Грант для anketa {anketa_id} создан")
                    else:
                        result = AgentProcessingResult(
                            success=False,
                            item_id=session_id,
                            message=f"Ошибка создания гранта: {writer_result.get('error', 'Unknown')}"
                        )
                        logger.error(f"❌ Ошибка создания гранта для anketa {anketa_id}")

                    stats.add_result(result)

                except Exception as e:
                    logger.error(f"❌ Ошибка обработки writer {anketa_id}: {e}")
                    logger.error(traceback.format_exc())
                    result = AgentProcessingResult(
                        success=False,
                        item_id=session_id,
                        message=f"Исключение: {str(e)}"
                    )
                    stats.add_result(result)

        stats.finish()
        logger.info(f"✅ Обработка Writer завершена: {stats.succeeded}/{stats.total_items} успешно")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки очереди Writer: {e}")
        logger.error(traceback.format_exc())
        stats.finish()

    return stats


async def process_reviewer_queue(limit: int = 10) -> QueueProcessingStats:
    """
    Обработать очередь Reviewer агента

    Reviewer обрабатывает гранты, у которых:
    - Нет review_score
    - status != 'archived'

    Args:
        limit: Максимальное количество элементов для обработки

    Returns:
        QueueProcessingStats с результатами обработки
    """
    stats = QueueProcessingStats('reviewer')

    try:
        logger.info(f"🔍 Начинаем обработку очереди Reviewer (limit={limit})...")

        # Получить элементы из очереди
        queue_items = execute_query("""
            SELECT
                g.id as grant_id,
                g.anketa_id,
                g.telegram_id,
                g.status,
                g.grant_text
            FROM grants g
            WHERE g.review_score IS NULL
              AND g.status != 'archived'
            ORDER BY g.id ASC
            LIMIT %s
        """, (limit,))

        stats.total_items = len(queue_items)
        logger.info(f"📋 Найдено элементов в очереди: {stats.total_items}")

        if stats.total_items == 0:
            logger.info("✅ Очередь Reviewer пуста")
            stats.finish()
            return stats

        # Импортируем агента
        try:
            from agents.reviewer_agent import ReviewerAgent
        except ImportError as e:
            logger.error(f"❌ Не удалось импортировать ReviewerAgent: {e}")
            stats.finish()
            return stats

        # Обработать каждый элемент
        db = GrantServiceDatabase()
        reviewer = ReviewerAgent(db=db, llm_provider='claude_code')

        for item in queue_items:
                grant_id = item['grant_id']
                anketa_id = item['anketa_id']

                try:
                    logger.info(f"🔄 Рецензирование гранта {grant_id}...")

                    # Загрузить данные гранта
                    grant_data = db.get_grant_by_id(grant_id)
                    if not grant_data:
                        result = AgentProcessingResult(
                            success=False,
                            item_id=grant_id,
                            message=f"Грант {grant_id} не найден"
                        )
                        stats.add_result(result)
                        continue

                    # Загрузить research results
                    research_data = execute_query("""
                        SELECT research_results
                        FROM researcher_research
                        WHERE anketa_id = %s AND status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (anketa_id,))

                    research_results = research_data[0]['research_results'] if research_data else {}

                    # Подготовить данные для рецензента
                    input_data = {
                        'grant_id': grant_id,
                        'grant_content': grant_data.get('grant_text', {}),
                        'research_results': research_results,
                        'user_answers': {},
                        'citations': grant_data.get('citations', []),
                        'tables': grant_data.get('tables', []),
                        'selected_grant': {}
                    }

                    # Вызвать агента
                    review_result = reviewer.process(input_data)

                    if review_result.get('status') == 'success':
                        # Сохранить результаты review в grants
                        execute_update("""
                            UPDATE grants
                            SET review_score = %s,
                                review_approval_probability = %s,
                                review_strengths = %s,
                                review_weaknesses = %s,
                                review_recommendations = %s,
                                review_data = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            review_result.get('readiness_score'),
                            review_result.get('approval_probability'),
                            json.dumps(review_result.get('strengths', []), ensure_ascii=False),
                            json.dumps(review_result.get('weaknesses', []), ensure_ascii=False),
                            json.dumps(review_result.get('recommendations', []), ensure_ascii=False),
                            json.dumps(review_result, ensure_ascii=False),
                            grant_id
                        ))

                        # 📄 ОТПРАВКА PDF РЕВЬЮ В АДМИНСКИЙ ЧАТ
                        try:
                            await _send_review_pdf_to_admin(
                                grant_id=grant_id,
                                anketa_id=anketa_id,
                                review_result=review_result
                            )
                        except Exception as pdf_error:
                            logger.error(f"❌ Ошибка отправки review PDF для гранта {grant_id}: {pdf_error}")
                            # Не прерываем выполнение - это не критично

                        result = AgentProcessingResult(
                            success=True,
                            item_id=grant_id,
                            message=f"Рецензия завершена: {review_result.get('readiness_score', 0):.2f}/10",
                            details={
                                'readiness_score': review_result.get('readiness_score'),
                                'approval_probability': review_result.get('approval_probability')
                            }
                        )
                        logger.info(f"✅ Грант {grant_id} рецензирован успешно")
                    else:
                        result = AgentProcessingResult(
                            success=False,
                            item_id=grant_id,
                            message=f"Ошибка рецензии: {review_result.get('message', 'Unknown')}"
                        )
                        logger.error(f"❌ Ошибка рецензии гранта {grant_id}")

                    stats.add_result(result)

                except Exception as e:
                    logger.error(f"❌ Ошибка обработки reviewer {grant_id}: {e}")
                    logger.error(traceback.format_exc())
                    result = AgentProcessingResult(
                        success=False,
                        item_id=grant_id,
                        message=f"Исключение: {str(e)}"
                    )
                    stats.add_result(result)

        stats.finish()
        logger.info(f"✅ Обработка Reviewer завершена: {stats.succeeded}/{stats.total_items} успешно")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки очереди Reviewer: {e}")
        logger.error(traceback.format_exc())
        stats.finish()

    return stats


def process_agent_queue(agent_name: str, limit: int = 10) -> QueueProcessingStats:
    """
    Обработать очередь для указанного агента

    Args:
        agent_name: Название агента (auditor, researcher, writer, reviewer)
        limit: Максимальное количество элементов для обработки

    Returns:
        QueueProcessingStats с результатами обработки
    """
    agent_processors = {
        'auditor': process_auditor_queue,
        'researcher': process_researcher_queue,
        'writer': process_writer_queue,
        'reviewer': process_reviewer_queue,
    }

    processor = agent_processors.get(agent_name)

    if not processor:
        logger.error(f"❌ Неизвестный агент: {agent_name}")
        stats = QueueProcessingStats(agent_name)
        stats.finish()
        return stats

    return processor(limit=limit)


__all__ = [
    'process_auditor_queue',
    'process_researcher_queue',
    'process_writer_queue',
    'process_reviewer_queue',
    'process_agent_queue',
    'QueueProcessingStats',
    'AgentProcessingResult',
]
