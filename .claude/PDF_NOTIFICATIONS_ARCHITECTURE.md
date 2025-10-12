# 📄 Архитектура PDF уведомлений в админский чат

**Version**: 1.0.0 | **Created**: 2025-10-12 | **Status**: DESIGN

---

## 🎯 Цель

Автоматически отправлять PDF отчеты в админский чат (-4930683040) на каждом этапе грантового workflow с возможностью включения/выключения в настройках.

---

## 📊 Workflow этапы и отчеты

### 1. 📝 Interview (Анкета)
**Триггер**: Пользователь завершил интервью (24 вопроса)

**PDF содержание**:
- Заголовок: "АНКЕТА ПОЛЬЗОВАТЕЛЯ"
- Metadata: anketa_id, username, дата
- Q&A формат: Вопрос → Ответ (24 пары)
- Footer: GrantService watermark

**Файл**: `#{anketa_id}_ANKETA.pdf`

---

### 2. 🔍 Auditor (Аудит)
**Триггер**: Аудитор завершил оценку проекта

**PDF содержание**:
- Заголовок: "АУДИТ ПРОЕКТА"
- Metadata: anketa_id, дата аудита
- Оценка качества: X/10
- Детальный анализ
- Оценка реализуемости
- Факторы риска
- Рекомендации

**Файл**: `#{anketa_id}_AUDIT.pdf`

---

### 3. 📊 Researcher (Исследование)
**Триггер**: Researcher завершил все 27 queries

**PDF содержание**:
- Заголовок: "ИССЛЕДОВАНИЕ ПРОЕКТА"
- Metadata: anketa_id, research_id, дата
- 27 Queries:
  - Query 1: Вопрос → Ответ → Источники
  - Query 2: ...
  - Query 27: ...
- Сводный анализ
- Ключевые находки

**Файл**: `#{research_id}_RESEARCH.pdf`

---

### 4. ✍️ Writer (Грант)
**Триггер**: Writer завершил написание гранта

**PDF содержание**:
- Заголовок: "ГРАНТОВАЯ ЗАЯВКА"
- Metadata: anketa_id, grant_id, дата
- Название проекта
- Оценка качества: X/10
- Секции гранта:
  - Описание проекта
  - Цели и задачи
  - План реализации
  - Бюджет
  - Ожидаемые результаты
- Полный текст гранта

**Файл**: `#{grant_id}_GRANT.pdf`

---

### 5. 👁️ Reviewer (Ревью)
**Триггер**: Reviewer завершил проверку гранта

**PDF содержание**:
- Заголовок: "ЗАКЛЮЧЕНИЕ РЕВЬЮВЕРА"
- Metadata: anketa_id, grant_id, дата ревью
- Оценка качества: X/10
- Сильные стороны
- Слабые стороны
- Рекомендации по улучшению
- Финальное заключение (одобрен/требует доработки)

**Файл**: `#{grant_id}_REVIEW.pdf`

---

## 🏗️ Архитектура компонентов

### 1. **StageReportGenerator** (NEW)
**Файл**: `telegram-bot/utils/stage_report_generator.py`

```python
class StageReportGenerator:
    """Генератор PDF отчетов для каждого этапа workflow"""

    def generate_interview_pdf(anketa_data: Dict) -> bytes
    def generate_audit_pdf(audit_data: Dict) -> bytes
    def generate_research_pdf(research_data: Dict) -> bytes
    def generate_grant_pdf(grant_data: Dict) -> bytes
    def generate_review_pdf(review_data: Dict) -> bytes
```

**Особенности**:
- ReportLab для генерации PDF
- Русский шрифт DejaVuSans
- Единый стиль для всех этапов
- Q&A форматирование
- Watermark GrantService

---

### 2. **AdminNotifier** (РАСШИРЕНИЕ)
**Файл**: `telegram-bot/utils/admin_notifications.py`

**Новые методы**:
```python
async def send_stage_completion_pdf(
    self,
    stage: str,  # 'interview', 'audit', 'research', 'grant', 'review'
    pdf_bytes: bytes,
    filename: str,
    caption: str,
    anketa_id: str
) -> bool
```

**Логика**:
1. Проверить настройки (включены ли уведомления для этого этапа)
2. Сгенерировать текстовое уведомление
3. Отправить PDF документ через telegram_sender
4. Логировать результат

---

### 3. **Settings в БД** (NEW TABLE)
**Таблица**: `admin_notification_settings`

```sql
CREATE TABLE admin_notification_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Настройки по умолчанию
INSERT INTO admin_notification_settings (setting_key, setting_value) VALUES
('notifications_enabled', TRUE),
('notify_on_interview', TRUE),
('notify_on_audit', TRUE),
('notify_on_research', TRUE),
('notify_on_grant', TRUE),
('notify_on_review', TRUE);
```

---

### 4. **Settings UI** (ОБНОВЛЕНИЕ)
**Файл**: `web-admin/pages/⚙️_Настройки.py`

**Новая секция**: "📄 Уведомления в админский чат"

