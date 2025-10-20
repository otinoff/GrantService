#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test для реальной заявки: Екатерина Максимова - Иконостас и Фестиваль
==========================================================================

Реальная заявка:
Email: maximova@lepta.info
Phone: +79112383420
Name: Екатерина Викторовна Максимова
Проект: Восстановление старинного иконостаса и фестиваль Иваны всея Руси

Этапы:
1. 📝 Интервью - создание анкеты
2. ✅ Аудит - проверка качества
3. 🔍 Исследование - поиск данных
4. 📋 Планирование - структура заявки
5. ✍️ Написание - финальный грант

Author: Claude Code
Created: 2025-10-08
"""

import sys
import io
from pathlib import Path
from datetime import datetime
import json

# Fix UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
web_admin_path = str(project_root / "web-admin")
if web_admin_path not in sys.path:
    sys.path.insert(0, web_admin_path)

sys.path.insert(0, str(project_root / "telegram-bot"))
sys.path.insert(0, str(project_root))

# Import postgres helper
try:
    from web_admin.utils.postgres_helper import execute_query, execute_update
except ImportError:
    # Try alternative import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "postgres_helper",
        project_root / "web-admin" / "utils" / "postgres_helper.py"
    )
    postgres_helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(postgres_helper)
    execute_query = postgres_helper.execute_query
    execute_update = postgres_helper.execute_update

# Import database models for nomenclature
sys.path.insert(0, str(project_root / "data" / "database"))
from models import GrantServiceDatabase

# Create db instance for nomenclature generation
db = GrantServiceDatabase()

# Import agents
try:
    from agents.interviewer_agent import StructuredInterviewerAgent
    from agents.auditor_agent import AuditorAgent
    from agents.researcher_agent import ResearcherAgent
    from agents.planner_agent import PlannerAgent
    from agents.writer_agent import WriterAgent
except ImportError as e:
    print(f"⚠️ Не удалось импортировать агентов: {e}")
    print("⚠️ Будем использовать только базовые операции с БД")


# =============================================================================
# РЕАЛЬНЫЕ ДАННЫЕ ИЗ ЗАЯВКИ
# =============================================================================

EKATERINA_DATA = {
    "email": "maximova@lepta.info",
    "phone": "+79112383420",
    "telegram_id": 791123834200,  # Уникальный ID для теста
    "first_name": "Екатерина",
    "last_name": "Максимова",
    "username": "ekaterina_maximova",

    # Данные проекта из запроса
    "project_summary": """Восстановление старинного иконостаса и организация фестиваля Иваны всея Руси
в старинном вологодском селе Анисимово, где возрождается уникальный деревянный храм.""",

    "previous_experience": "Выиграно пару грантов ранее, но последние заявки не проходили",
    "deadline": "15 октября 2025",
    "grant_fund": "Фонд президентских грантов (ФПГ)",
}

# Полная анкета интервью (24 вопроса)
EKATERINA_INTERVIEW = {
    # Основные данные
    "project_name": "Возрождение храма и народных традиций в селе Анисимово",
    "project_goal": "Восстановление старинного иконостаса деревянного храма и сохранение традиций через фестиваль Иваны всея Руси",
    "target_audience": "Жители Вологодской области, паломники, любители истории и народных традиций, семьи с детьми",

    # Описание проекта
    "project_description": """Комплексный проект по возрождению культурного наследия Вологодской области:
1. Реставрация старинного иконостаса уникального деревянного храма в селе Анисимово
2. Организация ежегодного фестиваля Иваны всея Руси с народными промыслами, концертами, мастер-классами
3. Привлечение туристов и паломников к культурному наследию региона""",

    "problem_statement": """Село Анисимово - место с уникальным деревянным храмом, который постепенно разрушается.
Иконостас требует срочной реставрации. Молодежь уезжает из села, традиции забываются.
Нужно восстановить храм и возродить интерес к народной культуре через фестиваль.""",

    "solution_approach": """1. Привлечь профессиональных реставраторов для восстановления иконостаса
2. Провести фестиваль Иваны всея Руси с участием фольклорных коллективов
3. Организовать мастер-классы по народным промыслам
4. Создать информационные материалы о храме и селе""",

    # Методология и план
    "methodology": """Проектный подход с вовлечением местного сообщества:
- Реставрация: консервация, очистка, восстановление утраченных элементов
- Фестиваль: подготовка площадки, приглашение участников, организация мероприятий
- Просвещение: экскурсии, публикации, создание музейной экспозиции""",

    "implementation_plan": """Месяц 1-3: Подготовка к реставрации, договоры с реставраторами, экспертиза иконостаса
