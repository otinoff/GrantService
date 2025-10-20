# План на следующую сессию - Тестирование "Лучные клубы Кемерово"

**Дата**: 2025-10-12
**Статус**: ✅ ГОТОВО К ЗАПУСКУ

---

## 🎯 ЦЕЛЬ

Запустить E2E тест "Лучные клубы Кемерово" и проверить работу интерактивного pipeline для президентских грантов.

---

## ⚡ БЫСТРЫЙ СТАРТ

### Шаг 1: Запустить тест

```bash
# Вариант 1: Через локальный скрипт (рекомендуется)
python scripts/generate_archery_grant_local.py

# Вариант 2: Через pytest
pytest tests/integration/test_archery_club_fpg_e2e.py -v -s
```

### Шаг 2: Проверить артефакты

```bash
# Открыть директорию с результатами
cd grants_output/archery_kemerovo/

# Список файлов
ls -la

# Ожидается:
# - anketa_archery_kemerovo_audit.md
# - anketa_archery_kemerovo_audit.pdf
# - research_archery_kemerovo.md
# - research_archery_kemerovo.pdf
# - grant_AN-YYYYMMDD-archery_kemerovo-NNN.md
# - grant_AN-YYYYMMDD-archery_kemerovo-NNN.pdf
# - review_AN-YYYYMMDD-archery_kemerovo-NNN.md
# - review_AN-YYYYMMDD-archery_kemerovo-NNN.pdf
```

### Шаг 3: Проверить качество

Открыть MD файлы и проверить:

#### Анкета (`anketa_archery_kemerovo_audit.md`)
- [ ] Все 24 поля заполнены
- [ ] Audit score >= 60/100
- [ ] Есть рекомендации по улучшению
- [ ] Интерактивные уточнения присутствуют

#### Исследование (`research_archery_kemerovo.md`)
- [ ] 28 блоков (27 базовых + 1 ФПГ)
- [ ] Есть цитаты и источники
- [ ] Блок fund_requirements присутствует
- [ ] Данные о направлениях и критериях ФПГ

