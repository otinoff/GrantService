# 🚀 ЗАПУСК АДМИНКИ GRANTSERVICE

## БЫСТРЫЙ СТАРТ

### Windows:
```bash
admin.bat
```

### Linux/Ubuntu:
```bash
chmod +x admin.sh
./admin.sh
```

### Альтернатива:
```bash
# Windows
python launcher.py

# Linux
python3 launcher.py
```

## ⚠️ ВАЖНО
**НЕ запускайте напрямую через streamlit!** Это не будет работать.
```bash
# ❌ НЕПРАВИЛЬНО:
streamlit run web-admin/pages/🏠_Главная.py
python start_admin.bat  # .bat это не Python!

# ✅ ПРАВИЛЬНО:
admin.bat               # или
python launcher.py
```

## ПРОВЕРКА
```bash
python launcher.py --test
```

Успешный тест покажет:
- ✅ data.database imported successfully
- ✅ Bot constants loaded

## СТРУКТУРА ПРОЕКТА

```
GrantService/
│
├── 📁 agents/                   # AI Agents (Production Code)
│   ├── interactive_interviewer_agent_v2.py
│   ├── full_flow_manager.py
│   ├── synthetic_user_simulator.py
│   └── ...
│
├── 📁 data/                     # Database Layer
│   ├── database/
│   └── ...
│
├── 📁 telegram-bot/             # Telegram Bot
│   ├── bot.py
│   ├── handlers/
│   └── ...
│
├── 📁 web-admin/                # Admin Panel (Streamlit)
│   ├── pages/
│   └── ...
│
├── 📁 shared/                   # Shared Utilities
│   └── ...
│
├── 📁 tests/                    # All Tests
│   ├── unit/
│   ├── integration/
│   └── ...
│
├── 📁 iterations/               # Development Iterations
│   ├── Iteration_41_Realistic_Interview/
│   ├── Iteration_42_Real_Dialog/
│   └── Iteration_43_Full_Flow/
│
├── 📁 scripts/                  # Utility Scripts
│   ├── test_iteration_41_realistic_interview.py
│   ├── test_iteration_42_real_dialog.py
│   ├── test_iteration_42_single_anketa.py
│   └── test_iteration_43_full_flow.py
│
├── 📁 docs/                     # Documentation
│   ├── 00_Project_Info/         # Project overview
│   ├── 02_Research/             # Research notes
│   ├── 03_Business/             # Business docs
│   └── 04_Deployment/           # Deployment guides
│
├── 📁 archive/                  # Archived Files
│   ├── old_tests/
│   ├── old_utils/
│   └── old_docs/
│
├── launcher.py                  # Main launcher
├── admin.bat                    # Windows launcher
├── admin.sh                     # Linux launcher
├── README.md                    # This file
└── REFACTORING_PLAN.md          # Refactoring documentation
```

## ПРОБЛЕМЫ?

1. **ModuleNotFoundError**: Запускайте через `launcher.py`
2. **SyntaxError с .bat**: Не запускайте .bat через python
3. **Import error**: Используйте `admin.bat` или `python launcher.py`

## ПОСЛЕ ЗАПУСКА
Откройте браузер: http://localhost:8501

---
**Все файлы рефакторены. Система готова к работе на Windows и Linux.**