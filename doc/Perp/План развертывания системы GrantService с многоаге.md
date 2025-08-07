<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# План развертывания системы GrantService с многоагентной архитектурой CrewAI

На основе анализа текущего технического задания, структуры проекта и лучших практик развертывания многоагентных систем, представляю комплексный план развертывания системы GrantService с миграцией на архитектуру CrewAI.

## Анализ текущего состояния

Текущая система GrantService представляет собой monolithic решение с следующими компонентами[^1][^2]:

- **Telegram Bot** (`main.py`) с n8n workflow
- **Веб-админ панель** (`main_admin.py`) на Streamlit
- **SQLite база данных** с таблицами: `interview_questions`, `users`, `sessions`
- **Системные сервисы**: `grantservice-bot.service`, `grantservice-web-admin.service`

Система проводит интервью из 7 базовых вопросов через Telegram и сохраняет данные в локальной БД[^2].

## Целевая архитектура

Новая архитектура предполагает миграцию на специализированных CrewAI агентов[^1]:

1. **Агент-интервьюер** (Telegram Bot) → собирает 30 вопросов → сохраняет в БД
2. **Агент-исследователь** (Perplexity API) → исследует контекст проекта
3. **Агент-писатель** (ГигаЧат API) → создает бета-версию заявки
4. **Агент-аналитик** (ГигаЧат API + БД) → анализирует качество заявки

![GrantService Multi-Agent System Deployment Architecture: Complete infrastructure stack with CrewAI agents](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/381637fdae2649b5f2cd7babf66257ff/081d6b59-d733-4d6b-96b2-20a9986d89ed/fbe68a2a.png)

GrantService Multi-Agent System Deployment Architecture: Complete infrastructure stack with CrewAI agents

## План развертывания по фазам

### Phase 1: Подготовка инфраструктуры (1-2 дня)

**Docker и контейнеризация**
Согласно лучшим практикам развертывания многоагентных систем, контейнеризация критически важна для обеспечения изоляции и масштабируемости[^3][^4].

```bash
# Установка основных компонентов
sudo apt update
sudo apt install docker.io docker-compose nginx

# Создание Docker network для микросервисов
docker network create grantservice_network
```

**Системные сервисы и мониторинг**
Конфигурация systemd сервисов для управления жизненным циклом приложений[^5][^6]:

```ini
# /etc/systemd/system/grantservice-crewai.service
[Unit]
Description=GrantService CrewAI Multi-Agent System
After=network.target docker.service

[Service]
Type=notify
ExecStart=/usr/local/bin/docker-compose -f /var/GrantService/docker-compose.yml up
ExecStop=/usr/local/bin/docker-compose -f /var/GrantService/docker-compose.yml down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Миграция базы данных**
Расширение текущей SQLite структуры[^2] для поддержки многоагентной архитектуры:

```sql
-- Новые таблицы для агентов
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    prompt_text TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE agent_tasks (
    id INTEGER PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE,
    agent_type VARCHAR(50),
    input_data TEXT,
    output_data TEXT,
    status VARCHAR(30) DEFAULT 'pending'
);
```


### Phase 2: Создание базовой архитектуры (2-3 дня)

**Новая структура проекта**
Создание модульной архитектуры согласно лучшим практикам микросервисов[^7][^8]:

```
GrantService/
├── agents/                    # CrewAI агенты
│   ├── interviewer_agent.py   # Telegram интервьюер
│   ├── researcher_agent.py    # Perplexity исследователь
│   ├── writer_agent.py        # ГигаЧат писатель
│   └── auditor_agent.py       # ГигаЧат аналитик
├── crew/                      # CrewAI оркестрация
│   ├── grant_crew.py          # Основная команда
│   └── tasks.py               # Задачи для агентов
├── tools/                     # Инструменты агентов
├── config/                    # Конфигурации и промпты
└── docker-compose.yml         # Многоконтейнерное развертывание
```

**Docker Compose конфигурация**
Использование мультиконтейнерного подхода для изоляции сервисов[^9][^10]:

```yaml
version: '3.8'
services:
  telegram-bot:
    build: ./agents
    environment:
      - AGENT_TYPE=interviewer
      - BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    depends_on:
      - database
    networks:
      - grantservice_network

  researcher-agent:
    build: ./agents
    environment:
      - AGENT_TYPE=researcher
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
    networks:
      - grantservice_network

  writer-agent:
    build: ./agents
    environment:
      - AGENT_TYPE=writer
      - GIGACHAT_API_KEY=${GIGACHAT_API_KEY}
    networks:
      - grantservice_network

  auditor-agent:
    build: ./agents
    environment:
      - AGENT_TYPE=auditor
    networks:
      - grantservice_network

  web-admin:
    build: ./web-admin
    ports:
      - "8501:8501"
    depends_on:
      - database
    networks:
      - grantservice_network

  database:
    image: alpine:latest
    volumes:
      - ./data:/data
    networks:
      - grantservice_network

