# PowerShell скрипт для регистрации агентов Claude Code
# Автоматически регистрирует все агенты из папки .claude/agents

$agentsPath = "C:\SnowWhiteAI\GrantService\.claude\agents"
$claudeCodePath = "claude"  # Путь к исполняемому файлу Claude Code

Write-Host "=== Регистрация агентов Claude Code ===" -ForegroundColor Cyan
Write-Host ""

# Проверяем существование папки с агентами
if (-not (Test-Path $agentsPath)) {
    Write-Host "Ошибка: Папка с агентами не найдена: $agentsPath" -ForegroundColor Red
    exit 1
}

# Получаем список всех .md файлов агентов
$agentFiles = Get-ChildItem -Path $agentsPath -Filter "*.md"

if ($agentFiles.Count -eq 0) {
    Write-Host "Агенты не найдены в папке $agentsPath" -ForegroundColor Yellow
    exit 0
}

Write-Host "Найдено агентов: $($agentFiles.Count)" -ForegroundColor Green
Write-Host ""

$registeredCount = 0
$failedCount = 0

foreach ($agentFile in $agentFiles) {
    $agentName = [System.IO.Path]::GetFileNameWithoutExtension($agentFile.Name)
    Write-Host "Регистрация агента: $agentName" -ForegroundColor Yellow

    try {
        # Регистрируем агента через Claude Code CLI
        # Команда: claude agent create <путь_к_файлу>
        $result = & $claudeCodePath agent create $agentFile.FullName 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Успешно зарегистрирован" -ForegroundColor Green
            $registeredCount++
        } else {
            Write-Host "  [ERROR] Ошибка регистрации: $result" -ForegroundColor Red
            $failedCount++
        }
    } catch {
        Write-Host "  [ERROR] Ошибка: $_" -ForegroundColor Red
        $failedCount++
    }

    Write-Host ""
}

# Итоговая статистика
Write-Host "=== Результаты регистрации ===" -ForegroundColor Cyan
Write-Host "Успешно зарегистрировано: $registeredCount" -ForegroundColor Green
if ($failedCount -gt 0) {
    Write-Host "Не удалось зарегистрировать: $failedCount" -ForegroundColor Red
}

# Показываем список зарегистрированных агентов
Write-Host ""
Write-Host "=== Список агентов ===" -ForegroundColor Cyan
try {
    & $claudeCodePath agent list
} catch {
    Write-Host "Не удалось получить список агентов" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Регистрация завершена!" -ForegroundColor Green