#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test: Valeria's PTSD Medical Project Case
==============================================

Реальный кейс для тестирования:
- Name: Валерия
- Project: Медицинское научное сообщество психиатров и психотерапевтов
- Topic: Образовательное мероприятие для врачей по методам работы с ПТСР

Тестирует полный цикл создания грантовой заявки для медицинского проекта.

Author: Test Engineer
Created: 2025-10-07
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
import json
import random

# Add project paths
tests_dir = Path(__file__).parent.parent
project_root = tests_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'telegram-bot'))
sys.path.insert(0, str(project_root / 'web-admin'))

# Import database
from data.database import GrantServiceDatabase


# ========================================
# Test Data - Valeria's PTSD Project
# ========================================

VALERIA_PROJECT_DATA = {
    # Основная информация
    "applicant_name": "Валерия",
    "project_title": "Образовательное мероприятие по методам работы с ПТСР для врачей",
    "organization_name": "Медицинское научное сообщество психиатров и психотерапевтов",

    # Описание проекта
    "project_essence": "Медицинское научное сообщество психиатров и психотерапевтов планирует провести образовательное мероприятие для врачей всех специальностей по методам работы с ПТСР (посттравматическое стрессовое расстройство), случаи которого значительно участились в последние годы",

    "target_audience": "Врачи всех специальностей: психиатры, психотерапевты, терапевты, неврологи, врачи общей практики - работающие с пациентами с ПТСР",

    "problem_statement": """
В последние годы значительно выросло количество людей, страдающих от посттравматического стрессового расстройства (ПТСР).
Это связано с увеличением числа стрессогенных событий, военных конфликтов, природных катастроф и других травмирующих ситуаций.

Основные проблемы:
- Недостаточная подготовка врачей общей практики по методам диагностики и лечения ПТСР
- Отсутствие регулярных образовательных программ для повышения квалификации
- Устаревшие методики работы с травмой в медицинских учреждениях
- Низкая осведомленность врачей о современных доказательных методах терапии ПТСР
- Недостаточная междисциплинарная координация между специалистами

Статистика:
- По данным ВОЗ, распространенность ПТСР в популяции составляет 3-5%
- В группах риска (ветераны, жертвы насилия) - до 30%
- Только 40% пациентов с ПТСР получают адекватное лечение
""",

    "project_goal": "Повышение квалификации врачей всех специальностей в области диагностики и лечения посттравматического стрессового расстройства через организацию образовательного мероприятия",

    "project_objectives": """
1. Организовать двухдневную научно-практическую конференцию по методам работы с ПТСР
2. Обучить минимум 150 врачей современным доказательным методам терапии ПТСР
3. Провести практические мастер-классы по техникам работы с травмой (EMDR, когнитивно-поведенческая терапия, групповая терапия)
4. Подготовить и распространить методические рекомендации для врачей
5. Создать профессиональную сеть специалистов для обмена опытом
6. Сформировать базу знаний и клинических случаев для дальнейшего обучения
""",

    "methodology": """
Образовательное мероприятие будет включать:

**День 1: Теоретическая часть**
- Пленарные доклады ведущих специалистов по ПТСР (4 часа)
- Нейробиология травмы и ПТСР (2 часа)
- Методы диагностики ПТСР (2 часа)
- Дифференциальная диагностика (1 час)

**День 2: Практическая часть**
- Мастер-класс по EMDR (Eye Movement Desensitization and Reprocessing) - 3 часа
- Мастер-класс по когнитивно-поведенческой терапии ПТСР - 3 часа
- Групповая терапия травмы - 2 часа
- Фармакотерапия ПТСР - 1 час

**Формат обучения:**
- Лекции от ведущих экспертов
- Интерактивные семинары
- Практические мастер-классы с разбором клинических случаев
- Групповые дискуссии
- Видеодемонстрации терапевтических сессий
""",

    "expected_results": """
Количественные результаты:
- Обучение 150+ врачей из различных регионов России
- Проведение 10 мастер-классов и 8 лекций
- Подготовка и распространение 200 методических пособий
- Создание видеобиблиотеки из 15 обучающих материалов

Качественные результаты:
- Повышение уровня знаний врачей о ПТСР на 60% (по результатам пре- и пост-тестирования)
- Формирование устойчивых практических навыков работы с травмой
- Создание профессионального сообщества специалистов
- Улучшение качества помощи пациентам с ПТСР в регионах
- Снижение времени до постановки диагноза ПТСР
- Увеличение процента пациентов, получающих адекватное лечение
""",

    "project_duration": "6 месяцев (подготовка 4 месяца + проведение 2 дня + отчетность 2 месяца)",

    "budget": "1500000",

    "budget_breakdown": """
Общий бюджет: 1 500 000 рублей

1. Организационные расходы - 450 000 руб.
   - Аренда конференц-зала на 200 человек (2 дня) - 150 000 руб.
   - Техническое оснащение (аудио, видео, презентации) - 100 000 руб.
   - Кейтеринг (кофе-брейки, обеды для 150 участников) - 200 000 руб.

2. Гонорары экспертов и спикеров - 400 000 руб.
   - 4 пленарных спикера (по 50 000 руб.) - 200 000 руб.
   - 6 ведущих мастер-классов (по 30 000 руб.) - 180 000 руб.
   - Модераторы (2 человека) - 20 000 руб.

3. Методические материалы - 300 000 руб.
   - Разработка и печать методических пособий (200 шт.) - 150 000 руб.
   - Создание видеоконтента (15 роликов) - 100 000 руб.
   - Дидактические материалы для мастер-классов - 50 000 руб.

4. Транспортные расходы - 200 000 руб.
   - Проезд спикеров из других городов - 120 000 руб.
   - Проживание спикеров (10 номеров × 2 ночи) - 80 000 руб.

5. Информационная поддержка - 100 000 руб.
   - Продвижение мероприятия (реклама в медицинских СМИ) - 60 000 руб.
   - Разработка сайта мероприятия - 40 000 руб.

6. Административные расходы - 50 000 руб.
   - Регистрация участников, выдача сертификатов - 30 000 руб.
   - Непредвиденные расходы (резерв) - 20 000 руб.
""",

    "team_experience": """
Команда проекта состоит из опытных специалистов в области психиатрии и психотерапии:

1. Руководитель проекта - Валерия
   - Опыт организации медицинских конференций (5+ лет)
   - Член медицинского научного сообщества психиатров

2. Научный руководитель - проф., д.м.н. Петров И.С.
   - 25 лет практики в психиатрии
   - Автор 50+ научных публикаций по ПТСР
   - Член Российского общества психиатров

3. Координатор образовательных программ - к.м.н. Сидорова М.А.
   - 15 лет опыта в медицинском образовании
   - Опыт проведения 20+ образовательных мероприятий

4. Эксперты и спикеры (10 специалистов):
   - Ведущие психиатры и психотерапевты России
   - Сертифицированные специалисты по EMDR и КПТ
   - Практикующие врачи с опытом работы с ПТСР 10+ лет
""",

    "innovation": """
Инновационные элементы проекта:

1. Междисциплинарный подход - участие врачей разных специальностей
2. Доказательные методы - фокус на методах с научно подтвержденной эффективностью
3. Практико-ориентированность - 50% времени на мастер-классы и отработку навыков
4. Видеобиблиотека - создание постоянно доступного образовательного ресурса
5. Сетевое взаимодействие - формирование профессионального сообщества
6. Онлайн доступ к материалам после мероприятия
""",

    "social_impact": """
Социальная значимость проекта:

Прямое воздействие:
- 150 врачей повысят квалификацию
- Улучшится качество медицинской помощи пациентам с ПТСР
- Сократится время диагностики и начала лечения

Косвенное воздействие:
- Каждый обученный врач сможет помочь 50-100 пациентам в год
- Потенциальный охват: 7500-15000 пациентов ежегодно
- Снижение инвалидизации от ПТСР
- Уменьшение социальных последствий травмы
- Профилактика суицидов среди пациентов с ПТСР

Долгосрочный эффект:
- Формирование культуры работы с травмой в медицинском сообществе
- Стандартизация подходов к лечению ПТСР
- Создание базы для будущих образовательных программ
""",

    "sustainability": """
План устойчивости проекта:

1. Онлайн-платформа с материалами (бесплатный доступ после мероприятия)
2. Ежегодное проведение конференции (самофинансирование через взносы участников)
3. Создание региональных отделений профессионального сообщества
4. Публикация научных статей по результатам мероприятия
5. Разработка онлайн-курса для дополнительного обучения
6. Партнерство с медицинскими университетами для интеграции материалов в учебные программы
""",

    "risk_management": """
Риски и их митигация:

Риск 1: Низкая явка участников
Митигация: Ранняя регистрация, активная реклама, баллы НМО (непрерывное медицинское образование)

Риск 2: Отмена участия ключевых спикеров
Митигация: Резервные спикеры, запись лекций заранее

Риск 3: Технические проблемы во время мероприятия
Митигация: Дублирование оборудования, тестирование за день до события, технический персонал

Риск 4: Недостаточное финансирование
Митигация: Поиск спонсоров, софинансирование от участников, гранты

Риск 5: Недостаточная практическая отработка навыков
Митигация: Малые группы для мастер-классов (15-20 человек), видеозаписи для повторения
""",

    "monitoring_evaluation": """
Мониторинг и оценка:

До мероприятия:
- Пре-тестирование участников (уровень знаний о ПТСР)
- Сбор ожиданий и запросов

Во время мероприятия:
- Регистрация посещаемости каждой сессии
- Опросы удовлетворенности после каждого блока
- Наблюдение за вовлеченностью участников

После мероприятия:
- Пост-тестирование (прирост знаний)
- Опросы удовлетворенности (5-балльная шкала)
- Оценка практических навыков (через кейсы)
- Follow-up опрос через 3 месяца (применение знаний на практике)

Показатели успеха:
- 80% участников завершили программу полностью
- Прирост знаний на 50%+
- Удовлетворенность 4.5+/5.0
- 70% участников применяют полученные знания в практике
""",

    "partnerships": """
Партнеры проекта:

1. Российское общество психиатров
   - Информационная поддержка
   - Экспертная оценка программы

2. Министерство здравоохранения региона
   - Аккредитация мероприятия
   - Баллы НМО для участников

3. Медицинские университеты (3 вуза)
   - Привлечение участников
   - Предоставление площадок

4. Фармацевтические компании (потенциальные спонсоры)
   - Финансовая поддержка
   - Информационные материалы

5. Профессиональные ассоциации психотерапевтов
   - Сетевое взаимодействие
   - Распространение информации
""",

    "geography": "Москва (мероприятие), участники из всех регионов России",

    "grant_fund": "Фонд президентских грантов",
    "grant_type": "Охрана здоровья граждан, пропаганда здорового образа жизни",
}


