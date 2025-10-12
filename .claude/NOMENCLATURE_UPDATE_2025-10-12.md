# 🏷️ Система номенклатуры внедрена - 2025-10-12

## ✅ Что сделано

### 1. Создана полная документация
📄 **Файл**: `doc/NOMENCLATURE.md` (1.0.0)
- 400+ строк детальной документации
- Формат, примеры, использование, best practices
- SQL запросы для проверки
- Руководство по миграции legacy данных

### 2. Исправлена кодовая база
✅ **researcher_agent_v2.py** - использует `db.generate_research_id(anketa_id)`
✅ **test_ekaterina_grant_e2e.py** - все ID через методы БД
✅ **writer_agent_v2.py** - проверен (не создает grant_id напрямую)

### 3. Обновлена главная документация
✅ **doc/README.md** v1.0.7 - добавлен раздел о номенклатуре
✅ **doc/CHANGELOG.md** v1.0.7 - полная запись изменений

### 4. Проверено E2E тестом
✅ Тест прошел успешно
✅ Все ID сохранены в правильном формате
✅ Связи между артефактами корректны

---

## 📊 Правильная номенклатура

### Формат

```
Anketa:   #AN-YYYYMMDD-{user_identifier}-{counter:03d}
Research: {anketa_id}-RS-{counter:03d}
Grant:    {anketa_id}-GR-{counter:03d}
```

### Реальный пример (Екатерина Максимова)

```
Anketa:   #AN-20251011-ekaterina_maksimova-001
Research: #AN-20251011-ekaterina_maksimova-001-RS-001
Grant:    #AN-20251011-ekaterina_maksimova-001-GR-001
```

### User Identifier (приоритет)

1. **first_name + last_name** (транслитерация) ⭐
   - Екатерина Максимова → `ekaterina_maksimova`
   - Валерия → `valeriya`

2. **username** (fallback)
   - @maxkate1 → `maxkate1`

3. **telegram_id** (last resort)
   - 123456789 → `123456789`

---

## 💻 Как использовать

### Правильный способ (используй ВСЕГДА)

```python
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

### ❌ Неправильный способ (НЕ ДЕЛАТЬ!)

```python
# ❌ НЕ ДЕЛАТЬ ТАК!
research_id = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
grant_id = f"GRANT_EKATERINA_{datetime.now().strftime('%Y%m%d')}"
anketa_id = f"EKATERINA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
```

---

## 🔍 Проверка в БД

### Найти все артефакты пользователя

```sql
-- По anketa_id
SELECT 'anketa' as type, anketa_id as id FROM sessions
WHERE anketa_id = '#AN-20251011-ekaterina_maksimova-001'

UNION ALL

SELECT 'research' as type, research_id as id FROM researcher_research
WHERE anketa_id = '#AN-20251011-ekaterina_maksimova-001'

UNION ALL

SELECT 'grant' as type, grant_id as id FROM grants
WHERE anketa_id = '#AN-20251011-ekaterina_maksimova-001'

ORDER BY type;
```

**Результат**:
```
type     | id
---------|--------------------------------------------------
anketa   | #AN-20251011-ekaterina_maksimova-001
grant    | #AN-20251011-ekaterina_maksimova-001-GR-001
research | #AN-20251011-ekaterina_maksimova-001-RS-001
```

### Проверить неправильную номенклатуру

```sql
-- Найти research без правильного формата
SELECT research_id, anketa_id FROM researcher_research
WHERE research_id NOT LIKE '#AN-%RS-%';

