# Система номенклатуры GrantService
**Version**: 1.0.0 | **Last Updated**: 2025-10-12

## 📋 Содержание
- [Общее описание](#общее-описание)
- [Формат номенклатуры](#формат-номенклатуры)
- [Примеры](#примеры)
- [Генерация ID](#генерация-id)
- [Использование в коде](#использование-в-коде)
- [Миграция данных](#миграция-данных)

---

## 🎯 Общее описание

GrantService использует **унифицированную систему номенклатуры** для отслеживания всех артефактов на протяжении всего жизненного цикла грантовой заявки.

### Зачем нужна номенклатура?

1. **Трассируемость** - отслеживание артефактов от анкеты до финального гранта
2. **Читаемость** - ID понятны человеку без базы данных
3. **Уникальность** - гарантированная уникальность ID
4. **Версионирование** - поддержка multiple research/grants для одной анкеты
5. **Debugging** - легко найти все связанные данные по anketa_id

---

## 📐 Формат номенклатуры

### Anketa ID (основа всей номенклатуры)
```
#AN-YYYYMMDD-{user_identifier}-{counter:03d}
```

**Где**:
- `#AN` - префикс (AnketA)
- `YYYYMMDD` - дата создания (год-месяц-день)
- `{user_identifier}` - идентификатор пользователя (см. ниже)
- `{counter:03d}` - счётчик анкет пользователя за день (001, 002, 003...)

**Пример**:
```
#AN-20251008-ekaterina_maksimova-001
```

### User Identifier (приоритет)

1. **first_name + last_name** (транслитерация) - ⭐ ПРИОРИТЕТ
   - Екатерина Максимова → `ekaterina_maksimova`
   - Валерия → `valeriya`

2. **username** (если нет имени/фамилии)
   - @maxkate1 → `maxkate1`

3. **telegram_id** (fallback)
   - 123456789 → `123456789`

### Audit ID
```
{anketa_id}-AU-{counter:03d}
```

**Пример**:
```
#AN-20251008-ekaterina_maksimova-001-AU-001
```

### Research ID
```
{anketa_id}-RS-{counter:03d}
```

**Пример**:
```
#AN-20251008-ekaterina_maksimova-001-RS-001
#AN-20251008-ekaterina_maksimova-001-RS-002
```

### Grant ID
```
{anketa_id}-GR-{counter:03d}
```

**Пример**:
```
#AN-20251008-ekaterina_maksimova-001-GR-001
#AN-20251008-ekaterina_maksimova-001-GR-002
```

### Review ID
```
{anketa_id}-RV-{counter:03d}
```

**Пример**:
```
#AN-20251008-ekaterina_maksimova-001-RV-001
#AN-20251008-ekaterina_maksimova-001-RV-002
```

**Важно**: Review - это **независимое экспертное мнение** о готовом гранте. Review НЕ изменяет грант, а создает отдельную оценочную запись с review_id. Один грант может иметь несколько review (например, после доработок).

### Названия файлов PDF

PDF файлы называются по соответствующим ID (без символа `#`):

```
{id}.pdf  (где id - anketa_id, audit_id, research_id, или grant_id без #)
```

**Примеры**:
```
Interview PDF:  AN-20251011-ekaterina_maksimova-001.pdf
Audit PDF:      AN-20251011-ekaterina_maksimova-001-AU-002.pdf
Research PDF:   AN-20251011-ekaterina_maksimova-001-RS-001.pdf
Grant PDF:      AN-20251011-ekaterina_maksimova-001-GR-001.pdf
Review PDF:     AN-20251011-ekaterina_maksimova-001-RV-001.pdf
```

**Реализация**:
```python
# Interview PDF (telegram-bot/main.py)
filename = f"{anketa_id.replace('#', '')}.pdf"

# Audit PDF (agents/auditor_agent.py)
filename = f"{audit_id.replace('#', '')}.pdf"

# Research PDF (agents/researcher_agent_v2.py)
filename = f"{research_id.replace('#', '')}.pdf"

# Grant PDF (будущее)
filename = f"{grant_id.replace('#', '')}.pdf"

# Review PDF (agents/reviewer_agent.py)
filename = f"{review_id.replace('#', '')}.pdf"
```

**Преимущества**:
- ✅ Единообразие с системой ID
- ✅ Уникальность имен файлов
- ✅ Легко найти PDF по ID из БД
- ✅ Файлы сортируются по дате/пользователю
- ✅ Нет проблем с символом # в именах файлов

### Названия файлов MD (Markdown отчеты)

MD файлы следуют той же номенклатуре, что и PDF (без символа `#`):

```
{id}.md  (где id - anketa_id, audit_id, research_id, или grant_id без #)
```

**Примеры**:
```
Audit MD:      AN-20251011-ekaterina_maksimova-001-AU-002.md
Research MD:   AN-20251011-ekaterina_maksimova-001-RS-001.md
Grant MD:      AN-20251011-ekaterina_maksimova-001-GR-001.md
Review MD:     AN-20251011-ekaterina_maksimova-001-RV-001.md
```

**Реализация**:
```python
# Audit MD (agents/auditor_agent.py) - TODO
md_filename = f"{audit_id.replace('#', '')}.md"

# Research MD (agents/researcher_agent_v2.py)
md_filename = f"{research_id.replace('#', '')}.md"
md_filepath = os.path.join(current_dir, 'reports', md_filename)

# Grant MD (будущее)
md_filename = f"{grant_id.replace('#', '')}.md"

# Review MD (agents/reviewer_agent.py)
md_filename = f"{review_id.replace('#', '')}.md"
md_filepath = os.path.join(current_dir, 'reports', md_filename)
```

**Назначение**:
- ✅ MD отчет генерируется основным кодом приложения
- ✅ Используется как источник для PDF генерации
- ✅ Обеспечивает консистентность между MD и PDF
- ✅ Позволяет просмотр результатов в текстовом виде
- ✅ Сохраняется в `reports/` директории для отладки

**Важно**: MD файлы генерируются методами агентов (например, `_generate_research_report_md()` в `researcher_agent_v2.py`) ПЕРЕД генерацией PDF, чтобы гарантировать соответствие содержимого.

---

## 💡 Примеры

### Реальный workflow - Екатерина Максимова

```
Anketa:
#AN-20251008-ekaterina_maksimova-001

Audit:
#AN-20251008-ekaterina_maksimova-001-AU-001

Research (27 queries):
#AN-20251008-ekaterina_maksimova-001-RS-001

Grant (финальная заявка):
#AN-20251008-ekaterina_maksimova-001-GR-001

Review (независимая экспертная оценка):
#AN-20251008-ekaterina_maksimova-001-RV-001
```

### Реальный workflow - Валерия (@Leryusya)

```
Anketa:
#AN-20251008-valeriya-001

Research:
#AN-20251008-valeriya-001-RS-001

Grant:
#AN-20251008-valeriya-001-GR-001
```

### Тестовый пользователь (без имени)

```
Anketa:
#AN-20251008-maxkate1-001

Research:
#AN-20251008-maxkate1-001-RS-001

Grant:
#AN-20251008-maxkate1-001-GR-001
```

### Multiple версии

Если пользователь запросил несколько research для одной анкеты:

```
#AN-20251008-ekaterina_maksimova-001-RS-001  (первое исследование)
#AN-20251008-ekaterina_maksimova-001-RS-002  (повторное исследование)
#AN-20251008-ekaterina_maksimova-001-RS-003  (третье исследование)
```

То же самое с грантами:

```
#AN-20251008-ekaterina_maksimova-001-GR-001  (первая версия гранта)
#AN-20251008-ekaterina_maksimova-001-GR-002  (переписанная версия)
```

---

## 🔧 Генерация ID

### Методы в `data/database/models.py`

#### 1. `generate_anketa_id(user_data: Dict) -> str`

Генерирует anketa_id на основе данных пользователя.

**Вход**:
```python
user_data = {
    'telegram_id': 791123834200,
    'first_name': 'Екатерина',
    'last_name': 'Максимова',
    'username': 'ekaterina_maximova'
}
```

**Выход**:
```python
'#AN-20251008-ekaterina_maksimova-001'
```

**Логика**:
```python
def generate_anketa_id(self, user_data: Dict[str, Any]) -> str:
    """Генерация ID анкеты в формате #AN-YYYYMMDD-username-001"""
    date_str = datetime.now().strftime("%Y%m%d")
    user_identifier = self._get_user_identifier(user_data)
    next_number = self._get_next_anketa_number(user_identifier, date_str)
    return f"#AN-{date_str}-{user_identifier}-{next_number:03d}"
```

#### 2. `generate_audit_id(anketa_id: str) -> str`

Генерирует audit_id на основе anketa_id.

**Вход**:
```python
anketa_id = '#AN-20251008-ekaterina_maksimova-001'
```

**Выход**:
```python
'#AN-20251008-ekaterina_maksimova-001-AU-001'
```

**Логика**:
```python
def generate_audit_id(self, anketa_id: str) -> str:
    """Generate audit ID: anketa_id + AU suffix + counter"""
    # Считаем существующие audit для этой anketa
    count = self._count_audits_for_anketa(anketa_id)
    return f"{anketa_id}-AU-{count + 1:03d}"
```

#### 3. `generate_research_id(anketa_id: str) -> str`

Генерирует research_id на основе anketa_id.

**Вход**:
```python
anketa_id = '#AN-20251008-ekaterina_maksimova-001'
```

**Выход**:
```python
'#AN-20251008-ekaterina_maksimova-001-RS-001'
```

**Логика**:
```python
def generate_research_id(self, anketa_id: str) -> str:
    """Generate research ID: anketa_id + RS suffix + counter"""
    # Считаем существующие research для этой anketa
    count = self._count_research_for_anketa(anketa_id)
    return f"{anketa_id}-RS-{count + 1:03d}"
```

#### 4. `generate_grant_id(anketa_id: str) -> str`

Генерирует grant_id на основе anketa_id.

**Вход**:
```python
anketa_id = '#AN-20251008-ekaterina_maksimova-001'
```

**Выход**:
```python
'#AN-20251008-ekaterina_maksimova-001-GR-001'
```

**Логика**:
```python
def generate_grant_id(self, anketa_id: str) -> str:
    """Generate grant ID: anketa_id + GR suffix + counter"""
    # Считаем существующие гранты для этой anketa
    count = self._count_grants_for_anketa(anketa_id)
    return f"{anketa_id}-GR-{count + 1:03d}"
```

#### 5. `generate_review_id(anketa_id: str) -> str`

Генерирует review_id на основе anketa_id.

**Вход**:
```python
anketa_id = '#AN-20251008-ekaterina_maksimova-001'
```

**Выход**:
```python
'#AN-20251008-ekaterina_maksimova-001-RV-001'
```

**Логика**:
```python
def generate_review_id(self, anketa_id: str) -> str:
    """Generate review ID: anketa_id + RV suffix + counter"""
    # Считаем существующие review для этой anketa
    count = self._count_reviews_for_anketa(anketa_id)
    return f"{anketa_id}-RV-{count + 1:03d}"
```

---

## 💻 Использование в коде

### ✅ ПРАВИЛЬНО - Agents

#### researcher_agent_v2.py

```python
async def _create_research_record(self, anketa_id: str, anketa: Dict) -> str:
    """Создать запись исследования в БД с правильной номенклатурой"""

    research_data = {
        # ❗ НЕ передаём research_id - db сам сгенерирует!
        'anketa_id': anketa_id,
        'user_id': user_id,
        'session_id': session_id,
        'research_type': 'expert_websearch_27_queries',
        'llm_provider': self.websearch_provider,
        'model': 'router',
        'status': 'pending',
        'research_results': {}
    }

    # ✅ db.save_research_results() автоматически вызывает generate_research_id()
    saved_id = self.db.save_research_results(research_data)
    return saved_id  # Вернёт: #AN-20251008-ekaterina_maksimova-001-RS-001
```

#### writer_agent_v2.py

Writer V2 НЕ создает grant_id напрямую - он сохраняет в `grant_applications`, не в `grants`.
Таблица `grants` используется только в E2E тестах.

### ✅ ПРАВИЛЬНО - E2E Tests

#### test_ekaterina_grant_e2e.py

```python
# Импорт БД для генерации ID
from models import GrantServiceDatabase
db = GrantServiceDatabase()

# Генерация anketa_id
anketa_id = db.generate_anketa_id({
    'telegram_id': 791123834200,
    'first_name': 'Екатерина',
    'last_name': 'Максимова',
    'username': 'ekaterina_maximova'
})
# Результат: #AN-20251011-ekaterina_maksimova-001

# Генерация research_id
research_id = db.generate_research_id(anketa_id)
# Результат: #AN-20251011-ekaterina_maksimova-001-RS-001

# Генерация grant_id
grant_id = db.generate_grant_id(anketa_id)
# Результат: #AN-20251011-ekaterina_maksimova-001-GR-001
```

### ❌ НЕПРАВИЛЬНО - Старые подходы

```python
# ❌ НЕ ДЕЛАТЬ ТАК!
research_id = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
# Результат: RES-20251012153045 (нет связи с anketa!)

# ❌ НЕ ДЕЛАТЬ ТАК!
grant_id = f"GRANT_EKATERINA_{datetime.now().strftime('%Y%m%d')}"
# Результат: GRANT_EKATERINA_20251012 (нет связи с anketa!)

# ❌ НЕ ДЕЛАТЬ ТАК!
anketa_id = f"EKATERINA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
# Результат: EKATERINA_20251012_153045 (не соответствует формату)
```

---

## 🔄 Миграция данных

### Migration 009: Unify Research and Grant IDs

Файл: `database/migrations/009_unify_research_grant_ids.sql`

```sql
-- Обновляем существующие research_id в правильный формат
UPDATE researcher_research
SET research_id = anketa_id || '-RS-001'
WHERE research_id NOT LIKE '%RS-%';

-- Обновляем существующие grant_id в правильный формат
UPDATE grants
SET grant_id = anketa_id || '-GR-001'
WHERE grant_id NOT LIKE '%GR-%';
```

### Как запустить миграцию

```bash
# PostgreSQL
PGPASSWORD=root psql -h localhost -U postgres -d grantservice -f database/migrations/009_unify_research_grant_ids.sql

# Или через Python
python scripts/apply_migration_009.py
```

---

## 📊 Проверка номенклатуры в БД

### Проверить все ID для одной анкеты

```sql
-- Найти все артефакты для Екатерины
SELECT
    'anketa' as type,
    anketa_id as id,
    created_at
FROM sessions
WHERE anketa_id LIKE '#AN-20251008-ekaterina_maksimova%'

UNION ALL

SELECT
    'research' as type,
    research_id as id,
    created_at
FROM researcher_research
WHERE anketa_id LIKE '#AN-20251008-ekaterina_maksimova%'

UNION ALL

SELECT
    'grant' as type,
    grant_id as id,
    created_at
FROM grants
WHERE anketa_id LIKE '#AN-20251008-ekaterina_maksimova%'

ORDER BY created_at;
```

**Ожидаемый результат**:
```
type     | id                                              | created_at
---------|------------------------------------------------|-------------------
anketa   | #AN-20251008-ekaterina_maksimova-001          | 2025-10-08 14:30:00
research | #AN-20251008-ekaterina_maksimova-001-RS-001   | 2025-10-08 14:35:00
grant    | #AN-20251008-ekaterina_maksimova-001-GR-001   | 2025-10-08 14:45:00
```

### Проверить неправильную номенклатуру

```sql
-- Найти research_id без правильного формата
SELECT research_id, anketa_id, created_at
FROM researcher_research
WHERE research_id NOT LIKE '#AN-%RS-%';

-- Найти grant_id без правильного формата
SELECT grant_id, anketa_id, created_at
FROM grants
WHERE grant_id NOT LIKE '#AN-%GR-%';
```

---

## 🔍 Debugging

### Как найти все данные пользователя?

Если известен anketa_id:
```sql
SELECT * FROM sessions WHERE anketa_id = '#AN-20251008-ekaterina_maksimova-001';
SELECT * FROM researcher_research WHERE anketa_id = '#AN-20251008-ekaterina_maksimova-001';
SELECT * FROM grants WHERE anketa_id = '#AN-20251008-ekaterina_maksimova-001';
```

Если известен только username:
```sql
SELECT * FROM sessions WHERE anketa_id LIKE '#AN-%-ekaterina_maksimova-%';
```

Если известен только telegram_id:
```sql
-- Сначала найти анкеты
SELECT anketa_id FROM sessions WHERE telegram_id = 791123834200;

-- Потом найти research и grants по anketa_id
```

---

## 📝 Best Practices

### ✅ DO

1. **Всегда используй методы БД** для генерации ID:
   ```python
   db.generate_anketa_id(user_data)
   db.generate_research_id(anketa_id)
   db.generate_grant_id(anketa_id)
   ```

2. **Проверяй формат** при вставке в БД:
   ```python
   assert anketa_id.startswith('#AN-'), "Invalid anketa_id format"
   assert research_id.endswith('-RS-'), "Invalid research_id format"
   assert grant_id.endswith('-GR-'), "Invalid grant_id format"
   ```

3. **Логируй ID** для debugging:
   ```python
   logger.info(f"Created research: {research_id} for anketa: {anketa_id}")
   ```

### ❌ DON'T

1. **НЕ создавай ID вручную**:
   ```python
   # ❌ НЕПРАВИЛЬНО
   research_id = f"RES-{timestamp}"
   ```

2. **НЕ забывай передавать anketa_id**:
   ```python
   # ❌ НЕПРАВИЛЬНО - research_id без связи с anketa
   research_id = generate_random_id()
   ```

3. **НЕ используй старые форматы**:
   ```python
   # ❌ НЕПРАВИЛЬНО - старый формат
   anketa_id = f"EKATERINA_{date}"
   ```

---

## 🧪 Тестирование номенклатуры

### E2E Test

Файл: `tests/integration/test_ekaterina_grant_e2e.py`

Тест проверяет правильность номенклатуры на всех этапах workflow:

```bash
python tests/integration/test_ekaterina_grant_e2e.py
```

**Проверяет**:
- ✅ Anketa ID соответствует формату `#AN-YYYYMMDD-username-NNN`
- ✅ Research ID = `{anketa_id}-RS-NNN`
- ✅ Grant ID = `{anketa_id}-GR-NNN`
- ✅ Все ID сохранены в БД
- ✅ Связи между артефактами корректны

---

## 📚 Связанные документы

- [DATABASE.md](./DATABASE.md) - Схема базы данных
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Архитектура системы
- [AI_AGENTS.md](./AI_AGENTS.md) - Конфигурация AI агентов
- [CHANGELOG.md](./CHANGELOG.md) - История изменений

---

## 🐛 Known Issues

### Issue #1: Legacy data без правильной номенклатуры

**Проблема**: Старые записи в БД созданы до внедрения номенклатуры.

**Решение**: Запустить migration 009:
```bash
python scripts/apply_migration_009.py
```

### Issue #2: Tests создают неправильные ID

**Проблема**: Старые тесты используют хардкод вместо db методов.

**Решение**: Обновлено в test_ekaterina_grant_e2e.py (2025-10-12).

---

## 📞 Support

Если номенклатура работает неправильно:

1. Проверьте формат ID в БД (см. раздел "Проверка номенклатуры")
2. Запустите E2E тест для проверки workflow
3. Проверьте логи агентов на предмет ошибок генерации ID
4. Создайте issue с примером неправильного ID

---

**Version**: 1.0.0
**Last Updated**: 2025-10-12
**Maintained by**: database-manager agent

---

*Эта документация является частью модульной системы документации GrantService*
