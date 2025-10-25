@echo off
REM E2E Test - Iteration 27 для Sber500 Bootcamp
REM Запуск с локальной БД и GigaChat-Max

echo ========================================
echo E2E Test - Iteration 27
echo Sber500 Bootcamp
echo ========================================
echo.

REM Загрузка credentials из .env.local
echo Loading credentials from .env.local...
cd /d "%~dp0\.."

for /f "usebackq tokens=1,* delims==" %%a in (".env.local") do (
    set "line=%%a"
    if not "!line:~0,1!"=="#" (
        set "%%a=%%b"
    )
)

echo [OK] Credentials loaded
echo.

REM Переопределение на локальную БД (скрипт сам это делает, но для явности)
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=grantservice
set PGUSER=postgres
set PGPASSWORD=root

echo Database: localhost:5432/grantservice
echo Model: GigaChat-Max
echo Anketa: #AN-20251012-Natalia_bruzzzz-001
echo.

echo ========================================
echo Starting E2E Test...
echo ========================================
echo.

REM Запуск Python скрипта
cd scripts
python -X utf8 run_e2e_local_windows.py

echo.
echo ========================================
echo E2E Test Complete
echo ========================================
echo.

pause
