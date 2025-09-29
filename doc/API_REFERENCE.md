# API Reference
**Version**: 1.0.1 | **Last Modified**: 2025-09-30

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [REST API Endpoints](#rest-api-endpoints)
- [Webhook Endpoints](#webhook-endpoints)
- [Telegram Bot API](#telegram-bot-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Overview

GrantService предоставляет несколько типов API:
- **REST API** - для веб-интерфейса и внешних интеграций
- **Webhook API** - для n8n workflows и интеграций
- **Telegram Bot API** - команды и обработчики бота

### Base URLs
```
Production: https://api.grantservice.ru
Development: http://localhost:8000
Webhooks: https://n8n.grantservice.ru/webhook
```

### Request/Response Format
- **Content-Type**: `application/json`
- **Encoding**: UTF-8
- **Date Format**: ISO 8601 (YYYY-MM-DDTHH:mm:ss.sssZ)

## Authentication

### Telegram OAuth
```http
POST /api/auth/telegram
Content-Type: application/json

{
    "id": 123456789,
    "first_name": "Ivan",
    "last_name": "Ivanov",
    "username": "ivanov",
    "auth_date": 1234567890,
    "hash": "a1b2c3d4e5f6..."
}

Response 200 OK:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
        "id": 1,
        "telegram_id": 123456789,
        "username": "ivanov",
        "role": "user"
    }
}
```

### JWT Token
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### API Key
```http
X-API-Key: your-api-key-here
```

## REST API Endpoints

### Users

#### Get Current User
```http
GET /api/users/me
Authorization: Bearer {token}

Response 200 OK:
{
    "id": 1,
    "telegram_id": 123456789,
    "username": "ivanov",
    "first_name": "Ivan",
    "last_name": "Ivanov",
    "role": "user",
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z",
    "statistics": {
        "total_sessions": 5,
        "completed_applications": 2
    }
}
```

#### Update User Profile
```http
PUT /api/users/me
Authorization: Bearer {token}
Content-Type: application/json

{
    "email": "ivan@example.com",
    "phone": "+7-900-123-45-67"
}

Response 200 OK:
{
    "message": "Profile updated successfully",
    "user": {...}
}
```

#### List Users (Admin)
```http
GET /api/users?page=1&limit=20&role=user&active=true
Authorization: Bearer {admin_token}

Response 200 OK:
{
    "items": [...],
    "total": 150,
    "page": 1,
    "pages": 8,
    "limit": 20
}
```

### Anketas

#### Create Anketa
```http
POST /api/anketas
Authorization: Bearer {token}
Content-Type: application/json

{
    "type": "grant_application",
    "project_name": "Образовательный проект",
    "data": {
        "description": "Описание проекта...",
        "goals": ["Цель 1", "Цель 2"],
        "audience": "Школьники 10-15 лет"
    }
}

Response 201 Created:
{
    "id": 123,
    "anketa_number": "AN-2025-01-29-001",
    "status": "draft",
    "created_at": "2025-01-29T12:00:00Z"
}
```

#### Get Anketa
```http
GET /api/anketas/{anketa_id}
Authorization: Bearer {token}

Response 200 OK:
{
    "id": 123,
    "anketa_number": "AN-2025-01-29-001",
    "user_id": 1,
    "status": "in_progress",
    "type": "grant_application",
    "data": {...},
    "created_at": "2025-01-29T12:00:00Z",
    "updated_at": "2025-01-29T13:00:00Z"
}
```

#### Update Anketa
```http
PATCH /api/anketas/{anketa_id}
Authorization: Bearer {token}
Content-Type: application/json

{
    "data": {
        "budget": 500000,
        "timeline": "6 months"
    }
}

Response 200 OK:
{
    "message": "Anketa updated successfully",
    "anketa": {...}
}
```

#### List User Anketas
```http
GET /api/anketas?status=active&sort=-created_at
Authorization: Bearer {token}

Response 200 OK:
{
    "items": [
        {
            "id": 123,
            "anketa_number": "AN-2025-01-29-001",
            "project_name": "Образовательный проект",
            "status": "active",
            "created_at": "2025-01-29T12:00:00Z"
        }
    ],
    "total": 5
}
```

#### Submit Anketa
```http
POST /api/anketas/{anketa_id}/submit
Authorization: Bearer {token}

Response 200 OK:
{
    "message": "Anketa submitted successfully",
    "anketa": {
        "id": 123,
        "status": "submitted",
        "submitted_at": "2025-01-29T14:00:00Z"
    }
}
```

### Grants

#### Generate Grant Application
```http
POST /api/grants/generate
Authorization: Bearer {token}
Content-Type: application/json

{
    "anketa_id": 123,
    "grant_type": "presidential",
    "ai_agent": "writer"
}

Response 202 Accepted:
{
    "task_id": "abc-123-def",
    "status": "processing",
    "message": "Grant application generation started"
}
```

#### Get Grant Status
```http
GET /api/grants/{grant_id}
Authorization: Bearer {token}

Response 200 OK:
{
    "id": 456,
    "anketa_id": 123,
    "grant_type": "presidential",
    "status": "generated",
    "application_text": "...",
    "evaluation_score": 8.5,
    "created_at": "2025-01-29T15:00:00Z"
}
```

#### Export Grant Document
```http
GET /api/grants/{grant_id}/export?format=docx
Authorization: Bearer {token}

Response 200 OK:
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="grant_application_456.docx"

[Binary Document Data]
```

### AI Agents

#### List AI Prompts
```http
GET /api/prompts?agent_type=interviewer&active=true
Authorization: Bearer {token}

Response 200 OK:
{
    "items": [
        {
            "id": 1,
            "agent_type": "interviewer",
            "prompt_name": "initial_interview",
            "version": "1.2.0",
            "is_active": true
        }
    ],
    "total": 4
}
```

#### Update AI Prompt (Admin)
```http
PUT /api/prompts/{prompt_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "prompt_text": "Updated prompt text...",
    "temperature": 0.8,
    "max_tokens": 2500
}

Response 200 OK:
{
    "message": "Prompt updated successfully",
    "prompt": {...}
}
```

#### Test AI Agent
```http
POST /api/ai/test
Authorization: Bearer {token}
Content-Type: application/json

{
    "agent_type": "auditor",
    "input_text": "Test project description...",
    "model": "gigachat-pro"
}

Response 200 OK:
{
    "response": "AI agent response...",
    "tokens_used": 1500,
    "execution_time": 2.3
}
```

### Documents

#### Upload Document
```http
POST /api/documents/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [binary data]
anketa_id: 123
document_type: "supporting_document"

Response 201 Created:
{
    "id": 789,
    "file_name": "document.pdf",
    "file_size": 1024567,
    "mime_type": "application/pdf",
    "url": "/api/documents/789/download"
}
```

#### Download Document
```http
GET /api/documents/{document_id}/download
Authorization: Bearer {token}

Response 200 OK:
Content-Type: [document mime type]
Content-Disposition: attachment; filename="document.pdf"

[Binary Document Data]
```

### Statistics

#### Get User Statistics
```http
GET /api/statistics/user
Authorization: Bearer {token}

Response 200 OK:
{
    "total_anketas": 10,
    "completed_anketas": 5,
    "draft_anketas": 3,
    "submitted_grants": 2,
    "success_rate": 0.4,
    "ai_requests": 150,
    "last_activity": "2025-01-29T16:00:00Z"
}
```

#### Get System Statistics (Admin)
```http
GET /api/statistics/system
Authorization: Bearer {admin_token}

Response 200 OK:
{
    "total_users": 500,
    "active_users_today": 50,
    "total_anketas": 1500,
    "total_grants": 800,
    "ai_requests_today": 2000,
    "system_health": {
        "database": "healthy",
        "ai_service": "healthy",
        "storage": "healthy"
    }
}
```

## Webhook Endpoints

### Telegram Bot Webhooks

#### Send Admin Notification (v1.0.1)
```http
POST /webhook/telegram/admin-notification
Content-Type: application/json
Authorization: Bearer {token}

{
    "application_data": {
        "application_number": "GA-20250930-A1B2C3D4",
        "title": "Образовательный проект",
        "status": "submitted"
    },
    "user_data": {
        "telegram_id": 123456789,
        "username": "user123",
        "full_name": "Иван Иванов"
    }
}

Response 200 OK:
{
    "success": true,
    "message_id": 313,
    "group_id": -4930683040,
    "timestamp": "2025-09-30T12:00:00Z"
}

Response 500 Error:
{
    "error": "Failed to send notification",
    "details": "Bot was blocked by the user or group"
}
```

#### Process Message
```http
POST /webhook/telegram/message
Content-Type: application/json
X-Telegram-Bot-Api-Secret-Token: {secret}

{
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {...},
        "chat": {...},
        "text": "/start"
    }
}

Response 200 OK:
{
    "ok": true
}
```

### n8n Workflow Webhooks

#### Start Interview
```http
POST /webhook/n8n/interview/start
Content-Type: application/json

{
    "user_id": 123,
    "telegram_id": 123456789,
    "anketa_id": 456
}

Response 200 OK:
{
    "status": "started",
    "workflow_id": "interview_001",
    "next_step": "question_1"
}
```

#### Process AI Response
```http
POST /webhook/n8n/ai/process
Content-Type: application/json

{
    "agent_type": "writer",
    "input_data": {...},
    "callback_url": "https://example.com/callback"
}

Response 202 Accepted:
{
    "task_id": "ai-task-123",
    "status": "processing",
    "estimated_time": 30
}
```

## Telegram Bot API

### Bot Information (Production)
- **Bot Username**: @Grafana_SnowWhite_bot
- **Bot ID**: 8057176426
- **Admin Group**: "Грантсервис" (ID: -4930683040)
- **Version**: 2.1.4
- **Features**: Admin notifications, improved error handling

### Commands

#### User Commands
```
/start - Начать работу с ботом
/interview - Запустить интервью
/status - Проверить статус заявки
/help - Получить помощь
/cancel - Отменить текущую операцию
/export - Экспортировать документ
/profile - Мой профиль
/anketas - Мои анкеты
```

#### Admin Commands
```
/admin - Открыть админ-панель
/stats - Статистика системы
/broadcast - Создать рассылку
/users - Управление пользователями
/logs - Просмотр логов
/backup - Создать резервную копию
```

### Inline Keyboards

#### Main Menu
```python
keyboard = [
    [InlineKeyboardButton("📝 Новая анкета", callback_data="new_anketa")],
    [InlineKeyboardButton("📋 Мои анкеты", callback_data="my_anketas")],
    [InlineKeyboardButton("💡 Помощь", callback_data="help")],
    [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
]
```

#### Callback Queries
```python
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "new_anketa":
        start_new_anketa(call.message)
    elif call.data == "my_anketas":
        show_user_anketas(call.message)
    # ...
```

### Deep Links
```
https://t.me/grantservice_bot?start=anketa_123
https://t.me/grantservice_bot?start=grant_456
https://t.me/grantservice_bot?start=ref_user789
```

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": [
            {
                "field": "project_name",
                "message": "Field is required"
            }
        ],
        "timestamp": "2025-01-29T17:00:00Z",
        "request_id": "req-123-456"
    }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Access denied |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Invalid input data |
| CONFLICT | 409 | Resource conflict |
| RATE_LIMIT | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

### Error Examples

#### 400 Bad Request
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {
                "field": "email",
                "message": "Invalid email format"
            }
        ]
    }
}
```

#### 401 Unauthorized
```json
{
    "error": {
        "code": "UNAUTHORIZED",
        "message": "Authentication required",
        "details": "Please provide a valid access token"
    }
}
```

#### 429 Too Many Requests
```json
{
    "error": {
        "code": "RATE_LIMIT",
        "message": "Rate limit exceeded",
        "details": {
            "limit": 100,
            "remaining": 0,
            "reset_at": "2025-01-29T18:00:00Z"
        }
    }
}
```

## Rate Limiting

### Limits
| Endpoint | Limit | Window |
|----------|-------|--------|
| Authentication | 10 requests | 5 minutes |
| User API | 100 requests | 1 minute |
| AI Agents | 20 requests | 1 minute |
| Document Upload | 10 files | 5 minutes |
| Admin API | 200 requests | 1 minute |

### Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

### Bypass Rate Limits (Admin)
```http
X-Admin-Override: true
Authorization: Bearer {admin_token}
```

## Pagination

### Request Parameters
```http
GET /api/resource?page=1&limit=20&sort=-created_at&filter=active
```

### Response Format
```json
{
    "items": [...],
    "pagination": {
        "total": 150,
        "page": 1,
        "pages": 8,
        "limit": 20,
        "has_next": true,
        "has_prev": false
    }
}
```

## Webhooks Configuration

### Register Webhook
```http
POST /api/webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
    "url": "https://example.com/webhook",
    "events": ["anketa.submitted", "grant.approved"],
    "secret": "webhook-secret-key"
}

Response 201 Created:
{
    "id": "webhook-123",
    "url": "https://example.com/webhook",
    "events": ["anketa.submitted", "grant.approved"],
    "created_at": "2025-01-29T18:00:00Z"
}
```

### Webhook Events
| Event | Description |
|-------|-------------|
| anketa.created | New anketa created |
| anketa.updated | Anketa updated |
| anketa.submitted | Anketa submitted |
| grant.generated | Grant application generated |
| grant.approved | Grant approved |
| user.registered | New user registered |

### Webhook Payload
```json
{
    "event": "anketa.submitted",
    "timestamp": "2025-01-29T18:00:00Z",
    "data": {
        "anketa_id": 123,
        "user_id": 456,
        "status": "submitted"
    },
    "signature": "sha256=..."
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-29 | Initial API documentation |

---

*This document is maintained by documentation-keeper agent*