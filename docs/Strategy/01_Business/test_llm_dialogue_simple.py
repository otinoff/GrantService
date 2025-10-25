#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified REAL LLM Dialogue Test
=================================

Прямой вызов LLM для тестирования реакции на нелогичные ответы.
Сохраняет полный диалог в JSON файл для анализа.

Без сложных зависимостей - просто LLM + dialogue recording.

Author: Grant Service Testing Team
Created: 2025-10-23
Version: 1.0 (Simplified)
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import time

# Setup path для LLM client
_grant_service = Path("C:/SnowWhiteAI/GrantService")
sys.path.insert(0, str(_grant_service))
sys.path.insert(0, str(_grant_service / "shared"))

try:
    from llm.unified_llm_client import UnifiedLLMClient
    LLM_AVAILABLE = True
except:
    print("⚠️ UnifiedLLMClient недоступен, используем mock LLM")
    LLM_AVAILABLE = False


# =============================================================================
# LLM Interviewer Simulator
# =============================================================================

class SimpleLLMInterviewer:
    """Упрощенный интервьюер с прямыми LLM вызовами"""

    def __init__(self, llm_provider='claude_code'):
        self.llm_provider = llm_provider
        if LLM_AVAILABLE:
            self.llm = UnifiedLLMClient(provider=llm_provider)
        else:
            self.llm = None

        self.dialogue_history = []

    def ask_question_with_context(self, user_answer: str, collected_info: dict) -> str:
        """
        Генерирует следующий вопрос на основе ответа пользователя

        Args:
            user_answer: Ответ пользователя (может быть нелогичным!)
            collected_info: Собранная информация до этого момента

        Returns:
            str: Следующий вопрос от агента
        """

        # Формируем prompt для LLM
        system_prompt = """Ты - интервьюер для грантовой заявки в Фонд Президентских Грантов (ФПГ).

Твоя задача:
1. Задавать вопросы чтобы собрать информацию для заявки
2. ПОМОГАТЬ пользователю, даже если он дает нелогичные ответы
3. Если ответ плохой - попробуй переспросить или дать пример
4. Не критикуй, а направляй

Ключевые поля для сбора:
- Имя
- Суть проекта
- Социальная проблема
- Целевая аудитория
- Методология
- Бюджет
- Ожидаемые результаты
"""

        # Формируем контекст
        context_str = "\n".join([f"- {k}: {v}" for k, v in collected_info.items()])

        user_prompt = f"""Собранная информация:
{context_str if context_str else "(Пока ничего не собрано)"}

Последний ответ пользователя: "{user_answer}"

ЗАДАЧА: Сгенерируй СЛЕДУЮЩИЙ вопрос для интервью.

Правила:
- Если ответ плохой (короткий/нелогичный) - попробуй уточнить или дать пример
- Если информация собрана - переходи к следующему полю
- Будь helpful, не критикуй
- Один вопрос за раз

ОТВЕТ (только текст вопроса, без пояснений):"""

        # Вызываем LLM
        if self.llm:
            response = self.llm.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=200,
                temperature=0.7
            )
            return response.strip()
        else:
            # Mock response если LLM недоступен
            return f"[MOCK] Следующий вопрос на основе ответа '{user_answer[:30]}...'"


# =============================================================================
# Dialogue Recorder
# =============================================================================

