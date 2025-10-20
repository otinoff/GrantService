#!/usr/bin/env python3
"""
Claude Code Wrapper Server
Предоставляет HTTP API для Claude CLI headless mode
Includes WebSearch support with content synthesis
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import subprocess
import json
import asyncio
from typing import Optional, List, Dict, Any
import logging
import time

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

    Two-step process:
    1. Search for information using WebSearch tool
    2. Synthesize comprehensive answer based on search results

    Returns:
    - content: Synthesized answer (500-1000 words)
    - results: List of sources with snippets
    - sources: List of unique domains
    - cost: Total cost for search + synthesis
    - usage: Token usage statistics
    """

    try:
        logger.info(f"🔍 WebSearch: {request.query[:60]}... (max_results={request.max_results})")

        start_time = time.time()

        # STEP 1: WebSearch + Synthesis в одном вызове
        # ============================================
        search_prompt = f"""Use the WebSearch tool to search for the following query and provide comprehensive answer:

Query: {request.query}

Please search for relevant information and then provide a detailed, synthesized answer (500-1000 words) based on the sources you find.

Requirements:
- Use WebSearch tool to find {request.max_results} most relevant sources
- Synthesize information into coherent, well-structured answer
- Include specific facts, data, and examples from sources
- Reference sources in text using [1], [2] format
- Organize answer with clear paragraphs or bullet points if needed"""

        if request.allowed_domains:
            domains_str = ", ".join(request.allowed_domains)
            search_prompt += f"\n- Only search in these domains: {domains_str}"

        if request.blocked_domains:
            blocked_str = ", ".join(request.blocked_domains)
            search_prompt += f"\n- Exclude these domains: {blocked_str}"

        search_prompt += """

At the end of your answer, provide the sources in JSON format:
```json
{
    "sources": [
        {
            "title": "Source title",
            "url": "Full URL",
            "snippet": "Brief relevant excerpt",
            "source": "domain.com"
        }
    ]
}
```"""

        # Запускаем Claude CLI с WebSearch
        cmd = [
            "claude",
            "-p",
            "--output-format", "json",
            search_prompt
        ]

        logger.info(f"🚀 Starting Claude CLI for WebSearch + Synthesis...")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Увеличенный таймаут для WebSearch + Synthesis (180 секунд)
        timeout = 180

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

        search_time = time.time() - start_time

        if response_data.get("type") == "result" and response_data.get("subtype") == "success":
            result_text = response_data.get("result", "").strip()

            # Извлекаем синтезированный контент и источники
            content = ""
            sources_data = []

            # Ищем JSON с источниками в конце ответа
            if "```json" in result_text:
                # Разделяем контент и JSON источников
                json_start = result_text.find("```json")
                content = result_text[:json_start].strip()

                # Извлекаем JSON
                json_block_start = json_start + 7
                json_block_end = result_text.find("```", json_block_start)
                if json_block_end == -1:
                    json_block_end = len(result_text)
                json_text = result_text[json_block_start:json_block_end].strip()

                try:
                    sources_json = json.loads(json_text)
                    sources_data = sources_json.get("sources", [])
                    logger.info(f"📚 Extracted {len(sources_data)} sources from JSON")
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Could not parse sources JSON: {e}")
            else:
                # Если нет JSON блока, весь текст - это контент
                content = result_text
                logger.warning("⚠️ No JSON sources block found, using full text as content")

            # Если контент пустой (не нашли разделение), используем весь текст
            if not content:
                content = result_text

            # Формируем список уникальных доменов
            unique_sources = list(set([s.get("source", "") for s in sources_data if s.get("source")]))

            # Собираем полный результат
            final_result = {
                "query": request.query,
                "content": content,  # ГЛАВНОЕ: синтезированный ответ
                "results": sources_data,
                "sources": unique_sources,
                "total_results": len(sources_data),
                "session_id": request.session_id,
                "usage": response_data.get("usage", {}),
                "cost": response_data.get("total_cost_usd", 0),
                "search_time": round(search_time, 2),
                "status": "success"
            }

            logger.info(f"✅ WebSearch complete: {len(content)} chars content, {len(sources_data)} sources, ${final_result['cost']:.4f}, {search_time:.1f}s")

            return final_result

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
