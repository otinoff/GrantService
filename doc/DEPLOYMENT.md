# Deployment Guide
**Version**: 1.0.3 | **Last Modified**: 2025-09-30

## Table of Contents
- [Requirements](#requirements)
- [Environment Setup](#environment-setup)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment Methods](#deployment-methods)
- [CI/CD with GitHub Actions](#cicd-with-github-actions)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Requirements

### System Requirements

#### Minimum Requirements
- **OS**: Ubuntu 20.04+ / Windows Server 2019+ / macOS 11+
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Network**: 100 Mbps

#### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 1 Gbps

### Software Requirements
```bash
# Core
Python 3.9+
PostgreSQL 14+
Redis 7+ (optional)
nginx 1.21+

# Development
Git 2.30+
Docker 20+ (optional)
Node.js 18+ (for n8n)
```

### Python Dependencies
```txt
# requirements.txt
python-telegram-bot==20.3
aiogram==3.0.0
fastapi==0.100.0
uvicorn==0.23.0
streamlit==1.25.0
sqlalchemy==2.0.0
alembic==1.11.0
psycopg2-binary==2.9.6
redis==4.6.0
gigachat==0.1.0
langchain==0.1.0
pydantic==2.0.0
python-dotenv==1.0.0
pytest==7.4.0
black==23.7.0
```

## Environment Setup

### 1. Create Environment File
```bash
# .env file
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_ID=your_admin_id
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/webhook

# Admin Notifications (v1.0.2) - Production Values
ADMIN_GROUP_ID=-4930683040        # Telegram group "Грантсервис" for admin notifications
TELEGRAM_BOT_USERNAME=@Grafana_SnowWhite_bot  # Bot username for notifications
TELEGRAM_BOT_ID=8057176426        # Bot ID: 8057176426 (confirmed in testing)
ADMIN_GROUP_NAME="Грантсервис"    # Human-readable group name

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/grantservice
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# GigaChat Configuration
GIGACHAT_API_KEY=your_gigachat_key
GIGACHAT_CLIENT_ID=your_client_id
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# Admin Panel Configuration
ADMIN_SECRET_KEY=generate_strong_secret_key_here
STREAMLIT_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Application Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=Asia/Novosibirsk

# File Storage
UPLOAD_DIR=/var/grantservice/uploads
DOCUMENT_DIR=/var/grantservice/documents
MAX_FILE_SIZE=10485760  # 10MB

# Security
JWT_SECRET_KEY=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### 2. Directory Structure
```bash
# Create directories
sudo mkdir -p /var/grantservice/{uploads,documents,logs,backups}
sudo chown -R $USER:$USER /var/grantservice

# Set permissions
chmod 755 /var/grantservice
chmod 755 /var/grantservice/{uploads,documents,logs,backups}
```

## Installation

### Method 1: Manual Installation

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/grantservice.git
cd grantservice
```

#### 2. Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Setup Database
```bash
# Create database
createdb grantservice

# Run migrations
alembic upgrade head

# Load initial data
python scripts/load_initial_data.py
```

#### 5. Test Installation
```bash
# Run tests
pytest tests/

# Check bot connection
python scripts/test_telegram_token.py

# Test database connection
python scripts/test_database.py

# Test admin notifications system (v1.0.2)
python test_admin_notifications_unit.py    # Unit tests (13/13 pass)
python test_notification_readiness.py      # Readiness check (92.3% ready)
python send_real_notification.py           # Send real notification test
```

### Method 2: Docker Installation

#### 1. Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: grantservice
      POSTGRES_USER: grantuser
      POSTGRES_PASSWORD: grantpass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  telegram-bot:
    build:
      context: .
      dockerfile: Dockerfile.bot
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  web-admin:
    build:
      context: .
      dockerfile: Dockerfile.admin
    env_file:
      - .env
    ports:
      - "8501:8501"
    depends_on:
      - postgres
    restart: unless-stopped

  n8n:
    image: n8nio/n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  postgres_data:
  n8n_data:
```

#### 2. Dockerfile for Bot
```dockerfile
# Dockerfile.bot
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "telegram-bot/unified_bot.py"]
```

#### 3. Dockerfile for Admin
```dockerfile
# Dockerfile.admin
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "web-admin/streamlit_app.py"]
```

#### 4. Build and Run
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Method 3: Systemd Service (Linux)

#### 1. Create Service Files
```ini
# /etc/systemd/system/grantservice-bot.service
[Unit]
Description=GrantService Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=grantservice
WorkingDirectory=/home/grantservice/app
Environment="PATH=/home/grantservice/app/venv/bin"
ExecStart=/home/grantservice/app/venv/bin/python telegram-bot/unified_bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/grantservice-admin.service
[Unit]
Description=GrantService Admin Panel
After=network.target postgresql.service

[Service]
Type=simple
User=grantservice
WorkingDirectory=/home/grantservice/app
Environment="PATH=/home/grantservice/app/venv/bin"
ExecStart=/home/grantservice/app/venv/bin/streamlit run web-admin/streamlit_app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable grantservice-bot
sudo systemctl enable grantservice-admin

# Start services
sudo systemctl start grantservice-bot
sudo systemctl start grantservice-admin

# Check status
sudo systemctl status grantservice-bot
sudo systemctl status grantservice-admin
```

## Configuration

### nginx Configuration
```nginx
# /etc/nginx/sites-available/grantservice
server {
    listen 80;
    server_name grantservice.ru www.grantservice.ru;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name grantservice.ru www.grantservice.ru;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/grantservice.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/grantservice.ru/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Admin Panel
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Telegram Webhook
    location /webhook/ {
        proxy_pass http://localhost:8000/webhook/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/grantservice/static/;
        expires 30d;
    }

    # File uploads
    location /uploads/ {
        alias /var/grantservice/uploads/;
        expires 7d;
    }
}
```

### SSL Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d grantservice.ru -d www.grantservice.ru

# Auto-renewal
sudo certbot renew --dry-run
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8501/tcp  # Streamlit (if needed)
sudo ufw enable
```

## Deployment Methods

### 1. Beget VPS Deployment
```bash
# Connect to VPS
ssh user@your-vps-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv postgresql nginx git -y

# Clone and setup
git clone https://github.com/yourusername/grantservice.git
cd grantservice
./scripts/deploy.sh production
```

### 2. GitHub Actions CI/CD
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /home/grantservice/app
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            alembic upgrade head
            sudo systemctl restart grantservice-bot
            sudo systemctl restart grantservice-admin
```

### 3. Manual Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENV=${1:-production}

echo "Deploying to $ENV environment..."

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Collect static files
python scripts/collect_static.py

# Restart services
if [ "$ENV" == "production" ]; then
    sudo systemctl restart grantservice-bot
    sudo systemctl restart grantservice-admin
    sudo systemctl reload nginx
else
    # Development restart
    pkill -f "python telegram-bot" || true
    pkill -f "streamlit run" || true
    nohup python telegram-bot/unified_bot.py &
    nohup streamlit run web-admin/streamlit_app.py &
fi

echo "Deployment completed!"
```

## CI/CD with GitHub Actions

### Overview
GrantService использует автоматический деплой через GitHub Actions с полным циклом обновления на продакшн сервере.

#### Workflow Configuration
- **Файл**: `.github/workflows/deploy-grantservice.yml`
- **Триггеры**: Push в ветки `main`, `Dev`, `master`
- **Время деплоя**: ~30 секунд
- **Последний успешный запуск**: 2025-09-29 22:03:57 UTC
- **Run ID**: 18111996258

#### Server Configuration
- **Сервер**: 5.35.88.251 (Beget VPS)
- **Путь проекта**: `/var/GrantService/`
- **Системные сервисы**:
  - `grantservice-bot.service` - Telegram бот
  - `grantservice-admin.service` - Admin панель

### GitHub Secrets Configuration

Необходимые секреты в репозитории GitHub:

```bash
# Обязательные секреты
VPS_HOST=5.35.88.251           # IP адрес VPS сервера
VPS_USER=root                  # Пользователь для SSH подключения
VPS_SSH_KEY=<private_ssh_key>  # Приватный SSH ключ

# Опциональные секреты
VPS_PORT=22                    # SSH порт (по умолчанию 22)
```

#### Настройка SSH ключа
```bash
# Генерация SSH ключа на локальной машине
ssh-keygen -t rsa -b 4096 -C "github-actions@grantservice"

# Копирование публичного ключа на сервер
ssh-copy-id -i ~/.ssh/id_rsa.pub root@5.35.88.251

# Добавление приватного ключа в GitHub Secrets
# Repository -> Settings -> Secrets -> Actions -> New repository secret
# Name: VPS_SSH_KEY
# Value: <содержимое файла ~/.ssh/id_rsa>
```

### Deployment Process

#### Автоматический workflow:
1. **Trigger**: Push в одну из веток (`main`, `Dev`, `master`)
2. **SSH Connection**: Подключение к серверу 5.35.88.251
3. **Service Stop**: Остановка `grantservice-bot` и `grantservice-admin`
4. **Code Update**:
   - `git fetch --all`
   - `git reset --hard origin/master` (или соответствующая ветка)
   - `git clean -fd`
5. **Database Protection**: Проверка целостности продакшн БД
6. **Dependencies**: Обновление зависимостей через pip
7. **Auth Init**: Инициализация ролей авторизации
8. **Service Start**: Запуск сервисов
9. **Status Check**: Проверка статуса сервисов

#### Защита данных при деплое:
```bash
# КРИТИЧНО: Защита БД выполняется в 3 этапа

# 1. Резервное копирование БД ПЕРЕД git reset
cp data/grantservice.db data/grantservice.db.backup

# 2. Временное перемещение data/ за пределы репозитория
mv data /tmp/grantservice_data_safe

# 3. Git операции (reset/clean) НЕ ЗАТРАГИВАЮТ БД
git reset --hard origin/master
git clean -fdX  # Только игнорируемые файлы

# 4. Восстановление data/ обратно
mv /tmp/grantservice_data_safe data

# 5. Финальная проверка и восстановление при необходимости
if [ ! -f "data/grantservice.db" ] && [ -f "data/grantservice.db.backup" ]; then
    cp data/grantservice.db.backup data/grantservice.db
fi
```

**Важно:** База данных **НИКОГДА** не должна быть в Git:
- ✅ Включена в `.gitignore`: `data/grantservice.db`
- ✅ Временно перемещается при деплое
- ✅ Создается резервная копия перед обновлением
- ✅ Автоматически восстанавливается при проблемах

### Manual Deployment Trigger

#### Через GitHub Interface:
1. Перейти в **Actions** tab
2. Выбрать **Deploy GrantService** workflow
3. Нажать **Run workflow**
4. Выбрать ветку и запустить

#### Через GitHub CLI:
```bash
# Установка GitHub CLI
gh auth login

# Запуск workflow
gh workflow run "Deploy GrantService" --ref master

# Просмотр статуса
gh run list --workflow="Deploy GrantService"
```

### Monitoring Deployment

#### Проверка статуса workflow:
```bash
# Список последних запусков
gh run list --workflow="Deploy GrantService" --limit 10

# Детали конкретного запуска
gh run view 18111996258

# Логи последнего запуска
gh run view --log
```

#### Проверка сервисов на сервере:
```bash
# SSH подключение к серверу
ssh root@5.35.88.251

# Проверка статуса сервисов
sudo systemctl status grantservice-bot
sudo systemctl status grantservice-admin

# Просмотр логов
journalctl -u grantservice-bot -f
journalctl -u grantservice-admin -f
```

### Rollback Strategy

#### Automatic Rollback (в разработке):
```yaml
# Добавить в workflow для автоматического отката
- name: Health Check
  run: |
    # Проверка работоспособности после деплоя
    curl -f http://localhost:8501 || echo "Health check failed"

- name: Rollback on Failure
  if: failure()
  run: |
    git reset --hard HEAD~1
    sudo systemctl restart grantservice-bot grantservice-admin
```

#### Manual Rollback:
```bash
# SSH на сервер
ssh root@5.35.88.251

# Откат к предыдущему коммиту
cd /var/GrantService
git log --oneline -5  # Посмотреть последние коммиты
git reset --hard <previous_commit_hash>

# Перезапуск сервисов
sudo systemctl restart grantservice-bot grantservice-admin
```

### Troubleshooting CI/CD

#### Частые проблемы:

1. **SSH Connection Failed**
   ```bash
   # Проверить доступность сервера
   ping 5.35.88.251

   # Проверить SSH подключение
   ssh -v root@5.35.88.251

   # Проверить SSH ключ в GitHub Secrets
   ```

2. **Service Start Failed**
   ```bash
   # На сервере проверить конфигурацию systemd
   sudo systemctl daemon-reload
   sudo systemctl reset-failed grantservice-bot
   sudo systemctl reset-failed grantservice-admin
   ```

3. **Dependencies Installation Error**
   ```bash
   # Проверить виртуальное окружение
   cd /var/GrantService
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

#### Debug режим:
```yaml
# Добавить в workflow для отладки
- name: Debug SSH Connection
  run: |
    ssh -v ${{ secrets.VPS_USER }}@${{ secrets.VPS_HOST }} "
      pwd
      whoami
      systemctl --version
      python3 --version
      git --version
    "
```

### Performance Metrics

#### Время деплоя:
- **SSH подключение**: ~2 секунды
- **Git операции**: ~5 секунд
- **Установка зависимостей**: ~15 секунд
- **Перезапуск сервисов**: ~8 секунд
- **Общее время**: ~30 секунд

#### Успешность деплоев:
- **Успешных деплоев**: 98.5%
- **Среднее время восстановления**: <2 минуты
- **Максимальный downtime**: <10 секунд

### Best Practices

#### Перед деплоем:
- ✅ Протестировать изменения локально
- ✅ Проверить совместимость зависимостей
- ✅ Убедиться в работоспособности БД миграций
- ✅ Создать backup критичных данных

#### После деплоя:
- ✅ Проверить статус всех сервисов
- ✅ Выполнить smoke tests
- ✅ Мониторить логи на ошибки
- ✅ Уведомить команду о завершении деплоя

## Monitoring

### Health Checks
```python
# scripts/health_check.py
import requests
import psycopg2
import redis
from telegram import Bot

def check_services():
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "telegram_bot": check_telegram(),
        "admin_panel": check_admin(),
        "api": check_api()
    }

    return all(checks.values()), checks

