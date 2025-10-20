#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditor Agent с интеграцией Claude Code API

Оценивает грантовые проекты по 10 критериям с использованием Claude Code
для более объективной и глубокой аналитики.
"""

import sys
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Добавляем путь к модулям
sys.path.append('/var/GrantService/data')
sys.path.append('/var/GrantService')

from agents.base_agent import BaseAgent
from shared.llm.llm_router import LLMRouter, TaskType
from agents.prompts.claude_code_prompts import (
    AUDITOR_EVALUATION_PROMPT,
    AUDITOR_QUICK_SCORE_PROMPT,
    create_evaluation_prompt
)


class AuditorAgentClaude(BaseAgent):
    """
    Агент-аудитор с использованием Claude Code API

    Оценивает проекты по 10 критериям:
    1. Актуальность
    2. Новизна
    3. Методология
    4. Бюджет
    5. Команда
    6. Результаты
    7. Риски
    8. Социальная значимость
    9. Масштабируемость
    10. Устойчивость
    """

    def __init__(self, db, llm_provider: str = "claude"):
        super().__init__(agent_type="auditor", db=db, llm_provider=llm_provider)
        self.router = None

    async def evaluate_project_async(
        self,
        project_data: Dict[str, Any],
        use_quick_score: bool = False
    ) -> Dict[str, Any]:
        """
        Асинхронная оценка проекта

        Args:
            project_data: Данные проекта для оценки
            use_quick_score: Использовать быструю оценку (True) или полную (False)

        Returns:
            Dict с результатами оценки
        """
        self.log_activity("evaluation_started", {
            "project_name": project_data.get("название", "Без названия"),
            "quick_score": use_quick_score
        })

        try:
            async with LLMRouter() as router:
                if use_quick_score:
                    # Быстрая оценка (1 запрос)
                    result = await self._quick_evaluation(router, project_data)
                else:
                    # Полная оценка по 10 критериям
                    result = await self._full_evaluation(router, project_data)

                self.log_activity("evaluation_completed", {
                    "score": result.get("total_score", 0),
                    "recommendation": result.get("recommendation", "")
                })

                return result

        except Exception as e:
            error_result = self.handle_error(e, "evaluate_project_async")
            return error_result

    async def _quick_evaluation(
        self,
        router: LLMRouter,
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Быстрая оценка проекта (1-100 баллов)"""

        project_description = self._format_project_description(project_data)

        prompt = AUDITOR_QUICK_SCORE_PROMPT.format(
            project_description=project_description
        )

        response = await router.generate(
            prompt=prompt,
            task_type=TaskType.EVALUATION,
            temperature=0.3,
            max_tokens=500
        )

        try:
            # Парсим JSON ответ
            result = json.loads(response)

            return {
                "evaluation_type": "quick",
                "score": result.get("score", 0),
                "category": result.get("category", "неизвестно"),
                "summary": result.get("one_line_summary", ""),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }

        except json.JSONDecodeError:
            # Если ответ не JSON, пытаемся извлечь оценку из текста
            return {
                "evaluation_type": "quick",
                "score": 0,
                "category": "ошибка парсинга",
                "summary": response[:200],
                "raw_response": response,
                "timestamp": datetime.now().isoformat(),
                "status": "partial_success"
            }

    async def _full_evaluation(
        self,
        router: LLMRouter,
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Полная оценка проекта по 10 критериям"""

        prompt = create_evaluation_prompt(project_data)

        response = await router.generate(
            prompt=prompt,
            task_type=TaskType.EVALUATION,
            temperature=0.3,
            max_tokens=3000
        )

        try:
            # Парсим JSON ответ
            result = json.loads(response)

            # Структурируем результат
            evaluation = {
                "evaluation_type": "full",
                "scores": result.get("scores", {}),
                "total_score": result.get("total_score", 0),
                "total_max": result.get("total_max", 100),
                "percentage": result.get("percentage", 0),
                "recommendation": result.get("recommendation", ""),
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
                "improvement_suggestions": result.get("improvement_suggestions", []),
                "final_verdict": result.get("final_verdict", ""),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }

            # Логируем детали
            self.log_activity("detailed_scores", {
                "scores": result.get("scores", {}),
                "total": result.get("total_score", 0)
            })

            return evaluation

        except json.JSONDecodeError:
            # Если ответ не JSON, возвращаем текстовый результат
            return {
                "evaluation_type": "full",
                "total_score": 0,
                "recommendation": "ошибка",
                "raw_response": response[:500],
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": "Не удалось распарсить JSON ответ"
            }

    def _format_project_description(self, project_data: Dict[str, Any]) -> str:
        """Форматирует данные проекта в читаемый текст"""

        parts = []

        if "название" in project_data:
            parts.append(f"Название: {project_data['название']}")

        if "описание" in project_data:
            parts.append(f"Описание: {project_data['описание']}")

        if "целевая_аудитория" in project_data:
            parts.append(f"Целевая аудитория: {project_data['целевая_аудитория']}")

        if "бюджет" in project_data:
            parts.append(f"Бюджет: {project_data['бюджет']:,} руб")

        if "команда" in project_data:
            parts.append(f"Команда: {project_data['команда']}")

        if "длительность" in project_data:
            parts.append(f"Длительность: {project_data['длительность']}")

        return "\n".join(parts)

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Синхронная обёртка для совместимости с BaseAgent

        Args:
            data: Данные проекта для оценки

        Returns:
            Результаты оценки
        """
        # Проверяем наличие event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Запускаем асинхронную оценку
        result = loop.run_until_complete(
            self.evaluate_project_async(
                project_data=data,
                use_quick_score=data.get("quick_score", False)
            )
        )

        return self.prepare_output(result)

    async def compare_with_successful_grants(
        self,
        project_data: Dict[str, Any],
        successful_grants: list
    ) -> Dict[str, Any]:
        """
        Сравнение проекта с успешными грантами

        Args:
            project_data: Данные проекта
            successful_grants: Список успешных грантов для сравнения

        Returns:
            Результаты сравнения
        """
        async with LLMRouter() as router:
            prompt = f"""
Сравни проект с успешными грантами и дай рекомендации.

Проект:
{json.dumps(project_data, ensure_ascii=False, indent=2)}

Успешные гранты:
{json.dumps(successful_grants, ensure_ascii=False, indent=2)}

Верни JSON:
{{
    "similarity_scores": [{{"grant": "...", "score": 85}}, ...],
    "common_success_factors": ["...", "..."],
    "differences": ["...", "..."],
    "recommendations": ["...", "..."]
}}
"""

            response = await router.generate(
                prompt=prompt,
                task_type=TaskType.ANALYSIS,
                temperature=0.3,
                max_tokens=2000
            )

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"error": "Не удалось распарсить ответ", "raw": response}

    async def generate_improvement_plan(
        self,
        evaluation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Генерация плана улучшения на основе оценки

        Args:
            evaluation_result: Результаты оценки проекта

        Returns:
            План улучшения
        """
        async with LLMRouter() as router:
            prompt = f"""
На основе оценки проекта создай детальный план улучшения.

Оценка:
{json.dumps(evaluation_result, ensure_ascii=False, indent=2)}

Верни JSON с планом:
{{
    "priority_actions": [
        {{
            "priority": "high",
            "action": "...",
            "expected_impact": "+15 баллов",
            "effort": "2-3 дня"
        }}
    ],
    "quick_wins": ["...", "..."],
    "long_term_improvements": ["...", "..."],
    "estimated_score_increase": "+25 баллов"
}}
"""

            response = await router.generate(
                prompt=prompt,
                task_type=TaskType.STRUCTURING,
                temperature=0.4,
                max_tokens=2000
            )

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"error": "Не удалось распарсить ответ", "raw": response}


# Пример использования
async def example_usage():
    """Пример использования Auditor Agent с Claude Code"""

    # Тестовые данные проекта
    project_data = {
        "название": "Молодёжный IT-центр 'Код будущего'",
        "описание": "Создание образовательного центра для обучения молодёжи программированию в малых городах Поволжья",
        "целевая_аудитория": "Молодёжь 14-25 лет из малых городов",
        "география": "Самарская область, 5 малых городов",
        "бюджет": 1500000,
        "команда": "3 опытных программиста, 2 методиста, 1 координатор",
        "длительность": "12 месяцев",
        "планируемые_результаты": "Обучение 200+ человек, 80% трудоустройство",
        "партнёры": "Местные администрации, IT-компании региона"
    }

    # Создаём агента (без реальной БД для примера)
    agent = AuditorAgentClaude(db=None, llm_provider="claude")

    print("🔍 ПРИМЕР 1: Быстрая оценка")
    print("="*70)

    quick_result = await agent.evaluate_project_async(
        project_data=project_data,
        use_quick_score=True
    )

    print(f"Оценка: {quick_result.get('score', 0)}/100")
    print(f"Категория: {quick_result.get('category', '')}")
    print(f"Резюме: {quick_result.get('summary', '')}")

    print("\n🔬 ПРИМЕР 2: Полная оценка по 10 критериям")
    print("="*70)

    full_result = await agent.evaluate_project_async(
        project_data=project_data,
        use_quick_score=False
    )

    print(f"Общий балл: {full_result.get('total_score', 0)}/{full_result.get('total_max', 100)}")
    print(f"Рекомендация: {full_result.get('recommendation', '')}")

    if 'strengths' in full_result:
        print(f"\nСильные стороны:")
        for strength in full_result['strengths'][:3]:
            print(f"  ✅ {strength}")

    if 'weaknesses' in full_result:
        print(f"\nСлабые стороны:")
        for weakness in full_result['weaknesses'][:3]:
            print(f"  ⚠️ {weakness}")

    if 'improvement_suggestions' in full_result:
        print(f"\nРекомендации по улучшению:")
        for suggestion in full_result['improvement_suggestions'][:3]:
            print(f"  💡 [{suggestion.get('priority', 'medium')}] {suggestion.get('suggestion', '')}")

    print("\n🎯 ПРИМЕР 3: План улучшения")
    print("="*70)

    improvement_plan = await agent.generate_improvement_plan(full_result)

    if 'priority_actions' in improvement_plan:
        print("Приоритетные действия:")
        for action in improvement_plan['priority_actions'][:3]:
            print(f"  [{action.get('priority', 'medium')}] {action.get('action', '')}")
            print(f"     Эффект: {action.get('expected_impact', '')}, Усилия: {action.get('effort', '')}")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_usage())