networks:
  grantservice_network:
    driver: bridge
```


### Phase 3: Развертывание агентов CrewAI (3-4 дня)

**Реализация специализированных агентов**
Создание четырех основных агентов согласно лучшим практикам CrewAI[^11][^12]:

```python
# agents/interviewer_agent.py
from crewai import Agent
from tools.telegram_tool import TelegramTool
from tools.database_tool import DatabaseTool

interviewer_agent = Agent(
    role="Grant Application Interviewer",
    goal="Conduct comprehensive 30-question interview via Telegram bot",
    backstory="Expert interviewer specialized in grant applications with 10+ years experience",
    tools=[TelegramTool(), DatabaseTool()],
    verbose=True,
    memory=True
)
```

**CrewAI Workflow оркестрация**
Настройка последовательного выполнения задач агентами[^13]:

```python
# crew/grant_crew.py
from crewai import Crew, Process

grant_crew = Crew(
    agents=[interviewer_agent, researcher_agent, writer_agent, auditor_agent],
    tasks=[interview_task, research_task, writing_task, audit_task],
    process=Process.sequential,
    verbose=True,
    max_rpm=10
)
```


### Phase 4: Настройка интеграций (2-3 дня)

**API интеграции**
Согласно лучшим практикам многоагентных систем, внешние интеграции должны быть изолированы в отдельные инструменты[^3]:

- **Telegram Bot API** - сохранение текущего интерфейса пользователя
- **Perplexity API** - профессиональные исследования вместо веб-поиска
- **ГигаЧат API** - генерация и анализ документов

**Конфигурация безопасности**
Применение принципов безопасности для многоагентных систем[^14]:

```python
# config/api_config.py
import os
from cryptography.fernet import Fernet

class SecureAPIConfig:
    def __init__(self):
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        self.cipher = Fernet(self.encryption_key)
    
    def get_encrypted_token(self, service):
        encrypted_token = os.getenv(f'{service.upper()}_TOKEN_ENCRYPTED')
        return self.cipher.decrypt(encrypted_token.encode()).decode()
```


### Phase 5: Веб-админка и мониторинг (2-3 дня)

**Обновление Streamlit админки**
Расширение текущей веб-панели[^2] новыми разделами:

- **Управление промптами агентов** - редактор для каждого из 4 агентов
- **Методические материалы** - загрузка документов в базу знаний
- **Критерии аудита** - настройка параметров оценки
- **Мониторинг агентов** - статистика работы CrewAI

**Nginx конфигурация**
Настройка reverse proxy для множественных сервисов[^15][^16]:

```nginx
# /etc/nginx/sites-enabled/grantservice.conf
upstream telegram_bot {
    server 127.0.0.1:8000;
}

upstream web_admin {
    server 127.0.0.1:8501;
}

