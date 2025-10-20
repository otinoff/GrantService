# AI Agents Settings Architecture
## Embedded Configuration Pattern

**Версия**: 1.0
**Дата**: 2025-10-05
**Автор**: Grant Architect + Database Manager
**Статус**: Архитектурный план (до реализации)

---

## 📋 Обзор

Архитектура встроенных настроек для AI-агентов GrantService, позволяющая переключаться между различными режимами работы и провайдерами LLM прямо в интерфейсе каждого агента.

### Ключевые принципы

1. **Embedded Settings** - настройки встроены в интерфейс агента (не отдельная страница)
2. **Per-Agent Configuration** - каждый агент имеет свои специфичные настройки
3. **Database-Driven** - настройки хранятся в PostgreSQL
4. **Hot Reload** - изменения применяются немедленно без перезапуска
5. **Backward Compatible** - существующий код продолжает работать

---

## 🏗 Архитектурное решение

### Проблема

Необходимо поддерживать два режима работы агентов:
- **Interviewer**: Structured (24 вопроса) vs AI-Powered (Claude Code)
- **Writer/Auditor/Planner**: GigaChat vs Claude Code

### Решение: Встроенные настройки

**❌ НЕ ИСПОЛЬЗУЕМ**: Отдельная страница "⚙️ Настройки" (создает путаницу в бизнес-логике)

**✅ ИСПОЛЬЗУЕМ**: Настройки внутри вкладки каждого агента на странице "🤖 Агенты"

### Структура UI

Каждая вкладка агента имеет два раздела:

```
📊 Статистика (существует)
├── Метрики (total, completed, avg_progress)
├── График активности
└── Последние сессии

⚙️ Настройки (NEW)
├── Выбор режима/провайдера
├── Специфичные параметры
└── Кнопка "Сохранить"
```

---

## 💾 База данных

### Схема таблицы

```sql
CREATE TABLE ai_agent_settings (
    agent_name VARCHAR(50) PRIMARY KEY,
    mode VARCHAR(20) NOT NULL,
    provider VARCHAR(20),
    config JSONB,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- Индекс для быстрого поиска
CREATE INDEX idx_ai_agent_settings_mode ON ai_agent_settings(mode);

-- Комментарии
COMMENT ON TABLE ai_agent_settings IS 'Настройки режимов работы AI-агентов';
COMMENT ON COLUMN ai_agent_settings.agent_name IS 'Имя агента: interviewer, writer, auditor, planner, researcher';
COMMENT ON COLUMN ai_agent_settings.mode IS 'Режим работы (для interviewer: structured/ai_powered, для остальных: используется provider)';
COMMENT ON COLUMN ai_agent_settings.provider IS 'LLM провайдер: gigachat, claude_code';
COMMENT ON COLUMN ai_agent_settings.config IS 'Дополнительные параметры в JSON (включая websearch_provider для Researcher)';
```

### Структура config JSONB

**Общие параметры:**
```json
{
    "temperature": 0.7,           // Креативность LLM (0.0-1.0)
    "fallback_provider": "gigachat"  // Fallback LLM провайдер
}
```

**Параметры для Researcher Agent:**
```json
{
    "temperature": 0.7,
    "fallback_provider": "gigachat",
    "websearch_provider": "perplexity",    // WebSearch провайдер: perplexity | claude_code
    "websearch_fallback": "claude_code"    // Fallback WebSearch провайдер
}
```

**Параметры для Writer Agent:**
```json
{
    "temperature": 0.7,
    "fallback_provider": "gigachat",
    "max_tokens": 4000
}
```

**Параметры для Auditor Agent:**
```json
{
    "temperature": 0.3,
    "auditor_mode": "batch"       // batch | incremental
}
```

### Начальные данные

```sql
INSERT INTO ai_agent_settings (agent_name, mode, provider, config) VALUES
    ('interviewer', 'structured', NULL, '{"questions_count": 24}'),
    ('writer', 'active', 'claude_code', '{"temperature": 0.7, "fallback_provider": "gigachat"}'),
    ('auditor', 'active', 'claude_code', '{"temperature": 0.3, "auditor_mode": "batch"}'),
    ('planner', 'active', 'claude_code', '{"temperature": 0.5}'),
    ('researcher', 'active', 'claude_code', '{"temperature": 0.7, "fallback_provider": "gigachat", "websearch_provider": "perplexity", "websearch_fallback": "claude_code"}');
```

