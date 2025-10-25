#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive Interviewer with Question Bank
Адаптивный интервьюер с банком вопросов

Философия: LLM выбирает ПОРЯДОК вопросов на основе ответов,
а не генерирует вопросы с нуля.

Version: 1.0 (Dev/Local)
Date: 2025-10-22
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdaptiveInterviewerWithQuestionBank:
    """
    Адаптивный интервьюер с банком из 10 фиксированных вопросов.
    LLM выбирает какой вопрос задать следующим на основе предыдущих ответов.
    """

    # Банк вопросов (фиксированный)
    QUESTION_BANK = {
        "Q1": {
            "text": "Как называется ваш проект?",
            "priority": "P0",  # Критичный
            "category": "basic"
        },
        "Q2": {
            "text": "Какую проблему решает ваш проект?",
            "priority": "P0",
            "category": "basic"
        },
        "Q3": {
            "text": "Кто ваша целевая аудитория? (возраст, количество, регион)",
            "priority": "P0",
            "category": "basic"
        },
        "Q4": {
            "text": "Какова цель проекта? (конкретная, измеримая)",
            "priority": "P0",
            "category": "basic"
        },
        "Q5": {
            "text": "Какие задачи нужно выполнить для достижения цели?",
            "priority": "P1",
            "category": "methodology"
        },
        "Q6": {
            "text": "Какой бюджет вам нужен? Расшифруйте основные статьи расходов.",
            "priority": "P1",
            "category": "budget"
        },
        "Q7": {
            "text": "Какие результаты вы планируете достичь? (с цифрами)",
            "priority": "P1",
            "category": "results"
        },
        "Q8": {
            "text": "Кто в команде проекта? Какой у них опыт?",
            "priority": "P2",
            "category": "team"
        },
        "Q9": {
            "text": "Есть ли партнёры? Кто они и как помогут?",
            "priority": "P2",
            "category": "partners"
        },
        "Q10": {
            "text": "Как проект будет работать после окончания гранта?",
            "priority": "P2",
            "category": "sustainability"
        }
    }

    def __init__(self, llm_client=None, llm_provider="claude_code"):
        """
        Args:
            llm_client: Клиент для LLM (UnifiedLLMClient или mock для тестов)
            llm_provider: Провайдер LLM (по умолчанию "claude_code")
                         ВАЖНО: Claude Code - основной и единственный провайдер!
                         GigaChat - только мануальный выбор, НЕ fallback!
        """
        self.llm_client = llm_client
        self.llm_provider = llm_provider
        self.conversation_history = []
        self.asked_questions = []
        self.skipped_questions = []  # Вопросы, которые косвенно раскрыты
        self.clarification_count = {}  # Счетчик уточнений по каждому вопросу

        logger.info(f"🤖 Adaptive Interviewer initialized with LLM provider: {llm_provider}")

    def _get_base_prompt(self) -> str:
        """Базовый промпт для LLM"""
        return """Ты - опытный консультант по грантовым заявкам Фонда президентских грантов (ФПГ).

ТВОЯ ЗАДАЧА: Провести интервью с заявителем, задавая вопросы в УМНОЙ ПОСЛЕДОВАТЕЛЬНОСТИ на основе ответов.

---

БАНК ВОПРОСОВ (10 вопросов):

{question_bank}

---

ПРАВИЛА ВЫБОРА СЛЕДУЮЩЕГО ВОПРОСА:

1. ВСЕГДА начинаем с [Q1] (название проекта)

2. После каждого ответа АНАЛИЗИРУЙ:
   - Насколько полон ответ? (1-10 баллов)
   - Какая информация КРИТИЧЕСКИ важна следующей?
   - Какие вопросы уже косвенно раскрыты в ответе?

3. ВЫБИРАЙ следующий вопрос по логике:
   - Если ответ слабый (качество < 6/10) → задай уточняющий вопрос (НЕ из банка, твой собственный)
   - Если ответ сильный (качество ≥ 6/10) → переходи к следующему по приоритету

4. ПРИОРИТЕТЫ вопросов:
   - P0 (критичные): ОБЯЗАТЕЛЬНЫ (Q1, Q2, Q3, Q4)
   - P1 (важные): Желательны (Q5, Q6, Q7)
   - P2 (опциональные): Если есть время (Q8, Q9, Q10)

5. АДАПТИВНОСТЬ:
   - Если в ответе человек УЖЕ раскрыл информацию из другого вопроса → ПРОПУСТИ тот вопрос
   - Пример: В Q2 (проблема) упомянул аудиторию → можно ПРОПУСТИТЬ Q3
   - Если ответ поверхностный → задай уточняющий ПЕРЕД переходом

6. ЛИМИТЫ:
   - Максимум 2 уточняющих вопроса на один базовый вопрос
   - Если уже задали все P0 + P1 вопросы → можно завершать

---

ФОРМАТ ОТВЕТА (строго JSON):

{{
  "analysis": {{
    "answer_quality": 7,
    "completeness": 0.8,
    "missing_info": ["масштаб проблемы"],
    "covered_questions": ["Q3"]
  }},
  "next_action": "ask_from_bank",
  "next_question": {{
    "id": "Q4",
    "text": "Какова цель проекта?",
    "reason": "Нужна конкретная измеримая цель"
  }},
  "should_finish": false
}}

---

ИСТОРИЯ ДИАЛОГА:
{conversation_history}

---

ТЕКУЩАЯ СИТУАЦИЯ:
- Последний вопрос: {last_question}
- Ответ пользователя: {user_answer}
- Уже заданные вопросы: {asked_questions}
- Пропущенные (раскрыты косвенно): {skipped_questions}
- Оставшиеся вопросы: {remaining_questions}

---

Проанализируй ответ и выбери следующий вопрос. Ответь в JSON формате.
"""

    def _format_question_bank(self) -> str:
        """Форматирует банк вопросов для промпта"""
        lines = []
        for qid, data in self.QUESTION_BANK.items():
            lines.append(f"[{qid}] {data['text']} (приоритет: {data['priority']})")
        return "\n".join(lines)

    def _get_remaining_questions(self) -> List[str]:
        """Возвращает список оставшихся вопросов"""
        all_questions = set(self.QUESTION_BANK.keys())
        asked = set(self.asked_questions)
        skipped = set(self.skipped_questions)
        return list(all_questions - asked - skipped)

    async def ask_next_question(self, user_answer: Optional[str] = None) -> Dict[str, Any]:
        """
        Задать следующий вопрос на основе ответа пользователя

        Args:
            user_answer: Ответ пользователя на предыдущий вопрос (None для первого вопроса)

        Returns:
            {
                'question_id': 'Q1',
                'question_text': '...',
                'is_clarifying': False,
                'should_finish': False,
                'analysis': {...}
            }
        """

        # Первый вопрос - всегда Q1 (hardcoded)
        if len(self.conversation_history) == 0:
            logger.info("🎯 Первый вопрос: Q1 (название проекта)")
            self.asked_questions.append("Q1")

            # Добавляем Q1 в историю сразу (ответ будет добавлен при следующем вызове)
            self.conversation_history.append({
                'question_id': 'Q1',
                'question_text': self.QUESTION_BANK['Q1']['text'],
                'is_clarifying': False
            })

            return {
                'question_id': 'Q1',
                'question_text': self.QUESTION_BANK['Q1']['text'],
                'is_clarifying': False,
                'should_finish': False,
                'analysis': None
            }

        # Сохраняем ответ в историю (обновляем последнюю запись)
        if self.conversation_history:
            # Обновляем последний вопрос, добавляя ответ
            self.conversation_history[-1]['answer'] = user_answer
            self.conversation_history[-1]['timestamp'] = datetime.now().isoformat()
            last_question = self.conversation_history[-1]['question_id']
        else:
            # Не должно происходить, но на всякий случай
            last_question = "Q1"

        # Формируем промпт для LLM
        prompt = self._get_base_prompt().format(
            question_bank=self._format_question_bank(),
            conversation_history=json.dumps(self.conversation_history, ensure_ascii=False, indent=2),
            last_question=last_question,
            user_answer=user_answer,
            asked_questions=json.dumps(self.asked_questions),
            skipped_questions=json.dumps(self.skipped_questions),
            remaining_questions=json.dumps(self._get_remaining_questions())
        )

        # Получаем решение от LLM
        if self.llm_client:
            llm_response = await self._call_llm(prompt)
        else:
            # Mock для тестирования без LLM
            llm_response = self._mock_llm_response(user_answer)

        # Парсим ответ LLM
        try:
            decision = json.loads(llm_response)
        except json.JSONDecodeError:
            logger.error(f"❌ LLM вернул некорректный JSON: {llm_response}")
            # Fallback: берем следующий по порядку
            decision = self._fallback_next_question()

        # Обрабатываем решение
        if decision.get('should_finish', False):
            logger.info("✅ Интервью завершено (все критичные вопросы заданы)")
            return {
                'question_id': None,
                'question_text': None,
                'is_clarifying': False,
                'should_finish': True,
                'analysis': decision.get('analysis')
            }

        # Обновляем skipped_questions
        covered = decision.get('analysis', {}).get('covered_questions', [])
        for q in covered:
            if q not in self.skipped_questions and q not in self.asked_questions:
                self.skipped_questions.append(q)
                logger.info(f"⏭️ Пропускаем {q} (уже раскрыт в ответе)")

        # Определяем следующий вопрос
        if decision['next_action'] == 'ask_clarifying':
            # Уточняющий вопрос (не из банка)
            clarifying_q = decision.get('clarifying_question', {})

            # Проверяем лимит уточнений
            clarification_key = last_question
            self.clarification_count[clarification_key] = self.clarification_count.get(clarification_key, 0) + 1

            if self.clarification_count[clarification_key] > 2:
                logger.warning(f"⚠️ Превышен лимит уточнений для {last_question}, переходим дальше")
                decision = self._fallback_next_question()
                next_q_id = decision['next_question']['id']
                next_q_text = self.QUESTION_BANK[next_q_id]['text']
                is_clarifying = False
            else:
                next_q_id = f"{last_question}_clarify_{self.clarification_count[clarification_key]}"
                next_q_text = clarifying_q.get('text', 'Уточните пожалуйста...')
                is_clarifying = True
        else:
            # Вопрос из банка
            next_q_id = decision['next_question']['id']
            next_q_text = self.QUESTION_BANK[next_q_id]['text']
            is_clarifying = False

            if next_q_id not in self.asked_questions:
                self.asked_questions.append(next_q_id)

        # Сохраняем в историю (для следующей итерации)
        self.conversation_history.append({
            'question_id': next_q_id,
            'question_text': next_q_text,
            'is_clarifying': is_clarifying
        })

        logger.info(f"❓ Следующий вопрос: {next_q_id} {'(уточнение)' if is_clarifying else ''}")

        return {
            'question_id': next_q_id,
            'question_text': next_q_text,
            'is_clarifying': is_clarifying,
            'should_finish': False,
            'analysis': decision.get('analysis')
        }

    async def _call_llm(self, prompt: str) -> str:
        """Вызов LLM (UnifiedLLMClient или другой)"""
        # TODO: Интеграция с UnifiedLLMClient
        response = await self.llm_client.generate_async(
            prompt=prompt,
            temperature=0.3,
            max_tokens=800
        )
        return response.get('content', '{}')

    def _mock_llm_response(self, user_answer: str) -> str:
        """Mock LLM для тестирования без реального LLM"""
        # Простая логика: если ответ короткий (<20 символов) → уточнение
        remaining = self._get_remaining_questions()

        if len(user_answer or '') < 20:
            # Короткий ответ → уточнение
            return json.dumps({
                "analysis": {
                    "answer_quality": 4,
                    "completeness": 0.3,
                    "missing_info": ["детали"],
                    "covered_questions": []
                },
                "next_action": "ask_clarifying",
                "clarifying_question": {
                    "text": "Ваш ответ слишком краток. Расскажите подробнее.",
                    "after_clarification_go_to": remaining[0] if remaining else "Q10"
                },
                "should_finish": False
            })
        else:
            # Нормальный ответ → следующий вопрос из банка
            if not remaining:
                return json.dumps({
                    "analysis": {
                        "answer_quality": 8,
                        "completeness": 0.9,
                        "missing_info": [],
                        "covered_questions": []
                    },
                    "next_action": "finish",
                    "should_finish": True
                })

            next_q = remaining[0]
            return json.dumps({
                "analysis": {
                    "answer_quality": 7,
                    "completeness": 0.7,
                    "missing_info": [],
                    "covered_questions": []
                },
                "next_action": "ask_from_bank",
                "next_question": {
                    "id": next_q,
                    "text": self.QUESTION_BANK[next_q]['text'],
                    "reason": f"Переходим к {next_q}"
                },
                "should_finish": False
            })

    def _fallback_next_question(self) -> Dict[str, Any]:
        """Fallback: выбрать следующий вопрос по приоритету"""
        remaining = self._get_remaining_questions()

        # Сортируем по приоритету
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
        remaining_sorted = sorted(
            remaining,
            key=lambda q: (priority_order[self.QUESTION_BANK[q]['priority']], q)
        )

        if remaining_sorted:
            next_q = remaining_sorted[0]
            return {
                "next_action": "ask_from_bank",
                "next_question": {
                    "id": next_q,
                    "text": self.QUESTION_BANK[next_q]['text'],
                    "reason": "Fallback - следующий по приоритету"
                },
                "should_finish": False
            }
        else:
            return {
                "next_action": "finish",
                "should_finish": True
            }

    def get_anketa(self) -> Dict[str, Any]:
        """
        Получить заполненную анкету из истории диалога

        Returns:
            {
                'project_name': '...',
                'problem_statement': '...',
                ...
            }
        """
        anketa = {}

        # Маппинг вопросов на поля анкеты
        mapping = {
            'Q1': 'project_name',
            'Q2': 'problem_statement',
            'Q3': 'target_audience',
            'Q4': 'project_goal',
            'Q5': 'project_tasks',
            'Q6': 'budget',
            'Q7': 'expected_results',
            'Q8': 'team_description',
            'Q9': 'partners',
            'Q10': 'sustainability'
        }

        for entry in self.conversation_history:
            if 'answer' in entry:
                q_id = entry['question_id']
                if q_id in mapping:
                    anketa[mapping[q_id]] = entry['answer']

        return anketa


