#!/usr/bin/env python3
"""
Claude Code Wrapper Server для Windows
Запускает HTTP API который использует локальный Claude CLI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
import asyncio
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "sonnet"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {
        "status": "healthy",
        "service": "Claude Code Wrapper",
        "oauth": "local_windows"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Чат с Claude через локальный CLI
    """
    try:
        logger.info(f"📨 Запрос: {len(request.message)} символов, model={request.model}")

        # Формируем команду
        cmd = [
            "claude",
            "-p",
            "--output-format", "json",
            request.message
        ]

        logger.info(f"🚀 Запускаем Claude CLI...")

        # Запускаем через subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Ждём результат (с таймаутом)
        timeout = min(request.max_tokens / 10, 120) if request.max_tokens else 60

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            raise HTTPException(status_code=504, detail="Claude CLI timeout")

        # Проверяем код возврата
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
            logger.error(f"❌ Claude CLI error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"CLI error: {error_msg}")

        # Парсим JSON ответ
        output = stdout.decode('utf-8')
        response_data = json.loads(output)

        # Извлекаем результат
        if response_data.get("type") == "result" and response_data.get("subtype") == "success":
            result = response_data.get("result", "").strip()

            logger.info(f"✅ Ответ: {len(result)} символов, ${response_data.get('total_cost_usd', 0):.4f}")

            return {
                "response": result,
                "model": request.model,
                "session_id": None,
                "usage": response_data.get("usage", {}),
                "cost": response_data.get("total_cost_usd", 0),
                "duration_ms": response_data.get("duration_ms", 0)
            }
        else:
            error = response_data.get("error", "Unknown error")
            raise HTTPException(status_code=500, detail=f"Claude error: {error}")

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {e}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("🚀 Claude Code Wrapper Server")
    print("=" * 80)
    print("Запускается на http://0.0.0.0:8000")
    print("OAuth: Использует локальные credentials из ~/.claude/.credentials.json")
    print("Для доступа с production сервера - настройте SSH туннель")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8000)
