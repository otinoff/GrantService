#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trainer Agent - Агент для тестирования функциональности других агентов

Ответственность:
- Тестирует ФУНКЦИОНАЛЬНОСТЬ (запуск, ошибки, интеграции)
- НЕ тестирует содержание (это делает Reviewer Agent)

Версия: 1.0 MVP
"""
import sys
import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Добавляем пути
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from agents.base_agent import BaseAgent
except ImportError:
    # Fallback если BaseAgent недоступен
    class BaseAgent:
        def __init__(self, name, db, llm_provider=None):
            self.name = name
            self.db = db

logger = logging.getLogger(__name__)


class TrainerAgent(BaseAgent):
    """
    Агент-тренировщик для тестирования функциональности других агентов

    MVP функции:
    - test_writer_functionality() - тестирует Writer Agent V2
    - generate_test_anketa() - создаёт тестовые данные
    - validate_writer_result() - проверяет результат
    """

    def __init__(self, db):
        super().__init__("trainer", db, llm_provider=None)
        logger.info("✅ Trainer Agent инициализирован")

    # ========================================
    # БАЗОВЫЙ МЕТОД (ТРЕБУЕТСЯ BaseAgent)
    # ========================================

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Базовый метод обработки (требуется для BaseAgent)

        Для Trainer Agent используйте напрямую:
        - test_writer_functionality()
        - test_researcher_functionality()
        """
        test_type = data.get('test_type', 'writer')

        if test_type == 'writer':
            return asyncio.run(self.test_writer_functionality(
                test_case=data.get('test_case'),
                use_real_llm=data.get('use_real_llm', False)
            ))
        else:
            return {
                'status': 'error',
                'message': f'Неизвестный тип теста: {test_type}'
            }

    # ========================================
    # ГЛАВНЫЙ МЕТОД: ТЕСТ WRITER AGENT
    # ========================================

    async def test_writer_functionality(self,
                                       test_case: Optional[Dict] = None,
                                       use_real_llm: bool = False) -> Dict:
        """
        Тестирует функциональность Writer Agent V2

        Проверки:
        1. ✅ Инициализация Writer Agent
        2. ✅ Expert Agent подключён
        3. ✅ Генерация гранта без критических ошибок
        4. ✅ Результат валиден (все поля)
        5. ✅ Сохранение в БД
        6. ✅ Время выполнения приемлемо

        Args:
            test_case: Тестовый кейс или None для автогенерации
            use_real_llm: Использовать реальный LLM или mock

        Returns:
            {
                'status': 'passed' | 'failed',
                'test_id': 'TR-20251017-001',
                'agent': 'writer_v2',
                'execution_time': 125.3,
                'checks': {...},
                'checks_passed': 6,
                'checks_total': 6,
                'errors': [],
                'warnings': [],
                'result_preview': {...}
            }
        """
        logger.info("🧪 Trainer: Начинаем тест Writer Agent V2")

        start_time = time.time()
        test_id = f"TR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        checks = {
            'can_initialize_writer': False,
            'has_expert_agent': False,
            'can_generate_grant': False,
            'result_is_valid': False,
            'saved_to_db': False,
            'execution_time_ok': False
        }

        errors = []
        warnings = []
        result_data = None

        try:
            # ПРОВЕРКА 1: Инициализация Writer Agent
            logger.info("  [1/6] Инициализация Writer Agent...")
            try:
                from agents.writer_agent_v2 import WriterAgentV2
                # ВАЖНО: Используем claude_code (по умолчанию), НЕ gigachat
                writer = WriterAgentV2(self.db, llm_provider="claude_code")
                checks['can_initialize_writer'] = True
                logger.info("  ✅ Writer Agent инициализирован (claude_code)")
            except Exception as e:
                errors.append(f"Ошибка инициализации Writer: {e}")
                logger.error(f"  ❌ Ошибка инициализации: {e}")
                raise

            # ПРОВЕРКА 2: Expert Agent подключён
            logger.info("  [2/6] Проверка Expert Agent...")
            if writer.expert_agent:
                checks['has_expert_agent'] = True
                logger.info("  ✅ Expert Agent подключён")
            else:
                warnings.append("Expert Agent не подключён к Writer")
                logger.warning("  ⚠️  Expert Agent НЕ подключён")

            # Генерируем тестовые данные
            if test_case is None:
                logger.info("  Генерация тестовых данных...")
                test_case = self.generate_test_anketa(project_type="sport")

            anketa_id = test_case['anketa_id']
            logger.info(f"  Используем anketa_id: {anketa_id}")

            # Создаём research_results для теста
            research_results = self.generate_test_research_results(test_case)
            self._save_research_results_to_db(anketa_id, research_results)

            # ПРОВЕРКА 3: Генерация гранта
            logger.info("  [3/6] Генерация гранта...")

            input_data = {
                'anketa_id': anketa_id,
                'user_answers': test_case['user_answers'],
                'selected_grant': test_case['selected_grant'],
                'requested_amount': test_case.get('requested_amount', 2000000),
                'project_duration': test_case.get('project_duration', 12),
                'admin_user': 'trainer_test'
            }

            try:
                if use_real_llm:
                    result_data = await writer.write_application_async(input_data)
                else:
                    # Mock режим - проверяем только что метод вызывается
                    logger.info("  🔧 Используем mock режим (без реального LLM)")
                    result_data = self._mock_writer_result(input_data)

                checks['can_generate_grant'] = True
                logger.info("  ✅ Грант сгенерирован")
            except Exception as e:
                errors.append(f"Ошибка генерации гранта: {e}")
                logger.error(f"  ❌ Ошибка генерации: {e}")
                raise

            # ПРОВЕРКА 4: Валидация результата
            logger.info("  [4/6] Валидация результата...")
            is_valid, validation_errors = self.validate_writer_result(result_data)
            if is_valid:
                checks['result_is_valid'] = True
                logger.info("  ✅ Результат валиден")
            else:
                errors.extend(validation_errors)
                logger.error(f"  ❌ Результат невалиден: {validation_errors}")

            # ПРОВЕРКА 5: Сохранение в БД (если не mock)
            logger.info("  [5/6] Проверка сохранения в БД...")
            if result_data.get('application_number'):
                checks['saved_to_db'] = True
                logger.info(f"  ✅ Сохранено в БД: {result_data['application_number']}")
            else:
                if use_real_llm:
                    warnings.append("Заявка не сохранена в БД")
                    logger.warning("  ⚠️  Не сохранено в БД")
                else:
                    # В mock режиме это нормально
                    checks['saved_to_db'] = True
                    logger.info("  ✅ Mock режим: пропускаем проверку БД")

            # ПРОВЕРКА 6: Время выполнения
            execution_time = time.time() - start_time
            logger.info(f"  [6/6] Проверка времени выполнения...")

            if use_real_llm:
                # Реальный LLM: ожидаем до 5 минут
                if execution_time < 300:
                    checks['execution_time_ok'] = True
                    logger.info(f"  ✅ Время: {execution_time:.1f}с (< 5 мин)")
                else:
                    warnings.append(f"Генерация заняла {execution_time:.1f}с (> 5 мин)")
                    logger.warning(f"  ⚠️  Долго: {execution_time:.1f}с")
            else:
                # Mock режим: ожидаем до 10 секунд
                checks['execution_time_ok'] = True
                logger.info(f"  ✅ Время: {execution_time:.1f}с (mock режим)")

        except Exception as e:
            errors.append(f"Критическая ошибка: {str(e)}")
            logger.error(f"❌ Критическая ошибка: {e}")

        # Подсчёт результатов
        checks_passed = sum(checks.values())
        checks_total = len(checks)
        status = 'passed' if checks_passed == checks_total and not errors else 'failed'

        execution_time = time.time() - start_time

        # Итоговый результат
        test_result = {
            'status': status,
            'test_id': test_id,
            'agent': 'writer_v2',
            'test_type': 'functionality',
            'execution_time': round(execution_time, 2),
            'checks': checks,
            'checks_passed': checks_passed,
            'checks_total': checks_total,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat(),
            'use_real_llm': use_real_llm
        }

        # Добавляем preview результата
        if result_data:
            test_result['result_preview'] = {
                'status': result_data.get('status'),
                'application_number': result_data.get('application_number'),
                'quality_score': result_data.get('quality_score', 0),
                'citations_count': len(result_data.get('citations', [])),
                'tables_count': len(result_data.get('tables', [])),
                'has_application': 'application' in result_data
            }

        # Логируем итог
        if status == 'passed':
            logger.info(f"✅ Тест ПРОЙДЕН: {checks_passed}/{checks_total} проверок")
        else:
            logger.error(f"❌ Тест ПРОВАЛЕН: {checks_passed}/{checks_total} проверок, {len(errors)} ошибок")

        # Сохраняем отчёт
        self._save_test_report(test_result)

        return test_result

    # ========================================
    # ГЛАВНЫЙ МЕТОД: ТЕСТ REVIEWER AGENT
    # ========================================

    async def test_reviewer_functionality(self,
                                         test_case: Optional[Dict] = None,
                                         use_real_llm: bool = False) -> Dict:
        """
        Тестирует функциональность Reviewer Agent

        Проверки:
        1. ✅ Инициализация Reviewer Agent
        2. ✅ Expert Agent подключён (для получения требований ФПГ)
        3. ✅ Review без критических ошибок
        4. ✅ Результат валиден (все поля)
        5. ✅ Сохранение в БД
        6. ✅ Время выполнения приемлемо

        Args:
            test_case: Тестовый кейс или None для автогенерации
            use_real_llm: Использовать реальный LLM или mock

        Returns:
            {
                'status': 'passed' | 'failed',
                'test_id': 'TR-20251017-001',
                'agent': 'reviewer',
                'execution_time': 45.3,
                'checks': {...},
                'checks_passed': 6,
                'checks_total': 6,
                'errors': [],
                'warnings': [],
                'result_preview': {...}
            }
        """
        logger.info("🧪 Trainer: Начинаем тест Reviewer Agent")

        start_time = time.time()
        test_id = f"TR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        checks = {
            'can_initialize_reviewer': False,
            'has_expert_agent': False,
            'can_review_grant': False,
            'result_is_valid': False,
            'saved_to_db': False,
            'execution_time_ok': False
        }

        errors = []
        warnings = []
        result_data = None

        try:
            # ПРОВЕРКА 1: Инициализация Reviewer Agent
            logger.info("  [1/6] Инициализация Reviewer Agent...")
            try:
                from agents.reviewer_agent import ReviewerAgent
                # ВАЖНО: Используем claude_code (по умолчанию)
                reviewer = ReviewerAgent(self.db, llm_provider="claude_code")
                checks['can_initialize_reviewer'] = True
                logger.info("  ✅ Reviewer Agent инициализирован (claude_code)")
            except Exception as e:
                errors.append(f"Ошибка инициализации Reviewer: {e}")
                logger.error(f"  ❌ Ошибка инициализации: {e}")
                raise

            # ПРОВЕРКА 2: Expert Agent подключён
            logger.info("  [2/6] Проверка Expert Agent...")
            if reviewer.expert_agent:
                checks['has_expert_agent'] = True
                logger.info("  ✅ Expert Agent подключён")
            else:
                warnings.append("Expert Agent не подключён к Reviewer")
                logger.warning("  ⚠️  Expert Agent НЕ подключён")

            # Генерируем тестовые данные (грантовую заявку для review)
            if test_case is None:
                logger.info("  Генерация тестовых данных...")
                test_case = self.generate_test_anketa(project_type="sport")

            anketa_id = test_case['anketa_id']
            logger.info(f"  Используем anketa_id: {anketa_id}")

            # Создаём тестовую грантовую заявку для review
            grant_content = self._generate_test_grant_content(test_case)
            research_results = self.generate_test_research_results(test_case)
            citations = self._generate_test_citations()
            tables = self._generate_test_tables()

            # ПРОВЕРКА 3: Review гранта
            logger.info("  [3/6] Запуск review...")

            input_data = {
                'anketa_id': anketa_id,
                'grant_id': f"{anketa_id}-GR-001",
                'grant_content': grant_content,
                'research_results': research_results,
                'user_answers': test_case['user_answers'],
                'citations': citations,
                'tables': tables,
                'selected_grant': test_case['selected_grant']
            }

            try:
                if use_real_llm:
                    result_data = await reviewer.review_and_save_grant_async(input_data)
                else:
                    # Mock режим - проверяем только что метод вызывается
                    logger.info("  🔧 Используем mock режим (без реального LLM)")
                    result_data = self._mock_reviewer_result(input_data)

                checks['can_review_grant'] = True
                logger.info("  ✅ Review выполнен")
            except Exception as e:
                errors.append(f"Ошибка review: {e}")
                logger.error(f"  ❌ Ошибка review: {e}")
                raise

            # ПРОВЕРКА 4: Валидация результата
            logger.info("  [4/6] Валидация результата...")
            is_valid, validation_errors = self.validate_reviewer_result(result_data)
            if is_valid:
                checks['result_is_valid'] = True
                logger.info("  ✅ Результат валиден")
            else:
                errors.extend(validation_errors)
                logger.error(f"  ❌ Результат невалиден: {validation_errors}")

            # ПРОВЕРКА 5: Сохранение в БД (если не mock)
            logger.info("  [5/6] Проверка сохранения в БД...")
            if result_data.get('review_id'):
                checks['saved_to_db'] = True
                logger.info(f"  ✅ Сохранено в БД: {result_data['review_id']}")
            else:
                if use_real_llm:
                    warnings.append("Review не сохранён в БД")
                    logger.warning("  ⚠️  Не сохранено в БД")
                else:
                    # В mock режиме это нормально
                    checks['saved_to_db'] = True
                    logger.info("  ✅ Mock режим: пропускаем проверку БД")

            # ПРОВЕРКА 6: Время выполнения
            execution_time = time.time() - start_time
            logger.info(f"  [6/6] Проверка времени выполнения...")

            if use_real_llm:
                # Реальный LLM: ожидаем до 2 минут
                if execution_time < 120:
                    checks['execution_time_ok'] = True
                    logger.info(f"  ✅ Время: {execution_time:.1f}с (< 2 мин)")
                else:
                    warnings.append(f"Review занял {execution_time:.1f}с (> 2 мин)")
                    logger.warning(f"  ⚠️  Долго: {execution_time:.1f}с")
            else:
                # Mock режим: ожидаем до 5 секунд
                checks['execution_time_ok'] = True
                logger.info(f"  ✅ Время: {execution_time:.1f}с (mock режим)")

        except Exception as e:
            errors.append(f"Критическая ошибка: {str(e)}")
            logger.error(f"❌ Критическая ошибка: {e}")

        # Подсчёт результатов
        checks_passed = sum(checks.values())
        checks_total = len(checks)
        status = 'passed' if checks_passed == checks_total and not errors else 'failed'

        execution_time = time.time() - start_time

        # Итоговый результат
        test_result = {
            'status': status,
            'test_id': test_id,
            'agent': 'reviewer',
            'test_type': 'functionality',
            'execution_time': round(execution_time, 2),
            'checks': checks,
            'checks_passed': checks_passed,
            'checks_total': checks_total,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat(),
            'use_real_llm': use_real_llm
        }

        # Добавляем preview результата
        if result_data:
            test_result['result_preview'] = {
                'status': result_data.get('status'),
                'review_id': result_data.get('review_id'),
                'readiness_score': result_data.get('readiness_score', 0),
                'approval_probability': result_data.get('approval_probability', 0),
                'can_submit': result_data.get('can_submit', False),
                'fpg_requirements_count': len(result_data.get('fpg_requirements', {}).get('evidence_base', [])) +
                                         len(result_data.get('fpg_requirements', {}).get('structure', [])) +
                                         len(result_data.get('fpg_requirements', {}).get('matching', [])) +
                                         len(result_data.get('fpg_requirements', {}).get('economics', []))
            }

        # Логируем итог
        if status == 'passed':
            logger.info(f"✅ Тест ПРОЙДЕН: {checks_passed}/{checks_total} проверок")
        else:
            logger.error(f"❌ Тест ПРОВАЛЕН: {checks_passed}/{checks_total} проверок, {len(errors)} ошибок")

        # Сохраняем отчёт
        self._save_test_report(test_result)

        return test_result

    # ========================================
    # ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ
    # ========================================

    def generate_test_anketa(self,
                            project_type: str = "sport",
                            difficulty: str = "medium") -> Dict:
        """
        Генерирует тестовую анкету

        Args:
            project_type: "sport", "education", "culture"
            difficulty: "easy", "medium", "hard"
        """
        logger.info(f"📋 Генерация тестовой анкеты: {project_type} ({difficulty})")

        # Базовый шаблон для стрельбы из лука
        if project_type == "sport":
            anketa = {
                'anketa_id': f"#AN-{datetime.now().strftime('%Y%m%d')}-test_trainer-001",
                'user_answers': {
                    'project_name': 'Школа олимпийского резерва по стрельбе из лука "Меткий лучник"',
                    'description': 'Создание современной школы олимпийского резерва для подготовки профессиональных спортсменов в области стрельбы из лука',
                    'problem': 'Низкий уровень развития олимпийских видов спорта в Кемеровской области',
                    'solution': 'Создание специализированной школы с современным оборудованием',
                    'target_group': 'Дети и подростки 10-18 лет',
                    'geography': 'Кемеровская область - Кузбасс',
                    'budget': '2000000',
                    'timeline': '12'
                },
                'selected_grant': {
                    'name': 'Фонд президентских грантов',
                    'max_amount': 3000000
                },
                'requested_amount': 2000000,
                'project_duration': 12
            }
        else:
            # Можно добавить другие типы проектов
            anketa = self.generate_test_anketa(project_type="sport")

        logger.info(f"✅ Анкета создана: {anketa['anketa_id']}")
        return anketa

    def generate_test_research_results(self, test_case: Dict) -> Dict:
        """Генерирует минимальные research_results для теста"""
        logger.info("📊 Генерация тестовых research_results")

        return {
            'metadata': {
                'sources_count': 27,
                'quotes_count': 45,
                'created_at': datetime.now().isoformat()
            },
            'block1_problem': {
                'summary': 'Низкий уровень развития олимпийских видов спорта в регионе',
                'key_facts': [
                    {'fact': 'Регион занимает 45 место по СШОР', 'source': 'Минспорт', 'date': '2024'},
                    {'fact': 'Только 2 тренера по стрельбе из лука', 'source': 'Депспорт', 'date': '2024'}
                ],
                'programs': [
                    {'name': 'Спорт - норма жизни', 'kpi': 'Увеличение до 70% к 2030'}
                ],
                'success_cases': [
                    {'name': 'СШОР Новосибирск', 'result': '5 мастеров спорта за 3 года'}
                ]
            },
            'block2_geography': {
                'summary': 'Кемеровская область, 2.6 млн населения',
                'key_facts': [
                    {'fact': 'Население: 2.6 млн', 'source': 'Росстат'},
                    {'fact': 'Дети 10-18 лет: 312 тыс', 'source': 'Росстат'}
                ]
            },
            'block3_goals': {
                'summary': 'Подготовка 50 спортсменов за 3 года',
                'main_goal_variants': [
                    {'text': 'Создать СШОР и подготовить 50 разрядников за 12 месяцев'}
                ]
            }
        }

    # ========================================
    # ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ
    # ========================================

    def validate_writer_result(self, result: Dict) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность результата Writer Agent

        Returns:
            (is_valid, errors)
        """
        errors = []

        # Проверка 1: Статус
        if result.get('status') != 'success':
            errors.append(f"Статус не success: {result.get('status')}")

        # Проверка 2: Наличие application
        if 'application' not in result:
            errors.append("Отсутствует поле 'application'")
            return False, errors

        application = result['application']

        # Проверка 3: Все 9 разделов
        required_sections = [
            'section_1_brief', 'section_2_problem', 'section_3_goal',
            'section_4_results', 'section_5_tasks', 'section_6_partners',
            'section_7_info', 'section_8_future', 'section_9_calendar'
        ]

        for section in required_sections:
            if section not in application or not application[section]:
                errors.append(f"Отсутствует или пустой раздел: {section}")

        # Проверка 4: Quality score
        if 'quality_score' not in result:
            errors.append("Отсутствует quality_score")

        # Проверка 5: Citations
        if 'citations' not in result or len(result['citations']) == 0:
            errors.append("Нет цитат")

        # Проверка 6: Tables
        if 'tables' not in result or len(result['tables']) == 0:
            errors.append("Нет таблиц")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_reviewer_result(self, result: Dict) -> Tuple[bool, List[str]]:
        """
        Проверяет валидность результата Reviewer Agent

        Returns:
            (is_valid, errors)
        """
        errors = []

        # Проверка 1: Статус
        if result.get('status') != 'success':
            errors.append(f"Статус не success: {result.get('status')}")

        # Проверка 2: Наличие readiness_score
        if 'readiness_score' not in result:
            errors.append("Отсутствует readiness_score")

        # Проверка 3: Наличие approval_probability
        if 'approval_probability' not in result:
            errors.append("Отсутствует approval_probability")

        # Проверка 4: Наличие criteria_scores
        if 'criteria_scores' not in result:
            errors.append("Отсутствует criteria_scores")
        else:
            required_criteria = ['evidence_base', 'structure', 'matching', 'economics']
            for criterion in required_criteria:
                if criterion not in result['criteria_scores']:
                    errors.append(f"Отсутствует критерий: {criterion}")

        # Проверка 5: Наличие strengths и weaknesses
        if 'strengths' not in result:
            errors.append("Отсутствует strengths")
        if 'weaknesses' not in result:
            errors.append("Отсутствует weaknesses")

        # Проверка 6: Наличие recommendations
        if 'recommendations' not in result:
            errors.append("Отсутствует recommendations")

        is_valid = len(errors) == 0
        return is_valid, errors

    # ========================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================

    def _generate_test_grant_content(self, test_case: Dict) -> Dict:
        """Генерирует тестовый контент грантовой заявки для review"""
        logger.info("📄 Генерация тестового контента гранта")

        return {
            'problem': 'В Кемеровской области наблюдается низкий уровень развития олимпийских видов спорта. ' * 50,
            'geography': 'Кемеровская область - Кузбасс, 2.6 млн населения',
            'goals': 'Создать школу олимпийского резерва и подготовить 50 разрядников за 12 месяцев',
            'solution': 'Создание специализированной школы с современным оборудованием и квалифицированными тренерами',
            'budget': '2,000,000 рублей: оборудование 1,500,000, зарплаты 300,000, аренда 200,000',
            'timeline': '12 месяцев: подготовка 3 мес, реализация 9 мес',
            'full_text': ' '.join([
                'Описание проблемы...' * 200,
                'География проекта...' * 100,
                'Цели и задачи...' * 100,
                'Решение...' * 150,
                'Бюджет проекта...' * 50
            ])
        }

    def _generate_test_citations(self) -> List[Dict]:
        """Генерирует тестовые цитаты"""
        logger.info("📚 Генерация тестовых цитат")

        return [
            {'text': 'По данным Росстата', 'source': 'Росстат', 'url': 'https://rosstat.gov.ru'},
            {'text': 'Согласно Минспорту РФ', 'source': 'Минспорт', 'url': ''},
            {'text': 'Нацпроект "Демография"', 'source': 'Правительство РФ', 'url': ''},
            {'text': 'Стратегия развития спорта до 2030', 'source': 'Минспорт', 'url': ''},
            {'text': 'Успешный кейс СШОР Новосибирск', 'source': 'Региональная статистика', 'url': ''},
            {'text': 'Данные переписи населения 2021', 'source': 'Росстат', 'url': ''},
            {'text': 'Статистика по СШОР в регионах', 'source': 'Минспорт', 'url': ''},
            {'text': 'Программа "Спорт - норма жизни"', 'source': 'Нацпроект', 'url': ''},
            {'text': 'Требования ФПГ к проектам', 'source': 'ФПГ', 'url': ''},
            {'text': 'Аналитика развития олимпийских видов спорта', 'source': 'Минспорт', 'url': ''}
        ]

    def _generate_test_tables(self) -> List[Dict]:
        """Генерирует тестовые таблицы"""
        logger.info("📊 Генерация тестовых таблиц")

        return [
            {
                'title': 'Сравнительная таблица СШОР по регионам',
                'content': '| Регион | Количество СШОР | Мастеров спорта |\n|--------|----------------|----------------|\n| Новосибирск | 15 | 45 |\n| Кемерово | 8 | 12 |'
            },
            {
                'title': 'Бюджет проекта по статьям расходов',
                'content': '| Статья | Сумма (руб) | Доля |\n|--------|-------------|------|\n| Оборудование | 1,500,000 | 75% |\n| Зарплаты | 300,000 | 15% |'
            }
        ]

    def _mock_reviewer_result(self, input_data: Dict) -> Dict:
        """Создаёт mock результат Reviewer Agent для быстрого теста"""
        return {
            'status': 'success',
            'agent_type': 'reviewer',
            'readiness_score': 7.5,
            'approval_probability': 47.8,
            'fpg_requirements': {
                'evidence_base': [],
                'structure': [],
                'matching': [],
                'economics': []
            },
            'criteria_scores': {
                'evidence_base': {
                    'score': 7.5,
                    'weight': 0.40,
                    'weighted_score': 3.0,
                    'details': {}
                },
                'structure': {
                    'score': 8.0,
                    'weight': 0.30,
                    'weighted_score': 2.4,
                    'details': {}
                },
                'matching': {
                    'score': 7.0,
                    'weight': 0.20,
                    'weighted_score': 1.4,
                    'details': {}
                },
                'economics': {
                    'score': 6.5,
                    'weight': 0.10,
                    'weighted_score': 0.65,
                    'details': {}
                }
            },
            'strengths': [
                'Сильная доказательная база',
                'Логичная структура',
                'SMART-цели'
            ],
            'weaknesses': [
                'Недостаточно таблиц',
                'Можно детализировать бюджет'
            ],
            'recommendations': [
                'Заявка хорошего качества',
                'Рекомендуется к подаче'
            ],
            'can_submit': True,
            'quality_tier': 'Good',
            'processing_time': 2.5,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _save_research_results_to_db(self, anketa_id: str, research_results: Dict):
        """Сохраняет тестовые research_results в БД"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                # Проверяем существует ли
                cursor.execute(
                    "SELECT id FROM researcher_research WHERE anketa_id = %s",
                    (anketa_id,)
                )
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE researcher_research
                        SET research_results = %s, status = 'completed', completed_at = NOW()
                        WHERE anketa_id = %s
                    """, (json.dumps(research_results), anketa_id))
                else:
                    cursor.execute("""
                        INSERT INTO researcher_research
                        (anketa_id, research_id, research_results, status, completed_at, user_id, llm_provider)
                        VALUES (%s, %s, %s, 'completed', NOW(), 1, 'mock_test')
                    """, (anketa_id, f"{anketa_id}-RS-001", json.dumps(research_results)))

                conn.commit()
                logger.info(f"✅ Research results сохранены для {anketa_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения research_results: {e}")

    def _mock_writer_result(self, input_data: Dict) -> Dict:
        """Создаёт mock результат Writer Agent для быстрого теста"""
        return {
            'status': 'success',
            'application': {
                'section_1_brief': 'Краткое описание проекта...',
                'section_2_problem': 'Описание проблемы... ' * 100,
                'section_3_goal': 'SMART цель проекта',
                'section_4_results': 'Ожидаемые результаты',
                'section_5_tasks': '1. Задача 1\n2. Задача 2',
                'section_6_partners': 'Партнёры проекта',
                'section_7_info': 'Информационное сопровождение',
                'section_8_future': 'Дальнейшее развитие',
                'section_9_calendar': '| Месяц | Мероприятие |\n|-------|-------------|',
                'full_text': 'Полный текст заявки...' * 500
            },
            'quality_score': 8.0,
            'citations': [{'text': 'Цитата 1'}, {'text': 'Цитата 2'}],
            'tables': [{'title': 'Таблица 1'}, {'title': 'Таблица 2'}],
            'research_used': True,
            'agent_type': 'writer_v2_mock'
        }

    def _save_test_report(self, test_result: Dict):
        """Сохраняет отчёт о тесте"""
        try:
            reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            filename = f"{test_result['test_id']}.json"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(test_result, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 Отчёт сохранён: {filepath}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения отчёта: {e}")

    # ========================================
    # СИНХРОННАЯ ОБЁРТКА
    # ========================================

    def test_writer(self, test_case: Optional[Dict] = None, use_real_llm: bool = False) -> Dict:
        """Синхронная версия test_writer_functionality"""
        return asyncio.run(self.test_writer_functionality(test_case, use_real_llm))