### Миграция

Файл: `database/migrations/003_add_ai_agent_settings.sql`

```sql
-- Migration: Add AI agent settings table
-- Author: Database Manager Agent
-- Date: 2025-10-05

BEGIN;

-- Create table
CREATE TABLE IF NOT EXISTS ai_agent_settings (
    agent_name VARCHAR(50) PRIMARY KEY,
    mode VARCHAR(20) NOT NULL,
    provider VARCHAR(20),
    config JSONB,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_ai_agent_settings_mode ON ai_agent_settings(mode);

-- Insert default values
INSERT INTO ai_agent_settings (agent_name, mode, provider, config)
VALUES
    ('interviewer', 'structured', NULL, '{"questions_count": 24}'),
    ('writer', 'active', 'gigachat', '{"temperature": 0.7}'),
    ('auditor', 'active', 'gigachat', '{"temperature": 0.3}'),
    ('planner', 'active', 'gigachat', '{"temperature": 0.5}'),
    ('researcher', 'active', 'gigachat', '{"temperature": 0.7}')
ON CONFLICT (agent_name) DO NOTHING;

COMMIT;
```

---

## 🎨 UI Компоненты

### 1. Interviewer Agent Settings

```python
# В файле: web-admin/pages/🤖_Агенты.py
# В функции: render_interviewer_tab()

def render_interviewer_settings(db):
    """Настройки Interviewer Agent"""
    st.markdown("---")
    st.markdown("### ⚙️ Настройки режима интервью")

    # Получаем текущие настройки
    current_settings = execute_query(
        "SELECT mode, config FROM ai_agent_settings WHERE agent_name = %s",
        ('interviewer',)
    )
    current_mode = current_settings[0].get('mode', 'structured') if current_settings else 'structured'

    # Радиокнопки выбора режима
    mode = st.radio(
        "Режим интервьюера:",
        options=['structured', 'ai_powered'],
        format_func=lambda x: {
            'structured': '📝 Structured (24 hardcoded вопроса)',
            'ai_powered': '🤖 AI-Powered (адаптивное интервью через Claude Code)'
        }[x],
        index=0 if current_mode == 'structured' else 1,
        key='interviewer_mode'
    )

    # Дополнительные параметры
    if mode == 'structured':
        st.info("Используется фиксированный набор из 24 вопросов из базы данных")
    else:
        st.info("Claude Code API будет генерировать вопросы динамически на основе ответов пользователя")

    # Кнопка сохранения
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("💾 Сохранить", key='save_interviewer'):
            execute_update(
                """
                INSERT INTO ai_agent_settings (agent_name, mode, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (agent_name) DO UPDATE
                SET mode = EXCLUDED.mode, updated_at = NOW()
                """,
                ('interviewer', mode)
            )
            st.success("✅ Настройки сохранены!")
            st.rerun()

    with col2:
        if st.button("🔄 Сбросить", key='reset_interviewer'):
            execute_update(
                """
                UPDATE ai_agent_settings
                SET mode = 'structured', updated_at = NOW()
                WHERE agent_name = %s
                """,
                ('interviewer',)
            )
            st.success("✅ Сброшено к structured режиму")
            st.rerun()
```

### 2. Writer Agent Settings

```python
def render_writer_settings(db):
    """Настройки Writer Agent"""
    st.markdown("---")
    st.markdown("### ⚙️ Настройки генератора текста")

    # Получаем текущие настройки
    current_settings = execute_query(
        "SELECT provider, config FROM ai_agent_settings WHERE agent_name = %s",
        ('writer',)
    )
    current_provider = current_settings[0].get('provider', 'gigachat') if current_settings else 'gigachat'

    # Выбор провайдера
    provider = st.radio(
        "LLM Провайдер:",
        options=['gigachat', 'claude_code'],
        format_func=lambda x: {
            'gigachat': '🇷🇺 GigaChat (русский текст, быстро)',
            'claude_code': '🇺🇸 Claude Code (аналитика + структура)'
        }[x],
        index=0 if current_provider == 'gigachat' else 1,
        key='writer_provider'
    )

    # Temperature slider
    config_data = current_settings[0].get('config', {}) if current_settings else {}
    temperature = st.slider(
        "Temperature (креативность):",
        min_value=0.0,
        max_value=1.0,
        value=config_data.get('temperature', 0.7),
        step=0.1,
        key='writer_temperature'
    )

    # Кнопка сохранения
    if st.button("💾 Сохранить", key='save_writer'):
        import json
        execute_update(
            """
            INSERT INTO ai_agent_settings (agent_name, provider, config, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (agent_name) DO UPDATE
            SET provider = EXCLUDED.provider,
                config = EXCLUDED.config,
                updated_at = NOW()
            """,
            ('writer', provider, json.dumps({'temperature': temperature}))
        )
        st.success("✅ Настройки Writer сохранены!")
        st.rerun()
```

