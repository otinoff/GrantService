#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование механизма отправки грантов
"""

import sys
import os
from pathlib import Path

# Добавляем пути для импортов
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def test_database_setup():
    """Тестирование настройки базы данных"""
    print("[ТЕСТ] Тестирование базы данных...")
    
    try:
        from data.database.models import GrantServiceDatabase
        
        # Определяем путь к базе данных
        if os.name == 'nt':  # Windows
            db_path = str(current_dir / "data" / "grantservice.db")
        else:  # Linux
            db_path = "/var/GrantService/data/grantservice.db"
        
        db = GrantServiceDatabase(db_path)
        
        # Проверяем создание таблицы sent_documents
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sent_documents'")
            result = cursor.fetchone()
            
            if result:
                print("[OK] Таблица sent_documents создана")
                
                # Проверяем структуру таблицы
                cursor.execute("PRAGMA table_info(sent_documents)")
                columns = cursor.fetchall()
                expected_columns = ['id', 'user_id', 'grant_application_id', 'file_path', 
                                  'file_name', 'file_size', 'admin_comment', 'delivery_status']
                
                column_names = [col[1] for col in columns]
                missing_columns = [col for col in expected_columns if col not in column_names]
                
                if not missing_columns:
                    print("[OK] Структура таблицы корректна")
                else:
                    print(f"[ОШИБКА] Отсутствуют колонки: {missing_columns}")
            else:
                print("[ОШИБКА] Таблица sent_documents не найдена")
        
        # Тестируем новые методы
        users = db.get_users_for_sending()
        print(f"[OK] Найдено пользователей для отправки: {len(users)}")
        
        # Показываем первых несколько пользователей
        for i, user in enumerate(users[:3]):
            print(f"   [USER] {user.get('display_name', 'Неизвестный')}")
            if i >= 2:  # Показываем только первых 3
                break
        
        return True
        
    except Exception as e:
        print(f"[ОШИБКА] Ошибка тестирования БД: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_connection():
    """Тестирование соединения с Telegram"""
    print("\n[ТЕСТ] Тестирование Telegram соединения...")
    
    try:
        web_admin_path = current_dir / "web-admin"
        if str(web_admin_path) not in sys.path:
            sys.path.insert(0, str(web_admin_path))
        from utils.telegram_sender import test_telegram_connection
        
        success, message = test_telegram_connection()
        print(f"   {message}")
        return success
        
    except Exception as e:
        print(f"[ОШИБКА] Ошибка тестирования Telegram: {e}")
        return False

def test_file_operations():
    """Тестирование файловых операций"""
    print("\n[ТЕСТ] Тестирование файловых операций...")
    
    try:
        # Проверяем папку ready_grants
        ready_grants_dir = current_dir / "data" / "ready_grants"
        
        if ready_grants_dir.exists():
            print("[OK] Папка ready_grants существует")
            
            # Считаем файлы
            files = list(ready_grants_dir.glob("*"))
            print(f"   [INFO] Файлов в папке: {len(files)}")
            
            # Создаем тестовый файл
            test_file = ready_grants_dir / "test_grant.txt"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("Тестовая грантовая заявка\nСоздана для проверки системы отправки.")
            
            print(f"[OK] Создан тестовый файл: {test_file.name}")
            
            return True
        else:
            print("[ОШИБКА] Папка ready_grants не найдена")
            return False
            
    except Exception as e:
        print(f"[ОШИБКА] Ошибка файловых операций: {e}")
        return False

def test_applications_export():
    """Тестирование экспорта заявок"""
    print("\n[ТЕСТ] Тестирование экспорта заявок...")
    
    try:
        from data.database.models import GrantServiceDatabase
        
        # Определяем путь к базе данных
        if os.name == 'nt':  # Windows
            db_path = str(current_dir / "data" / "grantservice.db")
        else:  # Linux
            db_path = "/var/GrantService/data/grantservice.db"
        
        db = GrantServiceDatabase(db_path)
        
        # Получаем список заявок
        applications = db.get_all_applications(limit=5)
        print(f"[OK] Найдено заявок: {len(applications)}")
        
        if applications:
            for app in applications[:3]:
                print(f"   [APP] {app['application_number']} - {app['title'][:50]}...")
            
            # Тестируем экспорт первой заявки
            if applications:
                web_admin_path = current_dir / "web-admin"
                if str(web_admin_path) not in sys.path:
                    sys.path.insert(0, str(web_admin_path))
                from utils.telegram_sender import export_application_to_pdf
                
                first_app = applications[0]
                exported_file = export_application_to_pdf(first_app['application_number'])
                
                if exported_file and os.path.exists(exported_file):
                    print(f"[OK] Заявка экспортирована: {os.path.basename(exported_file)}")
                    return True
                else:
                    print("[ОШИБКА] Ошибка экспорта заявки")
                    return False
        else:
            print("[INFO] Заявки для тестирования не найдены")
            return True
            
    except Exception as e:
        print(f"[ОШИБКА] Ошибка тестирования экспорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_send_document():
    """Тестирование отправки документа"""
    print("\n[ТЕСТ] Тестирование отправки документа...")
    
    try:
        # Добавляем путь к web-admin для импорта
        web_admin_path = current_dir / "web-admin"
        if str(web_admin_path) not in sys.path:
            sys.path.insert(0, str(web_admin_path))
        
        from utils.telegram_sender import send_document_to_telegram
        from data.database.models import GrantServiceDatabase
        
        # Определяем путь к базе данных
        if os.name == 'nt':  # Windows
            db_path = str(current_dir / "data" / "grantservice.db")
        else:  # Linux
            db_path = "/var/GrantService/data/grantservice.db"
        
        db = GrantServiceDatabase(db_path)
        
        # Получаем первого пользователя для тестирования
        users = db.get_users_for_sending()
        if not users:
            print("[SKIP] Нет пользователей для тестирования")
            return True  # Не считаем это ошибкой
        
        test_user = users[0]
        user_id = test_user['telegram_id']
        
        # Создаем тестовый файл
        ready_grants_dir = current_dir / "data" / "ready_grants"
        test_file = ready_grants_dir / "test_document_sending.docx"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Тестовый документ для отправки через Telegram Bot API")
        
        print(f"[INFO] Тестируем отправку файла {test_file.name} пользователю {user_id}")
        
        # Пробуем отправить документ
        success, response = send_document_to_telegram(
            user_id=user_id,
            file_path=str(test_file),
            caption="🧪 Тестовая отправка документа от GrantService"
        )
        
        if success:
            print(f"[OK] Документ успешно отправлен пользователю {user_id}")
            return True
        else:
            print(f"[FAIL] Ошибка отправки документа: {response.get('error', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        print(f"[ОШИБКА] Ошибка тестирования отправки: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция тестирования"""
    print("ТЕСТИРОВАНИЕ МЕХАНИЗМА ОТПРАВКИ ГРАНТОВ")
    print("=" * 60)
    
    # Добавляем информацию о системе
    print(f"[INFO] Операционная система: {os.name}")
    print(f"[INFO] Текущая директория: {current_dir}")
    print(f"[INFO] Python версия: {sys.version}")
    print("=" * 60)
    
    results = {
        'database': test_database_setup(),
        'telegram': test_telegram_connection(),
        'files': test_file_operations(),
        'export': test_applications_export(),
        'send_document': test_send_document()
    }
    
    print("\n" + "=" * 60)
    print("[РЕЗУЛЬТАТЫ] РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "[OK] ПРОШЕЛ" if result else "[FAIL] ПРОВАЛЕН"
        print(f"   {test_name.upper()}: {status}")
    
    print(f"\n[ИТОГО] ИТОГО: {passed_tests}/{total_tests} тестов прошли успешно")
    
    if passed_tests == total_tests:
        print("[SUCCESS] ВСЕ ТЕСТЫ ПРОШЛИ! Система готова к работе.")
    elif passed_tests >= total_tests - 1:
        print("[WARNING] Почти все тесты прошли. Система почти готова к работе.")
    else:
        print("[WARNING] Некоторые тесты провалились. Требуется дополнительная настройка.")
    
    print("\n[HELP] СЛЕДУЮЩИЕ ШАГИ:")
    print("   1. Запустите веб-админ панель: streamlit run web-admin/app_main.py")
    print("   2. Перейдите на страницу '📤 Отправка грантов'")
    print("   3. Выберите пользователя и документ для отправки")
    print("   4. Протестируйте отправку")
    
    print("\n[DEBUG] ОТЛАДОЧНАЯ ИНФОРМАЦИЯ:")
    print("   - Если видите HTTP ошибку 401, проверьте токен бота")
    print("   - Убедитесь что бот запущен и имеет правильные права")
    print("   - Проверьте что пользователь начинал диалог с ботом")

if __name__ == "__main__":
    main()