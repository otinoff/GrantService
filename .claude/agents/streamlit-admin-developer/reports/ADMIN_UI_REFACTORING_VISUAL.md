# 📊 Admin UI Refactoring: Visual Guide

## Current Architecture (Chaotic)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT STATE: 17 PAGES                      │
└─────────────────────────────────────────────────────────────────┘

Main Section:
┌─────────────────────┐
│ 🏠 Главная         │ (Dashboard)
│ 🎯 Pipeline        │ (Main working page)
└─────────────────────┘

Users & Data:
┌─────────────────────────────────┐
│ 👥 Пользователи                │
│ 📋 Анкеты_пользователей        │
│ 📄 Просмотр_заявки             │ ← Separate from Анкеты?
│ ❓ Вопросы_интервью            │
└─────────────────────────────────┘

AI Agents (CHAOS):
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI_Agents (Central Hub)                                     │
│    ├─ Shows ALL 5 agents                                        │
│    ├─ Prompts for ALL agents                                    │
│    └─ Stats for ALL agents                                      │
├─────────────────────────────────────────────────────────────────┤
│ ✍️ Writer_Agent (Separate Page!)                              │ ← Why separate?
│    ├─ Duplicates prompt management ⚠️                          │
│    └─ Writer-specific UI                                        │
├─────────────────────────────────────────────────────────────────┤
│ 🔍 Researcher_Agent (Separate Page!)                           │ ← Why separate?
│    └─ Duplicates prompt management ⚠️                          │
├─────────────────────────────────────────────────────────────────┤
│ 🔬 Исследования_исследователя (ANOTHER Researcher page!)       │ ← Confusion!
│    └─ Shows research data                                       │
├─────────────────────────────────────────────────────────────────┤
│ 🔬 Аналитика_исследователя (THIRD Researcher page!)            │ ← Too many!
│    └─ Analytics and costs                                       │
└─────────────────────────────────────────────────────────────────┘
                              ⬇️
                    ❌ PROBLEMS:
        • 5 pages for 5 agents (inconsistent)
        • Researcher split across 3 pages
        • Interviewer, Auditor, Planner have NO dedicated pages
        • Massive duplication of prompt management code

Grants (DUPLICATION):
┌─────────────────────────────────────────────────────────────────┐
│ 📄 Грантовые_заявки                                            │
│    ├─ List grants ✅                                           │
│    ├─ View details ✅                                          │
│    ├─ Filter ✅                                                │
│    └─ Export ✅                                                │
├─────────────────────────────────────────────────────────────────┤
│ 📋 Управление_грантами                                         │
│    ├─ List grants ✅  ← DUPLICATE!                            │
│    ├─ View details ✅  ← DUPLICATE!                           │
│    ├─ Filter ✅  ← DUPLICATE!                                 │
│    ├─ Send to Telegram ✅                                      │
│    └─ Archive ✅                                               │
└─────────────────────────────────────────────────────────────────┘
                              ⬇️
                    ❌ PROBLEM: 70% overlap!

Analytics:
┌─────────────────────────────────────────────────────────────────┐
│ 📊 Общая_аналитика                                             │
│ 📋 Мониторинг_логов                                            │
└─────────────────────────────────────────────────────────────────┘

Auth:
┌─────────────────────┐
│ 🔐 Вход            │
└─────────────────────┘

════════════════════════════════════════════════════════════════════

