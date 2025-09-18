#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления подсказок к вопросам интервью в БД
"""

import sys
import os
import sqlite3
import json

# Добавляем путь к модулю БД
import pathlib
current_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'data'))

from database.models import GrantServiceDatabase

def fix_interview_hints():
    """Обновить все вопросы интервью с правильными подсказками"""
    
    # Создаем экземпляр БД
    db = GrantServiceDatabase()
    
    # Полный список вопросов с подсказками
    questions_with_hints = [
        {
            'question_number': 1,
            'question_text': 'Как называется ваш проект в 3-7 словах?',
            'field_name': 'project_name',
            'hint_text': 'Пример: Мобильная библиотека для людей с ОВЗ'
        },
        {
            'question_number': 2,
            'question_text': 'Кратко опишите суть проекта (что хотите сделать)',
            'field_name': 'project_description',
            'hint_text': 'Пример: создадим выездную библиотеку и аудиокниги, чтобы жители сел Новокузнецкого района с ограничениями в здоровье могли бесплатно получить литературу на дом, образовываться и устраиваться на работу'
        },
        {
            'question_number': 3,
            'question_text': 'В каком городе, регионе вы хотите реализовать проект?',
            'field_name': 'project_location',
            'hint_text': 'Пример: Кемеровская область, новокузнецкий район, пгт…'
        },
        {
            'question_number': 4,
            'question_text': 'Опишите, какую проблему решает ваш проект и почему он важен?',
            'field_name': 'problem_solution',
            'hint_text': 'Пример: Сельские жители с ОВЗ Новокузнецкого района не имеют доступа к библиотекам, из-за этого страдает культура и развитие, что приводит к пьянству и невозможности устроиться на работу (по отчету минкультуры 2024)'
        },
        {
            'question_number': 5,
            'question_text': 'Кто будет основной целевой группой вашего проекта? (участники вашего проекта)',
            'field_name': 'target_audience',
            'hint_text': 'Пример: Охватим 300 взрослых людей с ОВЗ, проживающих по 3 поселкам Новокузнецкого района'
        },
        {
            'question_number': 6,
            'question_text': 'Какова главная цель проекта?',
            'field_name': 'main_goal',
            'hint_text': 'Пример: Повысить доступность чтения для людей с ОВЗ в сельской местности'
        },
        {
            'question_number': 7,
            'question_text': 'Перечислите конкретные задачи, которые нужно будет решить, чтобы запустить проект?',
            'field_name': 'project_tasks',
            'hint_text': 'Пример: 1. Оснастить автобус книжным фондом на 1000 экземпляров 2. Провести информационную компанию, чтобы оповестить людей 3.Провести 20 выездных библиотечных сессий с целевой аудиторией'
        },
        {
            'question_number': 8,
            'question_text': 'Сколько времени потребуется на реализацию (когда собираетесь начать и закончить проект?)',
            'field_name': 'project_timeline',
            'hint_text': 'Пример: 01.06.2028-31.12.28 (6 месяцев)'
        },
        {
            'question_number': 9,
            'question_text': 'Что может помешать реализации вашего проекта?',
            'field_name': 'potential_obstacles',
            'hint_text': 'Пример: Часть людей может заболеть и не прийти, но мы сделаем запасные даты встреч, чтобы охватить всю целевую аудиторию'
        },
        {
            'question_number': 10,
            'question_text': 'Опишите, кто будет в команде проекта, какой у них опыт и компетенции, что они будут делать в этом проекте?',
            'field_name': 'team_competencies',
            'hint_text': 'Пример: Руководитель проекта -Марья Ивановна, директор, НКО, 7 лет работает в доме культуры. Библиотекарь, специалист по рекламе, водитель.'
        },
        {
            'question_number': 11,
            'question_text': 'Есть ли добровольцы или волонтеры? Есть ли организации, готовые поддержать ваш проект?',
            'field_name': 'volunteers_partners',
            'hint_text': 'Пример: Администрация Новокузнецкого района, Дом культуры Села …., Добровольческий фонд "Надежда"'
        },
        {
            'question_number': 12,
            'question_text': 'Есть ли у вас АНО? Если да, когда зарегистрировали? Соответствует ли проект уставным видам деятельности?',
            'field_name': 'organization_info',
            'hint_text': 'Пример, да, АНО "Читай-село", ОГРН ….,дата регистрации 15.06.2021, да, п.2.3 устава "Культурно-просветительская деятельность"'
        },
        {
            'question_number': 13,
            'question_text': 'Есть ли у вас сайт, соц сети? Напишите ссылки',
            'field_name': 'online_presence',
            'hint_text': 'Укажите ссылки на сайт, социальные сети, если есть'
        },
        {
            'question_number': 14,
            'question_text': 'Получали ли вы раньше гранты? Если да, укажите год, фонд, результат.',
            'field_name': 'previous_grants',
            'hint_text': 'Пример: да, ФПГ, 2023, 450 000, отчет 100% сдан'
        },
        {
            'question_number': 15,
            'question_text': 'Какая материально-техническая база есть для осуществления проектом?',
            'field_name': 'existing_resources',
            'hint_text': 'Пример: Есть автобус, есть часть книг для использования в проекте'
        },
        {
            'question_number': 16,
            'question_text': 'Какие ключевые мероприятия запланированы?',
            'field_name': 'key_events',
            'hint_text': 'Пример: Июнь-подготовка автобуса, июль -закуп книг, август -проведение информационной компании для оповещения жителей, сентябрь -декабрь 20 выездов'
        },
        {
            'question_number': 17,
            'question_text': 'Какие измеримые результаты будут у каждого мероприятия?',
            'field_name': 'measurable_results',
            'hint_text': 'Пример: Подготовка автобуса - свидетельство ТО, Информационная компания - роздано 300 листовок, оповещено 300 человек, каждый выезд: охват не менее 15 человек.'
        },
        {
            'question_number': 18,
            'question_text': 'Кто отвечает за каждое мероприятие?',
            'field_name': 'event_responsibility',
            'hint_text': 'Пример: Петров - везет автобус на ТО, МарьИвана - и рекламный специалист делают делают листовки и с помощью волонтеров раздают жителям, библиотекарь -подбирает книги…'
        },
        {
            'question_number': 19,
            'question_text': 'Сколько денег нужно на осуществление проекта? Напишите приблизительную цифру',
            'field_name': 'budget_amount',
            'hint_text': 'Пример: 1200000'
        },
        {
            'question_number': 20,
            'question_text': 'Сколько собственных средств и ресурсов вы вкладываете сами в проект?',
            'field_name': 'own_contribution',
            'hint_text': 'Пример: 150000'
        },
        {
            'question_number': 21,
            'question_text': 'На какие основные статьи пойдут грантовые деньги, обоснование статьи?',
            'field_name': 'budget_breakdown',
            'hint_text': 'Пример: Тех.обслуживание автобуса -50000, книги 400000 (средняя цена за книгу 500 р), топливо 100000 (60 р/литр), зарплата команды 200000, реклама (печать листовок) -50000 …..'
        },
        {
            'question_number': 22,
            'question_text': 'Готовы ли вы при необходимости снизить бюджет? Если дадут сумму частично?',
            'field_name': 'budget_flexibility',
            'hint_text': 'Пример, да, сократим рекламные расходы, купим книги подешевле'
        },
        {
            'question_number': 23,
            'question_text': 'Как будете измерять эффективность проекта?',
            'field_name': 'effectiveness_measurement',
            'hint_text': 'Пример: Сделаем анкеты удовлетворенности после каждого выезда, реестр с подсчетом выданных книг и подписью, кому выдали, общее фото с мероприятий, сделаем опрос на сайте'
        },
        {
            'question_number': 24,
            'question_text': 'Что станет с инициативой после окончания гранта?',
            'field_name': 'post_grant_plans',
            'hint_text': 'Пример: После окончания автобус интегрируем в районную библиотечную сеть, финансирование через муниципальный бюджет, если проект понравится, будем проводить его в других селах нашего района'
        }
    ]
    
    print("🚀 Начинаем обновление подсказок в вопросах интервью...")
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем текущее состояние
            cursor.execute("SELECT question_number, question_text, hint_text FROM interview_questions WHERE is_active = 1 ORDER BY question_number")
            existing_questions = cursor.fetchall()
            
            print(f"\n📊 Найдено активных вопросов в БД: {len(existing_questions)}")
            
            # Анализируем каких вопросов нет
            existing_numbers = set()
            questions_without_hints = []
            
            for q_num, q_text, hint in existing_questions:
                existing_numbers.add(q_num)
                if not hint or hint == '':
                    questions_without_hints.append(q_num)
            
            if questions_without_hints:
                print(f"⚠️ Вопросы без подсказок: {questions_without_hints}")
            
            # Обновляем или добавляем вопросы
            updated_count = 0
            added_count = 0
            
            for question_data in questions_with_hints:
                q_num = question_data['question_number']
                
                if q_num in existing_numbers:
                    # Обновляем существующий вопрос (добавляем подсказку)
                    cursor.execute("""
                        UPDATE interview_questions 
                        SET hint_text = ?,
                            question_text = ?,
                            field_name = ?
                        WHERE question_number = ? AND is_active = 1
                    """, (
                        question_data['hint_text'],
                        question_data['question_text'],
                        question_data['field_name'],
                        q_num
                    ))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                        print(f"  ✅ Обновлен вопрос {q_num}: добавлена подсказка")
                else:
                    # Добавляем новый вопрос
                    cursor.execute("""
                        INSERT INTO interview_questions 
                        (question_number, question_text, field_name, question_type, hint_text, is_required, is_active)
                        VALUES (?, ?, ?, 'text', ?, 1, 1)
                    """, (
                        q_num,
                        question_data['question_text'],
                        question_data['field_name'],
                        question_data['hint_text']
                    ))
                    
                    if cursor.rowcount > 0:
                        added_count += 1
                        print(f"  ➕ Добавлен вопрос {q_num}")
            
            conn.commit()
            
            print(f"\n📈 Результаты обновления:")
            print(f"  • Обновлено вопросов: {updated_count}")
            print(f"  • Добавлено новых вопросов: {added_count}")
            
            # Проверяем финальное состояние
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN hint_text IS NOT NULL AND hint_text != '' THEN 1 END) as with_hints
                FROM interview_questions 
                WHERE is_active = 1
            """)
            
            total, with_hints = cursor.fetchone()
            print(f"\n✅ Финальная статистика:")
            print(f"  • Всего активных вопросов: {total}")
            print(f"  • Вопросов с подсказками: {with_hints}")
            print(f"  • Вопросов без подсказок: {total - with_hints}")
            
            if total == with_hints:
                print("\n🎉 Отлично! Все вопросы теперь имеют подсказки!")
            else:
                print(f"\n⚠️ Внимание! Остались вопросы без подсказок: {total - with_hints}")
                
                # Показываем какие вопросы без подсказок
                cursor.execute("""
                    SELECT question_number, question_text 
                    FROM interview_questions 
                    WHERE is_active = 1 AND (hint_text IS NULL OR hint_text = '')
                    ORDER BY question_number
                """)
                
                for q_num, q_text in cursor.fetchall():
                    print(f"    • Вопрос {q_num}: {q_text[:50]}...")
                    
    except Exception as e:
        print(f"\n❌ Ошибка при обновлении подсказок: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_hints_in_bot():
    """Тестовая функция для проверки подсказок"""
    print("\n🧪 Тестирование подсказок...")
    
    try:
        from database import get_interview_questions
        
        questions = get_interview_questions()
        
        print(f"\n📋 Получено вопросов через get_interview_questions(): {len(questions)}")
        
        for i, question in enumerate(questions[:3], 1):  # Показываем первые 3 вопроса
            print(f"\n  Вопрос {question.get('question_number', i)}:")
            print(f"    Текст: {question.get('question_text', 'НЕТ ТЕКСТА')[:50]}...")
            print(f"    Подсказка: {question.get('hint_text', 'НЕТ ПОДСКАЗКИ')[:50]}...")
            print(f"    Поле БД: {question.get('field_name', 'НЕТ ПОЛЯ')}")
            
    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("  ИСПРАВЛЕНИЕ ПОДСКАЗОК В ВОПРОСАХ ИНТЕРВЬЮ")
    print("=" * 60)
    
    # Исправляем подсказки
    if fix_interview_hints():
        print("\n✅ Подсказки успешно исправлены!")
        
        # Тестируем
        test_hints_in_bot()
    else:
        print("\n❌ Не удалось исправить подсказки")