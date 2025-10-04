-- ============================================================
-- GrantService PostgreSQL Migration Schema
-- Version: 1.0
-- Created: 2025-10-03
-- Description: Complete migration from SQLite to PostgreSQL
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For full-text search

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_sessions INTEGER DEFAULT 0,
    completed_applications INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    login_token VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user',
    permissions JSONB, -- Changed from TEXT to JSONB
    token_expires_at TIMESTAMP
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active, last_active);
CREATE INDEX idx_users_token ON users(login_token) WHERE login_token IS NOT NULL;

COMMENT ON TABLE users IS 'System users with Telegram authentication';
COMMENT ON COLUMN users.permissions IS 'User permissions stored as JSONB';

-- ============================================================
-- TABLE: interview_questions
-- ============================================================
CREATE TABLE interview_questions (
    id SERIAL PRIMARY KEY,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    question_type VARCHAR(50) DEFAULT 'text',
    options JSONB, -- Changed from TEXT to JSONB
    hint_text TEXT,
    is_required BOOLEAN DEFAULT TRUE,
    follow_up_question TEXT,
    validation_rules JSONB, -- Changed from TEXT to JSONB
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_questions_number ON interview_questions(question_number);
CREATE INDEX idx_questions_active ON interview_questions(is_active);
CREATE INDEX idx_questions_field_name ON interview_questions(field_name);

COMMENT ON TABLE interview_questions IS 'Interview questionnaire configuration';

-- ============================================================
-- TABLE: sessions
-- ============================================================
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    current_step VARCHAR(50),
    status VARCHAR(30) DEFAULT 'active',
    conversation_history JSONB, -- Changed from TEXT to JSONB
    collected_data JSONB, -- Changed from TEXT to JSONB
    interview_data JSONB, -- Changed from TEXT to JSONB
    audit_result JSONB, -- Changed from TEXT to JSONB
    plan_structure JSONB, -- Changed from TEXT to JSONB
    final_document TEXT,
    project_name VARCHAR(300),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    ai_requests_count INTEGER DEFAULT 0,
    progress_percentage INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 24,
    last_question_number INTEGER DEFAULT 1,
    answers_data JSONB, -- Changed from TEXT to JSONB
    session_duration_minutes INTEGER DEFAULT 0,
    completion_status VARCHAR(20) DEFAULT 'in_progress',
    anketa_id VARCHAR(50) UNIQUE,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_telegram_id ON sessions(telegram_id);
CREATE INDEX idx_sessions_telegram ON sessions(telegram_id);
CREATE INDEX idx_sessions_anketa_id ON sessions(anketa_id);
CREATE INDEX idx_sessions_anketa ON sessions(anketa_id);
CREATE INDEX idx_sessions_progress ON sessions(progress_percentage);
CREATE INDEX idx_sessions_status ON sessions(completion_status);
CREATE INDEX idx_sessions_activity ON sessions(last_activity);

-- GIN indexes for JSONB columns (for fast querying)
CREATE INDEX idx_sessions_conversation_gin ON sessions USING gin(conversation_history);
CREATE INDEX idx_sessions_interview_gin ON sessions USING gin(interview_data);

COMMENT ON TABLE sessions IS 'User grant application sessions';

-- ============================================================
-- TABLE: user_answers
-- ============================================================
CREATE TABLE user_answers (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer_text TEXT NOT NULL,
    answer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_status VARCHAR(20) DEFAULT 'valid',
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES interview_questions(id) ON DELETE RESTRICT
);

CREATE INDEX idx_user_answers_session ON user_answers(session_id);
CREATE INDEX idx_user_answers_question ON user_answers(question_id);
CREATE INDEX idx_user_answers_timestamp ON user_answers(answer_timestamp);

COMMENT ON TABLE user_answers IS 'User responses to interview questions';

-- ============================================================
-- TABLE: researcher_logs
-- ============================================================
CREATE TABLE researcher_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    session_id INTEGER,
    query_text TEXT NOT NULL,
    perplexity_response TEXT,
    sources JSONB, -- Changed from JSON to JSONB
    usage_stats JSONB, -- Changed from JSON to JSONB
    cost NUMERIC(10, 4) DEFAULT 0.0, -- Changed from REAL
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    credit_balance NUMERIC(10, 4) DEFAULT 0.0, -- Changed from REAL
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_researcher_logs_user_id ON researcher_logs(user_id);
CREATE INDEX idx_researcher_logs_session_id ON researcher_logs(session_id);
CREATE INDEX idx_researcher_logs_created_at ON researcher_logs(created_at);
CREATE INDEX idx_researcher_logs_status ON researcher_logs(status);

COMMENT ON TABLE researcher_logs IS 'Research API query logs';

-- ============================================================
-- TABLE: prompt_categories
-- ============================================================
CREATE TABLE prompt_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    agent_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prompt_categories_agent_type ON prompt_categories(agent_type);
CREATE INDEX idx_prompt_categories_active ON prompt_categories(is_active);

COMMENT ON TABLE prompt_categories IS 'AI agent prompt categories';

-- ============================================================
-- TABLE: agent_prompts
-- ============================================================
CREATE TABLE agent_prompts (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    prompt_template TEXT NOT NULL,
    variables JSONB, -- Changed from TEXT to JSONB
    default_values JSONB, -- Changed from TEXT to JSONB
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES prompt_categories(id) ON DELETE CASCADE
);

CREATE INDEX idx_agent_prompts_category ON agent_prompts(category_id);
CREATE INDEX idx_agent_prompts_active ON agent_prompts(is_active);
CREATE INDEX idx_agent_prompts_priority ON agent_prompts(priority DESC);

COMMENT ON TABLE agent_prompts IS 'AI agent prompt templates';

-- ============================================================
-- TABLE: prompt_versions
-- ============================================================
CREATE TABLE prompt_versions (
    id SERIAL PRIMARY KEY,
    prompt_id INTEGER NOT NULL,
    prompt_template TEXT NOT NULL,
    variables JSONB, -- Changed from TEXT to JSONB
    default_values JSONB, -- Changed from TEXT to JSONB
    version_number INTEGER NOT NULL,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES agent_prompts(id) ON DELETE CASCADE
);

CREATE INDEX idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);
CREATE INDEX idx_prompt_versions_number ON prompt_versions(version_number DESC);

