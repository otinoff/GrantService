# Iteration 41: Realistic Interactive Interview Simulation

**Date:** 2025-10-25
**Status:** 🚀 PLANNED
**Iteration:** 41 - Realistic Interview Simulation

---

## 🎯 OBJECTIVE

**Goal:** Симулировать 100 реалистичных интервью где InteractiveInterviewer задаёт вопросы, SyntheticUserSimulator отвечает, и AnketaValidator проверяет качество.

**Success Criteria:**
- ✅ 100 realistic interviews completed (20 low, 50 medium, 30 high quality)
- ✅ All interviews saved to database
- ✅ All 100 anketas audited by AnketaValidator
- ✅ Quality correlation verified: low/medium/high → audit score
- ✅ Database linking works: sessions ↔ auditor_results
- ✅ Ready for RL Optimization (state/action/reward data collected)

---

## 🏗️ ARCHITECTURE

### **3-Agent System:**

```
InteractiveInterviewer → SyntheticUserSimulator → AnketaValidator
     (вопросы)              (ответы)                (аудит)
```

### **Component 1: InteractiveInterviewer**
**Status:** ✅ Already exists

**Role:** Задаёт вопросы для сбора данных анкеты

**Methods:**
```python
class InteractiveInterviewer:
    async def ask_question(self, field_name: str) -> str:
        """Возвращает вопрос для конкретного поля"""

    async def validate_answer(self, field_name: str, answer: str) -> bool:
        """Проверяет минимальную длину ответа"""
```

---

### **Component 2: SyntheticUserSimulator**
**Status:** 🆕 NEW - Create in this iteration

**Role:** Генерирует реалистичные ответы пользователя на вопросы

**Implementation:**
```python
class SyntheticUserSimulator:
    """Симулирует реалистичные ответы российского грантозаявителя"""

    def __init__(self, quality_level: str, context: dict):
        """
        Args:
            quality_level: 'low', 'medium', 'high'
            context: {
                'region': 'Москва',
                'topic': 'молодёжь',
                'organization': 'АНО "Молодежные инициативы"'
            }
        """
        self.quality_level = quality_level
        self.context = context
        self.llm = UnifiedLLMClient(provider='gigachat', model='GigaChat')

        # Параметры для разных уровней качества
        self.quality_params = {
            'low': {
                'temperature': 0.9,
                'max_tokens': 500,
                'detail_instruction': 'Ответь кратко и просто (100-200 слов). Используй общие фразы без конкретики.'
            },
            'medium': {
                'temperature': 0.7,
                'max_tokens': 1500,
                'detail_instruction': 'Ответь со средней детализацией (200-400 слов). Включи основные факты и 1-2 примера.'
            },
            'high': {
                'temperature': 0.5,
                'max_tokens': 3000,
                'detail_instruction': 'Ответь подробно с конкретными примерами, цифрами и деталями (400-800 слов).'
            }
        }

    async def answer_question(self, question: str, field_name: str) -> str:
        """
        Генерирует реалистичный ответ на вопрос интервьюера

        Returns:
            Текстовый ответ пользователя
        """
        params = self.quality_params[self.quality_level]

        prompt = f"""Ты - представитель российской НКО, подаёшь заявку на грант.

Контекст твоего проекта:
- Регион: {self.context['region']}
- Организация: {self.context['organization']}
- Направление: {self.context['topic']}

Вопрос от менеджера грантового фонда:
"{question}"

{params['detail_instruction']}

Отвечай как реальный заявитель гранта - профессионально, но естественно.
Используй специфику российских НКО и грантовых программ.

Твой ответ:"""

        response = await self.llm.generate_text(
            prompt=prompt,
            max_tokens=params['max_tokens']
        )

        return response.strip()
```

---

### **Component 3: AnketaValidator**
**Status:** ✅ Already exists

**Role:** Аудит качества финальной анкеты

**Methods:**
```python
validator = AnketaValidator(llm_provider='gigachat', db=db)
result = await validator.validate(interview_data, user_id)

# Returns:
{
    'score': 7.5,  # 0-10
    'approval_status': 'approved',  # or 'needs_revision', 'rejected'
    'individual_scores': {
        'relevance': 8,
        'clarity': 7,
        'feasibility': 8,
        'impact': 7,
        'budget': 7
    }
}
```

---

## 📋 WORKFLOW

### **Single Interview Flow:**

