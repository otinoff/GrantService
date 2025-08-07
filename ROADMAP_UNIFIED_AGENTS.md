ram-bot# 
root@xkwmiregrh:/var/GrantService/telegram-bot# cd /var/GrantService && python3 -c "from data.database import db; db.insert_default_prompts()"
✅ Добавлено 6 промптов по умолчанию
root@xkwmiregrh:/var/GrantService# 
- [ ] Создание резервной копии
- [ ] Настройка git ветки для рефакторинга
- [ ] Установка CrewAI и зависимостей

#### **Результат:**
- Детальный план рефакторинга с агентами
- Резервная копия рабочей версии
- Готовая структура папок
- Установленные зависимости

---

### **ЭТАП 2: Расширение базы данных** 📊
**Время:** 1-2 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создать таблицы для агентов:
  ```sql
  CREATE TABLE agent_tasks (
      id INTEGER PRIMARY KEY,
      task_id VARCHAR(100) UNIQUE,
      agent_type VARCHAR(50),
      input_data TEXT,
      output_data TEXT,
      status VARCHAR(30) DEFAULT 'pending',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE agent_prompts (
      id INTEGER PRIMARY KEY,
      agent_type VARCHAR(50),
      prompt_text TEXT,
      version INTEGER DEFAULT 1,
      active BOOLEAN DEFAULT 1
  );
  ```
- [ ] Обновить существующие таблицы для поддержки агентов
- [ ] Создать миграционные скрипты

#### **Результат:**
- Таблицы для работы агентов
- Готовность к многоагентной архитектуре

---

### **ЭТАП 3: Создание базовой структуры** 📁
**Время:** 2-3 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание всех папок и файлов структуры
- [ ] Создание `__init__.py` файлов
- [ ] Настройка импортов между модулями
- [ ] Создание базовых классов для агентов
- [ ] Настройка конфигурации

#### **Файлы для создания:**
```
telegram-bot/
├── agents/__init__.py
├── crew/__init__.py
├── handlers/__init__.py
├── services/__init__.py
├── utils/__init__.py
├── config/__init__.py
└── tests/__init__.py
```

#### **Результат:**
- Готовая структура папок
- Базовые импорты настроены
- Можно начинать перенос кода

---

### **ЭТАП 4: Конфигурация и промпты** ⚙️
**Время:** 2-3 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание `config/settings.py` с настройками агентов
- [ ] Создание `config/constants.py` с константами
- [ ] Создание промптов для каждого агента:
  - **Interviewer Agent**: промпты для проведения интервью
  - **Researcher Agent**: промпты для исследования контекста
  - **Writer Agent**: промпты для создания заявки
  - **Auditor Agent**: промпты для анализа качества
- [ ] Настройка API ключей (Perplexity, ГигаЧат)

#### **Содержимое config/settings.py:**
```python
# Настройки бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

# Настройки агентов
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
GIGACHAT_API_KEY = os.getenv('GIGACHAT_API_KEY')

# Настройки CrewAI
CREWAI_MAX_RPM = 10
CREWAI_VERBOSE = True

# Настройки логирования
LOG_LEVEL = logging.INFO
LOG_FILE = '/var/GrantService/logs/telegram_bot.log'
```

#### **Результат:**
- Централизованная конфигурация
- Промпты для всех агентов
- Готовность к интеграции API

---

### **ЭТАП 5: Сервисы и API интеграции** 🔧
**Время:** 3-4 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание `services/database_service.py` (обновленная версия)
- [ ] Создание `services/perplexity_service.py`:
  ```python
  class PerplexityService:
      def __init__(self, api_key):
          self.api_key = api_key
          
      async def research_project_context(self, project_description):
          """Исследование контекста проекта через Perplexity"""
          
      async def find_similar_projects(self, project_type):
          """Поиск похожих проектов"""
  ```
- [ ] Создание `services/gigachat_service.py`:
  ```python
  class GigaChatService:
      def __init__(self, api_key):
          self.api_key = api_key
          
      async def generate_grant_application(self, interview_data):
          """Генерация заявки на грант"""
          
      async def analyze_application_quality(self, application_text):
          """Анализ качества заявки"""
  ```
- [ ] Создание `services/interview_service.py` (обновленная версия)
- [ ] Создание `services/menu_service.py`

#### **Результат:**
- Интеграция с Perplexity API
- Интеграция с ГигаЧат API
- Разделенная бизнес-логика
- Готовность к созданию агентов

---

