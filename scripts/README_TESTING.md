# 🧪 Headless Testing Scripts для Admin Panel

**Автор:** streamlit-admin-developer agent
**Дата:** 2025-10-03
**Статус:** Active

---

## 📋 Обзор

Два скрипта для автоматического тестирования Streamlit страниц:

1. **`test_page_headless.py`** - Тестирует одну страницу
2. **`test_all_pages.py`** - Тестирует все 6 финальных страниц

---

## 🚀 Установка зависимостей

```bash
# Установить Playwright
pip install playwright

# Установить браузер Chromium
python -m playwright install chromium
```

---

## 📝 Использование

### 1. Тестирование одной страницы

```bash
python scripts/test_page_headless.py "web-admin/pages/🎯_Dashboard.py"
```

**Что делает:**
- ✅ Запускает Streamlit на порту 8552
- ✅ Открывает страницу в headless браузере
- ✅ Ждёт 5 секунд полной загрузки
- ✅ Проверяет наличие Python traceback
- ✅ Проверяет Streamlit exceptions
- ✅ Делает скриншот
- ✅ Возвращает результат

**Пример вывода (успех):**
```
======================================================================
🧪 TESTING PAGE: 🎯_Dashboard
======================================================================

🚀 Starting Streamlit server on port 8552...
⏳ Waiting for server to start...
✅ Server started
🌐 Opening page in headless browser...
✅ Page loaded (status: 200)
⏳ Waiting for page to render (5 seconds)...
✅ No Python traceback found
✅ No Streamlit exceptions found
📸 Screenshot saved: test_screenshots/🎯_Dashboard_2025-10-03_14-30-15.png
🛑 Stopping Streamlit server...
✅ Server stopped

======================================================================
✅ TEST PASSED
======================================================================
```

**Пример вывода (ошибка):**
```
======================================================================
🧪 TESTING PAGE: 🤖_Агенты
======================================================================

🚀 Starting Streamlit server on port 8552...
✅ Server started
🌐 Opening page in headless browser...
✅ Page loaded (status: 200)
⏳ Waiting for page to render (5 seconds)...
❌ Python traceback found in page!
❌ Found 1 Streamlit exception(s)!
   Error: NameError: name 'get_db_connection' is not defined
📸 Screenshot saved: test_screenshots/🤖_Агенты_2025-10-03_14-32-10_ERROR.png
🛑 Stopping Streamlit server...

======================================================================
❌ TEST FAILED
======================================================================
```

---

### 2. Тестирование всех страниц

#### Только компиляция (быстро, ~10 секунд)

```bash
python scripts/test_all_pages.py --compile-only
```

**Вывод:**
```
======================================================================
🧪 TESTING ALL ADMIN PAGES - COMPILATION CHECK
======================================================================

Testing 6 page(s)...

======================================================================
COMPILATION CHECK
======================================================================

  ✅ 🎯_Dashboard.py
  ✅ 👥_Пользователи.py
  ✅ 🤖_Агенты.py
  ✅ 📄_Гранты.py
  ✅ 📊_Аналитика.py
  ✅ ⚙️_Настройки.py

======================================================================
SUMMARY
======================================================================

✅ Passed: 6/6
❌ Failed: 0/6
📊 Pass Rate: 100.0%
⏱️  Duration: 8.2s

✅ ALL TESTS PASSED!
======================================================================
```

#### Полное headless тестирование (~12 минут)

```bash
python scripts/test_all_pages.py
```

**Вывод:**
```
======================================================================
🧪 TESTING ALL ADMIN PAGES - FULL HEADLESS TEST
======================================================================

Testing 6 page(s)...

======================================================================
HEADLESS BROWSER TESTING
======================================================================
This will take ~2 minutes per page...

📄 Testing: 🎯_Dashboard.py
  ✅ 🎯_Dashboard.py

======================================================================
🧪 TESTING PAGE: 🎯_Dashboard
======================================================================
[... детальный вывод ...]
✅ TEST PASSED

📄 Testing: 👥_Пользователи.py
  ✅ 👥_Пользователи.py
[... и так далее для всех 6 страниц ...]

======================================================================
SUMMARY
======================================================================

✅ Passed: 6/6
❌ Failed: 0/6
📊 Pass Rate: 100.0%
⏱️  Duration: 720.5s

✅ ALL TESTS PASSED!
======================================================================
```

---

## 📸 Скриншоты

