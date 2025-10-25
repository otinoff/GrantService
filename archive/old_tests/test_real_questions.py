"""
Тест Expert Agent на реальных вопросах о грантах
"""

import sys
sys.path.append('C:\\SnowWhiteAI\\GrantService')

from expert_agent import ExpertAgent

print("Инициализация Expert Agent...")
agent = ExpertAgent()

# Реальные вопросы от пользователей
questions = [
    "Какие требования к названию проекта?",
    "Как правильно описать целевую аудиторию?",
    "Что нужно указать в разделе О проекте?",
    "Какие расходы можно включить в бюджет?",
    "На что нельзя тратить грант?",
    "Как составить календарный план проекта?",
    "Какие документы нужно предоставить?",
    "Что такое социальная значимость проекта?"
]

print("\n" + "=" * 70)
print("ТЕСТИРОВАНИЕ EXPERT AGENT НА РЕАЛЬНЫХ ВОПРОСАХ")
print("=" * 70)

for i, question in enumerate(questions, 1):
    print(f"\n[Вопрос {i}/{len(questions)}] {question}")
    print("-" * 70)

    results = agent.query_knowledge(
        question=question,
        fund="fpg",
        top_k=3,
        min_score=0.3
    )

    if results:
        print(f"Найдено {len(results)} ответов:\n")

        for j, r in enumerate(results, 1):
            print(f"  {j}. {r['section_name']}")
            print(f"     Relevance: {r['relevance_score']:.3f}")
            print(f"     Отрывок: {r['content'][:200]}...")
            print()
    else:
        print("  (нет релевантных ответов)")

    print()

print("=" * 70)
print("Статистика:")
stats = agent.get_statistics()
print(f"  Всего разделов в базе: {stats['postgres']['sections']}")
print(f"  Векторов в Qdrant: {stats['qdrant']['vectors']}")
print("=" * 70)

agent.close()
print("\nТест завершен!")