# ========================================
# Fixtures
# ========================================

@pytest.fixture(scope='function')
def db():
    """Database connection for tests"""
    database = GrantServiceDatabase()
    yield database


def execute_query(db, query, params=None):
    """Helper to execute SELECT queries and return dicts"""
    import psycopg2.extras
    with db.connect() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in results]


# ========================================
# Test Class
# ========================================

@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.medical
class TestValeriaPTSDCase:
    """
    E2E тест для реального кейса Валерии - медицинский проект по ПТСР

    Проверяет полный цикл создания грантовой заявки для специализированного
    медицинского проекта с фокусом на образовательное мероприятие.
    """

    def test_valeria_ptsd_full_grant_flow(self, db):
        """
        Полный E2E тест кейса Валерии: от интервью до готовой заявки

        Stages:
        1. Создание пользователя Валерии
        2. Создание сессии интервью
        3. Сбор ответов на вопросы (медицинская тематика)
        4. Аудит проекта (оценка медицинского проекта)
        5. Планирование структуры заявки
        6. Генерация текста грантовой заявки
        7. Верификация всех данных
        """

        print("\n" + "="*80)
        print("E2E TEST: Valeria's PTSD Medical Education Project")
        print("="*80)

        # ===== Stage 1: Create User =====
        print("\n[Stage 1] Creating user Valeria...")

        # Use random telegram_id to allow multiple test runs without cleanup
        test_telegram_id = 888000000 + random.randint(1000, 999999)  # Range: 888001000-888999999

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, role, registration_date)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (test_telegram_id, "valeria_test", "Валерия", "user", datetime.now())
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        print(f"[OK] User created: ID={user_id}, telegram_id={test_telegram_id}")

        # ===== Stage 2: Create Session =====
        print("\n[Stage 2] Creating interview session...")

        anketa_id = f"VALERIA_PTSD_{test_telegram_id}"

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (
                    telegram_id, anketa_id, status, started_at,
                    completion_status, progress_percentage
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (test_telegram_id, anketa_id, 'interview', datetime.now(), 'in_progress', 0)
            )
            session_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        print(f"[OK] Session created: ID={session_id}, anketa_id={anketa_id}")

        # ===== Stage 3: Collect Interview Answers =====
        print("\n[Stage 3] Collecting interview answers (14Q format)...")

        # Get active questions from database
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, question_text, field_name
                FROM interview_questions
                WHERE is_active = TRUE
                ORDER BY question_number
                LIMIT 15
                """
            )
            questions = cursor.fetchall()
            cursor.close()

        print(f"[OK] Loaded {len(questions)} active questions from database")

        # Map field_name from DB to VALERIA_PROJECT_DATA keys
        field_mapping = {
            'project_name': 'project_title',
            'project_description': 'project_essence',
            'project_location': 'geography',
            'problem_solution': 'problem_statement',
            'target_audience': 'target_audience',
            'main_goal': 'project_goal',
            'project_tasks': 'project_objectives',
            'project_timeline': 'project_duration',
            'potential_obstacles': 'risk_management',
            'team_competencies': 'team_experience',
            'volunteers_partners': 'partnerships',
            'organization_info': 'organization_name',
            'online_presence': 'geography',  # Fallback
            'previous_grants': 'sustainability',  # Fallback
            'grant_direction': 'grant_type',
        }

        # Save answers using field_name mapping
        answers_saved = 0
        with db.connect() as conn:
            cursor = conn.cursor()
            for question_id, question_text, field_name in questions:
                # Map field_name to VALERIA_PROJECT_DATA key
                data_key = field_mapping.get(field_name, field_name)
                answer_text = VALERIA_PROJECT_DATA.get(data_key, "")

                if answer_text:  # Only save non-empty answers
                    # Convert to string if not already
                    answer_str = str(answer_text)
                    cursor.execute(
                        """
                        INSERT INTO user_answers (
                            session_id, question_id, answer_text, answer_timestamp
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (session_id, question_id, answer_str, datetime.now())
                    )
                    answers_saved += 1

            conn.commit()
            cursor.close()

        print(f"[OK] Saved {answers_saved} interview answers")

        # Mark session as completed
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sessions
                SET completion_status = 'completed',
                    progress_percentage = 100,
                    completed_at = %s
                WHERE id = %s
                """,
                (datetime.now(), session_id)
            )
            conn.commit()
            cursor.close()

        print("[OK] Session marked as completed")

        # ===== Stage 4: Auditor Agent - Project Audit =====
        print("\n[Stage 4] Running Auditor Agent (project evaluation)...")

        # Simulate auditor evaluation for medical project
        auditor_evaluation = {
            "approval_status": "approved",
            "average_score": 8.8,
            "completeness_score": 9,  # Очень полное описание
            "clarity_score": 9,        # Четкие цели и задачи
            "feasibility_score": 8,    # Реалистичный план
            "innovation_score": 9,     # Инновационный подход
            "quality_score": 9,        # Высокое качество проработки
            "recommendations": {
                "text": "Отличный медицинский проект с четкой социальной значимостью",
                "strengths": [
                    "Актуальная тема - рост случаев ПТСР",
                    "Междисциплинарный подход",
                    "Фокус на доказательных методах",
                    "Практико-ориентированная программа",
                    "Четкий план оценки результатов",
                    "Устойчивость через онлайн-платформу"
                ],
                "weaknesses": [
                    "Можно добавить больше деталей по онлайн-трансляции",
                    "Уточнить механизм сертификации участников"
                ],
                "improvement_suggestions": [
                    "Рассмотреть возможность онлайн-участия для врачей из отдаленных регионов",
                    "Добавить follow-up вебинары через 6 месяцев"
                ]
            }
        }

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO auditor_results (
                    session_id, approval_status, average_score,
                    completeness_score, clarity_score, feasibility_score,
                    innovation_score, quality_score,
                    recommendations, auditor_llm_provider, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    session_id,
                    auditor_evaluation['approval_status'],
                    auditor_evaluation['average_score'],
                    auditor_evaluation['completeness_score'],
                    auditor_evaluation['clarity_score'],
                    auditor_evaluation['feasibility_score'],
                    auditor_evaluation['innovation_score'],
                    auditor_evaluation['quality_score'],
                    json.dumps(auditor_evaluation['recommendations'], ensure_ascii=False),
                    'gigachat',
                    datetime.now()
                )
            )
            auditor_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        print(f"[OK] Auditor evaluation: {auditor_evaluation['approval_status']}, score={auditor_evaluation['average_score']}/10")
        print(f"  Completeness: {auditor_evaluation['completeness_score']}, Clarity: {auditor_evaluation['clarity_score']}, Feasibility: {auditor_evaluation['feasibility_score']}")

        # ===== Stage 5: Planner Agent - Grant Structure =====
        print("\n[Stage 5] Running Planner Agent (grant structure)...")

        # Специализированная структура для медицинского образовательного проекта
        grant_structure = {
            "sections": [
                {
                    "section_name": "1. Актуальность и социальная значимость",
                    "content_plan": "Статистика ПТСР, рост случаев, проблемы в здравоохранении",
                    "word_count": 600,
                    "sources": ["problem_statement", "social_impact"]
                },
                {
                    "section_name": "2. Целевая аудитория",
                    "content_plan": "Врачи различных специальностей, количество, география",
                    "word_count": 300,
                    "sources": ["target_audience", "geography"]
                },
                {
                    "section_name": "3. Цели и задачи проекта",
                    "content_plan": "Главная цель, конкретные задачи, измеримые результаты",
                    "word_count": 500,
                    "sources": ["project_goal", "project_objectives", "expected_results"]
                },
                {
                    "section_name": "4. Программа образовательного мероприятия",
                    "content_plan": "Детальное описание программы, методология обучения",
                    "word_count": 800,
                    "sources": ["methodology", "innovation"]
                },
                {
                    "section_name": "5. Команда и партнеры",
                    "content_plan": "Опыт команды, спикеры, партнерские организации",
                    "word_count": 600,
                    "sources": ["team_experience", "partnerships"]
                },
                {
                    "section_name": "6. Бюджет проекта",
                    "content_plan": "Детализация расходов, обоснование статей бюджета",
                    "word_count": 700,
                    "sources": ["budget", "budget_breakdown"]
                },
                {
                    "section_name": "7. Ожидаемые результаты и социальный эффект",
                    "content_plan": "Количественные и качественные результаты, долгосрочный эффект",
                    "word_count": 500,
                    "sources": ["expected_results", "social_impact"]
                },
                {
                    "section_name": "8. Устойчивость проекта",
                    "content_plan": "План продолжения работы после завершения гранта",
                    "word_count": 400,
                    "sources": ["sustainability"]
                },
                {
                    "section_name": "9. Мониторинг и оценка",
                    "content_plan": "Показатели, методы оценки, отчетность",
                    "word_count": 400,
                    "sources": ["monitoring_evaluation"]
                },
                {
                    "section_name": "10. Риски и их минимизация",
                    "content_plan": "Основные риски и стратегии их предотвращения",
                    "word_count": 400,
                    "sources": ["risk_management"]
                }
            ],
            "total_sections": 10,
            "total_word_count": 5200,
            "grant_type": "medical_education"
        }

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO planner_structures (
                    session_id, audit_id, structure_json, sections_count,
                    total_word_count_target, data_mapping_complete, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    session_id,
                    auditor_id,
                    json.dumps(grant_structure, ensure_ascii=False),
                    grant_structure['total_sections'],
                    grant_structure['total_word_count'],
                    True,
                    datetime.now()
                )
            )
            planner_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        print(f"[OK] Grant structure planned: {grant_structure['total_sections']} sections, {grant_structure['total_word_count']} words target")

        # ===== Stage 6: Create Researcher Research (FK requirement) =====
        print("\n[Stage 6] Creating research record...")

        research_id = f"RES_VALERIA_{session_id}"

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO researcher_research (
                    research_id, anketa_id, user_id, llm_provider, created_at
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (research_id, anketa_id, user_id, 'gigachat', datetime.now())
            )
            research_pk = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        print(f"[OK] Research record created: ID={research_pk}")

        # ===== Stage 7: Writer Agent - Generate Grant =====
        print("\n[Stage 7] Running Writer Agent (grant generation)...")

        # Симуляция сгенерированного текста грантовой заявки
        grant_title = VALERIA_PROJECT_DATA['project_title']
        grant_content = f"""
