# Test Engineer Agent - Implementation Plan

**Дата:** 2025-10-30
**Статус:** Ready for Phase 1
**Database Strategy:** ✅ Production PostgreSQL (dedicated test user range)

---

## 🎯 Core Decision: Production Database Usage

### Why Production DB?

**Test Engineer Agent - это production monitoring tool, НЕ unit test framework!**

**Аналогия:**
- Unit tests (pytest) = лабораторный анализ образца (изолированная test DB)
- Test Engineer Agent = health check живого организма (production DB)

### Benefits:

1. **Real Schema:** Всегда актуальная schema (с alembic migrations)
2. **Real Constraints:** FK, CHECK constraints как в production
3. **Real Performance:** Видим bottlenecks на realistic data volume
4. **Production Parity:** "Test What You Run, Run What You Test"

### Safety Strategy:

```python
# Dedicated test user range
TEST_USER_ID_RANGE = (999999000, 999999999)  # 1000 test users
TEST_GRANT_PREFIX = "TEST_"

# Cleanup policy
KEEP_LAST_N_TESTS = 10
DELETE_OLDER_THAN_DAYS = 7
```

---

## 📅 Roadmap Overview

**Total Duration:** 7 недель (Q4 2025 - Q1 2026)

| Phase | Duration | Deliverables | Status |
|-------|----------|--------------|--------|
| **Phase 1:** Knowledge Base | 1 неделя | RAG retriever, Qdrant integration | ⏳ Next |
| **Phase 2:** User Simulator | 1 неделя | GigaChat-based answer generator | ⏳ |
| **Phase 3:** E2E Runner | 2 недели | Full 5-step pipeline automation | ⏳ |
| **Phase 4:** Memory & RL | 2 недели | Self-learning system | ⏳ |
| **Phase 5:** CI/CD Integration | 1 неделя | GitHub Actions, pre-commit hooks | ⏳ |

---

## Phase 1: Knowledge Base (Week 1)

### 🎯 Goal
RAG-retrieval по knowhow/ работает - Agent может отвечать на вопросы о системе

### 📦 Deliverables

#### 1.1: Qdrant Collection Setup
**File:** `tester/knowledge_base/setup_qdrant.py`

```python
#!/usr/bin/env python3
"""Setup Qdrant collection для Test Engineer Agent knowledge base"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def setup_knowledge_base_collection():
    """Create 'test_engineer_kb' collection"""

    client = QdrantClient(url="http://localhost:6333")

    # Check if exists
    collections = client.get_collections().collections
    if "test_engineer_kb" in [c.name for c in collections]:
        print("Collection 'test_engineer_kb' already exists")
        return

    # Create collection
    client.create_collection(
        collection_name="test_engineer_kb",
        vectors_config=VectorParams(
            size=1024,  # GigaChat Embeddings dimension
            distance=Distance.COSINE
        )
    )

    print("✅ Created collection 'test_engineer_kb'")

if __name__ == "__main__":
    setup_knowledge_base_collection()
```

**Run:**
```bash
python tester/knowledge_base/setup_qdrant.py
```

---

#### 1.2: Document Embedding Pipeline
**File:** `tester/knowledge_base/embed_documents.py`

```python
#!/usr/bin/env python3
"""Embed knowhow/*.md documents into Qdrant"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient

class DocumentEmbedder:
    """Embed markdown documents для RAG retrieval"""

    def __init__(self):
        self.qdrant = QdrantClient(url="http://localhost:6333")
        self.embeddings_client = GigaChatEmbeddingsClient()
        self.collection_name = "test_engineer_kb"

    def chunk_document(self, content: str, chunk_size=500) -> List[str]:
        """Split document на chunks с overlap"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line)

            if current_size + line_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n'.join(current_chunk))
                # Overlap: keep last 2 lines
                current_chunk = current_chunk[-2:] + [line]
                current_size = sum(len(l) for l in current_chunk)
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def embed_knowhow_directory(self, knowhow_path="knowhow/"):
        """Embed все .md файлы из knowhow/"""

        knowhow_dir = Path(knowhow_path)
        md_files = list(knowhow_dir.glob("*.md"))

        print(f"Found {len(md_files)} markdown files in {knowhow_path}")

        points = []
        point_id = 0

        for md_file in md_files:
            print(f"Processing {md_file.name}...")

            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Chunk document
            chunks = self.chunk_document(content, chunk_size=500)
            print(f"  → {len(chunks)} chunks")

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embeddings_client.get_embedding(chunk)

                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "file": md_file.name,
                        "chunk_id": i,
                        "content": chunk,
                        "doc_type": "knowhow",
                        "hash": hashlib.md5(chunk.encode()).hexdigest()
                    }
                )
                points.append(point)
                point_id += 1

        # Upload to Qdrant
        print(f"\nUploading {len(points)} points to Qdrant...")
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )

        print(f"✅ Embedded {len(md_files)} documents ({len(points)} chunks)")

if __name__ == "__main__":
    embedder = DocumentEmbedder()
    embedder.embed_knowhow_directory("knowhow/")
```

