# Iteration 36: Project Structure & Methodology Cleanup

**Created:** 2025-10-25
**Type:** Infrastructure / Technical Debt
**Priority:** P1 - HIGH
**Estimated Time:** 2-3 hours
**Based on:** Project Evolution Methodology (Cradle OS)

---

## 🎯 ПРОБЛЕМА

### Текущая ситуация - Беспорядок в структуре:

**1. Код в двух местах:**
- 📁 `C:\SnowWhiteAI\GrantService` - основной код (production)
- 📁 `C:\SnowWhiteAI\GrantService_Project` - работа по проекту (docs, iterations)

**2. Методология разбросана:**
- 📁 `C:\SnowWhiteAI\cradle\01-Active-Projects\Project-Evolution-Methodology` - общая методология
- 📁 `C:\SnowWhiteAI\Exchange\GrantService_Project` - обмен между проектами
- 📁 `C:\SnowWhiteAI\Exchange\from-cradle` - сообщения от Cradle

**3. Нет единого источника правды:**
- Где искать методологию для GrantService?
- Как применять Project Evolution Methodology?
- Как интегрироваться с Exchange Protocol?

**4. Нет CLAUDE.md с инструкциями:**
- Нет morning protocol
- Нет INBOX notifications
- Нет ссылок на Exchange messages

---

## 🎯 ЦЕЛЬ ИТЕРАЦИИ

Упорядочить структуру проекта согласно:
1. **Project Evolution Methodology** - DORA metrics, CI/CD
2. **Exchange Protocol** - межпроектная коммуникация
3. **Cradle OS Principles** - гомеостаз, метаболизм, регенерация

---

## 📋 ЗАДАЧИ

### Task 1: Создать CLAUDE.md в GrantService

**Файл:** `C:\SnowWhiteAI\GrantService\CLAUDE.md`

**Содержание:**
```markdown
# GrantService - AI Grant Application Generator

## Morning Protocol (Start of Session)

1. Check INBOX: @Exchange/from-cradle/GrantService/
2. Check DORA metrics: deployment frequency, lead time, MTTR, failure rate
3. Check error budget: SLO compliance
4. Review Iteration status: C:\SnowWhiteAI\GrantService_Project\Development\
5. Check CI/CD status: tests passing?

## Project Structure

- **Code:** C:\SnowWhiteAI\GrantService
- **Project Docs:** C:\SnowWhiteAI\GrantService_Project
- **Methodology:** @Exchange/from-cradle/GrantService/METHODOLOGY.md
- **Iterations:** C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\

## Methodology

Follow: **Project Evolution Methodology**
- Small commits (<200 lines)
- Trunk-based development
- 80% features / 20% tech debt
- DORA metrics tracking

## Exchange Protocol

**INBOX:** @Exchange/from-cradle/GrantService/
**OUTBOX:** @Exchange/to-cradle/GrantService/

When receiving messages:
1. Read message
2. Apply content
3. Archive to .messages/archive/
4. (Optional) Respond to OUTBOX

## Sber500 Bootcamp Integration

- Track GigaChat token usage
- Generate reports for bootcamp
- Follow GIGACHAT_SWITCH_PLAN.md

## Quick Commands

- Start bot: `python telegram-bot/main.py`
- Run tests: `pytest tests/`
- Deploy: (see DEPLOYMENT.md)
```

---

### Task 2: Создать symlinks для методологии

**Цель:** Избежать дублирования, использовать единый источник

**Действия:**
```bash
# В GrantService_Project создать ссылки на методологию
cd C:\SnowWhiteAI\GrantService_Project\00_Project_Info\

# Создать ссылку на методологию
mklink /D "Methodology" "C:\SnowWhiteAI\cradle\01-Active-Projects\Project-Evolution-Methodology"

# Создать ссылку на Exchange
mklink /D "Exchange" "C:\SnowWhiteAI\Exchange\GrantService_Project"
```

**Результат:**
```
GrantService_Project/
├── 00_Project_Info/
│   ├── Methodology/           → symlink to cradle methodology
│   └── Exchange/              → symlink to Exchange folder
```

---

### Task 3: Применить Exchange Protocol

