# Установка Qdrant на Production Server (5.35.88.251)

## Цель
Развернуть векторную БД Qdrant для работы Expert Agent с базой знаний ФПГ.

## Архитектура
```
Локальная разработка (Windows) → 5.35.88.251:6333 → Qdrant
Продакшен бот (Linux)          → localhost:6333   → Qdrant
```

## Шаг 1: Установка Qdrant через Docker

```bash
# SSH на сервер
ssh root@5.35.88.251

# Создать директорию для данных
mkdir -p /var/qdrant_storage
chmod 777 /var/qdrant_storage

# Запустить Qdrant контейнер
docker run -d \
  --name qdrant \
  --restart always \
  -p 6333:6333 \
  -p 6334:6334 \
  -v /var/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# Проверить что контейнер запущен
docker ps | grep qdrant

# Проверить API
curl http://localhost:6333/
```

**Ожидаемый результат:**
```json
{"title":"qdrant - vector search engine","version":"1.x.x"}
```

## Шаг 2: Открыть порт для внешних подключений

```bash
# Открыть порт в UFW
ufw allow 6333/tcp
ufw status

# Проверить что порт слушается снаружи
ss -tlnp | grep 6333
```

## Шаг 3: Загрузить базу знаний ФПГ

### Вариант A: С локальной машины (Windows)

```bash
cd C:\SnowWhiteAI\GrantService
python expert_agent/load_fpg_knowledge.py
```

Скрипт:
- Подключится к `5.35.88.251:6333`
- Создаст коллекцию `knowledge_sections`
- Загрузит данные из `fpg_docs_2025/UNIFIED_KNOWLEDGE_BASE.md`
- Создаст embeddings (384-мерные векторы)

### Вариант B: На сервере

```bash
# На сервере 5.35.88.251
cd /var/GrantService
python3 expert_agent/load_fpg_knowledge.py
```

## Шаг 4: Проверка данных

```bash
# Список коллекций
curl http://localhost:6333/collections | python3 -m json.tool

# Информация о knowledge_sections
curl http://localhost:6333/collections/knowledge_sections | python3 -m json.tool

# Должно быть:
# - points_count: ~50+ (количество секций из UNIFIED_KNOWLEDGE_BASE.md)
# - vectors_count: то же число
# - status: "green"
```

## Шаг 5: Тест семантического поиска

```python
# На локальной машине
from expert_agent.expert_agent import ExpertAgent

agent = ExpertAgent(
    postgres_host="localhost",
    qdrant_host="5.35.88.251",  # Продакшен
    qdrant_port=6333
)

# Поиск
results = agent.search_knowledge(
    query="Какие требования к бюджету проекта?",
    fund_name="fpg",
    limit=3
)

for r in results:
    print(f"Score: {r['score']:.3f}")
    print(f"Section: {r['section_name']}")
    print(f"Content: {r['content'][:200]}...")
    print("-" * 80)
```

## Шаг 6: Интеграция с Telegram ботом

Обновить конфигурацию в `telegram-bot/main.py`:

```python
# Определить окружение
import platform
IS_PRODUCTION = platform.system() == "Linux"

# Qdrant конфигурация
QDRANT_HOST = "localhost" if IS_PRODUCTION else "5.35.88.251"
QDRANT_PORT = 6333

# Инициализация Expert Agent
from expert_agent.expert_agent import ExpertAgent
self.expert_agent = ExpertAgent(
    postgres_host="localhost",
    qdrant_host=QDRANT_HOST,
    qdrant_port=QDRANT_PORT
)
```

## Безопасность

### ⚠️ Важно:
Qdrant по умолчанию **БЕЗ** аутентификации!

### Опции защиты:

**1. API Key (рекомендуется)**
```yaml
# В docker-compose.yml или env переменные
service:
  api:
    api_key: "ваш-секретный-ключ-здесь"
```

Использование:
```python
from qdrant_client import QdrantClient
client = QdrantClient(
    host="5.35.88.251",
    port=6333,
    api_key="ваш-секретный-ключ-здесь"
)
```

**2. Firewall (временное решение)**
```bash
# Разрешить только с локальной машины разработки
ufw allow from ВАШ_IP to any port 6333

# Или ограничить доступ через iptables
```

**3. VPN / SSH туннель**
```bash
# С локальной машины
ssh -L 6333:localhost:6333 root@5.35.88.251

# Подключаться к localhost:6333 (будет форвардить на сервер)
```

## Мониторинг

```bash
# Логи Qdrant
docker logs qdrant -f

# Использование диска
du -sh /var/qdrant_storage/

# Проверка health
curl http://localhost:6333/healthz
```

## Бекап

```bash
# Создать snapshot
curl -X POST http://localhost:6333/collections/knowledge_sections/snapshots

# Скачать snapshot
curl http://localhost:6333/collections/knowledge_sections/snapshots/SNAPSHOT_NAME \
  -o /backup/knowledge_sections_$(date +%Y%m%d).snapshot
```

## Troubleshooting

### Проблема: "Connection refused"
```bash
# Проверить что контейнер запущен
docker ps | grep qdrant

# Перезапустить контейнер
docker restart qdrant

# Проверить логи
docker logs qdrant --tail 50
```

### Проблема: "Permission denied"
```bash
# Права на директорию данных
sudo chown -R 1000:1000 /var/qdrant_storage
```

### Проблема: Порт закрыт
```bash
# Проверить firewall
ufw status
ufw allow 6333/tcp

# Проверить что Qdrant слушает 0.0.0.0 (а не только 127.0.0.1)
netstat -tlnp | grep 6333
```

## Полезные ссылки

- Qdrant Docs: https://qdrant.tech/documentation/
- Docker Hub: https://hub.docker.com/r/qdrant/qdrant
- API Reference: https://qdrant.tech/documentation/interfaces/

---

**Версия:** 1.0
**Дата:** 2025-10-20
**Автор:** Grant Service Team
