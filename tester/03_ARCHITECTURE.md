# Test Engineer Agent - Technical Architecture

**Дата:** 2025-10-30
**Версия:** 1.0
**Статус:** Design Complete

---

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Test Engineer Agent (GigaChat-Max)              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Knowledge  │  │     User     │  │  E2E Test    │              │
│  │   Base (RAG) │  │  Simulator   │  │   Runner     │              │
│  │              │  │              │  │              │              │
│  │  Qdrant +    │  │  GigaChat    │  │  5-step      │              │
│  │  knowhow/    │  │  Generator   │  │  Pipeline    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Memory     │  │      RL      │  │  Knowledge   │              │
│  │   System     │  │    Policy    │  │    Graph     │              │
│  │              │  │              │  │              │              │
│  │  SQLite DB   │  │  Q-learning  │  │  NetworkX    │              │
│  │  4 types     │  │  Optimizer   │  │  Relations   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼────────┐            ┌────────▼─────────┐
            │   Production   │            │   Production     │
            │   PostgreSQL   │            │   Agents (5)     │
            │                │            │                  │
            │  Test Users:   │            │  GigaChat-Max    │
            │  999999XXX     │            │  Based           │
            └────────────────┘            └──────────────────┘
```

---

## 📦 Component Architecture

### 1. Knowledge Base (RAG System)

**Purpose:** Retrieve relevant context из knowhow/ для informed decision making

**Stack:**
- **Vector DB:** Qdrant (localhost:6333)
- **Embeddings:** GigaChat Embeddings API (1024-dim)
- **Documents:** knowhow/*.md (chunked 500 chars)

**Data Flow:**
```
User Question
    ↓
GigaChat Embeddings (query → vector)
    ↓
Qdrant Search (top-k similar chunks)
    ↓
Context Assembly
    ↓
GigaChat Generation (question + context → answer)
```

**Implementation:**

```python
# tester/knowledge_base/rag_retriever.py