### **ЭТАП 6: Создание CrewAI агентов** 🤖
**Время:** 3-4 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание `agents/interviewer_agent.py`:
  ```python
  from crewai import Agent
  from services.database_service import DatabaseService
  from services.interview_service import InterviewService
  
  interviewer_agent = Agent(
      role="Grant Application Interviewer",
      goal="Conduct comprehensive 30-question interview via Telegram bot",
      backstory="Expert interviewer specialized in grant applications",
      tools=[DatabaseService(), InterviewService()],
      verbose=True,
      memory=True
  )
  ```
- [ ] Создание `agents/researcher_agent.py`:
  ```python
  researcher_agent = Agent(
      role="Project Context Researcher",
      goal="Research project context and find similar successful projects",
      backstory="Expert researcher with access to latest information",
      tools=[PerplexityService()],
      verbose=True
  )
  ```
- [ ] Создание `agents/writer_agent.py`:
  ```python
  writer_agent = Agent(
      role="Grant Application Writer",
      goal="Create professional grant application based on interview data",
      backstory="Expert grant writer with 10+ years experience",
      tools=[GigaChatService()],
      verbose=True
  )
  ```
- [ ] Создание `agents/auditor_agent.py`:
  ```python
  auditor_agent = Agent(
      role="Application Quality Auditor",
      goal="Analyze and improve grant application quality",
      backstory="Expert auditor specialized in grant applications",
      tools=[GigaChatService()],
      verbose=True
  )
  ```

#### **Результат:**
- 4 специализированных агента
- Интеграция с внешними API
- Готовность к оркестрации

---

### **ЭТАП 7: CrewAI оркестрация** 🎼
**Время:** 2-3 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание `crew/grant_crew.py`:
  ```python
  from crewai import Crew, Process
  
  grant_crew = Crew(
      agents=[interviewer_agent, researcher_agent, writer_agent, auditor_agent],
      tasks=[interview_task, research_task, writing_task, audit_task],
      process=Process.sequential,
      verbose=True,
      max_rpm=10
  )
  ```
- [ ] Создание `crew/tasks.py` с задачами для каждого агента
- [ ] Настройка последовательности выполнения
- [ ] Обработка ошибок и fallback механизмов

#### **Результат:**
- Оркестрированная команда агентов
- Последовательное выполнение задач
- Обработка ошибок

---

### **ЭТАП 8: Обработчики и интерфейс** 🎮
**Время:** 3-4 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание `handlers/menu_handlers.py` (обновленная версия)
- [ ] Создание `handlers/interview_handlers.py` (интеграция с агентами)
- [ ] Создание `handlers/callback_handlers.py`
- [ ] Создание `handlers/message_handlers.py`
- [ ] Интеграция CrewAI в обработчики

#### **Содержимое handlers/interview_handlers.py:**
```python
class InterviewHandlers:
    def __init__(self, grant_crew):
        self.grant_crew = grant_crew
        
    async def start_interview(self, update, context):
        """Начать интервью с использованием агентов"""
        result = await self.grant_crew.kickoff({
            'user_id': update.effective_user.id,
            'action': 'start_interview'
        })
        
    async def handle_answer(self, update, context):
        """Обработать ответ пользователя"""
        # Интеграция с interviewer_agent
```

#### **Результат:**
- Обработчики интегрированы с агентами
- Сохранен пользовательский интерфейс
- Добавлена функциональность агентов

---

### **ЭТАП 9: Главный файл и интеграция** 🎯
**Время:** 1-2 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Рефакторинг `main.py` (50-80 строк)
- [ ] Инициализация всех агентов и сервисов
- [ ] Регистрация обработчиков
- [ ] Настройка логирования
- [ ] Обработка ошибок

#### **Структура main.py:**
```python
class GrantServiceBot:
    def __init__(self):
        # Инициализация сервисов
        self.database_service = DatabaseService()
        self.perplexity_service = PerplexityService()
        self.gigachat_service = GigaChatService()
        
        # Инициализация агентов
        self.interviewer_agent = InterviewerAgent()
        self.researcher_agent = ResearcherAgent()
        self.writer_agent = WriterAgent()
        self.auditor_agent = AuditorAgent()
        
        # Инициализация команды
        self.grant_crew = GrantCrew([
            self.interviewer_agent,
            self.researcher_agent,
            self.writer_agent,
            self.auditor_agent
        ])
        
    def setup_handlers(self, application):
        """Регистрация обработчиков"""
        
    def run(self):
        """Запуск бота"""
```

