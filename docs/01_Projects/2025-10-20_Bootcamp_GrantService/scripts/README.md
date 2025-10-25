# 🔍 Sber500 Bootcamp Knowledge Base

**Назначение:** Личная база знаний о буткэмпе для быстрого поиска через semantic search

**НЕ для агентов** - для внутреннего использования!

---

## 📦 Что внутри:

### Коллекция в Qdrant: `sber500_bootcamp`

**Содержит:**
- ✉️ Информация из писем
- 🌐 Структура портала
- 📚 Описания воркшопов
- 🎯 Задачи от партнёра
- 📊 Критерии оценки
- 🚀 План GrantService для буткэмпа

**Всего документов:** 8 (будет пополняться)

---

## 🚀 Quick Start

### 1. Создать коллекцию
```bash
cd C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\scripts

python create_bootcamp_collection.py
```

**Output:**
```
🔌 Connecting to Qdrant (5.35.88.251:6333)...
📦 Creating collection 'sber500_bootcamp'...
✅ Collection 'sber500_bootcamp' created successfully!
```

---

### 2. Добавить документы
```bash
python add_bootcamp_docs.py
```

**Output:**
```
📝 Adding 8 documents...

1. 🔥 Письмо: Доступ к платформе Sber500 x GigaChat Bootcamp
   Source: email | Category: access

2. 🔥 Задачи от партнёра: Критерии оценки через неделю
   Source: partner | Category: requirements
   ⏰ Deadline: 2025-10-30

...

✅ Total documents added: 8
📊 Collection 'sber500_bootcamp' now has 8 documents
```

---

### 3. Искать информацию

#### Вариант А: Command line
```bash
python search_bootcamp.py "Критерии оценки"
python search_bootcamp.py "Воркшопы про метрики"
python search_bootcamp.py "Как сдать бизнес-кейс"
```

#### Вариант Б: Interactive mode (рекомендуется!)
```bash
python search_bootcamp.py
```

**Interactive commands:**
```
🔍 Search: критерии оценки      # Поиск
🔍 Search: full                 # Toggle full text
🔍 Search: limit:5              # Изменить количество результатов
🔍 Search: exit                 # Выход
```

---

## 📋 Примеры поисков:

### Пример 1: Критерии оценки
```bash
python search_bootcamp.py "Критерии оценки буткэмпа"
```

**Result:**
```
1. [0.874] 🔥 Задачи от партнёра: Критерии оценки через неделю
   Source: partner | Category: requirements
   Deadline: 2025-10-30

   Критерий оценки (через неделю):
   - Количество использованных токенов GigaChat
   - Для каких целей используются токены
   - Качество использования и результаты
```

---

### Пример 2: Воркшопы
```bash
python search_bootcamp.py "воркшопы про метрики AI продуктов"
```

**Result:**
```
1. [0.891] ⚡ Бизнес-воркшопы: 9 практических сессий
   Source: portal | Category: workshops

   3.7 Воркшоп № 6: Метрики AI-продуктов
   Ключевые метрики для оценки успеха AI-функций.
   - Технические метрики (latency, quality, cost)
   - Бизнес-метрики (conversion, retention, revenue)
```

---

### Пример 3: Как сдать кейс
```bash
python search_bootcamp.py "как сдать бизнес кейс с gigachat"
```

**Result:**
```
1. [0.912] 🔥 О программе и требования к бизнес-кейсу
   Source: portal | Category: requirements

   1.2 Как сдать свой бизнес-кейс с GigaChat?
   Инструкция по подготовке и сдаче бизнес-кейса...
```

---

## 📊 Структура документов в коллекции:

### 1. Письмо - Доступ к платформе
- **Source:** email
- **Category:** access
- **Importance:** 🔥 critical
- **Content:** Логин, пароль, ссылки

### 2. Задачи от партнёра
- **Source:** partner
- **Category:** requirements
- **Importance:** 🔥 critical
- **Deadline:** 2025-10-30
- **Content:** Что нужно сделать за неделю

### 3. Структура портала
- **Source:** portal
- **Category:** structure
- **Importance:** ⚡ high
- **Content:** Разделы 1-4, воркшопы, live sessions

### 4. О программе
- **Source:** portal
- **Category:** requirements
- **Importance:** 🔥 critical
- **Content:** Требования к бизнес-кейсу