Все скриншоты сохраняются в:
```
test_screenshots/
├── 🎯_Dashboard_2025-10-03_14-30-15.png
├── 👥_Пользователи_2025-10-03_14-32-20.png
├── 🤖_Агенты_2025-10-03_14-34-25.png
├── 📄_Гранты_2025-10-03_14-36-30.png
├── 📊_Аналитика_2025-10-03_14-38-35.png
└── ⚙️_Настройки_2025-10-03_14-40-40.png
```

**При ошибках:**
```
test_screenshots/
└── 🤖_Агенты_2025-10-03_14-32-10_ERROR.png  ← добавляется _ERROR
```

---

## 🔧 Кастомизация

### Изменить порт Streamlit

```bash
python scripts/test_page_headless.py "web-admin/pages/🎯_Dashboard.py" 9000
```

### Добавить свои проверки

Отредактируй `test_page_headless.py`, секция "Check for errors":

```python
# 5. Custom check example
custom_errors = await page.query_selector_all(".my-custom-error-class")
if custom_errors:
    print(f"❌ Found custom errors!")
    has_errors = True
```

---

## 🐛 Troubleshooting

### Ошибка: "Playwright not installed"

```bash
pip install playwright
python -m playwright install chromium
```

### Ошибка: "Server didn't start within 15 seconds"

Возможные причины:
- Порт уже занят (используй другой порт)
- Синтаксическая ошибка в файле страницы (сначала запусти `--compile-only`)
- Streamlit не установлен

### Ошибка: "File not found"

Проверь путь к файлу:
```bash
# Относительный путь от корня проекта
python scripts/test_page_headless.py "web-admin/pages/🎯_Dashboard.py"

# Или абсолютный путь
python scripts/test_page_headless.py "C:/SnowWhiteAI/GrantService/web-admin/pages/🎯_Dashboard.py"
```

---

## 📋 Workflow для разработчика

### После создания/изменения страницы:

```bash
# Шаг 1: Компиляция
python -m py_compile "web-admin/pages/🤖_Агенты.py"

# Шаг 2: Headless тест
python scripts/test_page_headless.py "web-admin/pages/🤖_Агенты.py"

# Шаг 3: Проверь скриншот
open test_screenshots/🤖_Агенты_*.png
```

### Перед коммитом:

```bash
# Быстрая проверка компиляции всех страниц
python scripts/test_all_pages.py --compile-only

# Если все OK, полное тестирование
python scripts/test_all_pages.py
```

---

## ⚙️ CI/CD Integration

### GitHub Actions

```yaml
name: Test Admin Panel

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright
          python -m playwright install chromium

      - name: Compile check
        run: python scripts/test_all_pages.py --compile-only

      - name: Headless tests
        run: python scripts/test_all_pages.py

      - name: Upload screenshots
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: test-screenshots
          path: test_screenshots/
```

---

## 📊 Метрики

### Время выполнения:

| Тип теста | Одна страница | Все 6 страниц |
|-----------|--------------|---------------|
| **Компиляция** | ~1 сек | ~10 сек |
| **Headless** | ~2 мин | ~12 мин |

### Что проверяется:

- ✅ Синтаксис Python (компиляция)
- ✅ Python traceback (runtime ошибки)
- ✅ Streamlit exceptions
- ✅ Console errors (JavaScript)
- ✅ Визуальная проверка (скриншот)

---

## 🎯 Best Practices

1. **Запускай компиляцию после каждого изменения**
   ```bash
   python -m py_compile "web-admin/pages/файл.py"
   ```

2. **Headless тест после рефакторинга**
   ```bash
   python scripts/test_page_headless.py "web-admin/pages/файл.py"
   ```

3. **Полное тестирование перед коммитом**
   ```bash
   python scripts/test_all_pages.py
   ```

4. **Проверяй скриншоты визуально**
   - Особенно при изменении UI
   - Сравнивай с предыдущими версиями

5. **Автоматизируй в CI/CD**
   - Добавь в GitHub Actions
   - Блокируй merge при failed тестах

---

## 📝 Changelog

**2025-10-03:**
- Создан `test_page_headless.py`
- Создан `test_all_pages.py`
- Добавлены скриншоты
- Интеграция с streamlit-admin-developer agent

---

## 🔗 Связанные документы

- `.claude/agents/streamlit-admin-developer.md` - Workflow агента
- `doc/FINAL_MENU_STRUCTURE.md` - Структура 6 финальных страниц
- `doc/REFACTORING_CHECKLIST.md` - Чеклист рефакторинга

---

**Поддержка:** streamlit-admin-developer agent
**Версия:** 1.0.0
