# 🚀 ЗАПУСК АДМИНКИ GRANTSERVICE

## БЫСТРЫЙ СТАРТ

### Windows:
```bash
admin.bat
```

### Linux/Ubuntu:
```bash
chmod +x admin.sh
./admin.sh
```

### Альтернатива:
```bash
# Windows
python launcher.py

# Linux
python3 launcher.py
```

## ⚠️ ВАЖНО
**НЕ запускайте напрямую через streamlit!** Это не будет работать.
```bash
# ❌ НЕПРАВИЛЬНО:
streamlit run web-admin/pages/🏠_Главная.py
python start_admin.bat  # .bat это не Python!

# ✅ ПРАВИЛЬНО:
admin.bat               # или
python launcher.py
```

## ПРОВЕРКА
```bash
python launcher.py --test
```

Успешный тест покажет:
- ✅ data.database imported successfully
- ✅ Bot constants loaded

## СТРУКТУРА
```
GrantService/
├── launcher.py    # Главный файл запуска
├── admin.bat      # Для Windows
├── admin.sh       # Для Linux
└── core/          # Настройки системы
```

## ПРОБЛЕМЫ?

1. **ModuleNotFoundError**: Запускайте через `launcher.py`
2. **SyntaxError с .bat**: Не запускайте .bat через python
3. **Import error**: Используйте `admin.bat` или `python launcher.py`

## ПОСЛЕ ЗАПУСКА
Откройте браузер: http://localhost:8501

---
**Все файлы рефакторены. Система готова к работе на Windows и Linux.**