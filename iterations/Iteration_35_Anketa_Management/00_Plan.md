# Iteration 35: Anketa Management & Quality Control

**Created:** 2025-10-25
**Type:** Feature Enhancement + Quality Control
**Priority:** P0 - CRITICAL
**Methodology:** Cradle OS - Гомеостаз (Testing), Иммунитет (Quality Control)
**Estimated Time:** 4-6 hours (local development + testing)

---

## 🧬 МЕТОДОЛОГИЯ CRADLE

### Применяемые принципы:

**1. Гомеостаз (Automated Testing):**
- ✅ Тесты ПЕРЕД deployment
- ✅ Локальная разработка и тестирование
- ✅ Pre-Deploy Checklist обязателен

**2. Иммунитет (Quality Control):**
- ✅ Auditor интеграция
- ✅ Проверка качества перед генерацией
- ✅ User feedback на каждом этапе

**3. Метаболизм (Continuous Integration):**
- ✅ Малые частые изменения
- ✅ 4 команды = 4 малых фичи
- ✅ Поэтапное внедрение

---

## 🎯 ПРОБЛЕМА

### Текущая ситуация:

**Пример:** Анкета #AN-20251007-theperipherals-005
```json
{
    "links": "фывафыва",
    "tasks": "фывафыва",
    "budget": "фывафыва",
    ...все поля - тестовый мусор
}
```

**Проблемы:**
1. ❌ User не может посмотреть свои анкеты
2. ❌ User не может удалить тестовые анкеты
3. ❌ User не знает качество своей анкеты ДО генерации гранта
4. ❌ Нет механизма проверки анкеты перед генерацией
5. ❌ Генерация гранта на мусорных данных = waste resources

---

## 🎯 РЕШЕНИЕ

### 4 новые команды для Telegram бота:

#### 1. `/my_anketas` - Список анкет пользователя

**Функционал:**
- Показать все анкеты пользователя
- Отобразить статус каждой анкеты
- Показать дату создания
- Кнопки для действий (Audit, Delete, Generate Grant)

**UI:**
```
📋 Ваши анкеты:

1. #AN-20251007-theperipherals-005
   📅 Создано: 2025-10-07
   ✅ Статус: completed
   🎯 Проект: [название из project_essence]

   [🔍 Аудит] [🗑️ Удалить] [📝 Грант]

2. #AN-20251008-another-002
   📅 Создано: 2025-10-08
   ⏳ Статус: in_progress

   [➡️ Продолжить]

─────────────
Всего: 2 анкеты
```

---

#### 2. `/delete_anketa` - Удаление анкеты

**Функционал:**
- Выбор анкеты для удаления (inline buttons)
- Подтверждение удаления (да/нет)
- Проверка прав (только владелец может удалить)
- Cascade delete связанных данных (audit, grants)

**UI Flow:**
```
User: /delete_anketa

Bot: Выберите анкету для удаления:

[#AN-20251007-theperipherals-005] (2025-10-07)
[#AN-20251008-another-002] (2025-10-08)

User: [clicks first]

Bot: ⚠️ Вы уверены что хотите удалить анкету?

📋 #AN-20251007-theperipherals-005
📅 Создано: 2025-10-07
🎯 Проект: [название]

Будут также удалены:
• Аудит (если есть)
• Грантовая заявка (если есть)
• Все связанные данные

[✅ Да, удалить] [❌ Отмена]

User: [clicks Да]

Bot: ✅ Анкета #AN-20251007-theperipherals-005 удалена
```

---

#### 3. `/audit_anketa` - Аудит качества анкеты

**Функционал:**
- Выбор анкеты для аудита (inline buttons)
- Запуск AuditorAgent
- Показ результатов аудита
- Рекомендации по улучшению
- Заключение: годна для гранта или нет