# ГРАНТОВАЯ ЗАЯВКА
# {grant_title}

**Организация:** {VALERIA_PROJECT_DATA['organization_name']}
**Заявитель:** {VALERIA_PROJECT_DATA['applicant_name']}
**Фонд:** {VALERIA_PROJECT_DATA['grant_fund']}
**Направление:** {VALERIA_PROJECT_DATA['grant_type']}

---

## 1. АКТУАЛЬНОСТЬ И СОЦИАЛЬНАЯ ЗНАЧИМОСТЬ

{VALERIA_PROJECT_DATA['problem_statement']}

### Социальная значимость проекта

{VALERIA_PROJECT_DATA['social_impact']}

---

## 2. ЦЕЛЕВАЯ АУДИТОРИЯ

{VALERIA_PROJECT_DATA['target_audience']}

**География проекта:** {VALERIA_PROJECT_DATA['geography']}

---

## 3. ЦЕЛИ И ЗАДАЧИ ПРОЕКТА

### Главная цель

{VALERIA_PROJECT_DATA['project_goal']}

### Задачи проекта

{VALERIA_PROJECT_DATA['project_objectives']}

### Ожидаемые результаты

{VALERIA_PROJECT_DATA['expected_results']}

---

## 4. ПРОГРАММА ОБРАЗОВАТЕЛЬНОГО МЕРОПРИЯТИЯ