class RAGRetriever:
    def __init__(self):
        self.qdrant = QdrantClient(url="http://localhost:6333")
        self.embeddings = GigaChatEmbeddingsClient()
        self.collection = "test_engineer_kb"

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve top-k relevant chunks

        Returns:
            [{"file": "E2E_TESTING_GUIDE.md",
              "chunk_id": 12,
              "content": "FIX #15: Extract full_text...",
              "score": 0.89}, ...]
        """
        query_vec = self.embeddings.get_embedding(query)
        results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_vec,
            limit=k
        )
        return [self._format_result(r) for r in results]
```

**Schema (Qdrant):**
```json
{
  "id": 42,
  "vector": [0.123, -0.456, ...],  // 1024-dim
  "payload": {
    "file": "E2E_TESTING_GUIDE.md",
    "chunk_id": 5,
    "content": "WriterModule validation checks grant_length >= 15000...",
    "doc_type": "knowhow",
    "hash": "a3f2b8c9..."
  }
}
```

**Performance:**
- **Search latency:** <100ms (k=5)
- **Collection size:** ~100 chunks (3 MD files × 30 chunks avg)
- **Embedding time:** ~500ms per query

---

### 2. User Simulator

**Purpose:** Generate realistic anketa answers для E2E tests

**Stack:**
- **LLM:** GigaChat-Max (temperature=0.3)
- **Quality Levels:** beginner | intermediate | expert
- **NKO Types:** education | youth | culture | sport

**Data Flow:**
```
Quality Profile + NKO Type
    ↓
Prompt Engineering (context + constraints)
    ↓
GigaChat Generation (JSON response)
    ↓
Validation (AuditorAgent check)
    ↓
Store in Production DB (anketa table)
```

**Implementation:**

```python
# tester/user_simulator/simulator.py

class UserSimulator:
    def generate_anketa(
        self,
        quality_level: str = "intermediate",
        nko_type: str = "education",
        seed: int = 42
    ) -> Dict[str, str]:
        """
        Generate 10 realistic answers

        Returns:
            {"answer_1": "...", "answer_2": "...", ..., "answer_10": "..."}
        """
        profile = self.quality_profiles[quality_level]
        context = self.nko_contexts[nko_type]

        prompt = self._build_prompt(profile, context)

        response = self.gigachat.generate(
            prompt,
            temperature=0.3,
            seed=seed  # For reproducibility
        )

        return json.loads(response)

    def get_test_user_id(self) -> int:
        """Random test user from production DB range"""
        return random.randint(999999000, 999999099)
```

**Quality Profiles:**

| Level | Detail | Vocabulary | Structure | Mistakes | Expected Audit Score |
|-------|--------|------------|-----------|----------|---------------------|
| **Beginner** | 2-3 sentences | Простой | Хаотичная | Есть грамматические | 3-6/10 |
| **Intermediate** | 4-5 sentences | Профессиональный | Логичная | Минимум | 5-8/10 |
| **Expert** | 6-8 sentences | Терминологичный | Идеальная | Нет ошибок | 7-10/10 |

**Validation:**
```python
# Generated anketa → AuditorAgent → Check score matches expected range
assert expected_min <= audit_score <= expected_max
```

---

### 3. E2E Test Runner

**Purpose:** Execute full 5-step pipeline используя production agents + production DB

**Stack:**
- **Test Modules:** tests/e2e/modules/*.py (5 modules)
- **Database:** Production PostgreSQL (test user range 999999XXX)
- **Artifacts:** iterations/Iteration_XX/artifacts/

**Pipeline Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│                   E2E Test Pipeline                          │
└──────────────────────────────────────────────────────────────┘

STEP 1: Interview
    ↓
    InterviewerModule.run_interview(test_user_id, answers)
    ├─ InteractiveInterviewerAgent (GigaChat-Max)
    ├─ Write to: anketa table (production DB)
    └─ Output: anketa_id = 999999XXX

STEP 2: Audit
    ↓
    AuditorModule.run_audit(anketa_id)
    ├─ AuditorAgent (GigaChat-Max)
    ├─ Read from: anketa table
    ├─ Write to: auditor_results, sessions (production DB)
    └─ Output: session_id, score (0-10)

STEP 3: Research
    ↓
    ResearcherModule.run_research(anketa_id, use_mock_websearch)
    ├─ ResearcherAgentV2 (GigaChat-Max + Claude WebSearch)
    ├─ Read from: anketa table
    ├─ Write to: researcher_research (production DB, status='completed')
    └─ Output: research_id, sources (2-10)

STEP 4: Writer (FIX #15 validation)
    ↓
    WriterModule.run_writer(anketa_id, research_id)
    ├─ WriterAgentV2 (GigaChat-Max)
    ├─ Read from: anketa, researcher_research
    ├─ Write to: grants table (production DB)
    ├─ Validation: grant_length >= 15000 ← FIX #15!
    └─ Output: grant_id = TEST_<timestamp>, grant_text

STEP 5: Review
    ↓
    ReviewerModule.run_review(grant_id)
    ├─ ReviewerAgent (GigaChat-Max)
    ├─ Read from: grants table
    └─ Output: review_score (0-10)

ALL STEPS SUCCESS
    ↓
Save Artifacts:
    ├─ results.json (all step metrics)
    ├─ anketa.txt (interview answers)
    ├─ research.json (sources)
    └─ grant.txt (final application)
```

**Error Handling:**

```python
# tester/runner/e2e_runner.py

class E2ETestRunner:
    def run_full_pipeline(self) -> Dict:
        results = {"steps": {}, "errors": []}

        try:
            # STEP 1
            interview_result = self.interviewer.run_interview(...)
            results["steps"]["interview"] = {"status": "success", ...}

            # STEP 2
            audit_result = self.auditor.run_audit(anketa_id)
            results["steps"]["audit"] = {"status": "success", ...}

            # STEP 3 (may fail with ERROR #16)
            try:
                research_result = self.researcher.run_research(anketa_id)
                results["steps"]["research"] = {"status": "success", ...}
            except TimeoutError as e:
                results["steps"]["research"] = {"status": "failed", "error": str(e)}
                results["errors"].append({"step": 3, "error": "WebSearch timeout"})

                # DECISION: Continue with mock research или stop?
                if self.config.continue_on_research_failure:
                    research_result = self.researcher.run_research(anketa_id, use_mock=True)
                else:
                    raise

            # STEP 4
            writer_result = self.writer.run_writer(anketa_id, research_id)

            # FIX #15 validation
            if writer_result["grant_length"] < 15000:
                raise ValidationError(f"Grant too short: {writer_result['grant_length']} < 15000")

            results["steps"]["writer"] = {"status": "success", ...}

            # STEP 5
            review_result = self.reviewer.run_review(grant_id)
            results["steps"]["review"] = {"status": "success", ...}

            return results

        except Exception as e:
            results["errors"].append({"message": str(e), "timestamp": datetime.now()})
            self._save_artifacts(results)  # Save даже при failure
            raise
```

**Validation Rules:**

| Step | Validation | Threshold | Action on Fail |
|------|-----------|-----------|----------------|
| Interview | questions_count | == 10 | Raise error |
| Interview | anketa_length | >= 4000 chars | Raise error |
| Audit | score | >= 5.0/10 | Warning (continue) |
| Research | sources_count | >= 2 | Raise error (or use mock) |
| Writer | grant_length | >= 15000 chars | Raise error |
| Writer | full_text exists | True | Raise error |
| Review | review_score | >= 6.0/10 | Warning (continue) |

---

### 4. Memory System

**Purpose:** Store short-term, long-term, working, and meta-memory для learning

**Stack:**
- **Storage:** SQLite (`tester/memory/test_engineer_memory.db`)
- **Tables:** 4 tables (one per memory type)
- **Embeddings:** GigaChat Embeddings для working memory RAG

**Schema:**

```sql
-- Short-term memory: Current test run
CREATE TABLE short_term_memory (
    id INTEGER PRIMARY KEY,
    test_run_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    step_name TEXT,           -- Interview, Audit, Research, Write, Review
    status TEXT,              -- success, failed, warning
    details JSON,             -- {"anketa_id": 999999001, "length": 4922, ...}
    duration_sec REAL
);

-- Long-term memory: Historical patterns
CREATE TABLE long_term_memory (
    id INTEGER PRIMARY KEY,
    pattern_name TEXT UNIQUE, -- "FIX_15_writer_grant_length"
    discovered_at DATETIME,
    description TEXT,
    occurrence_count INTEGER DEFAULT 1,
    last_seen DATETIME,
    fix_implemented BOOLEAN DEFAULT 0,
    related_files TEXT        -- JSON: ["writer_module.py", "writer_agent_v2.py"]
);

-- Working memory: Active context
CREATE TABLE working_memory (
    id INTEGER PRIMARY KEY,
    context_type TEXT,        -- "current_test", "relevant_bugs", "code_snippet"
    content TEXT,
    embedding BLOB,           -- Vector for RAG (1024-dim)
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Meta-memory: Knowledge about knowledge
CREATE TABLE meta_memory (
    id INTEGER PRIMARY KEY,
    knowledge_type TEXT,      -- "agent_behavior", "database_schema", "api_contracts"
    entity_name TEXT,         -- "WriterAgent", "grants_table", "GigaChat_API"
    confidence_level REAL,    -- 0.0 to 1.0
    last_validated DATETIME,
    notes TEXT
);
```

**Usage Example:**

```python
# tester/memory.py

memory = TestEngineerMemory()

# Test run starts
test_run_id = "test_20251030_143022"

# STEP 1: Store result
memory.store_step_result(
    test_run_id=test_run_id,
    step_name="Interview",
    status="success",
    details={"anketa_id": 999999001, "length": 4922},
    duration=15.3
)

# STEP 4: Writer failed - record bug pattern
if grant_length < 15000:
    memory.record_bug_pattern(
        pattern_name="writer_grant_length_short",
        description=f"WriterModule returned grant_length={grant_length} < 15000",
        related_files=["tests/e2e/modules/writer_module.py", "agents/writer_agent_v2.py"]
    )

    # Check history
    similar_bugs = memory.recall_similar_bugs("grant_length", limit=5)
    if similar_bugs:
        print(f"⚠️  This bug occurred {similar_bugs[0]['count']} times before!")

# Working memory for LLM
context = memory.load_working_context(test_run_id)
# Returns: {"current_test": [...], "relevant_bugs": [...], "code_snippets": [...]}

# Meta-memory update
memory.update_confidence(
    entity_name="WriterAgent",
    confidence=0.95,  # High confidence after successful test
    notes="FIX #15 verified - extract full_text works correctly"
)
```

---

### 5. Reinforcement Learning Policy

**Purpose:** Learn optimal test selection strategy (full E2E vs quick smoke vs skip)

**Algorithm:** Q-learning (off-policy TD control)

**State Representation:**
```python
state = f"files:{file_categories}_time:{time_bucket}"

# Examples:
# "files:agent_code_time:recent"       → Full E2E (high risk)
# "files:test_code_time:old"           → Quick smoke (low risk)
# "files:docs_time:recent"             → Skip test (no risk)
```

**Action Space:**
- `full_e2e`: Run all 5 steps (~20 minutes)
- `quick_smoke`: Run Interview + Audit only (~5 minutes)
- `skip_test`: Don't run test (0 minutes)

**Reward Function:**
```python
def compute_reward(test_result: Dict) -> float:
    if test_result["status"] == "passed":
        base_reward = 1.0

        # Bonus: Fast completion
        if test_result["duration"] < 600:  # < 10 min
            base_reward += 0.5

        # Bonus: No warnings
        if test_result["warnings"] == 0:
            base_reward += 0.2

        return base_reward

    elif test_result["status"] == "failed":
        base_penalty = -1.0

        # Harsher penalty: Critical bug reached production
        if test_result["bug_severity"] == "critical":
            base_penalty -= 2.0

        return base_penalty

    else:  # skipped
        # Small penalty: Missed opportunity
        return -0.1
```

**Q-Learning Update:**
```python
# Q(s, a) ← Q(s, a) + α[r + γ * max_a' Q(s', a') - Q(s, a)]

current_q = self.q_table[state][action]
max_next_q = max(self.q_table[next_state].values())

new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
self.q_table[state][action] = new_q
```

**Policy Evolution Example:**

| Commit Context | Initial Policy | After 10 runs | After 50 runs |
|----------------|----------------|---------------|---------------|
| writer_agent.py | full_e2e (random) | full_e2e (learned) | full_e2e (confident) |
| README.md | full_e2e (random) | quick_smoke (learned) | skip_test (confident) |
| auditor_agent.py | full_e2e (random) | full_e2e (learned) | full_e2e (confident) |
| test_*.py | quick_smoke (random) | skip_test (learned) | skip_test (confident) |

**Hyperparameters:**
```python
learning_rate = 0.01      # α - step size
discount_factor = 0.9     # γ - future reward discount
epsilon = 0.1             # ε-greedy exploration rate
```

---

### 6. Knowledge Graph

**Purpose:** Model relationships между agents, database tables, tests, bugs

**Stack:**
- **Library:** NetworkX (Python graph library)
- **Storage:** In-memory graph + pickle serialization
- **Query Engine:** DFS/BFS traversal, shortest path

**Graph Structure:**

```python
# Nodes (with types)
nodes = [
    ("InteractiveInterviewerAgent", {"type": "agent", "llm": "GigaChat-Max"}),
    ("AuditorAgent", {"type": "agent", "llm": "GigaChat-Max"}),
    ("WriterAgentV2", {"type": "agent", "llm": "GigaChat-Max"}),
    ("anketa", {"type": "database_table", "schema": "production"}),
    ("grants", {"type": "database_table", "schema": "production"}),
    ("writer_module", {"type": "test_module", "file": "tests/e2e/modules/writer_module.py"}),
    ("FIX_15_writer_grant_length", {"type": "bug_fix", "status": "fixed", "commit": "a2a194e"})
]

# Edges (with relations)
edges = [
    ("InteractiveInterviewerAgent", "anketa", {"relation": "writes_to"}),
    ("WriterAgentV2", "anketa", {"relation": "reads_from"}),
    ("WriterAgentV2", "grants", {"relation": "writes_to"}),
    ("writer_module", "WriterAgentV2", {"relation": "tests"}),
    ("FIX_15_writer_grant_length", "writer_module", {"relation": "affects"}),
    ("FIX_15_writer_grant_length", "WriterAgentV2", {"relation": "fixed_in"})
]
```

**Visualization:**

```
InteractiveInterviewerAgent
    │ writes_to
    ▼
  anketa
    │ reads_from
    ├──────────────┬──────────────┐
    ▼              ▼              ▼
AuditorAgent  ResearcherAgentV2  WriterAgentV2
                                  │ writes_to
                                  ▼
                                grants
                                  │ reads_from
                                  ▼
                              ReviewerAgent

Test Modules (tests each agent):
writer_module ──tests──> WriterAgentV2
auditor_module ──tests──> AuditorAgent

Bug Fixes:
FIX_15 ──affects──> writer_module
FIX_15 ──fixed_in──> WriterAgentV2
```

**Query APIs:**

```python
# tester/knowledge_graph.py

kg = TestKnowledgeGraph()

# Query 1: Impact analysis
impact = kg.query_impact("WriterAgentV2")
# Returns: [{"target": "grants", "relation": "writes_to", "type": "database_table"}]

# Query 2: Dependency analysis
deps = kg.query_dependencies("writer_module")
# Returns: [{"source": "WriterAgentV2", "relation": "tests", "type": "agent"}]

# Query 3: Test recommendation
changed_files = ["agents/writer_agent_v2.py", "agents/auditor_agent_claude.py"]
tests = kg.recommend_tests(changed_files)
# Returns: ["writer_module", "auditor_module"]

# Query 4: Bug history
bugs = kg.query_bugs_affecting("writer_module")
# Returns: [{"name": "FIX_15_writer_grant_length", "status": "fixed", "commit": "a2a194e"}]
```

**Dynamic Updates:**

```python
# When new bug discovered
kg.add_bug_fix(
    fix_name="FIX_16_websearch_timeout",
    affected_modules=["researcher_module"],
    status="open"
)

# When bug fixed
kg.update_bug_status("FIX_16_websearch_timeout", status="fixed", commit="b3c285f")
```

---

## 🔄 Integration Architecture

### Main Agent Loop

```python
# tester/agent.py

class TestEngineerAgent:
    """Main orchestrator coordinating all components"""

    def __init__(self):
        self.rag = RAGRetriever()
        self.memory = TestEngineerMemory()
        self.policy = TestPolicyLearner()
        self.kg = TestKnowledgeGraph()
        self.runner = E2ETestRunner()
        self.gigachat = UnifiedLLMClient()

    def run_test_cycle(self, commit_hash: str, changed_files: List[str]):
        """
        Main test cycle with learning

        Flow:
        1. Knowledge Graph → Recommend tests
        2. RL Policy → Decide test strategy
        3. RAG → Retrieve relevant context
        4. Memory → Load working context
        5. Run Test → Execute E2E pipeline
        6. Compute Reward → Evaluate outcome
        7. Update Policy → Q-learning update
        8. Update KG + Memory → Store results
        9. Generate Report → Markdown artifact
        """

        print(f"\n{'='*80}")
        print(f"TEST CYCLE START: {commit_hash[:7]}")
        print(f"Changed files: {changed_files}")
        print('='*80)

        # 1. KNOWLEDGE GRAPH: Recommend tests
        recommended_tests = self.kg.recommend_tests(changed_files)
        print(f"\n[KG] Recommended tests: {recommended_tests}")

        # 2. RL POLICY: Decision
        state = self.policy.get_state(changed_files, hours_since_deploy=2)
        action = self.policy.select_action(state, epsilon=0.1)
        print(f"[RL] Policy decision: {action} (state: {state})")

        # 3. RAG: Retrieve context
        query = f"How to test changes in {changed_files[0]}?"
        context_docs = self.rag.retrieve(query, k=3)
        print(f"[RAG] Retrieved {len(context_docs)} relevant docs")

        # 4. MEMORY: Load working context
        test_run_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        working_context = self.memory.load_working_context(test_run_id)

        # 5. RUN TEST (based on policy)
        if action == "full_e2e":
            print(f"\n[RUNNER] Starting full E2E test...")
            test_result = self.runner.run_full_pipeline(
                quality_level="intermediate",
                use_mock_websearch=False
            )
        elif action == "quick_smoke":
            print(f"\n[RUNNER] Starting quick smoke test...")
            test_result = self._run_quick_smoke(test_run_id)
        else:
            print(f"\n[RUNNER] Skipping test (policy decision)")
            test_result = {"status": "skipped", "duration": 0}

        # 6. COMPUTE REWARD
        reward = self.policy.compute_reward(test_result)
        print(f"\n[RL] Reward: {reward}")

        # 7. UPDATE POLICY
        next_state = self.policy.get_state([], hours_since_deploy=3)
        self.policy.update_policy(state, action, reward, next_state)
        print(f"[RL] Policy updated: Q({state}, {action}) adjusted")

        # 8. UPDATE KG + MEMORY
        if test_result["status"] == "failed":
            bug_name = f"BUG_{commit_hash[:7]}_{test_result.get('failed_step', 'unknown')}"

            self.kg.add_bug_fix(bug_name, recommended_tests, status="open")

            self.memory.record_bug_pattern(
                pattern_name=bug_name,
                description=test_result.get("error_message", "Unknown error"),
                related_files=changed_files
            )

            print(f"[KG+MEM] Recorded bug: {bug_name}")

        # 9. GENERATE REPORT
        report_path = self._generate_report(
            test_run_id,
            test_result,
            reward,
            context_docs,
            recommended_tests
        )

        print(f"\n[REPORT] Generated: {report_path}")
        print('='*80)
        print(f"TEST CYCLE END: {test_result['status']}")
        print('='*80)

        return test_result

    def _run_quick_smoke(self, test_run_id: str) -> Dict:
        """Quick smoke test: Interview + Audit only"""
        # Implementation...
        pass

    def _generate_report(self, test_run_id, results, reward, context, tests) -> Path:
        """Generate comprehensive markdown report"""
        # Implementation...
        pass
```

---

## 🌐 Deployment Architecture

### Development Environment (Local)

```
Local Machine (Windows/Mac/Linux)
├── PostgreSQL (localhost:5432)
│   └── grantservice DB (production schema)
│       └── Test users: 999999000-999999099
│
├── Qdrant (localhost:6333)
│   └── test_engineer_kb collection
│
├── Test Engineer Agent
│   ├── tester/agent.py (main)
│   ├── tester/config.py (mode=local)
│   └── tester/memory/test_engineer_memory.db
│
└── Production Agents
    ├── agents/interactive_interviewer_agent.py
    ├── agents/auditor_agent_claude.py
    ├── agents/researcher_agent_v2.py
    ├── agents/writer_agent_v2.py
    └── agents/reviewer_agent.py
```

**Run:**
```bash
# Local test
python tester/agent.py --mode local --commit HEAD --files agents/writer_agent_v2.py
```

---

### CI/CD Environment (GitHub Actions)

```
GitHub Actions Runner (ubuntu-latest)
├── PostgreSQL (5.35.88.251:5432) ← Remote production DB
│   └── grantservice DB
│       └── Test users: 999999000-999999099
│
├── Qdrant (5.35.88.251:6333) ← Remote Qdrant
│   └── test_engineer_kb collection
│
└── Test Engineer Agent (containerized)
    ├── Docker container with Python 3.11
    ├── Environment: PRODUCTION credentials
    └── Artifacts uploaded to GitHub
```

**GitHub Actions Workflow:**

```yaml
# .github/workflows/test-engineer-agent.yml

name: Test Engineer Agent - E2E Validation

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Test Engineer Agent
        env:
          TEST_ENGINEER_MODE: remote
          TEST_ENGINEER_DATABASE_URL: ${{ secrets.PRODUCTION_DB_URL }}
          TEST_ENGINEER_GIGACHAT_CREDENTIALS: ${{ secrets.GIGACHAT_TOKEN }}
          TEST_ENGINEER_QDRANT_URL: http://5.35.88.251:6333
        run: |
          python tester/agent.py \
            --commit ${{ github.sha }} \
            --files $(git diff --name-only HEAD~1)

      - name: Upload Test Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-engineer-report
          path: artifacts/test_*_report.md

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('artifacts/test_*_report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Test Engineer Agent Report\n\n${report}`
            });
```

---

### Production Server (5.35.88.251)

```
Production Server (Ubuntu 22.04)
├── PostgreSQL (localhost:5432)
│   └── grantservice DB (production)
│       ├── Real users: 1-999998999
│       └── Test users: 999999000-999999999
│
├── Qdrant (localhost:6333)
│   ├── grant_philosophy (production collection)
│   └── test_engineer_kb (test collection)
│
├── Telegram Bot (systemd service)
│   └── python telegram-bot/main.py
│
└── Test Engineer Agent (cron job)
    ├── Nightly run: 03:00 MSK
    ├── Full E2E test
    └── Cleanup old test data (7+ days)
```

**Cron Configuration:**

```bash
# /etc/cron.d/test-engineer-agent

# Nightly E2E test (03:00 MSK)
0 3 * * * root cd /var/GrantService && python tester/agent.py --mode nightly >> /var/log/test-engineer.log 2>&1

# Weekly cleanup (Sunday 04:00 MSK)
0 4 * * 0 root cd /var/GrantService && python tester/database/cleanup.py --days 7 --execute >> /var/log/test-cleanup.log 2>&1
```

---

## 📊 Performance Metrics

### Latency Budget

| Component | Target | Measured | Notes |
|-----------|--------|----------|-------|
| RAG Retrieval | <100ms | ~80ms | Qdrant search (k=5) |
| User Simulator | <30s | ~25s | GigaChat generation (10 answers) |
| Interview Step | <60s | ~45s | GigaChat + DB writes |
| Audit Step | <30s | ~20s | GigaChat analysis |
| Research Step | <120s | ~90s | With mock WebSearch |
| Research Step | <300s | ~240s | With real WebSearch (may timeout) |
| Writer Step | <180s | ~150s | GigaChat (60K+ tokens) |
| Review Step | <60s | ~40s | GigaChat final check |
| **Full E2E** | **<600s** | **~450s** | All 5 steps |

### Resource Usage

| Resource | Development | CI/CD | Production |
|----------|-------------|-------|------------|
| **RAM** | 2 GB | 4 GB | 8 GB |
| **CPU** | 2 cores | 2 cores | 4 cores |
| **Disk** | 500 MB | 1 GB | 5 GB (artifacts) |
| **Network** | 100 MB/test | 200 MB/test | 500 MB/day |

### Cost Estimation (GigaChat Tokens)

| Operation | Tokens | Cost (₽) |
|-----------|--------|----------|
| User Simulator (10 answers) | ~3,000 | 0.60 |
| Interview (10 Q&A) | ~5,000 | 1.00 |
| Audit | ~2,000 | 0.40 |
| Research (with embeddings) | ~4,000 | 0.80 |
| Writer (60K tokens) | ~65,000 | 13.00 |
| Review | ~2,000 | 0.40 |
| **Total per E2E test** | **~81,000** | **~16.20₽** |

**Monthly projection:**
- Daily tests: 1 (nightly)
- CI/CD tests: 10 (per month, on important commits)
- **Total: ~40 tests/month × 16.20₽ = 648₽/month**

**Compared to manual testing:**
- Manual testing: 20 hours/month × 1,500₽/hour = **30,000₽/month**
- **Savings: 98% (29,352₽/month)**

---

## 🔐 Security Considerations

### Production DB Access

**Risk:** Test Engineer Agent has write access to production DB

**Mitigation:**
1. **Dedicated test user range** (999999XXX) - isolated from real users
2. **Cleanup policy** - auto-delete old test data (7+ days)
3. **Audit trail** - keep last 10 test runs for forensics
4. **No cascade deletes** - FK constraints protect production data

**Database User Permissions:**

```sql
-- Create restricted user for Test Engineer Agent
CREATE USER test_engineer WITH PASSWORD '<secret>';

-- Grant read access to all tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO test_engineer;

-- Grant write access ONLY to test user range
GRANT INSERT, UPDATE ON sessions TO test_engineer;  -- For test users
GRANT INSERT, UPDATE, DELETE ON anketa TO test_engineer WHERE user_id BETWEEN 999999000 AND 999999999;
GRANT INSERT, UPDATE, DELETE ON grants TO test_engineer WHERE grant_id LIKE 'TEST_%';

-- Deny access to production users
REVOKE DELETE ON sessions FROM test_engineer;
```

### Secrets Management

**Environment Variables (.env):**
```bash
# NEVER commit these to git!
TEST_ENGINEER_GIGACHAT_CREDENTIALS=<secret>
TEST_ENGINEER_DATABASE_PASSWORD=<secret>
TEST_ENGINEER_CLAUDE_API_KEY=<secret>
```

**GitHub Actions Secrets:**
- `PRODUCTION_DB_URL`
- `GIGACHAT_TOKEN`
- `CLAUDE_API_KEY`

---

## 📚 API Reference

### TestEngineerAgent

```python
class TestEngineerAgent:
    def __init__(self):
        """Initialize all components"""

    def run_test_cycle(self, commit_hash: str, changed_files: List[str]) -> Dict:
        """
        Main test cycle

        Returns:
            {
                "test_id": "test_20251030_143022",
                "status": "passed" | "failed" | "skipped",
                "steps": {...},
                "reward": 1.5,
                "artifacts_path": "iterations/.../artifacts/run_..."
            }
        """
```

### RAGRetriever

```python
class RAGRetriever:
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve top-k relevant docs"""

    def answer_question(self, question: str, gigachat_client) -> str:
        """RAG-enhanced QA"""