TOTAL: 17 PAGES | 5,745 LINES | ~26% DUPLICATION
```

---

## Proposed Architecture (Clean)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROPOSED STATE: 10 PAGES                     │
└─────────────────────────────────────────────────────────────────┘

📊 Main
┌─────────────────────────────────────────────────────────────────┐
│ 🏠 Главная (Dashboard)                                         │
│    ├─ System health                                             │
│    ├─ Quick stats                                               │
│    └─ Recent activity                                            │
├─────────────────────────────────────────────────────────────────┤
│ 🎯 Pipeline Dashboard ⭐ (Main Working Page)                   │
│    ├─ Full pipeline view                                        │
│    ├─ Stage-by-stage breakdown                                  │
│    └─ Agent execution controls                                  │
└─────────────────────────────────────────────────────────────────┘

👥 Users & Data
┌─────────────────────────────────────────────────────────────────┐
│ 👥 Пользователи                                                │
│    ├─ User list                                                 │
│    ├─ Permissions                                               │
│    └─ User details                                              │
├─────────────────────────────────────────────────────────────────┤
│ 📋 Анкеты и заявки (MERGED)                                    │
│    ├─ [Tab] 📋 Список анкет                                   │
│    ├─ [Tab] 📄 Просмотр заявки                                │
│    └─ [Tab] 🔍 Поиск                                          │
└─────────────────────────────────────────────────────────────────┘

🤖 AI Agents (UNIFIED)
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI Agents (Single Page, Tabbed Interface)                   │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ [📝 Interviewer] [✅ Auditor] [📐 Planner] [🔍 Researcher] [✍️ Writer] │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Each Agent Tab Contains:                                        │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 📊 Stats & Monitoring                                    │   │
│ │    • Total runs                                          │   │
│ │    • Success rate                                        │   │
│ │    • Average execution time                              │   │
│ │    • Recent activity                                     │   │
│ ├──────────────────────────────────────────────────────────┤   │
│ │ ⚙️ Prompt Management (SHARED COMPONENT)                 │   │
│ │    • View prompts                                        │   │
│ │    • Edit prompts                                        │   │
│ │    • Version history                                     │   │
│ │    • Create new prompts                                  │   │
│ ├──────────────────────────────────────────────────────────┤   │
│ │ 🧪 Test & Execute                                        │   │
│ │    • Test prompt                                         │   │
│ │    • Manual execution                                    │   │
│ │    • View results                                        │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│ Special: Researcher Tab (with sub-tabs)                         │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ [⚙️ Настройки] [🔬 Исследования] [📊 Аналитика]       │   │
│ │                                                          │   │
│ │ Настройки:   → Standard agent interface                 │   │
│ │ Исследования: → Research data viewer                     │   │
│ │ Аналитика:    → Analytics & costs                        │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ⬇️
                    ✅ BENEFITS:
        • 1 page for all agents (consistent)
        • Researcher sub-tabs (organized)
        • All agents use same UI components (maintainable)
        • Shared prompt management (DRY)

📄 Grants (UNIFIED)
┌─────────────────────────────────────────────────────────────────┐
│ 📋 Управление грантами (MERGED)                                │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ [📄 Все заявки] [✅ Готовые] [📤 Отправка] [🗄️ Архив]  │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Все заявки:    → List all grants (from Грантовые_заявки)       │
│ Готовые:       → Ready grants                                   │
│ Отправка:      → Send to Telegram                               │
│ Архив:         → Archived grants                                │
└─────────────────────────────────────────────────────────────────┘
                              ⬇️
                    ✅ BENEFITS:
        • All grant operations in one place
        • No confusion about which page to use
        • No duplication of listing logic

📊 Analytics & Monitoring
┌─────────────────────────────────────────────────────────────────┐
│ 📊 Аналитика                                                   │
│    ├─ [Tab] Общая аналитика                                   │
│    ├─ [Tab] Аналитика агентов                                 │
│    └─ [Tab] Финансы и расходы                                 │
├─────────────────────────────────────────────────────────────────┤
│ 📋 Мониторинг                                                  │
│    ├─ [Tab] Логи системы                                      │
│    ├─ [Tab] Логи агентов                                      │
│    └─ [Tab] Ошибки                                            │
└─────────────────────────────────────────────────────────────────┘

⚙️ Settings
┌─────────────────────────────────────────────────────────────────┐
│ ❓ Вопросы интервью                                            │
│    ├─ Question management                                       │
│    ├─ Order & categorization                                    │
│    └─ Dynamic rules                                             │
├─────────────────────────────────────────────────────────────────┤
│ 🔐 Вход                                                        │
│    └─ Authentication                                            │
└─────────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════

TOTAL: 10 PAGES | ~3,800 LINES | <5% DUPLICATION
```

---

## Code Duplication: Before & After

### BEFORE: Duplicated Everywhere