**UI Flow:**
```
User: /audit_anketa

Bot: Выберите анкету для аудита:

[#AN-20251007-theperipherals-005] (2025-10-07)
[#AN-20251008-another-002] (2025-10-08)

User: [clicks first]

Bot: 🔍 Запускаю аудит анкеты...
⏱ Это займет ~30 секунд

Bot: ✅ Аудит завершен!

📊 Результаты аудита:
━━━━━━━━━━━━━━━━━━━━━

Анкета: #AN-20251007-theperipherals-005

📈 Оценки по критериям:
• Полнота информации: 3/10 ⚠️
• Ясность описания: 2/10 ❌
• Реалистичность: 1/10 ❌
• Инновационность: 1/10 ❌
• Качество: 2/10 ❌

📊 Общая оценка: 1.8/10

━━━━━━━━━━━━━━━━━━━━━

⛔ ЗАКЛЮЧЕНИЕ: Анкета НЕ ГОТОВА для генерации гранта

🔴 Статус: ОТКЛОНЕНА (rejected)

📋 Основные проблемы:

1. Поля заполнены тестовыми данными ("фывафыва")
2. Отсутствует описание проблемы
3. Не указаны конкретные задачи
4. Нет информации о бюджете
5. Не описана целевая аудитория

💡 Рекомендации:

1. Заполните все поля осмысленной информацией
2. Опишите социальную проблему которую решает проект
3. Укажите конкретные мероприятия и задачи
4. Добавьте реалистичный бюджет
5. Определите целевую аудиторию

━━━━━━━━━━━━━━━━━━━━━

🔄 Действия:
[📝 Редактировать анкету] [🗑️ Удалить] [⬅️ Назад]
```

**Если аудит положительный:**
```
✅ ЗАКЛЮЧЕНИЕ: Анкета ГОТОВА для генерации гранта

🟢 Статус: ОДОБРЕНА (approved)

📊 Общая оценка: 8.5/10

✨ Сильные стороны:
1. Четкое описание проблемы
2. Реалистичный план мероприятий
3. Обоснованный бюджет
4. Хорошо описана целевая аудитория

💡 Можно улучшить:
1. Добавить больше деталей об инновационности
2. Усилить описание партнеров

🚀 Действия:
[📝 Генерировать грант] [🔍 Подробнее] [⬅️ Назад]
```

---

#### 4. Integration: Audit check в `/generate_grant`

**Функционал:**
- Автоматическая проверка аудита перед генерацией
- Если нет аудита → предложить запустить
- Если аудит rejected → блокировать генерацию
- Если аудит needs_revision → предупредить, но разрешить
- Если аудит approved → продолжить генерацию

**UI Flow:**
```
User: /generate_grant

Bot: 🔍 Проверяю качество анкеты...

Case 1: Нет аудита
Bot: ⚠️ Анкета еще не проверена

Рекомендую сначала запустить аудит качества.
Это поможет избежать генерации некачественной заявки.

[🔍 Запустить аудит] [➡️ Продолжить без аудита]

Case 2: Аудит rejected (score < 5.0)
Bot: ❌ Анкета не прошла проверку качества

📊 Оценка: 1.8/10 (минимум 5.0)
🔴 Статус: ОТКЛОНЕНА

Генерация гранта невозможна.
Пожалуйста, улучшите анкету.

[🔍 Посмотреть рекомендации] [📝 Редактировать]

Case 3: Аудит needs_revision (5.0 <= score < 7.0)
Bot: ⚠️ Анкета требует доработки

📊 Оценка: 6.2/10
🟡 Статус: ТРЕБУЕТ ДОРАБОТКИ

Можно генерировать грант, но результат может быть не идеальным.

[🔍 Посмотреть рекомендации] [📝 Улучшить] [➡️ Продолжить]

Case 4: Аудит approved (score >= 7.0)
Bot: ✅ Качество анкеты: 8.5/10 - отлично!
🚀 Начинаю генерацию грантовой заявки...
```

---

## 📝 IMPLEMENTATION PLAN

### Phase 1: Database Methods (1 час)

**File:** `data/database/models.py`

**New methods:**