#### **Результат:**
- Чистый главный файл
- Интеграция всех компонентов
- Готовность к тестированию

---

### **ЭТАП 10: Обновление веб-админки** 🌐
**Время:** 2-3 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание `web-admin/agents_monitoring.py`:
  - Мониторинг статуса агентов
  - Логи выполнения задач
  - Статистика использования API
- [ ] Обновление `web-admin/main_admin.py`:
  - Новые разделы для агентов
  - Управление промптами
  - Метрики производительности
- [ ] Создание `web-admin/analytics_enhanced.py`:
  - Расширенная аналитика
  - Отчеты по агентам
  - Качество заявок

#### **Результат:**
- Админка с мониторингом агентов
- Управление промптами
- Расширенная аналитика

---

### **ЭТАП 11: Тестирование и отладка** 🧪
**Время:** 2-3 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Создание тестов для агентов
- [ ] Тестирование интеграций API
- [ ] Тестирование полного пайплайна
- [ ] Нагрузочное тестирование
- [ ] Отладка ошибок

#### **Результат:**
- Покрытие тестами
- Стабильная работа
- Готовность к продакшену

---

### **ЭТАП 12: Развертывание и мониторинг** 🚀
**Время:** 1-2 дня  
**Статус:** Ожидает

#### **Задачи:**
- [ ] Обновление systemd сервисов
- [ ] Настройка логирования
- [ ] Мониторинг производительности
- [ ] Резервное копирование
- [ ] Документация

#### **Результат:**
- Рабочая многоагентная система
- Мониторинг и логирование
- Готовность к использованию

---

## 📊 **МЕТРИКИ УСПЕХА**

### **Технические метрики:**
- ✅ **Размер файлов:** Каждый модуль < 150 строк
- ✅ **Сложность:** Снижение cyclomatic complexity
- ✅ **Тестирование:** Покрытие > 80%
- ✅ **Производительность:** Время ответа < 2 сек

### **Функциональные метрики:**
- ✅ **30 вопросов:** Полное интервью
- ✅ **4 агента:** Работают корректно
- ✅ **API интеграции:** Perplexity + ГигаЧат
- ✅ **UX:** Улучшенный пользовательский опыт

---

## 🎯 **ПРИОРИТЕТЫ РАЗРАБОТКИ**

### **Высокий приоритет:**
1. **Этап 1-3:** Подготовка и структура
2. **Этап 4-5:** Конфигурация и API
3. **Этап 6-7:** Агенты и оркестрация

### **Средний приоритет:**
4. **Этап 8-9:** Обработчики и интеграция
5. **Этап 10:** Веб-админка
6. **Этап 11:** Тестирование

### **Низкий приоритет:**
7. **Этап 12:** Развертывание

---

## 🚨 **РИСКИ И МИТИГАЦИЯ**

### **Риски:**
- ❌ **Сложность интеграции** CrewAI с существующим кодом
- ❌ **Проблемы с API** (Perplexity, ГигаЧат)
- ❌ **Производительность** многоагентной системы
- ❌ **Время разработки** больше планируемого

### **Митогация:**
- ✅ **Поэтапное тестирование** каждого агента
- ✅ **Fallback механизмы** при недоступности API
- ✅ **Мониторинг производительности**
- ✅ **Гибкий график** с возможностью корректировки

---

## 📅 **ПЛАН РАБОТЫ**

### **Неделя 1:**
- Этап 1-3: Подготовка, БД, структура

### **Неделя 2:**
- Этап 4-5: Конфигурация и API

### **Неделя 3:**
- Этап 6-7: Агенты и оркестрация

### **Неделя 4:**
- Этап 8-9: Обработчики и интеграция

### **Неделя 5:**
- Этап 10-11: Админка и тестирование

### **Неделя 6:**
- Этап 12: Развертывание

---

## 🎉 **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ**

После завершения получим:

### **Технические улучшения:**
- 🚀 **Многоагентная архитектура** с CrewAI
- 🔧 **Модульная структура** вместо монолита
- 🤖 **4 специализированных агента**
- 📊 **30 вопросов интервью**

### **Бизнес-улучшения:**
- ⚡ **Автоматическое исследование** контекста
- ✍️ **Генерация заявок** с помощью ИИ
- 🔍 **Анализ качества** заявок
- 📈 **Масштабируемость** системы

---

**Готовы к объединенному рефакторингу? Начинаем с Этапа 1!** 🚀 