```
┌─────────────────────────────────────────────────────────────────┐
│                   DUPLICATED CODE EXAMPLES                      │
└─────────────────────────────────────────────────────────────────┘

1. Database Connection (3 copies)
   ┌────────────────────────────────────────────────────────────┐
   │ 🎯_Pipeline_Dashboard.py                                   │
   │ 📋_Управление_грантами.py                                 │
   │ 🤖_AI_Agents.py                                           │
   │                                                            │
   │ @st.cache_resource                                         │
   │ def get_db_connection():                                   │
   │     db_path = Path(...) / "data" / "grantservice.db"       │
   │     return sqlite3.connect(str(db_path), ...)              │
   └────────────────────────────────────────────────────────────┘

2. Prompt Management (3 copies × 115 lines = 345 lines!)
   ┌────────────────────────────────────────────────────────────┐
   │ ✍️_Writer_Agent.py                                        │
   │ 🔍_Researcher_Agent.py                                    │
   │ archived/🤖_AI_Agents_OLD.py                              │
   │                                                            │
   │ def show_prompt_management(agent_type: str):               │
   │     # ... 115 identical lines of code ...                  │
   │     prompts = get_prompts_by_agent(agent_type)             │
   │     selected_prompt_name = st.selectbox(...)               │
   │     # ... forms, editing, saving ...                       │
   └────────────────────────────────────────────────────────────┘

3. Authorization Check (17 copies × 10 lines = 170 lines!)
   ┌────────────────────────────────────────────────────────────┐
   │ ALL 17 PAGES                                               │
   │                                                            │
   │ try:                                                       │
   │     from utils.auth import is_user_authorized              │
   │     if not is_user_authorized():                           │
   │         st.error("⛔ Не авторизован...")                  │
   │         st.stop()                                          │
   │ except ImportError as e:                                   │
   │     st.error(f"❌ Ошибка: {e}")                           │
   │     st.stop()                                              │
   └────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════

TOTAL DUPLICATION: ~1,500 lines (26% of codebase)
```

### AFTER: Shared Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHARED COMPONENTS APPROACH                   │
└─────────────────────────────────────────────────────────────────┘

1. Database Connection (1 implementation)
   ┌────────────────────────────────────────────────────────────┐
   │ utils/database.py                                          │
   │                                                            │
   │ @st.cache_resource                                         │
   │ def get_db_connection():                                   │
   │     """Centralized database connection"""                  │
   │     db_path = Path(...) / "data" / "grantservice.db"       │
   │     return sqlite3.connect(str(db_path), ...)              │
   │                                                            │
   │ Used by: ALL pages (import once)                           │
   └────────────────────────────────────────────────────────────┘

2. Prompt Management (1 implementation)
   ┌────────────────────────────────────────────────────────────┐
   │ utils/agent_components.py                                  │
   │                                                            │
   │ def render_prompt_management(agent_type: str):             │
   │     """Unified prompt management for all agents"""         │
   │     # ... 115 lines of code ...                            │
   │                                                            │
   │ Used by: All agent tabs                                    │
   └────────────────────────────────────────────────────────────┘

3. Authorization Check (1 decorator)
   ┌────────────────────────────────────────────────────────────┐
   │ utils/auth.py                                              │
   │                                                            │
   │ def require_auth(func):                                    │
   │     @wraps(func)                                           │
   │     def wrapper(*args, **kwargs):                          │
   │         if not is_user_authorized():                       │
   │             st.error("⛔ Не авторизован")                 │
   │             st.stop()                                      │
   │         return func(*args, **kwargs)                       │
   │     return wrapper                                         │
   │                                                            │
   │ Usage:                                                     │
   │ @require_auth                                              │
   │ def main():                                                │
   │     st.title("My Page")                                    │
   └────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════

TOTAL DUPLICATION: ~100 lines (<5% of codebase)
REDUCTION: -93% duplication eliminated!
```

---

## Migration Path

```
┌─────────────────────────────────────────────────────────────────┐
│                        PHASE 1: FOUNDATION                      │
│                          (Week 1: 5 days)                       │
└─────────────────────────────────────────────────────────────────┘

Day 1-2: Shared Components
   ┌────────────────────────────────────────────────────────────┐
   │ CREATE: utils/agent_components.py                          │
   │ ├─ render_prompt_management()                              │
   │ ├─ render_agent_stats()                                    │
   │ ├─ render_agent_header()                                   │
   │ └─ render_agent_testing()                                  │
   └────────────────────────────────────────────────────────────┘

Day 3-4: Database & Auth
   ┌────────────────────────────────────────────────────────────┐
   │ UPDATE: utils/database.py                                  │
   │ └─ Centralize get_db_connection()                          │
   │                                                            │
   │ UPDATE: utils/auth.py                                      │
   │ └─ Create @require_auth decorator                          │
   │                                                            │
   │ UPDATE: All 17 pages                                       │
   │ └─ Replace auth blocks with decorator                      │
   └────────────────────────────────────────────────────────────┘

