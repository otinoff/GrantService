#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, ".")

from shared.telegram_utils.file_generators import generate_anketa_txt

# Test data from InterviewAutoResponder
test_anketa = {
    'anketa_id': 'TEST_123',
    'project_name': 'AI Grant Assistant - Интеллектуальная система для грантов',
    'answers_data': {
        'название_проекта': 'AI Grant Assistant - Интеллектуальная система для грантов',
        'описание_проекта': 'Система использует AI для автоматизации грантовых заявок',
        'целевая_аудитория': 'Молодые учёные и исследователи до 35 лет',
        'бюджет': '1 500 000 рублей',
        'сроки': '12 месяцев',
        'результаты': 'Функциональная платформа с 1000+ пользователей',
        'команда': 'Команда из 5 специалистов: 2 разработчика, 1 дизайнер, 1 менеджер, 1 эксперт по грантам',
    },
    'interview_data': {
        'название_проекта': 'AI Grant Assistant - Интеллектуальная система для грантов',
        'описание_проекта': 'Система использует AI для автоматизации грантовых заявок',
        'целевая_аудитория': 'Молодые учёные и исследователи до 35 лет',
        'бюджет': '1 500 000 рублей',
    },
    'completed_at': '2025-10-27 10:18:00'
}

anketa_txt = generate_anketa_txt(test_anketa)
print(anketa_txt)