**Run:**
```bash
python tester/knowledge_base/embed_documents.py
```

**Expected Output:**
```
Found 3 markdown files in knowhow/
Processing E2E_TESTING_GUIDE.md...
  → 25 chunks
Processing ITERATION_LEARNINGS.md...
  → 18 chunks
Processing DATA_STRUCTURE_DEBUGGING.md...
  → 12 chunks

Uploading 55 points to Qdrant...
✅ Embedded 3 documents (55 chunks)
```

---

#### 1.3: RAG Retriever Module
**File:** `tester/knowledge_base/rag_retriever.py`

```python
"""RAG retrieval для Test Engineer Agent"""

from typing import List, Dict
from qdrant_client import QdrantClient
from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient

class RAGRetriever:
    """Retrieve relevant context from knowledge base"""

    def __init__(self):
        self.qdrant = QdrantClient(url="http://localhost:6333")
        self.embeddings_client = GigaChatEmbeddingsClient()
        self.collection_name = "test_engineer_kb"

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve top-k relevant documents"""

        # Generate query embedding
        query_embedding = self.embeddings_client.get_embedding(query)

        # Search in Qdrant
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=k
        )

        # Format results
        docs = []
        for hit in results:
            docs.append({
                "file": hit.payload["file"],
                "chunk_id": hit.payload["chunk_id"],
                "content": hit.payload["content"],
                "score": hit.score
            })

        return docs

    def answer_question(self, question: str, gigachat_client) -> str:
        """RAG-enhanced question answering"""

        # Retrieve context
        context_docs = self.retrieve(question, k=3)

        # Build context string
        context = "\n\n---\n\n".join([
            f"**{doc['file']} (chunk {doc['chunk_id']}):**\n{doc['content']}"
            for doc in context_docs
        ])

        # Generate answer with GigaChat
        prompt = f"""
Вопрос: {question}

Контекст из knowledge base:
{context}

Ответь на вопрос используя контекст выше. Если информации недостаточно - скажи это.
"""

        answer = gigachat_client.generate(prompt, temperature=0.2)
        return answer


# Test script
if __name__ == "__main__":
    from shared.llm.unified_llm_client import UnifiedLLMClient

    retriever = RAGRetriever()
    gigachat = UnifiedLLMClient()

    # Test questions
    questions = [
        "Что такое FIX #15?",
        "Как работает WriterModule validation?",
        "Какие шаги в E2E pipeline?"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        answer = retriever.answer_question(q, gigachat)
        print(f"A: {answer}")
```

**Run:**
```bash
python tester/knowledge_base/rag_retriever.py
```

**Expected Output:**
```
Q: Что такое FIX #15?
A: FIX #15 - это исправление в writer_module.py (lines 98-130).
   Проблема: len(dict) возвращал 22 (число ключей) вместо длины текста.
   Решение: Extract application_content['full_text'] вместо целого dict.

Q: Как работает WriterModule validation?
A: WriterModule validation проверяет:
   1. grant_length >= 15000 chars
   2. application_content contains 'full_text' key
   3. All required sections present (section_1_brief, section_2_problem, etc)

Q: Какие шаги в E2E pipeline?
A: E2E pipeline состоит из 5 шагов:
   1. Interview - InteractiveInterviewerAgent
   2. Audit - AuditorAgent
   3. Research - ResearcherAgentV2
   4. Write - WriterAgentV2
   5. Review - ReviewerAgent
```

---

### ✅ Phase 1 Success Criteria

1. **Qdrant collection** `test_engineer_kb` создана
2. **55+ document chunks** embedded из knowhow/
3. **RAG retrieval** работает - Agent отвечает на вопросы о системе
4. **Test passed:**
   ```python
   retriever = RAGRetriever()
   docs = retriever.retrieve("FIX #15", k=3)
   assert len(docs) == 3
   assert "writer_module" in docs[0]["content"].lower()
   ```

