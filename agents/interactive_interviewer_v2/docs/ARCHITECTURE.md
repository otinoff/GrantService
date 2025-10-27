# Техническая Архитектура InteractiveInterviewerAgentV2

**Версия:** 2.0 (Reference Points Framework)
**Статус:** Production
**Дата:** 2025-10-27

---

## Оглавление

1. [Общая Архитектура](#общая-архитектура)
2. [Модули и Компоненты](#модули-и-компоненты)
3. [Reference Points Framework](#reference-points-framework)
4. [State Machine](#state-machine)
5. [Адаптивная Генерация Вопросов](#адаптивная-генерация-вопросов)
6. [Интеграции](#интеграции)
7. [Database Schema](#database-schema)
8. [Data Flow](#data-flow)
9. [Error Handling](#error-handling)
10. [Performance & Scalability](#performance--scalability)

---

## Общая Архитектура

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          TELEGRAM BOT                                │
│                      (telegram-bot/main.py)                          │
│                                                                       │
│  User: /start_interview                                              │
│    ↓                                                                  │
│  Handler: start_interview_handler()                                  │
│    ↓                                                                  │
│  FullFlowManager.conduct_interview()  ← Production Entry Point      │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       │ creates & calls
                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│              INTERACTIVE INTERVIEWER AGENT V2                        │
│           (agents/interactive_interviewer_v2/agent.py)               │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ conduct_interview(user_data, callback_ask_question)        │    │
│  │   ↓                                                         │    │
│  │ _conversation_loop()  ← Main logic                         │    │
│  │   ↓                                                         │    │
│  │ Uses:                                                       │    │
│  │   • ReferencePointManager     (что собрать)                │    │
│  │   • ConversationFlowManager   (state machine)              │    │
│  │   • AdaptiveQuestionGenerator (как спросить)               │    │
│  │   • UnifiedLLMClient          (LLM provider)               │    │
│  │   • QdrantClient              (knowledge base)             │    │
│  └────────────────────────────────────────────────────────────┘    │
└──────────┬──────────────────┬──────────────────┬────────────────────┘
           │                  │                  │
           │                  │                  │
           ↓                  ↓                  ↓
    ┌────────────┐    ┌──────────────┐   ┌──────────────┐
    │ PostgreSQL │    │ GigaChat/    │   │   Qdrant     │
    │            │    │ Claude Code  │   │  (optional)  │
    │ sessions   │    │              │   │              │
    │ table      │    │ LLM API      │   │ Vector DB    │
    └────────────┘    └──────────────┘   └──────────────┘
```

### Layers

**1. Presentation Layer (Telegram Bot)**
- User interaction
- Message handling
- File sending
- Button callbacks

**2. Business Logic Layer (Agent)**
- Interview orchestration
- Question generation
- Answer validation
- State management

**3. Framework Layer (Reference Points)**
- Information structure
- Priority management
- Completion tracking
- Dependency resolution

**4. Infrastructure Layer**
- Database (PostgreSQL)
- LLM API (GigaChat/Claude)
- Vector DB (Qdrant)
- Logging

---

## Модули и Компоненты

### Core Agent Module

**File:** `agents/interactive_interviewer_v2/agent.py`

**Class:** `InteractiveInterviewerAgentV2(BaseAgent)`

**Key Methods:**

```python
class InteractiveInterviewerAgentV2(BaseAgent):
    def __init__(self, db, llm_provider, qdrant_host, qdrant_port):
        """Initialize agent with dependencies"""

    async def conduct_interview(
        self,
        user_data: Dict[str, Any],
        callback_ask_question: callable
    ) -> Dict[str, Any]:
        """
        Main entry point - conducts full interview

        Returns:
            {
                'anketa': {...},
                'questions_asked': int,
                'follow_ups_asked': int,
                'processing_time': float,
                'conversation_state': str
            }
        """

    async def _conversation_loop(
        self,
        user_data: Dict[str, Any],
        callback_ask_question: callable
    ) -> Dict[str, Any]:
        """Main conversation loop - iterates through RPs"""

    async def _generate_question_for_rp(
        self,
        rp: ReferencePoint,
        context: ConversationContext
    ) -> str:
        """Generate question for specific RP using LLM"""

    def _collect_anketa_from_rps(self) -> Dict[str, Any]:
        """Collect final anketa from completed RPs"""
```

---

### Reference Points Module

**Location:** `agents/interactive_interviewer_v2/reference_points/`

#### 1. ReferencePoint (reference_point.py)

**Data structure representing information to collect**

```python
from enum import Enum
from dataclasses import dataclass

class ReferencePointPriority(Enum):
    P0 = 0  # MUST HAVE
    P1 = 1  # SHOULD HAVE
    P2 = 2  # NICE TO HAVE
    P3 = 3  # OPTIONAL

class ReferencePointState(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class ReferencePoint:
    id: str
    name: str
    description: str
    priority: ReferencePointPriority
    state: ReferencePointState = ReferencePointState.NOT_STARTED
    completion_confidence: float = 0.0  # 0-1
    data: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    completion_criteria: CompletionCriteria = None

    def add_data(self, key: str, value: Any):
        """Store collected information"""
        self.data[key] = value

    def is_complete(self) -> bool:
        """Check if RP is sufficiently completed"""
        return self.completion_confidence >= 0.7
```

---

#### 2. ReferencePointManager (reference_point_manager.py)

**Manages collection of RPs and determines next RP to process**

```python
class ReferencePointManager:
    def __init__(self):
        self.reference_points: Dict[str, ReferencePoint] = {}
        self._rp_order: List[str] = []

    def load_fpg_reference_points(self):
        """Load 11 standard FPG reference points"""
        # P0 - Critical
        self.add_reference_point(ReferencePoint(
            id="project_name",
            name="Название проекта",
            priority=ReferencePointPriority.P0
        ))
        # ... 10 more RPs

    def get_next_reference_point(self) -> Optional[ReferencePoint]:
        """
        Determine next RP to work on

        Logic:
        1. Exclude blocked (dependencies not met)
        2. Prioritize P0 → P1 → P2 → P3
        3. Within priority: in_progress → not_started
        4. Return first match
        """

    def mark_completed(self, rp_id: str, confidence: float = 1.0):
        """Mark RP as completed"""

    def get_progress(self) -> ReferencePointsProgress:
        """
        Calculate overall progress

        Returns:
            ReferencePointsProgress(
                total_rps=11,
                completed_rps=8,
                overall_completion=0.73,
                critical_completed=True  # All P0 done
            )
        """
```

---

#### 3. ConversationFlowManager (conversation_flow_manager.py)

**State machine managing conversation flow**

```python
class ConversationState(Enum):
    INIT = "init"
    EXPLORING = "exploring"
    DEEPENING = "deepening"
    VALIDATING = "validating"
    FINALIZING = "finalizing"

class TransitionType(Enum):
    LINEAR = "linear"              # Next RP
    SKIP = "skip"                  # Already answered
    LOOP_BACK = "loop_back"        # Clarify previous
    DEEP_DIVE = "deep_dive"        # Follow-up
    FAST_FORWARD = "fast_forward"  # Skip to end
    FINALIZE = "finalize"          # Complete

@dataclass
class ConversationContext:
    current_state: ConversationState = ConversationState.INIT
    current_rp: Optional[ReferencePoint] = None
    questions_asked: int = 0
    follow_ups_asked: int = 0
    max_follow_ups: int = 5
    dialogue_history: List[Dict] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)

class ConversationFlowManager:
    def __init__(self, rp_manager: ReferencePointManager):
        self.rp_manager = rp_manager
        self.context = ConversationContext()

    def decide_next_action(
        self,
        last_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Decide what to do next

        Returns:
            {
                'type': 'ask' | 'finalize',
                'transition': TransitionType,
                'reference_point': ReferencePoint,
                'message': str
            }
        """

    def _should_finalize(self) -> bool:
        """Check if interview can be finalized"""
        progress = self.rp_manager.get_progress()
        return (
            progress.critical_completed and  # All P0 done
            progress.important_completed     # All P1 done (ideally)
        ) or self.context.questions_asked >= 30  # Safety limit

    def _transition_state(self, new_state: ConversationState):
        """Transition to new state"""
        self.context.current_state = new_state
```

---

#### 4. AdaptiveQuestionGenerator (adaptive_question_generator.py)

**Generates questions using LLM with context**

```python
class AdaptiveQuestionGenerator:
    def __init__(
        self,
        llm_client: UnifiedLLMClient,
        qdrant_client: Optional[QdrantClient] = None
    ):
        self.llm = llm_client
        self.qdrant = qdrant_client

    async def generate_question(
        self,
        rp: ReferencePoint,
        context: ConversationContext
    ) -> str:
        """
        Generate adaptive question for RP

        Process:
        1. Retrieve FPG context from Qdrant (optional)
        2. Build prompt with:
           - RP description
           - Dialogue history
           - Last answer
           - FPG guidelines
        3. Call LLM
        4. Return natural question
        """

    async def _get_fpg_context(
        self,
        rp: ReferencePoint,
        context: ConversationContext
    ) -> str:
        """
        Retrieve relevant FPG guidelines from Qdrant

        Args:
            rp: Reference point
            context: Conversation context

        Returns:
            Relevant text from FPG documentation
        """
        if not self.qdrant:
            return ""

        # Search query
        query = f"{rp.name} {rp.description} fpg requirements"

        # Vector search
        results = self.qdrant.search(
            collection_name="knowledge_sections",
            query_vector=self._embed_text(query),
            limit=3
        )

        return "\n".join([r.payload['text'] for r in results])

    def _build_prompt(
        self,
        rp: ReferencePoint,
        context: ConversationContext,
        fpg_context: str
    ) -> str:
        """Build prompt for LLM"""
        return f"""
Ты - эксперт по грантовым заявкам для Фонда Президентских Грантов.

ЗАДАЧА: Задай вопрос заявителю чтобы узнать "{rp.name}".

ОПИСАНИЕ: {rp.description}

КОНТЕКСТ ДИАЛОГА:
{self._format_history(context.dialogue_history)}

ПОСЛЕДНИЙ ОТВЕТ: {context.dialogue_history[-1]['answer'] if context.dialogue_history else 'N/A'}

УЖЕ ИЗВЕСТНО:
{self._format_collected_data(context.collected_data)}

ТРЕБОВАНИЯ ФПГ:
{fpg_context}

ПРАВИЛА:
1. Вопрос должен быть естественным и дружелюбным
2. НЕ повторяй то, что уже было сказано
3. Учитывай контекст предыдущих ответов
4. Будь кратким (1-2 предложения)
5. Используй требования ФПГ для формулировки

ВОПРОС:
"""
```

---

#### 5. Fallback Questions (fallback_questions.py)

**Bank of fallback questions when LLM fails**

```python
FALLBACK_QUESTIONS = {
    "project_name": "Как называется ваш проект?",
    "project_goal": "Какую цель преследует ваш проект?",
    "problem_description": "Какую проблему решает ваш проект?",
    "target_audience": "Кто ваша целевая аудитория?",
    "methodology": "Как вы планируете реализовать проект?",
    "project_budget": "Какой бюджет требуется для проекта?",
    "team_description": "Расскажите про вашу команду.",
    "expected_results": "Какие результаты вы ожидаете?",
    "project_sustainability": "Как проект будет работать после окончания гранта?",
    "project_partners": "Есть ли у вас партнёры?",
    "project_risks": "Какие риски есть у проекта?"
}

def get_fallback_question(rp_id: str) -> str:
    """Get fallback question for RP ID"""
    return FALLBACK_QUESTIONS.get(rp_id, "Расскажите подробнее.")
```

---

## Reference Points Framework

### Standard FPG Reference Points

**11 Reference Points загружаются при инициализации:**

```python
FPG_REFERENCE_POINTS = [
    # P0 - CRITICAL (MUST HAVE)
    {
        "id": "project_name",
        "name": "Название проекта",
        "description": "Как называется проект, его краткое имя",
        "priority": "P0",
        "map_to": "Название"
    },
    {
        "id": "project_goal",
        "name": "Цель проекта",
        "description": "Что хотят достичь, зачем нужен проект",
        "priority": "P0",
        "map_to": "Цель"
    },
    {
        "id": "problem_description",
        "name": "Описание проблемы",
        "description": "Какую проблему решает проект",
        "priority": "P0",
        "map_to": "Описание проблемы"
    },
    {
        "id": "target_audience",
        "name": "Целевая аудитория",
        "description": "Кто будет бенефициарами проекта",
        "priority": "P0",
        "map_to": "Целевая аудитория"
    },
    {
        "id": "project_budget",
        "name": "Общий бюджет",
        "description": "Сколько денег требуется для проекта",
        "priority": "P0",
        "map_to": "Общий бюджет"
    },

    # P1 - IMPORTANT (SHOULD HAVE)
    {
        "id": "methodology",
        "name": "Методология",
        "description": "Как будут реализовывать проект (мероприятия, подходы)",
        "priority": "P1",
        "map_to": "Методология"
    },
    {
        "id": "team_description",
        "name": "Описание команды",
        "description": "Кто будет реализовывать проект",
        "priority": "P1",
        "map_to": "Команда"
    },
    {
        "id": "expected_results",
        "name": "Ожидаемые результаты",
        "description": "Какие конкретные результаты ожидаются",
        "priority": "P1",
        "map_to": "Результаты"
    },
    {
        "id": "project_sustainability",
        "name": "Устойчивость",
        "description": "Как проект будет работать после окончания гранта",
        "priority": "P1",
        "map_to": "Устойчивость"
    },

    # P2 - NICE TO HAVE
    {
        "id": "project_partners",
        "name": "Партнёры",
        "description": "Кто поддерживает проект, с кем сотрудничество",
        "priority": "P2",
        "map_to": "Партнёры"
    },
    {
        "id": "project_risks",
        "name": "Риски",
        "description": "Какие риски есть у проекта",
        "priority": "P2",
        "map_to": "Риски"
    }
]
```

### Completion Criteria

```python
@dataclass
class CompletionCriteria:
    """Criteria for marking RP as completed"""
    min_words: int = 5           # Minimum words in answer
    min_confidence: float = 0.7  # Minimum confidence score
    required_fields: List[str] = field(default_factory=list)

    def is_satisfied(self, data: Dict, confidence: float) -> bool:
        """Check if completion criteria met"""
        # Check word count
        text = data.get('text', '')
        if len(text.split()) < self.min_words:
            return False

        # Check confidence
        if confidence < self.min_confidence:
            return False

        # Check required fields
        for field in self.required_fields:
            if field not in data or not data[field]:
                return False

        return True
```

---

## State Machine

### State Diagram

```
     ┌─────────┐
     │  INIT   │ (Приветствие)
     └────┬────┘
          │
          v
     ┌─────────────┐
     │  EXPLORING  │ (Базовые вопросы по RP)
     └─────┬───────┘
           │
           ├─→ (ответ неполный) ─→ ┌─────────────┐
           │                        │  DEEPENING  │ (Follow-up вопросы)
           │                        └──────┬──────┘
           │                               │
           │ ←─────────────────────────────┘
           │
           │ (все P0+P1 готовы)
           v
     ┌──────────────┐
     │  VALIDATING  │ (Валидация - ПРОПУСКАЕТСЯ в V2)
     └──────┬───────┘
            │
            v
     ┌──────────────┐
     │  FINALIZING  │ (Сборка анкеты, сохранение)
     └──────────────┘
```

### State Transitions

**Code:**

```python
def _decide_transition(
    self,
    current_state: ConversationState,
    rp: ReferencePoint,
    last_answer: Optional[str]
) -> Tuple[ConversationState, TransitionType]:
    """Decide next state and transition type"""

    if current_state == ConversationState.EXPLORING:
        # Check if answer is incomplete
        if last_answer and self._is_incomplete(last_answer):
            # Check if we have follow-up budget
            if self.context.get_remaining_follow_ups() > 0:
                return (ConversationState.DEEPENING, TransitionType.DEEP_DIVE)

        # Check if all critical RPs done
        progress = self.rp_manager.get_progress()
        if progress.critical_completed and progress.important_completed:
            return (ConversationState.FINALIZING, TransitionType.FINALIZE)

        # Continue exploring
        return (ConversationState.EXPLORING, TransitionType.LINEAR)

    elif current_state == ConversationState.DEEPENING:
        # After follow-up, return to exploring
        return (ConversationState.EXPLORING, TransitionType.LINEAR)

    elif current_state == ConversationState.INIT:
        # Always move to exploring after init
        return (ConversationState.EXPLORING, TransitionType.LINEAR)

    else:
        return (current_state, TransitionType.LINEAR)
```

---

## Адаптивная Генерация Вопросов

### LLM Prompt Structure

```python
QUESTION_GENERATION_PROMPT = """
Ты - эксперт по грантовым заявкам для Фонда Президентских Грантов (ФПГ).

РОЛЬ: Интервьюер, собирающий информацию для грантовой заявки.

ЗАДАЧА: Задай вопрос заявителю чтобы узнать "{rp.name}".

КОНТЕКСТ:
{context}

ПРАВИЛА:
1. Вопрос должен быть естественным и дружелюбным
2. НЕ повторяй то, что уже было сказано в диалоге
3. Учитывай предыдущие ответы для связности
4. Будь кратким (1-2 предложения максимум)
5. Используй требования ФПГ для формулировки

ВОПРОС:
"""
```

### Example Generations

**RP:** `project_budget`
**Context:** User talked about school archery project for 500 students
**Question:** "Отлично! А какой бюджет вы планируете для проекта со стрельбой из лука для 500 школьников?"

**RP:** `methodology`
**Context:** User wants to promote healthy lifestyle
**Question:** "Как именно вы планируете продвигать здоровый образ жизни? Какие мероприятия будете проводить?"

---

## Интеграции

### 1. PostgreSQL (Database)

**Connection:**
```python
from data.database import Database

db = Database(
    host="localhost",
    port=5432,
    database="grantservice",
    user="postgres",
    password=os.getenv("DB_PASSWORD", "root")
)
```

**Session Operations:**
```python
# Create session
session_id = db.create_interview_session(
    telegram_id=123,
    anketa_id="anketa_607_1761528637",
    project_name="Стрельба из лука"
)

# Update interview data (after each answer!)
db.update_interview_data(
    session_id=session_id,
    interview_data={
        'project_name': 'Стрельба из лука',
        'project_goal': '...'
    }
)

# Mark completed
db.update_session_status(
    session_id=session_id,
    status='completed',
    completed_at=datetime.now()
)
```

---

### 2. UnifiedLLMClient (LLM)

**Initialization:**
```python
from shared.llm.unified_llm_client import UnifiedLLMClient
from shared.llm.config import AGENT_CONFIGS

llm = UnifiedLLMClient(
    provider="gigachat",  # or "claude_code"
    config=AGENT_CONFIGS["interactive_interviewer_v2"]
)
```

**Question Generation:**
```python
response = await llm.generate(
    prompt=question_prompt,
    temperature=0.7,
    max_tokens=150
)

question = response['text']
```

**Provider Fallback:**
```python
try:
    # Try GigaChat first
    question = await llm.generate(prompt, provider="gigachat")
except Exception as e:
    # Fallback to Claude
    logger.warning(f"GigaChat failed: {e}, using Claude")
    question = await llm.generate(prompt, provider="claude_code")
```

---

### 3. QdrantClient (Vector DB)

**Connection:**
```python
from qdrant_client import QdrantClient

qdrant = QdrantClient(
    host="5.35.88.251",
    port=6333,
    timeout=10
)
```

**Search for Context:**
```python
# Search for relevant FPG guidelines
results = qdrant.search(
    collection_name="knowledge_sections",
    query_vector=embed_text(f"{rp.name} fpg requirements"),
    limit=3,
    score_threshold=0.7
)

# Extract text
fpg_context = "\n".join([
    result.payload['text']
    for result in results
])
```

**Graceful Degradation:**
```python
try:
    qdrant_context = await self._get_fpg_context(rp)
except (ConnectionError, TimeoutError):
    logger.warning("Qdrant unavailable, using fallback")
    qdrant_context = ""  # Continue without context
```

---

## Database Schema

### Table: `sessions`

```sql
CREATE TABLE sessions (
    -- Identity
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    anketa_id VARCHAR(255) UNIQUE,

    -- Project Info
    project_name TEXT,
    grant_fund VARCHAR(100) DEFAULT 'fpg',

    -- Interview Data (CRITICAL - saved after each answer!)
    interview_data JSONB DEFAULT '{}',  -- All answers from RPs
    answers_data JSONB DEFAULT '{}',    -- Formatted for anketa

    -- Status
    completion_status VARCHAR(50) DEFAULT 'pending',
    -- Values: 'pending', 'in_progress', 'completed', 'cancelled'

    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    questions_asked INTEGER DEFAULT 0,
    follow_ups_asked INTEGER DEFAULT 0,
    conversation_state VARCHAR(50)
);

CREATE INDEX idx_sessions_telegram_id ON sessions(telegram_id);
CREATE INDEX idx_sessions_status ON sessions(completion_status);
CREATE INDEX idx_sessions_started_at ON sessions(started_at DESC);
```

### Sample Data

```json
{
    "id": 607,
    "telegram_id": 123456789,
    "anketa_id": "anketa_607_1761528637",
    "project_name": "Стрельба из лука для школьников",
    "interview_data": {
        "project_name": "Стрельба из лука для школьников",
        "project_goal": "Приобщить детей к спорту и здоровому образу жизни",
        "problem_description": "Мало эффективных программ привлечения к спорту",
        "target_audience": "Дети и молодёжь 10-21 лет",
        "project_budget": "750000",
        "methodology": "Мастер-классы, турниры, информационная кампания",
        "team_description": "Клуб луки и стрелы",
        "expected_results": "Патриотическое воспитание, пропаганда ЗОЖ",
        "project_sustainability": "Клуб готов работать дальше",
        "project_partners": "Лига стрельбы Кемерово, Федерация Кузбасса",
        "project_risks": "Риск что не дадут денег"
    },
    "completion_status": "completed",
    "started_at": "2025-10-27 08:30:37",
    "completed_at": "2025-10-27 08:32:15",
    "questions_asked": 11,
    "follow_ups_asked": 2,
    "conversation_state": "finalizing"
}
```

---

## Data Flow

### Complete Interview Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. USER STARTS INTERVIEW                                          │
└────────────┬─────────────────────────────────────────────────────┘
             │
             v
┌──────────────────────────────────────────────────────────────────┐
│ 2. CREATE SESSION IN DB                                           │
│    session_id = db.create_interview_session(telegram_id)         │
│    status = 'in_progress'                                         │
└────────────┬─────────────────────────────────────────────────────┘
             │
             v
┌──────────────────────────────────────────────────────────────────┐
│ 3. INITIALIZE AGENT                                               │
│    agent = InteractiveInterviewerAgentV2(db, llm)                │
│    - Load 11 FPG Reference Points                                 │
│    - Initialize ConversationFlowManager                           │
│    - Connect to Qdrant (optional)                                 │
└────────────┬─────────────────────────────────────────────────────┘
             │
             v
┌──────────────────────────────────────────────────────────────────┐
│ 4. CONVERSATION LOOP                                              │
│    while not finalized:                                           │
│                                                                    │
│      A. Get next RP (priority P0 → P1 → P2)                      │
│         rp = rp_manager.get_next_reference_point()               │
│                                                                    │
│      B. Generate question (LLM + context)                         │
│         question = await generate_question(rp, context)          │
│                                                                    │
│      C. Ask user (via callback)                                   │
│         answer = await callback_ask_question(question)           │
│                                                                    │
│      D. Save answer to RP (in-memory)                            │
│         rp.add_data('text', answer)                              │
│                                                                    │
│      E. Save to DB (CRITICAL!)                                    │
│         db.update_interview_data(session_id, {                   │
│             rp.id: answer                                         │
│         })                                                        │
│                                                                    │
│      F. Evaluate completeness                                     │
│         confidence = evaluate_answer_completeness(answer)        │
│                                                                    │
│      G. Mark RP if complete                                       │
│         if confidence >= 0.7:                                     │
│             rp_manager.mark_completed(rp.id)                     │
│                                                                    │
│      H. Decide next action                                        │
│         action = flow_manager.decide_next_action(answer)         │
│         if action['type'] == 'finalize': break                   │
│                                                                    │
└────────────┬─────────────────────────────────────────────────────┘
             │
             v
┌──────────────────────────────────────────────────────────────────┐
│ 5. FINALIZE                                                       │
│    A. Collect anketa from completed RPs                           │
│       anketa = collect_anketa_from_rps()                         │
│                                                                    │
│    B. Save final version to DB                                    │
│       db.finalize_session(session_id, anketa)                    │
│       status = 'completed'                                        │
│                                                                    │
│    C. Generate anketa.txt                                         │
│       anketa_txt = generate_anketa_txt(anketa)                   │
│                                                                    │
│    D. Send to user                                                │
│       bot.send_document(telegram_id, anketa_txt)                 │
│                                                                    │
└────────────┬─────────────────────────────────────────────────────┘
             │
             v
┌──────────────────────────────────────────────────────────────────┐
│ 6. RESULT                                                         │
│    return {                                                       │
│        'anketa': {...},                                          │
│        'questions_asked': 11,                                    │
│        'follow_ups_asked': 2,                                    │
│        'processing_time': 45.3,                                  │
│        'conversation_state': 'finalizing'                        │
│    }                                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

### Exception Hierarchy

```python
class InterviewerError(Exception):
    """Base exception for interviewer errors"""
    pass

class QuestionGenerationError(InterviewerError):
    """Failed to generate question"""
    pass

class LLMConnectionError(InterviewerError):
    """LLM API connection failed"""
    pass

class DatabaseError(InterviewerError):
    """Database operation failed"""
    pass

class TimeoutError(InterviewerError):
    """User didn't respond in time"""
    pass
```

### Error Handling Strategy

**1. LLM Generation Failure:**
```python
try:
    question = await self.question_generator.generate_question(rp, context)
except QuestionGenerationError as e:
    logger.error(f"Question generation failed: {e}")
    # Fallback to template question
    question = get_fallback_question(rp.id)
```

**2. Database Failure:**
```python
try:
    db.update_interview_data(session_id, data)
except DatabaseError as e:
    logger.error(f"DB save failed: {e}", exc_info=True)
    # Store in memory, retry later
    self._pending_saves.append((session_id, data))
    # Continue interview (don't fail user experience)
```

**3. Qdrant Unavailable:**
```python
try:
    fpg_context = await self._get_fpg_context(rp)
except (ConnectionError, TimeoutError) as e:
    logger.warning(f"Qdrant unavailable: {e}")
    fpg_context = ""  # Graceful degradation
    # Continue without FPG context
```

**4. User Timeout:**
```python
try:
    answer = await asyncio.wait_for(
        callback_ask_question(question),
        timeout=300  # 5 minutes
    )
except asyncio.TimeoutError:
    logger.warning(f"User timeout for session {session_id}")
    # Save partial progress
    db.update_session_status(session_id, 'timeout')
    raise TimeoutError("User didn't respond in 5 minutes")
```

---

## Performance & Scalability

### Current Metrics

**Average Interview:**
- Duration: 45-60 seconds
- Questions: 10-13
- Follow-ups: 1-3
- DB writes: 11-15
- LLM calls: 11-15
- Qdrant queries: 11-15 (if available)

**Bottlenecks:**
1. LLM API latency (2-4 sec per call)
2. Qdrant search (0.5-1 sec per query)
3. Database writes (0.1-0.2 sec per write)

### Optimization Strategies

**1. Parallel Operations:**
```python
# Current: Sequential
question = await generate_question(rp)  # 3 sec
qdrant_context = await get_context(rp)  # 1 sec
# Total: 4 sec

# Optimized: Parallel
question, qdrant_context = await asyncio.gather(
    generate_question(rp),
    get_context(rp)
)
# Total: 3 sec
```

**2. Caching:**
```python
# Cache Qdrant results for common RPs
@lru_cache(maxsize=128)
def get_cached_fpg_context(rp_id: str) -> str:
    return qdrant.search(...)
```

**3. Batch DB Writes:**
```python
# Current: Write after each answer
db.update(session_id, {rp.id: answer})  # 11 writes

# Optimized: Batch every 3 answers
self._pending_updates.append({rp.id: answer})
if len(self._pending_updates) >= 3:
    db.batch_update(session_id, self._pending_updates)
    self._pending_updates.clear()
```

**4. Connection Pooling:**
```python
# DB connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=5,
    maxconn=20,
    host="localhost",
    database="grantservice"
)
```

### Scalability

**Current Capacity:**
- ~100 concurrent interviews (single instance)
- Bottleneck: LLM API rate limits

**Horizontal Scaling:**
```
┌─────────────┐
│  Load       │
│  Balancer   │
└──────┬──────┘
       │
       ├─→ Agent Instance 1 (GigaChat)
       ├─→ Agent Instance 2 (Claude)
       └─→ Agent Instance 3 (Claude)
           │
           └─→ Shared PostgreSQL + Qdrant
```

**Future: Message Queue:**
```
User → Telegram Bot → RabbitMQ → Agent Workers → PostgreSQL
                                     ↓
                                   Qdrant
```

---

## Dependencies

### Internal

```python
# Agents
from base_agent import BaseAgent
from auditor_agent import AuditorAgent

# Database
from data.database import Database

# LLM
from shared.llm.unified_llm_client import UnifiedLLMClient
from shared.llm.config import AGENT_CONFIGS

# Telegram
from shared.telegram.file_generators import generate_anketa_txt
```

### External

```python
# requirements.txt
qdrant-client==1.7.0      # Vector DB
psycopg2-binary==2.9.9    # PostgreSQL
asyncio                    # Async operations
pydantic==2.5.0           # Data validation
python-telegram-bot==20.7 # Telegram API
```

---

## Testing Architecture

### Test Structure

```
agents/interactive_interviewer_v2/tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests (70%)
│   ├── test_reference_point.py
│   ├── test_rp_manager.py
│   ├── test_flow_manager.py
│   └── test_question_generator.py
├── integration/                   # Integration tests (20%)
│   ├── test_database_integration.py
│   ├── test_llm_integration.py
│   └── test_qdrant_integration.py
└── e2e/                          # E2E tests (10%)
    └── test_full_interview_workflow.py
```

### Key Fixtures

```python
# conftest.py
@pytest.fixture
def mock_db():
    """Mock database for testing"""
    return MockDatabase()

@pytest.fixture
def mock_llm():
    """Mock LLM client"""
    return MockLLMClient()

@pytest.fixture
def rp_manager():
    """Real ReferencePointManager with FPG RPs"""
    manager = ReferencePointManager()
    manager.load_fpg_reference_points()
    return manager

@pytest.fixture
async def agent(mock_db, mock_llm):
    """Agent instance for testing"""
    return InteractiveInterviewerAgentV2(
        db=mock_db,
        llm_provider="mock"
    )
```

---

**Дата:** 2025-10-27
**Версия:** 2.0
**Автор:** Grant Service Team
**Статус:** Production ✅
