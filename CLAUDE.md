# GrantService - AI-Powered Grant Application System

## 🎯 Project Overview
GrantService is an automated system for creating grant applications using AI agents. The system guides users through the grant application process via a Telegram bot, leveraging multiple specialized AI agents to collect information, analyze projects, structure applications, and generate professional grant proposals.

## 🏗 Architecture

### Core Components
- **Telegram Bot** - User interface for grant application process
- **n8n Workflows** - Business logic orchestration
- **Claude Code API** - Premium AI (Opus 4 & Sonnet 4.5) for grant generation via HTTP wrapper
- **GigaChat API** - Russian LLM for user communication
- **PostgreSQL** - Primary data persistence (production)
- **Streamlit Admin** - Web administration panel

### AI Agents Pipeline
1. **Interviewer Agent** (GigaChat) - Collects project information through guided dialogue in Russian
2. **Researcher Agent** (Claude Sonnet 4.5 + WebSearch) - Researches grants and competition analysis
3. **Auditor Agent** (Claude Sonnet 4.5) - Analyzes project viability and scoring (1-10 scale)
4. **Planner Agent** (Claude Sonnet 4.5) - Structures grant application sections
5. **Writer Agent** (Claude Opus 4) - Generates professional grant text with premium quality

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

### claude-code-expert
Expert in Claude Code CLI integration, OAuth, WebSearch, and troubleshooting.
```bash
# Use for Claude Code integration issues
@claude-code-expert fix wrapper server connection
@claude-code-expert troubleshoot OAuth IP binding
```

### garbage-collector
Specialized agent for analyzing and cleaning temporary files, reports, and project clutter.
```bash
# Use for cleanup tasks
@garbage-collector analyze and clean temporary files
@garbage-collector identify obsolete documentation
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

5. **Claude Code API Issues**
   - Check wrapper server status: `curl http://178.236.17.55:8000/health`
   - Verify OAuth credentials on wrapper server
   - Review logs: `ssh root@178.236.17.55 tail -f /var/log/claude-wrapper.log`
   - See `Claude Code CLI/SETUP_GUIDE_178_SERVER_DETAILED.md` for troubleshooting

## 📝 Important Files

- **ARCHITECTURE.md** - Detailed system architecture
- **ROADMAP_UNIFIED_AGENTS.md** - Agent development roadmap
- **launcher.py** - Main application entry point
- **Claude Code CLI/** - Complete Claude Code integration documentation and setup guides
  - **BASE_RULES_CLAUDE_CODE.md** - Strategic requirements for Claude usage
  - **SETUP_GUIDE_178_SERVER_DETAILED.md** - Complete wrapper deployment guide
  - **SESSION_FINAL_REPORT_2025-10-12.md** - Integration session timeline

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
- ✅ Database schema deployed (PostgreSQL production)
- ✅ Admin panel functional
- ✅ Claude Code CLI integrated (Opus 4 + Sonnet 4.5)
- ✅ All AI agents configured with database-driven prompts
- ✅ WebSearch integration for Researcher Agent
- 🔄 Telegram bot in testing
- 🚀 Production: http://5.35.88.251:8501

## 🔄 Next Steps

1. Complete Telegram bot conversation flows
2. Test Claude Opus 4 Writer Agent with real grant applications
3. Optimize AI agent prompts based on results
4. Implement advanced analytics dashboard
5. Scale up with multiple concurrent users

---

*Last Updated: 2025-10-12*
*Version: 2.0* (Claude Code Integration Complete)