```python
async def conduct_realistic_interview(quality_level: str) -> dict:
    """Проводит одно реалистичное интервью"""

    # 1. Создаём контекст проекта
    context = {
        'region': random.choice(REGIONS),
        'topic': random.choice(TOPICS),
        'organization': generate_org_name()
    }

    # 2. Инициализируем агентов
    interviewer = InteractiveInterviewer(db=db)
    user_simulator = SyntheticUserSimulator(
        quality_level=quality_level,
        context=context
    )

    # 3. Проводим интервью (15 вопросов)
    interview_data = {}
    conversation_log = []

    for field_name in REQUIRED_FIELDS:
        # Вопрос от интервьюера
        question = await interviewer.ask_question(field_name)
        conversation_log.append({'role': 'interviewer', 'text': question})

        # Ответ пользователя
        answer = await user_simulator.answer_question(question, field_name)
        conversation_log.append({'role': 'user', 'text': answer})

        # Валидация длины
        is_valid = await interviewer.validate_answer(field_name, answer)
        if not is_valid:
            # (Можно добавить retry логику)
            pass

        interview_data[field_name] = answer

    # 4. Сохраняем анкету
    anketa_id = db.save_anketa({
        'interview_data': interview_data,
        'metadata': {
            'quality_target': quality_level,
            'context': context,
            'conversation_log': conversation_log
        }
    })

    # 5. Аудит качества
    validator = AnketaValidator(llm_provider='gigachat', db=db)
    audit_result = await validator.validate(interview_data, user_id)

    # 6. Сохраняем результат аудита
    db.save_audit_result(anketa_id, audit_result)

    return {
        'anketa_id': anketa_id,
        'quality_target': quality_level,
        'audit_score': audit_result['score'],
        'approval_status': audit_result['approval_status'],
        'context': context
    }
```

---

## 🎬 TEST PLAN

### **Test 1: Low Quality Interviews (20 anketas)**

**Parameters:**
- quality_level = 'low'
- temperature = 0.9
- max_tokens = 500
- Detail level: minimal

**Expected Results:**
```python
{
    'count': 20,
    'avg_score': 4.0-6.0,
    'approval_distribution': {
        'approved': 2 (10%),
        'needs_revision': 8 (40%),
        'rejected': 10 (50%)
    }
}
```

---

### **Test 2: Medium Quality Interviews (50 anketas)**

**Parameters:**
- quality_level = 'medium'
- temperature = 0.7
- max_tokens = 1500
- Detail level: normal

**Expected Results:**
```python
{
    'count': 50,
    'avg_score': 6.5-7.5,
    'approval_distribution': {
        'approved': 30 (60%),
        'needs_revision': 15 (30%),
        'rejected': 5 (10%)
    }
}
```

---

### **Test 3: High Quality Interviews (30 anketas)**

**Parameters:**
- quality_level = 'high'
- temperature = 0.5
- max_tokens = 3000
- Detail level: detailed

**Expected Results:**
```python
{
    'count': 30,
    'avg_score': 8.0-9.5,
    'approval_distribution': {
        'approved': 27 (90%),
        'needs_revision': 3 (10%),
        'rejected': 0 (0%)
    }
}
```

---

## 📊 DATABASE SCHEMA

### **After Iteration 41:**

```sql
-- sessions table (100 new rows):
sessions (
    id SERIAL PRIMARY KEY,
    anketa_id VARCHAR UNIQUE,  -- #AN-20251025-iter41_user-001, ..., -100
    telegram_id BIGINT,        -- 999999997 (new test user for Iteration 41)
    status VARCHAR,             -- 'completed'
    interview_data JSONB,       -- {...15 fields...}
    metadata JSONB,             -- {quality_target, context, conversation_log}
    created_at TIMESTAMP
)

-- auditor_results table (100 new rows):
auditor_results (
    id SERIAL PRIMARY KEY,
    session_id INTEGER,         -- FK → sessions.id
    average_score NUMERIC,      -- 0-10
    approval_status VARCHAR,    -- 'approved', 'needs_revision', 'rejected'
    individual_scores JSONB,    -- {relevance, clarity, feasibility, impact, budget}
    created_at TIMESTAMP
)
```

### **Linking Query:**

```sql
SELECT
    s.anketa_id,
    s.metadata->>'quality_target' as quality,
    s.metadata->'context'->>'region' as region,
    s.metadata->'context'->>'topic' as topic,
    ar.average_score,
    ar.approval_status
FROM sessions s
JOIN auditor_results ar ON s.id = ar.session_id
WHERE s.telegram_id = 999999997  -- Iteration 41 test user
ORDER BY s.created_at;
```

---

## 📈 TOKEN BUDGET

### **Per Interview:**

```
1 interview = 15 questions × 2 LLM calls per question
15 × (User Answer: ~500 tokens + Optional Retry: ~200 tokens) = ~10,500 tokens per interview

Audit: ~2,000 tokens

Total per interview: ~12,500 tokens
```

### **Total for 100 Interviews:**

```
100 interviews × 12,500 tokens = 1,250,000 tokens

Distribution:
- Low (20): 20 × 12,500 = 250,000 tokens
- Medium (50): 50 × 12,500 = 625,000 tokens
- High (30): 30 × 12,500 = 375,000 tokens

Model: GigaChat (user answers + audit)
Cost: ~$125 rubles (~1.25M tokens)
```