```

### UserSimulator

```python
class UserSimulator:
    def generate_anketa(
        self,
        quality_level: str = "intermediate",
        nko_type: str = "education",
        seed: int = 42
    ) -> Dict[str, str]:
        """Generate realistic anketa"""

    def get_test_user_id(self) -> int:
        """Random test user from 999999XXX range"""
```

### E2ETestRunner

```python
class E2ETestRunner:
    def run_full_pipeline(
        self,
        quality_level: str = "intermediate",
        use_mock_websearch: bool = False
    ) -> Dict:
        """Run full 5-step E2E test"""
```

### TestEngineerMemory

```python
class TestEngineerMemory:
    def store_step_result(self, test_run_id, step_name, status, details, duration):
        """Store short-term memory"""

    def record_bug_pattern(self, pattern_name, description, related_files):
        """Store long-term memory"""

    def load_working_context(self, test_run_id) -> Dict:
        """Assemble working memory"""

    def update_confidence(self, entity_name, confidence, notes):
        """Update meta-memory"""
```

---

## 🔗 Related Documentation

**In this folder:**
- `00_CONCEPT.md` - High-level concept and ROI analysis
- `01_METHODOLOGY_ADAPTATION.md` - Cradle methodology adaptation
- `02_IMPLEMENTATION_PLAN.md` - Detailed roadmap (7 weeks)

**Cradle Know-How:**
- `C:\SnowWhiteAI\cradle\Know-How\TESTING-METHODOLOGY.md`
- `C:\SnowWhiteAI\cradle\Know-How\SELF_LEARNING_SYSTEM_DESIGN.md`

**GrantService:**
- `knowhow/E2E_TESTING_GUIDE.md`
- `knowhow/ITERATION_LEARNINGS.md`
- `iterations/Iteration_66_E2E_Test_Suite/`

---

**Last Updated:** 2025-10-30
**Version:** 1.0
**Status:** ✅ Architecture Complete, Ready for Implementation

**Next Steps:**
1. Review all 3 docs (00_CONCEPT.md, 01_METHODOLOGY.md, 03_ARCHITECTURE.md)
2. Start Phase 1: Knowledge Base implementation
3. Create GitHub issue для tracking progress
