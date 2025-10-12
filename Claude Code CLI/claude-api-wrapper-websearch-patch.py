"""
Патч для добавления WebSearch в Claude Code API Wrapper

Добавьте этот код после строки 80 (после class CodeResponse)
"""

from typing import List

# Новые модели данных для WebSearch
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


# Добавьте этот метод в класс ClaudeCodeInterface (после метода execute_code)

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
        WebSearch через Claude Code

        Использует встроенный WebSearch tool Claude Code CLI
        """
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        working_dir = session["directory"]

        # Формируем промпт с явным указанием использовать WebSearch
        prompt = f"""
Use the WebSearch tool to search for: {query}

Search parameters:
- Query: {query}
"""

        if allowed_domains:
            domains_list = ", ".join(allowed_domains)
            prompt += f"- Only search in these domains: {domains_list}\n"

        if blocked_domains:
            blocked_list = ", ".join(blocked_domains)
            prompt += f"- Do NOT search in these domains: {blocked_list}\n"

        prompt += f"""
- Maximum results: {max_results}

Return the results in JSON format:
{{
    "query": "original query",
    "results": [
        {{
            "title": "Page title",
            "url": "Full URL",
            "snippet": "Content snippet",
            "relevance": "high|medium|low"
        }}
    ]
}}

Use WebSearch tool to perform this search.
"""

        # Экранируем промпт для shell
        escaped_prompt = prompt.replace('"', '\\"').replace('\n', '\\n')

        # Вызываем Claude с явным указанием использовать WebSearch
        command = f'echo "{escaped_prompt}" | claude'

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


# Добавьте этот endpoint после @app.get("/models") (после строки 364)

@app.post("/websearch", response_model=WebSearchResponse)
async def websearch_endpoint(
    request: WebSearchRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    WebSearch через Claude Code

    Использует встроенный WebSearch tool для поиска информации
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
                result_json = json.loads(result_text)
                results = result_json.get("results", [])
            except json.JSONDecodeError:
                # Если Claude вернул не JSON, пытаемся извлечь полезное
                results = [{
                    "title": "Raw response",
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