**Note:** Это дорого, но мы получаем:
- 100 realistic interviews
- 100 audit results
- Full conversation logs
- RL-ready dataset (state/action/reward)

**Optimization:** Можем начать с меньшего:
- **Phase 1:** 30 interviews (10+15+5) → ~375K tokens (~$40)
- **Phase 2:** Если работает → остальные 70

---

## 🔬 RL READINESS

### **State:**
```python
state = {
    'quality_target': 'medium',
    'region': 'Москва',
    'topic': 'молодёжь',
    'organization_type': 'АНО'
}
```

### **Action:**
```python
action = {
    'temperature': 0.7,
    'max_tokens': 1500,
    'detail_instruction': 'normal'
}
```

### **Reward:**
```python
reward = audit_score  # 0-10 from AnketaValidator
```

### **RL Model:**
```python
Q(state, action) → expected_reward

# Grid search:
for quality in ['low', 'medium', 'high']:
    for temp in [0.3, 0.5, 0.7, 0.9]:
        for max_tokens in [500, 1000, 1500, 2000]:
            # Generate + Audit
            # Find optimal (temp, max_tokens) for each quality_level
```

---

## 📝 FILES TO CREATE

1. **`00_ITERATION_PLAN.md`** ← THIS FILE
2. **`agents/synthetic_user_simulator.py`** - New SyntheticUserSimulator class
3. **`test_iteration_41_realistic_interview.py`** - Automated test script
4. **`01_INTERVIEW_RESULTS.md`** - Test execution log
5. **`02_AUDIT_STATISTICS.md`** - Audit score analysis
6. **`03_QUALITY_CORRELATION.md`** - quality_level → score correlation
7. **`04_CONVERSATION_SAMPLES.md`** - Sample conversations
8. **`05_RL_DATASET.json`** - RL training data (state/action/reward)
9. **`06_SUMMARY.md`** - Final iteration summary

---

## 🚀 EXECUTION PLAN

### **Phase 1: Implementation (30 minutes)**

1. Create `agents/synthetic_user_simulator.py`
2. Create `test_iteration_41_realistic_interview.py`
3. Test single interview (verify workflow)

### **Phase 2: Small Batch Test (30 minutes, ~$10)**

Run 30 interviews:
- 10 low quality
- 15 medium quality
- 5 high quality

Verify:
- ✅ Conversation flow works
- ✅ Answers are realistic
- ✅ Audit scores correlate with quality_level
- ✅ Database linking works

### **Phase 3: Full Run (90-120 minutes, ~$125)**

Run remaining 70 interviews:
- 10 more low
- 35 more medium
- 25 more high

Total: 100 interviews

### **Phase 4: Analysis (30 minutes)**

- Score distribution analysis
- Quality correlation
- Regional/topic patterns
- RL dataset preparation

---

## 🎯 SUCCESS CRITERIA

### **Must Pass:**

1. ✅ 100 interviews completed successfully
2. ✅ All anketas saved to database
3. ✅ All 100 audits completed
4. ✅ Quality correlation verified:
   - low → 4-6 avg score
   - medium → 6.5-7.5 avg score
   - high → 8-9.5 avg score
5. ✅ Database linking works (sessions ↔ auditor_results)

### **Nice to Have:**

- [ ] Conversation logs saved for review
- [ ] Regional/topic patterns identified
- [ ] RL dataset exported to JSON
- [ ] Sample conversations documented

---

## 💡 KEY INNOVATIONS

### **Why This is Better Than Iteration 39:**

1. **Avoids GigaChat Truncation:** Short prompts in dialog format
2. **Tests Real Workflow:** Full Interviewer → User → Validator cycle
3. **Realistic Data:** Natural conversation flow, not batch generation
4. **RL Ready:** Clean state/action/reward structure
5. **Quality Control:** Immediate audit feedback per interview

### **Comparison:**

| Iteration | Approach | Issues | RL Ready |
|-----------|----------|--------|----------|
| 38 | Batch generator | ❌ No diversity | ❌ No |
| 39 | Batch generator | ❌ GigaChat truncation | ❌ Failed |
| 40 | Hardcoded tests | ❌ Not realistic | ❌ No |
| **41** | **Realistic dialog** | ✅ **All fixed** | ✅ **YES** |

---

## 📌 NEXT STEPS (After Iteration 41)

### **Iteration 42: RL Optimization**

Use Iteration 41 data to:
1. Analyze quality_level → score correlation
2. Grid search for optimal temperature per quality
3. Test different prompt variants
4. Implement simple policy gradient

### **Iteration 43: Grant Writing**

Use approved anketas from Iteration 41 to:
1. Generate grant documents
2. Test GrantWriter agent
3. Verify full workflow: Interview → Audit → Grant

---

**Created:** 2025-10-25
**Status:** PLANNED
**Ready to Execute:** ✅ YES

**LET'S CREATE 100 REALISTIC INTERVIEWS! 🚀**
