#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для отправки документов через Telegram Bot API
"""

import os
import asyncio
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import requests
import time

# Получаем токен бота из переменных окружения или конфига
def get_bot_token() -> Optional[str]:
    """Получить токен Telegram бота"""
    try:
        print("🔍 Поиск токена Telegram бота...")
        
        # Сначала проверяем файлы конфигурации (приоритет над переменными окружения)
        current_dir = Path(__file__).parent
        config_paths = [
            current_dir.parent.parent / "config" / ".env",
            current_dir.parent.parent / "telegram-bot" / "config" / ".env",
            current_dir.parent.parent / ".env"
        ]
        
        print(f"🔍 Проверяю файлы конфигурации (приоритет):")
        for config_path in config_paths:
            print(f"   - {config_path}: {'✅' if config_path.exists() else '❌'}")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('TELEGRAM_BOT_TOKEN='):
                            found_token = line.split('=', 1)[1].strip().strip('"\'')
                            print(f"✅ Токен найден в файле {config_path}")
                            print(f"   Токен: {found_token[:20]}...{found_token[-10:]}")
                            return found_token
        
        # Пробуем получить из переменных окружения (второй приоритет)
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if token:
            print(f"✅ Токен найден в переменных окружения: {token[:20]}...{token[-10:]}")
            return token
        else:
            print("❌ Токен не найден в переменных окружения")
        
        # Если не найден в файлах, используем токен из main.py
        main_py_path = current_dir.parent.parent / "telegram-bot" / "main.py"
        print(f"🔍 Проверяю main.py: {main_py_path} ({'✅' if main_py_path.exists() else '❌'})")
        if main_py_path.exists():
            with open(main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Ищем строку с токеном
                lines = content.split('\n')
                for line in lines:
                    if 'TOKEN' in line and ':' in line and 'AAG' in line:
                        # Извлекаем токен из строки вида: TOKEN = "7685915842:AAG..."
                        token_part = line.split('"')[1] if '"' in line else line.split("'")[1]
                        if token_part and ':' in token_part:
                            print(f"✅ Токен найден в main.py: {token_part[:20]}...{token_part[-10:]}")
                            return token_part
        
        print("❌ Токен не найден во всех источниках!")
        return None
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
        return None

def send_document_to_telegram(user_id: int, file_path: str, caption: str = "",
                            grant_application_id: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Отправить документ пользователю через Telegram Bot API
    
    Args:
        user_id: Telegram ID пользователя
        file_path: Путь к файлу для отправки
        caption: Подпись к документу
        grant_application_id: ID грантовой заявки (опционально)
    
    Returns:
        Tuple[bool, Dict]: (успех, данные ответа или ошибка)
    """
    try:
        print(f"📤 === НАЧИНАЕМ ОТПРАВКУ ДОКУМЕНТА ===")
        print(f"   Пользователь: {user_id}")
        print(f"   Файл: {file_path}")
        print(f"   Подпись: {caption}")
        print(f"   ID заявки: {grant_application_id}")
        
        # Получаем токен бота
        print(f"🔑 Получаем токен бота...")
        bot_token = get_bot_token()
        if not bot_token:
            print(f"❌ Токен Telegram бота не найден!")
            return False, {"error": "Токен Telegram бота не найден"}
        
        print(f"✅ Токен получен: {bot_token[:20]}...{bot_token[-10:]}")
        
        # Проверяем существование файла
        print(f"📁 Проверяем файл: {file_path}")
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return False, {"error": f"Файл не найден: {file_path}"}
        
        file_size = os.path.getsize(file_path)
        print(f"✅ Файл найден, размер: {file_size} байт")
        
        # Если файл - это заявка, экспортируем её в PDF
        if grant_application_id and not file_path:
            print(f"📋 Экспортируем заявку {grant_application_id} в PDF...")
            file_path = export_application_to_pdf(grant_application_id)
            if not file_path:
                print(f"❌ Ошибка экспорта заявки в PDF")
                return False, {"error": "Ошибка экспорта заявки в PDF"}
        
        # Подготавливаем URL для API
        api_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        print(f"🔗 URL API: {api_url[:50]}...{api_url[-20:]}")
        
        # Подготавливаем файл для отправки
        file_name = os.path.basename(file_path)
        mime_type = get_mime_type(file_path)
        print(f"📄 Имя файла: {file_name}")
        print(f"📄 MIME тип: {mime_type}")
        
        print(f"🚀 Отправляем HTTP запрос...")
        
        with open(file_path, 'rb') as file:
            files = {
                'document': (file_name, file, mime_type)
            }
            
            data = {
                'chat_id': user_id,
                'caption': caption[:1024] if caption else ""  # Telegram лимит 1024 символа
            }
            
            print(f"📊 Данные запроса:")
            print(f"   chat_id: {data['chat_id']}")
            print(f"   caption: '{data['caption']}'")
            print(f"   document: {file_name}")
            
            # Отправляем запрос
            print(f"📤 Отправляем документ {file_name} пользователю {user_id}")
            response = requests.post(api_url, data=data, files=files, timeout=30)
            
            print(f"📥 Получен ответ:")
            print(f"   Статус код: {response.status_code}")
            print(f"   Заголовки: {dict(response.headers)}")
            
            # Проверяем ответ
            if response.status_code == 200:
                result = response.json()
                print(f"📄 Содержимое ответа: {result}")
                if result.get('ok'):
                    print(f"✅ Документ успешно отправлен: {file_name}")
                    return True, result.get('result', {})
                else:
                    error_msg = result.get('description', 'Неизвестная ошибка')
                    error_code = result.get('error_code', 'Неизвестный код')
                    print(f"❌ Ошибка API:")
                    print(f"   Код: {error_code}")
                    print(f"   Описание: {error_msg}")
                    return False, {"error": error_msg}
            else:
                print(f"❌ HTTP ошибка: {response.status_code}")
                try:
                    response_text = response.text
                    print(f"   Текст ответа: {response_text}")
                except:
                    print(f"   Текст ответа не доступен")
                error_msg = f"HTTP ошибка: {response.status_code}"
                return False, {"error": error_msg}
                
    except Exception as e:
        error_msg = f"Ошибка отправки: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"📋 Трассировка ошибки:")
        print(traceback.format_exc())
        return False, {"error": error_msg}

