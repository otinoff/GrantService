# 📋 Planned Sessions - Backlog для GrantService

**Назначение:** Хранилище идей и планов для будущих итераций проекта

**Философия нумерации:**
- **Iterations (1-999):** Реальная работа (что сделано/делается)
- **Sessions (1000+):** Backlog планов (что можно сделать в будущем)

**Процесс выбора:**
1. Есть идея → Создаём Session 100X
2. Решили делать → Переносим в Iteration N
3. Сделали → Iteration N = DONE
4. Следующая → Выбираем из Sessions

---

## 📊 Статус

**Всего планов:** 3
**В работе:** 0
**Следующая Iteration:** 27 (выбрать из Sessions)

---

## 🎯 Приоритизация

### 🔥 URGENT (делать немедленно)
| Session | Название | Impact | Время | Deadline |
|---------|----------|--------|-------|----------|
| **1003** | **GigaChat Bootcamp** | HIGH | 2h + week | **2025-10-30** (оценка!) |

### ⚡ HIGH (важно, но не срочно)
| Session | Название | Impact | Время | Reason |
|---------|----------|--------|-------|--------|
| **1001** | **Haiku Optimization** | HIGH | 4h | User feedback: "медленновато" |

### 📌 MEDIUM (когда будет время)
| Session | Название | Impact | Время | Reason |
|---------|----------|--------|-------|--------|
| 1002 | Question Prefetching | MEDIUM | 6h | Альтернатива Session 1001 |

---

## 📚 Index всех планов

### Session 1001: Haiku Optimization ⚡
**Файл:** `1001_Haiku_Optimization/00_Plan.md`

**Цель:**
Ускорить интервьюер в 3-4 раза через переход на Haiku + упрощение архитектуры

**Проблема:**
- Вопросы генерируются 5-8 секунд
- User feedback: "медленновато вопросы идут"
- Дорого (~$0.02 на вопрос)

**Решение:**
- Переход с Sonnet 4.5 на Haiku 3.5
- Убрать Qdrant из hot path (статичная структура в промпте)
- Оптимизировать промпты под Haiku

**Результаты:**
- Latency: 5-8s → 1.5-2s (**-60-75%**)
- Cost: $0.02 → $0.002 (**-90%**)
- Архитектура: проще, легче поддерживать

**Время:** 4 часа
**Приоритет:** HIGH
**Риск:** LOW-MEDIUM

**Связанные документы:**
- `ITERATION_26.3_COMPLETE_SUMMARY.md` - текущее состояние
- `Architecture_Analysis_Question_Generation.md` - текущая архитектура

---

### Session 1002: Question Prefetching 🔄
**Файл:** `1002_Question_Prefetching/00_Plan.md`

**Цель:**
Улучшить качество вопросов через расширение Qdrant corpus (100 → 1000+)

**Проблема:**
- 100 примеров вопросов в Qdrant - недостаточно
- Ограниченное разнообразие
- Не все edge cases покрыты

**Решение:**
- Проанализировать 100+ успешных FPG грантов
- Извлечь 500+ новых вопросов
- Загрузить в Qdrant с metadata
- Тестирование quality improvement

**Результаты:**
- Quality: +25% overall improvement
- Diversity: +35% (no repetition)
- Edge cases: +30% better handling
- Latency: +200ms (acceptable)

**Время:** 6 часов (5 фаз)
**Приоритет:** MEDIUM
**Риск:** LOW

**Note:** Альтернатива Session 1001. Можно:
- Делать Session 1001 (Haiku) вместо этого
- Или делать оба (сначала 1001, потом 1002)

---

### Session 1003: GigaChat Bootcamp 🚀
**Файл:** `1003_GigaChat_Bootcamp/00_Plan.md`

**Цель:**
Переключиться на GigaChat для участия в Sber500 буткэмпе и накопить статистику использования токенов

**Контекст:**
- Участвуем в Sber500 x GigaChat Bootcamp
- **Оценка через неделю (2025-10-30) по количеству использованных токенов**
- Нужно показать СБеру: сколько токенов используем и для каких целей
- Партнер: Наталья Брызгина

**Задачи:**
1. Промониторить победившие проекты Сбер500 прошлый год
2. Сделать прогоны заявок используя токены GigaChat
3. Отправить заявки в чат буткэмпа