COMMENT ON TABLE prompt_versions IS 'Version history of agent prompts';

-- ============================================================
-- TABLE: grant_applications
-- ============================================================
CREATE TABLE grant_applications (
    id SERIAL PRIMARY KEY,
    application_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content_json JSONB NOT NULL, -- Changed from TEXT to JSONB
    summary TEXT,
    status VARCHAR(30) DEFAULT 'draft',
    user_id INTEGER,
    session_id INTEGER,
    admin_user VARCHAR(100),
    quality_score NUMERIC(4, 2) DEFAULT 0.0, -- Changed from REAL
    llm_provider VARCHAR(50),
    model_used VARCHAR(100),
    processing_time NUMERIC(8, 2) DEFAULT 0.0, -- Changed from REAL
    tokens_used INTEGER DEFAULT 0,
    grant_fund VARCHAR(200),
    requested_amount NUMERIC(15, 2),
    project_duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
    CHECK (status IN ('draft', 'submitted', 'approved', 'rejected'))
);

CREATE INDEX idx_grant_applications_number ON grant_applications(application_number);
CREATE INDEX idx_grant_applications_user ON grant_applications(user_id);
CREATE INDEX idx_grant_applications_status ON grant_applications(status);
CREATE INDEX idx_grant_applications_date ON grant_applications(created_at);
CREATE INDEX idx_grant_applications_content_gin ON grant_applications USING gin(content_json);

COMMENT ON TABLE grant_applications IS 'Grant application submissions';

-- ============================================================
-- TABLE: researcher_research
-- ============================================================
CREATE TABLE researcher_research (
    id SERIAL PRIMARY KEY,
    research_id VARCHAR(100) UNIQUE NOT NULL,
    anketa_id VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    session_id INTEGER,
    research_type VARCHAR(50) DEFAULT 'comprehensive',
    llm_provider VARCHAR(50) NOT NULL,
    model VARCHAR(50),
    status VARCHAR(30) DEFAULT 'pending',
    research_results JSONB, -- Changed from TEXT to JSONB
    metadata JSONB, -- Changed from TEXT to JSONB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
    CHECK (status IN ('pending', 'processing', 'completed', 'error'))
);

CREATE INDEX idx_research_research_id ON researcher_research(research_id);
CREATE INDEX idx_research_anketa_id ON researcher_research(anketa_id);
CREATE INDEX idx_research_user_id ON researcher_research(user_id);
CREATE INDEX idx_research_date ON researcher_research(created_at);
CREATE INDEX idx_research_status ON researcher_research(status);
CREATE INDEX idx_research_provider ON researcher_research(llm_provider);
CREATE INDEX idx_research_results_gin ON researcher_research USING gin(research_results);

COMMENT ON TABLE researcher_research IS 'AI research results for grant applications';