```python
def get_user_anketas(self, telegram_id: int, limit: int = 10) -> List[Dict]:
    """Get all anketas for user"""
    try:
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    s.anketa_id,
                    s.project_name,
                    s.completion_status,
                    s.started_at,
                    s.completed_at,
                    s.questions_answered,
                    s.total_questions,
                    s.progress_percentage,
                    -- Check if audit exists
                    EXISTS(
                        SELECT 1 FROM auditor_results ar
                        WHERE ar.session_id = s.id
                    ) as has_audit,
                    -- Get audit score if exists
                    (
                        SELECT ar.average_score
                        FROM auditor_results ar
                        WHERE ar.session_id = s.id
                        ORDER BY ar.created_at DESC
                        LIMIT 1
                    ) as audit_score,
                    -- Get audit status if exists
                    (
                        SELECT ar.approval_status
                        FROM auditor_results ar
                        WHERE ar.session_id = s.id
                        ORDER BY ar.created_at DESC
                        LIMIT 1
                    ) as audit_status,
                    -- Check if grant exists
                    EXISTS(
                        SELECT 1 FROM grants g
                        WHERE g.anketa_id = s.anketa_id
                    ) as has_grant
                FROM sessions s
                WHERE s.telegram_id = %s
                ORDER BY s.started_at DESC
                LIMIT %s
            """, (telegram_id, limit))

            rows = cursor.fetchall()
            cursor.close()

            return [self._dict_row(cursor, row) for row in rows]

    except Exception as e:
        logger.error(f"Error getting user anketas: {e}")
        return []


def delete_anketa(self, anketa_id: str, telegram_id: int) -> bool:
    """
    Delete anketa and all related data
    CASCADE delete: audit, grants, etc.
    Only owner can delete
    """
    try:
        with self.connect() as conn:
            cursor = conn.cursor()

            # Verify ownership
            cursor.execute("""
                SELECT id FROM sessions
                WHERE anketa_id = %s AND telegram_id = %s
            """, (anketa_id, telegram_id))

            session = cursor.fetchone()
            if not session:
                logger.warning(f"User {telegram_id} tried to delete anketa {anketa_id} - not owner")
                return False

            # Delete session (CASCADE will delete related data)
            cursor.execute("""
                DELETE FROM sessions
                WHERE anketa_id = %s AND telegram_id = %s
            """, (anketa_id, telegram_id))

            conn.commit()
            cursor.close()

            deleted_count = cursor.rowcount
            logger.info(f"Deleted anketa {anketa_id} for user {telegram_id}, rows: {deleted_count}")

            return deleted_count > 0

    except Exception as e:
        logger.error(f"Error deleting anketa: {e}")
        return False


def get_audit_by_session_id(self, session_id: int) -> Optional[Dict]:
    """Get latest audit for session"""
    try:
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM auditor_results
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (session_id,))

            row = cursor.fetchone()
            cursor.close()

            return self._dict_row(cursor, row) if row else None

    except Exception as e:
        logger.error(f"Error getting audit: {e}")
        return None


def get_audit_by_anketa_id(self, anketa_id: str) -> Optional[Dict]:
    """Get latest audit for anketa"""
    try:
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT ar.* FROM auditor_results ar
                JOIN sessions s ON ar.session_id = s.id
                WHERE s.anketa_id = %s
                ORDER BY ar.created_at DESC
                LIMIT 1
            """, (anketa_id,))

            row = cursor.fetchone()
            cursor.close()

            return self._dict_row(cursor, row) if row else None

    except Exception as e:
        logger.error(f"Error getting audit by anketa_id: {e}")
        return None
```

---

### Phase 2: Telegram Bot Handlers (2-3 часа)

**File:** `telegram-bot/handlers/anketa_management_handler.py` (NEW FILE)