def get_mime_type(file_path: str) -> str:
    """Определить MIME тип файла"""
    extension = Path(file_path).suffix.lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.txt': 'text/plain'
    }
    return mime_types.get(extension, 'application/octet-stream')

def export_application_to_pdf(grant_application_id: str) -> Optional[str]:
    """
    Экспортировать грантовую заявку в PDF файл
    
    Args:
        grant_application_id: ID грантовой заявки
        
    Returns:
        Путь к созданному PDF файлу или None при ошибке
    """
    try:
        # Импортируем базу данных
        import sys
        from pathlib import Path
        
        current_dir = Path(__file__).parent
        base_dir = current_dir.parent.parent
        
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))
        
        from data.database.models import GrantServiceDatabase
        
        # Определяем путь к базе данных
        # PostgreSQL - параметры из переменных окружения
        db = GrantServiceDatabase()
        
        # Получаем данные заявки
        application = db.get_application_by_number(grant_application_id)
        if not application:
            print(f"Заявка {grant_application_id} не найдена")
            return None
        
        # Создаем простой текстовый файл (в будущем можно заменить на PDF)
        ready_grants_dir = base_dir / "data" / "ready_grants"
        ready_grants_dir.mkdir(exist_ok=True)
        
        output_file = ready_grants_dir / f"{grant_application_id}.txt"
        
        # Формируем содержимое файла
        content_lines = [
            f"ГРАНТОВАЯ ЗАЯВКА: {grant_application_id}",
            "=" * 50,
            f"Название: {application.get('title', 'Не указано')}",
            f"Статус: {application.get('status', 'Не указан')}",
            f"Создана: {application.get('created_at', 'Не указано')}",
            "",
            "СОДЕРЖАНИЕ:",
            "-" * 30
        ]
        
        # Добавляем содержимое заявки
        try:
            if application.get('content_json'):
                content_data = json.loads(application['content_json'])
                if isinstance(content_data, dict):
                    for key, value in content_data.items():
                        content_lines.append(f"{key}: {value}")
                else:
                    content_lines.append(str(content_data))
            else:
                content_lines.append("Содержимое недоступно")
        except Exception as e:
            content_lines.append(f"Ошибка чтения содержимого: {e}")
        
        # Записываем в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        print(f"✅ Заявка экспортирована: {output_file}")
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Ошибка экспорта заявки в PDF: {e}")
        print(traceback.format_exc())
        return None