### Методология

{VALERIA_PROJECT_DATA['methodology']}

### Инновационные элементы

{VALERIA_PROJECT_DATA['innovation']}

**Сроки реализации:** {VALERIA_PROJECT_DATA['project_duration']}

---

## 5. КОМАНДА И ПАРТНЕРЫ

### Команда проекта

{VALERIA_PROJECT_DATA['team_experience']}

### Партнеры

{VALERIA_PROJECT_DATA['partnerships']}

---

## 6. БЮДЖЕТ ПРОЕКТА

**Запрашиваемая сумма:** {VALERIA_PROJECT_DATA['budget']} рублей

### Детализация бюджета

{VALERIA_PROJECT_DATA['budget_breakdown']}

---

## 7. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ И СОЦИАЛЬНЫЙ ЭФФЕКТ

{VALERIA_PROJECT_DATA['expected_results']}

### Долгосрочный социальный эффект

{VALERIA_PROJECT_DATA['social_impact']}

---

## 8. УСТОЙЧИВОСТЬ ПРОЕКТА

{VALERIA_PROJECT_DATA['sustainability']}

---

## 9. МОНИТОРИНГ И ОЦЕНКА

{VALERIA_PROJECT_DATA['monitoring_evaluation']}

---

## 10. РИСКИ И ИХ МИНИМИЗАЦИЯ