```python
#!/usr/bin/env python3
"""
Anketa Management Handler
Commands: /my_anketas, /delete_anketa, /audit_anketa
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnketaManagementHandler:
    def __init__(self, db):
        self.db = db

    async def my_anketas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's anketas"""
        user_id = update.effective_user.id

        # Get anketas
        anketas = self.db.get_user_anketas(user_id, limit=10)

        if not anketas:
            await update.message.reply_text(
                "📋 У вас пока нет анкет\n\n"
                "Создайте анкету командой /start"
            )
            return

        # Format message
        message = "📋 **Ваши анкеты:**\n\n"

        for i, anketa in enumerate(anketas, 1):
            anketa_id = anketa['anketa_id']
            project = anketa.get('project_name') or 'Без названия'
            status = anketa['completion_status']
            created = anketa['started_at'].strftime('%d.%m.%Y')

            # Status emoji
            status_emoji = {
                'completed': '✅',
                'in_progress': '⏳',
                'abandoned': '❌'
            }.get(status, '❓')

            message += f"{i}. {anketa_id}\n"
            message += f"   📅 {created}\n"
            message += f"   {status_emoji} {status}\n"

            if project != 'Без названия':
                message += f"   🎯 {project[:50]}...\n" if len(project) > 50 else f"   🎯 {project}\n"

            # Audit info
            if anketa.get('has_audit'):
                score = anketa.get('audit_score', 0)
                audit_status = anketa.get('audit_status', 'pending')

                audit_emoji = {
                    'approved': '🟢',
                    'needs_revision': '🟡',
                    'rejected': '🔴',
                    'pending': '⏳'
                }.get(audit_status, '❓')

                message += f"   {audit_emoji} Аудит: {score}/10 ({audit_status})\n"

            # Grant info
            if anketa.get('has_grant'):
                message += f"   📝 Грант: готов\n"

            message += "\n"

        message += "─────────────\n"
        message += f"Всего: {len(anketas)} анкет(ы)"

        # Inline buttons для первых 3-х анкет
        keyboard = []
        for anketa in anketas[:3]:
            anketa_id = anketa['anketa_id']
            row = [
                InlineKeyboardButton(f"🔍 Аудит {anketa_id}", callback_data=f"audit_{anketa_id}"),
                InlineKeyboardButton(f"🗑️ Удалить", callback_data=f"delete_{anketa_id}")
            ]
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


    async def delete_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete anketa command"""
        user_id = update.effective_user.id

        # Get anketas
        anketas = self.db.get_user_anketas(user_id, limit=10)

        if not anketas:
            await update.message.reply_text("📋 У вас нет анкет для удаления")
            return

        # Show selection
        message = "🗑️ **Выберите анкету для удаления:**\n\n"

        keyboard = []
        for anketa in anketas:
            anketa_id = anketa['anketa_id']
            project = anketa.get('project_name') or 'Без названия'
            created = anketa['started_at'].strftime('%d.%m.%Y')

            button_text = f"{anketa_id} ({created})"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"delete_confirm_{anketa_id}")
            ])

        keyboard.append([
            InlineKeyboardButton("❌ Отмена", callback_data="delete_cancel")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


    async def delete_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        """Confirm deletion"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        # Get anketa details
        anketas = self.db.get_user_anketas(user_id, limit=100)
        anketa = next((a for a in anketas if a['anketa_id'] == anketa_id), None)

        if not anketa:
            await query.message.reply_text("❌ Анкета не найдена")
            return

        # Confirmation message
        project = anketa.get('project_name') or 'Без названия'
        created = anketa['started_at'].strftime('%d.%m.%Y')

        message = f"⚠️ **Вы уверены что хотите удалить анкету?**\n\n"
        message += f"📋 {anketa_id}\n"
        message += f"📅 Создано: {created}\n"
        message += f"🎯 Проект: {project}\n\n"

        message += "Будут также удалены:\n"
        if anketa.get('has_audit'):
            message += "• Аудит\n"
        if anketa.get('has_grant'):
            message += "• Грантовая заявка\n"
        message += "• Все связанные данные\n"

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"delete_execute_{anketa_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data="delete_cancel")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')


    async def delete_execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        """Execute deletion"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        # Delete
        success = self.db.delete_anketa(anketa_id, user_id)

        if success:
            await query.message.edit_text(f"✅ Анкета {anketa_id} удалена")
            logger.info(f"[ANKETA] User {user_id} deleted anketa {anketa_id}")
        else:
            await query.message.edit_text(f"❌ Не удалось удалить анкету {anketa_id}")
            logger.error(f"[ANKETA] Failed to delete anketa {anketa_id} for user {user_id}")


    async def audit_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Audit anketa command"""
        user_id = update.effective_user.id

        # Get completed anketas
        all_anketas = self.db.get_user_anketas(user_id, limit=10)
        anketas = [a for a in all_anketas if a['completion_status'] == 'completed']

        if not anketas:
            await update.message.reply_text(
                "📋 У вас нет завершенных анкет\n\n"
                "Завершите анкету чтобы запустить аудит"
            )
            return

        # Show selection
        message = "🔍 **Выберите анкету для аудита:**\n\n"

        keyboard = []
        for anketa in anketas:
            anketa_id = anketa['anketa_id']
            project = anketa.get('project_name') or 'Без названия'
            created = anketa['started_at'].strftime('%d.%m.%Y')

            # Check if already audited
            if anketa.get('has_audit'):
                score = anketa.get('audit_score', 0)
                button_text = f"{anketa_id} (Аудит: {score}/10) - Повторить"
            else:
                button_text = f"{anketa_id} ({created})"

            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"audit_run_{anketa_id}")
            ])

        keyboard.append([
            InlineKeyboardButton("❌ Отмена", callback_data="audit_cancel")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


    async def audit_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        """Run audit on anketa"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        # Get anketa data
        session = self.db.get_session_by_anketa_id(anketa_id)
        if not session:
            await query.message.reply_text("❌ Анкета не найдена")
            return

        # Verify ownership
        if session['telegram_id'] != user_id:
            await query.message.reply_text("❌ Это не ваша анкета")
            return

        # Get interview data
        anketa_data = session.get('interview_data')
        if not anketa_data:
            await query.message.reply_text("❌ Нет данных анкеты")
            return

        # Show progress
        await query.message.edit_text(
            f"🔍 Запускаю аудит анкеты {anketa_id}...\n"
            "⏱ Это займет ~30 секунд"
        )

        # Import and run auditor
        try:
            from agents.auditor_agent import AuditorAgent
            import asyncio

            # Get LLM preference
            llm_provider = self.db.get_user_llm_preference(user_id)

            # Create auditor
            auditor = AuditorAgent(self.db, llm_provider=llm_provider)

            # Run audit
            audit_result = await asyncio.to_thread(
                auditor.audit,
                anketa_data=anketa_data,
                session_id=session['id']
            )

            # Format result message
            message = self._format_audit_result(audit_result, anketa_id)

            # Buttons
            keyboard = [
                [
                    InlineKeyboardButton("📝 Генерировать грант", callback_data=f"generate_{anketa_id}"),
                    InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_confirm_{anketa_id}")
                ],
                [
                    InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_anketas")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')

            logger.info(f"[AUDIT] User {user_id} audited anketa {anketa_id}, score: {audit_result.get('average_score')}")

        except Exception as e:
            logger.error(f"[AUDIT] Error running audit: {e}")
            await query.message.edit_text(f"❌ Ошибка при запуске аудита: {e}")


    def _format_audit_result(self, audit_result: dict, anketa_id: str) -> str:
        """Format audit result message"""
        score = audit_result.get('average_score', 0)
        status = audit_result.get('approval_status', 'pending')

        # Status emoji and title
        status_emoji = {
            'approved': '🟢',
            'needs_revision': '🟡',
            'rejected': '🔴',
            'pending': '⏳'
        }.get(status, '❓')

        status_title = {
            'approved': 'ОДОБРЕНА',
            'needs_revision': 'ТРЕБУЕТ ДОРАБОТКИ',
            'rejected': 'ОТКЛОНЕНА',
            'pending': 'НА РАССМОТРЕНИИ'
        }.get(status, 'НЕИЗВЕСТНО')

        message = "✅ **Аудит завершен!**\n\n"
        message += "📊 **Результаты аудита:**\n"
        message += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"Анкета: {anketa_id}\n\n"

        # Scores
        message += "📈 **Оценки по критериям:**\n"
        message += f"• Полнота информации: {audit_result.get('completeness_score', 0)}/10\n"
        message += f"• Ясность описания: {audit_result.get('clarity_score', 0)}/10\n"
        message += f"• Реалистичность: {audit_result.get('feasibility_score', 0)}/10\n"
        message += f"• Инновационность: {audit_result.get('innovation_score', 0)}/10\n"
        message += f"• Качество: {audit_result.get('quality_score', 0)}/10\n\n"

        message += f"📊 **Общая оценка: {score}/10**\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Conclusion
        if status == 'approved':
            message += f"{status_emoji} **ЗАКЛЮЧЕНИЕ: Анкета ГОТОВА для генерации гранта**\n\n"
            message += f"🟢 **Статус: {status_title}**\n\n"
        elif status == 'needs_revision':
            message += f"{status_emoji} **ЗАКЛЮЧЕНИЕ: Анкета требует улучшений**\n\n"
            message += f"🟡 **Статус: {status_title}**\n\n"
        else:  # rejected
            message += f"{status_emoji} **ЗАКЛЮЧЕНИЕ: Анкета НЕ ГОТОВА для генерации гранта**\n\n"
            message += f"🔴 **Статус: {status_title}**\n\n"

        # Recommendations
        recommendations = audit_result.get('recommendations', [])
        if recommendations:
            message += "💡 **Рекомендации:**\n\n"
            for i, rec in enumerate(recommendations[:5], 1):
                message += f"{i}. {rec}\n"
            message += "\n"

        message += "━━━━━━━━━━━━━━━━━━━━━\n"

        return message


    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        data = query.data

        if data.startswith("delete_confirm_"):
            anketa_id = data.replace("delete_confirm_", "")
            await self.delete_confirm(update, context, anketa_id)

        elif data.startswith("delete_execute_"):
            anketa_id = data.replace("delete_execute_", "")
            await self.delete_execute(update, context, anketa_id)

        elif data == "delete_cancel":
            await query.answer()
            await query.message.edit_text("❌ Удаление отменено")

        elif data.startswith("audit_run_"):
            anketa_id = data.replace("audit_run_", "")
            await self.audit_run(update, context, anketa_id)

        elif data == "audit_cancel":
            await query.answer()
            await query.message.edit_text("❌ Аудит отменен")

        elif data == "back_to_anketas":
            await query.answer()
            # Re-show anketas list
            await self.my_anketas(update, context)
```