### 3. Generic Agent Settings Component

Для Auditor, Planner, Researcher - универсальный компонент:

```python
def render_generic_agent_settings(agent_name: str, display_name: str, db):
    """Универсальные настройки для Auditor/Planner/Researcher"""
    st.markdown("---")
    st.markdown(f"### ⚙️ Настройки {display_name}")

    # Получаем настройки
    current_settings = execute_query(
        "SELECT provider, config FROM ai_agent_settings WHERE agent_name = %s",
        (agent_name,)
    )
    current_provider = current_settings[0].get('provider', 'gigachat') if current_settings else 'gigachat'
    config_data = current_settings[0].get('config', {}) if current_settings else {}

    # Provider select
    provider = st.selectbox(
        "LLM Провайдер:",
        options=['gigachat', 'claude_code'],
        format_func=lambda x: '🇷🇺 GigaChat' if x == 'gigachat' else '🇺🇸 Claude Code',
        index=0 if current_provider == 'gigachat' else 1,
        key=f'{agent_name}_provider'
    )

    # Temperature
    temperature = st.slider(
        "Temperature:",
        min_value=0.0,
        max_value=1.0,
        value=config_data.get('temperature', 0.5),
        step=0.1,
        key=f'{agent_name}_temperature'
    )

    # Save button
    if st.button("💾 Сохранить", key=f'save_{agent_name}'):
        import json
        execute_update(
            """
            INSERT INTO ai_agent_settings (agent_name, provider, config, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (agent_name) DO UPDATE
            SET provider = EXCLUDED.provider,
                config = EXCLUDED.config,
                updated_at = NOW()
            """,
            (agent_name, provider, json.dumps({'temperature': temperature}))
        )
        st.success(f"✅ Настройки {display_name} сохранены!")
        st.rerun()
```

---

## 🔍 WebSearch Provider Configuration

### Обзор

Начиная с версии 2.2 (2025-10-11), ResearcherAgentV2 поддерживает динамический выбор WebSearch провайдера через настройки в базе данных. Это позволяет переключаться между Perplexity API и Claude Code WebSearch без изменения кода.

### Архитектурные принципы

1. **Database-Driven**: Провайдер WebSearch читается из `ai_agent_settings.config.websearch_provider`
2. **Automatic Fallback**: При недоступности основного провайдера используется fallback
3. **Drop-in Replacement**: Оба провайдера имеют идентичный async интерфейс
4. **Router Pattern**: WebSearchRouter аналогичен LLMRouter для унификации

### Поддерживаемые провайдеры

#### 1. Perplexity API (Рекомендован)
- **URL**: `https://api.perplexity.ai`
- **Модель**: `sonar` (WebSearch модель)
- **Преимущества**:
  - ✅ Работает из России без VPN
  - ✅ Официальные русские источники (Росстат, .gov.ru)
  - ✅ Высокая скорость (4-5s на запрос)
  - ✅ 100% success rate
- **Стоимость**: ~$0.01 за запрос (~$0.29 за 27 запросов)
- **API Key**: Хранится в `PERPLEXITY_API_KEY` env variable

#### 2. Claude Code WebSearch (Fallback)
- **URL**: `http://178.236.17.55:8000/websearch`
- **Модель**: Sonnet 4.5 с WebSearch tools
- **Ограничения**:
  - ❌ Географические ограничения (доступен не из всех регионов)
  - ⚠️ Может возвращать 500 errors
- **Преимущества**:
  - ✅ Интеграция с Claude Code API
  - ✅ Единый endpoint для LLM + WebSearch
- **Стоимость**: Включено в Claude Code API

### Конфигурация в базе данных

#### Добавление websearch_provider к Researcher