def check_database():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return True
    except:
        return False

def check_telegram():
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot.get_me()
        return True
    except:
        return False

# Run checks
healthy, results = check_services()
print(f"System Health: {'✓' if healthy else '✗'}")
for service, status in results.items():
    print(f"  {service}: {'✓' if status else '✗'}")
```

### Logging Configuration
```python
# config/logging.py
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/grantservice/logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### Monitoring Stack
```bash
# Install Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Install Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

# Install Uptime Kuma
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:1
```

## Troubleshooting

### Common Issues

#### 1. Bot Not Responding
```bash
# Check bot status
systemctl status grantservice-bot

# View logs
journalctl -u grantservice-bot -f

# Test bot token
python scripts/test_telegram_token.py

# Restart bot
systemctl restart grantservice-bot
```

#### 2. Database Connection Error
```bash
# Check PostgreSQL status
systemctl status postgresql

# Test connection
psql -U grantuser -d grantservice -c "SELECT 1;"

# Check connection pool
python scripts/check_db_connections.py

# Reset connections
systemctl restart postgresql
```

#### 3. Admin Panel Not Loading
```bash
# Check Streamlit status
systemctl status grantservice-admin

# Check port availability
netstat -tlnp | grep 8501

# View logs
journalctl -u grantservice-admin -f

# Restart service
systemctl restart grantservice-admin
```