---

### Phase 3: Integration in grant_handler.py (1 час)

**Add audit check before generation:**

```python
# In generate_grant method, BEFORE ProductionWriter

# Check audit
session_id = session['id']

await update.message.reply_text("🔍 Проверяю качество анкеты...")

audit = self.db.get_audit_by_session_id(session_id)

if not audit:
    # No audit - suggest running it
    keyboard = [
        [
            InlineKeyboardButton("🔍 Запустить аудит", callback_data=f"audit_run_{anketa_id}"),
            InlineKeyboardButton("➡️ Продолжить без аудита", callback_data=f"generate_force_{anketa_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚠️ **Анкета еще не проверена**\n\n"
        "Рекомендую сначала запустить аудит качества.\n"
        "Это поможет избежать генерации некачественной заявки.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return

# Check approval status
if audit['approval_status'] == 'rejected':
    # Blocked
    await update.message.reply_text(
        f"❌ **Анкета не прошла проверку качества**\n\n"
        f"📊 Оценка: {audit['average_score']}/10 (минимум 5.0)\n"
        f"🔴 Статус: ОТКЛОНЕНА\n\n"
        f"Генерация гранта невозможна.\n"
        f"Пожалуйста, улучшите анкету.\n\n"
        f"Используйте /audit_anketa чтобы посмотреть рекомендации",
        parse_mode='Markdown'
    )
    logger.warning(f"[GRANT] Blocked generation due to rejected audit: {anketa_id}")
    return

elif audit['approval_status'] == 'needs_revision':
    # Warning but allow
    keyboard = [
        [
            InlineKeyboardButton("🔍 Посмотреть рекомендации", callback_data=f"audit_run_{anketa_id}"),
            InlineKeyboardButton("➡️ Продолжить", callback_data=f"generate_force_{anketa_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚠️ **Анкета требует доработки**\n\n"
        f"📊 Оценка: {audit['average_score']}/10\n"
        f"🟡 Статус: ТРЕБУЕТ ДОРАБОТКИ\n\n"
        f"Можно генерировать грант, но результат может быть не идеальным.\n\n"
        f"Рекомендуем улучшить анкету перед генерацией.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    # Don't return - let user decide

else:  # approved
    await update.message.reply_text(
        f"✅ Качество анкеты: {audit['average_score']}/10 - отлично!\n"
        f"🚀 Начинаю генерацию грантовой заявки..."
    )

# Continue with ProductionWriter...
```