Day 5: Testing & Cleanup
   ┌────────────────────────────────────────────────────────────┐
   │ ✅ Run integration tests                                   │
   │ ✅ Remove duplicated functions                             │
   │ ✅ Update imports                                          │
   │ ✅ Document changes                                        │
   └────────────────────────────────────────────────────────────┘

Result: -500 lines of duplication removed ✅

════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: RESTRUCTURING                       │
│                         (Week 2-3: 10 days)                     │
└─────────────────────────────────────────────────────────────────┘

Week 2: Agent Consolidation
   ┌────────────────────────────────────────────────────────────┐
   │ Day 1-2: Create tabbed 🤖_AI_Agents.py                    │
   │    └─ 5 agent tabs (Interviewer, Auditor, Planner,        │
   │                      Researcher, Writer)                   │
   │                                                            │
   │ Day 3: Migrate ✍️_Writer_Agent.py → Writer tab           │
   │    └─ Move content, use shared components                  │
   │                                                            │
   │ Day 4: Migrate 🔍_Researcher_Agent.py → Researcher tab   │
   │    └─ Move content, use shared components                  │
   │                                                            │
   │ Day 5: Add Researcher sub-tabs                             │
   │    ├─ Integrate 🔬_Исследования_исследователя.py         │
   │    └─ Integrate 🔬_Аналитика_исследователя.py            │
   └────────────────────────────────────────────────────────────┘

Week 3: Grant & Application Consolidation
   ┌────────────────────────────────────────────────────────────┐
   │ Day 1-2: Merge grant pages                                 │
   │    └─ 📄_Грантовые_заявки + 📋_Управление_грантами       │
   │                                                            │
   │ Day 3: Merge application pages                             │
   │    └─ 📋_Анкеты + 📄_Просмотр_заявки                     │
   │                                                            │
   │ Day 4: Update navigation & links                           │
   │                                                            │
   │ Day 5: User acceptance testing                             │
   └────────────────────────────────────────────────────────────┘

Result: 17 pages → 10 pages ✅

════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: OPTIMIZATION                        │
│                         (Week 4+: Optional)                     │
└─────────────────────────────────────────────────────────────────┘

Component Library
   ┌────────────────────────────────────────────────────────────┐
   │ CREATE: components/                                        │
   │ ├─ cards.py                                                │
   │ ├─ tables.py                                               │
   │ ├─ forms.py                                                │
   │ ├─ charts.py                                               │
   │ └─ agent_widgets.py                                        │
   └────────────────────────────────────────────────────────────┘

Smart Caching
   ┌────────────────────────────────────────────────────────────┐
   │ CREATE: utils/cache_manager.py                             │
   │ └─ Centralized caching for expensive queries                │
   └────────────────────────────────────────────────────────────┘

API Layer
   ┌────────────────────────────────────────────────────────────┐
   │ CREATE: utils/api/                                         │
   │ ├─ agents.py (AgentAPI)                                    │
   │ ├─ grants.py (GrantAPI)                                    │
   │ └─ users.py (UserAPI)                                      │
   └────────────────────────────────────────────────────────────┘

Result: Clean architecture ✅
```

---

## Expected Results

```
┌─────────────────────────────────────────────────────────────────┐
│                         BEFORE vs AFTER                         │
└─────────────────────────────────────────────────────────────────┘

Metrics:
┌─────────────────────┬──────────┬──────────┬────────────────────┐
│ Metric              │ Before   │ After    │ Improvement        │
├─────────────────────┼──────────┼──────────┼────────────────────┤
│ Total pages         │ 17       │ 10       │ -41% ✅           │
│ Lines of code       │ 5,745    │ ~3,800   │ -34% ✅           │
│ Code duplication    │ ~26%     │ <5%      │ -80% ✅           │
│ Agent pages         │ 5        │ 1        │ -80% ✅           │
│ Grant pages         │ 3        │ 1        │ -67% ✅           │
│ Researcher pages    │ 3        │ 1        │ -67% ✅           │
│ DB connections      │ 3 copies │ 1 shared │ -67% ✅           │
│ Auth blocks         │ 17       │ 1 deco   │ -94% ✅           │
│ Prompt mgmt funcs   │ 3 copies │ 1 shared │ -67% ✅           │
└─────────────────────┴──────────┴──────────┴────────────────────┘