def test_telegram_connection() -> Tuple[bool, str]:
    """Тестировать соединение с Telegram Bot API"""
    try:
        print(f"🧪 === ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К TELEGRAM ===" )
        
        print(f"🔑 Получаем токен бота...")
        bot_token = get_bot_token()
        if not bot_token:
            print(f"❌ Токен бота не найден!")
            return False, "Токен бота не найден"
        
        print(f"✅ Токен получен: {bot_token[:20]}...{bot_token[-10:]}")
        
        # Тестируем соединение через getMe
        api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        print(f"🔗 URL для тестирования: {api_url[:50]}...getMe")
        
        print(f"🚀 Отправляем тестовый запрос...")
        response = requests.get(api_url, timeout=10)
        
        print(f"📥 Получен ответ:")
        print(f"   Статус код: {response.status_code}")
        print(f"   Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Содержимое ответа: {result}")
            if result.get('ok'):
                bot_info = result.get('result', {})
                bot_name = bot_info.get('first_name', 'Unknown')
                bot_username = bot_info.get('username', 'Unknown')
                bot_id = bot_info.get('id', 'Unknown')
                success_msg = f"✅ Бот подключен: {bot_name} (@{bot_username}), ID: {bot_id}"
                print(success_msg)
                return True, success_msg
            else:
                error_msg = result.get('description', 'Unknown')
                error_code = result.get('error_code', 'Unknown')
                print(f"❌ API ошибка:")
                print(f"   Код: {error_code}")
                print(f"   Описание: {error_msg}")
                return False, f"❌ API ошибка: {error_msg}"
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            try:
                response_text = response.text
                print(f"   Текст ответа: {response_text}")
            except:
                print(f"   Текст ответа не доступен")
            return False, f"❌ HTTP ошибка: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Ошибка соединения: {str(e)}")
        print(f"📋 Трассировка ошибки:")
        print(traceback.format_exc())
        return False, f"❌ Ошибка соединения: {str(e)}"

def send_message_to_telegram(user_id: int, text: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Отправить текстовое сообщение пользователю
    
    Args:
        user_id: Telegram ID пользователя
        text: Текст сообщения
    
    Returns:
        Tuple[bool, Dict]: (успех, данные ответа или ошибка)
    """
    try:
        bot_token = get_bot_token()
        if not bot_token:
            return False, {"error": "Токен Telegram бота не найден"}
        
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': user_id,
            'text': text[:4096],  # Telegram лимит
            'parse_mode': 'HTML'
        }
        
        response = requests.post(api_url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return True, result.get('result', {})
            else:
                return False, {"error": result.get('description', 'Неизвестная ошибка')}
        else:
            return False, {"error": f"HTTP ошибка: {response.status_code}"}
            
    except Exception as e:
        return False, {"error": f"Ошибка отправки сообщения: {str(e)}"}

# Функция для проверки доступности пользователя
def check_user_availability(user_id: int) -> Tuple[bool, str]:
    """
    Проверить, доступен ли пользователь для отправки сообщений
    
    Args:
        user_id: Telegram ID пользователя
    
    Returns:
        Tuple[bool, str]: (доступен, статус)
    """
    try:
        # Отправляем тестовое сообщение
        success, response = send_message_to_telegram(
            user_id, 
            "🔍 Тест соединения от GrantService"
        )
        
        if success:
            return True, "Пользователь доступен"
        else:
            error = response.get('error', 'Неизвестная ошибка')
            if 'blocked' in error.lower():
                return False, "Бот заблокирован пользователем"
            elif 'not found' in error.lower():
                return False, "Пользователь не найден"
            else:
                return False, f"Ошибка: {error}"
                
    except Exception as e:
        return False, f"Ошибка проверки: {str(e)}"

if __name__ == "__main__":
    # Тестирование модуля
    print("🧪 Тестирование Telegram Sender")
    
    # Тест подключения
    success, message = test_telegram_connection()
    print(f"Тест подключения: {message}")
    
    if success:
        print("\n✅ Модуль готов к работе!")
    else:
        print("\n❌ Требуется настройка токена бота")