---

## 🧪 TESTING PLAN

### Phase 1: Unit Tests (1 час)

**File:** `tests/test_anketa_management.py`

```python
import pytest
from data.database.models import GrantServiceDatabase

def test_get_user_anketas():
    """Test getting user anketas"""
    db = GrantServiceDatabase()
    anketas = db.get_user_anketas(telegram_id=5032079932, limit=10)
    assert isinstance(anketas, list)
    if anketas:
        assert 'anketa_id' in anketas[0]
        assert 'completion_status' in anketas[0]

def test_delete_anketa():
    """Test deleting anketa"""
    # Create test anketa
    # Delete it
    # Verify deleted
    pass

def test_get_audit():
    """Test getting audit result"""
    db = GrantServiceDatabase()
    audit = db.get_audit_by_anketa_id('#AN-20251007-theperipherals-005')
    # Will be None since no audit exists
    assert audit is None or isinstance(audit, dict)
```

### Phase 2: Integration Tests (1 час)

**Manual testing:**

1. **Test /my_anketas:**
   - Run command
   - Verify list shows
   - Verify buttons work

2. **Test /delete_anketa:**
   - Run command
   - Select anketa
   - Confirm deletion
   - Verify deleted

3. **Test /audit_anketa:**
   - Run command
   - Select anketa
   - Wait for audit
   - Verify result shows

