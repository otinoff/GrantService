# GrantService - AI-Powered Grant Application System

## 🎯 Project Overview
GrantService is an automated system for creating grant applications using AI agents. The system guides users through the grant application process via a Telegram bot, leveraging multiple specialized AI agents to collect information, analyze projects, structure applications, and generate professional grant proposals.

## 🏗 Architecture

### Core Components
- **Telegram Bot** - User interface for grant application process
- **n8n Workflows** - Business logic orchestration
- **GigaChat API** - Russian LLM for content generation
- **PostgreSQL/SQLite** - Data persistence
- **Streamlit Admin** - Web administration panel

### AI Agents Pipeline
1. **Interviewer Agent** - Collects project information through guided dialogue
2. **Auditor Agent** - Analyzes project viability and scoring (1-10 scale)
3. **Planner Agent** - Structures grant application sections
4. **Writer Agent** - Generates professional grant text

## 📂 Project Structure
```
GrantService/
├── telegram-bot/       # Telegram bot implementation
├── web-admin/         # Streamlit admin interface
├── agents/           # AI agent configurations
├── data/            # Database and storage
├── scripts/         # Utility scripts
├── n8n-workflows/   # Workflow definitions
└── .claude/        # Claude Code agents
    └── agents/     # Specialized development agents
```

## 🤖 Available Claude Code Agents

### grant-architect
Main system architect specializing in grant application systems and AI agent design.
```bash
# Use for architectural decisions, system design, grant logic
@grant-architect help me design a new grant evaluation module
```

### telegram-bot-developer
Expert in Telegram bot development with python-telegram-bot v20+.
```bash
# Use for bot features, handlers, user interaction
@telegram-bot-developer implement conversation flow for grant interview
```

### database-manager
PostgreSQL/SQLite expert for schema design and optimization.
```bash
# Use for database operations, migrations, optimization
@database-manager optimize the grant_applications table queries
```

### ai-integration-specialist
GigaChat API integration and prompt engineering expert.
```bash
# Use for AI prompts, token optimization, agent configuration
@ai-integration-specialist improve the interviewer agent prompts
```

### documentation-keeper
Expert in maintaining modular, versioned documentation across 8 core files.
```bash
# Use for updating docs after code changes
@documentation-keeper update docs after adding new feature
```

### deployment-manager
Automates full deployment cycle: git push, monitoring, verification, reporting.
```bash
# Use for deploying to production
@deployment-manager deploy latest changes to production
@deployment-manager check server status
@deployment-manager rollback last deployment
```

## 🚀 Quick Start

### Launch Admin Panel
```bash
# Windows
admin.bat

# Linux/Mac
./admin.sh

# Alternative
python launcher.py
```

### Test Installation
```bash
python launcher.py --test
```

## 💾 Database Schema

### Key Tables
- **users** - System users (telegram_id, role, permissions)
- **sessions** - User sessions and progress tracking
- **interview_questions** - Dynamic questionnaire (24 questions)
- **grant_applications** - Completed applications
- **agent_prompts** - AI agent configurations
- **researcher_research** - Research data and analysis
- **grants** - Final grant documents

### Database Location
```
C:\SnowWhiteAI\GrantService\data\grantservice.db
```

## 🔧 Development Guidelines

### Code Style
- Python 3.9+ with type hints
- Async/await for Telegram bot handlers
- SQLAlchemy for database operations
- Environment variables for configuration

### Testing Commands
```bash
# Run tests
python test_streamlit_imports.py
python test_anketa_autosave.py
python test_deep_link.py

# Check database
python check_remote_db.py
```

### Git Workflow
```bash
# Feature branch workflow
git checkout -b feature/your-feature
git commit -m "feat: your feature description"
git push origin feature/your-feature
```

## 🔐 Security

### Authentication
- Telegram ID-based authentication
- JWT tokens for admin panel
- Role-based access control (user, coordinator, admin)

### Data Protection
- Personal data stored on Russian servers
- HTTPS for all connections
- Token expiration and rotation

## 📊 Monitoring

### Key Metrics
- Application completion rate
- Average time to complete
- Grant approval success rate
- AI token usage and costs
- User satisfaction (NPS)

### Health Checks
- Database connectivity
- Telegram bot status
- GigaChat API availability
- Admin panel responsiveness

## 🛠 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   - Always launch via `launcher.py` or `admin.bat`
   - Check Python path configuration

2. **Database Connection**
   - Verify SQLite file exists
   - Check file permissions

3. **Telegram Bot Not Responding**
   - Check token in environment variables
   - Verify webhook/polling configuration

4. **AI Agent Errors**
   - Monitor GigaChat API quota
   - Check prompt token limits
   - Review context window size

## 📝 Important Files

- **ARCHITECTURE.md** - Detailed system architecture
- **ROADMAP_UNIFIED_AGENTS.md** - Agent development roadmap
- **DEPLOYMENT_STATUS.md** - Current deployment status
- **launcher.py** - Main application entry point

## 🎯 Project Goals

1. **Increase Grant Success Rate** from 10-15% to 40-50%
2. **Automate Application Process** reducing time from weeks to hours
3. **Provide Expert-Level Quality** through specialized AI agents
4. **Support Multiple Grant Types** (presidential, youth, international)

## 👥 Team

- **Developer**: Nikolay Stepanov
- **Consultant**: Andrey Otinov (@otinoff)
- **Contact**: otinoff@gmail.com

## 🚦 Current Status

- ✅ Core architecture implemented
- ✅ Database schema deployed
- ✅ Admin panel functional
- ✅ Basic AI agents configured
- 🔄 Telegram bot in testing
- 📅 Production launch: September 2025

## 🔄 Next Steps

1. Complete Telegram bot conversation flows
2. Optimize AI agent prompts for better results
3. Implement analytics dashboard
4. Add multi-language support
5. Deploy to production environment

---

*Last Updated: 2025-09-29*
*Version: 1.0*