---

## Phase 2: User Simulator (Week 2)

### 🎯 Goal
GigaChat генерирует realistic user answers для интервью

### 📦 Deliverables

#### 2.1: Database Setup (Production DB!)
**File:** `tester/database/setup_test_users.py`

```python
#!/usr/bin/env python3
"""Setup test user range в PRODUCTION database"""

import psycopg2
from datetime import datetime

# ⚠️ IMPORTANT: Using PRODUCTION database!
DATABASE_URL = "postgresql://postgres:root@localhost:5432/grantservice"

def setup_test_user_range():
    """Create test users 999999000-999999099 в production DB"""

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check if test users already exist
    cursor.execute("""
        SELECT COUNT(*) FROM sessions
        WHERE telegram_id BETWEEN 999999000 AND 999999099
    """)
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"Found {existing_count} existing test users")
        return

    # Create 100 test users
    test_users = []
    for i in range(100):
        telegram_id = 999999000 + i
        username = f"test_user_{telegram_id}"
        test_users.append((telegram_id, username, datetime.now()))

    # Insert into production DB
    cursor.executemany("""
        INSERT INTO sessions (telegram_id, username, created_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id) DO NOTHING
    """, test_users)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Created {len(test_users)} test users (999999000-999999099)")
    print("   These users exist in PRODUCTION database!")
    print("   Use them for Test Engineer Agent runs")

if __name__ == "__main__":
    setup_test_user_range()
```

**Run:**
```bash
python tester/database/setup_test_users.py
```

---

#### 2.2: User Simulator with Quality Levels
**File:** `tester/user_simulator/simulator.py`

```python
"""User simulator для генерации realistic anketa answers"""

import random
from typing import Dict, List
from shared.llm.unified_llm_client import UnifiedLLMClient

class UserSimulator:
    """Generate realistic user answers для interview"""

    def __init__(self):
        self.gigachat = UnifiedLLMClient()

    def generate_anketa(
        self,
        quality_level: str = "intermediate",
        nko_type: str = "education",
        seed: int = 42
    ) -> Dict[str, str]:
        """
        Generate anketa answers

        Args:
            quality_level: beginner | intermediate | expert
            nko_type: education | youth | culture | sport
            seed: Random seed для reproducibility
        """

        random.seed(seed)

        # Quality level profiles
        quality_profiles = {
            "beginner": {
                "detail_level": "2-3 предложения",
                "vocabulary": "простой, бытовой",
                "structure": "хаотичная, прыгает между темами",
                "mistakes": "есть грамматические ошибки"
            },
            "intermediate": {
                "detail_level": "4-5 предложений",
                "vocabulary": "профессиональный, но не идеальный",
                "structure": "логичная, но неидеальная",
                "mistakes": "минимум ошибок"
            },
            "expert": {
                "detail_level": "6-8 предложений с примерами",
                "vocabulary": "экспертный, терминологичный",
                "structure": "идеальная логика и структура",
                "mistakes": "нет ошибок"
            }
        }

        profile = quality_profiles[quality_level]

        # NKO context
        nko_contexts = {
            "education": "образовательная НКО, работа со школьниками",
            "youth": "молодежная организация, развитие лидерства",
            "culture": "культурный центр, поддержка искусства",
            "sport": "спортивная секция, детский спорт"
        }

        context = nko_contexts[nko_type]

        # Generate answers for 10 interview questions
        prompt = f"""
Ты - представитель НКО ({context}).

Уровень подготовленности: {quality_level}
- Детальность: {profile['detail_level']}
- Словарь: {profile['vocabulary']}
- Структура: {profile['structure']}
- Ошибки: {profile['mistakes']}

Ответь на 10 вопросов анкеты. Твои ответы должны быть РЕАЛИСТИЧНЫМИ (как реальный человек, не идеальный шаблон).

1. Опишите вашу организацию и её миссию
2. Какую проблему вы решаете?
3. Кто ваша целевая аудитория?
4. Какие методы вы используете?
5. Какие результаты уже достигнуты?
6. Каков бюджет проекта?
7. Команда проекта (опыт, роли)
8. Партнеры и поддержка
9. Измеримые показатели успеха
10. Долгосрочное влияние проекта

Ответь в JSON:
{{"answer_1": "...", "answer_2": "...", ..., "answer_10": "..."}}
"""

        # GigaChat generation (low temperature для reproducibility)
        response = self.gigachat.generate(
            prompt,
            temperature=0.3,
            seed=seed  # If GigaChat API supports seed
        )

        # Parse JSON response
        import json
        answers = json.loads(response)

        return answers

    def get_test_user_id(self) -> int:
        """Get random test user from production DB range"""
        return random.randint(999999000, 999999099)


# Test script
if __name__ == "__main__":
    simulator = UserSimulator()

    # Test different quality levels
    for quality in ["beginner", "intermediate", "expert"]:
        print(f"\n{'='*60}")
        print(f"Quality Level: {quality}")
        print('='*60)

        anketa = simulator.generate_anketa(
            quality_level=quality,
            nko_type="education",
            seed=42
        )

        print(f"\nAnswer 1 (length: {len(anketa['answer_1'])}):")
        print(anketa['answer_1'])

        print(f"\nAnswer 2 (length: {len(anketa['answer_2'])}):")
        print(anketa['answer_2'])
```