4. **Test /generate_grant with audit:**
   - Run on rejected anketa → Should block
   - Run on needs_revision anketa → Should warn
   - Run on approved anketa → Should proceed

---

## ✅ SUCCESS CRITERIA

- [ ] `/my_anketas` shows all user anketas
- [ ] `/delete_anketa` deletes with confirmation
- [ ] `/audit_anketa` runs audit and shows results
- [ ] `/generate_grant` checks audit before generation
- [ ] Rejected anketas blocked from generation
- [ ] All tests pass
- [ ] Pre-Deploy Checklist applied
- [ ] Deployed to production
- [ ] User tested successfully

---

## 📊 METRICS

### Expected Impact:

**Quality:**
- ✅ 100% anketas audited before grant generation
- ✅ 0% grants generated on garbage data
- ✅ User satisfaction +50% (better guidance)

**Usability:**
- ✅ User can manage anketas easily
- ✅ User knows quality BEFORE generation
- ✅ User gets clear recommendations

**Performance:**
- First audit: +30s
- Cached audit: +0.1s
- Overall: Positive (quality > speed)

---

## 🔄 DEVELOPMENT WORKFLOW (Методология Cradle)

### Step 1: Local Development (сегодня)
1. ✅ Написать код локально
2. ✅ Написать тесты
3. ✅ Запустить тесты
4. ✅ Исправить bugs
5. ✅ Документировать

### Step 2: Pre-Deploy Checklist (завтра?)
1. ✅ Code Review
2. ✅ Run all tests
3. ✅ Check database queries
4. ✅ Check integration points
5. ✅ Verify error handling

### Step 3: Deployment (после checklist)
1. ✅ Git commit
2. ✅ Git push
3. ✅ Deploy to production
4. ✅ Verify in logs
5. ✅ User testing

---

## 📝 FILE STRUCTURE

```
Development/02_Feature_Development/Interviewer_Iterations/Iteration_35_Anketa_Management/
├── 00_Plan.md (this file)
├── 01_Implementation/
│   ├── anketa_management_handler.py
│   ├── database_methods.py
│   └── grant_handler_integration.py
├── 02_Tests/
│   ├── test_anketa_management.py
│   ├── test_database_methods.py
│   └── test_integration.py
└── 03_Report.md (after completion)
```

---

## 🎯 NEXT ACTIONS

### Сейчас (локально):
1. Создать `anketa_management_handler.py`
2. Добавить методы в `models.py`
3. Написать тесты
4. Запустить локально
5. Протестировать все команды

### Завтра/следующая сессия:
1. Применить Pre-Deploy Checklist
2. Code review
3. Deploy to production
4. User testing
5. Собрать feedback

---

**Status:** READY TO DEVELOP
**Estimated Time:** 4-6 hours
**Methodology:** Cradle OS ✅
**Local Development:** YES ✅
**Tests Required:** YES ✅

---

🧬 **Grow Fast, Stay Healthy!**