**Решение (3 фазы):**

**Phase 1: Switch to GigaChat (30 мин)**
- Проверить GigaChat credentials
- Переключить всех users на GigaChat в БД
- Тест в Telegram

**Phase 2: Token Tracking (1 час)**
- Создать таблицу `gigachat_usage_log`
- Добавить логирование токенов в UnifiedLLMClient
- Тестирование tracking

**Phase 3: Statistics (30 мин)**
- Создать SQL queries для analytics
- Python скрипт генерации отчётов
- Первый отчёт для буткэмпа

**Результаты:**
- Week 1: 50,000-100,000 токенов использовано
- 10-20 грантовых заявок создано
- 4 агента задействовано (Interviewer, Writer, Researcher, Reviewer)
- Статистика для оценки комиссией

**Время:** 2 часа setup + неделя data collection
**Приоритет:** URGENT (deadline через неделю!)
**Риск:** LOW-MEDIUM

**Важно:**
- ✅ Инфраструктура уже готова (UnifiedLLMClient поддерживает GigaChat)
- ✅ База данных имеет `preferred_llm_provider`
- ✅ Нужно только: переключить users + добавить tracking

**Связанные документы:**
- `01_Projects/2025-10-20_Bootcamp_GrantService/` - детали буткэмпа
- Platform: http://sber500.2080vc.io

---

## 🎯 Рекомендация для Iteration 27

### Вариант А: Session 1003 (GigaChat) - РЕКОМЕНДУЮ! 🔥

**Почему:**
- ⚠️ СРОЧНО: оценка через неделю (2025-10-30)
- ✅ Быстрая реализация: 2 часа setup
- ✅ Инфраструктура готова
- ✅ Business impact: проход в следующий этап буткэмпа
- 📊 Накопим статистику за неделю

**Timeline:**
- **Сегодня:** Setup (2 часа)
- **Days 2-6:** Data collection (20-30 интервью)
- **Day 7:** Финальный отчёт + оценка

**After bootcamp:**
- Можно сделать Session 1001 (Haiku) для long-term optimization
- Или вернуться на Claude

---

### Вариант Б: Session 1001 (Haiku)

**Почему:**
- User feedback: "медленновато"
- Long-term optimization
- Дешевле и быстрее

**Но:**
- ❌ Не срочно (можно сделать после буткэмпа)
- ⏰ 4 часа работы vs 2 часа для GigaChat

---

### Вариант В: Оба параллельно

**Timeline:**
1. **Сегодня:** Session 1003 setup (2 часа)
2. **Завтра:** Session 1001 Haiku (4 часа)
3. **Days 3-7:** Data collection GigaChat

**Результат:**
- ✅ Быстрый интервьюер (Haiku)
- ✅ Статистика для буткэмпа (GigaChat)
- ✅ Оба улучшения done!

---

## 📊 Критерии выбора Session

При выборе следующей Session учитывай:

### 1. Срочность (Urgency)
- **URGENT:** Есть deadline (Session 1003 - неделя!)
- **HIGH:** User complaints, production issues
- **MEDIUM:** Nice to have, optimization
- **LOW:** Future ideas

### 2. Бизнес-impact (Impact)
- **HIGH:** Влияет на revenue, user satisfaction
- **MEDIUM:** Улучшает quality, снижает cost
- **LOW:** Internal improvements

### 3. Сложность (Complexity)
- **LOW:** 1-2 часа, простая задача
- **MEDIUM:** 4-6 часов, несколько компонентов
- **HIGH:** Несколько дней, много зависимостей

### 4. Зависимости (Dependencies)
- Нужны ли другие Sessions перед этим?
- Блокирует ли другие Sessions?

### 5. ROI (Return on Investment)
- Время реализации vs польза
- Cost savings
- User satisfaction improvement

---

## 🔄 Workflow: От Session к Iteration

### Процесс выбора:

```
1. Анализ Sessions
   ├─ Проверить приоритеты
   ├─ Оценить сроки
   └─ Обсудить с командой

2. Выбрать Session
   ├─ Решение: делаем Session 100X
   └─ Создать Iteration N

3. Реализация
   ├─ Скопировать план из Session 100X
   ├─ Создать Iteration_N_Name/
   │  ├─ 00_Plan.md (из Session)
   │  ├─ 01_Implementation_Report.md
   │  └─ 02_Final_Report.md
   └─ Начать работу

4. Завершение
   ├─ Iteration N = DONE
   ├─ Session 100X = IMPLEMENTED
   └─ Выбрать следующую Session
```

---

## 📝 Добавление новых Sessions

### Как добавить новую идею:

1. **Определить номер:** Следующий свободный (1004, 1005, ...)
2. **Создать директорию:** `100X_Session_Name/`
3. **Создать план:** `00_Plan.md`
4. **Обновить README:** Добавить в Index
5. **Приоритизировать:** Указать URGENT/HIGH/MEDIUM/LOW

### Template для нового плана:

```markdown
# Session 100X: Название

**Дата создания:** YYYY-MM-DD
**Статус:** PLANNED
**Приоритет:** HIGH/MEDIUM/LOW

## Цель
[Что хотим достичь]

## Проблема
[Текущая ситуация, что не так]

## Решение
[Как будем решать]

## Результаты
[Ожидаемые метрики]

## Время
[Оценка времени реализации]

## Риски
[Что может пойти не так]

## Зависимости
[Нужны ли другие Sessions перед этим]
```

---

## 🗂️ Структура директории

```
Strategy/03_Planned_Sessions/
├── README.md                       (этот файл - главный индекс)
│
├── 1001_Haiku_Optimization/
│   └── 00_Plan.md                  (⚡ HIGH: -60% latency, -90% cost)
│
├── 1002_Question_Prefetching/
│   └── 00_Plan.md                  (📌 MEDIUM: +25% quality)
│
├── 1003_GigaChat_Bootcamp/
│   └── 00_Plan.md                  (🔥 URGENT: deadline 2025-10-30!)
│
└── [Future Sessions 1004+...]
```

---

## 📞 Quick Reference

**Текущая Iteration:** 26.3 (DONE - V2 Interview UX Fixed)
**Следующая Iteration:** 27 (выбрать из Sessions)
**Рекомендация:** Session 1003 (GigaChat - URGENT!)

**Документы:**
- Все Iterations: `Development/02_Feature_Development/Interviewer_Iterations/`
- Все Sessions: `Strategy/03_Planned_Sessions/` (этот раздел)
- Version 1.0: `Versions/Version_1.0_2025-10-23/`

**Индексы:**
- INTERVIEWER_ITERATION_INDEX.md - история всех итераций
- DEPLOYMENT_INDEX.md - история деплоев
- VERSION_1.0_SUMMARY.md - краткая сводка v1.0

---

## 💡 Идеи для будущих Sessions (1004+)

### Интервьюер:
- Session 1004: Streaming responses (показывать текст по мере генерации)
- Session 1005: Smart caching (кешировать частые вопросы)
- Session 1006: Multi-language support (English, другие языки)

### Качество:
- Session 1007: User feedback loop (рейтинг вопросов)
- Session 1008: A/B testing framework
- Session 1009: Fine-tune LLM on FPG data

### Инфраструктура:
- Session 1010: Production venv improvements
- Session 1011: Automated deployment pipeline
- Session 1012: Monitoring dashboard

### Бизнес:
- Session 1013: Team collaboration features
- Session 1014: Multi-fund support (не только ФПГ)
- Session 1015: API for integrations

---

## 🎯 Следующие шаги

1. **Выбрать Session для Iteration 27:**
   - Рекомендация: Session 1003 (GigaChat - URGENT!)
   - Альтернатива: Session 1001 (Haiku - HIGH)

2. **Создать Iteration 27:**
   ```bash
   mkdir Development/02_Feature_Development/Interviewer_Iterations/Iteration_27_[Name]/
   cp Strategy/03_Planned_Sessions/100X_[Name]/00_Plan.md → Iteration_27/
   ```

3. **Начать работу!** 🚀

---

**Создано:** 2025-10-23
**Автор:** Claude Code AI Assistant
**Версия:** 1.0
**Статус:** ACTIVE BACKLOG

**Всего Sessions:** 3
**Следующий номер:** 1004

🎯 **Готов выбрать Session и начать Iteration 27!**
