# QUICK FIX - Test Engineer Agent на Production

## Статус: 🟡 В РАБОТЕ

**Commit текущий:** `b6e731b` (Fix imports and pass db instance)
**Проблема:** E2E modules - асинхронные, Test Engineer Agent - синхронный

---

## ✅ ПРОГРЕСС

1. ✅ Fix f-string syntax error (line 423)
2. ✅ Fix imports - use `InterviewerTestModule` not `InterviewerModule`
3. ✅ Pass `db` instance to all modules
4. ✅ DB credentials найдены - нужны PG* env variables
5. ✅ DB подключается успешно!
6. 🟡 **ТЕКУЩАЯ ПРОБЛЕМА:** E2E modules async, agent sync

---

## ❌ ТЕКУЩАЯ ОШИБКА

```
AttributeError: 'InterviewerTestModule' object has no attribute 'run_interview'
```

**Причина:**
- Agent вызывает `self.interviewer.run_interview()` (неправильно)
- Правильно: `await self.interviewer.run_automated_interview(telegram_id, username, llm_provider)`

---

## 🔧 ЧТО НУЖНО ИСПРАВИТЬ

### 1. Сделать `run_e2e_test` асинхронным

```python
# БЫЛО:
def run_e2e_test(self, use_mock_websearch: bool = True) -> Dict:

# ДОЛЖНО БЫТЬ:
async def run_e2e_test(self, use_mock_websearch: bool = True) -> Dict:
```

### 2. Исправить вызовы E2E modules

#### Interviewer (STEP 1):
```python
# БЫЛО:
interview_result = self.interviewer.run_interview(
    test_user_id=test_user_id,
    user_answers=test_answers
)

# ДОЛЖНО БЫТЬ:
interview_result = await self.interviewer.run_automated_interview(
    telegram_id=999999001,
    username="test_user_001",
    llm_provider="gigachat"
)
```

#### Auditor (STEP 2):
```python
# БЫЛО:
audit_result = self.auditor.run_audit(anketa_id)

# ДОЛЖНО БЫТЬ:
anketa_data = {"anketa_id": anketa_id, "answers_data": interview_result.get("answers_data")}
audit_result = await self.auditor.test_auditor(
    anketa_data=anketa_data,
    llm_provider="gigachat"
)
```

#### Researcher (STEP 3):
```python
# БЫЛО:
research_result = self.researcher.run_research(
    anketa_id,
    use_mock_websearch=use_mock_websearch
)

# ДОЛЖНО БЫТЬ:
anketa_data = {"anketa_id": anketa_id, "answers_data": interview_result.get("answers_data")}
research_result = await self.researcher.test_researcher(
    anketa_data=anketa_data,
    llm_provider="claude_code"  # For WebSearch
)
```

#### Writer (STEP 4):
```python
# БЫЛО:
writer_result = self.writer.run_writer(
    anketa_id,
    research_id=research_result["research_id"]
)

# ДОЛЖНО БЫТЬ:
anketa_data = {"anketa_id": anketa_id}
research_data = research_result  # Already has research_content
writer_result = await self.writer.test_writer(
    anketa_data=anketa_data,
    research_data=research_data,
    llm_provider="gigachat"
)
```

#### Reviewer (STEP 5):
```python
# БЫЛО:
review_result = self.reviewer.run_review(writer_result["grant_id"])

# ДОЛЖНО БЫТЬ:
grant_data = {
    "grant_id": writer_result["grant_id"],
    "grant_text": writer_result["grant_text"]
}
review_result = await self.reviewer.test_reviewer(
    grant_data=grant_data,
    llm_provider="gigachat"
)
```

### 3. Изменить `main()` для поддержки async

```python
def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()

    use_mock_websearch = not args.real_websearch

    try:
        agent = TestEngineerAgent(artifacts_dir=args.artifacts_dir)

        # ✅ НОВОЕ: Run async method
        import asyncio
        results = asyncio.run(agent.run_e2e_test(use_mock_websearch=use_mock_websearch))

        # ... rest of code
```

---

## 📁 PRODUCTION DB CREDENTIALS

```bash
export PGHOST=localhost
export PGPORT=5434
export PGDATABASE=grantservice
export PGUSER=grantservice
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
```

---

## 🚀 КАК ЗАПУСТИТЬ ПОСЛЕ ФИКСА

```bash
# 1. Git commit + push
git add tester/agent.py
git commit -m "fix(iteration-66): Make TestEngineerAgent async and fix E2E module calls"
git push origin master

# 2. Deploy на production
ssh -i /c/Users/Андрей/.ssh/id_rsa root@5.35.88.251 "cd /var/GrantService && git pull origin master"

# 3. Запуск с credentials
ssh -i /c/Users/Андрей/.ssh/id_rsa root@5.35.88.251 \
  "cd /var/GrantService && \
   export PGHOST=localhost && \
   export PGPORT=5434 && \
   export PGDATABASE=grantservice && \
   export PGUSER=grantservice && \
   export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' && \
   python3 tester/agent.py --mock-websearch"
```

---

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

```
================================================================================
🤖 TEST ENGINEER AGENT - E2E TEST RUN
================================================================================

[STEP 1/5] Interview - InteractiveInterviewerAgent
✅ Interview complete: anketa_id=999999001

[STEP 2/5] Audit - AuditorAgent
✅ Audit complete: score=7.0/10

[STEP 3/5] Research - ResearcherAgentV2
✅ Research complete: 8 sources

[STEP 4/5] Writer - WriterAgentV2 (FIX #15 CHECK!)
✅ Writer complete: grant_length=62000 chars

🔍 FIX #15 VALIDATION
✅ FIX #15 VERIFIED: grant_length = 62000 >= 15000

[STEP 5/5] Review - ReviewerAgent
✅ Review complete: score=8.0/10

================================================================================
✅ E2E TEST PASSED: 20251030_165335
================================================================================
```

---

**Created:** 2025-10-30 16:56
**Status:** Ready for async refactoring
**Next:** Make `run_e2e_test` async + fix all 5 module calls
