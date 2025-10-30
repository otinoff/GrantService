# Project Evolution Methodology - Actionable Playbook

**Version:** 1.0.0
**For:** All SnowWhiteAI projects (Cradle, GrantService, Michael, New_Media, Psychology)
**Philosophy:** Develop projects like living organisms - controlled growth with integrity
**Based on:** 119 KB research (WebSearch + Perplexity + Parallel)

---

## 🎯 ONE-SENTENCE SUMMARY

**Develop projects through small frequent changes (metabolism), automated stability checks (homeostasis), and managed technical debt (regeneration) - measured by DORA metrics.**

---

## ✅ PRE-PROJECT CHECKLIST

Before starting ANY project or iteration, ensure:

- [ ] **CI/CD pipeline** configured (automated deploy)
- [ ] **Automated tests** >80% coverage target
- [ ] **DORA metrics tracking** setup (deployment frequency, lead time, MTTR, failure rate)
- [ ] **20% time allocation** for technical debt paydown
- [ ] **Service Level Objectives (SLOs)** defined (what "stable" means)
- [ ] **Rollback mechanism** ready (can undo any change)
- [ ] **Trunk/main branch** protected (requires review)
- [ ] **Error budget** calculated (acceptable failure %)

**If missing any:** Set up before first iteration, not during!

---

## 🔄 5-STEP ITERATION WORKFLOW

**Use for:** Every sprint, every feature, every project phase

### STEP 1: PLAN (Start of iteration)

**Time:** 10-15% of iteration

**Actions:**
1. **Prioritize backlog** - what delivers most value?
2. **Allocate capacity:**
   - 80% → new features
   - 20% → technical debt (refactoring, tests, docs)
3. **Define success metrics** - how measure if iteration succeeded?
4. **Break down tasks** - each task <1 day of work
5. **Set sprint goal** - one sentence: "We will achieve X"

**Output:** Clear plan, committed deliverables

**Anti-pattern:** ❌ Planning >20% of iteration time

---

### STEP 2: DEVELOP (Daily)

**Practices:**

**Small Commits (<200 lines):**
- Commit 2-5 times per day minimum
- Each commit = one logical change
- Commit message explains WHY, not WHAT

**Trunk-Based Development:**
- One main branch (trunk/main)
- Short-lived feature branches (<1 day)
- Merge to trunk daily
- Trunk always "green" (deployable)

**Automated Tests on Every Commit:**
- Unit tests run locally (pre-commit hook)
- Integration tests run in CI
- If tests fail → fix immediately, don't merge

**Code Review (<4 hours turnaround):**
- Every PR reviewed by ≥1 person
- Review for: correctness, clarity, maintainability
- Approval required to merge
- Reviewer accountability: you approve = you own bugs too

**Continuous Integration:**
- CI pipeline runs on every commit
- Tests + linting + security scan
- <10 minutes pipeline time (if longer → optimize!)
- Green pipeline = ready to deploy

**Output:** Working code, tested, reviewed, merged

**Anti-patterns:**
- ❌ Long-lived branches (>1 day)
- ❌ Committing untested code
- ❌ Skipping code review "to save time"
- ❌ Merge conflicts (means not syncing with trunk daily)

---

### STEP 3: INTEGRATE (Continuous)

**Practices:**

**Deploy to Staging Automatically:**
- Every merge to trunk → auto-deploy to staging
- Staging = production-like environment
- Run smoke tests automatically

**Monitor Key Metrics:**
- Check DORA metrics daily:
  - Deployment frequency
  - Lead time for changes
  - Change failure rate
  - Time to restore service (MTTR)

**Canary Releases (for production):**
- Deploy to 5% of users first
- Monitor error rate, latency, SLO compliance
- If metrics good → gradually expand to 100%
- If metrics bad → rollback immediately

**Error Budget Management:**
- Track SLO compliance (e.g., 99.9% uptime)
- Error budget = 0.1% (acceptable downtime)
- If budget spent → freeze features, focus on stability
- If budget healthy → innovate freely

**Output:** Stable staging environment, production-ready code

