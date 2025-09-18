#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт инициализации полного списка вопросов интервью из qwestions.md
"""

import sys
import os
sys.path.append('/var/GrantService/data')

from database import GrantServiceDatabase

def init_full_questions():
    """Инициализация полного списка вопросов интервью"""
    
    # Создаем экземпляр БД
    db = GrantServiceDatabase()
    
    # Полный список вопросов из qwestions.md
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
            'question_text': 'Кратко опишите суть проекта (что хотите сделать)',
            'field_name': 'project_description',
            'question_type': 'textarea',
            'hint_text': 'Пример: создадим выездную библиотеку и аудиокниги, чтобы жители сел Новокузнецкого района с ограничениями в здоровье могли бесплатно получить литературу на дом, образовываться и устраиваться на работу',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 500}
        },
        {
            'question_number': 3,
            'question_text': 'В каком городе, регионе вы хотите реализовать проект?',
            'field_name': 'project_location',
            'question_type': 'text',
            'hint_text': 'Пример: Кемеровская область, новокузнецкий район, пгт…',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 5, 'max_length': 200}
        },
        {
            'question_number': 4,
            'question_text': 'Опишите, какую проблему решает ваш проект и почему он важен?',
            'field_name': 'problem_solution',
            'question_type': 'textarea',
            'hint_text': 'Пример: Сельские жители с ОВЗ Новокузнецкого района не имеют доступа к библиотекам, из-за этого страдает культура и развитие, что приводит к пьянству и невозможности устроиться на работу (по отчету минкультуры 2024)',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 30, 'max_length': 400}
        },
        {
            'question_number': 5,
            'question_text': 'Кто будет основной целевой группой вашего проекта? (участники вашего проекта)',
            'field_name': 'target_audience',
            'question_type': 'textarea',
            'hint_text': 'Пример: Охватим 300 взрослых людей с ОВЗ, проживающих по 3 поселкам Новокузнецкого района',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 15, 'max_length': 300}
        },
        {
            'question_number': 6,
            'question_text': 'Какова главная цель проекта?',
            'field_name': 'main_goal',
            'question_type': 'textarea',
            'hint_text': 'Пример: Повысить доступность чтения для людей с ОВЗ в сельской местности',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 10, 'max_length': 200}
        },
        {
            'question_number': 7,
            'question_text': 'Перечислите конкретные задачи, которые нужно будет решить, чтобы запустить проект?',
            'field_name': 'project_tasks',
            'question_type': 'textarea',
            'hint_text': 'Пример: 1. Оснастить автобус книжным фондом на 1000 экземпляров 2. Провести информационную компанию, чтобы оповестить людей 3.Провести 20 выездных библиотечных сессий с целевой аудиторией',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 30, 'max_length': 500}
        },
        {
            'question_number': 8,
            'question_text': 'Сколько времени потребуется на реализацию (когда собираетесь начать и закончить проект?)',
            'field_name': 'project_timeline',
            'question_type': 'text',
            'hint_text': 'Пример: 01.06.2028-31.12.28 (6 месяцев)',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 10, 'max_length': 100}
        },
        {
            'question_number': 9,
            'question_text': 'Что может помешать реализации вашего проекта?',
            'field_name': 'potential_obstacles',
            'question_type': 'textarea',
            'hint_text': 'Пример: Часть людей может заболеть и не прийти, но мы сделаем запасные даты встреч, чтобы охватить всю целевую аудиторию',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 15, 'max_length': 300}
        },
        {
            'question_number': 10,
            'question_text': 'Опишите, кто будет в команде проекта, какой у них опыт и компетенции, что они будут делать в этом проекте?',
            'field_name': 'team_competencies',
            'question_type': 'textarea',
            'hint_text': 'Пример: Руководитель проекта -Марья Ивановна, директор, НКО, 7 лет работает в доме культуры. Библиотекарь, специалист по рекламе, водитель.',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 400}
        },
        {
            'question_number': 11,
            'question_text': 'Есть ли добровольцы или волонтеры? Есть ли организации, готовые поддержать ваш проект?',
            'field_name': 'volunteers_partners',
            'question_type': 'textarea',
            'hint_text': 'Пример: Администрация Новокузнецкого района, Дом культуры Села …., Добровольческий фонд "Надежда"',
            'is_required': False,
            'is_active': True,
            'validation_rules': {'min_length': 10, 'max_length': 300}
        },
        {
            'question_number': 12,
            'question_text': 'Есть ли у вас АНО? Если да, когда зарегистрировали? Соответствует ли проект уставным видам деятельности?',
            'field_name': 'organization_info',
            'question_type': 'textarea',
            'hint_text': 'Пример, да, АНО "Читай-село", ОГРН ….,дата регистрации 15.06.2021, да, п.2.3 устава "Культурно-просветительская деятельность"',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 15, 'max_length': 300}
        },
        {
            'question_number': 13,
            'question_text': 'Есть ли у вас сайт, соц сети? Напишите ссылки',
            'field_name': 'online_presence',
            'question_type': 'textarea',
            'hint_text': 'Укажите ссылки на сайт, социальные сети, если есть',
            'is_required': False,
            'is_active': True,
            'validation_rules': {'min_length': 5, 'max_length': 200}
        },
        {
            'question_number': 14,
            'question_text': 'Получали ли вы раньше гранты? Если да, укажите год, фонд, результат.',
            'field_name': 'previous_grants',
            'question_type': 'textarea',
            'hint_text': 'Пример: да, ФПГ, 2023, 450 000, отчет 100% сдан',
            'is_required': False,
            'is_active': True,
            'validation_rules': {'min_length': 5, 'max_length': 200}
        },
        {
            'question_number': 15,
            'question_text': 'Какая материально-техническая база есть для осуществления проектом?',
            'field_name': 'existing_resources',
            'question_type': 'textarea',
            'hint_text': 'Пример: Есть автобус, есть часть книг для использования в проекте',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 10, 'max_length': 300}
        },
        {
            'question_number': 16,
            'question_text': 'Какие ключевые мероприятия запланированы?',
            'field_name': 'key_events',
            'question_type': 'textarea',
            'hint_text': 'Пример: Июнь-подготовка автобуса, июль -закуп книг, август -проведение информационной компании для оповещения жителей, сентябрь -декабрь 20 выездов',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 400}
        },
        {
            'question_number': 17,
            'question_text': 'Какие измеримые результаты будут у каждого мероприятия?',
            'field_name': 'measurable_results',
            'question_type': 'textarea',
            'hint_text': 'Пример: Подготовка автобуса - свидетельство ТО, Информационная компания - роздано 300 листовок, оповещено 300 человек, каждый выезд: охват не менее 15 человек.',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 400}
        },
        {
            'question_number': 18,
            'question_text': 'Кто отвечает за каждое мероприятие?',
            'field_name': 'event_responsibility',
            'question_type': 'textarea',
            'hint_text': 'Пример: Петров - везет автобус на ТО, МарьИвана - и рекламный специалист делают делают листовки и с помощью волонтеров раздают жителям, библиотекарь -подбирает книги…',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 400}
        },
        {
            'question_number': 19,
            'question_text': 'Сколько денег нужно на осуществление проекта? Напишите приблизительную цифру',
            'field_name': 'budget_amount',
            'question_type': 'number',
            'hint_text': 'Пример: 1200000',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_value': 1000, 'max_value': 10000000}
        },
        {
            'question_number': 20,
            'question_text': 'Сколько собственных средств и ресурсов вы вкладываете сами в проект?',
            'field_name': 'own_contribution',
            'question_type': 'number',
            'hint_text': 'Пример: 150000',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_value': 0, 'max_value': 1000000}
        },
        {
            'question_number': 21,
            'question_text': 'На какие основные статьи пойдут грантовые деньги, обоснование статьи?',
            'field_name': 'budget_breakdown',
            'question_type': 'textarea',
            'hint_text': 'Пример: Тех.обслуживание автобуса -50000, книги 400000 (средняя цена за книгу 500 р), топливо 100000 (60 р/литр), зарплата команды 200000, реклама (печать листовок) -50000 …..',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 30, 'max_length': 500}
        },
        {
            'question_number': 22,
            'question_text': 'Готовы ли вы при необходимости снизить бюджет? Если дадут сумму частично?',
            'field_name': 'budget_flexibility',
            'question_type': 'textarea',
            'hint_text': 'Пример, да, сократим рекламные расходы, купим книги подешевле',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 10, 'max_length': 200}
        },
        {
            'question_number': 23,
            'question_text': 'Как будете измерять эффективность проекта?',
            'field_name': 'effectiveness_measurement',
            'question_type': 'textarea',
            'hint_text': 'Пример: Сделаем анкеты удовлетворенности после каждого выезда, реестр с подсчетом выданных книг и подписью, кому выдали, общее фото с мероприятий, сделаем опрос на сайте',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 400}
        },
        {
            'question_number': 24,
            'question_text': 'Что станет с инициативой после окончания гранта?',
            'field_name': 'post_grant_plans',
            'question_type': 'textarea',
            'hint_text': 'Пример: После окончания автобус интегрируем в районную библиотечную сеть, финансирование через муниципальный бюджет, если проект понравится, будем проводить его в других селах нашего района',
            'is_required': True,
            'is_active': True,
            'validation_rules': {'min_length': 20, 'max_length': 400}
        }
    ]
    
    print("Инициализация полного списка вопросов интервью...")
    
    # Очищаем существующие вопросы
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM interview_questions")
            conn.commit()
            print("Существующие вопросы удалены")
    except Exception as e:
        print(f"Ошибка очистки БД: {e}")
    
    # Добавляем новые вопросы в БД
    for question_data in questions:
        try:
            question_id = db.create_question(question_data)
            if question_id:
                print(f"Вопрос {question_data['question_number']} создан (ID: {question_id})")
            else:
                print(f"Ошибка создания вопроса {question_data['question_number']}")
        except Exception as e:
            print(f"Ошибка при создании вопроса {question_data['question_number']}: {e}")
    
    print("\nИнициализация завершена!")
    
    # Проверяем результат
    active_questions = db.get_active_questions()
    print(f"Всего активных вопросов: {len(active_questions)}")

if __name__ == "__main__":
    init_full_questions() 