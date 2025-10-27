# Production Deployments

**Purpose:** Document all production releases, testing, and verification.

---

## 📋 Process Overview

Each production deployment follows this workflow:

```
1. PLAN          → What are we deploying?
2. PRE-DEPLOY    → Are we ready? (checklist)
3. DEPLOY        → Execute deployment (log everything)
4. VERIFY        → Does it work? (smoke tests)
5. MONITOR       → Watch for issues (24-48 hours)
```

---

## 📁 Structure

```
deployments/
├── README.md                        ← This file
├── TEMPLATE/                        ← Templates for new releases
│   ├── 00_PLAN.md
│   ├── 01_PRE_DEPLOY_CHECKLIST.md
│   ├── 02_DEPLOYMENT_LOG.md
│   └── 03_VERIFICATION.md
├── Release_001_Initial_Production/  ← Example
├── Release_002_Interviewer_Fix/     ← Iteration 53 fix
└── Release_XXX_Feature_Name/        ← Future releases
```

---

## 🚀 How to Create New Release

### Step 1: Copy Template

```bash
# Create new release folder
cp -r deployments/TEMPLATE deployments/Release_003_Feature_Name

# Edit files
cd deployments/Release_003_Feature_Name
```

### Step 2: Fill Out Documents

1. **00_PLAN.md** - What are we deploying? Why?
2. **01_PRE_DEPLOY_CHECKLIST.md** - Pre-deployment checks
3. **02_DEPLOYMENT_LOG.md** - Log deployment steps (during deploy)
4. **03_VERIFICATION.md** - Smoke tests results (after deploy)

### Step 3: Execute Deployment

Follow the plan, check each item in checklist, log everything.

### Step 4: Verify & Monitor

Run smoke tests, verify critical functionality, monitor for 24-48 hours.

---

## 📊 Release Naming Convention

```
Release_XXX_Short_Description

Where:
  XXX = Sequential number (001, 002, 003...)
  Short_Description = Brief feature/fix name (2-4 words)

Examples:
  Release_001_Initial_Production
  Release_002_Interviewer_Fix
  Release_003_Writer_Upgrade
  Release_004_Database_Migration
```

---

## ✅ Definition of Done

Release is complete when:

- [ ] All 4 documents filled out
- [ ] Pre-deploy checklist 100% passed
- [ ] Deployment log complete (all steps documented)
- [ ] Verification passed (all smoke tests green)
- [ ] Monitoring period complete (24-48h, no critical issues)
- [ ] Git tag created: `release-XXX`
- [ ] Team notified

---

## 🔗 Related Documents

**Development Process:**
- `iterations/` - Development iterations (features, fixes)
- `cradle/PROJECT-EVOLUTION-METHODOLOGY.md` - Development workflow

**Production Process:**
- `deployments/` - Production releases (this folder)
- `C:\SnowWhiteAI\GrantService_Project\Development\PRE_DEPLOY_CHECKLIST.md` - Master checklist

**Monitoring:**
- SSH: `ssh root@5.35.88.251`
- Logs: `/var/log/grantservice/`
- Status: `systemctl status grantservice-bot`

---

## 📈 Release History

| Release | Date | Description | Status |
|---------|------|-------------|--------|
| [002](Release_002_Interviewer_Fix/) | 2025-10-27 | Fix Iteration 53 import bug | ✅ DEPLOYED |
| 001 | TBD | Initial production setup | 📅 PLANNED |

---

**Maintainer:** Grant Service Team
**Last Updated:** 2025-10-27