#### Грант (`grant_AN-*.md`)
- [ ] 9 разделов (форма ФПГ)
- [ ] 15000-20000 символов
- [ ] 10+ цитат из research
- [ ] 2+ таблицы
- [ ] Номенклатура правильная (#AN-YYYYMMDD-username-NNN)

#### Обзор (`review_AN-*.md`)
- [ ] Оценка по 4 критериям
- [ ] Readiness score >= 6/10
- [ ] Approval probability >= 30%
- [ ] Есть рекомендации по улучшению

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### Оценки

| Метрика | Ожидаемое | Описание |
|---------|-----------|----------|
| Audit Score | 60-80/100 | Качество анкеты |
| Total Queries | 28 | 27 + 1 ФПГ |
| Grant Length | 15000-20000 | Символов |
| Readiness | 6-8/10 | Готовность |
| Approval | 40-50% | Вероятность |

### Время выполнения

- ЭТАП 1 (Interview): ~5-10 минут
- ЭТАП 2 (Research): ~10-15 минут
- ЭТАП 3 (Writing): ~5-10 минут
- ЭТАП 4 (Review): ~2-5 минут
- **ИТОГО**: ~22-40 минут

---

## 🔧 ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК

### Ошибка: ModuleNotFoundError

```bash
# Проверить пути
python -c "import sys; print('\n'.join(sys.path))"

# Переустановить зависимости
pip install -r requirements.txt
```

### Ошибка: Database connection

```bash
# Проверить .env файл
cat config/.env | grep PG

# Должно быть:
# PGHOST=5.35.88.251
# PGPORT=5432
# PGDATABASE=grantservice
# PGUSER=postgres
# PGPASSWORD=root
```

### Ошибка: GigaChat API

```bash
# Проверить ключ
cat config/.env | grep GIGACHAT

# Должен быть актуальный ключ
# GIGACHAT_API_KEY=...
```

### Ошибка: Perplexity API

```bash
# Проверить ключ
cat config/.env | grep PERPLEXITY

# Должен быть актуальный ключ
# PERPLEXITY_API_KEY=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
```

---

## 📝 ЧТО ДЕЛАТЬ ПОСЛЕ ТЕСТА

### Сценарий 1: Тест прошёл успешно ✅

1. **Проверить качество артефактов**
   - Открыть MD файлы
   - Оценить полноту и корректность данных

2. **Документировать результаты**
   - Скопировать оценки в отчёт
   - Сделать скриншоты (опционально)

3. **Обсудить следующие шаги**
   - Нужны ли доработки?
   - Готовы ли к интеграции в production?
   - Какие ещё тесты нужны?

4. **Подготовить к коммиту** (если утверждено)
   - Code review
   - Обновить документацию
   - Создать PR

### Сценарий 2: Тест провалился ❌

1. **Изучить логи**
   - Найти место ошибки
   - Понять причину

2. **Исправить проблему**
   - Обновить код
   - Добавить обработку ошибок

3. **Повторить тест**
   ```bash
   python scripts/generate_archery_grant_local.py
   ```

4. **Документировать баги**
   - Создать issues
   - Добавить в TODO

---

## 🎯 АЛЬТЕРНАТИВНЫЕ ТЕСТЫ

После успешного теста "Лучные клубы Кемерово" можно протестировать другие проекты:

### Тест 2: Социальная поддержка молодых семей (Москва)

```python
YOUNG_FAMILIES_DATA = {
    "project_name": "Социальная поддержка молодых семей",
    "geography": "Москва",
    "budget": "1200000",
    "grant_fund": "Фонд президентских грантов",
    # ... остальные данные
}
```

### Тест 3: Экологический проект (Санкт-Петербург)

```python
ECO_PROJECT_DATA = {
    "project_name": "Чистый город - экология для всех",
    "geography": "Санкт-Петербург",
    "budget": "900000",
    "grant_fund": "Фонд президентских грантов",
    # ... остальные данные
}
```

---

## 📚 ДОКУМЕНТАЦИЯ

### Созданные файлы (локально, НЕ в git)

1. **План**: `.claude/PRESIDENTIAL_GRANTS_INTERACTIVE_PIPELINE_PLAN.md`
   - Архитектура pipeline
   - Требования и спецификации

2. **Отчёт**: `.claude/PRESIDENTIAL_GRANTS_IMPLEMENTATION_REPORT.md`
   - Детали реализации
   - Технические характеристики

3. **Этот файл**: `.claude/NEXT_SESSION_ARCHERY_TEST.md`
   - Инструкции для запуска

### Код (локально, НЕ в git)

1. `agents/interactive_interviewer_agent.py`
2. `agents/presidential_grants_researcher.py`
3. `utils/artifact_saver.py`
4. `tests/integration/test_archery_club_fpg_e2e.py`
5. `scripts/generate_archery_grant_local.py`

### Изменения (локально, НЕ в git)

1. `shared/llm/config.py` - Writer/Auditor → GigaChat

---

## ✅ ЧЕКЛИСТ ПЕРЕД ЗАПУСКОМ

- [ ] PostgreSQL доступна (5.35.88.251)
- [ ] GigaChat API ключ в config/.env
- [ ] Perplexity API ключ в config/.env
- [ ] Claude API ключ в config/.env (для Researcher LLM)
- [ ] Python 3.9+ установлен
- [ ] Все зависимости установлены (pip install -r requirements.txt)
- [ ] Нет конфликтующих процессов (проверить порты)

---

## 🚀 КОМАНДА ДЛЯ ЗАПУСКА

```bash
python scripts/generate_archery_grant_local.py
```

**Время выполнения**: 22-40 минут

**Артефакты**: `grants_output/archery_kemerovo/` (8 файлов)

---

**ВАЖНО**: НЕ коммитить в git до утверждения!

---

**Готово к запуску!** 🎯