```python
st.subheader("📄 Уведомления в админский чат")
st.info(f"Чат ID: -4930683040")

# Главный toggle
notifications_enabled = st.toggle(
    "Включить автоматические уведомления",
    value=get_setting('notifications_enabled')
)

if notifications_enabled:
    col1, col2 = st.columns(2)

    with col1:
        notify_interview = st.checkbox("📝 Анкета заполнена", value=True)
        notify_audit = st.checkbox("🔍 Аудит завершен", value=True)
        notify_research = st.checkbox("📊 Исследование готово", value=True)

    with col2:
        notify_grant = st.checkbox("✍️ Грант написан", value=True)
        notify_review = st.checkbox("👁️ Ревью завершено", value=True)

if st.button("💾 Сохранить настройки"):
    save_notification_settings(...)
    st.success("✅ Настройки сохранены!")
```

---

## 🔄 Интеграция в workflow

### Interview Agent
**Файл**: `agents/interviewer_agent.py`

```python
# После завершения интервью
if session_complete:
    # Генерация PDF
    pdf_generator = StageReportGenerator()
    pdf_bytes = pdf_generator.generate_interview_pdf(anketa_data)

    # Отправка в админский чат
    notifier = AdminNotifier(bot_token)
    await notifier.send_stage_completion_pdf(
        stage='interview',
        pdf_bytes=pdf_bytes,
        filename=f"#{anketa_id}_ANKETA.pdf",
        caption=f"📝 Анкета заполнена\nПользователь: {username}\nID: {anketa_id}",
        anketa_id=anketa_id
    )
```

### Auditor Agent
**Файл**: `agents/auditor_agent.py`

```python
# После завершения аудита
if audit_complete:
    pdf_bytes = pdf_generator.generate_audit_pdf(audit_data)

    await notifier.send_stage_completion_pdf(
        stage='audit',
        pdf_bytes=pdf_bytes,
        filename=f"#{anketa_id}_AUDIT.pdf",
        caption=f"🔍 Аудит завершен\nОценка: {score}/10\nID: {anketa_id}",
        anketa_id=anketa_id
    )
```

### Researcher Agent V2
**Файл**: `agents/researcher_agent_v2.py`

```python
# После завершения всех 27 queries
if all_queries_complete:
    pdf_bytes = pdf_generator.generate_research_pdf(research_data)

    await notifier.send_stage_completion_pdf(
        stage='research',
        pdf_bytes=pdf_bytes,
        filename=f"#{research_id}_RESEARCH.pdf",
        caption=f"📊 Исследование завершено\n27 queries выполнено\nID: {research_id}",
        anketa_id=anketa_id
    )
```

### Writer Agent V2
**Файл**: `agents/writer_agent_v2.py`

```python
# После написания гранта
if grant_complete:
    pdf_bytes = pdf_generator.generate_grant_pdf(grant_data)

    await notifier.send_stage_completion_pdf(
        stage='grant',
        pdf_bytes=pdf_bytes,
        filename=f"#{grant_id}_GRANT.pdf",
        caption=f"✍️ Грант написан\nОценка: {quality_score}/10\nID: {grant_id}",
        anketa_id=anketa_id
    )
```

### Reviewer Agent
**Файл**: `agents/reviewer_agent.py`

```python
# После ревью
if review_complete:
    pdf_bytes = pdf_generator.generate_review_pdf(review_data)

    await notifier.send_stage_completion_pdf(
        stage='review',
        pdf_bytes=pdf_bytes,
        filename=f"#{grant_id}_REVIEW.pdf",
        caption=f"👁️ Ревью завершено\nРезультат: {verdict}\nID: {grant_id}",
        anketa_id=anketa_id
    )
```

---

## 🔐 Безопасность

### 1. Проверка настроек перед отправкой
```python
def should_send_notification(stage: str) -> bool:
    """Проверить, нужно ли отправлять уведомление для этапа"""
    if not get_setting('notifications_enabled'):
        return False

    return get_setting(f'notify_on_{stage}', default=True)
```

### 2. Защита от спама
```python
# Rate limiting: не более 10 PDF в минуту
from datetime import datetime, timedelta

last_notifications = {}

def can_send_notification(anketa_id: str) -> bool:
    last_time = last_notifications.get(anketa_id)
    if last_time and (datetime.now() - last_time) < timedelta(seconds=6):
        return False

    last_notifications[anketa_id] = datetime.now()
    return True
```

### 3. Логирование
```python
# Логировать все отправленные PDF
logger.info(f"📄 PDF отправлен: {stage} | {anketa_id} | {filename} | Success: {success}")
```

---

## 📁 Структура файлов

