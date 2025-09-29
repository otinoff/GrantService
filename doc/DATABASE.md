# Database Schema
**Version**: 1.0.1 | **Last Modified**: 2025-09-29

## Table of Contents
- [Overview](#overview)
- [Database Configuration](#database-configuration)
- [Tables Schema](#tables-schema)
- [Indexes](#indexes)
- [Migrations](#migrations)
- [Backup & Recovery](#backup--recovery)

## Overview

GrantService использует гибридный подход к хранению данных:
- **Production**: PostgreSQL 14+
- **Development**: SQLite 3.35+
- **Cache**: Redis 7+ (optional)

### Database Architecture
```
┌─────────────────────────────────────┐
│         Application Layer           │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│         ORM Layer (SQLAlchemy)      │
└─────────────┬───────────────────────┘
              │
      ┌───────┴────────┬──────────────┐
      ▼                ▼              ▼
┌──────────┐    ┌──────────┐   ┌──────────┐
│PostgreSQL│    │  SQLite  │   │  Redis   │
│  (Prod)  │    │  (Dev)   │   │ (Cache)  │
└──────────┘    └──────────┘   └──────────┘
```

## Database Configuration

### Connection Settings

#### PostgreSQL (Production)
```python
DATABASE_URL = "postgresql://user:password@host:5432/grantservice"

SQLALCHEMY_CONFIG = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    "echo": False
}
```

#### SQLite (Development)
```python
DATABASE_URL = "sqlite:///./data/grantservice.db"

SQLALCHEMY_CONFIG = {
    "check_same_thread": False,
    "echo": True
}
```

#### Redis (Cache)
```python
REDIS_URL = "redis://localhost:6379/0"

REDIS_CONFIG = {
    "decode_responses": True,
    "max_connections": 50,
    "socket_keepalive": True
}
```

## Tables Schema

### Core Tables

#### 1. users
Primary user information table.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_blocked BOOLEAN DEFAULT FALSE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_sessions INTEGER DEFAULT 0,
    completed_applications INTEGER DEFAULT 0,
    login_token VARCHAR(255),
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_token ON users(login_token);
```

#### 2. sessions
User session and interaction tracking.

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT NOT NULL,
    anketa_id VARCHAR(20) UNIQUE,
    current_step VARCHAR(50),
    status VARCHAR(30) DEFAULT 'active',
    conversation_history TEXT,  -- JSON
    collected_data TEXT,         -- JSON
    interview_data TEXT,         -- JSON
    audit_result TEXT,           -- JSON
    plan_structure TEXT,         -- JSON
    final_document TEXT,
    project_name VARCHAR(300),
    grant_direction VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    ai_requests_count INTEGER DEFAULT 0,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);

-- Indexes
CREATE INDEX idx_sessions_telegram_id ON sessions(telegram_id);
CREATE INDEX idx_sessions_anketa_id ON sessions(anketa_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_last_activity ON sessions(last_activity);
```

#### 3. interview_questions
Dynamic interview questions management.

```sql
CREATE TABLE interview_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    question_type VARCHAR(50) DEFAULT 'text',
    options TEXT,                -- JSON array
    hint_text TEXT,
    is_required BOOLEAN DEFAULT TRUE,
    follow_up_question TEXT,
    validation_rules TEXT,        -- JSON
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_questions_number ON interview_questions(question_number);
CREATE INDEX idx_questions_active ON interview_questions(is_active);
CREATE INDEX idx_questions_field ON interview_questions(field_name);
```

#### 4. anketas
Application forms storage.

```sql
CREATE TABLE anketas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    anketa_number VARCHAR(50) UNIQUE,
    status VARCHAR(50) DEFAULT 'draft',
    type VARCHAR(50),
    data JSONB,                   -- PostgreSQL JSON
    project_name VARCHAR(500),
    project_description TEXT,
    target_audience TEXT,
    budget DECIMAL(15,2),
    timeline VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_anketas_user_id ON anketas(user_id);
CREATE INDEX idx_anketas_status ON anketas(status);
CREATE INDEX idx_anketas_number ON anketas(anketa_number);
CREATE INDEX idx_anketas_created ON anketas(created_at);
```

#### 5. grants
Grant applications and submissions.

```sql
CREATE TABLE grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anketa_id INTEGER NOT NULL,
    grant_type VARCHAR(100),
    grant_name VARCHAR(500),
    status VARCHAR(50) DEFAULT 'draft',
    application_text TEXT,
    evaluation_score DECIMAL(3,2),
    reviewer_comments TEXT,
    submitted_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anketa_id) REFERENCES anketas(id)
);

-- Indexes
CREATE INDEX idx_grants_anketa_id ON grants(anketa_id);
CREATE INDEX idx_grants_status ON grants(status);
CREATE INDEX idx_grants_type ON grants(grant_type);
```

##### Business Logic Updates (v1.0.1)
Метод `save_grant_application()` обновлен для интеграции с системой уведомлений:

```python
def save_grant_application(self, application_data: Dict[str, Any]) -> str:
    """Сохранить грантовую заявку в базу данных и отправить уведомление администраторам"""
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Генерация номера заявки
            if 'application_number' in application_data:
                application_number = application_data['application_number']
            else:
                import uuid
                application_number = f"GA-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

            # Сохранение данных заявки
            # ... логика сохранения в БД ...

            logger.info(f"Grant application {application_number} saved successfully")
            return application_number

    except Exception as e:
        logger.error(f"Error saving grant application: {e}")
        raise
```

**Интеграция с уведомлениями**: После успешного сохранения заявки в БД, система автоматически отправляет уведомление администраторам через AdminNotifier.

#### 6. ai_prompts
AI prompts versioning and management.

```sql
CREATE TABLE ai_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type VARCHAR(50) NOT NULL,
    prompt_name VARCHAR(100) NOT NULL,
    prompt_text TEXT NOT NULL,
    model VARCHAR(50) DEFAULT 'gigachat-pro',
    temperature DECIMAL(2,1) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2000,
    version VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_prompts_agent ON ai_prompts(agent_type);
CREATE INDEX idx_prompts_active ON ai_prompts(is_active);
CREATE INDEX idx_prompts_version ON ai_prompts(version);
```

#### 7. documents
Generated documents storage.

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anketa_id INTEGER NOT NULL,
    document_type VARCHAR(50),
    file_name VARCHAR(255),
    file_path TEXT,
    file_size INTEGER,
    mime_type VARCHAR(100),
    hash_sum VARCHAR(64),
    is_final BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (anketa_id) REFERENCES anketas(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_documents_anketa ON documents(anketa_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_created ON documents(created_at);
```

#### 8. notifications
Notification queue and history.

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type VARCHAR(50),
    channel VARCHAR(20) DEFAULT 'telegram',
    subject VARCHAR(255),
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at);
```

#### 9. audit_log
System audit trail.

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_value TEXT,              -- JSON
    new_value TEXT,              -- JSON
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
```

#### 10. system_settings
System configuration storage.

```sql
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE UNIQUE INDEX idx_settings_key ON system_settings(key);
```

## Indexes

### Performance Indexes
```sql
-- Composite indexes for common queries
CREATE INDEX idx_sessions_user_status ON sessions(telegram_id, status);
CREATE INDEX idx_anketas_user_status ON anketas(user_id, status);
CREATE INDEX idx_grants_status_type ON grants(status, grant_type);

-- Full-text search indexes (PostgreSQL)
CREATE INDEX idx_anketas_search ON anketas USING gin(to_tsvector('russian', project_description));
CREATE INDEX idx_grants_search ON grants USING gin(to_tsvector('russian', application_text));

-- Partial indexes
CREATE INDEX idx_active_users ON users(telegram_id) WHERE is_active = TRUE;
CREATE INDEX idx_pending_notifications ON notifications(scheduled_at) WHERE status = 'pending';
```

## Migrations

### Migration Strategy
```python
# Alembic configuration
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Upgrade database schema"""
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )

def downgrade():
    """Rollback database schema"""
    op.drop_table('new_table')
```

### Migration Files Structure
```
data/migrations/
├── alembic.ini
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_grants_table.py
│   ├── 003_add_notifications.py
│   └── 004_add_audit_log.py
└── env.py
```

### Running Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show migration history
alembic history
```

## Backup & Recovery

### Backup Strategy

#### PostgreSQL Backup
```bash
# Full backup
pg_dump -h localhost -U user -d grantservice > backup.sql

# Compressed backup
pg_dump -h localhost -U user -d grantservice | gzip > backup.sql.gz

# Custom format (allows selective restore)
pg_dump -Fc -h localhost -U user -d grantservice > backup.dump
```

#### SQLite Backup
```python
import sqlite3
import shutil

def backup_sqlite():
    # Simple file copy
    shutil.copy2('data/grantservice.db', 'backups/grantservice_backup.db')

    # Using SQLite backup API
    source = sqlite3.connect('data/grantservice.db')
    backup = sqlite3.connect('backups/grantservice_backup.db')

    with backup:
        source.backup(backup)

    source.close()
    backup.close()
```

### Recovery Process

#### PostgreSQL Recovery
```bash
# Restore from SQL dump
psql -h localhost -U user -d grantservice < backup.sql

# Restore from custom format
pg_restore -h localhost -U user -d grantservice backup.dump

# Restore specific tables
pg_restore -h localhost -U user -d grantservice -t users -t anketas backup.dump
```

#### Point-in-Time Recovery
```sql
-- Enable WAL archiving for PITR
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /backup/archive/%f';

-- Restore to specific time
SELECT pg_create_restore_point('before_major_update');
```

### Automated Backup Schedule
```yaml
# Cron schedule for automated backups
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup_database.sh

# Weekly full backup on Sunday
0 3 * * 0 /usr/local/bin/full_backup.sh

# Monthly archive on 1st
0 4 1 * * /usr/local/bin/archive_backup.sh
```

## Data Retention Policy

### Retention Rules
| Table | Retention Period | Archive Strategy |
|-------|-----------------|------------------|
| users | Permanent | No deletion |
| sessions | 90 days | Archive to cold storage |
| anketas | 1 year | Archive completed |
| grants | Permanent | No deletion |
| notifications | 30 days | Delete after sending |
| audit_log | 2 years | Archive yearly |
| documents | 1 year | Move to S3 |

### Cleanup Scripts
```python
def cleanup_old_sessions():
    """Remove sessions older than 90 days"""
    cutoff_date = datetime.now() - timedelta(days=90)

    query = """
        DELETE FROM sessions
        WHERE last_activity < :cutoff
        AND status != 'active'
    """

    db.execute(query, {"cutoff": cutoff_date})
```

## Performance Optimization

### Query Optimization
```sql
-- Use EXPLAIN ANALYZE
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM anketas
WHERE user_id = 123
AND status = 'active';

-- Optimize common queries
CREATE INDEX CONCURRENTLY idx_optimize_1
ON sessions(telegram_id, status, last_activity DESC);
```

### Connection Pooling
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=1800
)
```

### Partitioning (PostgreSQL)
```sql
-- Partition large tables by date
CREATE TABLE audit_log_2025 PARTITION OF audit_log
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE audit_log_2026 PARTITION OF audit_log
FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-29 | Initial database documentation |

---

*This document is maintained by documentation-keeper agent*