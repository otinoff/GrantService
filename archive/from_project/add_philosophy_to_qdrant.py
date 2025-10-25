#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавление философии интервьюера в Qdrant базу знаний
"""
import requests
import uuid

QDRANT_HOST = "5.35.88.251"
QDRANT_PORT = 6333
COLLECTION_NAME = "knowledge_sections"

print("=" * 80)
print("ДОБАВЛЕНИЕ ФИЛОСОФИИ ИНТЕРВЬЮЕРА В QDRANT")
print("=" * 80)

# Load model
try:
    from sentence_transformers import SentenceTransformer
    print("\n[1/3] Загрузка модели...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    print("      ✅ Модель загружена")
except Exception as e:
    print(f"\n❌ Ошибка загрузки модели: {e}")
    exit(1)

# Philosophy content - ключевые разделы для агентов
philosophy_sections = [
    {
        "section_name": "Философия интервьюера: Главная идея",
        "content": """Интервьюер - это мост между хаосом идеи и требованиями фонда.

Человек приходит с идеей в голове - хаотичной, эмоциональной, неструктурированной.
Фонд президентских грантов (ФПГ) - это конкретная машина, требующая точных ответов на точные вопросы.

Задача интервьюера: Превратить сырую идею в структурированную заявку, соответствующую требованиям ФПГ,
причем сделать это по ходу разговора, а не после.

Ключевая цель: Человек должен уйти с анкетой, которая готова к подаче в ФПГ, без переделок."""
    },
    {
        "section_name": "Философия интервьюера: 5 ключевых функций",
        "content": """1. Вытягивает структуру из хаоса - превращает "хочу детям помочь" в конкретные цифры:
сколько детей, какого возраста, из каких семей, в каком регионе.

2. Проверяет честность бюджета - копает детали: на что конкретно, почему такая цена, где смета по статьям.

3. Ищет слабые места ПО ХОДУ, а не после - после каждых 5 вопросов говорит "вот тут слабо, давайте сразу уточним".

4. Заставляет думать о ПОСЛЕ гранта - как будет работать без гранта, кто будет платить, есть ли партнеры.

5. Использует базу знаний ФПГ - лезет в Qdrant, смотрит требования, задает вопрос с учетом контекста успешных заявок."""
    },
    {
        "section_name": "Философия интервьюера: НЕ допросчик, а консультант",
        "content": """Интервьюер НЕ должен быть допросчиком с чек-листом:
- Не механический процесс "вопрос-ответ"
- Не экзамен для пользователя

Интервьюер ДОЛЖЕН быть умным консультантом:
- Слышит идею целиком
- Задает уточняющие вопросы там, где нужно
- Объясняет ЧТО хочет ФПГ и ПОЧЕМУ
- Помогает сформулировать так, чтобы попасть в требования
- Человек чувствует поддержку, а не давление

Ощущение от процесса должно быть: не экзамен, а консультация."""
    },
    {
        "section_name": "Философия интервьюера: Анализ = Аудит одновременно",
        "content": """Ключевой принцип (Adaptive подход):

АНАЛИЗ ОТВЕТА = ЭТО И ЕСТЬ АУДИТ

Не нужно:
- Отдельный AuditorAgent
- Промежуточные аудиты после блоков
- Этап "переделки" анкеты

Вместо этого:
- Анализируем каждый ответ сразу
- Решаем: достаточно или копать глубже
- Если качество ответа ≥7/10 - идем дальше
- Если <7/10 - уточняем прямо сейчас
- Анкета готова сразу (качество ≥80/100)

Это экономит LLM вызовы, улучшает UX, повышает завершаемость с 70% до 85%."""
    },
    {
        "section_name": "Философия интервьюера: Адаптивная глубина по темам",
        "content": """12 тем вместо 15 фиксированных вопросов:
problem, goal, target_audience, methodology, budget, team, partners,
risks, results, sustainability, timeline, uniqueness

По каждой теме:
- Минимальное качество: 7/10 (для критичных тем) или 6/10 (для важных)
- Максимум вопросов по теме: 5
- Если пользователь сразу дал хороший ответ → идем дальше (1 вопрос)
- Если слабо → копаем глубже (до 5 вопросов)
- Общее количество вопросов: от 15 до 30 (адаптивно)

Используй контекст из Qdrant для каждой темы:
- Поиск по теме (например, "бюджет проекта")
- Берешь Top 3 релевантных раздела из требований ФПГ
- Генерируешь вопрос с учетом этих требований"""
    }
]

print(f"\n[2/3] Генерация эмбеддингов для {len(philosophy_sections)} разделов...")

# Add sections to Qdrant
points = []
for idx, section in enumerate(philosophy_sections):
    # Generate embedding
    content = section['content']
    embedding = model.encode(content, convert_to_tensor=False)

    # Create point
    point = {
        "id": str(uuid.uuid4()),
        "vector": embedding.tolist(),
        "payload": {
            "section_name": section['section_name'],
            "content": content,
            "source": "INTERVIEWER_PHILOSOPHY.md",
            "type": "philosophy",
            "priority": "P0"  # Критичная информация для агентов
        }
    }
    points.append(point)
    print(f"   ✅ {idx+1}/{len(philosophy_sections)}: {section['section_name'][:50]}...")

print(f"\n[3/3] Загрузка в Qdrant ({QDRANT_HOST}:{QDRANT_PORT})...")

# Upload to Qdrant
response = requests.put(
    f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points",
    json={
        "points": points
    }
)

if response.status_code == 200:
    print(f"\n✅ Успешно добавлено {len(points)} разделов философии!")

    # Get updated stats
    response = requests.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}")
    if response.status_code == 200:
        data = response.json()
        result = data.get('result', {})
        print(f"\n📊 Обновленная статистика:")
        print(f"   • Всего разделов: {result.get('points_count', 0)}")
        print(f"   • Из них философия: {len(points)}")
        print(f"   • Статус: {result.get('status', 'unknown')}")
else:
    print(f"\n❌ Ошибка загрузки: {response.status_code}")
    print(response.text)

print("\n" + "=" * 80)
print("ФИЛОСОФИЯ ДОБАВЛЕНА В БАЗУ ЗНАНИЙ")
print("Теперь агенты-интервьюеры могут использовать эти принципы!")
print("=" * 80)