**Run:**
```bash
python tester/user_simulator/simulator.py
```

---

#### 2.3: Validation Against AuditorAgent
**File:** `tester/user_simulator/validate_quality.py`

```python
"""Validate generated anketa против AuditorAgent"""

from tester.user_simulator.simulator import UserSimulator
from agents.auditor_agent_claude import AuditorAgent

def validate_anketa_quality():
    """Test: Generated anketa passes AuditorAgent validation"""

    simulator = UserSimulator()
    auditor = AuditorAgent()

    quality_levels = ["beginner", "intermediate", "expert"]

    for quality in quality_levels:
        print(f"\n{'='*60}")
        print(f"Testing Quality: {quality}")
        print('='*60)

        # Generate anketa
        anketa = simulator.generate_anketa(quality_level=quality, seed=42)

        # Concatenate answers
        anketa_text = "\n\n".join([
            f"Вопрос {i+1}: {anketa[f'answer_{i+1}']}"
            for i in range(10)
        ])

        # Audit with production AuditorAgent
        audit_result = auditor.audit(anketa_text)

        score = audit_result.get("score", 0)
        issues = audit_result.get("issues", [])

        print(f"Audit Score: {score}/10")
        print(f"Issues: {len(issues)}")

        # Validation thresholds
        expected_scores = {
            "beginner": (3, 6),      # 3-6/10
            "intermediate": (5, 8),  # 5-8/10
            "expert": (7, 10)        # 7-10/10
        }

        min_score, max_score = expected_scores[quality]

        if min_score <= score <= max_score:
            print(f"✅ PASS: Score {score} in expected range [{min_score}, {max_score}]")
        else:
            print(f"❌ FAIL: Score {score} outside expected range [{min_score}, {max_score}]")

if __name__ == "__main__":
    validate_anketa_quality()
```

**Run:**
```bash
python tester/user_simulator/validate_quality.py
```

**Expected Output:**
```
============================================================
Testing Quality: beginner
============================================================
Audit Score: 4.5/10
Issues: 5
✅ PASS: Score 4.5 in expected range [3, 6]

============================================================
Testing Quality: intermediate
============================================================
Audit Score: 6.5/10
Issues: 2
✅ PASS: Score 6.5 in expected range [5, 8]

============================================================
Testing Quality: expert
============================================================
Audit Score: 8.0/10
Issues: 1
✅ PASS: Score 8.0 in expected range [7, 10]
```

---

### ✅ Phase 2 Success Criteria

1. **100 test users** created в production DB (999999000-999999099)
2. **UserSimulator** генерирует anketa для 3 quality levels
3. **AuditorAgent validation** проходит для всех levels
4. **Reproducibility:** Same seed → same anketa (deterministic)

---

## Phase 3: E2E Test Runner (Weeks 3-4)

### 🎯 Goal
Полный 5-step E2E pipeline работает автономно с production DB

### 📦 Deliverables

#### 3.1: Test Runner Core
**File:** `tester/runner/e2e_runner.py`