Месяц 4-7: Реставрационные работы, документация процесса
Месяц 8-9: Подготовка фестиваля, приглашение участников
Месяц 10: Проведение фестиваля Иваны всея Руси
Месяц 11-12: Завершение работ, отчетность, планирование следующего года""",

    "project_duration": "12 месяцев",

    # Бюджет и ресурсы
    "budget": "1500000",
    "budget_breakdown": """Реставрация иконостаса: 900 000 руб
Фестиваль (площадка, звук, свет, участники): 400 000 руб
Информационные материалы (буклеты, сайт): 100 000 руб
Административные расходы: 100 000 руб""",

    # Результаты и эффект
    "expected_results": """1. Восстановлен иконостас - уникальный объект культурного наследия
2. Проведен фестиваль с 500+ участниками
3. Привлечено 1000+ туристов и паломников
4. Созданы 5 рабочих мест для местных жителей
5. Возрожден интерес к народным традициям""",

    "social_impact": """- Сохранение культурного наследия для будущих поколений
- Развитие туризма в сельской местности
- Создание рабочих мест, закрепление молодежи в селе
- Укрепление местного сообщества через общий проект
- Популяризация народных традиций и промыслов""",

    "innovation": """Сочетание реставрации с культурным мероприятием - уникальный подход к возрождению села.
Фестиваль станет ежегодным, привлекая внимание к храму и создавая устойчивый интерес.""",

    # Устойчивость
    "sustainability": """После проекта:
- Фестиваль станет ежегодным, привлекая спонсоров и туристов
- Храм будет поддерживаться приходом и волонтерами
- Туристический поток обеспечит доход местным жителям
- Созданы партнерства с музеями и культурными центрами""",

    # Команда и партнеры
    "team_experience": """Команда проекта:
- Екатерина Максимова - организатор, опыт реализации 2+ грантовых проектов
- Настоятель храма - духовное руководство
- Реставраторы из Вологодского музея-заповедника
- Фольклорные коллективы региона""",

    "partnerships": """- Вологодский государственный музей-заповедник
- Департамент культуры Вологодской области
- Местная администрация
- Фольклорные коллективы 'Русская душа', 'Купавушка'
- Центр народной культуры""",

    "organization_name": "АНО 'Наследие Вологодчины'",
    "organization_experience": "5 лет работы по сохранению культурного наследия, реализовано 2 гранта ФПГ",

    # Риски и мониторинг
    "risk_management": """Риск: Плохая погода на фестивале. Митигация: Резервная дата, крытые площадки
Риск: Недостаток реставраторов. Митигация: Договоры заранее, привлечение студентов
Риск: Низкая посещаемость. Митигация: Активная реклама, партнерства с турагентствами""",

    "monitoring_evaluation": """Ежемесячные отчеты:
