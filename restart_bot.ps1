# PowerShell скрипт для перезапуска Telegram бота GrantService
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Перезапуск Telegram бота GrantService" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Устанавливаем рабочую директорию
Set-Location -Path "C:\SnowWhiteAI\GrantService"

# Проверяем виртуальное окружение
$venvPath = "telegram-bot\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[ERROR] Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "Создаем виртуальное окружение..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Виртуальное окружение создано." -ForegroundColor Green
    Write-Host ""
}

# Активируем виртуальное окружение
Write-Host "[1] Активируем виртуальное окружение..." -ForegroundColor Cyan
& "telegram-bot\venv\Scripts\Activate.ps1"

# Обновляем зависимости
Write-Host ""
Write-Host "[2] Обновляем зависимости..." -ForegroundColor Cyan
pip install --upgrade pip --quiet
pip install python-telegram-bot requests python-dotenv --quiet

# Проверяем конфигурацию
Write-Host ""
Write-Host "[3] Проверяем переменные окружения..." -ForegroundColor Cyan
if (-not (Test-Path "config\.env")) {
    Write-Host "[WARNING] Файл config\.env не найден!" -ForegroundColor Red
    Write-Host "Используйте config\.env.example как шаблон" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Останавливаем старые процессы
Write-Host ""
Write-Host "[4] Останавливаем старый процесс бота (если запущен)..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*GrantService*"} | Stop-Process -Force

# Запускаем бота
Write-Host ""
Write-Host "[5] Запускаем бота..." -ForegroundColor Green
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""

# Запускаем Python скрипт
python telegram-bot\main.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Бот остановлен." -ForegroundColor Yellow
Read-Host "Нажмите Enter для закрытия"