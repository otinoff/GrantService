# GrantService Project Refactoring Plan

**Date:** 2025-10-25
**Goal:** Объединить всё в одну папку C:\SnowWhiteAI\GrantService

---

## 🎯 Текущая Проблема

**Сейчас разбросано по 2 папкам:**

### 1. C:\SnowWhiteAI\GrantService (CODE)
```
GrantService/
├── agents/                    # Production code
├── data/                      # Database code
├── telegram-bot/              # Bot code
├── web-admin/                 # Admin panel
├── shared/                    # Shared utilities
├── tests/                     # Tests
├── Iteration_41_Realistic_Interview/  # Testing iterations
├── Iteration_42_Real_Dialog/
├── Iteration_43_Full_Flow/
└── test_*.py                  # Test scripts
```

### 2. C:\SnowWhiteAI\GrantService_Project (DOCUMENTATION)
```
GrantService_Project/
├── 00_Project_Info/           # Project documentation
├── 01_Projects/               # Project plans
├── 02_Research/               # Research
├── 03_Business/               # Business docs
├── 04_Reports/                # Reports
├── 05_Marketing/              # Marketing
├── 06_Archive/                # Archive
└── Development/               # Development docs
```

---

## ✅ Целевая Структура (После Рефакторинга)

### C:\SnowWhiteAI\GrantService (ВСЁ В ОДНОЙ ПАПКЕ)

```
GrantService/
│
├── 📁 src/                            # Production Code
│   ├── agents/                        # AI agents
│   ├── data/                          # Database
│   ├── telegram-bot/                  # Telegram bot
│   ├── web-admin/                     # Admin panel
│   └── shared/                        # Shared utilities
│
├── 📁 tests/                          # All Tests
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── iterations/                    # Testing iterations
│       ├── Iteration_41_Realistic_Interview/
│       ├── Iteration_42_Real_Dialog/
│       └── Iteration_43_Full_Flow/
│
├── 📁 docs/                           # All Documentation
│   ├── 00_Project_Info/               # Project overview
│   ├── 01_Architecture/               # Architecture docs
│   ├── 02_Research/                   # Research notes
│   ├── 03_Business/                   # Business docs
│   ├── 04_Deployment/                 # Deployment guides
│   └── 05_API/                        # API documentation
│
├── 📁 scripts/                        # Utility Scripts
│   ├── deployment/                    # Deployment scripts
│   ├── testing/                       # Test runners
│   └── utilities/                     # Utilities
│
├── 📁 migrations/                     # Database migrations
│   ├── 001_initial_schema.sql
│   ├── 002_add_dialog_history.sql
│   └── ...
│
├── 📁 config/                         # Configuration
│   ├── .env.example
│   ├── config.yaml
│   └── ...
│
├── .gitignore
├── README.md                          # Main README
├── requirements.txt
└── pyproject.toml
```

---

## 📋 Migration Steps

### Step 1: Create New Directory Structure

```bash
cd C:\SnowWhiteAI\GrantService

# Create new structure
mkdir -p src/{agents,data,telegram-bot,web-admin,shared}
mkdir -p tests/{unit,integration,iterations}
mkdir -p docs/{00_Project_Info,01_Architecture,02_Research,03_Business,04_Deployment,05_API}
mkdir -p scripts/{deployment,testing,utilities}
mkdir -p migrations
mkdir -p config
```

### Step 2: Move Production Code

```bash
# Move to src/
mv agents src/
mv data src/
mv telegram-bot src/
mv web-admin src/
mv shared src/
```

### Step 3: Move Tests and Iterations

```bash
# Move iterations to tests/iterations/
mv Iteration_*/ tests/iterations/

# Keep existing tests structure
mv tests/* tests/integration/
```

### Step 4: Move Documentation from GrantService_Project

```bash
# Copy docs from GrantService_Project
cp -r C:\SnowWhiteAI\GrantService_Project/00_Project_Info docs/
cp -r C:\SnowWhiteAI\GrantService_Project/02_Research docs/
cp -r C:\SnowWhiteAI\GrantService_Project/03_Business docs/
cp -r C:\SnowWhiteAI\GrantService_Project/Development docs/04_Deployment
```

