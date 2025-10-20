#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Anketa and Generate Grant - E2E Pipeline
================================================
Импортирует готовые ответы на 15 вопросов анкеты и запускает полную цепочку агентов:
1. Загружает ответы в БД (anketas, sessions, interview_answers)
2. Auditor → скоринг (1-10)
3. Researcher V2 → 27 запросов для сбора данных
4. Writer V2 → создание заявки на грант
5. Reviewer → финальная оценка
6. Экспорт артефактов (research_results.json, grant.docx)

Usage:
    python import_anketa_and_generate_grant.py --input anketa.json
    python import_anketa_and_generate_grant.py --input anketa.txt --format text

Author: Grant Architect Agent
Date: 2025-10-10
"""
import sys
import os
from pathlib import Path
import json
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'agents'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'web-admin'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'data'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports
try:
    from utils.database import AdminDatabase
    from auditor_agent import AuditorAgent
    from researcher_agent_v2 import ResearcherAgentV2
    from writer_agent_v2 import WriterAgentV2
    from reviewer_agent import ReviewerAgent
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    sys.exit(1)


class AnketaImporter:
    """Импорт анкеты и запуск pipeline агентов"""

    def __init__(self, db_connection):
        self.db = db_connection
        self.anketa_id = None
        self.session_id = None

    def load_anketa_from_json(self, json_path: str) -> Dict[str, Any]:
        """Загрузить анкету из JSON файла"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"✅ Загружен JSON: {json_path}")
        return data

    def load_anketa_from_text(self, text_path: str) -> Dict[str, Any]:
        """Загрузить анкету из текстового файла (вопрос-ответ)"""
        with open(text_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        answers = {}
        current_q = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Определяем вопрос (начинается с числа и точки)
            if line[0].isdigit() and '.' in line[:3]:
                parts = line.split('.', 1)
                current_q = parts[0].strip()
                if len(parts) > 1:
                    answers[current_q] = parts[1].strip()
            elif current_q:
                # Продолжение ответа
                answers[current_q] = answers.get(current_q, '') + ' ' + line

        logger.info(f"✅ Загружен текст: {text_path}, вопросов: {len(answers)}")

        return {
            'telegram_id': 'imported_user',
            'answers': answers
        }

    def create_anketa_in_db(self, telegram_id: str, answers: Dict[str, str]) -> str:
        """Создать анкету в БД"""
        try:
            # 1. Создаем запись в anketas
            anketa_query = """
                INSERT INTO anketas (
                    telegram_id,
                    project_name,
                    description,
                    geography,
                    problem,
                    target_group,
                    goal,
                    tasks,
                    timeline,
                    risks,
                    team,
                    volunteers,
                    ano_info,
                    social_links,
                    grants_history,
                    grant_direction,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING anketa_id
            """

            result = self.db.execute_query(anketa_query, (
                telegram_id,
                answers.get('1', ''),  # project_name
                answers.get('2', ''),  # description
                answers.get('3', ''),  # geography
                answers.get('4', ''),  # problem
                answers.get('5', ''),  # target_group
                answers.get('6', ''),  # goal
                answers.get('7', ''),  # tasks
                answers.get('8', ''),  # timeline
                answers.get('9', ''),  # risks
                answers.get('10', ''), # team
                answers.get('11', ''), # volunteers
                answers.get('12', ''), # ano_info
                answers.get('13', ''), # social_links
                answers.get('14', ''), # grants_history
                answers.get('15', '1') # grant_direction (default 1)
            ))

            if not result:
                raise Exception("Не удалось создать анкету")

            anketa_id = result[0]['anketa_id']
            self.anketa_id = anketa_id

            logger.info(f"✅ Анкета создана: anketa_id={anketa_id}")

            # 2. Создаем session
            session_query = """
                INSERT INTO sessions (
                    telegram_id,
                    anketa_id,
                    completion_status,
                    started_at,
                    completed_at,
                    current_stage
                ) VALUES (
                    %s, %s, 'completed', NOW(), NOW(), 'auditor'
                )
                RETURNING id
            """

            session_result = self.db.execute_query(session_query, (telegram_id, anketa_id))
            if session_result:
                self.session_id = session_result[0]['id']
                logger.info(f"✅ Session создана: session_id={self.session_id}")

            # 3. Создаем interview_answers
            for q_num, answer in answers.items():
                if not q_num.isdigit():
                    continue

                answer_query = """
                    INSERT INTO interview_answers (
                        anketa_id, question_number, answer_text
                    ) VALUES (%s, %s, %s)
                    ON CONFLICT (anketa_id, question_number)
                    DO UPDATE SET answer_text = EXCLUDED.answer_text
                """
                self.db.execute_query(answer_query, (anketa_id, int(q_num), answer))

            logger.info(f"✅ Interview answers сохранены: {len(answers)} ответов")

            return anketa_id

        except Exception as e:
            logger.error(f"❌ Ошибка создания анкеты: {e}")
            raise

    async def run_pipeline(self, anketa_id: str) -> Dict[str, Any]:
        """Запустить полную цепочку агентов"""
        results = {
            'anketa_id': anketa_id,
            'auditor': None,
            'researcher': None,
            'writer': None,
            'reviewer': None,
            'artifacts': {}
        }

        try:
            # Загружаем данные анкеты
            anketa_data = self._load_anketa_data(anketa_id)

            logger.info("=" * 80)
            logger.info("🚀 ЗАПУСК PIPELINE АГЕНТОВ")
            logger.info("=" * 80)

            # ЭТАП 1: Auditor - Оценка проекта
            logger.info("\n📊 ЭТАП 1: Auditor - Оценка проекта")
            auditor = AuditorAgent(self.db, llm_provider="gigachat")

            auditor_input = {
                'user_answers': anketa_data,
                'anketa_id': anketa_id
            }

            auditor_result = await auditor.audit_async(auditor_input)
            results['auditor'] = auditor_result

            score = auditor_result.get('overall_score', 0)
            logger.info(f"✅ Auditor завершен: Оценка {score}/10")

            # ЭТАП 2: Researcher V2 - Сбор данных (27 запросов)
            logger.info("\n🔍 ЭТАП 2: Researcher V2 - Сбор данных (27 запросов)")
            researcher = ResearcherAgentV2(self.db, llm_provider="gigachat")

            researcher_input = {
                'user_answers': anketa_data,
                'anketa_id': anketa_id
            }

            researcher_result = await researcher.research_async(researcher_input)
            results['researcher'] = researcher_result

            if researcher_result.get('status') == 'success':
                logger.info(f"✅ Researcher завершен: {researcher_result.get('queries_executed', 0)} запросов")
            else:
                logger.warning(f"⚠️ Researcher завершен с предупреждениями")

            # ЭТАП 3: Writer V2 - Создание заявки
            logger.info("\n✍️ ЭТАП 3: Writer V2 - Создание заявки на грант")
            writer = WriterAgentV2(self.db, llm_provider="gigachat")

            writer_input = {
                'user_answers': anketa_data,
                'anketa_id': anketa_id,
                'selected_grant': {
                    'name': 'Президентские гранты',
                    'max_amount': 1000000
                },
                'research_results': researcher_result.get('research_results')
            }

            writer_result = await writer.write_application_async(writer_input)
            results['writer'] = writer_result

            if writer_result.get('status') == 'success':
                logger.info(f"✅ Writer завершен: Заявка создана")
            else:
                logger.warning(f"⚠️ Writer завершен с ошибками")

            # ЭТАП 4: Reviewer - Финальная оценка
            logger.info("\n🔎 ЭТАП 4: Reviewer - Финальная оценка готовности")
            reviewer = ReviewerAgent(self.db, llm_provider="gigachat")

            reviewer_input = {
                'grant_content': writer_result.get('application', {}),
                'research_results': researcher_result.get('research_results'),
                'user_answers': anketa_data,
                'citations': writer_result.get('citations', []),
                'tables': writer_result.get('tables', []),
                'selected_grant': writer_input['selected_grant']
            }

            reviewer_result = await reviewer.review_grant_async(reviewer_input)
            results['reviewer'] = reviewer_result

            if reviewer_result.get('status') == 'success':
                readiness = reviewer_result.get('readiness_score', 0)
                approval = reviewer_result.get('approval_probability', 0)
                logger.info(f"✅ Reviewer завершен: Готовность {readiness}/10, Вероятность одобрения {approval}%")

            logger.info("\n" + "=" * 80)
            logger.info("✅ PIPELINE ЗАВЕРШЕН УСПЕШНО!")
            logger.info("=" * 80)

            return results

        except Exception as e:
            logger.error(f"❌ Ошибка в pipeline: {e}")
            import traceback
            traceback.print_exc()
            return results

    def _load_anketa_data(self, anketa_id: str) -> Dict[str, Any]:
        """Загрузить данные анкеты из БД"""
        query = """
            SELECT * FROM anketas WHERE anketa_id = %s
        """
        result = self.db.execute_query(query, (anketa_id,))

        if not result:
            raise Exception(f"Анкета {anketa_id} не найдена")

        anketa = result[0]

        # Преобразуем в формат для агентов
        return {
            'project_name': anketa.get('project_name', ''),
            'description': anketa.get('description', ''),
            'geography': anketa.get('geography', ''),
            'problem': anketa.get('problem', ''),
            'target_group': anketa.get('target_group', ''),
            'goal': anketa.get('goal', ''),
            'tasks': anketa.get('tasks', ''),
            'timeline': anketa.get('timeline', ''),
            'risks': anketa.get('risks', ''),
            'team': anketa.get('team', ''),
            'volunteers': anketa.get('volunteers', ''),
            'ano_info': anketa.get('ano_info', ''),
            'social_links': anketa.get('social_links', ''),
            'grants_history': anketa.get('grants_history', ''),
            'grant_direction': anketa.get('grant_direction', '1')
        }

    def export_artifacts(self, results: Dict[str, Any], output_dir: str = 'grants_output'):
        """Экспортировать артефакты (research, grant)"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        anketa_id = results.get('anketa_id', 'unknown')

        try:
            # 1. Research results
            if results.get('researcher'):
                research_file = output_path / f'research_{anketa_id}_{timestamp}.json'
                with open(research_file, 'w', encoding='utf-8') as f:
                    json.dump(results['researcher'], f, ensure_ascii=False, indent=2)
                logger.info(f"✅ Research экспортирован: {research_file}")

            # 2. Grant application
            if results.get('writer'):
                grant_file = output_path / f'grant_{anketa_id}_{timestamp}.txt'
                grant_content = results['writer'].get('application', {})

                with open(grant_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("ЗАЯВКА НА ГРАНТ (СГЕНЕРИРОВАНА AI)\n")
                    f.write("=" * 80 + "\n\n")

                    if 'full_text' in grant_content:
                        f.write(grant_content['full_text'])
                    else:
                        for section, text in grant_content.items():
                            if isinstance(text, str):
                                f.write(f"\n## {section.upper()}\n")
                                f.write(text + "\n")

                logger.info(f"✅ Grant экспортирован: {grant_file}")

            # 3. Summary report
            summary_file = output_path / f'summary_{anketa_id}_{timestamp}.json'
            summary = {
                'anketa_id': anketa_id,
                'timestamp': timestamp,
                'auditor_score': results.get('auditor', {}).get('overall_score', 0),
                'researcher_queries': results.get('researcher', {}).get('queries_executed', 0),
                'writer_status': results.get('writer', {}).get('status', 'unknown'),
                'reviewer_readiness': results.get('reviewer', {}).get('readiness_score', 0),
                'reviewer_approval_probability': results.get('reviewer', {}).get('approval_probability', 0)
            }

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Summary экспортирован: {summary_file}")

            logger.info(f"\n📦 Все артефакты сохранены в: {output_path.absolute()}")

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта артефактов: {e}")


async def main(args):
    """Main function"""
    logger.info("=" * 80)
    logger.info("🚀 IMPORT ANKETA AND GENERATE GRANT - START")
    logger.info("=" * 80)

    # Initialize database
    try:
        db = AdminDatabase()
        logger.info("✅ Подключение к БД установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return

    # Create importer
    importer = AnketaImporter(db)

    # Load anketa
    if args.format == 'json':
        anketa_data = importer.load_anketa_from_json(args.input)
    elif args.format == 'text':
        anketa_data = importer.load_anketa_from_text(args.input)
    else:
        logger.error(f"❌ Неизвестный формат: {args.format}")
        return

    telegram_id = anketa_data.get('telegram_id', 'imported_user')
    answers = anketa_data.get('answers', {})

    logger.info(f"📝 Telegram ID: {telegram_id}")
    logger.info(f"📝 Ответов: {len(answers)}")

    # Create anketa in DB
    try:
        anketa_id = importer.create_anketa_in_db(telegram_id, answers)
    except Exception as e:
        logger.error(f"❌ Не удалось создать анкету: {e}")
        return

    # Run pipeline
    if not args.skip_pipeline:
        results = await importer.run_pipeline(anketa_id)

        # Export artifacts
        if not args.skip_export:
            importer.export_artifacts(results, args.output)
    else:
        logger.info("⏭️ Pipeline пропущен (--skip-pipeline)")

    logger.info("\n" + "=" * 80)
    logger.info("✅ IMPORT ANKETA AND GENERATE GRANT - COMPLETED")
    logger.info("=" * 80)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import anketa and generate grant')
    parser.add_argument('--input', required=True, help='Path to input file (JSON or TXT)')
    parser.add_argument('--format', choices=['json', 'text'], default='json', help='Input format')
    parser.add_argument('--output', default='grants_output', help='Output directory for artifacts')
    parser.add_argument('--skip-pipeline', action='store_true', help='Skip agent pipeline')
    parser.add_argument('--skip-export', action='store_true', help='Skip export artifacts')

    args = parser.parse_args()

    asyncio.run(main(args))