**Создать структуру:**
```
Exchange/
├── from-cradle/
│   └── GrantService/
│       ├── msg-2025-10-25-001.md    (методология)
│       └── METHODOLOGY.md           (quick reference)
├── to-cradle/
│   └── GrantService/
│       └── response-2025-10-25-001.md
└── GrantService_Project/
    └── .messages/
        └── archive/                 (прочитанные сообщения)
```

---

### Task 4: Создать Pre-Deploy Checklist

**Файл:** `C:\SnowWhiteAI\GrantService_Project\Development\PRE_DEPLOY_CHECKLIST.md`

**Содержание:**
```markdown
# Pre-Deploy Checklist - GrantService

Before deploying ANY iteration to production:

## Code Quality
- [ ] All tests pass locally (`pytest tests/`)
- [ ] Code review completed (if team >1)
- [ ] No hardcoded secrets or credentials
- [ ] Error handling for all external APIs

## Database
- [ ] Migration SQL tested on local DB
- [ ] Backup created before migration
- [ ] Rollback plan documented

## Configuration
- [ ] Environment variables checked (.env)
- [ ] GigaChat credentials valid
- [ ] PostgreSQL connection working
- [ ] Qdrant connection working

## Deployment
- [ ] Git commit created with clear message
- [ ] Git pushed to GitHub
- [ ] Production server accessible (SSH)
- [ ] Services can be restarted without downtime

## Testing
- [ ] Smoke test plan ready
- [ ] User acceptance criteria defined
- [ ] Rollback tested on staging

## Monitoring
- [ ] Logs accessible
- [ ] Error tracking enabled
- [ ] Performance metrics tracked

## Communication
- [ ] Team notified about deployment
- [ ] Users notified if breaking changes
- [ ] Documentation updated

## Sber500 Bootcamp
- [ ] Token tracking enabled (if using GigaChat)
- [ ] Statistics collection working
```

---

### Task 5: Setup DORA Metrics Tracking

**Файл:** `C:\SnowWhiteAI\GrantService_Project\Development\DORA_METRICS.md`

**Метрики для отслеживания:**
```markdown
# DORA Metrics - GrantService

## 1. Deployment Frequency
**Target:** ≥1 deploy per week
**Current:** Track in deployment log

## 2. Lead Time for Changes
**Target:** <1 day (commit → production)
**Current:** Measure: commit timestamp → deploy timestamp

## 3. Change Failure Rate
**Target:** <15%
**Current:** Failed deployments / Total deployments

## 4. Time to Restore Service (MTTR)
**Target:** <1 hour
**Current:** Bug reported → fix deployed

## Tracking
Log each deployment:
- Date & Time
- Iteration number
- Commit hash
- Success/Failure
- If failure: MTTR

Example:
| Date | Iteration | Commit | Success | MTTR |
|------|-----------|--------|---------|------|
| 2025-10-25 | 35 | abc123 | ✅ | - |
| 2025-10-26 | 36 | def456 | ❌ | 45 min |
```

---

### Task 6: Создать Iteration Template

**Файл:** `C:\SnowWhiteAI\GrantService_Project\Development\ITERATION_TEMPLATE.md`

**Шаблон для всех будущих итераций:**
```markdown
# Iteration XX: [Name]

**Created:** YYYY-MM-DD
**Type:** Feature | Bug Fix | Refactoring | Infrastructure
**Priority:** P0-CRITICAL | P1-HIGH | P2-MEDIUM | P3-LOW
**Estimated Time:** X hours
**Methodology:** [Principle from Cradle/Project Evolution]

---

## 🎯 PROBLEM
[What problem are we solving?]

## 🎯 SOLUTION
[How will we solve it?]

## 📋 TASKS
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## 📊 SUCCESS CRITERIA
- [ ] Criterion 1
- [ ] Criterion 2

## 🐛 BUGS FOUND
[Track bugs found during iteration]

## 📝 LESSONS LEARNED
[What we learned]

## 🔗 RELATED
- Previous: Iteration XX-1
- Next: Iteration XX+1
- Methodology: @Exchange/from-cradle/GrantService/METHODOLOGY.md
```

---

## 📊 SUCCESS CRITERIA

