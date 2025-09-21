# GrantService Database Structure

**Database Path:** `C:\SnowWhiteAI\GrantService\data\grantservice.db`
**Analysis Date:** 2025-09-21T21:15:00.780035
**Total Tables:** 16

## Tables Summary

| Table Name | Row Count | Columns | Indexes | Foreign Keys |
|------------|-----------|---------|---------|--------------|
| interview_questions | 24 | 13 | 2 | 0 |
| sqlite_sequence | 10 | 2 | 0 | 0 |
| users | 4 | 14 | 2 | 0 |
| sessions | 11 | 24 | 6 | 1 |
| user_answers | 0 | 6 | 2 | 2 |
| researcher_logs | 7 | 12 | 3 | 2 |
| prompt_categories | 14 | 7 | 1 | 0 |
| prompt_versions | 1 | 8 | 0 | 1 |
| agent_prompts | 14 | 11 | 0 | 1 |
| grant_applications | 9 | 19 | 1 | 2 |
| researcher_research | 2 | 16 | 7 | 2 |
| grants | 0 | 19 | 8 | 3 |
| db_version | 1 | 3 | 0 | 0 |
| db_timestamps | 1 | 4 | 0 | 0 |
| auth_logs | 3 | 8 | 0 | 1 |
| page_permissions | 0 | 6 | 1 | 0 |

## Detailed Table Structures

### 📊 interview_questions

**Rows:** 24

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| question_number | INTEGER | ✓ |  |  |
| question_text | TEXT | ✓ |  |  |
| field_name | VARCHAR(100) | ✓ |  |  |
| question_type | VARCHAR(50) |  | 'text' |  |
| options | TEXT |  |  |  |
| hint_text | TEXT |  |  |  |
| is_required | BOOLEAN |  | 1 |  |
| follow_up_question | TEXT |  |  |  |
| validation_rules | TEXT |  |  |  |
| is_active | BOOLEAN |  | 1 |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| updated_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

#### Indexes:
- idx_questions_active 
- idx_questions_number 

---

### 📊 sqlite_sequence

**Rows:** 10

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| name |  |  |  |  |
| seq |  |  |  |  |

---

### 📊 users

**Rows:** 4

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| telegram_id | BIGINT | ✓ |  |  |
| username | VARCHAR(100) |  |  |  |
| first_name | VARCHAR(100) |  |  |  |
| last_name | VARCHAR(100) |  |  |  |
| registration_date | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| last_active | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| total_sessions | INTEGER |  | 0 |  |
| completed_applications | INTEGER |  | 0 |  |
| is_active | BOOLEAN |  | 1 |  |
| login_token | VARCHAR(255) |  |  |  |
| role | VARCHAR(20) |  | 'user' |  |
| permissions | TEXT |  |  |  |
| token_expires_at | TIMESTAMP |  |  |  |

#### Indexes:
- idx_users_telegram_id 
- sqlite_autoindex_users_1 UNIQUE

---

### 📊 sessions

**Rows:** 11

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| telegram_id | BIGINT | ✓ |  |  |
| current_step | VARCHAR(50) |  |  |  |
| status | VARCHAR(30) |  | 'active' |  |
| conversation_history | TEXT |  |  |  |
| collected_data | TEXT |  |  |  |
| interview_data | TEXT |  |  |  |
| audit_result | TEXT |  |  |  |
| plan_structure | TEXT |  |  |  |
| final_document | TEXT |  |  |  |
| project_name | VARCHAR(300) |  |  |  |
| started_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| completed_at | TIMESTAMP |  |  |  |
| last_activity | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| total_messages | INTEGER |  | 0 |  |
| ai_requests_count | INTEGER |  | 0 |  |
| progress_percentage | INTEGER |  | 0 |  |
| questions_answered | INTEGER |  | 0 |  |
| total_questions | INTEGER |  | 24 |  |
| last_question_number | INTEGER |  | 1 |  |
| answers_data | TEXT |  |  |  |
| session_duration_minutes | INTEGER |  | 0 |  |
| completion_status | VARCHAR(20) |  | "in_progress" |  |
| anketa_id | VARCHAR(20) |  |  |  |

#### Indexes:
- idx_sessions_anketa 
- idx_sessions_telegram 
- idx_sessions_anketa_id 
- idx_sessions_status 
- idx_sessions_progress 
- idx_sessions_telegram_id 

