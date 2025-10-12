#!/usr/bin/env python3
"""
Claude Code API Wrapper v2.0
Обертка для Claude Code, предоставляющая HTTP API интерфейс
+ НОВОЕ: WebSearch поддержка
"""

import asyncio
import subprocess
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Настройка приложения
app = FastAPI(
    title="Claude Code API Wrapper",
    description="HTTP API обертка для Claude Code с WebSearch",
    version="2.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничьте конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Аутентификация (простая)
security = HTTPBearer()

# Конфигурация
class Config:
    CLAUDE_TIMEOUT = 300  # 5 минут
    MAX_CONCURRENT_REQUESTS = 5
    API_KEY = os.getenv("API_KEY", "your-secure-api-key")
    CLAUDE_WORKING_DIR = os.getenv("CLAUDE_WORKING_DIR", "/tmp/claude_sessions")

config = Config()

# Семафор для ограничения параллельных запросов
request_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)

# Модели данных
class ChatRequest(BaseModel):
    message: str = Field(..., description="Сообщение для Claude")
    session_id: Optional[str] = Field(None, description="ID сессии (опционально)")
    model: Optional[str] = Field("sonnet", description="Модель Claude (sonnet/opus)")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Температура генерации")
    max_tokens: Optional[int] = Field(1000, ge=1, le=8000, description="Максимум токенов")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    model: str
    timestamp: datetime
    status: str = "success"

class CodeRequest(BaseModel):
    code: str = Field(..., description="Код для выполнения")
    language: str = Field("python", description="Язык программирования")
    session_id: Optional[str] = Field(None, description="ID сессии")

class CodeResponse(BaseModel):
    result: str
    session_id: str
    language: str
    timestamp: datetime
    status: str = "success"

# НОВОЕ: WebSearch модели
class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    allowed_domains: Optional[List[str]] = Field(None, description="Разрешённые домены")
    blocked_domains: Optional[List[str]] = Field(None, description="Заблокированные домены")
    session_id: Optional[str] = Field(None, description="ID сессии")
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Максимум результатов")

class WebSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    session_id: str
    timestamp: datetime
    status: str = "success"

class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    status: str

# Управление сессиями
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())

        session_dir = Path(config.CLAUDE_WORKING_DIR) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        self.sessions[session_id] = {
            "id": session_id,
            "directory": str(session_dir),
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "status": "active"
        }

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)

    def update_activity(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.now()

    def cleanup_session(self, session_id: str):
        if session_id in self.sessions:
            # Очистка временных файлов
            session_dir = Path(self.sessions[session_id]["directory"])
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir, ignore_errors=True)

            del self.sessions[session_id]

session_manager = SessionManager()

# Аутентификация
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != config.API_KEY:
        raise HTTPException(status_code=401, detail="Неверный API ключ")
    return credentials.credentials

# Claude Code интерфейс
class ClaudeCodeInterface:
    @staticmethod
    async def execute_command(command: str, working_dir: str, timeout: int = 300) -> tuple[str, str, int]:
        """Выполнение команды Claude Code"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=os.environ.copy()
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return (
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore'),
                process.returncode or 0
            )

        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            raise HTTPException(status_code=408, detail="Timeout: команда выполнялась слишком долго")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка выполнения: {str(e)}")

    @classmethod
    async def chat(cls, message: str, session_id: str, model: str = "sonnet") -> str:
        """Отправка сообщения в Claude Code"""
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        working_dir = session["directory"]

        # Формирование команды для Claude Code
        escaped_message = message.replace('"', '\\"').replace('\n', '\\n')
        command = f'echo "{escaped_message}" | claude'

        stdout, stderr, returncode = await cls.execute_command(
            command,
            working_dir,
            config.CLAUDE_TIMEOUT
        )

        if returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Claude Code ошибка: {stderr}"
            )

        session_manager.update_activity(session_id)
        return stdout.strip()

    @classmethod
    async def execute_code(cls, code: str, language: str, session_id: str) -> str:
        """Выполнение кода через Claude Code"""
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        working_dir = session["directory"]

        # Создание временного файла с кодом
        file_ext = {"python": ".py", "javascript": ".js", "bash": ".sh"}.get(language, ".txt")
        temp_file = Path(working_dir) / f"temp_code_{uuid.uuid4().hex[:8]}{file_ext}"

        try:
            temp_file.write_text(code, encoding='utf-8')

            # Команда для выполнения через Claude
            command = f'claude "Выполни код из файла {temp_file.name}"'

            stdout, stderr, returncode = await cls.execute_command(
                command,
                working_dir,
                config.CLAUDE_TIMEOUT
            )

            if returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка выполнения кода: {stderr}"
                )

            session_manager.update_activity(session_id)
            return stdout.strip()

        finally:
            # Очистка временного файла
            if temp_file.exists():
                temp_file.unlink()

    @classmethod
    async def websearch(
        cls,
        query: str,
        session_id: str,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        max_results: int = 10
    ) -> str:
        """
        НОВОЕ: WebSearch через Claude Code

        Использует встроенный WebSearch tool Claude Code CLI
        """
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        working_dir = session["directory"]

        # Формируем промпт с явным указанием использовать WebSearch
        prompt = f"""Use the WebSearch tool to search for: {query}