**Anti-patterns:**
- ❌ Deploy directly to production without staging
- ❌ Deploy on Friday afternoon (no time to fix!)
- ❌ Ignore monitoring ("it deployed, we're done")
- ❌ No rollback plan

---

### STEP 4: RELEASE (When ready)

**Strategies:**

**Feature Toggles (Flags):**
- New features hidden behind flags
- Enable for testing → then gradually for users
- Can disable instantly if problems
- Decouples deployment from release

**Blue-Green Deployment:**
- Two environments: Blue (current) + Green (new)
- Deploy to Green, test
- Switch traffic to Green
- Keep Blue for rollback

**Progressive Rollout:**
- 5% → 25% → 50% → 100% user traffic
- Monitor at each step
- Pause or rollback if issues

**Output:** Feature live in production, users happy

**Anti-patterns:**
- ❌ "Big bang" releases (all at once)
- ❌ No monitoring post-deployment
- ❌ Ignore user feedback
- ❌ Can't rollback

---

### STEP 5: REFLECT (End of iteration)

**Time:** 5-10% of iteration

**Retrospective:**
1. **What went well?** (celebrate!)
2. **What went wrong?** (blameless, focus on process)
3. **What to improve?** (actionable items)
4. **Update process** (don't repeat mistakes)

**Metrics Review:**
- Update DORA dashboard
- Check velocity trend
- Review technical debt ratio
- Team health check (burnout?)

**Knowledge Capture:**
- Document learnings
- Update playbooks
- Share with other teams

**Plan Next Iteration:**
- What worked → keep doing
- What didn't → change approach
- New ideas → backlog

**Output:** Learnings captured, process improved

**Anti-pattern:** ❌ Skip retrospective ("we're too busy")

---

## 📊 METRICS TO TRACK

### DORA Four Keys (Industry Standard)

**1. Deployment Frequency**
- Elite: >1 per day
- High: Once per day to once per week
- Medium: Once per week to once per month
- Low: <Once per month

**Target for SnowWhiteAI:** High (≥1 per day)

**2. Lead Time for Changes**
- Elite: <1 hour
- High: <1 day
- Medium: 1 day to 1 week
- Low: >1 week

**Target:** High (<1 day from commit to production)

**3. Change Failure Rate**
- Elite: 0-15%
- High: 16-30%
- Medium: 31-45%
- Low: >45%

**Target:** Elite (<15%)

**4. Mean Time to Recovery (MTTR)**
- Elite: <1 hour
- High: <1 day
- Medium: 1 day to 1 week
- Low: >1 week

**Target:** Elite (<1 hour to fix/rollback)

---

### Technical Health Metrics

**Code Quality:**
- Test Coverage: >80% (target)
- Technical Debt Ratio: <5% (critical threshold)
- Code Duplication: <3%
- Cyclomatic Complexity: <10 per function

**Team Health (SPACE Framework):**
- Satisfaction & well-being (survey)
- Performance (outcomes achieved)
- Activity (work completed)
- Communication (team collaboration)
- Efficiency & flow (time in "flow state")

**SRE Metrics:**
- SLO compliance % (99.9% uptime target)
- Error budget remaining (how much downtime left)
- Toil reduction % (automate manual work)

---

## 🚫 ANTI-PATTERNS (Don't Do This!)

**Development:**
- ❌ Long-lived feature branches (>1 day) → merge conflicts hell
- ❌ Skip tests "to save time" → bugs multiply
- ❌ Commit untested code → breaks main branch
- ❌ Ignore technical debt >2 sprints → compound interest kills velocity

**Deployment:**
- ❌ Deploy without staging environment → production = testing ground
- ❌ Deploy on Friday → weekend on-call guaranteed
- ❌ No rollback plan → stuck with broken code
- ❌ "Big bang" releases → high failure rate

**Process:**
- ❌ Skip code review → quality drops, knowledge silos
- ❌ Skip retrospectives → repeat same mistakes
- ❌ Ignore metrics → flying blind
- ❌ Hero culture ("John always saves us") → unsustainable

**Management:**
- ❌ Sprint on sprint without refactoring → technical bankruptcy
- ❌ 100% feature capacity (0% debt) → system degrades
- ❌ Micro-management → destroys autonomy and speed
- ❌ Blame culture → people hide problems

---

## 🧬 5 BIOLOGICAL PRINCIPLES → 5 PRACTICES

### 1. METABOLISM → Continuous Integration
**Biological:** Organism digests food gradually, not all at once
**Software:** Integrate changes frequently, in small chunks

**Practice:**
- Commit 2-5 times/day
- CI pipeline runs on every commit
- Merge to trunk daily
- Small PRs (<200 lines)

**Why:** Small changes = easy to "digest", easy to rollback

---

### 2. HOMEOSTASIS → Automated Testing
**Biological:** Body maintains stable internal state
**Software:** Automated tests maintain code stability

**Practice:**
- Unit tests (fast, >80% coverage)
- Integration tests (realistic scenarios)
- E2E tests (critical user flows)
- Performance tests (no regression)

**Why:** Tests = early warning system for "illness"

---

### 3. DIFFERENTIATION → Modular Architecture
**Biological:** Cells specialize but remain part of organism
**Software:** Modules specialize, loosely coupled

**Practice:**
- Domain-Driven Design (bounded contexts)
- Microservices (independent deploy)
- APIs between modules (clear contracts)
- Two-pizza teams (own specific services)

**Why:** Changes in one module don't break others

---

### 4. IMMUNITY → Code Review + CI/CD
**Biological:** Immune system filters harmful pathogens
**Software:** Review + CI filter bad code

**Practice:**
- Code review required (≥1 reviewer)
- CI pipeline (automated checks)
- Security scanning (dependency audit)
- Quality gates (coverage, complexity thresholds)

**Why:** Prevent "infections" (bugs) from entering system

---

### 5. REGENERATION → 20% Rule (Technical Debt)
**Biological:** Body continuously renews tissues
**Software:** Continuously refactor and clean code

**Practice:**
- 20% sprint capacity → debt paydown
- Regular refactoring sprints
- Boy Scout Rule ("leave code better than you found it")
- Track debt ratio (<5% target)

**Why:** Prevent "aging" and "decay" of codebase

---

## 🔧 TROUBLESHOOTING DECISION TREE

**If project feels "broken" or unstable:**

### Problem: High Change Failure Rate (>15%)
**Diagnosis:** Too many deployments causing issues
**Solution:**
1. Check recent deployments → rollback problematic ones
2. Review test coverage → add missing tests
3. Slow down deploys → focus on stability
4. Spend error budget on fixes, not features

---

### Problem: Low Deployment Frequency (<1/week)
**Diagnosis:** Integration problems, fear of deploying
**Solution:**
1. Check branch lifetime → force daily merges
2. Improve CI speed → reduce pipeline time
3. Add staging environment → safe testing ground
4. Feature flags → decouple deploy from release

---

### Problem: High Technical Debt Ratio (>5%)
**Diagnosis:** Not enough refactoring time
**Solution:**
1. Allocate 30% capacity to debt (emergency mode)
2. Identify highest-impact debt (SonarQube)
3. Plan dedicated refactoring sprint
4. Prevent new debt (stricter code review)

---

### Problem: Long Lead Time (>1 week)
**Diagnosis:** Slow review, long branches, manual processes
**Solution:**
1. Enforce <4 hour review turnaround
2. Enforce <1 day branch lifetime
3. Automate manual steps (CI/CD)
4. Remove approval bottlenecks

---

### Problem: High MTTR (>1 day)
**Diagnosis:** Slow detection, complex rollback, unclear ownership
**Solution:**
1. Improve monitoring (faster detection)
2. Practice rollbacks (make it easy)
3. Document on-call procedures
4. Blameless post-mortems (learn from incidents)

---

## 🎓 CASE STUDIES (What Works)

### Amazon: Two-Pizza Teams + Frequent Deploys
- **Practice:** Small autonomous teams (≤8 people)
- **Result:** 1 deployment every 11.7 seconds
- **Metric:** Some services → 1,079 deploys/day
- **Lesson:** Autonomy + automation = velocity

### Netflix: Chaos Engineering
- **Practice:** Intentionally break production (controlled)
- **Result:** System resilient to failures
- **Metric:** Thousands deploys/day, high availability
- **Lesson:** Test resilience in production, not staging

### Google: SRE + Error Budgets
- **Practice:** SLOs define stability, error budgets enable innovation
- **Result:** Balance between velocity and reliability
- **Metric:** Ship fast while maintaining 99.99% uptime
- **Lesson:** Data-driven trade-offs, not gut feeling

### Яндекс: Platform Engineering
- **Practice:** Shared platform for all teams
- **Result:** Consistent quality, faster onboarding
- **Metric:** Reduced operational toil, higher velocity
- **Lesson:** Invest in platform = multiply team effectiveness

---

## 📚 DEEP DIVE (When You Need Details)

**For detailed theory, examples, case studies:**

**Use Qdrant semantic search:**
```python
# Example query
semantic_search(
    query="How does Netflix implement Chaos Engineering?",
    collection="project-evolution-methodology",
    limit=5
)
```

**Available knowledge:**
- 3 research sources (WebSearch, Perplexity, Parallel)
- 119 KB detailed analysis
- Biological metaphors (detailed theory)
- Enterprise frameworks (SAFe, LeSS, Spotify Model)
- Tech giants practices (Amazon, Google, Netflix, Microsoft, Meta)
- Russian practices (Яндекс, Озон, Сбер)

**When to use:**
- Stuck on specific problem
- Need detailed example
- Want to learn theory
- Researching new practice

**When NOT to use:**
- Daily work (this playbook is enough!)
- Under time pressure (actionable > theory)

---

## 🎯 QUICK REFERENCE

**Daily workflow:**
1. Pull from trunk
2. Create small feature branch
3. Write test → write code → commit
4. Push → CI runs → review
5. Merge → delete branch
6. Repeat

**Weekly workflow:**
1. Sprint planning (20% debt allocation)
2. Daily standups (blockers?)
3. Deploy to production (when ready)
4. Monitor DORA metrics
5. Retrospective (Friday)

**Monthly workflow:**
1. Review DORA trends
2. Technical debt assessment
3. Team health check
4. Process improvements
5. Knowledge sharing

---

## ✅ SUCCESS CHECKLIST

**Project is healthy if:**
- [ ] Deploying >1 per day (or >3 per week minimum)
- [ ] Lead time <1 day (commit to production)
- [ ] Change failure rate <15%
- [ ] MTTR <1 hour
- [ ] Test coverage >80%
- [ ] Technical debt ratio <5%
- [ ] Team morale positive (no burnout)
- [ ] Retrospectives happening regularly

**If missing any:** Use troubleshooting section above!

---

## 🚀 IMPLEMENTATION ROADMAP

**Week 1: Foundation**
- Setup CI/CD pipeline
- Configure automated testing
- Define DORA metrics tracking
- Establish trunk branch policy

**Week 2: Process**
- Implement PR review process
- Establish 20% debt rule
- Document workflow
- Team training

**Week 3-4: Culture**
- Run retrospectives
- Celebrate small wins
- Knowledge sharing sessions
- Iterate and improve

**Ongoing: Optimization**
- Monitor DORA metrics
- Reduce technical debt
- Improve test coverage
- Scale practices

---

## 📝 PROJECT-SPECIFIC METHODOLOGIES

**This is universal playbook. For project-specific guidance:**

- **Cradle OS:** See `.claude/METHODOLOGY.md` (meta-project management)
- **GrantService:** See `Exchange/from-cradle/GrantService_Project/METHODOLOGY.md` (Telegram bot + AI)
- **Michael:** See `Exchange/from-cradle/Michael/METHODOLOGY.md` (multi-project)
- **New_Media:** See `Exchange/from-cradle/New_Media/METHODOLOGY.md` (content)
- **Psychology:** See `Exchange/from-cradle/Psychology/METHODOLOGY.md` (research)

---

**Version:** 1.0.0
**Created:** 2025-10-25
**Authors:** Cradle OS Team (Claude + Alexey Krol)
**Research:** WebSearch (12 KB) + Perplexity (73 KB) + Parallel (34 KB)
**Theories:** Extended Mind, Knowledge Spiral, VSM, Learning Organization, Evolutionary Organizations

🧬 **Grow Fast, Stay Healthy!**
