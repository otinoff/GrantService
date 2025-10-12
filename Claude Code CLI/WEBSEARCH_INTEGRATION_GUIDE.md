# 🔍 WebSearch Integration Guide

**Дата**: 2025-10-08
**Проблема**: Claude Code API wrapper не поддерживает WebSearch tool
**Решение**: Добавить endpoint `/websearch`

---

## 🎯 Проблема

**Текущее состояние:**
```python
# В claude-api-wrapper.py строка 178:
command = f'echo "{escaped_message}" | claude'
```

Это **НЕ** дает доступ к WebSearch tool. Claude Code CLI нужно явно указать использовать WebSearch.

---

## ✅ Решение

### Вариант 1: Добавить endpoint `/websearch` (Рекомендуется)

**Файл**: `claude-api-wrapper.py`

#### 1. Добавить модели данных (после строки 80)

```python
from typing import List

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
```

#### 2. Добавить метод websearch в ClaudeCodeInterface (после execute_code)

```python
@classmethod
async def websearch(
    cls,
    query: str,
    session_id: str,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    max_results: int = 10
) -> str:
    """WebSearch через Claude Code"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    working_dir = session["directory"]

    # Промпт с явным указанием использовать WebSearch
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

    escaped_prompt = prompt.replace('"', '\\"').replace('\n', '\\n')
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
```

#### 3. Добавить endpoint (после @app.get("/models"))

```python
@app.post("/websearch", response_model=WebSearchResponse)
async def websearch_endpoint(
    request: WebSearchRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """WebSearch через Claude Code"""
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

            # Парсим JSON
            try:
                result_json = json.loads(result_text)
                results = result_json.get("results", [])
            except json.JSONDecodeError:
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
```

---

## 🧪 Тестирование

### 1. Перезапустить сервер

```bash
# На сервере 178.236.17.55
ssh root@178.236.17.55

# Найти процесс
ps aux | grep claude-api-wrapper

# Убить старый процесс
kill <PID>

# Запустить новый
nohup python3 /path/to/claude-api-wrapper.py > /var/log/claude-api.log 2>&1 &
```

### 2. Протестировать /websearch

```bash
curl -X POST http://178.236.17.55:8000/websearch \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "официальная статистика детский спорт Россия 2024",
    "allowed_domains": ["rosstat.gov.ru", "fedstat.ru", "minsport.gov.ru"],
    "max_results": 10
  }'
```

**Ожидаемый ответ:**
```json
{
  "query": "официальная статистика детский спорт Россия 2024",
  "results": [
    {
      "title": "Статистика детско-юношеского спорта - Росстат",
      "url": "https://rosstat.gov.ru/...",
      "snippet": "По данным за 2024 год...",
      "relevance": "high"
    }
  ],
  "session_id": "...",
  "timestamp": "2025-10-08T...",
  "status": "success"
}
```

---

## 🔗 Интеграция с Researcher Agent

**Файл**: `agents/researcher_agent.py`

```python
import requests

class ResearcherAgent(BaseAgent):
    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("researcher", db, llm_provider)

        self.claude_api_key = os.getenv('CLAUDE_CODE_API_KEY')
        self.claude_base_url = os.getenv('CLAUDE_CODE_BASE_URL')

    async def websearch(
        self,
        query: str,
        allowed_domains: List[str] = None
    ) -> Dict:
        """WebSearch через Claude Code API"""

        headers = {
            "Authorization": f"Bearer {self.claude_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "query": query,
            "allowed_domains": allowed_domains or [
                "rosstat.gov.ru",
                "fedstat.ru",
                "minsport.gov.ru",
                "nationalprojects.ru",
                "government.ru"
            ],
            "max_results": 10
        }

        try:
            response = requests.post(
                f"{self.claude_base_url}/websearch",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"WebSearch API error: {response.status_code}")

        except Exception as e:
            print(f"❌ WebSearch ошибка: {e}")
            return {
                'query': query,
                'results': [],
                'status': 'error',
                'error': str(e)
            }

    async def research_block1(self, placeholders: Dict) -> Dict:
        """Блок 1: Официальная статистика"""

        # Запрос 1: Росстат
        result1 = await self.websearch(
            query=f"статистика {placeholders['ПРОБЛЕМА']} {placeholders['РЕГИОН']} 2022-2025",
            allowed_domains=["rosstat.gov.ru", "fedstat.ru"]
        )

        # Запрос 2: Минспорт
        result2 = await self.websearch(
            query=f"программы {placeholders['СФЕРА']} {placeholders['ЦЕЛЕВАЯ_ГРУППА']} 2024",
            allowed_domains=["minsport.gov.ru", "nationalprojects.ru"]
        )

        return {
            'statistics': result1.get('results', []),
            'programs': result2.get('results', [])
        }
```

---

## 📊 Результат

**До:**
```
❌ WebSearch не работает через API wrapper
❌ Researcher не может собирать данные
❌ Гранты без статистики
```

**После:**
```
✅ Endpoint /websearch добавлен
✅ Researcher использует WebSearch
✅ Фильтрация по RU-доменам
✅ Структурированные результаты (JSON)
✅ Гранты с официальной статистикой
```

---

## 🚀 Деплой на сервер

### Полный скрипт деплоя:

```bash
#!/bin/bash
# deploy-websearch.sh

SERVER="root@178.236.17.55"
WRAPPER_PATH="/root/claude-api-wrapper.py"

echo "📦 Uploading updated wrapper..."
scp claude-api-wrapper.py $SERVER:$WRAPPER_PATH

echo "🔄 Restarting service..."
ssh $SERVER << 'EOF'
  # Найти старый процесс
  PID=$(ps aux | grep claude-api-wrapper | grep -v grep | awk '{print $2}')

  if [ ! -z "$PID" ]; then
    echo "Stopping old process (PID: $PID)..."
    kill $PID
    sleep 2
  fi

  # Запустить новый
  echo "Starting new process..."
  cd /root
  nohup python3 claude-api-wrapper.py > /var/log/claude-api.log 2>&1 &

  sleep 3

  # Проверить
  NEW_PID=$(ps aux | grep claude-api-wrapper | grep -v grep | awk '{print $2}')
  echo "New process started (PID: $NEW_PID)"
EOF

echo "✅ Testing /websearch endpoint..."
curl -X POST http://178.236.17.55:8000/websearch \
  -H "Authorization: Bearer 1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "тест WebSearch",
    "max_results": 3
  }'

echo -e "\n✅ Deployment complete!"
```

---

## ✅ Checklist

- [ ] Добавить модели WebSearchRequest/WebSearchResponse
- [ ] Добавить метод ClaudeCodeInterface.websearch()
- [ ] Добавить endpoint /websearch
- [ ] Протестировать локально
- [ ] Задеплоить на сервер 178.236.17.55
- [ ] Протестировать /websearch на сервере
- [ ] Обновить Researcher Agent для использования /websearch
- [ ] Протестировать полный цикл: Анкета → Researcher → WebSearch → Grant

---

## 📝 Альтернатива: Perplexity API

Если WebSearch через Claude Code не заработает (региональные ограничения), можно использовать **Perplexity API**:

- Работает из любого региона
- Стоимость: $0.01 за запрос
- Специализирован на поиске
- Уже есть документация в `CLAUDE_CODE_WEBSEARCH_FOR_RESEARCHER.md`

---

**Статус**: 📋 План готов
**Время реализации**: 1-2 часа
**Приоритет**: 🔴 Критический