```python
"""E2E test runner using production modules and production DB"""

import time
import json
from datetime import datetime
from typing import Dict, List
from pathlib import Path

# Import production E2E modules
from tests.e2e.modules.interviewer_module import InterviewerModule
from tests.e2e.modules.auditor_module import AuditorModule
from tests.e2e.modules.researcher_module import ResearcherModule
from tests.e2e.modules.writer_module import WriterModule
from tests.e2e.modules.reviewer_module import ReviewerModule

# Import user simulator
from tester.user_simulator.simulator import UserSimulator

class E2ETestRunner:
    """Run full 5-step E2E test using production agents and production DB"""

    def __init__(self, artifacts_dir="iterations/Iteration_66_E2E_Test_Suite/artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.simulator = UserSimulator()

        # Initialize modules (they connect to PRODUCTION DB!)
        self.interviewer = InterviewerModule()
        self.auditor = AuditorModule()
        self.researcher = ResearcherModule()
        self.writer = WriterModule()
        self.reviewer = ReviewerModule()

    def run_full_pipeline(
        self,
        quality_level: str = "intermediate",
        use_mock_websearch: bool = False
    ) -> Dict:
        """
        Run full E2E test

        Args:
            quality_level: beginner | intermediate | expert
            use_mock_websearch: True для обхода ERROR #16 (WebSearch timeout)

        Returns:
            Test results dict
        """

        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n{'='*80}")
        print(f"E2E TEST RUN: {test_id}")
        print(f"Quality Level: {quality_level}")
        print(f"Mock WebSearch: {use_mock_websearch}")
        print('='*80)

        results = {
            "test_id": test_id,
            "quality_level": quality_level,
            "steps": {},
            "artifacts": {},
            "errors": []
        }

        try:
            # STEP 1: Interview
            print(f"\n[STEP 1] Running Interview...")
            start = time.time()

            # Generate user answers
            user_answers = self.simulator.generate_anketa(quality_level=quality_level)
            test_user_id = self.simulator.get_test_user_id()

            # Run interview (writes to PRODUCTION DB!)
            interview_result = self.interviewer.run_interview(
                test_user_id=test_user_id,
                user_answers=user_answers
            )

            duration = time.time() - start

            results["steps"]["interview"] = {
                "status": "success",
                "anketa_id": interview_result["anketa_id"],
                "questions_count": interview_result["questions_count"],
                "anketa_length": interview_result["anketa_length"],
                "duration_sec": duration
            }

            print(f"✅ Interview complete: anketa_id={interview_result['anketa_id']}, {duration:.1f}s")

            anketa_id = interview_result["anketa_id"]

            # STEP 2: Audit
            print(f"\n[STEP 2] Running Audit...")
            start = time.time()

            audit_result = self.auditor.run_audit(anketa_id)
            duration = time.time() - start

            results["steps"]["audit"] = {
                "status": "success",
                "session_id": audit_result["session_id"],
                "score": audit_result["score"],
                "duration_sec": duration
            }

            print(f"✅ Audit complete: score={audit_result['score']}/10, {duration:.1f}s")

            # STEP 3: Research
            print(f"\n[STEP 3] Running Research...")
            start = time.time()

            research_result = self.researcher.run_research(
                anketa_id,
                use_mock_websearch=use_mock_websearch
            )
            duration = time.time() - start

            results["steps"]["research"] = {
                "status": "success",
                "research_id": research_result["research_id"],
                "sources_count": research_result["sources_count"],
                "duration_sec": duration
            }

            print(f"✅ Research complete: {research_result['sources_count']} sources, {duration:.1f}s")

            # STEP 4: Writer (FIX #15 validation here!)
            print(f"\n[STEP 4] Running Writer...")
            start = time.time()

            writer_result = self.writer.run_writer(
                anketa_id,
                research_id=research_result["research_id"]
            )
            duration = time.time() - start

            results["steps"]["writer"] = {
                "status": "success",
                "grant_id": writer_result["grant_id"],
                "grant_length": writer_result["grant_length"],
                "duration_sec": duration
            }

            print(f"✅ Writer complete: grant_length={writer_result['grant_length']}, {duration:.1f}s")

            # STEP 5: Review
            print(f"\n[STEP 5] Running Review...")
            start = time.time()

            review_result = self.reviewer.run_review(writer_result["grant_id"])
            duration = time.time() - start

            results["steps"]["review"] = {
                "status": "success",
                "review_score": review_result["review_score"],
                "duration_sec": duration
            }

            print(f"✅ Review complete: score={review_result['review_score']}/10, {duration:.1f}s")

            # Save artifacts
            self._save_artifacts(test_id, results)

            print(f"\n{'='*80}")
            print(f"✅ E2E TEST PASSED: {test_id}")
            print('='*80)

            return results

        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ E2E TEST FAILED: {error_msg}")

            results["errors"].append({
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            })

            self._save_artifacts(test_id, results)

            raise

    def _save_artifacts(self, test_id: str, results: Dict):
        """Save test artifacts"""

        run_dir = self.artifacts_dir / f"run_{test_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save results.json
        with open(run_dir / "results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n📁 Artifacts saved: {run_dir}")


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run E2E test")
    parser.add_argument("--quality", choices=["beginner", "intermediate", "expert"], default="intermediate")
    parser.add_argument("--mock-websearch", action="store_true", help="Use mock WebSearch (avoid ERROR #16)")

    args = parser.parse_args()

    runner = E2ETestRunner()
    results = runner.run_full_pipeline(
        quality_level=args.quality,
        use_mock_websearch=args.mock_websearch
    )
```

