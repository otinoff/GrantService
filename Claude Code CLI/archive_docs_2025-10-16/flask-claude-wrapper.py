#!/usr/bin/env python3
"""
Простая Flask обертка для Claude Code
"""

import subprocess
import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import threading
import time

app = Flask(__name__)
CORS(app)  # Разрешить CORS для всех доменов

# Конфигурация
API_KEY = os.getenv("API_KEY", "your-secure-api-key")
CLAUDE_TIMEOUT = 300
WORKING_DIR = os.getenv("CLAUDE_WORKING_DIR", "/tmp/claude_sessions")

# Создание рабочей директории
Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)

# Простое управление сессиями
sessions = {}

def require_auth(f):
    """Декоратор для проверки API ключа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Отсутствует Authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        if token != API_KEY:
            return jsonify({"error": "Неверный API ключ"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def execute_claude_command(command, working_dir):
    """Выполнение команды Claude Code"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=working_dir,
            env=os.environ.copy()
        )
        
        if result.returncode != 0:
            return None, f"Ошибка Claude Code: {result.stderr}"
        
        return result.stdout.strip(), None
        
    except subprocess.TimeoutExpired:
        return None, "Timeout: команда выполнялась слишком долго"
    except Exception as e:
        return None, f"Ошибка выполнения: {str(e)}"

def create_session(session_id=None):
    """Создание новой сессии"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    session_dir = Path(WORKING_DIR) / session_id
    session_dir.mkdir(exist_ok=True)
    
    sessions[session_id] = {
        "id": session_id,
        "directory": str(session_dir),
        "created_at": datetime.now(),
        "last_activity": datetime.now()
    }
    
    return session_id

def get_session(session_id):
    """Получение сессии"""
    session = sessions.get(session_id)
    if session:
        session["last_activity"] = datetime.now()
    return session

@app.route('/health')
def health():
    """Проверка здоровья сервиса"""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        claude_status = "available" if result.returncode == 0 else "unavailable"
        
        return jsonify({
            "status": "healthy",
            "claude_code": claude_status,
            "active_sessions": len(sessions),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/chat', methods=['POST'])
@require_auth
def chat():
    """Чат с Claude Code"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "Отсутствует поле 'message'"}), 400
    
    message = data['message']
    session_id = data.get('session_id')
    
    # Создание или получение сессии
    if not session_id or session_id not in sessions:
        session_id = create_session(session_id)
    
    session = get_session(session_id)
    working_dir = session["directory"]
    
    # Формирование команды
    escaped_message = message.replace('"', '\\"').replace('\n', '\\n')
    command = f'echo "{escaped_message}" | claude'
    
    # Выполнение команды
    output, error = execute_claude_command(command, working_dir)
    
    if error:
        return jsonify({
            "error": error,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }), 500
    
    return jsonify({
        "response": output,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    })

@app.route('/code', methods=['POST'])
@require_auth
def execute_code():
    """Выполнение кода через Claude Code"""
    data = request.get_json()
    
    if not data or 'code' not in data:
        return jsonify({"error": "Отсутствует поле 'code'"}), 400
    
    code = data['code']
    language = data.get('language', 'python')
    session_id = data.get('session_id')
    
    # Создание или получение сессии
    if not session_id or session_id not in sessions:
        session_id = create_session(session_id)
    
    session = get_session(session_id)
    working_dir = session["directory"]
    
    # Создание временного файла
    file_ext = {
        "python": ".py",
        "javascript": ".js", 
        "bash": ".sh"
    }.get(language, ".txt")
    
    temp_file = Path(working_dir) / f"temp_code_{uuid.uuid4().hex[:8]}{file_ext}"
    
    try:
        # Запись кода в файл
        temp_file.write_text(code, encoding='utf-8')
        
        # Команда для выполнения
        command = f'claude "Выполни код из файла {temp_file.name}"'
        
        # Выполнение
        output, error = execute_claude_command(command, working_dir)
        
        if error:
            return jsonify({
                "error": error,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }), 500
        
        return jsonify({
            "result": output,
            "session_id": session_id,
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
    finally:
        # Очистка временного файла
        if temp_file.exists():
            temp_file.unlink()

@app.route('/sessions', methods=['GET'])
@require_auth
def list_sessions():
    """Список активных сессий"""
    session_list = []
    for sid, session in sessions.items():
        session_list.append({
            "session_id": sid,
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat()
        })
    
    return jsonify({
        "sessions": session_list,
        "total": len(sessions)
    })

@app.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def delete_session(session_id):
    """Удаление сессии"""
    if session_id not in sessions:
        return jsonify({"error": "Сессия не найдена"}), 404
    
    # Очистка директории сессии
    session_dir = Path(sessions[session_id]["directory"])
    if session_dir.exists():
        import shutil
        shutil.rmtree(session_dir, ignore_errors=True)
    
    del sessions[session_id]
    
    return jsonify({"message": f"Сессия {session_id} удалена"})

@app.route('/')
def index():
    """Корневая страница"""
    return jsonify({
        "service": "Claude Code API Wrapper (Flask)",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health - проверка здоровья",
            "/chat - чат с Claude",
            "/code - выполнение кода",
            "/sessions - список сессий"
        ],
        "timestamp": datetime.now().isoformat()
    })

def cleanup_old_sessions():
    """Фоновая очистка старых сессий"""
    while True:
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, session_data in sessions.items():
                # Удаление сессий старше 1 часа
                if (current_time - session_data["last_activity"]).seconds > 3600:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                if session_id in sessions:
                    session_dir = Path(sessions[session_id]["directory"])
                    if session_dir.exists():
                        import shutil
                        shutil.rmtree(session_dir, ignore_errors=True)
                    del sessions[session_id]
                    
            time.sleep(600)  # Проверка каждые 10 минут
            
        except Exception as e:
            print(f"Ошибка очистки сессий: {e}")
            time.sleep(600)

if __name__ == '__main__':
    # Запуск фоновой очистки
    cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
    cleanup_thread.start()
    
    # Настройки запуска
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"""
╭─────────────────────────────────────╮
│   Claude Code API Wrapper (Flask)  │
├─────────────────────────────────────┤
│  Host: {host:<25} │
│  Port: {port:<25} │
│  Debug: {debug:<24} │
╰─────────────────────────────────────╯
    """)
    
    app.run(host=host, port=port, debug=debug)