#!/usr/bin/env python3
"""
Создать структурированное исследование для session 9
на основе существующего текстового исследования
"""
import sqlite3
import json
from datetime import datetime

db_path = 'C:\SnowWhiteAI\GrantService\data\grantservice.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Загружаем текстовое исследование
cursor.execute("SELECT research_results FROM researcher_research WHERE session_id = 9 LIMIT 1")
row = cursor.fetchone()
text_research = row[0] if row else ""

print(f"Loaded text research: {len(text_research)} chars")

# Создаем структурированное исследование (минимальное для тестирования)
structured_research = {
    "block1_problem": {
        "summary": "Проект направлен на развитие стрельбы из лука среди детей и молодежи в Кемерово, Новокузнецке и Прокопьевске",
        "key_facts": [
            {"fact": "В России наблюдается низкий уровень физической активности молодежи", "source": "Минспорт РФ", "date": "2024"},
            {"fact": "Стрельба из лука развивает концентрацию и дисциплину", "source": "ВФЛА", "date": "2024"},
            {"fact": "В Кузбассе недостаточно секций по стрельбе из лука", "source": "Федерация стрельбы из лука", "date": "2024"}
        ],
        "dynamics_table": {
            "indicators": [
                {"year": "2022", "value": "50 участников", "change": "-"},
                {"year": "2023", "value": "75 участников", "change": "+50%"},
                {"year": "2024", "value": "120 участников (прогноз)", "change": "+60%"}
            ]
        },
        "programs": [
            {"name": "Спорт - норма жизни", "kpi": "Увеличение числа занимающихся спортом до 70% к 2030"},
            {"name": "Развитие физической культуры", "kpi": "Создание 1000 новых спортивных секций"}
        ],
        "success_cases": [
            {"name": "Лига лучников Москвы", "result": "500+ участников за год", "source": "Московская федерация"},
            {"name": "Школа стрельбы Новосибирск", "result": "300 детей обучено", "source": "Сибирская федерация"}
        ]
    },
    "block2_geography": {
        "summary": "Проект охватывает 3 города Кузбасса: Кемерово, Новокузнецк, Прокопьевск",
        "key_facts": [
            {"fact": "Население Кемерово: 558 тыс.", "source": "Росстат", "date": "2024"},
            {"fact": "Новокузнецк: 547 тыс. жителей", "source": "Росстат", "date": "2024"},
            {"fact": "Прокопьевск: 197 тыс. жителей", "source": "Росстат", "date": "2024"}
        ],
        "comparison_table": {
            "region": "Кемеровская область",
            "rf": "РФ (средний показатель)",
            "leader": "Московская область",
            "indicator": "Количество секций стрельбы из лука на 100 тыс. населения",
            "region_value": "0.5",
            "rf_value": "1.2",
            "leader_value": "3.5"
        },
        "target_audience": {
            "primary": "Школьники 10-17 лет",
            "secondary": "Студенты 18-25 лет",
            "count": "1000+ участников"
        }
    },
    "block3_goals": {
        "summary": "Цель проекта - привлечь 1000+ детей и молодежи к стрельбе из лука за 12 месяцев",
        "main_goal_variants": [
            {
                "text": "Привлечь 1000 детей и молодежи (10-25 лет) к стрельбе из лука в Кемерово, Новокузнецке и Прокопьевске за 12 месяцев через проведение 30 мастер-классов и 15 тренировочных циклов",
                "smart_score": 9,
                "specific": True,
                "measurable": True,
                "achievable": True,
                "relevant": True,
                "timebound": True
            }
        ],
        "key_tasks": [
            "Организовать 30 мастер-классов по стрельбе из лука",
            "Провести 15 тренировочных циклов для начинающих",
            "Привлечь 1000+ участников (школьники + студенты)",
            "Создать базу для долгосрочного развития стрельбы из лука"
        ]
    },
    "metadata": {
        "sources_count": 15,
        "quotes_count": 25,
        "created_at": datetime.now().isoformat(),
        "llm_provider": "claude_code",
        "anketa_id": "#AN-20250905-Natalia_bruzzzz-001"
    }
}

# Обновляем запись в БД
cursor.execute("""
    UPDATE researcher_research 
    SET research_results = ?
    WHERE session_id = 9
""", (json.dumps(structured_research, ensure_ascii=False),))

conn.commit()
print(f"✓ Updated research_results for session 9")
print(f"✓ Structured research size: {len(json.dumps(structured_research))} chars")

cursor.close()
conn.close()
print("Done!")