**Run:**
```bash
# With mock WebSearch (fast, no timeout)
python tester/runner/e2e_runner.py --quality intermediate --mock-websearch

# With real WebSearch (may hit ERROR #16)
python tester/runner/e2e_runner.py --quality expert
```

---

#### 3.2: Production DB Cleanup Policy
**File:** `tester/database/cleanup.py`

```python
"""Cleanup старых test data из production DB"""

import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://postgres:root@localhost:5432/grantservice"

def cleanup_old_test_data(days_to_keep=7, dry_run=True):
    """
    Clean старые test data (но сохраняем последние N дней для audit trail)

    Args:
        days_to_keep: Сколько дней хранить test data
        dry_run: True = только показать что удалится, False = реально удалить
    """

    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Count what will be deleted
    cursor.execute("""
        SELECT COUNT(*) FROM anketa
        WHERE user_id BETWEEN 999999000 AND 999999099
          AND created_at < %s
    """, (cutoff_date,))
    anketa_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM grants
        WHERE grant_id LIKE 'TEST_%'
          AND created_at < %s
    """, (cutoff_date,))
    grants_count = cursor.fetchone()[0]

    print(f"{'='*60}")
    print(f"Cleanup Summary (cutoff: {cutoff_date.date()})")
    print('='*60)
    print(f"Anketa to delete: {anketa_count}")
    print(f"Grants to delete: {grants_count}")

    if dry_run:
        print(f"\n⚠️  DRY RUN - no data deleted")
        print("   Run with --execute to actually delete")
    else:
        # Delete anketa (CASCADE will delete related auditor_results, researcher_research)
        cursor.execute("""
            DELETE FROM anketa
            WHERE user_id BETWEEN 999999000 AND 999999099
              AND created_at < %s
        """, (cutoff_date,))

        # Delete grants
        cursor.execute("""
            DELETE FROM grants
            WHERE grant_id LIKE 'TEST_%'
              AND created_at < %s
        """, (cutoff_date,))

        conn.commit()
        print(f"\n✅ Deleted {anketa_count} anketa + {grants_count} grants")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Keep last N days")
    parser.add_argument("--execute", action="store_true", help="Actually delete (not dry run)")

    args = parser.parse_args()

    cleanup_old_test_data(
        days_to_keep=args.days,
        dry_run=not args.execute
    )
```

**Run:**
```bash
# Dry run (preview)
python tester/database/cleanup.py --days 7

# Execute cleanup
python tester/database/cleanup.py --days 7 --execute
```

---

### ✅ Phase 3 Success Criteria

1. **Full E2E test** проходит все 5 steps успешно
2. **Production DB usage** confirmed - test users 999999XXX
3. **Artifacts** сохраняются в iterations/Iteration_XX/artifacts/
4. **FIX #15 validation** passes в STEP 4 (Writer)
5. **Cleanup policy** работает - старые test data удаляются

---

## Phase 4: Memory & RL (Weeks 5-6)

*(Documentation continues with Memory System and Reinforcement Learning implementation...)*

---

## Phase 5: CI/CD Integration (Week 7)

*(Documentation continues with GitHub Actions, pre-commit hooks, post-deploy validation...)*

---

## 🎯 Quick Start Commands

**Setup (one-time):**
```bash
# Phase 1: Knowledge Base
python tester/knowledge_base/setup_qdrant.py
python tester/knowledge_base/embed_documents.py

# Phase 2: Test Users
python tester/database/setup_test_users.py
```

**Run E2E Test:**
```bash
# Quick test with mock WebSearch
python tester/runner/e2e_runner.py --quality intermediate --mock-websearch

# Full test (may hit ERROR #16)
python tester/runner/e2e_runner.py --quality expert
```

**Cleanup:**
```bash
# Preview cleanup
python tester/database/cleanup.py --days 7

# Execute cleanup
python tester/database/cleanup.py --days 7 --execute
```

---

**Next:** Read `03_ARCHITECTURE.md` для детальной технической архитектуры