### Must Have:
- [x] CLAUDE.md создан
- [ ] Symlinks на методологию работают
- [ ] Exchange Protocol применен
- [ ] Pre-Deploy Checklist создан
- [ ] DORA Metrics tracking setup
- [ ] Iteration Template создан

### Nice to Have:
- [ ] CI/CD pipeline setup
- [ ] Automated tests >80%
- [ ] Service Level Objectives defined
- [ ] Error budget calculated

---

## 🔄 WORKFLOW (Project Evolution Methodology)

### STEP 1: PLAN (15% времени)
- ✅ Этот документ = план
- Breakdown tasks: 6 задач, каждая <30 min
- Sprint goal: "Упорядочить структуру проекта"

### STEP 2: DEVELOP (Daily)
- Small commits (<200 lines)
- Each task = отдельный commit
- Commit message: "Iteration 36: Task X - [description]"

### STEP 3: INTEGRATE
- Test locally after each task
- Merge to trunk (main) daily
- No long-lived branches

### STEP 4: RELEASE
- Deploy after all tasks complete
- Use Pre-Deploy Checklist
- Monitor DORA metrics

### STEP 5: LEARN
- Document in FINAL_REPORT.md
- Update methodology if needed
- Share learnings via Exchange Protocol

---

## 📂 FILE STRUCTURE (After Iteration)

```
GrantService/
├── CLAUDE.md                          NEW ✨
├── telegram-bot/
├── agents/
└── ...existing code...

GrantService_Project/
├── 00_Project_Info/
│   ├── Methodology/                   SYMLINK ✨
│   └── Exchange/                      SYMLINK ✨
├── Development/
│   ├── PRE_DEPLOY_CHECKLIST.md        NEW ✨
│   ├── DORA_METRICS.md                NEW ✨
│   ├── ITERATION_TEMPLATE.md          NEW ✨
│   └── 02_Feature_Development/
│       └── Interviewer_Iterations/
│           ├── Iteration_35_Anketa_Management/
│           └── Iteration_36_Methodology_Cleanup/   THIS ✨

Exchange/
├── from-cradle/
│   └── GrantService/
│       ├── msg-2025-10-25-001.md       NEW ✨
│       └── METHODOLOGY.md              NEW ✨
└── to-cradle/
    └── GrantService/                   (for responses)
```

---

## ⏱️ TIMELINE

**Total: 2-3 hours**

| Task | Time | Status |
|------|------|--------|
| 1. CLAUDE.md | 30 min | ⏳ |
| 2. Symlinks | 15 min | ⏳ |
| 3. Exchange Protocol | 30 min | ⏳ |
| 4. Pre-Deploy Checklist | 20 min | ⏳ |
| 5. DORA Metrics | 20 min | ⏳ |
| 6. Iteration Template | 15 min | ⏳ |
| **Total** | **2h 10min** | |

---

## 🎓 ПРИНЦИПЫ CRADLE OS

### 1. Гомеостаз (Homeostasis)
- Pre-Deploy Checklist = automated stability checks
- DORA metrics = health monitoring
- Rollback plan = self-healing

### 2. Метаболизм (Metabolism)
- Small iterations (каждая <3 часа)
- Frequent commits (2-5 per day)
- Continuous integration

### 3. Регенерация (Regeneration)
- 20% времени на tech debt
- Refactoring как часть каждой итерации
- Documentation updates

---

## 🔗 INTEGRATION WITH SBER500

После Iteration 36:
- ✅ Структура готова для token tracking
- ✅ DORA metrics для демонстрации процессов
- ✅ Exchange Protocol для коммуникации с партнерами
- ✅ Pre-Deploy Checklist для качества

---

## 📝 NEXT ITERATION SUGGESTIONS

**Iteration 37: CI/CD Pipeline Setup**
- GitHub Actions или GitLab CI
- Automated testing
- Automated deployment to staging
- DORA metrics automation

**Iteration 38: Token Tracking (Sber500)**
- `gigachat_usage_log` table
- Logging в UnifiedLLMClient
- Report generator
- Dashboard

---

**Created:** 2025-10-25
**Status:** 📋 READY TO START
**Previous:** Iteration 35 (Anketa Management)
**Next:** Iteration 37 (CI/CD Pipeline)
