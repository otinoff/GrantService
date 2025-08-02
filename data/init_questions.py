#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт инициализации вопросов интервью в базе данных
"""

import sys
import os
sys.path.append('/var/GrantService/data')

from database import GrantServiceDatabase

def init_questions():
    """Инициализация вопросов интервью"""
    
    # Создаем экземпляр БД
    db = GrantServiceDatabase()
    
    # Тестовые вопросы из qwestions.md
    questions = [
        {
            'question_number': 1,
            'question_text': 'Как называется ваш проект в 3-7 словах?',
            'field_name': 'project_name',
            'question_type': 'text',
            'hint_text': 'Пример: Мобильная библиотека для людей с ОВЗ',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 3, 'max_length': 50}
        },
        {
            'question_number': 2,
            'question_text': 'Кратко опишите суть проекта',
            'field_name': 'project_description',
            'question_type': 'textarea',
            'hint_text': 'Пример: создадим выездную библиотеку для людей с ограниченными возможностями здоровья, которая будет доставлять книги на дом и проводить литературные встречи',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 500}
        },
        {
            'question_number': 3,
            'question_text': 'На какой грант и в какой фонд планируете подавать заявку?',
            'field_name': 'grant_foundation',
            'question_type': 'text',
            'hint_text': 'Пример: Фонд Потанина, конкурс "Музей 4.0"',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 5, 'max_length': 200}
        },
        {
            'question_number': 4,
            'question_text': 'Кто ваша целевая аудитория? Кому поможет проект?',
            'field_name': 'target_audience',
            'question_type': 'textarea',
            'hint_text': 'Пример: люди с ограниченными возможностями здоровья, пожилые люди, дети из малообеспеченных семей',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 10, 'max_length': 300}
        },
        {
            'question_number': 5,
            'question_text': 'Какой у вас бюджет и сроки реализации проекта?',
            'field_name': 'budget_timeline',
            'question_type': 'textarea',
            'hint_text': 'Пример: бюджет 500,000 рублей, срок реализации 12 месяцев',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 10, 'max_length': 200}
        },
        {
            'question_number': 6,
            'question_text': 'Расскажите о команде проекта и ключевых компетенциях',
            'field_name': 'team_competencies',
            'question_type': 'textarea',
            'hint_text': 'Пример: команда из 5 человек: руководитель проекта, библиотекарь, социальный работник, водитель, координатор',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 400}
        },
        {
            'question_number': 7,
            'question_text': 'В чем уникальность и инновационность вашего проекта?',
            'field_name': 'uniqueness_innovation',
            'question_type': 'textarea',
            'hint_text': 'Пример: первая в регионе мобильная библиотека для людей с ОВЗ с использованием современных технологий',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 15, 'max_length': 300}
        },
        {
            'question_number': 8,
            'question_text': 'Как вы планируете измерять результаты проекта?',
            'field_name': 'success_metrics',
            'question_type': 'textarea',
            'hint_text': 'Пример: количество обслуженных читателей, количество выданных книг, отзывы участников',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 15, 'max_length': 300}
        }
    ]
    
    print("🚀 Инициализация вопросов интервью...")
    
    # Добавляем вопросы в БД
    for question_data in questions:
        try:
            question_id = db.create_question(question_data)
            if question_id:
                print(f"✅ Вопрос {question_data['question_number']} создан (ID: {question_id})")
            else:
                print(f"❌ Ошибка создания вопроса {question_data['question_number']}")
        except Exception as e:
            print(f"❌ Ошибка при создании вопроса {question_data['question_number']}: {e}")
    
    print("\n🎉 Инициализация завершена!")
    
    # Проверяем результат
    active_questions = db.get_active_questions()
    print(f"📊 Всего активных вопросов: {len(active_questions)}")

if __name__ == "__main__":
    init_questions() 