# ============================================================================
# ДЕМО / ТЕСТ
# ============================================================================

async def demo_adaptive_interview():
    """Демонстрация работы адаптивного интервьюера"""

    print("=" * 80)
    print("DEMO: Adaptive Interviewer with Question Bank (Claude Code)")
    print("=" * 80)

    # ВАЖНО: Claude Code - основной провайдер, НЕ GigaChat!
    interviewer = AdaptiveInterviewerWithQuestionBank(
        llm_client=None,  # Mock режим для демо
        llm_provider="claude_code"
    )

    # Тестовые ответы
    test_answers = [
        "Лучные клубы Кемерово",  # Q1
        "В Кемерово нет доступа к стрельбе из лука для молодёжи 14-25 лет",  # Q2
        "500+ молодых людей, открыть 3 клуба, работать 2 года",  # Q4 (Q3 пропустится)
        "Задачи: найти помещения, купить оборудование, набрать тренеров",  # Q5
        "800 тысяч рублей: 300к на оборудование, 200к на аренду, 300к на зарплаты",  # Q6
        "Результаты: 500 участников, 3 клуба, 20 мероприятий в год",  # Q7
        "Команда: я руководитель, 3 тренера с опытом 5+ лет",  # Q8
        "Партнёры: городская администрация, школы",  # Q9
        "После гранта будем работать на членские взносы 1000р/мес"  # Q10
    ]

    answer_idx = 0

    # Первый вопрос
    result = await interviewer.ask_next_question()
    print(f"\n[{result['question_id']}] {result['question_text']}")

    # Цикл интервью
    while not result['should_finish'] and answer_idx < len(test_answers):
        user_answer = test_answers[answer_idx]
        print(f"USER: {user_answer}")

        answer_idx += 1

        result = await interviewer.ask_next_question(user_answer)

        if result['analysis']:
            print(f"ANALYSIS: quality {result['analysis']['answer_quality']}/10, "
                  f"completeness {result['analysis']['completeness']}")

        if not result['should_finish']:
            clarify = " (CLARIFYING)" if result.get('is_clarifying') else ""
            print(f"\n[{result['question_id']}] {result['question_text']}{clarify}")

    print("\n" + "=" * 80)
    print("INTERVIEW COMPLETED")
    print("=" * 80)

    anketa = interviewer.get_anketa()
    print("\nFINAL ANKETA:")
    print(json.dumps(anketa, ensure_ascii=False, indent=2))

    print(f"\nSTATISTICS:")
    print(f"   - Asked questions: {len(interviewer.asked_questions)}")
    print(f"   - Skipped questions: {len(interviewer.skipped_questions)}")
    print(f"   - Total in bank: {len(interviewer.QUESTION_BANK)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_adaptive_interview())
