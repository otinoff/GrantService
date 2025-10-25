# Удаление старой папки GrantService_Project

## Статус

Все файлы из `C:\SnowWhiteAI\GrantService_Project` были перемещены в `C:\SnowWhiteAI\GrantService`.

## Что было сделано:

### Перемещено в `GrantService/docs/`:
- ✅ `01_Projects/` → `docs/01_Projects/`
- ✅ `04_Reports/` → `docs/04_Reports/`
- ✅ `Strategy/` → `docs/Strategy/`
- ✅ `Versions/` → `docs/Versions/`
- ✅ Все `.md` файлы из корня

### Перемещено в `GrantService/archive/from_project/`:
- ✅ `_Agent_Work/`
- ✅ `05_Marketing/`
- ✅ `06_Archive/`
- ✅ Все `.py` и `.txt` файлы

### Было скопировано ранее в `GrantService/docs/`:
- ✅ `00_Project_Info/` → `docs/00_Project_Info/`
- ✅ `02_Research/` → `docs/02_Research/`
- ✅ `03_Business/` → `docs/03_Business/`
- ✅ `Development/` → `docs/04_Deployment/`

## Инструкция по удалению:

Папка `C:\SnowWhiteAI\GrantService_Project` сейчас используется (возможно, открыта в проводнике или Claude Code).

**Для удаления:**

1. Закройте все окна проводника с этой папкой
2. Закройте Claude Code (если открыт в этой папке)
3. Откройте PowerShell и выполните:

```powershell
Remove-Item -Path "C:\SnowWhiteAI\GrantService_Project" -Recurse -Force
```

Или через проводник:
1. Перезагрузите компьютер (если папка всё ещё занята)
2. Удалите папку `C:\SnowWhiteAI\GrantService_Project` через проводник

## Проверка

После удаления должна остаться только одна папка проекта:
```
C:\SnowWhiteAI\GrantService\  ← Единственная папка проекта
```

Все файлы теперь находятся в `GrantService/`.