server {
    listen 443 ssl;
    server_name grantservice.yourdomain.com;
    
    location /admin/ {
        proxy_pass http://web_admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://telegram_bot/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Мониторинг и наблюдаемость**
Внедрение комплексного мониторинга согласно лучшим практикам[^3]:

```python
# tools/monitoring_tool.py
import logging
from systemd.journal import JournaldLogHandler

class AgentMonitor:
    def __init__(self, agent_name):
        self.logger = logging.getLogger(f'crewai.{agent_name}')
        journald_handler = JournaldLogHandler()
        self.logger.addHandler(journald_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_task_execution(self, task_id, status, duration):
        self.logger.info(f"Task {task_id}: {status} in {duration}ms")
```


### Phase 6: Тестирование и запуск (2-3 дня)

**Тестирование системы**
Комплексное тестирование многоагентной системы[^3]:

```python
# tests/test_agent_integration.py
import pytest
from crew.grant_crew import grant_crew

class TestAgentIntegration:
    def test_interview_to_research_pipeline(self):
        # Тест полного пайплайна от интервью до исследования
        result = grant_crew.kickoff({
            'topic': 'AI-powered education platform',
            'user_id': 12345
        })
        assert result.status == 'completed'
        
    def test_concurrent_user_sessions(self):
        # Тест обработки множественных пользователей
        pass
```

**Развертывание production**
Запуск системы с использованием лучших практик production развертывания[^4]:

```bash
# Финальный запуск системы
sudo systemctl enable grantservice-crewai
sudo systemctl start grantservice-crewai

# Мониторинг статуса
sudo systemctl status grantservice-crewai
sudo journalctl -u grantservice-crewai -f
```


## Ключевые технические решения

### Архитектурные паттерны

**Microservices Architecture**
Каждый агент развертывается как независимый микросервис, что обеспечивает изоляцию ошибок и независимое масштабирование[^7][^8].

**Event-Driven Communication**
Агенты взаимодействуют через события, что обеспечивает слабую связанность и высокую отзывчивость системы[^3].

**Circuit Breaker Pattern**
Защита от каскадных отказов при недоступности внешних API (Perplexity, ГигаЧат)[^4].

### Безопасность и соответствие требованиям

**Zero Trust Architecture**
Каждый запрос между агентами проходит аутентификацию и авторизацию[^14].

**API Security**

- JWT токены для внутренней аутентификации
- Rate limiting для предотвращения злоупотреблений
- Шифрование всех внешних коммуникаций

**Audit Logging**
Полное логирование всех действий агентов для соответствия требованиям compliance[^4].

## Управление конфигурацией

**Hot-reload промптов**
Система поддерживает обновление промптов агентов без перезапуска сервисов:

```python
# config/prompt_manager.py
class PromptManager:
    def __init__(self):
        self.prompts_cache = {}
        self.last_update = None
    
    def get_prompt(self, agent_type, version='latest'):
        # Автоматическое обновление из БД при изменениях
        if self.needs_update():
            self.reload_prompts()
        return self.prompts_cache.get(agent_type)
```

**Environment Variables Management**
Использование Docker secrets для безопасного управления API ключами[^9].

## Мониторинг и наблюдаемость

**Metrics Collection**

- Время выполнения задач каждым агентом
- Количество успешных/неуспешных обращений к внешним API
- Загрузка CPU/памяти для каждого контейнера

**Health Checks**
Автоматические проверки работоспособности каждого агента с автоматическим перезапуском при сбоях[^4].

**Distributed Tracing**
Отслеживание выполнения задач через всю цепочку агентов для диагностики проблем производительности.

## Масштабирование и производительность

**Horizontal Scaling**
Возможность запуска множественных экземпляров каждого агента при увеличении нагрузки[^3].

**Load Balancing**
Nginx распределяет нагрузку между экземплярами агентов.

**Resource Optimization**

- Использование Alpine Linux для минимизации размера контейнеров
- Оптимизация использования памяти через параметры JVM для ГигаЧат интеграции


## Оценка ресурсов и времени

**Команда разработки:**

- 2-3 Python разработчика (знание CrewAI, FastAPI, SQLite)
- 1 DevOps специалист (Docker, Nginx, systemd)
- 1 QA инженер для тестирования интеграций

**Временные рамки:**

- Общее время разработки: 12-18 дней
- MVP версия: 8-10 дней
- Production-ready версия: 15-20 дней

**Инфраструктурные требования:**

- Сервер: 4+ CPU cores, 8GB+ RAM, 50GB+ SSD
- Резервное копирование БД каждые 6 часов
- SSL сертификаты для HTTPS


## Риски и митигация

**Технические риски:**

- Недоступность внешних API (Perplexity, ГигаЧат) - реализация fallback механизмов
- Превышение лимитов API - реализация rate limiting и очередей
- Конкурентный доступ к БД - использование connection pooling

**Операционные риски:**

- Потеря данных пользователей - регулярное резервное копирование
- Проблемы производительности - мониторинг и автоматическое масштабирование
- Нарушение безопасности - regular security audits и обновления

Данный план развертывания обеспечивает плавную миграцию от текущей monolithic архитектуры к современной многоагентной системе с сохранением всей функциональности и значительным расширением возможностей системы GrantService.

<div style="text-align: center">⁂</div>

[^1]: Sozdanie-masshtabiruemogo-proekta-mnogoagentnykh-AI.md

[^2]: smotri-nam-nado-agentov-kak-na-izobrazhenii-vo-vlozh.md

[^3]: database_structure.md

[^4]: README-2.md

[^5]: https://www.youtube.com/watch?v=3EqSV-CYDZA

[^6]: https://www.aalpha.net/blog/how-to-build-multi-agent-ai-system/

[^7]: https://www.docker.com/blog/containerized-python-development-part-2/

[^8]: https://help.crewai.com/deploying-your-crew-to-crewai

[^9]: https://docs.swarms.world/en/latest/swarms_cloud/production_deployment/

[^10]: https://stackoverflow.com/questions/70594413/how-to-create-a-container-for-each-microservice-in-the-same-folder

[^11]: https://www.wednesday.is/writing-articles/crewai-deployment-guide-production-implementation

[^12]: https://bestaiagents.ai/blog/building-multi-agent-workflows-a-comprehensive-guide

[^13]: https://github.com/cloudacademy/python-flask-microservices

[^14]: https://docs.crewai.com/en/enterprise/guides/deploy-crew

[^15]: https://www.anthropic.com/engineering/built-multi-agent-research-system

[^16]: https://earthly.dev/blog/python-microservices-rabbitmq-docker/

[^17]: https://docs.crewai.com/quickstart

[^18]: https://botpress.com/blog/multi-agent-systems

[^19]: https://kinsta.com/blog/python-microservices/

[^20]: https://www.lindy.ai/blog/crew-ai-pricing

[^21]: https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/

[^22]: https://www.youtube.com/watch?v=0LPRomOq_i4

[^23]: https://docs.crewai.com/en/enterprise/introduction

[^24]: https://dev.to/aws-builders/three-ways-to-build-multi-agent-systems-on-aws-3h8p

[^25]: https://www.cherryservers.com/blog/docker-compose-multi-container-applications

[^26]: https://github.com/torfsen/python-systemd-tutorial

[^27]: https://timothy-quinn.com/using-nginx-as-a-reverse-proxy-for-multiple-sites/

[^28]: https://dev.to/mukhilpadmanabhan/a-simple-guide-to-docker-compose-multi-container-applications-5e0g

[^29]: https://pypi.org/project/systemd-service/

[^30]: https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/

[^31]: https://overcast.blog/multi-environment-deployments-with-docker-a-guide-890e193191b6

[^32]: https://docs.rockylinux.org/gemstones/systemd_service_for_python_script/

[^33]: https://stackoverflow.com/questions/78154473/multi-layer-reverse-proxy-nginx

[^34]: https://stackoverflow.com/questions/49191304/how-to-deal-with-multiple-services-inside-a-docker-compose-yml

[^35]: https://discuss.python.org/t/python-script-as-a-systemd-service/16518

[^36]: https://www.reddit.com/r/selfhosted/comments/unfjnc/how_to_run_multiple_services_on_a_dedicated/

[^37]: https://forums.docker.com/t/docker-compose-push-multiple-services-containers-to-docker-hub/121826

[^38]: https://stackoverflow.com/questions/33646374/starting-a-systemd-service-via-python

[^39]: https://www.baeldung.com/linux/nginx-multiple-proxy-endpoints

[^40]: https://www.reddit.com/r/docker/comments/qqq70h/how_to_start_multiple_services_from_a/

[^41]: https://www.codementor.io/@ufuksfk/how-to-run-a-python-script-in-linux-with-systemd-1nh2x3hi0e

[^42]: https://habr.com/ru/articles/765536/

[^43]: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/multi-container-applications-docker-compose

[^44]: https://github.com/systemd/python-systemd

[^45]: https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/381637fdae2649b5f2cd7babf66257ff/4afc637a-559c-457b-af2e-65c0b6efcf0d/ff0394ba.csv

