#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Engineer Agent - MVP Version
Autonomous E2E test runner для GrantService
"""

import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import production E2E modules
from tests.e2e.modules.interviewer_module import InterviewerModule
from tests.e2e.modules.auditor_module import AuditorModule
from tests.e2e.modules.researcher_module import ResearcherModule
from tests.e2e.modules.writer_module import WriterModule
from tests.e2e.modules.reviewer_module import ReviewerModule


class TestEngineerAgent:
    """
    MVP Test Engineer Agent

    Запускает E2E тесты на production DB и проверяет все фиксы
    """

    def __init__(self, artifacts_dir: str = None):
        """
        Initialize agent

        Args:
            artifacts_dir: Path to save artifacts (default: iterations/Iteration_66_E2E_Test_Suite/artifacts)
        """
        if artifacts_dir is None:
            artifacts_dir = project_root / "iterations" / "Iteration_66_E2E_Test_Suite" / "artifacts"

        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        print(f"Test Engineer Agent initialized")
        print(f"Artifacts dir: {self.artifacts_dir}")

        # Initialize E2E modules (they connect to PRODUCTION DB!)
        self.interviewer = InterviewerModule()
        self.auditor = AuditorModule()
        self.researcher = ResearcherModule()
        self.writer = WriterModule()
        self.reviewer = ReviewerModule()

    def run_e2e_test(self, use_mock_websearch: bool = True) -> Dict:
        """
        Run full E2E test

        Args:
            use_mock_websearch: True to avoid ERROR #16 (WebSearch timeout)

        Returns:
            Test results dict
        """

        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("\n" + "="*80)
        print(f"🤖 TEST ENGINEER AGENT - E2E TEST RUN")
        print("="*80)
        print(f"Test ID: {test_id}")
        print(f"Mock WebSearch: {use_mock_websearch}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        results = {
            "test_id": test_id,
            "timestamp": datetime.now().isoformat(),
            "mock_websearch": use_mock_websearch,
            "steps": {},
            "validations": {},
            "errors": []
        }

        try:
            # STEP 1: Interview
            print(f"\n{'─'*80}")
            print(f"[STEP 1/5] Interview - InteractiveInterviewerAgent")
            print(f"{'─'*80}")

            start = time.time()

            # Use test user from production DB range
            test_user_id = 999999001  # First test user

            # Simple test answers (embedded in code for MVP)
            test_answers = self._generate_simple_test_answers()

            interview_result = self.interviewer.run_interview(
                test_user_id=test_user_id,
                user_answers=test_answers
            )

            duration = time.time() - start

            results["steps"]["interview"] = {
                "status": "success",
                "anketa_id": interview_result["anketa_id"],
                "questions_count": interview_result["questions_count"],
                "anketa_length": interview_result["anketa_length"],
                "duration_sec": round(duration, 2)
            }

            print(f"✅ Interview complete:")
            print(f"   - Anketa ID: {interview_result['anketa_id']}")
            print(f"   - Questions: {interview_result['questions_count']}")
            print(f"   - Length: {interview_result['anketa_length']} chars")
            print(f"   - Duration: {duration:.1f}s")

            anketa_id = interview_result["anketa_id"]

            # STEP 2: Audit
            print(f"\n{'─'*80}")
            print(f"[STEP 2/5] Audit - AuditorAgent")
            print(f"{'─'*80}")

            start = time.time()

            audit_result = self.auditor.run_audit(anketa_id)

            duration = time.time() - start

            results["steps"]["audit"] = {
                "status": "success",
                "session_id": audit_result["session_id"],
                "score": audit_result["score"],
                "duration_sec": round(duration, 2)
            }

            print(f"✅ Audit complete:")
            print(f"   - Session ID: {audit_result['session_id']}")
            print(f"   - Score: {audit_result['score']}/10")
            print(f"   - Duration: {duration:.1f}s")

            # STEP 3: Research
            print(f"\n{'─'*80}")
            print(f"[STEP 3/5] Research - ResearcherAgentV2")
            print(f"{'─'*80}")

            start = time.time()

            research_result = self.researcher.run_research(
                anketa_id,
                use_mock_websearch=use_mock_websearch
            )

            duration = time.time() - start

            results["steps"]["research"] = {
                "status": "success",
                "research_id": research_result["research_id"],
                "sources_count": research_result["sources_count"],
                "duration_sec": round(duration, 2)
            }

            print(f"✅ Research complete:")
            print(f"   - Research ID: {research_result['research_id']}")
            print(f"   - Sources: {research_result['sources_count']}")
            print(f"   - Duration: {duration:.1f}s")

            # STEP 4: Writer (FIX #15 validation!)
            print(f"\n{'─'*80}")
            print(f"[STEP 4/5] Writer - WriterAgentV2 (FIX #15 CHECK!)")
            print(f"{'─'*80}")

            start = time.time()

            writer_result = self.writer.run_writer(
                anketa_id,
                research_id=research_result["research_id"]
            )

            duration = time.time() - start

            results["steps"]["writer"] = {
                "status": "success",
                "grant_id": writer_result["grant_id"],
                "grant_length": writer_result["grant_length"],
                "duration_sec": round(duration, 2)
            }

            print(f"✅ Writer complete:")
            print(f"   - Grant ID: {writer_result['grant_id']}")
            print(f"   - Length: {writer_result['grant_length']} chars")
            print(f"   - Duration: {duration:.1f}s")

            # FIX #15 Validation
            print(f"\n{'─'*40}")
            print(f"🔍 FIX #15 VALIDATION")
            print(f"{'─'*40}")

            grant_length = writer_result["grant_length"]

            if grant_length >= 15000:
                print(f"✅ FIX #15 VERIFIED: grant_length = {grant_length} >= 15000")
                results["validations"]["fix_15"] = {
                    "status": "passed",
                    "grant_length": grant_length,
                    "threshold": 15000,
                    "message": "WriterModule correctly extracts full_text from application_content"
                }
            else:
                print(f"❌ FIX #15 FAILED: grant_length = {grant_length} < 15000")
                results["validations"]["fix_15"] = {
                    "status": "failed",
                    "grant_length": grant_length,
                    "threshold": 15000,
                    "message": "WriterModule still returning dict length instead of text length"
                }
                raise AssertionError(f"FIX #15 validation failed: {grant_length} < 15000")

            # STEP 5: Review
            print(f"\n{'─'*80}")
            print(f"[STEP 5/5] Review - ReviewerAgent")
            print(f"{'─'*80}")

            start = time.time()

            review_result = self.reviewer.run_review(writer_result["grant_id"])

            duration = time.time() - start

            results["steps"]["review"] = {
                "status": "success",
                "review_score": review_result["review_score"],
                "duration_sec": round(duration, 2)
            }

            print(f"✅ Review complete:")
            print(f"   - Score: {review_result['review_score']}/10")
            print(f"   - Duration: {duration:.1f}s")

            # Save artifacts
            self._save_artifacts(test_id, results)

            # Final report
            print(f"\n{'='*80}")
            print(f"✅ E2E TEST PASSED: {test_id}")
            print(f"{'='*80}")
            print(f"Summary:")
            print(f"  - All 5 steps: SUCCESS")
            print(f"  - FIX #15: VERIFIED ✅")
            print(f"  - Artifacts saved: {self.artifacts_dir / f'run_{test_id}'}")
            print("="*80)

            return results

        except Exception as e:
            error_msg = str(e)
            print(f"\n{'='*80}")
            print(f"❌ E2E TEST FAILED: {error_msg}")
            print(f"{'='*80}")

            results["errors"].append({
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            })

            self._save_artifacts(test_id, results)

            raise

    def _generate_simple_test_answers(self) -> Dict[str, str]:
        """
        Generate simple test answers (embedded for MVP)

        В Phase 2 заменим на GigaChat User Simulator
        """
        return {
            "answer_1": """
