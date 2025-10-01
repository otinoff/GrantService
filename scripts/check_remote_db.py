#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для удаленной проверки базы данных на сервере
Использование: python3 check_remote_db.py
"""

import subprocess
import sys

def run_remote_command(host, command):
    """Выполнение команды на удаленном сервере"""
    try:
        cmd = ['ssh', f'root@{host}', command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)

def check_remote_database():
    """Проверка базы данных на удаленном сервере"""
    host = "5.35.88.251"
    db_path = "/var/GrantService/data/grant_service.db"
    
    print(f"🔍 Проверка базы данных на сервере {host}")
    print("=" * 60)
    
    # 1. Проверяем существование файла
    print("1️⃣ Проверка существования файла БД...")
    code, out, err = run_remote_command(host, f"ls -la {db_path}")
    if code == 0:
        print(f"✅ Файл БД найден:")
        print(out.strip())
    else:
        print(f"❌ Файл БД не найден: {err}")
        return False
    
    print()
    
    # 2. Проверяем время изменения
    print("2️⃣ Время последнего изменения...")
    code, out, err = run_remote_command(host, f"stat {db_path}")
    if code == 0:
        print("✅ Информация о файле:")
        for line in out.split('\n'):
            if 'Modify:' in line or 'Size:' in line:
                print(f"  {line.strip()}")
    
    print()
    
    # 3. Проверяем содержимое БД
    print("3️⃣ Содержимое базы данных...")
    
    # Количество активных вопросов
    sql_cmd = f"sqlite3 {db_path} \"SELECT COUNT(*) FROM questions WHERE is_active = 1;\""
    code, out, err = run_remote_command(host, sql_cmd)
    if code == 0:
        active_questions = out.strip()
        print(f"📊 Активных вопросов: {active_questions}")
    else:
        print(f"❌ Ошибка запроса активных вопросов: {err}")
    
    # Количество вопросов с подсказками
    sql_cmd = f"sqlite3 {db_path} \"SELECT COUNT(*) FROM questions WHERE hint_text IS NOT NULL AND hint_text != '';\""
    code, out, err = run_remote_command(host, sql_cmd)
    if code == 0:
        hints_count = out.strip()
        print(f"💡 Вопросов с подсказками: {hints_count}")
    else:
        print(f"❌ Ошибка запроса подсказок: {err}")
    
    # Общее количество вопросов
    sql_cmd = f"sqlite3 {db_path} \"SELECT COUNT(*) FROM questions;\""
    code, out, err = run_remote_command(host, sql_cmd)
    if code == 0:
        total_questions = out.strip()
        print(f"📝 Всего вопросов: {total_questions}")
    else:
        print(f"❌ Ошибка запроса общего количества: {err}")
    
    # Количество заявок
    sql_cmd = f"sqlite3 {db_path} \"SELECT COUNT(*) FROM grant_applications;\""
    code, out, err = run_remote_command(host, sql_cmd)
    if code == 0:
        apps_count = out.strip()
        print(f"📋 Всего заявок: {apps_count}")
    else:
        print(f"❌ Ошибка запроса заявок: {err}")
    
    print()
    
    # 4. Проверяем процессы бота
    print("4️⃣ Процессы бота на сервере...")
    code, out, err = run_remote_command(host, "pgrep -f main.py")
    if code == 0 and out.strip():
        pids = out.strip().split('\n')
        print(f"🤖 Найдены процессы бота: {', '.join(pids)}")
        
        # Проверяем время запуска процессов
        for pid in pids:
            code2, out2, err2 = run_remote_command(host, f"ps -o pid,etime,cmd -p {pid}")
            if code2 == 0:
                print(f"  PID {pid}:")
                lines = out2.strip().split('\n')
                if len(lines) > 1:
                    print(f"    {lines[1]}")
    else:
        print("❌ Процессы бота не найдены")
    
    print()
    
    # 5. Показываем первые 3 активных вопроса для проверки
    print("5️⃣ Примеры активных вопросов...")
    sql_cmd = f"sqlite3 {db_path} \"SELECT question_number, question_text, CASE WHEN hint_text IS NOT NULL AND hint_text != '' THEN 'ДА' ELSE 'НЕТ' END as has_hint FROM questions WHERE is_active = 1 ORDER BY question_number LIMIT 3;\""
    code, out, err = run_remote_command(host, sql_cmd)
    if code == 0:
        lines = out.strip().split('\n')
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    q_num = parts[0]
                    q_text = parts[1][:50] + "..." if len(parts[1]) > 50 else parts[1]
                    has_hint = parts[2]
                    print(f"  {q_num}. {q_text} | Подсказка: {has_hint}")
    
    print()
    print("✅ Проверка завершена")
    
    return True

def check_github_actions():
    """Проверка последних GitHub Actions"""
    print("\n🔄 Информация о GitHub Actions:")
    print("Для проверки автодеплоя зайдите на:")
    print("https://github.com/otinoff/GrantService/actions")
    print("Там можно посмотреть:")
    print("- Время последнего деплоя")
    print("- Лог деплоя")
    print("- Есть ли автоперезапуск бота")

if __name__ == "__main__":
    try:
        success = check_remote_database()
        check_github_actions()
        
        if success:
            print("\n💡 Если бот показывает старые данные:")
            print("1. Перезапустите бот командой: ssh root@5.35.88.251 'pkill -f main.py && cd /var/GrantService/telegram-bot && nohup python3 main.py &'")
            print("2. Или добавьте перезапуск в GitHub Actions")
        
    except KeyboardInterrupt:
        print("\n⏹️ Проверка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")