#### Foreign Keys:
- telegram_id → users.telegram_id

---

### 📊 user_answers

**Rows:** 0

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| session_id | INTEGER | ✓ |  |  |
| question_id | INTEGER | ✓ |  |  |
| answer_text | TEXT | ✓ |  |  |
| answer_timestamp | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| validation_status | VARCHAR(20) |  | 'valid' |  |

#### Indexes:
- idx_user_answers_question 
- idx_user_answers_session 

#### Foreign Keys:
- question_id → interview_questions.id
- session_id → sessions.id

---

### 📊 researcher_logs

**Rows:** 7

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| user_id | INTEGER |  |  |  |
| session_id | INTEGER |  |  |  |
| query_text | TEXT | ✓ |  |  |
| perplexity_response | TEXT |  |  |  |
| sources | JSON |  |  |  |
| usage_stats | JSON |  |  |  |
| cost | REAL |  | 0.0 |  |
| status | VARCHAR(50) |  | 'success' |  |
| error_message | TEXT |  |  |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| credit_balance | REAL |  | 0.0 |  |

#### Indexes:
- idx_researcher_logs_created_at 
- idx_researcher_logs_session_id 
- idx_researcher_logs_user_id 

#### Foreign Keys:
- session_id → user_sessions.id
- user_id → users.id

---

### 📊 prompt_categories

**Rows:** 14

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| name | VARCHAR(100) | ✓ |  |  |
| description | TEXT |  |  |  |
| agent_type | VARCHAR(50) | ✓ |  |  |
| is_active | BOOLEAN |  | 1 |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| updated_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

#### Indexes:
- sqlite_autoindex_prompt_categories_1 UNIQUE

---

### 📊 prompt_versions

**Rows:** 1

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| prompt_id | INTEGER | ✓ |  |  |
| prompt_template | TEXT | ✓ |  |  |
| variables | TEXT |  |  |  |
| default_values | TEXT |  |  |  |
| version_number | INTEGER | ✓ |  |  |
| created_by | VARCHAR(100) |  |  |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:
- prompt_id → agent_prompts.id

---

### 📊 agent_prompts

**Rows:** 14

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| category_id | INTEGER | ✓ |  |  |
| name | VARCHAR(100) | ✓ |  |  |
| description | TEXT |  |  |  |
| prompt_template | TEXT | ✓ |  |  |
| variables | TEXT |  |  |  |
| default_values | TEXT |  |  |  |
| is_active | BOOLEAN |  | 1 |  |
| priority | INTEGER |  | 0 |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| updated_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:
- category_id → prompt_categories.id

---

### 📊 grant_applications

**Rows:** 9

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| application_number | VARCHAR(50) | ✓ |  |  |
| title | VARCHAR(500) | ✓ |  |  |
| content_json | TEXT | ✓ |  |  |
| summary | TEXT |  |  |  |
| status | VARCHAR(30) |  | 'draft' |  |
| user_id | INTEGER |  |  |  |
| session_id | INTEGER |  |  |  |
| admin_user | VARCHAR(100) |  |  |  |
| quality_score | REAL |  | 0.0 |  |
| llm_provider | VARCHAR(50) |  |  |  |
| model_used | VARCHAR(100) |  |  |  |
| processing_time | REAL |  | 0.0 |  |
| tokens_used | INTEGER |  | 0 |  |
| grant_fund | VARCHAR(200) |  |  |  |
| requested_amount | DECIMAL(15,2) |  |  |  |
| project_duration | INTEGER |  |  |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| updated_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

#### Indexes:
- sqlite_autoindex_grant_applications_1 UNIQUE

#### Foreign Keys:
- session_id → sessions.id
- user_id → users.id

#### Sample Data (Latest 5 records):

| ID | User ID | Created At | Status |
|----|---------|------------|--------|
| 9 | None | 2025-09-09T10:38:52.876720+07:00 | draft |
| 8 | None | 2025-09-06T00:22:46.916330+07:00 | draft |
| 7 | None | 2025-08-30T20:54:52.022281+07:00 | draft |
| 6 | None | 2025-08-30T17:23:10.254472+07:00 | draft |
| 5 | None | 2025-08-29T19:40:09.243275+07:00 | draft |