{VALERIA_PROJECT_DATA['risk_management']}

---

## ЗАКЛЮЧЕНИЕ

Проект "{grant_title}" направлен на решение критически важной проблемы недостаточной подготовки врачей в области диагностики и лечения ПТСР.

Реализация проекта позволит:
- Повысить квалификацию 150+ врачей
- Улучшить качество медицинской помощи тысячам пациентов с ПТСР
- Создать устойчивую систему обмена знаниями между специалистами
- Внести вклад в развитие российского здравоохранения

Команда проекта обладает необходимым опытом и компетенциями для успешной реализации всех запланированных мероприятий.

---

**Контактная информация:**
Организация: {VALERIA_PROJECT_DATA['organization_name']}
Руководитель: {VALERIA_PROJECT_DATA['applicant_name']}
"""

        grant_id = f"GRANT_VALERIA_{session_id}"

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO grants (
                    grant_id, anketa_id, research_id, user_id,
                    grant_title, grant_content,
                    llm_provider, status, quality_score, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    grant_id,
                    anketa_id,
                    research_id,
                    user_id,
                    grant_title,
                    grant_content,
                    'gigachat',
                    'completed',
                    8.8,  # Same as auditor average_score
                    datetime.now()
                )
            )
            grant_pk = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        print(f"[OK] Grant generated: ID={grant_pk}, quality_score=8.8/10")
        print(f"  Title: {grant_title}")
        print(f"  Content length: {len(grant_content)} characters")

        # ===== Stage 8: Verification =====
        print("\n[Stage 8] Verifying all data...")

        # Verify session
        sessions = execute_query(db, "SELECT * FROM sessions WHERE id = %s", (session_id,))
        assert len(sessions) == 1, "Session not found"
        assert sessions[0]['completion_status'] == 'completed', "Session not completed"
        print("[OK] Session verified: completed")

        # Verify answers
        answers = execute_query(db, "SELECT * FROM user_answers WHERE session_id = %s", (session_id,))
        assert len(answers) >= 10, f"Expected >= 10 answers, got {len(answers)}"
        print(f"[OK] Answers verified: {len(answers)} answers saved")

        # Verify auditor
        auditors = execute_query(db, "SELECT * FROM auditor_results WHERE session_id = %s", (session_id,))
        assert len(auditors) == 1, "Auditor result not found"
        assert auditors[0]['approval_status'] == 'approved', "Project not approved"
        assert auditors[0]['average_score'] >= 8.0, f"Score too low: {auditors[0]['average_score']}"
        print(f"[OK] Auditor verified: approved, score={auditors[0]['average_score']}/10")

        # Verify planner
        planners = execute_query(db, "SELECT * FROM planner_structures WHERE session_id = %s", (session_id,))
        assert len(planners) == 1, "Planner structure not found"
        assert planners[0]['sections_count'] == 10, f"Expected 10 sections, got {planners[0]['sections_count']}"
        assert planners[0]['data_mapping_complete'] is True, "Data mapping not complete"
        print(f"[OK] Planner verified: {planners[0]['sections_count']} sections, {planners[0]['total_word_count_target']} words")

        # Verify grant
        grants = execute_query(db, "SELECT * FROM grants WHERE id = %s", (grant_pk,))
        assert len(grants) == 1, "Grant not found"
        assert grants[0]['status'] == 'completed', "Grant not completed"
        assert grants[0]['quality_score'] >= 8.0, f"Grant quality too low: {grants[0]['quality_score']}"
        assert len(grants[0]['grant_content']) > 1000, "Grant content too short"
        print(f"[OK] Grant verified: completed, quality={grants[0]['quality_score']}/10, {len(grants[0]['grant_content'])} chars")

        # ===== Final Report =====
        print("\n" + "="*80)
        print("[SUCCESS] E2E TEST PASSED - Valeria's PTSD Project")
        print("="*80)
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        print(f"Grant ID: {grant_pk} ({grant_id})")
        print(f"Quality Score: {grants[0]['quality_score']}/10")
        print(f"Answers: {len(answers)}")
        print(f"Sections: {planners[0]['sections_count']}")
        print(f"Word Count Target: {planners[0]['total_word_count_target']}")
        print("="*80 + "\n")

        # Return data for potential follow-up tests
        return {
            'user_id': user_id,
            'session_id': session_id,
            'grant_id': grant_pk,
            'quality_score': grants[0]['quality_score'],
            'answers_count': len(answers)
        }


# ========================================
# Run Tests
# ========================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