-- Найти grants без правильного формата
SELECT grant_id, anketa_id FROM grants
WHERE grant_id NOT LIKE '#AN-%GR-%';
```

---

## 📚 Где найти документацию

### Главный индекс документации
📂 **Файл**: `doc/README.md`

Таблица документации:
```
🏗️ Architecture      - ARCHITECTURE.md
🔧 Components        - COMPONENTS.md
🗄️ Database          - DATABASE.md
🏷️ Nomenclature ⭐   - NOMENCLATURE.md  (НОВОЕ!)
📡 API Reference     - API_REFERENCE.md
🤖 AI Agents         - AI_AGENTS.md
🚀 Deployment        - DEPLOYMENT.md
📝 Change Log        - CHANGELOG.md
```

### Полная документация номенклатуры
📄 **Файл**: `doc/NOMENCLATURE.md`

**Содержание**:
- 📋 Общее описание
- 📐 Формат номенклатуры
- 💡 Примеры (реальные workflow)
- 🔧 Генерация ID (методы БД)
- 💻 Использование в коде
- 🔄 Миграция данных
- 📊 Проверка в БД
- 🔍 Debugging
- 📝 Best practices
- 🧪 Тестирование

### История изменений
📄 **Файл**: `doc/CHANGELOG.md` - версия 1.0.7

Запись о внедрении номенклатуры с полным списком изменений.

---

## 🎯 Преимущества новой системы

### До (проблемы)
❌ Разные форматы ID (`RES-timestamp`, `GRANT_EKATERINA_date`, `EKATERINA_datetime`)
❌ Нет связи между артефактами
❌ Сложно найти все данные пользователя
❌ ID не читаемы без БД
❌ Нет поддержки версий

### После (решение)
✅ Единый формат для всех ID
✅ Четкая связь через anketa_id
✅ Легко найти все данные: `WHERE anketa_id LIKE '#AN-%-username-%'`
✅ ID читаемы: видно дату, имя, тип
✅ Поддержка версий: -RS-001, -RS-002, -GR-001, -GR-002

---

## 🧪 Тестирование

### E2E Test
```bash
python tests/integration/test_ekaterina_grant_e2e.py
```

**Статус**: ✅ PASSED

**Проверяет**:
- Anketa ID в правильном формате
- Research ID = anketa_id-RS-001
- Grant ID = anketa_id-GR-001
- Все ID сохранены в БД
- Связи между артефактами корректны

### Результат теста (2025-10-12)
```
✅ Anketa ID: #AN-20251011-ekaterina_maksimova-001
✅ Research ID: #AN-20251011-ekaterina_maksimova-001-RS-001
✅ Grant ID: #AN-20251011-ekaterina_maksimova-001-GR-001
✅ Все артефакты: 5/5 сохранены
```

---

## 🔧 Измененные файлы

### Кодовая база
1. `agents/researcher_agent_v2.py` - line 438-464
   - Убран хардкод `research_id = f"RES-{timestamp}"`
   - Теперь `db.save_research_results()` генерирует ID автоматически

2. `tests/integration/test_ekaterina_grant_e2e.py` - lines 59-64, 337, 424, 522
   - Добавлен импорт `GrantServiceDatabase`
   - Все ID генерируются через методы БД

3. `agents/writer_agent_v2.py` - проверен
   - Не создает grant_id напрямую
   - Сохраняет в `grant_applications`, не в `grants`

### Документация
1. `doc/NOMENCLATURE.md` - **НОВЫЙ** файл (400+ строк)
2. `doc/README.md` v1.0.6 → v1.0.7
   - Добавлен раздел о номенклатуре
   - Обновлена таблица документации
3. `doc/CHANGELOG.md` v1.0.6 → v1.0.7
   - Полная запись изменений 1.0.7

---

## 📞 Быстрая помощь

### Если ID в неправильном формате

1. **Проверь в БД**:
   ```sql
   SELECT research_id, anketa_id FROM researcher_research
   WHERE research_id NOT LIKE '#AN-%RS-%';
   ```

2. **Запусти миграцию**:
   ```bash
   python scripts/apply_migration_009.py
   ```

3. **Проверь код**:
   - Используешь ли `db.generate_*_id()` методы?
   - Не создаёшь ли ID вручную через `f"RES-{timestamp}"`?

### Если нужны примеры

📖 Открой `doc/NOMENCLATURE.md` - раздел "Примеры"

Там есть реальные workflow для:
- Екатерины Максимовой (с именем и фамилией)
- Валерии (@Leryusya - только имя)
- Тестового пользователя (username)
- Multiple versions (RS-001, RS-002, GR-001, GR-002)

### Если что-то не работает

1. Проверь E2E тест: `python tests/integration/test_ekaterina_grant_e2e.py`
2. Проверь логи агентов на предмет ошибок генерации ID
3. Открой issue с примером неправильного ID

---

## ✅ Чек-лист для новых разработчиков

Перед тем как создавать новые ID:

- [ ] Прочитал `doc/NOMENCLATURE.md`?
- [ ] Использую `db.generate_anketa_id(user_data)`?
- [ ] Использую `db.generate_research_id(anketa_id)`?
- [ ] Использую `db.generate_grant_id(anketa_id)`?
- [ ] НЕ создаю ID вручную через f-strings?
- [ ] Логирую созданные ID для debugging?
- [ ] Проверил формат ID в БД после теста?

---

## 🎉 Итого

**Система номенклатуры полностью внедрена!**

✅ Документация создана
✅ Код исправлен
✅ Тесты проходят
✅ БД проверена

**Больше не путаемся с ID!** Все в одном месте: `doc/NOMENCLATURE.md`

---

**Дата**: 2025-10-12
**Версия документации**: 1.0.7
**Maintained by**: database-manager agent