Search parameters:
- Query: {query}
"""

        if allowed_domains:
            domains_list = ", ".join(allowed_domains)
            prompt += f"- Only search in these domains: {domains_list}\n"

        if blocked_domains:
            blocked_list = ", ".join(blocked_domains)
            prompt += f"- Do NOT search in these domains: {blocked_list}\n"

        prompt += f"""- Maximum results: {max_results}

Return the results in JSON format:
{{
    "query": "{query}",
    "results": [
        {{
            "title": "Page title",
            "url": "Full URL",
            "snippet": "Content snippet (2-3 sentences)",
            "relevance": "high|medium|low"
        }}
    ]
}}

Use WebSearch tool to perform this search. Return ONLY valid JSON."""

        # Экранируем промпт для shell
        escaped_prompt = prompt.replace('"', '\\"').replace('\n', '\\n').replace('$', '\\$')

        # Вызываем Claude с явным указанием использовать WebSearch
        # ВАЖНО: --dangerously-skip-permissions для автоматического одобрения
        # --print для неинтерактивного режима
        command = f'echo "{escaped_prompt}" | claude --print --dangerously-skip-permissions'

        stdout, stderr, returncode = await cls.execute_command(
            command,
            working_dir,
            config.CLAUDE_TIMEOUT
        )

        if returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"WebSearch error: {stderr}"
            )

        session_manager.update_activity(session_id)
        return stdout.strip()

# API эндпоинты
@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Claude Code API Wrapper",
        "version": "2.0.0",
        "features": ["chat", "code", "websearch"],
        "status": "running",
        "timestamp": datetime.now()
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверка доступности Claude Code
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        claude_status = "available" if result.returncode == 0 else "unavailable"
        claude_version = result.stdout.strip() if result.returncode == 0 else None

        return {
            "status": "healthy",
            "claude_code": claude_status,
            "claude_version": claude_version,
            "active_sessions": len(session_manager.sessions),
            "features": ["chat", "code", "websearch"],
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Чат с Claude Code"""
    async with request_semaphore:
        session_id = request.session_id or session_manager.create_session()

        if not session_manager.get_session(session_id):
            session_id = session_manager.create_session(session_id)

        try:
            response = await ClaudeCodeInterface.chat(
                request.message,
                session_id,
                request.model
            )

            return ChatResponse(
                response=response,
                session_id=session_id,
                model=request.model,
                timestamp=datetime.now()
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/code", response_model=CodeResponse)
async def code_execution_endpoint(
    request: CodeRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Выполнение кода через Claude Code"""
    async with request_semaphore:
        session_id = request.session_id or session_manager.create_session()

        if not session_manager.get_session(session_id):
            session_id = session_manager.create_session(session_id)

        try:
            result = await ClaudeCodeInterface.execute_code(
                request.code,
                request.language,
                session_id
            )

            return CodeResponse(
                result=result,
                session_id=session_id,
                language=request.language,
                timestamp=datetime.now()
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions(token: str = Depends(verify_token)):
    """Список активных сессий"""
    sessions = []
    for session_id, session_data in session_manager.sessions.items():
        sessions.append(SessionInfo(
            session_id=session_id,
            created_at=session_data["created_at"],
            last_activity=session_data["last_activity"],
            status=session_data["status"]
        ))

    return {"sessions": sessions, "total": len(sessions)}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, token: str = Depends(verify_token)):
    """Удаление сессии"""
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session_manager.cleanup_session(session_id)
    return {"message": f"Сессия {session_id} удалена"}

@app.get("/models")
async def list_models(token: str = Depends(verify_token)):
    """Список доступных моделей"""
    return {
        "models": [
            {"id": "sonnet", "name": "Claude Sonnet 4.5", "description": "Быстрая модель для большинства задач"},
            {"id": "opus", "name": "Claude Opus 4", "description": "Мощная модель для сложных задач"}
        ]
    }

# НОВОЕ: WebSearch endpoint
@app.post("/websearch", response_model=WebSearchResponse)
async def websearch_endpoint(
    request: WebSearchRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    НОВОЕ: WebSearch через Claude Code

    Использует встроенный WebSearch tool для поиска информации.
    Поддерживает фильтрацию по доменам для получения RU-источников.
    """
    async with request_semaphore:
        session_id = request.session_id or session_manager.create_session()

        if not session_manager.get_session(session_id):
            session_id = session_manager.create_session(session_id)

        try:
            result_text = await ClaudeCodeInterface.websearch(
                query=request.query,
                session_id=session_id,
                allowed_domains=request.allowed_domains,
                blocked_domains=request.blocked_domains,
                max_results=request.max_results
            )

            # Парсим JSON из ответа Claude
            try:
                # Извлекаем JSON из ответа (может быть обернут в markdown)
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_text = result_text[json_start:json_end]
                    result_json = json.loads(json_text)
                    results = result_json.get("results", [])
                else:
                    raise ValueError("No JSON found in response")

            except (json.JSONDecodeError, ValueError) as e:
                # Если Claude вернул не JSON, пытаемся извлечь полезное
                print(f"Warning: Failed to parse JSON: {e}")
                print(f"Raw response: {result_text[:500]}")
                results = [{
                    "title": "Raw response (JSON parsing failed)",
                    "url": "",
                    "snippet": result_text[:500],
                    "relevance": "unknown"
                }]

            return WebSearchResponse(
                query=request.query,
                results=results,
                session_id=session_id,
                timestamp=datetime.now()
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"WebSearch failed: {str(e)}"
            )

# Автоочистка старых сессий
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    # Создание рабочей директории
    Path(config.CLAUDE_WORKING_DIR).mkdir(parents=True, exist_ok=True)

    # Запуск фоновой задачи очистки
    asyncio.create_task(cleanup_old_sessions())

async def cleanup_old_sessions():
    """Очистка старых сессий"""
    while True:
        try:
            current_time = datetime.now()
            sessions_to_remove = []

            for session_id, session_data in session_manager.sessions.items():
                # Удаление сессий старше 1 часа без активности
                if (current_time - session_data["last_activity"]).seconds > 3600:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                session_manager.cleanup_session(session_id)

            await asyncio.sleep(600)  # Проверка каждые 10 минут

        except Exception as e:
            print(f"Ошибка очистки сессий: {e}")
            await asyncio.sleep(600)

if __name__ == "__main__":
    # Настройки запуска
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"""
╭────────────────────────────────────────╮
│   Claude Code API Wrapper v2.0.0      │
│        ✨ WITH WEBSEARCH ✨           │
├────────────────────────────────────────┤
│  Host: {host:<26}  │
│  Port: {port:<26}  │
│  Debug: {debug:<25}  │
│  API Key: {config.API_KEY[:8]}...{'*' * 18}  │
│  Features: chat, code, websearch      │
╰────────────────────────────────────────╯
    """)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        access_log=debug
    )
