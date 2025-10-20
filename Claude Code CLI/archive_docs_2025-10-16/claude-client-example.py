#!/usr/bin/env python3
"""
Пример клиента для Claude Code API Wrapper
"""

import requests
import json
import time
from typing import Optional, Dict, Any

class ClaudeCodeClient:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session_id: Optional[str] = None
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}' if api_key else None
        }
        
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья API"""
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "unhealthy"}
    
    def chat(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Отправка сообщения в Claude Code"""
        try:
            payload = {
                "message": message,
                "session_id": session_id or self.session_id
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            # Сохранение session_id для последующих запросов
            if not self.session_id:
                self.session_id = result.get('session_id')
                
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def execute_code(self, code: str, language: str = "python", 
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """Выполнение кода через Claude Code"""
        try:
            payload = {
                "code": code,
                "language": language,
                "session_id": session_id or self.session_id
            }
            
            response = requests.post(
                f"{self.base_url}/code",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            if not self.session_id:
                self.session_id = result.get('session_id')
                
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def list_sessions(self) -> Dict[str, Any]:
        """Получение списка активных сессий"""
        try:
            response = requests.get(f"{self.base_url}/sessions", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Удаление сессии"""
        try:
            response = requests.delete(
                f"{self.base_url}/sessions/{session_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

def main():
    """Пример использования клиента"""
    # Настройка клиента
    client = ClaudeCodeClient(
        base_url="http://localhost:8000",
        api_key="your-secure-api-key"
    )
    
    print("🤖 Claude Code API Client - Демонстрация")
    print("=" * 50)
    
    # 1. Проверка здоровья API
    print("\n1. Проверка здоровья API:")
    health = client.health_check()
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    if health.get("status") != "healthy":
        print("❌ API недоступен!")
        return
    
    # 2. Простой чат
    print("\n2. Простой чат с Claude:")
    chat_response = client.chat("Привет! Как дела?")
    if "error" not in chat_response:
        print(f"Claude: {chat_response.get('response')}")
        print(f"Session ID: {chat_response.get('session_id')}")
    else:
        print(f"Ошибка: {chat_response['error']}")
    
    # 3. Выполнение Python кода
    print("\n3. Выполнение Python кода:")
    python_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Вычисление первых 10 чисел Фибоначчи
result = [fibonacci(i) for i in range(10)]
print("Числа Фибоначчи:", result)
"""
    
    code_response = client.execute_code(python_code, "python")
    if "error" not in code_response:
        print(f"Результат выполнения:")
        print(code_response.get('result'))
    else:
        print(f"Ошибка: {code_response['error']}")
    
    # 4. Программирование через чат
    print("\n4. Программирование через чат:")
    programming_request = """
Создай функцию на Python для сортировки списка строк по длине.
Функция должна принимать список строк и возвращать отсортированный список.
Также добавь пример использования.
"""
    
    prog_response = client.chat(programming_request)
    if "error" not in prog_response:
        print("Claude создал код:")
        print(prog_response.get('response'))
    else:
        print(f"Ошибка: {prog_response['error']}")
    
    # 5. Список сессий
    print("\n5. Активные сессии:")
    sessions = client.list_sessions()
    if "error" not in sessions:
        print(f"Всего сессий: {sessions.get('total')}")
        for session in sessions.get('sessions', []):
            print(f"  - {session['session_id']} (создана: {session['created_at']})")
    else:
        print(f"Ошибка: {sessions['error']}")
    
    print("\n✅ Демонстрация завершена!")

# Интерактивный режим
def interactive_mode():
    """Интерактивный чат с Claude"""
    client = ClaudeCodeClient(
        base_url="http://localhost:8000",
        api_key="your-secure-api-key"
    )
    
    print("🤖 Интерактивный чат с Claude Code")
    print("Введите 'quit' для выхода, 'code' для выполнения кода")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n👤 Вы: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'code':
                print("Введите код (завершите ввод пустой строкой):")
                code_lines = []
                while True:
                    line = input()
                    if line == "":
                        break
                    code_lines.append(line)
                
                if code_lines:
                    code = '\n'.join(code_lines)
                    language = input("Язык программирования [python]: ") or "python"
                    
                    result = client.execute_code(code, language)
                    if "error" not in result:
                        print(f"\n📄 Результат выполнения:")
                        print(result.get('result'))
                    else:
                        print(f"❌ Ошибка: {result['error']}")
                continue
            
            if not user_input:
                continue
                
            response = client.chat(user_input)
            if "error" not in response:
                print(f"\n🤖 Claude: {response.get('response')}")
            else:
                print(f"❌ Ошибка: {response['error']}")
                
        except KeyboardInterrupt:
            print("\n\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_mode()
    else:
        main()