class DialogueRecorder:
    """Записывает полный диалог"""

    def __init__(self):
        self.dialogue = []
        self.metadata = {
            'test_name': 'simple_llm_dialogue',
            'start_time': datetime.now().isoformat(),
            'llm_provider': None
        }

    def add_turn(self, question: str, user_answer: str, llm_response_time: float = 0):
        """Добавить один ход"""
        self.dialogue.append({
            'turn': len(self.dialogue) + 1,
            'question': question,
            'user_answer': user_answer,
            'llm_response_time': llm_response_time,
            'timestamp': datetime.now().isoformat()
        })

    def save_to_file(self, filepath: str):
        """Сохранить в JSON"""
        self.metadata['end_time'] = datetime.now().isoformat()
        self.metadata['total_turns'] = len(self.dialogue)

        output = {
            'metadata': self.metadata,
            'dialogue': self.dialogue
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n📁 Диалог сохранен: {filepath}")

    def print_dialogue(self):
        """Вывести диалог в консоль"""
        print("\n" + "="*80)
        print("📖 ПОЛНЫЙ ДИАЛОГ")
        print("="*80)

        for turn in self.dialogue:
            print(f"\n--- ХОД {turn['turn']} ---")
            print(f"❓ Вопрос: {turn['question']}")
            print(f"👤 Ответ: {turn['user_answer']}")
            print(f"⏱️ LLM ответил за: {turn['llm_response_time']:.2f}s")

        print("\n" + "="*80)


# =============================================================================
# Main Test
# =============================================================================

def run_chaotic_interview():
    """
    Запускает интервью с нелогичными ответами
    """

    print("\n" + "="*80)
    print("🧪 SIMPLIFIED LLM DIALOGUE TEST")
    print("="*80)
    print("\nТестирование реакции LLM на нелогичные ответы")
    print("Диалог будет сохранен в JSON файл для анализа\n")

    # Инициализация
    interviewer = SimpleLLMInterviewer(llm_provider='claude_code')
    recorder = DialogueRecorder()
    recorder.metadata['llm_provider'] = 'claude_code'

    # Нелогичные ответы для теста
    chaotic_answers = [
        ("Скажите ваше имя", "Вася"),  # OK
        ("В чем суть проекта?", "Мне нравятся бананы и синий цвет"),  # ПЛОХОЙ
        ("Какую проблему решает проект?", "asdfgh"),  # GIBBERISH
        ("Кто целевая аудитория?", "Все"),  # СЛИШКОМ ОБЩИЙ
        ("Опишите методологию", "???"),  # БЕССМЫСЛЕННЫЙ
        ("Какой нужен бюджет?", "Да"),  # ОДНОСЛОЖНЫЙ
    ]

    collected_info = {}

    print("🎬 НАЧАЛО ИНТЕРВЬЮ\n")

    for i, (question, answer) in enumerate(chaotic_answers, 1):
        print(f"\n{'='*80}")
        print(f"ХОД {i}")
        print(f"{'='*80}")

        print(f"❓ Вопрос: {question}")
        print(f"👤 Пользователь отвечает: '{answer}'")

        # Пользователь дает ответ
        if i == 1:
            collected_info['name'] = answer
        elif i == 2:
            collected_info['project_essence'] = answer
        elif i == 3:
            collected_info['social_problem'] = answer
        elif i == 4:
            collected_info['target_audience'] = answer
        elif i == 5:
            collected_info['methodology'] = answer
        elif i == 6:
            collected_info['budget'] = answer

        # LLM генерирует следующий вопрос (или реагирует на плохой ответ)
        print(f"\n🤖 LLM думает...")
        start_time = time.time()

        next_question = interviewer.ask_question_with_context(answer, collected_info)

        elapsed = time.time() - start_time
        print(f"🤖 LLM ответил ({elapsed:.2f}s): {next_question}")

        # Записываем в диалог
        recorder.add_turn(
            question=question,
            user_answer=answer,
            llm_response_time=elapsed
        )

        # Небольшая пауза
        time.sleep(0.5)

    print("\n" + "="*80)
    print("✅ ИНТЕРВЬЮ ЗАВЕРШЕНО")
    print("="*80)

    # Сохраняем диалог
    output_file = Path(__file__).parent / f"dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    recorder.save_to_file(str(output_file))

    # Выводим полный диалог
    recorder.print_dialogue()

    # Анализ
    print("\n" + "="*80)
    print("📊 АНАЛИЗ")
    print("="*80)

    print(f"\nВсего ходов: {len(recorder.dialogue)}")
    print(f"LLM провайдер: {recorder.metadata['llm_provider']}")
    print(f"\nДиалог сохранен: {output_file}")

    print("\n💡 Теперь можно прочитать файл и проанализировать:")
    print("  - Как LLM реагирует на нелогичные ответы?")
    print("  - Переспрашивает ли?")
    print("  - Дает ли примеры?")
    print("  - Помогает ли пользователю?")

    return str(output_file)


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    # Fix encoding for Windows console
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("\n" + "="*80)
    print("SIMPLE LLM DIALOGUE TEST - Business Logic Robustness")
    print("="*80)

    if not LLM_AVAILABLE:
        print("\n⚠️ WARNING: UnifiedLLMClient недоступен!")
        print("Тест будет использовать mock responses")
        print("Для реальных LLM вызовов нужно исправить import\n")

    # Запуск
    dialogue_file = run_chaotic_interview()

    print("\n" + "="*80)
    print("🎯 РЕЗУЛЬТАТ")
    print("="*80)
    print(f"\n✅ Диалог сохранен: {dialogue_file}")
    print("\n📖 Читай файл чтобы увидеть КАК LLM справился с нелогичными ответами!")
    print("="*80 + "\n")