### Step 5: Move Migrations

```bash
# Move database migrations
mv data/database/migrations/* migrations/
```

### Step 6: Move Scripts

```bash
# Move test scripts
mv test_*.py scripts/testing/

# Move deployment scripts
mv deploy_*.py scripts/deployment/
mv deploy_*.bat scripts/deployment/
```

### Step 7: Update Import Paths

All Python imports need to be updated:
```python
# BEFORE:
from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

# AFTER:
from src.agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
```

### Step 8: Create New README

Create comprehensive README.md with:
- Project overview
- Architecture diagram
- Setup instructions
- Testing guide
- Deployment guide

---

## 🔄 Alternative: Minimal Refactoring (RECOMMENDED)

Если полная реорганизация слишком большая, можно сделать **минимальный рефакторинг:**

### Keep Current Structure + Add Docs Folder

```
GrantService/
│
├── agents/                    # Keep as is
├── data/                      # Keep as is
├── telegram-bot/              # Keep as is
├── web-admin/                 # Keep as is
├── shared/                    # Keep as is
├── tests/                     # Keep as is
│
├── 📁 docs/                   # NEW - Move all docs here
│   ├── 00_Project_Info/       # From GrantService_Project
│   ├── 01_Architecture/       # From GrantService_Project/Development
│   ├── 02_Research/           # From GrantService_Project
│   ├── 03_Business/           # From GrantService_Project
│   ├── 04_Deployment/         # Deployment guides
│   └── iterations/            # Move iterations here
│       ├── Iteration_41_Realistic_Interview/
│       ├── Iteration_42_Real_Dialog/
│       └── Iteration_43_Full_Flow/
│
├── 📁 scripts/                # NEW - Test scripts
│   └── test_iteration_*.py    # Move test scripts here
│
└── README.md                  # Update
```

**Advantages:**
- NO import path changes needed
- Less risky
- Easier to implement
- Still organized

---

## ⚡ Quick Start (Minimal Refactoring)

### Step 1: Create docs folder
```bash
cd C:\SnowWhiteAI\GrantService
mkdir docs
mkdir docs\iterations
mkdir scripts
```

### Step 2: Move iterations
```bash
mv Iteration_*/ docs/iterations/
```

### Step 3: Move test scripts
```bash
mv test_iteration_*.py scripts/
```

### Step 4: Copy documentation from GrantService_Project
```bash
xcopy /E /I "C:\SnowWhiteAI\GrantService_Project\00_Project_Info" "C:\SnowWhiteAI\GrantService\docs\00_Project_Info"
xcopy /E /I "C:\SnowWhiteAI\GrantService_Project\02_Research" "C:\SnowWhiteAI\GrantService\docs\02_Research"
xcopy /E /I "C:\SnowWhiteAI\GrantService_Project\03_Business" "C:\SnowWhiteAI\GrantService\docs\03_Business"
xcopy /E /I "C:\SnowWhiteAI\GrantService_Project\Development" "C:\SnowWhiteAI\GrantService\docs\04_Deployment"
```

### Step 5: Create/Update README.md

---

## 📝 Commit Plan

After refactoring:
```bash
git add .
git commit -m "refactor: Reorganize project structure - consolidate all docs and iterations

- Move iterations to docs/iterations/
- Move test scripts to scripts/
- Import documentation from GrantService_Project
- Create unified project structure
- Update README with new structure

All code remains functional - no import path changes needed."
```

---

## 🎯 Recommendation

**I RECOMMEND: Minimal Refactoring**

Why:
1. ✅ No breaking changes to imports
2. ✅ Can be done in 5 minutes
3. ✅ Keeps project organized
4. ✅ Easy to revert if needed
5. ✅ No risk to production code

The full refactoring can be done later in Iteration 44+ if needed.

---

**Next Steps:**
1. Review this plan
2. Choose approach (Minimal or Full)
3. Execute refactoring
4. Update README
5. Commit changes
