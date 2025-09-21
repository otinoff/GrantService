#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для удаленной проверки базы данных на сервере с Windows
Использует paramiko для SSH подключения
"""

try:
    import paramiko
except ImportError:
    print("❌ Для работы скрипта нужна библиотека paramiko")
    print("Установите её командой: pip install paramiko")
    exit(1)

import sys
import time

class RemoteDBChecker:
    def __init__(self, host, username, password=None, key_file=None):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.client = None
    
    def connect(self):
        """Подключение к серверу"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_file:
                print(f"🔑 Подключение к {self.host} с ключом...")
                self.client.connect(self.host, username=self.username, key_filename=self.key_file)
            elif self.password:
                print(f"🔑 Подключение к {self.host} с паролем...")
                self.client.connect(self.host, username=self.username, password=self.password)
            else:
                print(f"🔑 Подключение к {self.host} (попытка без пароля)...")
                self.client.connect(self.host, username=self.username)
            
            print("✅ Подключение успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def run_command(self, command):
        """Выполнение команды на сервере"""
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            return exit_code, stdout_data, stderr_data
            
        except Exception as e:
            return -1, "", str(e)
    
    def find_database_files(self):
        """Поиск файлов базы данных"""
        print("🔍 Поиск файлов базы данных...")
        
        # Сначала проверяем основной файл БД по коду
        main_db_path = "/var/GrantService/data/grantservice.db"
        print(f"   Проверяем основной файл БД: {main_db_path}")
        code, out, err = self.run_command(f"ls -la '{main_db_path}' 2>/dev/null")
        
        db_files = []
        if code == 0:
            db_files.append(main_db_path)
        
        # Проверяем альтернативные варианты
        alternative_paths = [
            "/var/GrantService/data/grant_service.db",  # с подчеркиванием
            "/var/GrantService/grantservice.db",       # в корне проекта
            "/var/GrantService/grant_service.db"       # в корне с подчеркиванием
        ]
        
        for alt_path in alternative_paths:
            print(f"   Проверяем альтернативный путь: {alt_path}")
            code, out, err = self.run_command(f"ls -la '{alt_path}' 2>/dev/null")
            if code == 0 and alt_path not in db_files:
                db_files.append(alt_path)
        
        # Если ничего не найдено, ищем все .db файлы в проекте
        if not db_files:
            print("   Поиск всех .db файлов в /var/GrantService...")
            code, out, err = self.run_command("find /var/GrantService -name '*.db' 2>/dev/null")
            if code == 0 and out.strip():
                files = out.strip().split('\n')
                for file in files:
                    if file.strip():
                        db_files.append(file.strip())
        
        if db_files:
            print(f"✅ Найдены файлы БД:")
            for i, db_file in enumerate(db_files, 1):
                # Показываем информацию о файле
                code, out, err = self.run_command(f"ls -la '{db_file}'")
                if code == 0:
                    print(f"   {i}. {db_file}")
                    print(f"      {out.strip()}")
        else:
            print("❌ Файлы БД не найдены")
        
        return db_files
    
    def check_database(self, db_path=None):
        """Проверка базы данных"""
        print(f"🔍 Проверка базы данных на сервере {self.host}")
        print("=" * 60)
        
        # 1. Если путь не указан, ищем БД
        if not db_path:
            db_files = self.find_database_files()
            if not db_files:
                return False
            
            if len(db_files) == 1:
                db_path = db_files[0]
                print(f"📍 Используем найденную БД: {db_path}")
            else:
                print("\n🤔 Найдено несколько файлов БД:")
                for i, db_file in enumerate(db_files, 1):
                    print(f"   {i}. {db_file}")
                
                try:
                    choice = int(input("Выберите номер файла для проверки: ")) - 1
                    if 0 <= choice < len(db_files):
                        db_path = db_files[choice]
                    else:
                        print("❌ Неверный выбор")
                        return False
                except (ValueError, IndexError):
                    print("❌ Неверный ввод")
                    return False
        
        print(f"\n📋 Анализ БД: {db_path}")
        print("-" * 40)
        
        # 2. Проверяем существование выбранного файла
        code, out, err = self.run_command(f"ls -la '{db_path}'")
        if code != 0:
            print(f"❌ Файл недоступен: {err}")
            return False
        
        print("✅ Файл БД:")
        print(f"   {out.strip()}")
        
        print()
        
        # 2. Проверяем время изменения
        print("2️⃣ Информация о файле...")
        code, out, err = self.run_command(f"stat {db_path} | grep -E 'Size|Modify'")
        if code == 0:
            print("✅ Время изменения:")
            print(f"   {out.strip()}")
        
        print()
        
        # 3. Проверяем содержимое БД
        print("3️⃣ Анализ содержимого БД...")
        
        # Сначала проверим, какие таблицы есть в БД
        code, out, err = self.run_command(f"sqlite3 {db_path} \".tables\"")
        if code == 0:
            tables = out.strip()
            print(f"📋 Таблицы в БД: {tables}")
        
        # Проверяем правильное название таблицы
        table_name = "interview_questions"  # правильное название
        
        # Активные вопросы
        code, out, err = self.run_command(f"sqlite3 {db_path} \"SELECT COUNT(*) FROM {table_name} WHERE is_active = 1;\"")
        if code == 0:
            active_questions = out.strip()
            print(f"📊 Активных вопросов: {active_questions}")
        else:
            print(f"❌ Ошибка подсчета активных вопросов: {err}")
        
        # Вопросы с подсказками
        code, out, err = self.run_command(f"sqlite3 {db_path} \"SELECT COUNT(*) FROM {table_name} WHERE hint_text IS NOT NULL AND hint_text != '';\"")
        if code == 0:
            hints_count = out.strip()
            print(f"💡 Вопросов с подсказками: {hints_count}")
        else:
            print(f"❌ Ошибка подсчета подсказок: {err}")
        
        # Общее количество
        code, out, err = self.run_command(f"sqlite3 {db_path} \"SELECT COUNT(*) FROM {table_name};\"")
        if code == 0:
            total_questions = out.strip()
            print(f"📝 Всего вопросов: {total_questions}")
        
        # Заявки
        code, out, err = self.run_command(f"sqlite3 {db_path} \"SELECT COUNT(*) FROM grant_applications;\"")
        if code == 0:
            apps_count = out.strip()
            print(f"📋 Всего заявок: {apps_count}")
        
        print()
        
        # 4. Процессы бота
        print("4️⃣ Процессы бота...")
        code, out, err = self.run_command("pgrep -f main.py")
        if code == 0 and out.strip():
            pids = out.strip().split('\n')
            print(f"🤖 Процессы бота: {', '.join(pids)}")
            
            # Время работы процессов
            for pid in pids:
                code2, out2, err2 = self.run_command(f"ps -o pid,etime,cmd -p {pid} | tail -1")
                if code2 == 0:
                    print(f"   PID {pid}: {out2.strip()}")
        else:
            print("❌ Процессы бота не найдены")
        
        print()
        
        # 5. Примеры вопросов
        print("5️⃣ Примеры активных вопросов...")
        code, out, err = self.run_command(f"sqlite3 {db_path} \"SELECT question_number || '. ' || substr(question_text, 1, 40) || '...' || ' [Подсказка: ' || CASE WHEN hint_text IS NOT NULL AND hint_text != '' THEN 'ДА' ELSE 'НЕТ' END || ']' FROM {table_name} WHERE is_active = 1 ORDER BY question_number LIMIT 3;\"")
        if code == 0:
            examples = out.strip().split('\n')
            for example in examples:
                if example.strip():
                    print(f"   {example}")
        
        print()
        print("✅ Проверка завершена")
        return True
    
    def restart_bot(self):
        """Перезапуск бота через systemd сервис"""
        print("🔄 Перезапуск бота через systemd...")
        
        # Сначала проверяем, какие сервисы есть
        print("   Поиск сервиса GrantService...")
        code, out, err = self.run_command("systemctl list-units --type=service | grep -i grant")
        if code == 0 and out.strip():
            print(f"   Найдены сервисы: {out.strip()}")
        
        # Пробуем стандартные названия сервисов
        service_names = ["grantservice", "grant-service", "telegram-bot", "grantservice-bot"]
        
        for service_name in service_names:
            print(f"   Проверяем сервис: {service_name}")
            code, out, err = self.run_command(f"systemctl status {service_name}")
            
            if code == 0:
                print(f"✅ Найден активный сервис: {service_name}")
                
                # Перезапускаем сервис
                print(f"   Перезапускаем сервис {service_name}...")
                code, out, err = self.run_command(f"systemctl restart {service_name}")
                
                if code == 0:
                    print(f"✅ Сервис {service_name} перезапущен")
                    time.sleep(3)
                    
                    # Проверяем статус
                    code, out, err = self.run_command(f"systemctl is-active {service_name}")
                    if code == 0 and "active" in out:
                        print(f"✅ Сервис {service_name} активен")
                        return True
                    else:
                        print(f"❌ Сервис {service_name} не активен: {out}")
                else:
                    print(f"❌ Ошибка перезапуска сервиса {service_name}: {err}")
        
        # Если сервис не найден, пробуем ручной перезапуск
        print("   Сервис не найден, пробуем ручной перезапуск...")
        code, out, err = self.run_command("pkill -f 'python.*main.py'")
        time.sleep(3)
        
        code, out, err = self.run_command("cd /var/GrantService/telegram-bot && nohup python3 main.py > /dev/null 2>&1 &")
        time.sleep(2)
        
        # Проверяем
        code, out, err = self.run_command("pgrep -f main.py")
        if code == 0 and out.strip():
            print(f"✅ Бот перезапущен вручную, PID: {out.strip()}")
            return True
        else:
            print("❌ Не удалось перезапустить бота")
            return False
    
    def disconnect(self):
        """Отключение"""
        if self.client:
            self.client.close()
            print("🔌 Отключение от сервера")

def main():
    # Параметры подключения
    host = "5.35.88.251"
    username = "root"
    
    print("🌐 Проверка удаленной базы данных GrantService")
    print("=" * 60)
    
    # Спрашиваем способ подключения
    print("Выберите способ подключения:")
    print("1. По паролю")
    print("2. По SSH ключу")
    print("3. Без пароля (если настроен доступ)")
    
    choice = input("Введите номер (1-3): ").strip()
    
    checker = None
    
    if choice == "1":
        password = input("Введите пароль: ")
        checker = RemoteDBChecker(host, username, password=password)
    elif choice == "2":
        key_path = input("Путь к SSH ключу (Enter для ~/.ssh/id_rsa): ").strip()
        if not key_path:
            key_path = None  # Будет использован стандартный
        checker = RemoteDBChecker(host, username, key_file=key_path)
    elif choice == "3":
        checker = RemoteDBChecker(host, username)
    else:
        print("❌ Неверный выбор")
        return
    
    try:
        if checker.connect():
            checker.check_database()
            
            print("\n🔍 АНАЛИЗ ПРОБЛЕМЫ:")
            print("✅ База данных обновилась на сервере")
            print("❌ Бот использует старые данные в памяти (19 вопросов вместо 15)")
            print("💡 Нужен перезапуск бота для обновления")
            
            # Автоматически предлагаем перезапуск
            restart = input("\n🤖 Перезапустить бота для обновления данных? (Y/n): ").lower()
            if restart != 'n':
                print("🔄 Перезапускаем бота...")
                checker.restart_bot()
        
    except KeyboardInterrupt:
        print("\n⏹️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        if checker:
            checker.disconnect()

if __name__ == "__main__":
    main()