Наша организация "Точка роста" - это образовательная НКО, работающая с подростками
из малообеспеченных семей. Мы помогаем им получить дополнительное образование в
сфере IT и дизайна, чтобы они могли построить успешную карьеру.
            """.strip(),

            "answer_2": """
Мы решаем проблему неравного доступа к качественному IT-образованию. Многие талантливые
подростки из небольших городов не могут позволить себе платные курсы по программированию,
веб-дизайну и другим востребованным профессиям.
            """.strip(),

            "answer_3": """
Наша целевая аудитория - подростки 14-18 лет из семей с низким доходом, проживающие
в городах с населением до 100 тысяч человек. Основной фокус - молодые люди, которые
проявляют интерес к технологиям, но не имеют возможности получить профессиональное обучение.
            """.strip(),

            "answer_4": """
Мы используем онлайн-обучение через собственную платформу, где студенты изучают Python,
веб-разработку и графический дизайн. Каждому ученику назначается ментор - практикующий
специалист из IT-компаний. Также проводим хакатоны и помогаем с трудоустройством.
            """.strip(),

            "answer_5": """
За два года работы мы обучили 150 подростков, из них 45 человек уже нашли работу или
стажировку в IT-компаниях. Средняя зарплата выпускников составляет 40 000 рублей, что
в 2 раза выше среднего дохода их семей.
            """.strip(),

            "answer_6": """
Бюджет проекта на год составляет 2 500 000 рублей. Основные статьи расходов:
- Зарплата преподавателей и кураторов: 1 200 000 руб
- Техническое обеспечение (ноутбуки для учеников): 800 000 руб
- Разработка и поддержка обучающей платформы: 300 000 руб
- Административные расходы: 200 000 руб
            """.strip(),

            "answer_7": """