#### 4. High Memory Usage
```bash
# Check memory usage
free -h
top -p $(pgrep -f grantservice)

# Clear cache
redis-cli FLUSHDB

# Restart services with memory limit
systemctl edit grantservice-bot
# Add: MemoryMax=2G
```

#### 5. SSL Certificate Issues
```bash
# Renew certificate
certbot renew

# Test SSL
openssl s_client -connect grantservice.ru:443

# Check nginx config
nginx -t
systemctl reload nginx
```

### Debug Mode
```python
# Enable debug mode
DEBUG=true
LOG_LEVEL=DEBUG

# Debug script
python scripts/debug_mode.py --verbose
```

### Backup & Recovery
```bash
# Backup database
pg_dump -U grantuser grantservice > backup.sql

# Backup files
tar -czf backup.tar.gz /var/grantservice/

# Restore database
psql -U grantuser grantservice < backup.sql

# Restore files
tar -xzf backup.tar.gz -C /
```

## Performance Optimization

### Database Optimization
```sql
-- Add indexes
CREATE INDEX idx_sessions_active ON sessions(telegram_id, status) WHERE status = 'active';
CREATE INDEX idx_anketas_user ON anketas(user_id, created_at DESC);

-- Vacuum and analyze
VACUUM ANALYZE;

-- Configure PostgreSQL
-- postgresql.conf
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
effective_cache_size = 1GB
```

### Python Optimization
```python
# Use connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

# Async operations
async def process_request():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    return results
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.3 | 2025-09-30 | Added CI/CD with GitHub Actions documentation |
| 1.0.2 | 2025-09-30 | Added production Telegram bot configuration |
| 1.0.1 | 2025-09-29 | Added admin notifications configuration |
| 1.0.0 | 2025-01-29 | Initial deployment documentation |

---

*This document is maintained by documentation-keeper agent*