```sql
-- Обновить настройки Researcher для использования Perplexity
UPDATE ai_agent_settings
SET config = jsonb_set(
    jsonb_set(
        COALESCE(config, '{}'::jsonb),
        '{websearch_provider}',
        '"perplexity"'
    ),
    '{websearch_fallback}',
    '"claude_code"'
),
updated_at = NOW()
WHERE agent_name = 'researcher';
```

#### Проверка конфигурации

```sql
-- Посмотреть текущую конфигурацию WebSearch
SELECT
    agent_name,
    provider as llm_provider,
    config->>'websearch_provider' as websearch_provider,
    config->>'websearch_fallback' as websearch_fallback,
    config->>'temperature' as temperature
FROM ai_agent_settings
WHERE agent_name = 'researcher';
```

**Ожидаемый результат:**
```
agent_name  | llm_provider | websearch_provider | websearch_fallback | temperature
------------|--------------|--------------------|--------------------|------------
researcher  | claude_code  | perplexity         | claude_code        | 0.7
```

### WebSearchRouter Implementation

#### Архитектура

```python
# Файл: shared/llm/websearch_router.py

class WebSearchRouter:
    """
    Роутер для автоматического выбора WebSearch провайдера

    Поддерживает:
    - Perplexity API (основной для РФ)
    - Claude Code WebSearch (fallback)

    Читает настройки из ai_agent_settings.config
    """

    def __init__(self, db):
        self.db = db
        self.perplexity_client = None
        self.claude_websearch_client = None

    async def __aenter__(self):
        # Получить настройки из БД (НЕ захардкоженные!)
        settings = get_agent_settings('researcher')
        config = settings['config']

        self.primary_provider = config.get('websearch_provider', 'perplexity')
        self.fallback_provider = config.get('websearch_fallback', 'claude_code')

        # Инициализировать необходимые клиенты
        if self.primary_provider == 'perplexity' or self.fallback_provider == 'perplexity':
            self.perplexity_client = PerplexityWebSearchClient()
            await self.perplexity_client.__aenter__()

        if self.primary_provider == 'claude_code' or self.fallback_provider == 'claude_code':
            self.claude_websearch_client = ClaudeCodeWebSearchClient()
            await self.claude_websearch_client.__aenter__()

        return self

    async def websearch(self, query: str, allowed_domains: Optional[List[str]] = None,
                       max_results: int = 5) -> Dict[str, Any]:
        """
        Выполнить WebSearch с автоматическим выбором провайдера

        Returns:
            Dict в едином формате для обоих провайдеров
        """
        # Попытка основного провайдера
        try:
            if self.primary_provider == 'perplexity':
                return await self.perplexity_client.websearch(
                    query=query,
                    allowed_domains=allowed_domains,
                    max_results=max_results
                )
            else:
                return await self.claude_websearch_client.websearch(
                    query=query,
                    allowed_domains=allowed_domains,
                    max_results=max_results
                )
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_provider} failed: {e}")

            # Fallback к другому провайдеру
            try:
                if self.fallback_provider == 'perplexity':
                    return await self.perplexity_client.websearch(
                        query=query,
                        allowed_domains=allowed_domains,
                        max_results=max_results
                    )
                else:
                    return await self.claude_websearch_client.websearch(
                        query=query,
                        allowed_domains=allowed_domains,
                        max_results=max_results
                    )
            except Exception as fallback_error:
                logger.error(f"Fallback provider also failed: {fallback_error}")
                raise

    async def check_health(self) -> bool:
        """Проверить доступность провайдеров"""
        try:
            if self.primary_provider == 'perplexity':
                return await self.perplexity_client.check_health()
            else:
                return await self.claude_websearch_client.check_health()
        except:
            return False
```

### Использование в ResearcherAgentV2

#### ПРАВИЛЬНЫЙ подход (DB-driven):

```python
class ResearcherAgentV2(BaseAgent):
    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("researcher_v2", db, llm_provider)

        # Читаем настройки из БД (НЕ захардкоженные!)
        self.settings = get_agent_settings('researcher')
        self.config = self.settings['config']

        # WebSearch провайдер из настроек
        self.websearch_provider = self.config.get('websearch_provider', 'perplexity')
        self.websearch_fallback = self.config.get('websearch_fallback', 'claude_code')

        logger.info(f"[ResearcherAgentV2] Initialized with websearch_provider={self.websearch_provider}")

    async def research_with_expert_prompts(self, anketa_id: str):
        """Исследование через WebSearchRouter (НЕ прямой клиент!)"""

        # Использовать роутер для автоматического выбора провайдера
        async with WebSearchRouter(self.db) as websearch_router:
            # Проверить здоровье
            healthy = await websearch_router.check_health()
            logger.info(f"[WebSearch] Health check: {healthy}")

            # Выполнить запросы через роутер
            block1_results = await self._execute_block_queries(
                block_name="block1_problem",
                queries=all_queries['block1'],
                websearch_client=websearch_router,  # Router вместо конкретного клиента!
                ...
            )
```