User Experience:
┌─────────────────────┬──────────┬──────────┬────────────────────┐
│ Aspect              │ Before   │ After    │ Change             │
├─────────────────────┼──────────┼──────────┼────────────────────┤
│ Navigation clarity  │ 5/10 🔴 │ 9/10 🟢 │ +80% ✅           │
│ Time to find page   │ ~45s 🔴 │ ~15s 🟢 │ -67% ✅           │
│ Task completion     │ 65% 🟡  │ 85%+ 🟢 │ +31% ✅           │
│ User satisfaction   │ 6/10 🟡 │ 8/10 🟢 │ +33% ✅           │
└─────────────────────┴──────────┴──────────┴────────────────────┘

Development:
┌─────────────────────┬──────────┬──────────┬────────────────────┐
│ Task                │ Before   │ After    │ Improvement        │
├─────────────────────┼──────────┼──────────┼────────────────────┤
│ Add new agent       │ Copy page│ Add tab  │ 90% faster ✅     │
│ Update agent UI     │ 5 places │ 1 place  │ 80% faster ✅     │
│ Fix bug             │ Check all│ Fix once │ 75% faster ✅     │
│ Onboard new dev     │ ~8 hours │ ~2 hours │ 75% faster ✅     │
└─────────────────────┴──────────┴──────────┴────────────────────┘
```

---

## Critical Decision Points

```
┌─────────────────────────────────────────────────────────────────┐
│                      DECISION NEEDED                            │
└─────────────────────────────────────────────────────────────────┘

Question 1: Start with which phase?
   ┌────────────────────────────────────────────────────────────┐
   │ Option A: Phase 1 (Foundation)                             │
   │ ├─ Pros: Low risk, quick wins, enables Phase 2             │
   │ ├─ Cons: No visible UI changes                             │
   │ └─ Recommendation: ✅ START HERE                           │
   │                                                            │
   │ Option B: Phase 2 (Restructuring)                          │
   │ ├─ Pros: Immediate UX improvement                          │
   │ ├─ Cons: Higher risk without Phase 1 foundation            │
   │ └─ Recommendation: ⚠️ DO AFTER PHASE 1                    │
   │                                                            │
   │ Option C: Both at once                                     │
   │ ├─ Pros: Faster overall delivery                           │
   │ ├─ Cons: Very high risk, hard to rollback                  │
   │ └─ Recommendation: ❌ TOO RISKY                            │
   └────────────────────────────────────────────────────────────┘

Question 2: What to do with old pages during migration?
   ┌────────────────────────────────────────────────────────────┐
   │ Option A: Archive immediately after migration              │
   │ ├─ Pros: Clean codebase                                    │
   │ ├─ Cons: No fallback if issues                             │
   │ └─ Recommendation: ❌ TOO RISKY                            │
   │                                                            │
   │ Option B: Keep in production with deprecation warning      │
   │ ├─ Pros: Safe rollback, gradual transition                 │
   │ ├─ Cons: Duplicate pages temporarily                       │
   │ └─ Recommendation: ✅ SAFE APPROACH                        │
   │                                                            │
   │ Option C: Feature flag toggle                              │
   │ ├─ Pros: A/B testing, instant rollback                     │
   │ ├─ Cons: Extra complexity                                  │
   │ └─ Recommendation: ⚠️ IF TIME ALLOWS                      │
   └────────────────────────────────────────────────────────────┘

Question 3: Testing strategy?
   ┌────────────────────────────────────────────────────────────┐
   │ Must have:                                                 │
   │ ✅ Unit tests for shared components                        │
   │ ✅ Integration tests for workflows                         │
   │ ✅ UAT with real users (2-3 power users)                   │
   │                                                            │
   │ Nice to have:                                              │
   │ ⚠️ E2E tests with Selenium                                │
   │ ⚠️ Performance benchmarks                                 │
   │ ⚠️ Load testing                                           │
   └────────────────────────────────────────────────────────────┘
```

---

**END OF VISUAL GUIDE**

---

*See `AUDIT_REPORT_ADMIN_UI_ARCHITECTURE.md` for detailed analysis and full refactoring plan.*
