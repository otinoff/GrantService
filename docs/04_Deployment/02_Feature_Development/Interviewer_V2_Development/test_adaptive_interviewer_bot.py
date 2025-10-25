#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматическое тестирование Telegram бота с Adaptive Interviewer

Методология (из GrantService):
1. Получить chat_id из истории бота
2. Отправить команду /start_adaptive_interview
3. Получить первый вопрос
4. Отправить ответ
5. Получить следующий вопрос
6. Повторить до завершения
7. Проверить что анкета заполнена

ВАЖНО: Claude Code - основной LLM провайдер!
"""

import requests
import time
import json
import sys

# TODO: Заменить на ваш токен бота
BOT_TOKEN = "7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Тестовые данные проекта
TEST_PROJECT_ANSWERS = {
    "Q1": "Лучные клубы Кемерово",
    "Q2": "В Кемерово нет доступа к стрельбе из лука для молодёжи 14-25 лет",
    "Q3": "500+ молодых людей 14-25 лет в Кемеровской области",
    "Q4": "Создать сеть из 3 лучных клубов и вовлечь 500+ участников за 2 года",
    "Q5": "Задачи: найти помещения, купить оборудование, набрать тренеров, провести мероприятия",
    "Q6": "800 тысяч рублей: 300к на оборудование, 200к на аренду помещений, 300к на зарплаты тренеров",
    "Q7": "Результаты: 500 участников, 3 клуба, 20 мероприятий в год, рост интереса к традиционным видам спорта",
    "Q8": "Команда: я руководитель с опытом 10 лет, 3 тренера с опытом 5+ лет, бухгалтер",
    "Q9": "Партнёры: городская администрация Кемерово, школы №5 и №12, федерация стрельбы из лука",
    "Q10": "После гранта будем работать на членские взносы 1000р/мес, аренда тира для мероприятий"
}


def get_latest_chat_id():
    """Получить chat_id из последних обновлений"""
    response = requests.get(f"{BASE_URL}/getUpdates")
    data = response.json()

    if data['ok'] and data['result']:
        last_update = data['result'][-1]
        if 'message' in last_update:
            chat_id = last_update['message']['chat']['id']
            username = last_update['message']['chat'].get('username', 'Unknown')
            return chat_id, username
    return None, None


def send_message(chat_id, text):
    """Отправить сообщение в чат"""
    response = requests.post(f"{BASE_URL}/sendMessage", json={
        'chat_id': chat_id,
        'text': text
    })
    return response.json()


def get_bot_messages(offset):
    """Получить новые сообщения от бота"""
    params = {'timeout': 5}
    if offset:
        params['offset'] = offset

    response = requests.get(f"{BASE_URL}/getUpdates", params=params)
    data = response.json()

    bot_messages = []
    new_offset = offset

    if data['ok'] and data['result']:
        for update in data['result']:
            if 'message' in update:
                msg = update['message']
                # Только сообщения от бота
                if msg.get('from', {}).get('is_bot'):
                    bot_messages.append(msg.get('text', ''))

                # Обновляем offset
                new_offset = update['update_id'] + 1

    return bot_messages, new_offset


def extract_question_id(message):
    """Извлечь ID вопроса из сообщения бота"""
    # Ищем паттерн [Q1], [Q2], etc.
    import re
    match = re.search(r'\[Q(\d+)\]', message)
    if match:
        return f"Q{match.group(1)}"

    # Или паттерн "Вопрос 1/10"
    match = re.search(r'Вопрос (\d+)/10', message)
    if match:
        return f"Q{match.group(1)}"

    return None


def main():
    print("=" * 80)
    print("🧪 ТЕСТ: Adaptive Interviewer Bot (Claude Code)")
    print("=" * 80)

    # Шаг 1: Получаем chat_id
    print("\n📱 [1/6] Получение chat_id...")
    chat_id, username = get_latest_chat_id()

    if not chat_id:
        print("❌ Не найдено сообщений. Отправьте боту /start и запустите снова.")
        return

    print(f"✅ Chat ID: {chat_id}")
    print(f"✅ Username: @{username}")

    # Получаем текущий offset
    updates = requests.get(f"{BASE_URL}/getUpdates").json()
    if updates['ok'] and updates['result']:
        current_offset = updates['result'][-1]['update_id'] + 1
    else:
        current_offset = 0

    # Шаг 2: Отправляем команду старта интервью
    print(f"\n📤 [2/6] Отправка команды /start_adaptive_interview...")
    result = send_message(chat_id, "/start_adaptive_interview")

    if not result['ok']:
        print(f"❌ Ошибка отправки: {result}")
        return

    print("✅ Команда отправлена!")

    # Шаг 3: Цикл интервью
    print(f"\n❓ [3/6] Начало интервью...")
    print("=" * 80)

    question_count = 0
    max_questions = 15  # Защита от зацикливания

    while question_count < max_questions:
        # Ждем ответ от бота
        time.sleep(3)

        # Получаем сообщения
        bot_messages, current_offset = get_bot_messages(current_offset)

        if not bot_messages:
            print("⚠️ Нет новых сообщений от бота")
            time.sleep(2)
            continue

        # Обрабатываем сообщения
        for message in bot_messages:
            print(f"\n🤖 БОТ:\n{message}")
            print("-" * 80)

            # Проверяем завершение
            if "завершено" in message.lower() or "completed" in message.lower():
                print("\n✅ Интервью завершено!")
                print("=" * 80)

                # Проверяем упоминание Claude Code
                if "claude_code" in message.lower() or "claude code" in message.lower():
                    print("✅ SUCCESS: Claude Code упомянут (основной LLM)!")
                else:
                    print("⚠️ WARNING: Claude Code не упомянут в результатах")

                # Проверяем audit score
                if "оценка" in message.lower() or "score" in message.lower():
                    print("✅ SUCCESS: Audit score присутствует!")

                return

            # Извлекаем ID вопроса
            q_id = extract_question_id(message)

            if q_id:
                question_count += 1
                print(f"\n📝 Вопрос {question_count}: {q_id}")

                # Получаем ответ из тестовых данных
                if q_id in TEST_PROJECT_ANSWERS:
                    answer = TEST_PROJECT_ANSWERS[q_id]
                    print(f"👤 ОТВЕТ: {answer}")

                    # Отправляем ответ
                    send_message(chat_id, answer)
                    print("✅ Ответ отправлен")
                else:
                    print(f"⚠️ Нет тестового ответа для {q_id}")
                    # Отправляем дефолтный ответ
                    send_message(chat_id, "Тестовый ответ для " + q_id)

                break

    print("\n⚠️ Достигнут лимит вопросов (защита от зацикливания)")


if __name__ == "__main__":
    main()