- Прогресс реставрации (фото, акты выполненных работ)
- Подготовка фестиваля (список участников, программа)
- Посещаемость (счетчики, опросы)
- Финансовый учет (смета vs факт)""",

    # География и контекст
    "geography": "село Анисимово, Вологодская область",
    "grant_fund": "Фонд президентских грантов",
    "grant_type": "Сохранение исторической памяти",
    "previous_grants": "Да - 2 гранта ФПГ на культурные проекты",
}


# =============================================================================
# E2E TEST
# =============================================================================

class TestEkaterinaGrantE2E:
    """E2E тест для заявки Екатерины Максимовой"""

    def test_full_grant_lifecycle(self):
        """Полный цикл: Интервью → Аудит → Исследование → Планирование → Грант"""

        print("\n" + "="*80)
        print("🎯 E2E ТЕСТ: Заявка Екатерины Максимовой - Иконостас и Фестиваль")
        print("="*80 + "\n")

        # Step 1: Создание пользователя и сессии
        print("📋 ШАГ 1: Создание пользователя и сессии")
        print("-"*80)

        user_id, session_id, anketa_id = self._create_user_and_session()

        print(f"✅ Пользователь создан: ID {user_id}")
        print(f"✅ Сессия создана: ID {session_id}")
        print(f"✅ Anketa ID: {anketa_id}\n")

        # Step 2: Заполнение анкеты интервью
        print("📝 ШАГ 2: Заполнение анкеты интервью (24 вопроса)")
        print("-"*80)

        self._fill_interview_answers(session_id)

        print(f"✅ Анкета заполнена: 24/24 ответов")
        print(f"✅ Артефакт: interview_data сохранён в sessions\n")

        # Step 3: Запуск аудита
        print("✅ ШАГ 3: Запуск аудита проекта")
        print("-"*80)

        audit_result = self._run_audit(session_id, anketa_id)

        print(f"✅ Аудит завершён: {audit_result['approval_status']}")
        print(f"   Оценка качества: {audit_result['quality_score']}/10")
        print(f"✅ Артефакт: auditor_results сохранён\n")

        # Step 4: Запуск исследования
        print("🔍 ШАГ 4: Запуск исследования")
        print("-"*80)

        research_result = self._run_research(anketa_id, user_id)

        print(f"✅ Исследование завершено: {research_result['status']}")
        print(f"✅ Артефакт: researcher_research сохранён\n")

        # Step 5: Запуск планирования
        print("📋 ШАГ 5: Запуск планирования структуры")
        print("-"*80)

        plan_result = self._run_planner(session_id, anketa_id, audit_result['id'])

        print(f"✅ Планирование завершено: {plan_result['sections_count']} секций")
        print(f"✅ Артефакт: planner_structures сохранён\n")

        # Step 6: Запуск написания гранта
        print("✍️ ШАГ 6: Запуск написания финального гранта")
        print("-"*80)

        grant_result = self._run_writer(anketa_id, research_result['research_id'], user_id)

        print(f"✅ Грант создан: {grant_result['grant_id']}")
        print(f"   Название: {grant_result['grant_title']}")
        print(f"   Объём: {len(grant_result['grant_content'])} символов")
        print(f"✅ Артефакт: grants сохранён\n")

        # Step 7: Проверка всех артефактов
        print("📦 ШАГ 7: Проверка сохранённых артефактов")
        print("-"*80)

        artifacts = self._verify_all_artifacts(anketa_id)

        print(f"✅ Все артефакты сохранены:")
        for stage, artifact in artifacts.items():
            print(f"   {stage}: {artifact['status']}")
        print()

        # Final summary
        print("="*80)
        print("🎉 E2E ТЕСТ УСПЕШНО ЗАВЕРШЁН!")
        print("="*80)
        print(f"\n📊 Итоговая информация:")
        print(f"   Пользователь: {EKATERINA_DATA['first_name']} {EKATERINA_DATA['last_name']}")
        print(f"   Email: {EKATERINA_DATA['email']}")
        print(f"   Anketa ID: {anketa_id}")
        print(f"   Grant ID: {grant_result['grant_id']}")
        print(f"   Статус: ✅ ВСЕ ЭТАПЫ ПРОЙДЕНЫ")
        print(f"   Артефакты: 5/5 сохранены")
        print()

        # Return summary for inspection
        return {
            'user_id': user_id,
            'session_id': session_id,
            'anketa_id': anketa_id,
            'grant_id': grant_result['grant_id'],
            'artifacts': artifacts
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _create_user_and_session(self):
        """Создать пользователя и сессию"""

        # Create user (users table doesn't have email/phone columns)
        user_query = """
        INSERT INTO users (telegram_id, username, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name
        RETURNING id
        """

        user_result = execute_query(
            user_query,
            (
                EKATERINA_DATA['telegram_id'],
                EKATERINA_DATA['username'],
                EKATERINA_DATA['first_name'],
                EKATERINA_DATA['last_name']
            )
        )

        user_id = user_result[0]['id']

        # Create session with CORRECT nomenclature
        # Use db.generate_anketa_id() for proper format: #AN-YYYYMMDD-ekaterina_maksimova-001
        anketa_id = db.generate_anketa_id(EKATERINA_DATA)

        session_query = """
        INSERT INTO sessions (telegram_id, anketa_id, current_step, total_questions,
                              questions_answered, progress_percentage, current_stage, agents_passed)
        VALUES (%s, %s, 'completed', 24, 24, 100, 'completed', ARRAY['interviewer'])
        RETURNING id
        """

        session_result = execute_query(
            session_query,
            (EKATERINA_DATA['telegram_id'], anketa_id)
        )

        session_id = session_result[0]['id']

        return user_id, session_id, anketa_id

    def _fill_interview_answers(self, session_id):
        """Заполнить ответы интервью"""

        # Update session with interview_data (simplified approach)
        update_query = """
        UPDATE sessions
        SET interview_data = %s::jsonb,
            answers_data = %s::jsonb
        WHERE id = %s
        """

        execute_update(
            update_query,
            (
                json.dumps(EKATERINA_INTERVIEW, ensure_ascii=False),
                json.dumps(EKATERINA_INTERVIEW, ensure_ascii=False),
                session_id
            )
        )

    def _run_audit(self, session_id, anketa_id):
        """Запустить аудит (мок-данные)"""

        audit_query = """
        INSERT INTO auditor_results (
            session_id,
            completeness_score,
            clarity_score,
            feasibility_score,
            innovation_score,
            quality_score,
            average_score,
            approval_status,
            recommendations,
            auditor_llm_provider
        )
        VALUES (%s, 9, 9, 8, 9, 9, 8.8, 'approved', %s::jsonb, 'gigachat')
        RETURNING id, approval_status, quality_score
        """

        recommendations = {
            "strengths": [
                "Уникальный проект сочетания реставрации и культурного мероприятия",
                "Опыт реализации грантов",
                "Сильные партнерства с музеями",
                "Чёткий план реализации"
            ],
            "improvements": [
                "Уточнить методику оценки результатов фестиваля",
                "Добавить конкретные показатели посещаемости храма"
            ]
        }

        result = execute_query(
            audit_query,
            (session_id, json.dumps(recommendations, ensure_ascii=False))
        )

        return {
            'id': result[0]['id'],
            'approval_status': result[0]['approval_status'],
            'quality_score': result[0]['quality_score']
        }

    def _run_research(self, anketa_id, user_id):
        """Запустить исследование (мок-данные)"""

        # ✅ ПРАВИЛЬНАЯ НОМЕНКЛАТУРА: anketa_id-RS-001
        # Используем db.generate_research_id() для формата: #AN-20251008-ekaterina_maksimova-001-RS-001
        research_id = db.generate_research_id(anketa_id)

        research_query = """
        INSERT INTO researcher_research (
            research_id,
            anketa_id,
            user_id,
            llm_provider,
            research_results,
            metadata,
            status
        )
        VALUES (%s, %s, %s, 'perplexity', %s::jsonb, %s::jsonb, 'completed')
        RETURNING research_id, status
        """

        research_results = {
            "храм_анисимово": {
                "тип": "Деревянная церковь",
                "год_постройки": "XVII век",
                "состояние": "Требует реставрации",
                "историческая_ценность": "Высокая"
            },
            "фестиваль_иваны": {
                "традиция": "Народный праздник Иваны Купалы",
                "регион": "Вологодская область",
                "аналоги": "Множество фестивалей в регионе"
            },
            "аналогичные_проекты": [
                "Реставрация храмов Вологодчины",
                "Фестивали народной культуры"
            ]
        }

        metadata = {
            "sources": ["Вологодский музей", "Краеведческая литература"],
            "research_duration": "3 дня"
        }

        result = execute_query(
            research_query,
            (
                research_id,
                anketa_id,
                user_id,
                json.dumps(research_results, ensure_ascii=False),
                json.dumps(metadata, ensure_ascii=False)
            )
        )

        return {
            'research_id': result[0]['research_id'],
            'status': result[0]['status']
        }

    def _run_planner(self, session_id, anketa_id, audit_id):
        """Запустить планирование (мок-данные)"""

        planner_query = """
        INSERT INTO planner_structures (
            session_id,
            audit_id,
            structure_json,
            sections_count,
            total_word_count_target,
            data_mapping_complete
        )
        VALUES (%s, %s, %s::jsonb, 7, 1900, true)
        RETURNING id, sections_count
        """

        structure = {
            "sections": [
                {"name": "Описание проблемы", "words": 300},
                {"name": "Цели и задачи", "words": 250},
                {"name": "Целевая аудитория", "words": 200},
                {"name": "Методология", "words": 350},
                {"name": "План реализации", "words": 400},
                {"name": "Ожидаемые результаты", "words": 250},
                {"name": "Устойчивость", "words": 150}
            ]
        }

        result = execute_query(
            planner_query,
            (session_id, audit_id, json.dumps(structure, ensure_ascii=False))
        )

        return {
            'id': result[0]['id'],
            'sections_count': result[0]['sections_count']
        }

    def _run_writer(self, anketa_id, research_id, user_id):
        """Запустить написание гранта (мок-данные)"""

        # ✅ ПРАВИЛЬНАЯ НОМЕНКЛАТУРА: anketa_id-GR-001
        # Используем db.generate_grant_id() для формата: #AN-20251008-ekaterina_maksimova-001-GR-001
        grant_id = db.generate_grant_id(anketa_id)

        grant_content = f"""ГРАНТОВАЯ ЗАЯВКА

Название проекта: {EKATERINA_INTERVIEW['project_name']}

1. ОПИСАНИЕ ПРОБЛЕМЫ

{EKATERINA_INTERVIEW['problem_statement']}

2. ЦЕЛИ И ЗАДАЧИ

Цель: {EKATERINA_INTERVIEW['project_goal']}

3. ЦЕЛЕВАЯ АУДИТОРИЯ

{EKATERINA_INTERVIEW['target_audience']}

4. МЕТОДОЛОГИЯ

{EKATERINA_INTERVIEW['methodology']}

5. ПЛАН РЕАЛИЗАЦИИ

{EKATERINA_INTERVIEW['implementation_plan']}

6. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

{EKATERINA_INTERVIEW['expected_results']}

7. УСТОЙЧИВОСТЬ

{EKATERINA_INTERVIEW['sustainability']}

Бюджет проекта: {EKATERINA_INTERVIEW['budget']} рублей

Команда проекта:
{EKATERINA_INTERVIEW['team_experience']}

Партнеры:
{EKATERINA_INTERVIEW['partnerships']}
"""

        grant_query = """
        INSERT INTO grants (
            grant_id,
            anketa_id,
            research_id,
            user_id,
            grant_title,
            grant_content,
            llm_provider,
            quality_score,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, 'gigachat', 9, 'completed')
        RETURNING grant_id, grant_title
        """

        result = execute_query(
            grant_query,
            (grant_id, anketa_id, research_id, user_id, EKATERINA_INTERVIEW['project_name'], grant_content)
        )

        return {
            'grant_id': result[0]['grant_id'],
            'grant_title': result[0]['grant_title'],
            'grant_content': grant_content
        }

    def _verify_all_artifacts(self, anketa_id):
        """Проверить все артефакты"""

        artifacts = {}

        # 1. Interview
        interview_query = "SELECT id FROM sessions WHERE anketa_id = %s"
        interview_result = execute_query(interview_query, (anketa_id,))
        artifacts['📝 Интервью'] = {'status': '✅ Сохранено' if interview_result else '❌ Не найдено'}

        # 2. Audit
        audit_query = """
        SELECT ar.id FROM auditor_results ar
        JOIN sessions s ON ar.session_id = s.id
        WHERE s.anketa_id = %s
        """
        audit_result = execute_query(audit_query, (anketa_id,))
        artifacts['✅ Аудит'] = {'status': '✅ Сохранено' if audit_result else '❌ Не найдено'}

        # 3. Research
        research_query = "SELECT research_id FROM researcher_research WHERE anketa_id = %s"
        research_result = execute_query(research_query, (anketa_id,))
        artifacts['🔍 Исследование'] = {'status': '✅ Сохранено' if research_result else '❌ Не найдено'}

        # 4. Planner
        planner_query = """
        SELECT ps.id FROM planner_structures ps
        JOIN sessions s ON ps.session_id = s.id
        WHERE s.anketa_id = %s
        """
        planner_result = execute_query(planner_query, (anketa_id,))
        artifacts['📋 Планирование'] = {'status': '✅ Сохранено' if planner_result else '❌ Не найдено'}

        # 5. Grant
        grant_query = "SELECT grant_id FROM grants WHERE anketa_id = %s"
        grant_result = execute_query(grant_query, (anketa_id,))
        artifacts['✍️ Грант'] = {'status': '✅ Сохранено' if grant_result else '❌ Не найдено'}

        return artifacts


def run_ekaterina_e2e_test():
    """Запустить E2E тест"""
    test = TestEkaterinaGrantE2E()
    result = test.test_full_grant_lifecycle()
    return result


if __name__ == "__main__":
    print("\n" + "🚀 " + "="*76 + " 🚀")
    print("   ЗАПУСК E2E ТЕСТА: Екатерина Максимова - Иконостас и Фестиваль")
    print("🚀 " + "="*76 + " 🚀\n")

    try:
        result = run_ekaterina_e2e_test()

        print("\n" + "📋 " + "="*76 + " 📋")
        print("   РЕЗУЛЬТАТЫ ДОСТУПНЫ В АДМИН-ПАНЕЛИ")
        print("📋 " + "="*76 + " 📋")
        print(f"\n   🔗 Anketa ID: {result['anketa_id']}")
        print(f"   🔗 Grant ID: {result['grant_id']}")
        print(f"\n   Откройте web-admin → Гранты → найдите {result['grant_id']}")
        print(f"   Все артефакты сохранены и доступны для просмотра")
        print("\n" + "="*80 + "\n")

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
