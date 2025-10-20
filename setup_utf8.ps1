# ============================================
# PowerShell UTF-8 Setup Script
# ============================================
# Run this to permanently fix encoding issues

Write-Host "🔧 Настройка UTF-8 для PowerShell..." -ForegroundColor Cyan

# Set UTF-8 for current session
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# Set environment variables for current session
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

Write-Host ""
Write-Host "✅ UTF-8 настроен для текущей сессии!" -ForegroundColor Green
Write-Host ""

# Ask user if they want to add to PowerShell profile
$addToProfile = Read-Host "Добавить в PowerShell профиль для постоянного использования? (y/n)"

if ($addToProfile -eq "y" -or $addToProfile -eq "Y") {
    $profilePath = $PROFILE.CurrentUserCurrentHost

    # Create profile if doesn't exist
    if (!(Test-Path -Path $profilePath)) {
        New-Item -ItemType File -Path $profilePath -Force | Out-Null
        Write-Host "📄 Создан новый профиль: $profilePath" -ForegroundColor Yellow
    }

    # Add UTF-8 configuration to profile
    $utfConfig = @"

# ============================================
# UTF-8 Encoding Configuration (GrantService)
# ============================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

`$env:PYTHONIOENCODING = "utf-8"
`$env:PYTHONUTF8 = "1"
"@

    # Check if already added
    $profileContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue

    if ($profileContent -notmatch "UTF-8 Encoding Configuration") {
        Add-Content -Path $profilePath -Value $utfConfig
        Write-Host "✅ UTF-8 конфигурация добавлена в профиль!" -ForegroundColor Green
        Write-Host "📍 Путь: $profilePath" -ForegroundColor Cyan
    } else {
        Write-Host "ℹ️ UTF-8 конфигурация уже есть в профиле" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "📋 Текущие настройки:" -ForegroundColor Cyan
Write-Host "   Code Page: $(chcp | Select-String -Pattern '\d+')"
Write-Host "   OutputEncoding: $($OutputEncoding.EncodingName)"
Write-Host "   PYTHONIOENCODING: $env:PYTHONIOENCODING"
Write-Host "   PYTHONUTF8: $env:PYTHONUTF8"
Write-Host ""
Write-Host "✅ Готово! Перезапустите PowerShell для применения изменений." -ForegroundColor Green