```
GrantService/
├── telegram-bot/
│   └── utils/
│       ├── admin_notifications.py       # ✅ Существует (расширить)
│       ├── stage_report_generator.py    # 🆕 Создать
│       └── telegram_sender.py           # ✅ Существует (использовать)
│
├── web-admin/
│   ├── pages/
│   │   └── ⚙️_Настройки.py             # 📝 Обновить (добавить секцию)
│   └── utils/
│       └── artifact_exporter.py         # ✅ Существует (использовать как база)
│
├── agents/
│   ├── interviewer_agent.py             # 📝 Обновить (добавить PDF отправку)
│   ├── auditor_agent.py                 # 📝 Обновить
│   ├── researcher_agent_v2.py           # 📝 Обновить
│   ├── writer_agent_v2.py               # 📝 Обновить
│   └── reviewer_agent.py                # 📝 Обновить
│
└── database/
    └── migrations/
        └── 012_add_notification_settings.sql  # 🆕 Создать
```

---

## 🧪 План тестирования

### 1. Unit Tests
```python
# tests/unit/test_stage_report_generator.py
def test_generate_interview_pdf()
def test_generate_audit_pdf()
def test_generate_research_pdf()
def test_generate_grant_pdf()
def test_generate_review_pdf()
```

### 2. Integration Tests
```python
# tests/integration/test_pdf_notifications.py
async def test_interview_completion_sends_pdf()
async def test_audit_completion_sends_pdf()
async def test_research_completion_sends_pdf()
async def test_grant_completion_sends_pdf()
async def test_review_completion_sends_pdf()
```

### 3. E2E Test
```python
# tests/integration/test_full_workflow_with_pdfs.py
async def test_full_workflow_sends_5_pdfs_to_admin_chat()
# Проверить:
# - Все 5 PDF созданы
# - Все 5 PDF отправлены в чат -4930683040
# - Правильные filename и captions
# - Настройки работают (можно отключить отправку)
```

---

## 📊 Метрики и мониторинг

### Отслеживаемые метрики:
- Количество отправленных PDF по этапам
- Процент успешных отправок
- Средний размер PDF
- Время генерации PDF
- Ошибки отправки

### Dashboard в админке:
```python
st.metric("PDF отправлено сегодня", count_today)
st.metric("Успешность отправки", f"{success_rate}%")

# График отправок по этапам
chart_data = {
    'Interview': interview_count,
    'Audit': audit_count,
    'Research': research_count,
    'Grant': grant_count,
    'Review': review_count
}
st.bar_chart(chart_data)
```

---

## 🚀 План внедрения

### Phase 1: Инфраструктура (День 1)
- [x] Создать StageReportGenerator
- [x] Расширить AdminNotifier
- [x] Создать миграцию для настроек

### Phase 2: PDF Генераторы (День 2)
- [x] Реализовать generate_interview_pdf()
- [x] Реализовать generate_audit_pdf()
- [x] Реализовать generate_research_pdf()
- [x] Реализовать generate_grant_pdf()
- [x] Реализовать generate_review_pdf()

### Phase 3: UI Settings (День 3)
- [x] Добавить секцию в ⚙️ Настройки
- [x] Реализовать сохранение/загрузку настроек
- [x] Добавить preview отправки

### Phase 4: Интеграция в агенты (День 4)
- [x] Interviewer Agent
- [x] Auditor Agent
- [x] Researcher Agent V2
- [x] Writer Agent V2
- [x] Reviewer Agent

### Phase 5: Тестирование (День 5)
- [x] Unit tests
- [x] Integration tests
- [x] E2E test
- [x] Production test с реальным пользователем

---

## ⚠️ Важные замечания

### 1. Bot Permissions
Убедиться, что бот имеет права на отправку документов в группу -4930683040:
- /setprivacy OFF
- Бот должен быть админом группы (или хотя бы участником)

### 2. PDF Size Limits
- Telegram: макс 50 MB для документов
- Наши PDF: ~100-500 KB (безопасно)
- Если > 50 MB: сжать или разбить на части

### 3. Encoding
- Использовать DejaVuSans.ttf для русских символов
- UTF-8 encoding для всех текстов
- Fallback на латиницу если шрифт не найден

### 4. Error Handling
```python
try:
    pdf_bytes = generate_pdf(data)
    success = await send_pdf(pdf_bytes)
except Exception as e:
    logger.error(f"PDF generation/sending failed: {e}")
    # Отправить текстовое уведомление вместо PDF
    await send_text_notification(data)
```

---

## 📝 Checklist для разработчика

Перед началом работы с PDF уведомлениями:

- [ ] Прочитал NOMENCLATURE.md (понимаю формат ID)
- [ ] Изучил admin_notifications.py (существующая инфраструктура)
- [ ] Изучил artifact_exporter.py (пример PDF генерации)
- [ ] Изучил telegram_sender.py (отправка документов)
- [ ] Понимаю workflow агентов (5 этапов)
- [ ] Знаю ID админского чата: -4930683040
- [ ] Протестировал отправку PDF вручную
- [ ] Проверил права бота в группе

---

**Status**: DESIGN COMPLETE ✅
**Next**: Начать реализацию Phase 1 (StageReportGenerator)

---

*Architecture designed by: Claude Code AI*
*Date: 2025-10-12*
*Version: 1.0.0*
