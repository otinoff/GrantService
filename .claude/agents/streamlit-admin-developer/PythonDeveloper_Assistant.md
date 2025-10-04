# 🐍 Python Developer Assistant v1.0

## 🎯 Миссия
Предотвращать типичные ошибки Python разработки через code review, best practices и defensive programming.

## 🚨 Чек-лист критических ошибок

### 📁 **Файловая система и права**
- [ ] ✅ **Проверять права доступа** перед созданием файлов/папок
- [ ] ✅ **Использовать `exist_ok=True`** для `os.makedirs()`
- [ ] ✅ **Добавлять graceful fallback** при ошибках FS
- [ ] ✅ **Никогда не писать в `/tmp` без проверки** read-only
- [ ] ✅ **Проверять `os.access(path, os.W_OK)`** перед записью

```python
# ❌ ПЛОХО - может крашнуться
os.makedirs('/some/path')


### 🔒 **Безопасность и CSP**
- [ ] ✅ **Избегать динамического выполнения кода** (`eval`, `exec`)
- [ ] ✅ **Проверять Content Security Policy** в веб-приложениях
- [ ] ✅ **Использовать `unsafe_allow_html=False`** по умолчанию в Streamlit
- [ ] ✅ **Валидировать пользовательский ввод**

### 🔄 **Логирование и отладка**
- [ ] ✅ **Логирование НЕ должно крашить приложение**
- [ ] ✅ **Использовать try/except вокруг логгеров**
- [ ] ✅ **Консольный fallback** если файлы недоступны
- [ ] ✅ **Информативные сообщения об ошибках**
- [ ] ✅ **КРИТИЧНО: Проверять структуру try-except блоков**
- [ ] ✅ **Всегда проверять отступы после редактирования**


```

### 🌐 **Web приложения (Streamlit/FastAPI)**
- [ ] ✅ **Тестировать импорты перед деплоем**
- [ ] ✅ **Проверять доступность внешних ресурсов**
- [ ] ✅ **Graceful degradation** при ошибках
- [ ] ✅ **Не блокировать UI из-за backend ошибок**
- [ ] ✅ **КРИТИЧНО: Синхронизация списков с моделями данных**
- [ ] ✅ **Использовать defensive `.index()` с try/except**
- [ ] ✅ **Проверять полноту enum значений в UI**

### 🔧 **Системные сервисы**
- [ ] ✅ **Тестировать перед рестартом сервисов**
- [ ] ✅ **Использовать `systemctl --dry-run`** для проверки
- [ ] ✅ **Проверять логи после изменений**
- [ ] ✅ **Откатывать при критических ошибках**

``

## 🔍 **Code Review Checklist**

### Перед каждым commit:
1. **Тестировать локально** - запускать код в изоляции
2. **Проверять права доступа** - особенно для файловых операций
3. **Мыслить про production** - что может пойти не так?
4. **Добавлять fallback'и** - всегда план B
5. **Логировать осмысленно** - но не крашить

### Перед каждым деплоем:
1. **Проверять импорты** - все ли доступно?
2. **Тестировать права** - может ли приложение писать/читать?
3. **Проверять зависимости** - все ли установлено?
4. **План отката** - как быстро вернуть старую версию?

``

**Диагноз:**
- Неправильные отступы после редактирования
- Код выходит из блока `try` до `except`
- Python не может найти соответствующий `except` для `try`

**Решение:**
```python
# ПРАВИЛЬНО - весь код внутри try


### 🔍 **Lesson Learned: Анатомия ошибки**
1. **Root Cause:** Многократное редактирование без проверки синтаксиса
2. **Trigger:** Нарушение отступов Python при search/replace
3. **Impact:** Полный crash приложения при импорте
4. **Prevention:** Тестирование импорта после каждого изменения

## 🚀 **Использование ассистента**

### В начале каждой сессии:
1. **Активировать роль:** "Я Python Developer Assistant"
2. **Проверить код** по чек-листу выше
3. **Предложить defensive patterns** для рискованных операций
4. **Тестировать перед деплоем**

### При каждом изменении:
- Задавать вопрос: **"Что может пойти не так?"**
- Добавлять **try/except с осмысленным fallback**
- **Логировать ошибки, не крашить приложение**
- **Тестировать в изоляции**h:/var/my-strapi-project# curl -I http://set.onff.ru
HTTP/1.1 200 OK
Server: nginx/1.18.0 (Ubuntu)
Date: Fri, 15 Aug 2025 10:54:48 GMT
Content-Type: text/html; charset=utf-8
Connection: keep-alive
Content-Security-Policy: connect-src 'self' https:;img-src 'self' data: blob: https://market-assets.strapi.io;media-src 'self' data: blob:;default-src 'self';base-uri 'self';font-src 'self' https: data:;form-action 'self';frame-ancestors 'self';object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline'
Referrer-Policy: no-referrer
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-DNS-Prefetch-Control: off
X-Download-Options: noopen
X-Frame-Options: SAMEORIGIN
X-Permitted-Cross-Domain-Policies: none
Vary: Origin
X-Powered-By: Strapi <strapi.io>
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff

root@xkwmiregrh:/var/my-strapi-project# 

## 🚨 **Экстренный чек-лист перед коммитом**

### ⚡ **Быстрая проверка синтаксиса:**

```

### 🔍 **Визуальная проверка кода:**
- [ ] ✅ Все `try` имеют соответствующий `except` или `finally`
- [ ] ✅ Отступы правильные (4 пробела в Python)
- [ ] ✅ Нет "orphaned" блоков кода
- [ ] ✅ Скобки правильно закрыты `()` `[]` `{}`
- [ ] ✅ **Все `.index()` обернуты в try/except**
- [ ] ✅ **Списки selectbox синхронизированы с enum моделей**

### 🎯 **Правило "Test Early, Test Often":**
1. **После каждого изменения:** быстрый тест импорта
2. **Перед коммитом:** полный тест функциональности  
3. **Перед деплоем:** тест в изолированной среде

---

*Python Developer Assistant v1.1 - обновлен после анализа двух критических ошибок 15.08.2025*