---

### 📊 researcher_research

**Rows:** 2

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| research_id | VARCHAR(50) | ✓ |  |  |
| anketa_id | VARCHAR(20) | ✓ |  |  |
| user_id | BIGINT | ✓ |  |  |
| username | VARCHAR(100) |  |  |  |
| first_name | VARCHAR(100) |  |  |  |
| last_name | VARCHAR(100) |  |  |  |
| session_id | INTEGER |  |  |  |
| research_type | VARCHAR(50) |  | 'comprehensive' |  |
| llm_provider | VARCHAR(50) | ✓ |  |  |
| model | VARCHAR(50) |  |  |  |
| status | VARCHAR(30) |  | 'pending' |  |
| research_results | TEXT |  |  |  |
| metadata | TEXT |  |  |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| completed_at | TIMESTAMP |  |  |  |

#### Indexes:
- idx_research_provider 
- idx_research_status 
- idx_research_date 
- idx_research_user_id 
- idx_research_anketa_id 
- idx_research_research_id 
- sqlite_autoindex_researcher_research_1 UNIQUE

#### Foreign Keys:
- session_id → sessions.id
- user_id → users.telegram_id

---

### 📊 grants

**Rows:** 0

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| grant_id | VARCHAR(50) | ✓ |  |  |
| anketa_id | VARCHAR(20) | ✓ |  |  |
| research_id | VARCHAR(50) | ✓ |  |  |
| user_id | BIGINT | ✓ |  |  |
| username | VARCHAR(100) |  |  |  |
| first_name | VARCHAR(100) |  |  |  |
| last_name | VARCHAR(100) |  |  |  |
| grant_title | VARCHAR(200) |  |  |  |
| grant_content | TEXT |  |  |  |
| grant_sections | TEXT |  |  |  |
| metadata | TEXT |  |  |  |
| llm_provider | VARCHAR(50) | ✓ |  |  |
| model | VARCHAR(50) |  |  |  |
| status | VARCHAR(30) |  | 'draft' |  |
| quality_score | INTEGER |  | 0 |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| updated_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| submitted_at | TIMESTAMP |  |  |  |

#### Indexes:
- idx_grants_provider 
- idx_grants_status 
- idx_grants_date 
- idx_grants_user_id 
- idx_grants_research_id 
- idx_grants_anketa_id 
- idx_grants_grant_id 
- sqlite_autoindex_grants_1 UNIQUE

#### Foreign Keys:
- research_id → researcher_research.research_id
- anketa_id → sessions.anketa_id
- user_id → users.telegram_id

---

### 📊 db_version

**Rows:** 1

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| version | TEXT | ✓ |  |  |
| updated_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

---

### 📊 db_timestamps

**Rows:** 1

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| timestamp | TEXT | ✓ |  |  |
| description | TEXT |  |  |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

---

### 📊 auth_logs

**Rows:** 3

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| user_id | INTEGER |  |  |  |
| action | VARCHAR(50) |  |  |  |
| ip_address | VARCHAR(45) |  |  |  |
| user_agent | TEXT |  |  |  |
| success | BOOLEAN |  | 1 |  |
| error_message | TEXT |  |  |  |
| created_at | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:
- user_id → users.id

---

### 📊 page_permissions

**Rows:** 0

#### Columns:

| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| id | INTEGER |  |  | ✓ |
| page_name | VARCHAR(100) | ✓ |  |  |
| required_role | VARCHAR(20) |  |  |  |
| required_permissions | TEXT |  |  |  |
| description | TEXT |  |  |  |
| is_active | BOOLEAN |  | 1 |  |

#### Indexes:
- sqlite_autoindex_page_permissions_1 UNIQUE

---

## 📋 Grant Applications Analysis

**Total Applications:** 9

The grant_applications table contains filled grant applications.
Each application is linked to a user and contains:
- Application data in JSON format
- User responses to interview questions
- Status tracking
- Timestamps for creation and updates

## 🔍 Key Relationships

1. **Users ↔ Grant Applications**: One-to-many relationship
2. **Users ↔ User Answers**: Track interview responses
3. **Sessions ↔ Users**: Authentication and session management
4. **Interview Questions ↔ User Answers**: Q&A tracking
5. **Grants ↔ Grant Applications**: Grant program tracking