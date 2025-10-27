# Cradle: Methodology & Knowledge Base

**Purpose:** Central repository for all project methodologies and lessons learned.

**Maintained by:** GrantService Team
**Last Updated:** 2025-10-27 (Iteration 53)

---

## 📚 What's Inside

### 1. **GRANTSERVICE-LESSONS-LEARNED.md** ⭐ NEW
**Type:** Project-Specific Knowledge
**Size:** ~35 KB
**Sections:** 9

**Content:**
- Real production bugs and fixes
- AI/LLM integration lessons
- Telegram bot patterns
- Database anti-patterns
- Testing strategies that actually work

**When to Read:**
- ✅ Before starting similar project
- ✅ When encountering production bug
- ✅ When debugging Telegram bot issues
- ✅ When working with LLM APIs

---

### 2. **TESTING-METHODOLOGY.md**
**Type:** Testing Strategy
**Size:** ~15 KB
**Author:** Cradle OS Team

**Content:**
- Test pyramid (70% unit, 20% integration, 10% E2E)
- Production parity principles
- When to write tests (and when not to)
- Anti-patterns to avoid

**When to Read:**
- ✅ Before writing new tests
- ✅ When deciding test strategy
- ✅ When automated tests fail

---

### 3. **SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md**
**Type:** General Best Practices
**Size:** ~220 KB
**Sections:** 8 Complete
**Examples:** 100+

**Content:**
- Python & Golang best practices
- Code quality framework
- Anti-patterns catalog
- Production troubleshooting
- CI/CD practices

**When to Read:**
- ✅ When starting new project
- ✅ During code reviews
- ✅ When setting up CI/CD
- ✅ When debugging production issues

---

### 4. **PROJECT-EVOLUTION-METHODOLOGY.md**
**Type:** Development Workflow
**Author:** Cradle OS Team

**Content:**
- 5-phase development lifecycle
- Planning → Development → Integration → Release → Learn
- Iteration structure
- Гомеостаз, Метаболизм, Регенерация principles

**When to Read:**
- ✅ At start of each iteration
- ✅ When planning new feature
- ✅ When reviewing development process

---

### 5. **SELF_LEARNING_SYSTEM_DESIGN.md**
**Type:** Architecture Design
**Author:** Cradle OS Team

**Content:**
- Self-learning system architecture
- Feedback loops
- Knowledge accumulation patterns
- Meta-learning strategies

**When to Read:**
- ✅ When designing adaptive systems
- ✅ When implementing feedback loops
- ✅ When building AI agents

---

## 🎯 Quick Decision Tree

### "I'm starting a new feature..."
1. Read: **PROJECT-EVOLUTION-METHODOLOGY.md** (Planning phase)
2. Read: **GRANTSERVICE-LESSONS-LEARNED.md** (Check similar features)
3. Follow: 5-phase workflow

### "I found a production bug..."
1. Read: **GRANTSERVICE-LESSONS-LEARNED.md** (Production Bugs section)
2. Write: Edge case test to reproduce
3. Fix: Apply lesson learned
4. Update: Add new lesson to document

### "I'm writing tests..."
1. Read: **TESTING-METHODOLOGY.md** (Test strategy)
2. Read: **GRANTSERVICE-LESSONS-LEARNED.md** (Testing lessons)
3. Apply: Production parity principle

### "I'm doing code review..."
1. Check: **SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md** (Anti-patterns)
2. Verify: **GRANTSERVICE-LESSONS-LEARNED.md** (Known issues)
3. Ensure: Tests are production parity

### "I'm debugging production issue..."
1. Check: **GRANTSERVICE-LESSONS-LEARNED.md** (Production Bugs Hall of Fame)
2. Check: **SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md** (Troubleshooting)
3. Add: New lesson if novel bug

---

## 📊 Document Comparison

| Document | Scope | When to Use | Update Frequency |
|----------|-------|-------------|------------------|
| GRANTSERVICE-LESSONS-LEARNED | ⭐ Project-specific | Daily development | After each iteration |
| TESTING-METHODOLOGY | Testing strategy | Before writing tests | Rarely (stable) |
| SOFTWARE-DEV-PRACTICES | General practices | Code reviews | Quarterly |
| PROJECT-EVOLUTION | Development workflow | Planning phase | Rarely (stable) |
| SELF-LEARNING | Architecture | System design | Rarely (stable) |

---

## 🔄 Maintenance Guidelines

### When to Update Documents

**GRANTSERVICE-LESSONS-LEARNED.md:**
- ✅ After finding production bug
- ✅ After major refactoring
- ✅ After each iteration (if lessons learned)
- ✅ When solving hard problem

**TESTING-METHODOLOGY.md:**
- ⚠️ Rarely - only if testing strategy changes
- Example: Switching from unit-first to integration-first

**SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md:**
- ⚠️ Rarely - general practices are stable
- Example: New language added to project

**PROJECT-EVOLUTION-METHODOLOGY.md:**
- ⚠️ Rarely - workflow is stable
- Example: Major process change

---

## 📝 Contributing

### Adding New Lesson
```markdown
1. Identify the lesson category (Testing, AI/LLM, Database, etc.)
2. Add to GRANTSERVICE-LESSONS-LEARNED.md:
   - What happened (with code example)
   - Root cause
   - Fix applied
   - Lesson learned
3. Add edge case test if applicable
4. Update this README if new category added
```

### Updating Existing Lesson
```markdown
1. Find lesson in GRANTSERVICE-LESSONS-LEARNED.md
2. Add "UPDATE (Iteration XX):" section
3. Describe what changed and why
4. Keep old content (shows evolution)
```

---

## 🎓 Reading Order for New Team Members

### Week 1: Core Concepts
1. **CLAUDE.md** (project overview)
2. **PROJECT-EVOLUTION-METHODOLOGY.md** (workflow)
3. **GRANTSERVICE-LESSONS-LEARNED.md** (Sections 1-5)

### Week 2: Deep Dive
4. **TESTING-METHODOLOGY.md** (full read)
5. **SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md** (Sections 1-3)
6. **GRANTSERVICE-LESSONS-LEARNED.md** (Sections 6-9)

### Week 3: Reference
7. **SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md** (Sections 4-8)
8. **SELF_LEARNING_SYSTEM_DESIGN.md** (for AI features)

### Ongoing
- Refer back to **GRANTSERVICE-LESSONS-LEARNED.md** when encountering issues
- Use decision trees above for quick reference

---

## 🏆 Success Metrics

**How we know these docs are useful:**

✅ **0 repeated production bugs** after adding lesson
✅ **50% faster debugging** (consult lessons first)
✅ **80% test coverage** (following testing methodology)
✅ **2-3 iterations** for major features (following evolution methodology)

**Current Stats (Iteration 53):**
- Production bugs documented: 3
- Edge case tests created: 10
- Lessons learned: 20+
- Time saved vs Iteration 52: 78 minutes (78%)

---

## 📞 Questions?

**For methodology questions:**
- Check: **PROJECT-EVOLUTION-METHODOLOGY.md**
- Ask: Team lead or Cradle OS maintainers

**For project-specific questions:**
- Check: **GRANTSERVICE-LESSONS-LEARNED.md** first
- If not found: Document new lesson after solving

**For general best practices:**
- Check: **SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md**
- Reference: Industry standards and Cradle OS guidelines

---

**Remember:**
> "Every bug is a lesson. Every lesson makes us stronger."
> "Read the docs before asking. Document after solving."
> "Knowledge shared is knowledge multiplied."

---

**END OF README**