#### ❌ НЕПРАВИЛЬНЫЙ подход (Hardcoded):

```python
# ❌ НЕ ДЕЛАТЬ ТАК!
class ResearcherAgentV2(BaseAgent):
    def __init__(self, db, llm_provider: str = "claude_code"):
        super().__init__("researcher_v2", db, llm_provider)

        # ❌ ЗАХАРДКОЖЕНЫ значения
        self.api_key = os.getenv('PERPLEXITY_API_KEY', 'pplx-...')
        self.base_url = 'https://api.perplexity.ai'

    async def research_with_expert_prompts(self, anketa_id: str):
        # ❌ ПРЯМОЕ использование клиента вместо роутера
        async with PerplexityWebSearchClient(api_key=self.api_key) as client:
            ...
```

### UI для переключения провайдеров

#### Компонент в web-admin

```python
# Файл: web-admin/pages/🤖_Агенты.py

def render_researcher_settings(db):
    """Настройки Researcher Agent"""
    st.markdown("---")
    st.markdown("### ⚙️ Настройки исследователя")

    current_settings = get_agent_settings('researcher')
    config = current_settings['config']

    # WebSearch провайдер
    websearch_provider = st.selectbox(
        "WebSearch Provider:",
        options=['perplexity', 'claude_code'],
        index=0 if config.get('websearch_provider', 'perplexity') == 'perplexity' else 1,
        key='researcher_websearch_provider',
        help="""
        Perplexity: Работает из РФ, ~$0.01/запрос, 100% success rate
        Claude Code: Географические ограничения, может быть недоступен
        """
    )

    # Fallback провайдер
    websearch_fallback = st.selectbox(
        "WebSearch Fallback:",
        options=['claude_code', 'perplexity'],
        index=0 if config.get('websearch_fallback', 'claude_code') == 'claude_code' else 1,
        key='researcher_websearch_fallback',
        help="Используется если основной провайдер недоступен"
    )

    # LLM Temperature
    temperature = st.slider(
        "Temperature:",
        0.0, 1.0,
        config.get('temperature', 0.7),
        0.1,
        key='researcher_temperature'
    )

    # Кнопка сохранения
    if st.button("💾 Сохранить", key='save_researcher'):
        config['websearch_provider'] = websearch_provider
        config['websearch_fallback'] = websearch_fallback
        config['temperature'] = temperature

        save_agent_settings('researcher', config=config)
        st.success("✅ Настройки Researcher сохранены!")
        st.rerun()
```

### Миграция существующих установок

#### SQL миграция для добавления WebSearch настроек

Файл: `database/migrations/011_add_websearch_provider_settings.sql`

```sql
-- Migration: Add WebSearch provider settings to Researcher
-- Author: AI Integration Specialist
-- Date: 2025-10-11

BEGIN;

-- Обновить Researcher настройки для использования Perplexity
UPDATE ai_agent_settings
SET config = jsonb_set(
    jsonb_set(
        COALESCE(config, '{}'::jsonb),
        '{websearch_provider}',
        '"perplexity"'
    ),
    '{websearch_fallback}',
    '"claude_code"'
),
updated_at = NOW(),
updated_by = 'migration_011'
WHERE agent_name = 'researcher';

-- Проверить результат
DO $$
DECLARE
    websearch_provider TEXT;
BEGIN
    SELECT config->>'websearch_provider' INTO websearch_provider
    FROM ai_agent_settings
    WHERE agent_name = 'researcher';

    IF websearch_provider = 'perplexity' THEN
        RAISE NOTICE 'SUCCESS: websearch_provider set to perplexity';
    ELSE
        RAISE EXCEPTION 'FAILED: websearch_provider not set correctly';
    END IF;
END $$;

COMMIT;
```

### Performance Comparison

#### Benchmark Results (27 запросов)