### 5. Курсы GigaChat
- **Source:** portal
- **Category:** education
- **Importance:** ⚡ high
- **Content:** API, документация, best practices

### 6. Воркшопы (9 штук)
- **Source:** portal
- **Category:** workshops
- **Importance:** ⚡ high
- **Content:** Jobs-To-Be-Done, Value Proposition, Metrics, Pricing, etc.

### 7. Live Sessions
- **Source:** portal
- **Category:** events
- **Importance:** 📌 medium
- **Content:** Q&A с экспертами, нетворкинг

### 8. GrantService план
- **Source:** internal
- **Category:** strategy
- **Importance:** 🔥 critical
- **Content:** Как использовать GigaChat, ожидаемые метрики

---

## 🎯 Use Cases:

### Use Case 1: Быстро найти дедлайн
```bash
python search_bootcamp.py "deadline"
# → Найдёт: 27 сентября, оценка через неделю
```

### Use Case 2: Вспомнить про воркшоп
```bash
python search_bootcamp.py "growth hacking"
# → Найдёт: Воркшоп № 5
```

### Use Case 3: Критерии оценки
```bash
python search_bootcamp.py "критерии оценки токены"
# → Найдёт: задачи от партнёра
```

### Use Case 4: Техническая документация
```bash
python search_bootcamp.py "API GigaChat"
# → Найдёт: Раздел 2.3
```

---

## 📂 Добавление новых документов:

### Вариант А: Редактировать скрипт
1. Открыть `add_bootcamp_docs.py`
2. Добавить новый документ в список `documents`
3. Запустить скрипт

**Пример:**
```python
{
    "text": """
    Новая информация с портала...
    """,
    "title": "Название документа",
    "source": "portal",  # или "email", "telegram", "partner"
    "category": "...",
    "section": "...",
    "date_added": "2025-10-23",
    "importance": "high"  # critical, high, medium, low
}
```

### Вариант Б: Создать отдельный скрипт
```python
# add_new_doc.py
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import uuid

client = QdrantClient(host="5.35.88.251", port=6333)
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

doc = {
    "text": "Новая информация...",
    "title": "Заголовок",
    # ... остальные поля
}

embedding = model.encode(doc["text"]).tolist()

client.upsert(
    collection_name="sber500_bootcamp",
    points=[{"id": str(uuid.uuid4()), "vector": embedding, "payload": doc}]
)
```

---

## 🔧 Полезные команды:

### Проверить количество документов:
```python
from qdrant_client import QdrantClient

client = QdrantClient(host="5.35.88.251", port=6333)
info = client.get_collection("sber500_bootcamp")
print(f"Documents: {info.points_count}")
```

### Удалить коллекцию (если нужно пересоздать):
```python
client.delete_collection("sber500_bootcamp")
```

### Экспортировать все документы:
```python
# TODO: Создать скрипт export_bootcamp_docs.py
```

---

## 💡 Tips:

### 1. Semantic search работает на русском и английском
```bash
# Оба запроса найдут то же самое:
python search_bootcamp.py "metrics"
python search_bootcamp.py "метрики"
```

### 2. Можно искать по смыслу, не только по словам
```bash
# Найдёт информацию о монетизации:
python search_bootcamp.py "как зарабатывать на AI"
```

### 3. Interactive mode удобнее для исследования
```bash
python search_bootcamp.py
# Потом можно делать много запросов подряд
```

### 4. Full text для детального чтения
```bash
python search_bootcamp.py
🔍 Search: full              # Включить полный текст
🔍 Search: ваш запрос       # Увидишь всё содержимое
```

---

## 📞 Quick Reference:

**Создать коллекцию:**
```bash
python create_bootcamp_collection.py
```

**Загрузить документы:**
```bash
python add_bootcamp_docs.py
```

**Искать (interactive):**
```bash
python search_bootcamp.py
```

**Искать (command line):**
```bash
python search_bootcamp.py "ваш запрос"
```

---

## 🎯 Следующие шаги:

1. ✅ Создать коллекцию
2. ✅ Загрузить начальные документы (8 штук)
3. ⏳ Добавить информацию с портала (когда получим доступ)
4. ⏳ Добавить данные о победителях прошлых лет
5. ⏳ Пополнять по мере поступления новой информации

---

**Создано:** 2025-10-23
**Автор:** Claude Code AI Assistant
**Версия:** 1.0
**Purpose:** Personal knowledge base (NOT for agents!)

🔍 **Happy searching!**
