# GrantService - AI Grant Application Generator

**Project Type:** AI-powered Telegram Bot for Grant Applications
**Status:** Production (Sber500 Bootcamp participant)
**LLM Primary:** GigaChat-Max (switched from Claude Code 2025-10-25)

---

## 🌅 MORNING PROTOCOL

### 1. Check INBOX
📬 `@C:\SnowWhiteAI\Exchange\from-cradle\GrantService\`
- New messages from Cradle OS or other projects?
- Read → Apply → Archive to `.messages/archive/`

### 2. Check Current Iteration
📂 `C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\`
- Latest: `Iteration_XX_Name/`
- Read `00_PLAN.md` or `SUCCESS.md`

### 3. Review Status
- Tests passing? `pytest tests/`
- Bot running? Check logs
- Database healthy?

---

## 📁 PROJECT STRUCTURE

### Code (Production):
```
C:\SnowWhiteAI\GrantService\
├── telegram-bot/          # Telegram bot
├── agents/                # AI agents
├── data/database/         # PostgreSQL
├── shared/llm/            # GigaChat, Claude
└── tests/                 # Tests
```

### Documentation:
```
C:\SnowWhiteAI\GrantService_Project\
├── Development/
│   └── 02_Feature_Development/
│       └── Interviewer_Iterations/
│           └── Iteration_XX_Name/
└── 01_Projects/
    └── 2025-10-20_Bootcamp_GrantService/
```

---

## 🔄 METHODOLOGY

**Follow:** Project Evolution Methodology (Cradle OS)

**Principles:**
- **Гомеостаз:** Tests before commit, Pre-Deploy Checklist
- **Метаболизм:** Small commits (<200 lines), 2-5 per day
- **Регенерация:** 80% features / 20% tech debt

**Workflow:**
1. PLAN (15%) → 2. DEVELOP (daily) → 3. INTEGRATE → 4. RELEASE → 5. LEARN

---

## 📬 EXCHANGE PROTOCOL

**INBOX:** `C:\SnowWhiteAI\Exchange\from-cradle\GrantService\`
**OUTBOX:** `C:\SnowWhiteAI\Exchange\to-cradle\GrantService\`

When message received → Read → Apply → Archive

---

## 🎯 SBER500 BOOTCAMP

**Goal:** Top-50 for акселератор
**Metric:** GigaChat token usage
**Client ID:** 967330d4-e5ab-4fca-a8e8-12a7d510d249

**Plan:** `01_Projects/2025-10-20_Bootcamp_GrantService/GIGACHAT_SWITCH_PLAN.md`

---

## 🚀 QUICK COMMANDS

**Start bot:**
```bash
python telegram-bot/main.py
```

**Tests:**
```bash
pytest tests/
```

**Production SSH:**
```bash
ssh root@5.35.88.251
```

---

## 📋 PRE-DEPLOY CHECKLIST

Before production deploy:
`C:\SnowWhiteAI\GrantService_Project\Development\PRE_DEPLOY_CHECKLIST.md`

---

## 📊 CURRENT STATUS

**Iteration:** 36 - Methodology Cleanup
**Previous:** 35 - Anketa Management ✅
**LLM:** GigaChat-Max (primary)

---

**Last Updated:** 2025-10-25
**Iteration:** 36