| Metric | Claude Code WebSearch | Perplexity WebSearch |
|--------|----------------------|---------------------|
| **Success Rate** | 0% (geo restrictions) | 100% |
| **Total Sources** | 0 | 117 |
| **Avg Time per Query** | N/A (errors) | ~5.4s |
| **Total Time (27 queries)** | 62s (all failed) | 146s (all succeeded) |
| **Cost per Anketa** | $0 (didn't work) | ~$0.29 |
| **Quality** | N/A | Отличное (официальные источники) |

**Рекомендация**: Perplexity как primary, Claude Code как fallback (когда доступен)

### Мониторинг и отладка

#### Проверка здоровья провайдеров

```python
# Файл: shared/api_health_checker.py

class APIHealthChecker:
    """Проверка доступности всех API провайдеров"""

    def check_websearch_providers(self) -> Dict[str, Any]:
        """Проверить оба WebSearch провайдера"""
        return {
            'perplexity': self._check_perplexity(),
            'claude_code': self._check_websearch()
        }

    def get_recommendations(self) -> Dict[str, str]:
        """Рекомендации по выбору провайдеров"""
        recommendations = {}

        # Для WebSearch
        if self.results['providers']['perplexity']['status'] == 'online':
            recommendations['websearch'] = 'perplexity'
        elif self.results['providers']['websearch']['status'] == 'online':
            recommendations['websearch'] = 'claude_code'
        else:
            recommendations['websearch'] = 'unavailable'

        return recommendations
```

#### Логирование выбора провайдера

```python
# В ResearcherAgentV2
logger.info(f"[WebSearch] Using provider: {self.websearch_provider}")
logger.info(f"[WebSearch] Fallback provider: {self.websearch_fallback}")

# При переключении на fallback
logger.warning(f"[WebSearch] Primary provider {primary} failed, switching to {fallback}")
```

---

## 🔌 Backend Integration

### 1. Database Helper Functions

Файл: `web-admin/utils/agent_settings.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent Settings Manager
Управление настройками AI-агентов
"""

from typing import Dict, Any, Optional
from .postgres_helper import execute_query, execute_update
import json


def get_agent_settings(agent_name: str) -> Dict[str, Any]:
    """
    Получить настройки агента

    Args:
        agent_name: Имя агента (interviewer, writer, auditor, planner, researcher)

    Returns:
        Dict с настройками агента
    """
    result = execute_query(
        "SELECT mode, provider, config FROM ai_agent_settings WHERE agent_name = %s",
        (agent_name,)
    )

    if not result:
        # Default settings
        return {
            'mode': 'structured' if agent_name == 'interviewer' else 'active',
            'provider': 'gigachat',
            'config': {}
        }

    settings = result[0]
    return {
        'mode': settings.get('mode'),
        'provider': settings.get('provider'),
        'config': settings.get('config', {})
    }


def save_agent_settings(agent_name: str, mode: Optional[str] = None,
                        provider: Optional[str] = None,
                        config: Optional[Dict] = None) -> bool:
    """
    Сохранить настройки агента

    Args:
        agent_name: Имя агента
        mode: Режим работы (для interviewer)
        provider: LLM провайдер (для остальных)
        config: Дополнительные параметры

    Returns:
        True если успешно
    """
    # Build UPDATE query dynamically
    updates = []
    params = []

    if mode:
        updates.append("mode = %s")
        params.append(mode)

    if provider:
        updates.append("provider = %s")
        params.append(provider)

    if config:
        updates.append("config = %s")
        params.append(json.dumps(config))

    updates.append("updated_at = NOW()")

    params.append(agent_name)

    query = f"""
        INSERT INTO ai_agent_settings (agent_name, {', '.join([u.split('=')[0].strip() for u in updates])})
        VALUES (%s, {', '.join(['%s'] * len(updates))})
        ON CONFLICT (agent_name) DO UPDATE
        SET {', '.join(updates)}
    """

    # Insert agent_name at the beginning
    all_params = [agent_name] + params

    rowcount = execute_update(query, tuple(all_params))
    return rowcount > 0


def get_interviewer_mode() -> str:
    """Получить режим интервьюера (structured/ai_powered)"""
    settings = get_agent_settings('interviewer')
    return settings.get('mode', 'structured')


def get_agent_provider(agent_name: str) -> str:
    """Получить LLM провайдера для агента"""
    settings = get_agent_settings(agent_name)
    return settings.get('provider', 'gigachat')


def is_claude_code_enabled(agent_name: str) -> bool:
    """Проверить включен ли Claude Code для агента"""
    if agent_name == 'interviewer':
        return get_interviewer_mode() == 'ai_powered'
    else:
        return get_agent_provider(agent_name) == 'claude_code'
```

### 2. Telegram Bot Integration

Файл: `telegram-bot/agent_router.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent Router
Маршрутизация между GigaChat и Claude Code на основе настроек
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database import GrantServiceDatabase


def get_interviewer_handler(db: GrantServiceDatabase):
    """
    Получить обработчик интервью в зависимости от настроек

    Returns:
        InterviewerAgent: Structured или AI-Powered
    """
    result = db.execute_query(
        "SELECT mode FROM ai_agent_settings WHERE agent_name = 'interviewer'"
    )

    mode = result[0]['mode'] if result else 'structured'

    if mode == 'ai_powered':
        from agents.interviewer_agent_claude import ClaudeInterviewerAgent
        return ClaudeInterviewerAgent(db)
    else:
        from agents.interviewer_agent import InterviewerAgent
        return InterviewerAgent(db)


def get_agent_llm_client(agent_name: str, db: GrantServiceDatabase):
    """
    Получить LLM клиента для агента (GigaChat или Claude Code)

    Args:
        agent_name: writer, auditor, planner, researcher

    Returns:
        LLM client instance
    """
    result = db.execute_query(
        "SELECT provider, config FROM ai_agent_settings WHERE agent_name = %s",
        (agent_name,)
    )

    provider = result[0]['provider'] if result else 'gigachat'
    config = result[0]['config'] if result else {}

    if provider == 'claude_code':
        from shared.llm.claude_code_client import ClaudeCodeClient
        return ClaudeCodeClient()
    else:
        from shared.llm.gigachat_client import GigaChatClient
        temperature = config.get('temperature', 0.7)
        return GigaChatClient(temperature=temperature)
```

---

## 📝 Implementation Plan

### Phase 1: Database (1-2 hours)

1. ✅ Create migration file `003_add_ai_agent_settings.sql`
2. ✅ Run migration on local PostgreSQL
3. ✅ Run migration on production
4. ✅ Verify table created and data inserted

### Phase 2: Backend Helpers (2-3 hours)

1. ✅ Create `web-admin/utils/agent_settings.py`
2. ✅ Add functions: `get_agent_settings()`, `save_agent_settings()`
3. ✅ Create `telegram-bot/agent_router.py`
4. ✅ Add routing logic for Interviewer and other agents
5. ✅ Write unit tests for helper functions

### Phase 3: UI Components (3-4 hours)

1. ✅ Update `web-admin/pages/🤖_Агенты.py`
2. ✅ Add `render_interviewer_settings()` to Interviewer tab
3. ✅ Add `render_writer_settings()` to Writer tab
4. ✅ Add `render_generic_agent_settings()` for Auditor/Planner/Researcher
5. ✅ Test UI locally with Streamlit
6. ✅ Verify settings save/load correctly

### Phase 4: Integration (2-3 hours)

1. ✅ Update Telegram bot to read settings from DB
2. ✅ Implement agent routing in conversation handlers
3. ✅ Add logging for mode switches
4. ✅ Test end-to-end: Change setting → Bot uses new mode

### Phase 5: Cleanup (1 hour)

1. ✅ Delete `web-admin/pages/⚙️_Настройки.py` (if no longer needed)
2. ✅ Move any useful settings to agent tabs
3. ✅ Update navigation menu
4. ✅ Update documentation

**Total Estimate**: 9-13 hours

---

## ✅ Benefits

### For Users

- **Intuitiveness**: Настройки там, где агент (не нужно искать отдельную страницу)
- **Immediate Feedback**: Видишь как работает агент и можешь сразу настроить
- **Less Clicks**: Нет переключения между страницами

### For Developers

- **Modularity**: Каждый агент инкапсулирует свою логику + настройки
- **Scalability**: Добавить агента = добавить вкладку с настройками автоматически
- **Maintainability**: Меньше глобальных настроек, больше локальных
- **Testing**: Проще тестировать - каждый агент независим

### For Business

- **A/B Testing**: Легко переключать режимы для эксперимента
- **Cost Optimization**: Выбирать дешевле GigaChat или умнее Claude Code
- **Feature Flags**: Включать новые возможности без deploy

---

## 🚀 Migration Strategy

### Step 1: Add New Settings System (Backward Compatible)

```python
# В telegram-bot/handlers/interview.py

def get_interviewer():
    """Get interviewer with fallback to hardcoded if settings not found"""
    try:
        settings = get_agent_settings('interviewer')
        if settings['mode'] == 'ai_powered':
            return ClaudeInterviewerAgent()
        else:
            return StructuredInterviewerAgent()
    except Exception as e:
        logger.warning(f"Failed to load settings, using default: {e}")
        return StructuredInterviewerAgent()  # Safe fallback
```

### Step 2: Test in Staging

1. Deploy to staging environment
2. Test both modes (structured/ai_powered)
3. Monitor logs for errors
4. Check database writes

### Step 3: Gradual Rollout

1. Start with Interviewer only (most critical)
2. Enable for 10% of users
3. Monitor metrics (completion rate, time, satisfaction)
4. Increase to 50%, then 100%
5. Roll out to Writer, Auditor, Planner

### Step 4: Remove Old Code

After 2 weeks of stable operation:
1. Remove fallback code
2. Delete unused Settings page
3. Clean up legacy configuration

---

## 🧪 Testing Checklist

### Unit Tests

- [ ] `test_get_agent_settings()` - получение настроек
- [ ] `test_save_agent_settings()` - сохранение настроек
- [ ] `test_get_interviewer_handler()` - правильный обработчик
- [ ] `test_get_agent_llm_client()` - правильный LLM клиент

### Integration Tests

- [ ] `test_interviewer_mode_switch()` - переключение режима интервьюера
- [ ] `test_writer_provider_switch()` - переключение провайдера Writer
- [ ] `test_settings_ui_save_load()` - сохранение через UI
- [ ] `test_telegram_bot_respects_settings()` - бот использует настройки

### E2E Tests

- [ ] `test_full_grant_flow_structured()` - полный цикл (structured)
- [ ] `test_full_grant_flow_ai_powered()` - полный цикл (ai_powered)
- [ ] `test_mode_switch_during_interview()` - смена режима во время интервью
- [ ] `test_provider_comparison()` - сравнение результатов GigaChat vs Claude Code

---

## 📚 References

- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [Streamlit Components](https://docs.streamlit.io/library/api-reference)
- [Claude Code API Documentation](http://178.236.17.55:8000/docs)
- [GigaChat API Documentation](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest)

---

## 🔄 Future Enhancements

### Version 2.0

- [ ] **Agent Performance Dashboard**: Сравнение эффективности режимов (время, качество, cost)
- [ ] **A/B Testing Framework**: Автоматическое тестирование режимов
- [ ] **User Preferences**: Пользователи выбирают предпочитаемый режим
- [ ] **Smart Routing**: Автоматический выбор режима на основе типа заявки

### Version 3.0

- [ ] **Multi-Agent Collaboration**: Агенты работают вместе (Claude Code анализирует → GigaChat пишет)
- [ ] **Custom Agents**: Пользователи создают свои агенты
- [ ] **Agent Marketplace**: Библиотека готовых агентов

---

## 📊 Metrics to Track

### Technical Metrics

- **Settings Load Time**: < 100ms
- **Settings Save Time**: < 200ms
- **Database Query Count**: Minimize (use caching)
- **UI Render Time**: < 500ms

### Business Metrics

- **Mode Adoption Rate**: % пользователей использующих AI-powered
- **Quality Comparison**: Средний балл заявок (structured vs ai_powered)
- **Cost per Grant**: Средняя стоимость генерации (GigaChat vs Claude Code)
- **User Satisfaction**: NPS по режимам

---

## ⚠️ Important Notes

1. **Settings Page Deletion**: Страница `⚙️_Настройки.py` должна быть удалена, так как создает путаницу в бизнес-логике. Все настройки теперь встроены в агентов.

2. **Backward Compatibility**: При миграции обязательно сохранить fallback на старый режим, если настройки не найдены.

3. **Performance**: Кешировать настройки в Streamlit session_state для уменьшения запросов к БД.

4. **Security**: Проверять права доступа перед изменением настроек (только admin/coordinator).

5. **Monitoring**: Логировать все изменения настроек для аудита.

---

**Status**: ✅ Architectural Design Complete
**Next Step**: Create comprehensive end-to-end tests
**Estimated Implementation**: 9-13 hours