-- ============================================================
-- TABLE: grants
-- ============================================================
CREATE TABLE grants (
    id SERIAL PRIMARY KEY,
    grant_id VARCHAR(50) UNIQUE NOT NULL,
    anketa_id VARCHAR(50) NOT NULL,
    research_id VARCHAR(100) NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    grant_title VARCHAR(200),
    grant_content TEXT,
    grant_sections JSONB, -- Changed from TEXT to JSONB
    metadata JSONB, -- Changed from TEXT to JSONB
    llm_provider VARCHAR(50) NOT NULL,
    model VARCHAR(50),
    status VARCHAR(30) DEFAULT 'draft',
    quality_score INTEGER DEFAULT 0 CHECK (quality_score >= 0 AND quality_score <= 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (anketa_id) REFERENCES sessions(anketa_id) ON DELETE RESTRICT,
    FOREIGN KEY (research_id) REFERENCES researcher_research(research_id) ON DELETE RESTRICT,
    CHECK (status IN ('draft', 'completed', 'submitted', 'approved', 'rejected'))
);

CREATE INDEX idx_grants_grant_id ON grants(grant_id);
CREATE INDEX idx_grants_anketa_id ON grants(anketa_id);
CREATE INDEX idx_grants_research_id ON grants(research_id);
CREATE INDEX idx_grants_user_id ON grants(user_id);
CREATE INDEX idx_grants_date ON grants(created_at);
CREATE INDEX idx_grants_status ON grants(status);
CREATE INDEX idx_grants_provider ON grants(llm_provider);
CREATE INDEX idx_grants_sections_gin ON grants USING gin(grant_sections);

-- Full-text search index
CREATE INDEX idx_grants_title_trgm ON grants USING gin(grant_title gin_trgm_ops);
CREATE INDEX idx_grants_content_trgm ON grants USING gin(grant_content gin_trgm_ops);

COMMENT ON TABLE grants IS 'Final grant documents';

-- ============================================================
-- TABLE: db_version
-- ============================================================
CREATE TABLE db_version (
    id SERIAL PRIMARY KEY,
    version TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE: db_timestamps
-- ============================================================
CREATE TABLE db_timestamps (
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE: auth_logs
-- ============================================================
CREATE TABLE auth_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_auth_logs_user_id ON auth_logs(user_id);
CREATE INDEX idx_auth_logs_created_at ON auth_logs(created_at);
CREATE INDEX idx_auth_logs_action ON auth_logs(action);

COMMENT ON TABLE auth_logs IS 'Authentication and authorization audit log';

-- ============================================================
-- TABLE: page_permissions
-- ============================================================
CREATE TABLE page_permissions (
    id SERIAL PRIMARY KEY,
    page_name VARCHAR(100) UNIQUE NOT NULL,
    required_role VARCHAR(20),
    required_permissions JSONB, -- Changed from TEXT to JSONB
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_page_permissions_role ON page_permissions(required_role);
CREATE INDEX idx_page_permissions_active ON page_permissions(is_active);

COMMENT ON TABLE page_permissions IS 'Access control for admin panel pages';

-- ============================================================
-- TABLE: sent_documents
-- ============================================================
CREATE TABLE sent_documents (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    grant_application_id TEXT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    admin_comment TEXT,
    delivery_status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    error_message TEXT,
    telegram_message_id INTEGER,
    admin_user VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (grant_application_id) REFERENCES grant_applications(application_number) ON DELETE SET NULL,
    CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed'))
);

CREATE INDEX idx_sent_documents_user_id ON sent_documents(user_id);
CREATE INDEX idx_sent_documents_status ON sent_documents(delivery_status);
CREATE INDEX idx_sent_documents_date ON sent_documents(sent_at);
CREATE INDEX idx_sent_documents_grant_id ON sent_documents(grant_application_id);

COMMENT ON TABLE sent_documents IS 'Document delivery tracking';

-- ============================================================
-- TABLE: auditor_results
-- ============================================================
CREATE TABLE auditor_results (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    completeness_score INTEGER NOT NULL CHECK(completeness_score >= 1 AND completeness_score <= 10),
    clarity_score INTEGER NOT NULL CHECK(clarity_score >= 1 AND clarity_score <= 10),
    feasibility_score INTEGER NOT NULL CHECK(feasibility_score >= 1 AND feasibility_score <= 10),
    innovation_score INTEGER NOT NULL CHECK(innovation_score >= 1 AND innovation_score <= 10),
    quality_score INTEGER NOT NULL CHECK(quality_score >= 1 AND quality_score <= 10),
    average_score NUMERIC(4, 2) NOT NULL,
    approval_status VARCHAR(30) DEFAULT 'pending',
    recommendations JSONB, -- Changed from TEXT to JSONB
    auditor_llm_provider VARCHAR(50) NOT NULL,
    model VARCHAR(50),
    metadata JSONB, -- Changed from TEXT to JSONB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    CHECK (approval_status IN ('pending', 'approved', 'needs_revision', 'rejected'))
);

CREATE INDEX idx_auditor_session_id ON auditor_results(session_id);
CREATE INDEX idx_auditor_approval_status ON auditor_results(approval_status);
CREATE INDEX idx_auditor_average_score ON auditor_results(average_score);
CREATE INDEX idx_auditor_created_at ON auditor_results(created_at);
CREATE INDEX idx_auditor_status_date ON auditor_results(approval_status, created_at);

COMMENT ON TABLE auditor_results IS 'AI audit scores for grant applications';

-- ============================================================
-- TABLE: planner_structures
-- ============================================================
CREATE TABLE planner_structures (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    audit_id INTEGER NOT NULL,
    structure_json JSONB NOT NULL, -- Changed from TEXT to JSONB
    sections_count INTEGER DEFAULT 7 CHECK(sections_count > 0),
    total_word_count_target INTEGER DEFAULT 1900 CHECK(total_word_count_target > 0),
    estimated_pages INTEGER DEFAULT 8,
    data_mapping_complete BOOLEAN DEFAULT FALSE,
    missing_data_sections JSONB, -- Changed from TEXT to JSONB
    template_name VARCHAR(100) DEFAULT 'standard_grant_v1',
    template_version VARCHAR(20) DEFAULT '1.0',
    planner_llm_provider VARCHAR(50),
    model VARCHAR(50),
    metadata JSONB, -- Changed from TEXT to JSONB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (audit_id) REFERENCES auditor_results(id) ON DELETE RESTRICT
);

CREATE INDEX idx_planner_session_id ON planner_structures(session_id);
CREATE INDEX idx_planner_audit_id ON planner_structures(audit_id);
CREATE INDEX idx_planner_template ON planner_structures(template_name);
CREATE INDEX idx_planner_data_mapping ON planner_structures(data_mapping_complete);
CREATE INDEX idx_planner_created_at ON planner_structures(created_at);
CREATE INDEX idx_planner_session_mapping ON planner_structures(session_id, data_mapping_complete);
CREATE INDEX idx_planner_structure_gin ON planner_structures USING gin(structure_json);

COMMENT ON TABLE planner_structures IS 'Grant application structure planning';

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Trigger: update_auditor_timestamp
CREATE OR REPLACE FUNCTION update_auditor_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_auditor_timestamp
    BEFORE UPDATE ON auditor_results
    FOR EACH ROW
    EXECUTE FUNCTION update_auditor_timestamp();

-- Trigger: update_planner_timestamp
CREATE OR REPLACE FUNCTION update_planner_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_planner_timestamp
    BEFORE UPDATE ON planner_structures
    FOR EACH ROW
    EXECUTE FUNCTION update_planner_timestamp();

-- Trigger: validate_auditor_average_score
CREATE OR REPLACE FUNCTION validate_auditor_average_score()
RETURNS TRIGGER AS $$
BEGIN
    IF ABS(NEW.average_score - (
        (NEW.completeness_score + NEW.clarity_score +
         NEW.feasibility_score + NEW.innovation_score +
         NEW.quality_score) / 5.0
    )) > 0.1 THEN
        RAISE EXCEPTION 'Average score must equal the mean of all 5 scores';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_auditor_average_score
    BEFORE INSERT ON auditor_results
    FOR EACH ROW
    EXECUTE FUNCTION validate_auditor_average_score();

-- Trigger: auto_set_approval_status
CREATE OR REPLACE FUNCTION auto_set_approval_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.approval_status = 'pending' THEN
        NEW.approval_status = CASE
            WHEN NEW.average_score >= 6.0 THEN 'approved'
            WHEN NEW.average_score >= 4.0 THEN 'needs_revision'
            ELSE 'rejected'
        END;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_set_approval_status
    BEFORE INSERT ON auditor_results
    FOR EACH ROW
    EXECUTE FUNCTION auto_set_approval_status();

-- ============================================================
-- VIEWS
-- ============================================================

-- View: v_recent_audits
CREATE OR REPLACE VIEW v_recent_audits AS
SELECT
    ar.id,
    ar.session_id,
    s.anketa_id,
    s.telegram_id,
    u.username,
    u.first_name,
    u.last_name,
    ar.completeness_score,
    ar.clarity_score,
    ar.feasibility_score,
    ar.innovation_score,
    ar.quality_score,
    ar.average_score,
    ar.approval_status,
    ar.auditor_llm_provider,
    ar.created_at
FROM auditor_results ar
JOIN sessions s ON ar.session_id = s.id
LEFT JOIN users u ON s.telegram_id = u.telegram_id
ORDER BY ar.created_at DESC;

COMMENT ON VIEW v_recent_audits IS 'Recent audit results with user info';

-- View: v_auditor_stats
CREATE OR REPLACE VIEW v_auditor_stats AS
SELECT
    COUNT(*) as total_audits,
    COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved_count,
    COUNT(CASE WHEN approval_status = 'needs_revision' THEN 1 END) as revision_count,
    COUNT(CASE WHEN approval_status = 'rejected' THEN 1 END) as rejected_count,
    ROUND(AVG(average_score), 2) as avg_score,
    ROUND(AVG(completeness_score), 2) as avg_completeness,
    ROUND(AVG(clarity_score), 2) as avg_clarity,
    ROUND(AVG(feasibility_score), 2) as avg_feasibility,
    ROUND(AVG(innovation_score), 2) as avg_innovation,
    ROUND(AVG(quality_score), 2) as avg_quality,
    ROUND(
        COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
        1
    ) as approval_rate_pct
FROM auditor_results
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

COMMENT ON VIEW v_auditor_stats IS 'Audit statistics for last 30 days';

-- View: v_recent_plans
CREATE OR REPLACE VIEW v_recent_plans AS
SELECT
    ps.id,
    ps.session_id,
    s.anketa_id,
    s.telegram_id,
    u.username,
    u.first_name,
    u.last_name,
    ar.average_score as audit_score,
    ar.approval_status as audit_status,
    ps.sections_count,
    ps.total_word_count_target,
    ps.data_mapping_complete,
    ps.template_name,
    ps.created_at
FROM planner_structures ps
JOIN sessions s ON ps.session_id = s.id
JOIN auditor_results ar ON ps.audit_id = ar.id
LEFT JOIN users u ON s.telegram_id = u.telegram_id
ORDER BY ps.created_at DESC;

COMMENT ON VIEW v_recent_plans IS 'Recent planning structures with context';

-- View: v_planner_stats
CREATE OR REPLACE VIEW v_planner_stats AS
SELECT
    COUNT(*) as total_plans,
    COUNT(CASE WHEN data_mapping_complete = TRUE THEN 1 END) as complete_mappings,
    ROUND(AVG(sections_count), 1) as avg_sections,
    ROUND(AVG(total_word_count_target), 0) as avg_word_target,
    template_name,
    COUNT(*) as template_usage_count
FROM planner_structures
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY template_name;

COMMENT ON VIEW v_planner_stats IS 'Planning statistics by template';

-- View: v_plans_incomplete_data
CREATE OR REPLACE VIEW v_plans_incomplete_data AS
SELECT
    ps.id,
    s.anketa_id,
    u.username,
    ps.missing_data_sections,
    ps.sections_count,
    jsonb_array_length(ps.missing_data_sections) as missing_sections_count,
    ps.created_at
FROM planner_structures ps
JOIN sessions s ON ps.session_id = s.id
LEFT JOIN users u ON s.telegram_id = u.telegram_id
WHERE ps.data_mapping_complete = FALSE
    AND ps.missing_data_sections IS NOT NULL
ORDER BY ps.created_at DESC;

COMMENT ON VIEW v_plans_incomplete_data IS 'Plans with incomplete data mapping';

-- ============================================================
-- INITIAL DATA
-- ============================================================

-- Insert DB version
INSERT INTO db_version (version) VALUES ('1.0-postgresql');

-- Insert timestamp
INSERT INTO db_timestamps (timestamp, description)
VALUES (CURRENT_TIMESTAMP::TEXT, 'PostgreSQL migration completed');

-- ============================================================
-- DATABASE SETTINGS OPTIMIZATION
-- ============================================================

-- Optimize for application performance
COMMENT ON DATABASE grantservice IS 'GrantService application database - Optimized for JSONB operations';

-- ============================================================
-- GRANTS
-- ============================================================

-- Grant appropriate permissions (to be customized based on user setup)
-- Example:
-- GRANT CONNECT ON DATABASE grantservice TO grantservice_user;
-- GRANT USAGE ON SCHEMA public TO grantservice_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO grantservice_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO grantservice_user;

-- ============================================================
-- END OF MIGRATION SCHEMA
-- ============================================================
