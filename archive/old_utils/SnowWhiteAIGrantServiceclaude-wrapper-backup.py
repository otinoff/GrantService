#!/usr/bin/env python3
"""
Claude Code Wrapper Server
Предоставляет HTTP API для Claude CLI headless mode
Includes WebSearch support
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import subprocess
import json
import asyncio
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "sonnet"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    allowed_domains: Optional[List[str]] = Field(None, description="Разрешённые домены")
    blocked_domains: Optional[List[str]] = Field(None, description="Заблокированные домены")
    max_results: Optional[int] = Field(5, ge=1, le=20, description="Максимум результатов")
    session_id: Optional[str] = Field(None, description="ID сессии")

@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {
        "status": "healthy",
        "service": "Claude Code Wrapper",
        "server": "178.236.17.55",
        "oauth": "max_subscription"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Чат с Claude через локальный CLI"""
    try:
        logger.info(f"📨 Request: {len(request.message)} chars, model={request.model}")

        # Формируем команду
        cmd = [
            "claude",
            "-p",
            "--output-format", "json",
            request.message
        ]

        logger.info(f"🚀 Starting Claude CLI...")

        # Запускаем через subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Ждём результат (с таймаутом)
        timeout = max(15, min(request.max_tokens / 5, 180)) if request.max_tokens else 60

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
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            logger.error(f"❌ CLI error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"CLI error: {error_msg}")

        # Парсим JSON ответ
        output = stdout.decode("utf-8")
        response_data = json.loads(output)

        # Извлекаем результат
        if response_data.get("type") == "result" and response_data.get("subtype") == "success":
            result = response_data.get("result", "").strip()

            logger.info(f"✅ Response: {len(result)} chars, ${response_data.get('total_cost_usd', 0):.4f}")

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

@app.post("/websearch")
async def websearch(request: WebSearchRequest):
    """
    WebSearch через Claude CLI with web search tool

    Claude CLI автоматически использует WebSearch tool когда видит запрос
    с явным указанием "search for" или "find information"
    """
    try:
        logger.info(f"🔍 WebSearch: {request.query[:60]}... (max_results={request.max_results})")

        # Формируем промпт для Claude с явным указанием использовать WebSearch
        search_prompt = f"""Use the WebSearch tool to search for the following query:

Query: {request.query}

Search Parameters:
- Maximum results: {request.max_results}"""

        if request.allowed_domains:
            domains_str = ", ".join(request.allowed_domains)
            search_prompt += f"\n- Only search in these domains: {domains_str}"

        if request.blocked_domains:
            blocked_str = ", ".join(request.blocked_domains)
            search_prompt += f"\n- Exclude these domains: {blocked_str}"

        search_prompt += """

Return the search results in the following JSON format:
{
    "query": "the original query",
    "results": [
        {
            "title": "Result title",
            "url": "Full URL",
            "snippet": "Content snippet or summary",
            "source": "domain.com",
            "date": "Publication date if available"
        }
    ],
    "sources": ["unique list of domains"],
    "total_results": 5
}

IMPORTANT: Use WebSearch tool to perform actual web search. Do not make up results."""

        # Запускаем Claude CLI с WebSearch prompt
        cmd = [
            "claude",
            "-p",
            "--output-format", "json",
            search_prompt
        ]

        logger.info(f"🚀 Starting Claude CLI for WebSearch...")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Увеличенный таймаут для WebSearch (120 секунд)
        timeout = 120

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            logger.error(f"⏱️ WebSearch timeout ({timeout}s)")
            raise HTTPException(status_code=504, detail="WebSearch timeout")

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            logger.error(f"❌ CLI error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"CLI error: {error_msg}")

        # Парсим JSON ответ от Claude
        output = stdout.decode("utf-8")
        response_data = json.loads(output)

        if response_data.get("type") == "result" and response_data.get("subtype") == "success":
            result_text = response_data.get("result", "").strip()

            # Попытаться распарсить JSON из результата
            try:
                # Claude может обернуть JSON в markdown код
                if "```json" in result_text:
                    # Извлечь JSON из markdown блока
                    json_start = result_text.find("```json") + 7
                    json_end = result_text.find("```", json_start)
                    result_text = result_text[json_start:json_end].strip()
                elif "```" in result_text:
                    # Извлечь из обычного блока кода
                    json_start = result_text.find("```") + 3
                    json_end = result_text.find("```", json_start)
                    result_text = result_text[json_start:json_end].strip()

                search_results = json.loads(result_text)

                # Валидация структуры результата
                if not isinstance(search_results, dict):
                    raise ValueError("Result is not a dictionary")

                if "results" not in search_results:
                    search_results["results"] = []

                if "query" not in search_results:
                    search_results["query"] = request.query

                # Добавить метаданные
                search_results["session_id"] = request.session_id
                search_results["usage"] = response_data.get("usage", {})
                search_results["cost"] = response_data.get("total_cost_usd", 0)
                search_results["status"] = "success"

                logger.info(f"✅ WebSearch: {len(search_results.get('results', []))} results found, ${search_results['cost']:.4f}")

                return search_results

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"⚠️ Could not parse search results as JSON: {e}")
                logger.error(f"Raw result: {result_text[:500]}")

                # Возвращаем результат в текстовом формате
                return {
                    "query": request.query,
                    "results": [],
                    "raw_text": result_text,
                    "sources": [],
                    "total_results": 0,
                    "session_id": request.session_id,
                    "usage": response_data.get("usage", {}),
                    "cost": response_data.get("total_cost_usd", 0),
                    "status": "parsed_as_text",
                    "error": f"Could not parse JSON: {str(e)}"
                }
        else:
            error = response_data.get("error", "Unknown error")
            logger.error(f"❌ Claude error: {error}")
            raise HTTPException(status_code=500, detail=f"Claude error: {error}")

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {e}")

    except Exception as e:
        logger.error(f"❌ WebSearch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
