# Test Engineer Agent - Адаптация Методологий Cradle

**Источники:**
- `C:\SnowWhiteAI\cradle\Know-How\TESTING-METHODOLOGY.md` (1,550 lines)
- `C:\SnowWhiteAI\cradle\Know-How\SELF_LEARNING_SYSTEM_DESIGN.md` (616 lines)

**Дата:** 2025-10-30

---

## 🧪 TESTING-METHODOLOGY.md → Test Engineer Agent

### Принцип 1: "Test What You Run, Run What You Test" (Production Parity)

**Оригинал из Cradle:**
> Tests must use same code, same configurations, same database schemas as production.
> Anti-pattern: Mocking production components that could be tested with real implementations.

**Адаптация для Test Engineer Agent:**

✅ **Применяем:**
- Test Engineer Agent использует **те же самые production agents** (agents/*.py)
- Использует **тот же PostgreSQL** (production parity schema)
- Использует **тот же GigaChat-Max** (та же модель, те же prompts)

```python
# agents/test_engineer_agent.py

from agents.interactive_interviewer_agent import InteractiveInterviewerAgent
from agents.auditor_agent_claude import AuditorAgent
from agents.researcher_agent_v2 import ResearcherAgentV2
from agents.writer_agent_v2 import WriterAgentV2
from agents.reviewer_agent import ReviewerAgent

# ✅ GOOD: Используем production code
interviewer = InteractiveInterviewerAgent()

# ❌ BAD: Mock для production agent
# interviewer = MockInterviewer()  # NEVER DO THIS
```

**Исключение:** WebSearch API mock (ERROR #16)
- **Причина:** Claude Code WebSearch timeout >60 sec в production
- **Решение:** Mock ТОЛЬКО для WebSearch, НЕ для ResearcherAgent logic
- **Код:**
```python
# tests/e2e/modules/researcher_module.py (lines 80-95)

if use_mock_websearch:
    # Mock только WebSearch response, не весь ResearcherAgent
    mock_sources = [
        {"title": "Росстат данные", "url": "https://rosstat.gov.ru/...", "content": "..."},
        {"title": "Минтруд РФ", "url": "https://mintrud.gov.ru/...", "content": "..."}
    ]
    # ResearcherAgent.analyze() использует настоящий GigaChat
    result = researcher.analyze(mock_sources)
else:
    # Production path: настоящий WebSearch + GigaChat
    result = researcher.research(query)
```

---

### Принцип 2: Single Source of Truth (Configuration Management)

**Оригинал из Cradle:**
> Use pydantic-settings for environment-driven configuration.
> Avoid duplicate settings in .env, config.py, tests/conftest.py

**Адаптация для Test Engineer Agent:**

✅ **Применяем:**
- Все конфигурации Test Engineer Agent в одном файле: `tester/config.py`
- Environment variables через pydantic-settings

```python
# tester/config.py

from pydantic_settings import BaseSettings

class TestEngineerConfig(BaseSettings):
    """Single source of truth для Test Engineer Agent"""

    # GigaChat settings
    gigachat_model: str = "GigaChat-Max"
    gigachat_temperature: float = 0.2  # Детерминированность для тестов
    gigachat_credentials: str = ""  # From .env

    # Knowledge Base
    knowhow_path: str = "C:/SnowWhiteAI/GrantService/knowhow"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "test_engineer_kb"

    # E2E Tests
    e2e_modules_path: str = "tests/e2e/modules"
    artifacts_path: str = "iterations/Iteration_{iter}/artifacts"

    # User Simulator
    user_quality_level: str = "intermediate"  # beginner/intermediate/expert
    user_nko_type: str = "education"  # education/youth/culture/sport

    # Memory System
    memory_db_path: str = "tester/memory/test_engineer_memory.db"

    # Reinforcement Learning
    reward_pass: float = 1.0
    reward_fail: float = -1.0
    learning_rate: float = 0.01

    class Config:
        env_file = ".env"
        env_prefix = "TEST_ENGINEER_"

# Usage:
config = TestEngineerConfig()
```

**Environment Variables (.env):**
```bash
# Test Engineer Agent config
TEST_ENGINEER_GIGACHAT_CREDENTIALS=<secret>
TEST_ENGINEER_USER_QUALITY_LEVEL=intermediate
TEST_ENGINEER_ARTIFACTS_PATH=iterations/Iteration_{iter}/artifacts
```

---

### Принцип 3: Adapted Test Pyramid

**Оригинал из Cradle:**
```
      /\
     /E2E\     10% - Slow, expensive, brittle
    /------\
   /Integr.\  20% - Medium speed, some external deps
  /----------\
 /   Unit     \ 70% - Fast, cheap, reliable
/--------------\
```

**Адаптация для Test Engineer Agent:**

⚠️ **ИЗМЕНЕНИЕ:** Test Engineer Agent фокусируется НА E2E!

**Причина:**
- Unit tests для production agents уже существуют (pytest tests/unit/)
- Integration tests для database/API уже покрыты (pytest tests/integration/)
- **Критический gap:** E2E validation перед deploy

**Новая пирамида для GrantService:**
```
      /\
     /E2E\     30% - Test Engineer Agent (автоматизирован!)
    /------\
   /Integr.\  20% - Existing pytest tests
  /----------\
 /   Unit     \ 50% - Existing pytest tests
/--------------\
```

**Что тестирует Test Engineer Agent:**
1. Full 5-agent pipeline (Interview → Audit → Research → Write → Review)
2. User journey simulation (realistic НКО scenarios)
3. Production database state transitions
4. Artifact generation (anketa.txt, grant.txt, research.json)

**Что НЕ тестирует:**
- Unit logic internal to agents (covered by pytest)
- Database schema migrations (manual/alembic)
- API endpoint responses (integration tests)

---

### Принцип 4: AI/LLM Testing Strategies

**Оригинал из Cradle:**
> Challenge: LLM outputs are non-deterministic
> Strategies:
> 1. Deterministic test inputs → Assert output structure (not exact content)
> 2. Use "golden outputs" for regression testing
> 3. LLM-as-a-Judge for semantic validation

**Адаптация для Test Engineer Agent:**

✅ **Strategy 1: Deterministic Inputs**
```python
# tester/user_simulator.py

def generate_anketa(quality_level="intermediate", seed=42):
    """Generate deterministic user answers for reproducibility"""

    # Set seed for GigaChat sampling (если API поддерживает)
    config = {"temperature": 0.1, "seed": seed}

    prompt = f"""
    Ты - соискатель гранта для НКО (образование, работа с молодежью).
    Уровень подготовленности: {quality_level}

    Ответь на 10 вопросов анкеты. Твои ответы должны быть:
    - Реалистичными (как реальный человек)
    - Уровень детальности: {quality_level}
    - Без идеального "шаблонного" языка

    Вопрос 1: Опишите вашу организацию...
    """

    # GigaChat with low temperature
    response = gigachat.generate(prompt, **config)
    return response
```

**Validation - Structure, Not Content:**
```python
# tests/e2e/modules/interviewer_module.py (line 65)

# ✅ GOOD: Validate structure
assert len(questions_asked) == 10, f"Expected 10 questions, got {len(questions_asked)}"
assert anketa_length >= 4000, f"Anketa too short: {anketa_length} < 4000"

# ❌ BAD: Validate exact content (non-deterministic!)
# assert "образование" in anketa_text  # Может быть "обучение", "преподавание" etc
```

✅ **Strategy 2: Golden Outputs (Regression Testing)**
```python
# tester/regression_tests.py

GOLDEN_OUTPUTS = {
    "test_v66_fix15": {
        "anketa_id": 999999001,
        "audit_score_range": (5.0, 9.0),  # Range, not exact
        "research_sources_min": 2,
        "grant_length_min": 15000,
        "review_score_range": (6.0, 10.0)
    }
}

def validate_against_golden(test_id, actual_results):
    """Compare actual results with golden baseline"""
    golden = GOLDEN_OUTPUTS.get(test_id)

    # Range validation (flexible)
    assert golden["audit_score_range"][0] <= actual_results["audit_score"] <= golden["audit_score_range"][1]

    # Threshold validation
    assert actual_results["grant_length"] >= golden["grant_length_min"]
```

✅ **Strategy 3: LLM-as-a-Judge**
```python
# tester/llm_judge.py

class LLMJudge:
    """Use GigaChat to evaluate semantic quality of outputs"""

    def evaluate_grant_quality(self, grant_text: str) -> dict:
        """Semantic evaluation of grant application"""

        criteria_prompt = """
        Оцени качество грантовой заявки по критериям (0-10):

        1. Актуальность проблемы (цифры, статистика)
        2. Четкость целей и задач
        3. Реалистичность методов
        4. Обоснованность бюджета
        5. Измеримость результатов

        Заявка:
        {grant_text}

        Ответ в JSON:
        {{"scores": {{"relevance": X, "clarity": Y, ...}}, "total": Z}}
        """

        response = gigachat.generate(criteria_prompt.format(grant_text=grant_text))
        scores = json.loads(response)
        return scores

    def validate(self, scores: dict) -> bool:
        """Check if grant passes quality threshold"""
        return scores["total"] >= 6.0  # Same as ReviewerAgent threshold
```

**Использование в E2E test:**
```python
# tests/e2e/test_grant_workflow.py (after STEP 4)

judge = LLMJudge()
scores = judge.evaluate_grant_quality(grant_text)

if not judge.validate(scores):
    print(f"⚠️  WARNING: Grant quality below threshold: {scores['total']}/10")
    print(f"   Weakest criteria: {min(scores['scores'], key=scores['scores'].get)}")
```

---

### Принцип 5: Continuous Assurance Pipeline

**Оригинал из Cradle:**
```
Code Change → Pre-commit Hooks → CI Tests → Deploy → Monitoring
              (lint, type)     (unit+int)         (logs, alerts)
```

**Адаптация для GrantService + Test Engineer Agent:**

```
Code Change (agents/*.py)
    ↓
Pre-commit Hook
    ├─ black (formatting)
    ├─ mypy (type checking)
    └─ Test Engineer Agent (quick smoke test) ← NEW!
        └─ Duration: 5 minutes
        └─ Tests: Interview + Audit only (partial E2E)
    ↓
Push to GitHub
    ↓
GitHub Actions CI
    ├─ pytest tests/unit/
    ├─ pytest tests/integration/
    └─ Test Engineer Agent (full E2E) ← NEW!
        └─ Duration: 20 minutes
        └─ Tests: All 5 agents
    ↓
Manual Approval (if CI passed)
    ↓
Deploy to Production (5.35.88.251)
    ├─ git pull
    ├─ systemctl restart grant-service
    └─ Test Engineer Agent (post-deploy validation) ← NEW!
        └─ Duration: 15 minutes
        └─ Tests: Smoke test on production DB
    ↓
Monitoring
    ├─ Telegram bot logs
    ├─ PostgreSQL query logs
    └─ Test Engineer Agent (nightly regression) ← NEW!
        └─ Schedule: 03:00 MSK daily
        └─ Tests: Full E2E with golden outputs
```

**Implementation:**

**.git/hooks/pre-commit**
```bash
#!/bin/bash
# Pre-commit hook with Test Engineer Agent

echo "Running pre-commit checks..."

# 1. Format check
black --check agents/ tests/ || exit 1

# 2. Type check
mypy agents/ || exit 1

# 3. Test Engineer Agent - Quick Smoke Test
echo "Running Test Engineer Agent (quick mode)..."
python tester/agent.py --mode quick --timeout 300

if [ $? -ne 0 ]; then
    echo "❌ Test Engineer Agent failed! Fix before commit."
    exit 1
fi

echo "✅ Pre-commit checks passed!"
```

**.github/workflows/ci.yml**
```yaml
name: CI with Test Engineer Agent

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Unit Tests
        run: pytest tests/unit/ -v

      - name: Integration Tests
        run: pytest tests/integration/ -v

      - name: Test Engineer Agent - Full E2E
        run: |
          python tester/agent.py \
            --mode full \
            --timeout 1200 \
            --report artifacts/test_report.md
        env:
          TEST_ENGINEER_GIGACHAT_CREDENTIALS: ${{ secrets.GIGACHAT_TOKEN }}

      - name: Upload Test Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-engineer-report
          path: artifacts/test_report.md
```

---

## 🧠 SELF_LEARNING_SYSTEM_DESIGN.md → Test Engineer Agent

### Component 1: Memory System

**Оригинал из Cradle:**
> Four types of memory:
> 1. Short-term: Current episode (conversation, session)
> 2. Long-term: Historical knowledge (facts, patterns)
> 3. Working: Active context (current task + relevant history)
> 4. Meta-memory: "Knowledge about knowledge" (what I know, what I don't)

**Адаптация для Test Engineer Agent:**

```python
# tester/memory.py

import sqlite3
from datetime import datetime
from typing import List, Dict

class TestEngineerMemory:
    """Memory system for Test Engineer Agent"""

    def __init__(self, db_path="tester/memory/test_engineer_memory.db"):
        self.db = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        """Create memory tables"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY,
                test_run_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                step_name TEXT,  -- Interview, Audit, Research, Write, Review
                status TEXT,     -- success, failed, warning
                details JSON,    -- validation results, error messages
                duration_sec REAL
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY,
                pattern_name TEXT UNIQUE,  -- "FIX_15_writer_grant_length"
                discovered_at DATETIME,
                description TEXT,
                occurrence_count INTEGER DEFAULT 1,
                last_seen DATETIME,
                fix_implemented BOOLEAN DEFAULT 0,
                related_files TEXT  -- JSON array of file paths
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY,
                context_type TEXT,  -- "current_test", "relevant_bugs", "code_snippet"
                content TEXT,
                embedding BLOB,  -- Vector embedding for RAG retrieval
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS meta_memory (
                id INTEGER PRIMARY KEY,
                knowledge_type TEXT,  -- "agent_behavior", "database_schema", "api_contracts"
                entity_name TEXT,     -- "WriterAgent", "grants_table", "GigaChat_API"
                confidence_level REAL, -- 0.0 to 1.0
                last_validated DATETIME,
                notes TEXT
            )
        """)

        self.db.commit()

    # SHORT-TERM MEMORY: Current test run
    def store_step_result(self, test_run_id: str, step_name: str, status: str, details: dict, duration: float):
        """Store результат одного шага E2E теста"""
        self.db.execute("""
            INSERT INTO short_term_memory (test_run_id, step_name, status, details, duration_sec)
            VALUES (?, ?, ?, ?, ?)
        """, (test_run_id, step_name, status, json.dumps(details), duration))
        self.db.commit()

    def get_current_test_context(self, test_run_id: str) -> List[Dict]:
        """Retrieve все шаги текущего теста для analysis"""
        cursor = self.db.execute("""
            SELECT step_name, status, details, duration_sec
            FROM short_term_memory
            WHERE test_run_id = ?
            ORDER BY timestamp
        """, (test_run_id,))
        return [
            {"step": row[0], "status": row[1], "details": json.loads(row[2]), "duration": row[3]}
            for row in cursor.fetchall()
        ]

    # LONG-TERM MEMORY: Historical patterns
    def record_bug_pattern(self, pattern_name: str, description: str, related_files: List[str]):
        """Record новый bug pattern для future reference"""
        self.db.execute("""
            INSERT OR REPLACE INTO long_term_memory
            (pattern_name, discovered_at, description, occurrence_count, last_seen, related_files)
            VALUES (?, ?, ?,
                    COALESCE((SELECT occurrence_count + 1 FROM long_term_memory WHERE pattern_name = ?), 1),
                    ?, ?)
        """, (
            pattern_name,
            datetime.now(),
            description,
            pattern_name,  # For COALESCE subquery
            datetime.now(),
            json.dumps(related_files)
        ))
        self.db.commit()

    def recall_similar_bugs(self, error_message: str, limit=5) -> List[Dict]:
        """RAG-style retrieval: find similar bugs from history"""
        # Simplified: Full-text search (в production: vector similarity)
        cursor = self.db.execute("""
            SELECT pattern_name, description, occurrence_count, fix_implemented
            FROM long_term_memory
            WHERE description LIKE ?
            ORDER BY occurrence_count DESC
            LIMIT ?
        """, (f"%{error_message}%", limit))

        return [
            {"pattern": row[0], "description": row[1], "count": row[2], "fixed": bool(row[3])}
            for row in cursor.fetchall()
        ]

    # WORKING MEMORY: Active context
    def load_working_context(self, test_run_id: str) -> Dict:
        """Assemble working memory для LLM context"""
        return {
            "current_test": self.get_current_test_context(test_run_id),
            "relevant_bugs": self.recall_similar_bugs(""),  # Загрузить все недавние
            "code_snippets": self._retrieve_code_context()
        }

    def _retrieve_code_context(self) -> List[str]:
        """RAG: Retrieve relevant code snippets from knowhow/"""
        # Implement RAG retrieval here (Qdrant integration)
        pass

    # META-MEMORY: Knowledge about knowledge
    def update_confidence(self, entity_name: str, confidence: float, notes: str):
        """Update confidence в знании об entity (agent, table, API)"""
        self.db.execute("""
            INSERT OR REPLACE INTO meta_memory
            (knowledge_type, entity_name, confidence_level, last_validated, notes)
            VALUES (?, ?, ?, ?, ?)
        """, ("agent_behavior", entity_name, confidence, datetime.now(), notes))
        self.db.commit()

    def get_confidence(self, entity_name: str) -> float:
        """Check confidence level для decision making"""
        cursor = self.db.execute("""
            SELECT confidence_level FROM meta_memory
            WHERE entity_name = ?
        """, (entity_name,))
        row = cursor.fetchone()
        return row[0] if row else 0.5  # Default: uncertain
```

**Usage Example:**
```python
# tester/agent.py

memory = TestEngineerMemory()

# Test run starts
test_run_id = "test_" + datetime.now().strftime("%Y%m%d_%H%M%S")

# STEP 1: Interview
start = time.time()
result = interview_module.run_interview(user_answers)
duration = time.time() - start

memory.store_step_result(
    test_run_id=test_run_id,
    step_name="Interview",
    status="success" if result["status"] == "ok" else "failed",
    details={"anketa_id": result["anketa_id"], "length": result["length"]},
    duration=duration
)

# STEP 4: Writer (FIX #15)
result = writer_module.run_writer(anketa_id)

if result["grant_length"] < 15000:
    # Record bug pattern in long-term memory
    memory.record_bug_pattern(
        pattern_name="writer_grant_length_short",
        description=f"WriterModule returned grant_length={result['grant_length']} < 15000",
        related_files=["tests/e2e/modules/writer_module.py", "agents/writer_agent_v2.py"]
    )

    # Check if we've seen this before
    similar_bugs = memory.recall_similar_bugs("grant_length")
    if similar_bugs:
        print(f"⚠️  Similar bug seen {similar_bugs[0]['count']} times before!")
        print(f"   Pattern: {similar_bugs[0]['pattern']}")

# Working memory для LLM analysis
working_context = memory.load_working_context(test_run_id)

# GigaChat analysis with context
analysis_prompt = f"""
Analyze test run results:

Current test: {json.dumps(working_context['current_test'], indent=2)}
Similar historical bugs: {json.dumps(working_context['relevant_bugs'], indent=2)}

Question: Should we proceed to STEP 5 (Review) or investigate Writer failure?
"""

decision = gigachat.generate(analysis_prompt)
```

---

### Component 2: Feedback Loop System (Reinforcement Learning)

**Оригинал из Cradle:**
> Reinforcement Learning components:
> - State: System state representation
> - Action: Agent's decision/action
> - Reward: +/- based on outcome
> - Policy: Strategy for action selection
> - Value Function: Expected long-term reward

**Адаптация для Test Engineer Agent:**

```python
# tester/reinforcement_learning.py

import numpy as np
from typing import Dict, List

class TestPolicyLearner:
    """RL system для оптимизации test selection"""

    def __init__(self, learning_rate=0.01, discount_factor=0.9):
        self.lr = learning_rate
        self.gamma = discount_factor

        # Q-table: state -> action -> expected reward
        # State: (last_commit_files, time_since_deploy)
        # Action: (full_e2e, quick_smoke, skip_test)
        self.q_table = {}

    def get_state(self, commit_files: List[str], hours_since_deploy: int) -> str:
        """Represent current state as hashable string"""
        # Categorize files
        file_categories = set()
        for f in commit_files:
            if f.startswith("agents/"):
                file_categories.add("agent_code")
            elif f.startswith("tests/"):
                file_categories.add("test_code")
            elif f.startswith("data/database/"):
                file_categories.add("database")

        # Discretize time
        time_bucket = "recent" if hours_since_deploy < 24 else "old"

        return f"files:{','.join(sorted(file_categories))}_time:{time_bucket}"

    def select_action(self, state: str, epsilon=0.1) -> str:
        """Epsilon-greedy action selection"""
        actions = ["full_e2e", "quick_smoke", "skip_test"]

        # Exploration (10% chance)
        if np.random.random() < epsilon:
            return np.random.choice(actions)

        # Exploitation: choose best action
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in actions}

        q_values = self.q_table[state]
        return max(q_values, key=q_values.get)

    def update_policy(self, state: str, action: str, reward: float, next_state: str):
        """Q-learning update"""
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in ["full_e2e", "quick_smoke", "skip_test"]}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in ["full_e2e", "quick_smoke", "skip_test"]}

        # Q(s, a) ← Q(s, a) + α[r + γ * max_a' Q(s', a') - Q(s, a)]
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())

        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q

    def compute_reward(self, test_result: Dict) -> float:
        """Reward function based on test outcome"""
        if test_result["status"] == "passed":
            # Positive reward
            base_reward = 1.0

            # Bonus: Fast test completion
            if test_result["duration"] < 600:  # < 10 minutes
                base_reward += 0.5

            # Bonus: No warnings
            if test_result["warnings"] == 0:
                base_reward += 0.2

            return base_reward

        elif test_result["status"] == "failed":
            # Negative reward
            base_penalty = -1.0

            # Harsher penalty: Bug reached production
            if test_result["bug_severity"] == "critical":
                base_penalty -= 2.0

            # Penalty: Wasted time on irrelevant test
            if test_result["false_positive"]:
                base_penalty -= 0.5

            return base_penalty

        else:  # skipped
            # Small penalty for not running test (missed opportunity)
            return -0.1


# Usage in Test Engineer Agent
policy_learner = TestPolicyLearner()

# Pre-commit hook decision
commit_files = ["agents/writer_agent_v2.py", "agents/auditor_agent_claude.py"]
hours_since_last_deploy = 3

state = policy_learner.get_state(commit_files, hours_since_last_deploy)
action = policy_learner.select_action(state)

print(f"RL Policy Decision: {action}")

if action == "full_e2e":
    test_result = run_full_e2e_test()
elif action == "quick_smoke":
    test_result = run_quick_smoke_test()
else:
    test_result = {"status": "skipped", "duration": 0, "warnings": 0}

# Compute reward
reward = policy_learner.compute_reward(test_result)

# Update policy
next_state = policy_learner.get_state([], hours_since_last_deploy + 1)
policy_learner.update_policy(state, action, reward, next_state)

print(f"Reward: {reward}, Q-value updated for state '{state}', action '{action}'")
```

**Reward Function Examples:**

| Scenario | Test Action | Outcome | Reward | Explanation |
|----------|-------------|---------|--------|-------------|
| Writer fix commit | Full E2E | Passed (15 min) | +1.5 | Fast, no warnings |
| Docs update | Skip test | No bug found | -0.1 | Wasted opportunity (should have tested) |
| Agent refactor | Quick smoke | Failed (bug) | -1.5 | Bug slipped through |
| Agent refactor | Full E2E | Caught bug | +2.0 | Bug prevented! |
| Database migration | Full E2E | Passed (25 min) | +1.0 | Slow but thorough |

**Over time:**
- Policy learns: "writer_agent_v2.py commits → always full E2E"
- Policy learns: "README.md commits → skip test"
- Policy learns: "late night commits → full E2E (higher bug risk)"

---

### Component 3: Knowledge Graph

**Оригинал из Cradle:**
> Knowledge Graph structure:
> - Nodes: Concepts, entities, facts
> - Edges: Relationships, dependencies
> - Queries: "What depends on X?", "How does Y relate to Z?"

**Адаптация для Test Engineer Agent:**

```python
# tester/knowledge_graph.py

import networkx as nx
from typing import List, Dict

class TestKnowledgeGraph:
    """Knowledge graph for Test Engineer Agent"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_initial_graph()

    def _build_initial_graph(self):
        """Initialize graph with GrantService architecture"""

        # AGENTS (nodes)
        agents = [
            "InteractiveInterviewerAgent",
            "AuditorAgent",
            "ResearcherAgentV2",
            "WriterAgentV2",
            "ReviewerAgent"
        ]
        for agent in agents:
            self.graph.add_node(agent, type="agent", llm="GigaChat-Max")

        # DATABASE TABLES (nodes)
        tables = ["users", "sessions", "anketa", "auditor_results", "researcher_research", "grants"]
        for table in tables:
            self.graph.add_node(table, type="database_table")

        # DEPENDENCIES (edges)
        self.graph.add_edge("InteractiveInterviewerAgent", "anketa", relation="writes_to")
        self.graph.add_edge("AuditorAgent", "anketa", relation="reads_from")
        self.graph.add_edge("AuditorAgent", "auditor_results", relation="writes_to")
        self.graph.add_edge("ResearcherAgentV2", "anketa", relation="reads_from")
        self.graph.add_edge("ResearcherAgentV2", "researcher_research", relation="writes_to")
        self.graph.add_edge("WriterAgentV2", "anketa", relation="reads_from")
        self.graph.add_edge("WriterAgentV2", "researcher_research", relation="reads_from")
        self.graph.add_edge("WriterAgentV2", "grants", relation="writes_to")
        self.graph.add_edge("ReviewerAgent", "grants", relation="reads_from")

        # E2E TEST MODULES (nodes)
        test_modules = [
            "interviewer_module",
            "auditor_module",
            "researcher_module",
            "writer_module",
            "reviewer_module"
        ]
        for module in test_modules:
            self.graph.add_node(module, type="test_module")

        # TEST -> AGENT mapping (edges)
        self.graph.add_edge("interviewer_module", "InteractiveInterviewerAgent", relation="tests")
        self.graph.add_edge("auditor_module", "AuditorAgent", relation="tests")
        self.graph.add_edge("researcher_module", "ResearcherAgentV2", relation="tests")
        self.graph.add_edge("writer_module", "WriterAgentV2", relation="tests")
        self.graph.add_edge("reviewer_module", "ReviewerAgent", relation="tests")

        # BUGS/FIXES (nodes)
        self.graph.add_node("FIX_15_writer_grant_length", type="bug_fix", status="fixed")
        self.graph.add_edge("FIX_15_writer_grant_length", "writer_module", relation="affects")
        self.graph.add_edge("FIX_15_writer_grant_length", "WriterAgentV2", relation="fixed_in")

    def add_bug_fix(self, fix_name: str, affected_modules: List[str], status="open"):
        """Record новый bug fix в knowledge graph"""
        self.graph.add_node(fix_name, type="bug_fix", status=status)
        for module in affected_modules:
            self.graph.add_edge(fix_name, module, relation="affects")

    def query_impact(self, entity_name: str) -> Dict:
        """Query: What does this entity impact?"""
        if entity_name not in self.graph:
            return {"error": f"Entity '{entity_name}' not found"}

        # Find all outgoing edges
        impacts = []
        for successor in self.graph.successors(entity_name):
            edge_data = self.graph.get_edge_data(entity_name, successor)
            impacts.append({
                "target": successor,
                "relation": edge_data["relation"],
                "type": self.graph.nodes[successor].get("type")
            })

        return {"entity": entity_name, "impacts": impacts}

    def query_dependencies(self, entity_name: str) -> Dict:
        """Query: What does this entity depend on?"""
        if entity_name not in self.graph:
            return {"error": f"Entity '{entity_name}' not found"}

        # Find all incoming edges
        deps = []
        for predecessor in self.graph.predecessors(entity_name):
            edge_data = self.graph.get_edge_data(predecessor, entity_name)
            deps.append({
                "source": predecessor,
                "relation": edge_data["relation"],
                "type": self.graph.nodes[predecessor].get("type")
            })

        return {"entity": entity_name, "dependencies": deps}

    def recommend_tests(self, changed_files: List[str]) -> List[str]:
        """Recommend which E2E modules to run based on changed files"""
        tests_to_run = set()

        for file in changed_files:
            # Map file to agent
            if "writer_agent" in file:
                agent = "WriterAgentV2"
            elif "auditor_agent" in file:
                agent = "AuditorAgent"
            elif "interviewer" in file:
                agent = "InteractiveInterviewerAgent"
            elif "researcher" in file:
                agent = "ResearcherAgentV2"
            elif "reviewer" in file:
                agent = "ReviewerAgent"
            else:
                continue  # Unknown file

            # Find test module that tests this agent
            for predecessor in self.graph.predecessors(agent):
                if self.graph.nodes[predecessor].get("type") == "test_module":
                    tests_to_run.add(predecessor)

        return list(tests_to_run)


# Usage
kg = TestKnowledgeGraph()

# Query impact of WriterAgentV2
impact = kg.query_impact("WriterAgentV2")
print(f"WriterAgentV2 impacts: {impact['impacts']}")
# Output: [{"target": "grants", "relation": "writes_to", "type": "database_table"}]

# Query dependencies of writer_module test
deps = kg.query_dependencies("writer_module")
print(f"writer_module depends on: {deps['dependencies']}")

# Recommend tests for commit
changed_files = ["agents/writer_agent_v2.py", "agents/auditor_agent_claude.py"]
recommended_tests = kg.recommend_tests(changed_files)
print(f"Recommended tests: {recommended_tests}")
# Output: ["writer_module", "auditor_module"]
```

---

## 🔄 Integration: All Components Together

**Test Engineer Agent Main Loop:**

```python
# tester/agent.py

from tester.memory import TestEngineerMemory
from tester.reinforcement_learning import TestPolicyLearner
from tester.knowledge_graph import TestKnowledgeGraph
from tester.rag_retriever import RAGRetriever

class TestEngineerAgent:
    """Main agent orchestrating all components"""

    def __init__(self):
        self.memory = TestEngineerMemory()
        self.policy = TestPolicyLearner()
        self.knowledge_graph = TestKnowledgeGraph()
        self.rag = RAGRetriever(knowhow_path="knowhow/")

    def run_test_cycle(self, commit_hash: str, changed_files: List[str]):
        """Main test cycle with learning"""

        # 1. KNOWLEDGE GRAPH: Recommend tests
        recommended_tests = self.knowledge_graph.recommend_tests(changed_files)
        print(f"Knowledge Graph recommends: {recommended_tests}")

        # 2. REINFORCEMENT LEARNING: Policy decision
        state = self.policy.get_state(changed_files, hours_since_deploy=2)
        action = self.policy.select_action(state)
        print(f"RL Policy decision: {action}")

        # 3. RAG: Retrieve relevant context
        context_docs = self.rag.retrieve(query=f"How to test {changed_files[0]}?", k=3)
        print(f"RAG retrieved {len(context_docs)} relevant docs")

        # 4. MEMORY: Load working context
        test_run_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        working_context = self.memory.load_working_context(test_run_id)

        # 5. RUN TEST (based on policy decision)
        if action == "full_e2e":
            test_result = self._run_full_e2e(test_run_id)
        elif action == "quick_smoke":
            test_result = self._run_quick_smoke(test_run_id)
        else:
            test_result = {"status": "skipped"}

        # 6. COMPUTE REWARD
        reward = self.policy.compute_reward(test_result)

        # 7. UPDATE POLICY
        next_state = self.policy.get_state([], hours_since_deploy=3)
        self.policy.update_policy(state, action, reward, next_state)

        # 8. UPDATE KNOWLEDGE GRAPH (if bug found)
        if test_result["status"] == "failed":
            bug_name = f"BUG_{commit_hash[:7]}_{test_result['failed_step']}"
            self.knowledge_graph.add_bug_fix(bug_name, recommended_tests, status="open")

            # 9. UPDATE MEMORY (long-term pattern)
            self.memory.record_bug_pattern(
                pattern_name=bug_name,
                description=test_result["error_message"],
                related_files=changed_files
            )

        # 10. GENERATE REPORT
        self._generate_report(test_run_id, test_result, reward, context_docs)

    def _run_full_e2e(self, test_run_id: str) -> Dict:
        """Run full 5-step E2E test"""
        # Import E2E modules
        from tests.e2e.modules import interviewer_module, auditor_module, ...

        results = {}

        # STEP 1: Interview
        start = time.time()
        interview_result = interviewer_module.run_interview(...)
        duration = time.time() - start

        self.memory.store_step_result(
            test_run_id, "Interview",
            "success" if interview_result["status"] == "ok" else "failed",
            interview_result, duration
        )

        # ... repeat for all 5 steps

        return results

    def _generate_report(self, test_run_id: str, results: Dict, reward: float, context: List):
        """Generate markdown report with all context"""
        report = f"""
# Test Engineer Agent Report

**Test Run ID:** {test_run_id}
**Timestamp:** {datetime.now()}
**RL Reward:** {reward}

## Test Results
{json.dumps(results, indent=2)}

## Retrieved Context
{chr(10).join([f"- {doc['title']}" for doc in context])}

## Memory State
- Short-term events: {len(self.memory.get_current_test_context(test_run_id))}
- Long-term patterns: {len(self.memory.db.execute("SELECT * FROM long_term_memory").fetchall())}

## Knowledge Graph Insights
- Total nodes: {self.knowledge_graph.graph.number_of_nodes()}
- Total edges: {self.knowledge_graph.graph.number_of_edges()}
        """

        with open(f"artifacts/{test_run_id}_report.md", "w") as f:
            f.write(report)
```

---

## 📊 Summary

### Cradle TESTING-METHODOLOGY → Test Engineer Agent

| Принцип Cradle | Адаптация для GrantService |
|----------------|----------------------------|
| Production Parity | ✅ Use production agents, DB, GigaChat |
| Single Source of Truth | ✅ `tester/config.py` with pydantic-settings |
| Adapted Test Pyramid | ⚠️ Modified: 30% E2E (agent focus), 50% unit, 20% integration |
| AI/LLM Testing | ✅ Deterministic inputs, golden outputs, LLM-as-Judge |
| Continuous Assurance | ✅ Pre-commit hook, CI/CD, post-deploy validation |

### Cradle SELF_LEARNING → Test Engineer Agent

| Component Cradle | Implementation |
|------------------|----------------|
| Memory System | ✅ SQLite DB: short-term, long-term, working, meta-memory |
| Feedback Loop (RL) | ✅ Q-learning for test policy optimization |
| Knowledge Graph | ✅ NetworkX graph: agents, tables, tests, bugs |
| RAG Retrieval | ✅ Qdrant embeddings для knowhow/ search |

---

**Next:** Read `02_IMPLEMENTATION_PLAN.md` для детального roadmap