Команда проекта состоит из 8 человек:
- Руководитель проекта (опыт в НКО - 5 лет)
- 3 преподавателя IT-дисциплин (практикующие разработчики)
- 2 карьерных консультанта
- 1 SMM-менеджер
- 1 бухгалтер
Все сотрудники работают на постоянной основе.
            """.strip(),

            "answer_8": """
У нас есть партнерство с 5 IT-компаниями региона, которые предоставляют менторов и
стажировки для выпускников. Также сотрудничаем с местной администрацией - они
выделили нам помещение для офлайн-занятий бесплатно.
            """.strip(),

            "answer_9": """
Измеримые показатели успеха:
- Количество обученных студентов: 100 человек в год
- Доля завершивших программу: не менее 80%
- Доля трудоустроенных в течение 6 месяцев: не менее 30%
- Средняя оценка качества обучения от студентов: не менее 4.5/5
            """.strip(),

            "answer_10": """
Долгосрочное влияние проекта - создание устойчивой экосистемы IT-образования в регионе.
Мы планируем масштабировать проект на 10 городов за 3 года и обучить более 1000 подростков.
Это поможет снизить уровень безработицы среди молодежи и привлечь IT-компании в регионы.
            """.strip()
        }

    def _save_artifacts(self, test_id: str, results: Dict):
        """Save test artifacts"""

        run_dir = self.artifacts_dir / f"run_{test_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save results.json
        results_file = run_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Save markdown report
        report_file = run_dir / "REPORT.md"
        self._generate_markdown_report(report_file, results)

        print(f"\n📁 Artifacts saved:")
        print(f"   - {results_file}")
        print(f"   - {report_file}")

    def _generate_markdown_report(self, report_file: Path, results: Dict):
        """Generate markdown report"""

        report = f"""# Test Engineer Agent - E2E Test Report

**Test ID:** {results['test_id']}
**Timestamp:** {results['timestamp']}
**Mock WebSearch:** {results['mock_websearch']}

---

## 📊 Summary

| Step | Status | Duration |
|------|--------|----------|
"""

        # Add step results
        for step_name, step_data in results["steps"].items():
            status_emoji = "✅" if step_data["status"] == "success" else "❌"
            report += f"| {step_name.title()} | {status_emoji} {step_data['status']} | {step_data['duration_sec']}s |\n"

        report += "\n---\n\n## 🔍 Validations\n\n"

        # Add validations
        if results["validations"]:
            for validation_name, validation_data in results["validations"].items():
                status_emoji = "✅" if validation_data["status"] == "passed" else "❌"
                report += f"### {validation_name.upper()}\n\n"
                report += f"**Status:** {status_emoji} {validation_data['status'].upper()}\n\n"
                report += f"**Message:** {validation_data['message']}\n\n"

                if "grant_length" in validation_data:
                    report += f"**Grant Length:** {validation_data['grant_length']} chars\n"
                    report += f"**Threshold:** {validation_data['threshold']} chars\n\n"

        # Add errors if any
        if results["errors"]:
            report += "\n---\n\n## ❌ Errors\n\n"
            for error in results["errors"]:
                report += f"- **{error['timestamp']}:** {error['message']}\n"

        report += "\n---\n\n## 🎯 Conclusion\n\n"

        if not results["errors"] and results["validations"].get("fix_15", {}).get("status") == "passed":
            report += "✅ **E2E TEST PASSED**\n\n"
            report += "All 5 steps completed successfully. FIX #15 verified - WriterModule correctly extracts full_text.\n"
        else:
            report += "❌ **E2E TEST FAILED**\n\n"
            report += "Test encountered errors. Review error details above.\n"

        report += f"\n---\n\n**Generated by:** Test Engineer Agent (MVP)\n"
        test_id = results['test_id']
        run_dir = self.artifacts_dir / f'run_{test_id}'
        report += f"**Artifacts:** `{run_dir}`\n"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)


def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description="Test Engineer Agent - Autonomous E2E tester"
    )

    parser.add_argument(
        "--mock-websearch",
        action="store_true",
        default=True,
        help="Use mock WebSearch to avoid ERROR #16 (default: True)"
    )

    parser.add_argument(
        "--real-websearch",
        action="store_true",
        help="Use real WebSearch (may timeout with ERROR #16)"
    )

    parser.add_argument(
        "--artifacts-dir",
        type=str,
        help="Custom artifacts directory"
    )

    args = parser.parse_args()

    # Determine websearch mode
    use_mock_websearch = not args.real_websearch

    # Initialize agent
    agent = TestEngineerAgent(artifacts_dir=args.artifacts_dir)

    # Run E2E test
    try:
        results = agent.run_e2e_test(use_mock_websearch=use_mock_websearch)

        # Exit with success
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test Engineer Agent failed: {e}")
        import traceback
        traceback.print_exc()

        # Exit with error
        sys.exit(1)


if __name__ == "__main__":
    main()
